# Scout — Architecture

## System Overview

Scout is three layers: a **Claude skill** that routes intent, a **FastAPI server** that exposes five HTTP endpoints, and a **Crawl4AI + Playwright engine** that does the crawling.

```mermaid
graph TD
    User["👤 User / Claude Code"]

    subgraph Skill["Skill Layer  (~/.claude/commands/scout.md)"]
        Router["Skill Router\nFires on: About · Leadership · Hiring · IR · PDFs\nPattern: Map → Filter → Scrape"]
    end

    subgraph Server["Scout Server  (localhost:8421)"]
        Auth["AuthMiddleware\nX-API-Key validation"]
        Dispatcher["ScoutCrawler\nRequest dispatcher"]

        subgraph Endpoints["HTTP Endpoints"]
            EP_Health["GET /health\n(no auth)"]
            EP_Scrape["POST /scrape\nOne page → markdown"]
            EP_Map["POST /map\nURL discovery"]
            EP_Crawl["POST /crawl\nBFS multi-page"]
            EP_Extract["POST /extract\nStructured data"]
            EP_Screenshot["POST /screenshot\nFull-page PNG"]
        end
    end

    subgraph Engine["Crawl4AI + Playwright"]
        BrowserConfig["BrowserConfig\nheadless · JS toggle · stealth"]
        Filter["PruningContentFilter\nthreshold=0.4\nstrips nav/footer noise"]
        MdGen["DefaultMarkdownGenerator\nfit_markdown output"]
        Browser["Playwright Browser\nChromium · stealth mode\nbot detection bypass"]
    end

    subgraph Web["Target Websites"]
        About["About / Company pages"]
        Leadership["Leadership / Team pages"]
        Careers["Careers / Jobs pages"]
        IR["Investor Relations pages"]
        PDFs["PDF documents"]
    end

    User -->|"request about About · Leadership\nHiring · IR · PDF"| Router
    Router -->|"curl POST with X-API-Key"| Auth
    Auth --> Dispatcher

    Dispatcher --> EP_Scrape
    Dispatcher --> EP_Map
    Dispatcher --> EP_Crawl
    Dispatcher --> EP_Extract
    Dispatcher --> EP_Screenshot

    EP_Scrape & EP_Crawl & EP_Map & EP_Screenshot & EP_Extract --> BrowserConfig
    BrowserConfig --> Browser
    Browser -->|"rendered HTML"| Filter
    Filter --> MdGen
    MdGen -->|"fit_markdown + links[]"| Dispatcher

    EP_Map -->|"discovers URLs for"| About & Leadership & Careers & IR & PDFs
    EP_Scrape -->|"fetches content from"| About & Leadership & Careers & IR & PDFs
    EP_Crawl -->|"deep crawls"| Careers
    EP_Extract -->|"structured fields from"| Leadership
```

---

## Scrape Request — Sequence Diagram

```mermaid
sequenceDiagram
    participant U as User / Claude
    participant SK as Skill (scout.md)
    participant API as Scout Server :8421
    participant C4AI as Crawl4AI
    participant PW as Playwright

    U->>SK: "Find the leadership team at company.com"

    SK->>API: POST /map {"url": "company.com", "max_pages": 100}
    API->>API: validate X-API-Key
    API->>C4AI: map_urls()
    C4AI->>PW: fetch robots.txt → sitemap.xml
    PW-->>C4AI: URL list
    C4AI-->>API: MapResponse {urls: [...]}
    API-->>SK: urls[] including /about/leadership

    SK->>API: POST /scrape {"url": "/about/leadership", "use_js": true}
    API->>API: validate X-API-Key
    API->>C4AI: scrape()
    C4AI->>PW: launch headless Chromium
    PW->>PW: render JS, wait for DOM
    PW-->>C4AI: full rendered HTML
    C4AI->>C4AI: PruningContentFilter (threshold=0.4)
    C4AI->>C4AI: DefaultMarkdownGenerator → fit_markdown
    C4AI-->>API: CrawlResult {markdown, links, metadata}
    API-->>SK: ScrapeResponse
    SK-->>U: "Executive Team: CEO Jane Smith, CTO John Doe..."
```

---

## Server File Structure

```
Scout/
├── scout/
│   ├── api/
│   │   ├── main.py             ← FastAPI app entry point + lifespan startup
│   │   ├── config.py           ← Settings loaded from .env
│   │   │                         SCOUT_API_KEY (default: dev-key)
│   │   │                         PORT (default: 8421)
│   │   │                         LLM_API_KEY (optional, for /extract)
│   │   ├── deps.py             ← get_crawler() DI factory
│   │   ├── middleware/
│   │   │   └── auth.py         ← API key gate (all endpoints except /health)
│   │   └── routers/
│   │       ├── health.py       ← GET /health
│   │       ├── scrape.py       ← POST /scrape
│   │       ├── map.py          ← POST /map
│   │       ├── crawl.py        ← POST /crawl
│   │       ├── extract.py      ← POST /extract
│   │       └── screenshot.py   ← POST /screenshot
│   ├── core/
│   │   ├── crawler.py          ← ScoutCrawler — thin dispatcher
│   │   ├── types.py            ← Pydantic request/response models (source of truth)
│   │   └── modes/
│   │       ├── scrape.py       ← single page fetch via Crawl4AI
│   │       ├── map.py          ← URL discovery via sitemap + BFS
│   │       ├── crawl.py        ← BFS multi-page crawl
│   │       ├── extract.py      ← LLM/CSS structured extraction
│   │       └── screenshot.py   ← Playwright visual capture
│   ├── cli.py                  ← scout serve / scrape / map / crawl / extract / screenshot
│   └── skill/
│       └── scout.md            ← canonical skill (source of truth for this file)
├── .env                        ← your local config (not committed)
├── .env.example                ← template
├── install-skill.sh            ← copies skill → ~/.claude/commands/scout.md
├── pyproject.toml              ← pip install -e .
└── tests/
    ├── unit/                   ← mocked, fast
    └── integration/            ← live network + browser
```

---

## Key Design Decisions

**Why a local server instead of a Python library called directly?**
Claude Code calls tools via Bash. A local HTTP server is the cleanest interface — it works the same way whether Claude calls it via curl, the CLI calls it directly, or an external script calls it. No Python import path issues, no async runtime conflicts.

**Why Crawl4AI instead of raw Playwright/Requests?**
Crawl4AI handles the messy middle layer: JS rendering, content pruning (`PruningContentFilter`), and markdown generation. Scout adds auth, request routing, Pydantic contracts, and stealth configuration on top.

**Why is `/map` separate from `/scrape`?**
Discovering URLs is cheap (sitemap fetch + BFS). Scraping is expensive (full browser render per page). Separating the two lets Claude pick exactly which pages to scrape rather than downloading everything blindly.

**Why is `stealth` opt-in instead of always-on?**
Stealth mode (`enable_stealth + simulate_user + magic` in Crawl4AI) adds latency and memory overhead. Static pages don't need it. The skill enables it selectively for JS-heavy and bot-protected pages.

---

## Security Notes

- All endpoints except `GET /health` require a valid `X-API-Key` header.
- The default `dev-key` is for local development only. Set `SCOUT_API_KEY` to a real secret before exposing the server on any shared or network-accessible interface.
- Scout does not persist scraped content to disk. All data is returned in the HTTP response and discarded after the request completes.
- Scout only fetches publicly accessible content. It does not follow authentication redirects or submit credentials.
