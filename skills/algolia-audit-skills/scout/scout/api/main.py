"""Scout FastAPI application — entry point for the HTTP service."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from scout.api.config import settings
from scout.api.deps import get_crawler
from scout.api.middleware.auth import AuthMiddleware
from scout.api.routers import crawl, extract, health
from scout.api.routers import map as map_router
from scout.api.routers import scrape, screenshot
from scout.core.crawler import ScoutCrawler

# Re-export get_crawler so tests can import it from scout.api.main for
# dependency_overrides.
__all__ = ["app", "get_crawler"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise shared resources on startup; release them on shutdown."""
    app.state.crawler = ScoutCrawler(llm_api_key=settings.llm_api_key)
    yield


app = FastAPI(title="Scout", lifespan=lifespan)

app.add_middleware(AuthMiddleware, api_key=settings.scout_api_key)

app.include_router(health.router)
app.include_router(scrape.router)
app.include_router(crawl.router)
app.include_router(extract.router)
app.include_router(map_router.router)
app.include_router(screenshot.router)
