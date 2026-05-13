"""Scrape mode — single URL fetch to clean markdown + optional screenshot.

Returns ScrapeResponse with:
- markdown: clean filtered content (primary, always populated on success)
- raw_html: original HTML (only if ScoutFormats.RAW_HTML in formats)
- screenshot_base64: PNG base64 (only if ScoutFormats.SCREENSHOT in formats)
- links: all internal and external hrefs extracted from page
- metadata: title, description, word_count, token_estimate, language
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import cast

import structlog
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, CrawlResult
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from scout.core.types import ScoutFormats, ScoutMetadata, ScrapeRequest, ScrapeResponse

logger = structlog.get_logger(__name__)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~0.75 tokens per word (4 chars avg)."""
    return max(1, len(text) // 4)


def _count_words(text: str) -> int:
    """Return number of whitespace-separated words in text."""
    return len(text.split())


def _extract_links(links_dict: dict) -> list[str]:
    """Flatten crawl4ai links dict to a list of hrefs."""
    result = []
    for link in links_dict.get("internal", []):
        href = link.get("href", "")
        if href:
            result.append(href)
    for link in links_dict.get("external", []):
        href = link.get("href", "")
        if href:
            result.append(href)
    return result


async def scrape(req: ScrapeRequest) -> ScrapeResponse:
    """Fetch a single URL and return clean content."""
    started = time.monotonic()
    crawled_at = datetime.now(timezone.utc).isoformat()

    want_screenshot = ScoutFormats.SCREENSHOT in req.formats
    want_raw_html = ScoutFormats.RAW_HTML in req.formats

    md_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
    )
    browser_cfg = BrowserConfig(
        headless=True,
        java_script_enabled=req.use_js,
        enable_stealth=req.stealth,
    )
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=md_generator,
        screenshot=want_screenshot,
        page_timeout=req.timeout_ms,
        wait_for=req.wait_for,
        simulate_user=req.stealth,
        magic=req.stealth,
    )

    def _empty_meta() -> ScoutMetadata:
        return ScoutMetadata(url=req.url, crawled_at=crawled_at)

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            # arun() returns CrawlResultContainer whose __getattr__ delegates to _results[0].
            # Cast to CrawlResult so pyright can resolve attributes; runtime behaviour is unchanged.
            result = cast(CrawlResult, await crawler.arun(req.url, config=run_cfg))

        duration_ms = int((time.monotonic() - started) * 1000)

        if not result.success:
            logger.warning("[scout/scrape] crawl failed", url=req.url, error=result.error_message)
            return ScrapeResponse(
                success=False,
                url=req.url,
                metadata=_empty_meta(),
                error=result.error_message or "Unknown error",
                duration_ms=duration_ms,
            )

        # result.markdown is StringCompatibleMarkdown (has .fit_markdown via __getattr__) or None.
        # Use getattr so tests that pass plain strings as markdown mock values don't break.
        _md = result.markdown
        clean_md = getattr(_md, "fit_markdown", None) or str(_md or "") or ""
        raw_meta = result.metadata or {}

        metadata = ScoutMetadata(
            url=result.url or req.url,
            crawled_at=crawled_at,
            title=raw_meta.get("title", "") or "",
            description=raw_meta.get("description", "") or "",
            language=raw_meta.get("language", "") or "",
            word_count=_count_words(clean_md),
            token_estimate=_estimate_tokens(clean_md),
        )

        return ScrapeResponse(
            success=True,
            url=result.url or req.url,
            markdown=clean_md,
            raw_html=result.html or "" if want_raw_html else "",
            screenshot_base64=result.screenshot or "" if want_screenshot else "",
            links=_extract_links(result.links or {}),
            metadata=metadata,
            duration_ms=duration_ms,
        )

    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception("[scout/scrape] unexpected error", url=req.url, exc=str(exc))
        return ScrapeResponse(
            success=False,
            url=req.url,
            metadata=_empty_meta(),
            error=str(exc),
            duration_ms=duration_ms,
        )
