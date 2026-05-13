"""Map router — URL discovery without content extraction."""

from fastapi import APIRouter, Depends

from scout.api.deps import get_crawler
from scout.core.crawler import ScoutCrawler
from scout.core.types import MapRequest, MapResponse

router = APIRouter()


@router.post("/map", response_model=MapResponse)
async def map_urls(
    req: MapRequest,
    crawler: ScoutCrawler = Depends(get_crawler),
) -> MapResponse:
    """Discover all URLs on a site without extracting page content."""
    return await crawler.map_urls(req)
