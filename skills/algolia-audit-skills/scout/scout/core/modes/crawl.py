"""Crawl mode — recursive BFS crawl via Crawl4AI's BFSDeepCrawlStrategy.

Uses crawl4ai's native BFSDeepCrawlStrategy passed via CrawlerRunConfig.deep_crawl_strategy.
The DeepCrawlDecorator on AsyncWebCrawler intercepts crawler.arun(url, config) and delegates
to the strategy's streaming BFS loop. Entry point is crawler.arun(), NOT arun_many().

DomainFilter restricts crawl to the seed domain (prevents link leak to external sites).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import AsyncGenerator, cast
from urllib.parse import urlparse

import structlog
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, DomainFilter, FilterChain
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.models import CrawlResult

from scout.core.types import CrawlPage, CrawlRequest, CrawlResponse, ScoutMetadata

logger = structlog.get_logger(__name__)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~0.75 tokens per word (4 chars avg)."""
    return max(1, len(text) // 4)


async def crawl(req: CrawlRequest) -> CrawlResponse:
    """Recursively crawl a site using BFSDeepCrawlStrategy."""
    started = time.monotonic()
    crawled_at = datetime.now(timezone.utc).isoformat()

    domain = urlparse(req.url).netloc

    md_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
    )

    bfs = BFSDeepCrawlStrategy(
        max_depth=req.max_depth,
        max_pages=req.max_pages,
        filter_chain=FilterChain([DomainFilter(allowed_domains=[domain])]),
        include_external=req.include_external,
    )

    browser_cfg = BrowserConfig(
        headless=True,
        java_script_enabled=req.use_js,
        enable_stealth=req.stealth,
    )
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        deep_crawl_strategy=bfs,
        stream=True,
        markdown_generator=md_generator,
        page_timeout=req.timeout_ms,
        simulate_user=req.stealth,
        magic=req.stealth,
    )

    pages: list[CrawlPage] = []

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            # DeepCrawlDecorator intercepts arun(), returns async generator when stream=True.
            # Cast to AsyncGenerator so pyright can verify async iteration.
            gen = cast(
                AsyncGenerator[CrawlResult, None],
                await crawler.arun(req.url, config=run_cfg),
            )
            async for result in gen:
                _md = result.markdown
                clean_md = getattr(_md, "fit_markdown", None) or str(_md or "") or ""
                raw_meta = result.metadata or {}
                meta = ScoutMetadata(
                    url=result.url or req.url,
                    crawled_at=crawled_at,
                    title=raw_meta.get("title", "") or "",
                    description=raw_meta.get("description", "") or "",
                    language=raw_meta.get("language", "") or "",
                    word_count=len(clean_md.split()),
                    token_estimate=_estimate_tokens(clean_md),
                )

                if result.success:
                    pages.append(
                        CrawlPage(
                            url=result.url or req.url,
                            markdown=clean_md,
                            metadata=meta,
                            success=True,
                        )
                    )
                else:
                    pages.append(
                        CrawlPage(
                            url=result.url or req.url,
                            metadata=meta,
                            success=False,
                            error=result.error_message or "",
                        )
                    )

        duration_ms = int((time.monotonic() - started) * 1000)
        logger.info("[scout/crawl] complete", start_url=req.url, pages=len(pages))
        return CrawlResponse(
            success=True,
            start_url=req.url,
            pages=pages,
            total_pages=len(pages),
            duration_ms=duration_ms,
        )

    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception("[scout/crawl] error", url=req.url, exc=str(exc))
        return CrawlResponse(
            success=False,
            start_url=req.url,
            pages=[],
            total_pages=0,
            error=str(exc),
            duration_ms=duration_ms,
        )
