# Scout — Web Intelligence Skill for Claude Code

Scout is a self-hosted web intelligence platform that gives Claude the ability to crawl real company websites. It wraps [Crawl4AI](https://github.com/unclecode/crawl4ai) + Playwright into a local FastAPI server, and the `SKILL.md` in this directory teaches Claude when and how to use it.

Unlike WebFetch or raw curl, Scout handles:
- **JS-rendered pages** — team pages, dynamic job listings, SPA-based IR sites
- **Stealth mode** — bypasses bot detection (Cloudflare, Akamai, Imperva)
- **PDF extraction** — annual reports, investor decks, whitepapers as markdown
- **Sitemap discovery** — finds the right URL before scraping, no guessing

---

## What Scout Can Fetch

| Intelligence Type | What you get | Typical URL patterns |
|---|---|---|
| **About / Company** | Mission, HQ, founding year, company size | `/about`, `/company`, `/who-we-are` |
| **Executive Team** | C-suite names + titles | `/team`, `/leadership`, `/about/team` |
| **Hiring / Open Roles** | Positions, departments, locations | `/careers`, `/jobs`, `/join-us` |
| **Investor Relations** | IR page, earnings dates, SEC filings | `/investors`, `/ir` |
| **Reports & PDFs** | Annual reports, investor decks, whitepapers | Any `.pdf` URL |

---

## Prerequisites

- Python 3.11+
- pip
- Claude Code CLI

---

## Install

Scout has two components to install: the **server** (the FastAPI app that does the crawling) and the **skill** (the markdown file that teaches Claude to use it).

### Step 1 — Get the Scout server

> **Note:** The Scout server repository URL will be provided by the maintainer. Replace `[SCOUT_SERVER_REPO_URL]` with the actual repo URL.

```bash
git clone [SCOUT_SERVER_REPO_URL]
cd Scout
pip install -e .
```

Install Playwright's browser (one-time):
```bash
playwright install chromium
```

### Step 2 — Configure

```bash
cp .env.example .env
```

Edit `.env` and set your API key:
```
SCOUT_API_KEY=your-secret-key
LLM_API_KEY=                    # optional — only needed for /extract with LLM mode
PORT=8421
```

> For local single-user development, the default `SCOUT_API_KEY=dev-key` works fine. Use a real secret before sharing the server over any network.

### Step 3 — Install the Claude skill

From the root of this skills repository:
```bash
cp skills/algolia-audit-skills/scout/SKILL.md ~/.claude/commands/scout.md
```

Restart Claude Code (or open a new session) to load the skill.

### Step 4 — Start the server

```bash
scout serve
```

Verify it's running:
```bash
curl -s http://localhost:8421/health
# → {"status":"ok"}
```

---

## Using Scout

Once the server is running and the skill is installed, Claude routes to Scout automatically when you ask for any of the five supported intelligence types. No explicit invocation needed.

**Examples:**
```
find the leadership team at company.com
get the investor relations page for company.com
what roles is company.com hiring for?
scrape the careers section at company.com
get their annual report PDF
```

You can also call the Scout API directly:

### Map — discover all URLs on a domain
```bash
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com", "max_pages": 300}'
```

### Scrape — fetch one page as clean markdown
```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/about/leadership", "use_js": true}'
```

### Crawl — BFS multi-page crawl
```bash
curl -s --max-time 120 -X POST http://localhost:8421/crawl \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/careers", "max_depth": 2, "max_pages": 30}'
```

### Extract — structured data via LLM or CSS selectors
```bash
# CSS extraction (no API key needed)
curl -s -X POST http://localhost:8421/extract \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{
    "url": "https://company.com/team",
    "css_schema": {
      "name": "team",
      "baseSelector": ".team-member",
      "fields": [
        {"name": "name", "selector": "h3", "type": "text"},
        {"name": "title", "selector": "p.role", "type": "text"}
      ]
    }
  }'
```

### Screenshot — full-page PNG
```bash
curl -s -X POST http://localhost:8421/screenshot \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com"}'
# → base64-encoded PNG in response
```

---

## CLI

The Scout CLI calls modes directly without starting the HTTP server:

```bash
scout serve                                       # start HTTP server (port 8421)
scout serve --port 9000                           # custom port
scout scrape https://company.com/about            # single page scrape
scout map https://company.com --pages 200         # URL discovery
scout crawl https://company.com/careers \         # multi-page crawl
  --depth 2 --pages 30
scout extract https://company.com/team \          # structured extraction
  --llm-key $LLM_API_KEY
scout screenshot https://company.com              # visual capture
```

---

## API Reference

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/health` | GET | none | Liveness check |
| `/scrape` | POST | required | Fetch one page → markdown + links + metadata |
| `/map` | POST | required | Discover all URLs on a domain via sitemap/BFS |
| `/crawl` | POST | required | BFS multi-page crawl from a start URL |
| `/extract` | POST | required | Structured data via LLM schema or CSS selectors |
| `/screenshot` | POST | required | Full-page screenshot → base64 PNG |

### Key request parameters

**`/scrape`**
```json
{
  "url": "https://company.com/page",
  "use_js": false,        // enable Playwright JS rendering
  "stealth": false,       // enable bot detection bypass
  "wait_for": "",         // CSS selector or JS expr to wait for
  "timeout_ms": 30000,
  "formats": ["markdown"] // "markdown" | "raw_html" | "screenshot"
}
```

**`/map`**
```json
{
  "url": "https://company.com",
  "max_pages": 100,
  "url_pattern": "",      // substring filter on discovered URLs
  "stealth": false
}
```

**`/crawl`**
```json
{
  "url": "https://company.com/section",
  "max_depth": 2,
  "max_pages": 10,
  "url_pattern": "",
  "use_js": false,
  "timeout_ms": 60000
}
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Connection refused` on port 8421 | Run `scout serve` to start the server |
| HTTP 403 on any endpoint | Add `-H "X-API-Key: $SCOUT_API_KEY"` — check your `.env` |
| Empty or sparse markdown | Add `"use_js": true` — page requires JavaScript |
| Crawl times out | Reduce `max_pages`, or set `"use_js": false` for static pages |
| `"No LLM API key"` on `/extract` | Use `css_schema` instead, or set `LLM_API_KEY` in `.env` |
| Team page names missing | Use `"formats": ["raw_html"]` and parse card markup directly |

---

## How the Skill Routes

The `SKILL.md` file instructs Claude to prefer Scout over WebFetch or curl whenever the intelligence target is one of the five supported types. The routing logic is:

1. Claude receives a request involving company research
2. The skill triggers if the target is: About, Leadership, Hiring, IR, or PDFs
3. Claude calls `GET /health` first — if Scout is down, it falls back to WebFetch with a warning
4. Claude maps the domain, filters URLs, then scrapes the relevant sections
5. Results are returned as structured markdown

---

## Attribution

Scout is built on [Crawl4AI](https://github.com/unclecode/crawl4ai) by UncleCode, licensed under Apache 2.0.
