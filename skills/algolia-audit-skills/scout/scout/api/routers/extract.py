"""Extract router — LLM-powered structured data extraction."""

from fastapi import APIRouter, Depends

from scout.api.deps import get_crawler
from scout.core.crawler import ScoutCrawler
from scout.core.types import ExtractRequest, ExtractResponse

router = APIRouter()


@router.post("/extract", response_model=ExtractResponse)
async def extract(
    req: ExtractRequest,
    crawler: ScoutCrawler = Depends(get_crawler),
) -> ExtractResponse:
    """Crawl a URL and extract structured data using an LLM strategy."""
    return await crawler.extract(req)
