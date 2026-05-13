"""Scout core types — the contract every endpoint fulfils.

All request/response models are defined here. Nothing outside this file
defines the API contract. Change here first; implementations follow.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ScoutFormats(str, Enum):
    MARKDOWN = "markdown"
    RAW_HTML = "raw_html"
    SCREENSHOT = "screenshot"


class ScoutMetadata(BaseModel):
    model_config = {"frozen": True}

    url: str
    crawled_at: str
    title: str = ""
    description: str = ""
    language: str = ""
    word_count: int = 0
    token_estimate: int = 0


# ---------------------------------------------------------------------------
# /scrape
# ---------------------------------------------------------------------------


class ScrapeRequest(BaseModel):
    url: str
    formats: list[ScoutFormats] = [ScoutFormats.MARKDOWN]
    use_js: bool = False
    wait_for: str = ""
    timeout_ms: int = 30000
    stealth: bool = False  # enable_stealth + simulate_user + magic in Crawl4AI


class ScrapeResponse(BaseModel):
    success: bool
    url: str
    markdown: str = ""
    raw_html: str = ""
    screenshot_base64: str = ""
    links: list[str] = Field(default_factory=list)
    metadata: ScoutMetadata
    error: str = ""
    duration_ms: int


# ---------------------------------------------------------------------------
# /crawl
# ---------------------------------------------------------------------------


class CrawlRequest(BaseModel):
    url: str
    max_depth: int = 2
    max_pages: int = 10
    url_pattern: str = ""
    include_external: bool = False
    use_js: bool = False
    timeout_ms: int = 60000
    stealth: bool = False


class CrawlPage(BaseModel):
    url: str
    markdown: str = ""
    metadata: ScoutMetadata
    success: bool
    error: str = ""


class CrawlResponse(BaseModel):
    success: bool
    start_url: str
    pages: list[CrawlPage] = Field(default_factory=list)
    total_pages: int
    error: str = ""
    duration_ms: int


# ---------------------------------------------------------------------------
# /extract
# ---------------------------------------------------------------------------


class ExtractRequest(BaseModel):
    model_config = {"populate_by_name": True}

    url: str
    extraction_schema: dict = Field(default_factory=dict, alias="schema")
    instruction: str = ""
    llm_provider: str = "gemini/gemini-2.0-flash"
    css_schema: dict | None = None  # {baseSelector, fields: [{name, selector, type}]}
    use_js: bool = False
    timeout_ms: int = 45000


class ExtractResponse(BaseModel):
    success: bool
    url: str
    data: dict = Field(default_factory=dict)
    markdown: str = ""
    metadata: ScoutMetadata
    error: str = ""
    duration_ms: int


# ---------------------------------------------------------------------------
# /map
# ---------------------------------------------------------------------------


class MapRequest(BaseModel):
    url: str
    max_pages: int = 100
    url_pattern: str = ""
    include_external: bool = False
    stealth: bool = False


class MapResponse(BaseModel):
    success: bool
    start_url: str
    urls: list[str] = Field(default_factory=list)
    total: int
    error: str = ""
    duration_ms: int


# ---------------------------------------------------------------------------
# /screenshot
# ---------------------------------------------------------------------------


class ScreenshotRequest(BaseModel):
    url: str
    full_page: bool = True
    viewport_width: int = 1280
    viewport_height: int = 800
    wait_for: str = ""
    use_js: bool = True


class ScreenshotResponse(BaseModel):
    success: bool
    url: str
    screenshot_base64: str = ""
    width: int
    height: int
    error: str = ""
    duration_ms: int
