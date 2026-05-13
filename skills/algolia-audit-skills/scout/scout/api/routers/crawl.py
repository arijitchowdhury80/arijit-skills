"""Crawl router — recursive BFS site crawl."""

from fastapi import APIRouter, Depends

from scout.api.deps import get_crawler
from scout.core.crawler import ScoutCrawler
from scout.core.types import CrawlRequest, CrawlResponse

router = APIRouter()


@router.post("/crawl", response_model=CrawlResponse)
async def crawl(
    req: CrawlRequest,
    crawler: ScoutCrawler = Depends(get_crawler),
) -> CrawlResponse:
    """Recursively crawl a site via BFS and return all discovered pages."""
    return await crawler.crawl(req)
