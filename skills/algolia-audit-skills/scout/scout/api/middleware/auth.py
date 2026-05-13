"""Authentication middleware — enforces X-API-Key on all non-health routes."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class AuthMiddleware(BaseHTTPMiddleware):
    """Reject requests missing or carrying a wrong X-API-Key header.

    The /health path is whitelisted and always passes through.
    """

    def __init__(self, app: object, api_key: str) -> None:
        """Initialise middleware with the expected API key."""
        super().__init__(app)  # type: ignore[arg-type]
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next: object) -> Response:
        """Pass /health through; reject all other requests without a valid key."""
        if request.url.path == "/health":
            return await call_next(request)  # type: ignore[misc]

        incoming_key = request.headers.get("X-API-Key")
        if not incoming_key or incoming_key != self._api_key:
            return JSONResponse({"detail": "Unauthorized"}, status_code=403)

        return await call_next(request)  # type: ignore[misc]
