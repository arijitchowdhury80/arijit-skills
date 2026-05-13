# Scout — Architecture

## System Overview

Scout is a three-layer system: a **Claude skill** that routes Claude's intent, a **FastAPI server** that exposes five HTTP endpoints, and a **Crawl4AI/Playwright engine** that does the actual crawling.

```mermaid
graph TD
    User["👤 User / Claude Code"]

    subgraph Skill["Claude Skill Layer (~/.claude/commands/scout.md)"]
        SkillRouter["Skill Router\nRoutes to Scout when intent matches\n5 intelligence types"]
    end

    subgraph Server["Scout Server (localhost:8421)"]
        Auth["AuthMiddleware\nX-API-Key validation"]
        ScoutCrawler["ScoutCrawler\nRequest dispatcher"]

        subgraph Endpoints["HTTP Endpoints"]
            EP_Health["GET /health\n(no auth)"]
            EP_Scrape["POST /scrape\nSingle page → markdown"]
            EP_Map["POST /map\nURL discovery via sitemap"]
            EP_Crawl["POST /crawl\nBFS multi-page crawl"]
            EP_Extract["POST /extract\nStructured data (LLM/CSS)"]
            EP_Screenshot["POST /screenshot\nFull-page PNG"]
        end
    end

    subgraph Engine["Crawl4AI + Playwright Engine"]
        BrowserCfg["BrowserConfig\nheadless, JS toggle, stealth"]
        PruningFilter["PruningContentFilter\nthreshold=0.4 — strips nav/footer noise"]
        MdGenerator["DefaultMarkdownGenerator\nclean fit_markdown output"]
        Playwright["Playwright Browser\nChromium, stealth mode\nbot detection bypass"]
    end

    subgraph Intelligence["5 Intelligence Types"]
        About["About / Company\n/about, /company, /who-we-are"]
        Leadership["Executive Team\n/team, /leadership, /about/team"]
        Hiring["Hiring / Roles\n/careers, /jobs, /join-us"]
        IR["Investor Relations\n/investors, /ir"]
        PDFs["Reports & PDFs\n*.pdf direct URLs"]
    end

    subgraph Consumers["PRISM Pipeline Consumers"]
        IntelCompany["algolia-intel-company\nscout_company.py"]
        IntelCompetitors["algolia-intel-competitors\nscout_competitive.py"]
        IntelInvestor["algolia-intel-investor"]
        IntelHiring["algolia-intel-hiring"]
    end

    User -->|"find leadership / get IR / scrape careers"| SkillRouter
    SkillRouter -->|"curl POST"| Auth
    Auth --> ScoutCrawler
    ScoutCrawler --> EP_Scrape
    ScoutCrawler --> EP_Map
    ScoutCrawler --> EP_Crawl
    ScoutCrawler --> EP_Extract
    ScoutCrawler --> EP_Screenshot

    EP_Scrape --> BrowserCfg
    EP_Crawl --> BrowserCfg
    EP_Map --> BrowserCfg
    EP_Screenshot --> BrowserCfg
    EP_Extract --> BrowserCfg

    BrowserCfg --> PruningFilter
    PruningFilter --> MdGenerator
    BrowserCfg --> Playwright

    MdGenerator -->|"fit_markdown + links[]"| EP_Scrape
    Playwright -->|"renders JS, bypasses WAF"| BrowserCfg

    EP_Map -->|"URL list"| About
    EP_Map -->|"URL list"| Leadership
    EP_Map -->|"URL list"| Hiring
    EP_Map -->|"URL list"| IR
    EP_Map -->|"URL list"| PDFs

    IntelCompany -->|"scout_company.py\nAbout + Leadership + Careers + IR"| Server
    IntelCompetitors -->|"scout_competitive.py\nNewsroom scrape → Haiku signals"| Server
    IntelInvestor --> Server
    IntelHiring --> Server
```

---

## Data Flow: Single Scrape Request

```mermaid
sequenceDiagram
    participant C as Claude / User
    participant SK as Skill (scout.md)
    participant API as FastAPI Server
    participant AUTH as AuthMiddleware
    participant CRAW as ScoutCrawler
    participant C4AI as Crawl4AI
    participant PW as Playwright

    C->>SK: "Find the leadership team at company.com"
    SK->>API: POST /map {"url": "company.com", "max_pages": 100}
    API->>AUTH: validate X-API-Key
    AUTH->>CRAW: dispatch map_urls()
    CRAW->>C4AI: sitemap fetch → BFS fallback
    C4AI->>PW: launch headless browser
    PW-->>C4AI: HTML + links
    C4AI-->>CRAW: urls[]
    CRAW-->>API: MapResponse
    API-->>SK: {"urls": [..."/about/leadership", ...]}

    SK->>API: POST /scrape {"url": "/about/leadership", "use_js": true}
    API->>AUTH: validate X-API-Key
    AUTH->>CRAW: dispatch scrape()
    CRAW->>C4AI: AsyncWebCrawler.arun()
    C4AI->>PW: render JS, wait for DOM
    PW-->>C4AI: rendered HTML
    C4AI->>C4AI: PruningContentFilter (threshold=0.4)
    C4AI->>C4AI: DefaultMarkdownGenerator → fit_markdown
    C4AI-->>CRAW: CrawlResult
    CRAW-->>API: ScrapeResponse {markdown, links, metadata}
    API-->>SK: clean markdown + executive cards
    SK-->>C: "Executive Team: CEO Jane Smith, CTO John Doe..."
```

---

## File Structure

```
Scout/                          ← server repo (separate from skills repo)
├── scout/
│   ├── api/
│   │   ├── main.py             ← FastAPI app, lifespan startup
│   │   ├── config.py           ← Settings (SCOUT_API_KEY, PORT=8421)
│   │   ├── deps.py             ← get_crawler() DI factory
│   │   ├── middleware/
│   │   │   └── auth.py         ← API key gate
│   │   └── routers/
│   │       ├── scrape.py       ← POST /scrape
│   │       ├── map.py          ← POST /map
│   │       ├── crawl.py        ← POST /crawl
│   │       ├── extract.py      ← POST /extract
│   │       ├── screenshot.py   ← POST /screenshot
│   │       └── health.py       ← GET /health
│   ├── core/
│   │   ├── crawler.py          ← ScoutCrawler (dispatcher)
│   │   ├── types.py            ← Pydantic contracts (source of truth)
│   │   └── modes/
│   │       ├── scrape.py       ← single page fetch
│   │       ├── map.py          ← URL discovery
│   │       ├── crawl.py        ← BFS multi-page
│   │       ├── extract.py      ← structured extraction
│   │       └── screenshot.py   ← visual capture
│   ├── cli.py                  ← scout serve / scrape / map / crawl
│   └── skill/
│       └── scout.md            ← canonical skill (source of truth)
├── .env.example
├── install-skill.sh            ← copies skill → ~/.claude/commands/
└── pyproject.toml              ← pip install -e .

algolia-claude-skills/          ← this repo
└── skills/algolia-audit-skills/scout/
    ├── SKILL.md                ← distributable skill copy
    ├── README.md               ← install + usage guide (this file's companion)
    └── ARCHITECTURE.md         ← this file
```

---

## Security Notes

- The `AuthMiddleware` rejects all requests (except `/health`) without a valid `X-API-Key` header.
- The default `dev-key` is acceptable for local single-user development. Set a real key in `.env` before exposing the server on any shared or network-accessible interface.
- Scout does not store scraped content to disk — all results are returned in the HTTP response and discarded after the request completes.
- Scout does not follow authentication redirects or submit credentials. It scrapes only publicly accessible content.
