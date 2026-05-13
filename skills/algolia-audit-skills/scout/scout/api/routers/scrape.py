"""Scrape router — single-URL fetch with optional JS rendering."""

from fastapi import APIRouter, Depends

from scout.api.deps import get_crawler
from scout.core.crawler import ScoutCrawler
from scout.core.types import ScrapeRequest, ScrapeResponse

router = APIRouter()


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape(
    req: ScrapeRequest,
    crawler: ScoutCrawler = Depends(get_crawler),
) -> ScrapeResponse:
    """Fetch a single URL and return clean markdown content."""
    return await crawler.scrape(req)
