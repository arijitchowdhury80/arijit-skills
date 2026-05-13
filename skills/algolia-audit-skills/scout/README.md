# Scout — Web Scraper and Crawler for Claude Code

Scout is a self-hosted web scraping platform that turns any public website into clean, structured content. It wraps [Crawl4AI](https://github.com/unclecode/crawl4ai) + Playwright into a local HTTP server, and the `SKILL.md` in this directory teaches Claude when and how to use it.

Unlike WebFetch or raw curl, Scout handles:
- **JS-rendered pages** — React/Vue/Angular SPAs, lazy-loaded content
- **Stealth mode** — bypasses bot detection (Cloudflare, Akamai, Imperva)
- **PDF extraction** — returns PDF text as clean markdown
- **Sitemap discovery** — maps a full domain before scraping, no URL guessing
- **Multi-page crawl** — BFS crawl of entire site sections in one call
- **Structured extraction** — pull specific fields via CSS selectors or LLM

---

## What You Can Do With Scout

| Task | Endpoint | Example |
|---|---|---|
| Scrape a single page | `/scrape` | Product page, About page, blog post |
| Discover all URLs on a site | `/map` | Find all product category URLs |
| Crawl an entire section | `/crawl` | All pages under `/products` or `/blog` |
| Extract structured fields | `/extract` | Pull name, price, SKU from product pages |
| Screenshot a page | `/screenshot` | Visual capture for reference or debugging |

**Example use cases:**
- Scrape a retailer's product catalog to build an Algolia demo index
- Extract company leadership, job listings, or investor info for research
- Crawl documentation sites and turn them into searchable content
- Pull product names, descriptions, and prices from any e-commerce site
- Map a competitor's site structure before a deep analysis

---

## Prerequisites

- Python 3.11+
- pip
- Claude Code CLI

---

## Install

Everything — server code, skill file, and config — lives in this directory. One clone, four steps.

### Step 1 — Clone and install

```bash
git clone https://github.com/arijitchowdhury80/algolia-claude-skills.git
cd algolia-claude-skills/skills/algolia-audit-skills/scout
pip install -e .
playwright install chromium
```

### Step 2 — Configure (optional for local use)

```bash
cp .env.example .env
```

The defaults work for local development — no changes required. Only edit `.env` if you want to:
- Change the port (default: `8421`)
- Set a custom `SCOUT_API_KEY` before sharing the server over a network
- Add an `LLM_API_KEY` to use the LLM extraction mode on `/extract`

### Step 3 — Install the Claude skill

```bash
bash install-skill.sh
```

This copies `SKILL.md` → `~/.claude/commands/scout.md`. Restart Claude Code (or open a new session) to load it.

### Step 4 — Start the server

```bash
scout serve
```

Verify:
```bash
curl -s http://localhost:8421/health
# → {"status":"ok"}
```

---

## Authentication

Scout uses a simple API key to protect its endpoints. The default key for local development is `dev-key` — no setup needed. Include it in every request:

```
-H "X-API-Key: dev-key"
```

If you change `SCOUT_API_KEY` in `.env`, use that value instead.

---

## Core Pattern: Map → Filter → Scrape

For most tasks, this is the right flow:

```
1. Map the domain   →  get all URLs
2. Filter the list  →  find the section you need
3. Scrape those URLs
```

Don't guess URLs. Map first — site structures vary wildly.

```bash
# Step 1: discover the site
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://example.com", "max_pages": 200}'

# Step 2: scrape a specific page from the returned urls[]
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://example.com/products/category", "use_js": true}'
```

---

## API Reference

### `GET /health` — liveness check (no auth)
```bash
curl http://localhost:8421/health
```

---

### `POST /scrape` — fetch one page as markdown

```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://example.com/page",
    "use_js": false,
    "stealth": false,
    "wait_for": "",
    "timeout_ms": 30000,
    "formats": ["markdown"]
  }'
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | string | required | Page to fetch |
| `use_js` | bool | `false` | Enable Playwright JS rendering |
| `stealth` | bool | `false` | Enable bot detection bypass |
| `wait_for` | string | `""` | CSS selector or JS expr to wait for before capturing |
| `timeout_ms` | int | `30000` | Page load timeout |
| `formats` | list | `["markdown"]` | `"markdown"` \| `"raw_html"` \| `"screenshot"` |

Returns: `{ success, url, markdown, links[], metadata: { title, word_count, ... } }`

---

### `POST /map` — discover all URLs on a domain

```bash
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://example.com",
    "max_pages": 200,
    "url_pattern": "/products"
  }'
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | string | required | Domain to map |
| `max_pages` | int | `100` | Max URLs to return |
| `url_pattern` | string | `""` | Substring filter on returned URLs |
| `stealth` | bool | `false` | Enable stealth mode |

Returns: `{ success, urls[], total }`

---

### `POST /crawl` — BFS multi-page crawl

```bash
curl -s --max-time 120 -X POST http://localhost:8421/crawl \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://example.com/products",
    "max_depth": 2,
    "max_pages": 50,
    "url_pattern": "/products",
    "use_js": false
  }'
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | string | required | Start URL |
| `max_depth` | int | `2` | BFS depth limit |
| `max_pages` | int | `10` | Max pages to crawl |
| `url_pattern` | string | `""` | Only follow URLs matching this substring |
| `use_js` | bool | `false` | Enable JS rendering per page |

Returns: `{ success, pages: [{ url, markdown, metadata }], total_pages }`

---

### `POST /extract` — structured field extraction

**CSS extraction** (fast, no API key needed, requires known DOM structure):
```bash
curl -s -X POST http://localhost:8421/extract \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://example.com/product/123",
    "css_schema": {
      "name": "product",
      "baseSelector": ".product-card",
      "fields": [
        {"name": "title",       "selector": "h1.product-title", "type": "text"},
        {"name": "price",       "selector": ".price",           "type": "text"},
        {"name": "description", "selector": ".product-desc",    "type": "text"},
        {"name": "sku",         "selector": "[data-sku]",       "type": "attribute", "attribute": "data-sku"}
      ]
    }
  }'
```

**LLM extraction** (works on any page, requires `LLM_API_KEY` in `.env`):
```bash
curl -s -X POST http://localhost:8421/extract \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://example.com/product/123",
    "schema": {
      "type": "object",
      "properties": {
        "title":       {"type": "string"},
        "price":       {"type": "string"},
        "description": {"type": "string"}
      }
    },
    "instruction": "Extract the product title, price, and description"
  }'
```

Returns: `{ success, data: { ... }, markdown }`

---

### `POST /screenshot` — full-page PNG

```bash
curl -s -X POST http://localhost:8421/screenshot \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://example.com"}'
# → base64-encoded PNG in response.screenshot_base64
```

---

## CLI

```bash
scout serve                                       # start server (port 8421)
scout serve --port 9000                           # custom port
scout scrape https://example.com/page             # single page → markdown
scout map https://example.com --pages 200         # URL discovery
scout crawl https://example.com/products \        # multi-page crawl
  --depth 2 --pages 50
scout extract https://example.com/product/123 \   # LLM structured extraction
  --llm-key $LLM_API_KEY
scout screenshot https://example.com              # visual capture
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Connection refused` on port 8421 | Run `scout serve` |
| HTTP 403 | Add `-H "X-API-Key: dev-key"` (or your custom key) |
| Empty or sparse markdown | Add `"use_js": true` — page requires JavaScript |
| Page content not fully loaded | Add `"wait_for": ".selector"` to wait for a DOM element |
| Crawl times out | Reduce `max_pages`, or set `"use_js": false` for static pages |
| `"No LLM API key"` on `/extract` | Use `css_schema` instead, or set `LLM_API_KEY` in `.env` |

---

## Attribution

Scout is built on [Crawl4AI](https://github.com/unclecode/crawl4ai) by UncleCode, licensed under Apache 2.0.
