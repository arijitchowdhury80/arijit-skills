"""Shared FastAPI dependencies — importable by all routers."""

from fastapi import Request

from scout.core.crawler import ScoutCrawler


def get_crawler(request: Request) -> ScoutCrawler:
    """Return the ScoutCrawler instance stored on app.state at startup."""
    crawler: ScoutCrawler = request.app.state.crawler
    return crawler
