"""Screenshot router — visual page capture as base64 PNG."""

from fastapi import APIRouter, Depends

from scout.api.deps import get_crawler
from scout.core.crawler import ScoutCrawler
from scout.core.types import ScreenshotRequest, ScreenshotResponse

router = APIRouter()


@router.post("/screenshot", response_model=ScreenshotResponse)
async def screenshot(
    req: ScreenshotRequest,
    crawler: ScoutCrawler = Depends(get_crawler),
) -> ScreenshotResponse:
    """Capture a visual screenshot of a URL as a base64-encoded PNG."""
    return await crawler.screenshot(req)
