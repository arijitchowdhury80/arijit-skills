"""Screenshot mode — visual capture only, no content extraction.

Returns a base64-encoded PNG of the page. Useful for:
- Before/after site comparisons (restaurant redesign use case)
- Visual audits
- UI regression detection
"""

from __future__ import annotations

import time
from typing import cast

import structlog
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, CrawlResult

from scout.core.types import ScreenshotRequest, ScreenshotResponse

logger = structlog.get_logger(__name__)


async def screenshot(req: ScreenshotRequest) -> ScreenshotResponse:
    """Capture a visual screenshot of a URL."""
    started = time.monotonic()

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        screenshot=True,
        page_timeout=30000,
        wait_for=req.wait_for,
        word_count_threshold=1,
    )
    browser_cfg = BrowserConfig(
        headless=True,
        java_script_enabled=req.use_js,
        viewport_width=req.viewport_width,
        viewport_height=req.viewport_height,
    )

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            # arun() returns CrawlResultContainer whose __getattr__ delegates to _results[0].
            # Cast to CrawlResult so pyright can resolve attributes; runtime behaviour is unchanged.
            result = cast(CrawlResult, await crawler.arun(req.url, config=run_cfg))

        duration_ms = int((time.monotonic() - started) * 1000)

        if not result.success:
            return ScreenshotResponse(
                success=False,
                url=req.url,
                error=result.error_message or "Crawl failed",
                width=req.viewport_width,
                height=req.viewport_height,
                duration_ms=duration_ms,
            )

        return ScreenshotResponse(
            success=True,
            url=result.url or req.url,
            screenshot_base64=result.screenshot or "",
            width=req.viewport_width,
            height=req.viewport_height,
            duration_ms=duration_ms,
        )

    except Exception as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        logger.exception("[scout/screenshot] error", url=req.url, exc=str(exc))
        return ScreenshotResponse(
            success=False,
            url=req.url,
            error=str(exc),
            width=req.viewport_width,
            height=req.viewport_height,
            duration_ms=duration_ms,
        )
