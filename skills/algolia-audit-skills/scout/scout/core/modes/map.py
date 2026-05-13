"""Map mode — URL discovery via sitemap-first + BFS link-follow fallback.

Primary path: crawl4ai AsyncUrlSeeder parses robots.txt → sitemap.xml (including
sub-sitemaps) → returns full URL list. Fast: typically < 3s for well-maintained sites.

Fallback path: manual BFS link-follow when sitemap yields fewer than
_SITEMAP_MIN_THRESHOLD URLs (site has no sitemap or it's malformed).

Threshold check is on the RAW sitemap count (before url_pattern filter) so that
a narrow url_pattern on a valid sitemap does not incorrectly trigger BFS.
"""

from __future__ import annotations

import time
from collections import deque
from typing import cast
from urllib.parse import urlparse

import structlog
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    CrawlResult,
    SeedingConfig,
)

from scout.core.types import MapRequest, MapResponse

logger = structlog.get_logger(__name__)

_SITEMAP_MIN_THRESHOLD = 5
_MAP_BFS_MAX_DEPTH = 3


async def map_urls(req: MapRequest) -> MapResponse:
    """Discover all URLs for a site. Sitemap-first, BFS fallback."""
    started = time.monotonic()

    try:
        urls, raw_count = await _sitemap_discovery(req)
        # Threshold check uses raw (pre-filter) count.
        # When a url_pattern is active and the sitemap returned any URLs at all,
        # treat the sitemap as valid — the pattern narrows results by design,
        # not because the sitemap is broken.
        sitemap_sufficient = raw_count >= _SITEMAP_MIN_THRESHOLD or (
            req.url_pattern and raw_count > 0
        )
        if not sitemap_sufficient:
            logger.info(
                "[scout/map] sitemap sparse, falling back to BFS",
                sitemap_count=raw_count,
                url=req.url,
            )
            urls = await _bfs_link_follow(req)

        # Respect max_pages cap
        if req.max_pages and len(urls) > req.max_pages:
            urls = urls[: req.max_pages]

        duration_ms = int((time.monotonic() - started) * 1000)
        logger.info("[scout/map] complete", start_url=req.url, urls=len(urls))
        return MapResponse(
            success=True,
            start_url=req.url,
            urls=urls,
            total=len(urls),
            duration_ms=duration_ms,
        )

    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception("[scout/map] error", url=req.url, exc=str(exc))
        return MapResponse(
            success=False,
            start_url=req.url,
            urls=[],
            total=0,
            error=str(exc),
            duration_ms=duration_ms,
        )


async def _sitemap_discovery(req: MapRequest) -> tuple[list[str], int]:
    """Parse robots.txt + sitemap.xml to collect all URLs. Fast path.

    Returns (filtered_urls, raw_count).

    The raw_count (pre-filter) is used for the BFS threshold decision so that
    a narrow url_pattern on a valid sitemap does not incorrectly trigger BFS.
    """
    # aseed_urls takes bare domain, not full URL
    domain = urlparse(req.url).netloc

    seed_cfg = SeedingConfig(
        source="sitemap",
        max_urls=req.max_pages if req.max_pages > 0 else -1,
        hits_per_sec=5,
        filter_nonsense_urls=True,
    )

    async with AsyncWebCrawler() as crawler:
        raw = await crawler.aseed_urls(domain, config=seed_cfg)

    # aseed_urls returns list[str] on most domains but list[dict] on some —
    # normalise unconditionally so MapResponse always receives plain strings.
    raw_urls: list[str] = [
        u["url"] if isinstance(u, dict) and "url" in u else str(u)
        for u in cast(list, raw)
        if u
    ]

    raw_count = len(raw_urls)

    # Apply url_pattern filter if specified — after recording raw count
    filtered_urls = [u for u in raw_urls if req.url_pattern in u] if req.url_pattern else raw_urls

    logger.info(
        "[scout/map] sitemap discovery",
        domain=domain,
        raw=raw_count,
        filtered=len(filtered_urls),
    )
    return filtered_urls, raw_count


async def _bfs_link_follow(req: MapRequest) -> list[str]:
    """BFS fallback: follow <a href> links when sitemap is absent/sparse."""
    browser_cfg = BrowserConfig(
        headless=True,
        java_script_enabled=req.stealth,  # need JS for stealth pages
        enable_stealth=req.stealth,
    )
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=1,
        simulate_user=req.stealth,
        magic=req.stealth,
    )

    visited: set[str] = set()
    discovered: list[str] = [req.url]
    queue: deque[tuple[str, int]] = deque([(req.url, 0)])

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        while queue and len(discovered) < req.max_pages:
            url, depth = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            result = cast(CrawlResult, await crawler.arun(url, config=run_cfg))

            if not result.success or depth >= _MAP_BFS_MAX_DEPTH:
                continue

            links: dict = result.links or {}
            candidates = list(links.get("internal", []))
            if req.include_external:
                candidates += list(links.get("external", []))

            for link in candidates:
                href = link.get("href", "") if isinstance(link, dict) else str(link)
                if not href or href in visited or href in discovered:
                    continue
                if req.url_pattern and req.url_pattern not in href:
                    continue
                discovered.append(href)
                queue.append((href, depth + 1))
                if len(discovered) >= req.max_pages:
                    break

    logger.info("[scout/map] BFS fallback complete", start_url=req.url, urls=len(discovered))
    return discovered
