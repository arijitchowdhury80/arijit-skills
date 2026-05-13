"""Health check router — no authentication required."""

from fastapi import APIRouter

from scout.core.version import CRAWL4AI_VERSION, SCOUT_VERSION

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Return service liveness and version info."""
    return {
        "status": "ok",
        "crawl4ai_version": CRAWL4AI_VERSION,
        "scout_version": SCOUT_VERSION,
    }
