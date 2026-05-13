"""Scout CLI — run Scout modes directly without starting the HTTP server."""

from __future__ import annotations

import asyncio
import json

import typer

from scout.core.modes.crawl import crawl as _crawl
from scout.core.modes.extract import extract as _extract
from scout.core.modes.map import map_urls as _map
from scout.core.modes.scrape import scrape as _scrape
from scout.core.modes.screenshot import screenshot as _screenshot
from scout.core.types import (
    CrawlRequest,
    ExtractRequest,
    MapRequest,
    ScreenshotRequest,
    ScrapeRequest,
)

app = typer.Typer(
    name="scout",
    help=(
        "Scout web intelligence CLI.\n\n"
        "This product includes software developed by UncleCode (https://x.com/unclecode) "
        "as part of the Crawl4AI project (https://github.com/unclecode/crawl4ai), "
        "licensed under the Apache License 2.0."
    ),
    no_args_is_help=True,
)


def _out(data: dict) -> None:
    print(json.dumps(data, indent=2, default=str))


def _die(resp: object) -> None:
    """Print response and exit 1 if success=False."""
    d = resp.model_dump()  # type: ignore[union-attr]
    _out(d)
    if not d.get("success", True):
        raise SystemExit(1)


@app.command()
def scrape(
    url: str = typer.Argument(..., help="URL to fetch"),
    js: bool = typer.Option(False, "--js", help="Enable JS rendering (Playwright)"),
    wait_for: str = typer.Option("", "--wait-for", help="CSS selector or JS expression to wait for"),
    timeout: int = typer.Option(30000, "--timeout", help="Page load timeout in ms"),
) -> None:
    """Fetch a single page and return clean markdown + metadata."""
    req = ScrapeRequest(url=url, use_js=js, wait_for=wait_for, timeout_ms=timeout)
    resp = asyncio.run(_scrape(req))
    _die(resp)


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Start URL for BFS crawl"),
    depth: int = typer.Option(2, "--depth", help="Max BFS depth"),
    pages: int = typer.Option(10, "--pages", help="Max pages to crawl"),
    pattern: str = typer.Option("", "--pattern", help="URL substring filter"),
    js: bool = typer.Option(False, "--js", help="Enable JS rendering"),
    timeout: int = typer.Option(60000, "--timeout", help="Per-page timeout in ms"),
) -> None:
    """BFS deep crawl from a start URL — returns all pages up to depth/pages limit."""
    req = CrawlRequest(url=url, max_depth=depth, max_pages=pages, url_pattern=pattern, use_js=js, timeout_ms=timeout)
    resp = asyncio.run(_crawl(req))
    _die(resp)


@app.command()
def map(
    url: str = typer.Argument(..., help="Site URL to discover URLs for"),
    pages: int = typer.Option(100, "--pages", help="Max URLs to return"),
    pattern: str = typer.Option("", "--pattern", help="URL substring filter (applied after sitemap fetch)"),
) -> None:
    """Discover all URLs on a site via sitemap, with BFS fallback."""
    req = MapRequest(url=url, max_pages=pages, url_pattern=pattern)
    resp = asyncio.run(_map(req))
    _die(resp)


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to extract structured data from"),
    schema: str = typer.Option("{}", "--schema", help="JSON Schema string for LLM extraction"),
    instruction: str = typer.Option("", "--instruction", help="Natural language extraction instruction"),
    css_schema: str = typer.Option("", "--css-schema", help="CSS schema JSON string for selector-based extraction"),
    llm_key: str = typer.Option("", "--llm-key", envvar="LLM_API_KEY", help="LLM API key (or set LLM_API_KEY env var)"),
    provider: str = typer.Option("gemini/gemini-2.0-flash", "--provider", help="LiteLLM provider string"),
    js: bool = typer.Option(False, "--js", help="Enable JS rendering"),
) -> None:
    """Extract structured data — LLM-based or CSS selector-based fallback."""
    try:
        schema_dict: dict = json.loads(schema)
    except json.JSONDecodeError:
        typer.echo(f"Error: --schema is not valid JSON: {schema}", err=True)
        raise SystemExit(1)

    css_schema_dict: dict | None = None
    if css_schema:
        try:
            css_schema_dict = json.loads(css_schema)
        except json.JSONDecodeError:
            typer.echo(f"Error: --css-schema is not valid JSON: {css_schema}", err=True)
            raise SystemExit(1)

    req = ExtractRequest(
        url=url,
        **{"schema": schema_dict},
        instruction=instruction,
        llm_provider=provider,
        css_schema=css_schema_dict,
        use_js=js,
    )
    resp = asyncio.run(_extract(req, llm_api_key=llm_key))
    _die(resp)


@app.command()
def screenshot(
    url: str = typer.Argument(..., help="URL to screenshot"),
    full_page: bool = typer.Option(True, "--full-page/--viewport-only", help="Capture full scrollable page"),
    width: int = typer.Option(1280, "--width", help="Viewport width in px"),
    height: int = typer.Option(800, "--height", help="Viewport height in px"),
    out: str = typer.Option("", "--out", help="Save base64 PNG to this file path instead of stdout"),
) -> None:
    """Capture a full-page screenshot and return base64 PNG."""
    req = ScreenshotRequest(url=url, full_page=full_page, viewport_width=width, viewport_height=height, use_js=True)
    resp = asyncio.run(_screenshot(req))
    if out and resp.screenshot_base64:
        import base64
        with open(out, "wb") as f:
            f.write(base64.b64decode(resp.screenshot_base64))
        typer.echo(f"Screenshot saved to {out} ({resp.width}x{resp.height}px)")
    else:
        _die(resp)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind"),
    port: int = typer.Option(8421, "--port", envvar="PORT", help="Port to listen on"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
) -> None:
    """Start the Scout HTTP server."""
    import uvicorn
    uvicorn.run("scout.api.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
