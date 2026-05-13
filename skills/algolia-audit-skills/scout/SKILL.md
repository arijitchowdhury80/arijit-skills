---
name: scout
description: Use Scout to scrape and crawl any public website and return clean markdown content. Scout is a self-hosted web scraping platform at http://localhost:8421. Use it instead of WebFetch or raw curl whenever you need to: scrape a page that requires JavaScript rendering, crawl multiple pages of a site section, extract structured fields (product names, prices, descriptions) via CSS selectors or LLM, discover all URLs on a domain before scraping, bypass bot detection on pages that block basic fetch, or extract text from a PDF URL. Invoke Scout for any web content task — product catalog extraction, company research, documentation scraping, demo data preparation, or any situation where WebFetch returns empty or broken content.
layer: 0-infrastructure
type: server-backed
server_port: 8421
health_check: "curl -s http://localhost:8421/health"
start_command: "scout serve"
requires_install: true
version: 1.2
---

# Scout — Web Scraper and Crawler

Scout is a self-hosted web scraping platform that turns any public website into clean, structured content. It runs locally at `http://localhost:8421` and wraps Crawl4AI with Playwright.

**Always check health first:**
```bash
curl -s http://localhost:8421/health
```
If not running: `scout serve` (see [README.md](README.md) for install steps)

**Auth:** Every endpoint except `/health` requires `X-API-Key: dev-key` (the default — no setup needed for local use).

---

## When to Use Scout

Use Scout instead of WebFetch or raw curl when:
- The page requires JavaScript to render content (SPAs, lazy-loaded products, dynamic tables)
- You need to crawl multiple pages of a section in one call
- You need to extract structured fields (name, price, SKU) from a page
- You need to discover all URLs on a domain before deciding what to scrape
- The page blocks basic fetch requests (bot detection)
- The URL points to a PDF and you need the text content

---

## Core Pattern: Map → Filter → Scrape

```bash
# Step 1: discover the site structure
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://example.com", "max_pages": 200}'

# Step 2: from the urls[] list, identify the section you need

# Step 3: scrape it
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://example.com/products", "use_js": true}'
```

Don't guess URLs — sites vary wildly. Map first, then scrape what you need.

---

## Playbooks

### Scrape a single page

```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://example.com/page", "use_js": true}'
```

If the page content is not fully loaded, wait for a DOM element:
```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://example.com/page", "use_js": true, "wait_for": ".product-grid"}'
```

If markdown conversion loses structure (e.g. product cards, team member grids), request raw HTML and parse it directly:
```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://example.com/page", "use_js": true, "formats": ["raw_html"]}'
```

---

### Crawl a site section (multiple pages)

```bash
curl -s --max-time 120 -X POST http://localhost:8421/crawl \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://example.com/products",
    "max_depth": 2,
    "max_pages": 50,
    "url_pattern": "/products"
  }'
```

Returns all pages as `{ pages: [{ url, markdown, metadata }] }`.

---

### Extract structured fields (product catalog, demo data)

**CSS extraction** — fast, no LLM needed, requires you know the DOM structure:
```bash
curl -s -X POST http://localhost:8421/extract \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://example.com/product/123",
    "css_schema": {
      "name": "product",
      "baseSelector": ".product-card",
      "fields": [
        {"name": "title",       "selector": "h1",         "type": "text"},
        {"name": "price",       "selector": ".price",     "type": "text"},
        {"name": "description", "selector": ".desc",      "type": "text"},
        {"name": "sku",         "selector": "[data-sku]", "type": "attribute", "attribute": "data-sku"}
      ]
    }
  }'
```

**LLM extraction** — works on any page without knowing the DOM (requires `LLM_API_KEY` in `.env`):
```bash
curl -s -X POST http://localhost:8421/extract \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{
    "url": "https://example.com/product/123",
    "schema": {"type": "object", "properties": {"title": {"type": "string"}, "price": {"type": "string"}}},
    "instruction": "Extract the product title and price"
  }'
```

---

### Discover all URLs on a domain

```bash
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://example.com", "max_pages": 300, "url_pattern": "/products"}'
```

Returns `{ urls: [...], total }`. Use `url_pattern` to filter to a specific section.

---

### Scrape a PDF

Pass the direct PDF URL to `/scrape` — returns the extracted text as markdown:
```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://example.com/report.pdf"}'
```

---

### Screenshot a page

```bash
curl -s -X POST http://localhost:8421/screenshot \
  -H "Content-Type: application/json" -H "X-API-Key: dev-key" \
  -d '{"url": "https://example.com"}'
```

Returns `{ screenshot_base64: "..." }` — a base64 PNG of the full page.

---

## API Quick Reference

| Endpoint | Use case | Timeout |
|---|---|---|
| `GET /health` | Liveness check (no auth) | instant |
| `POST /scrape` | One page → markdown + links + metadata | 45s |
| `POST /map` | Discover all URLs on a domain | 60s |
| `POST /crawl` | BFS multi-page crawl of a section | 120s |
| `POST /extract` | Structured fields via CSS selectors or LLM | 60s |
| `POST /screenshot` | Full-page PNG (base64) | 30s |

**Error reference:**

| Error | Fix |
|---|---|
| `Connection refused` | Run `scout serve` |
| HTTP 403 | Add `-H "X-API-Key: dev-key"` |
| HTTP 422 | Malformed JSON body |
| Sparse/empty markdown | Add `"use_js": true` |
| Content not fully loaded | Add `"wait_for": ".selector"` |
| `"No LLM API key"` on `/extract` | Use `css_schema` instead, or set `LLM_API_KEY` in `.env` |

---

## CLI

```bash
scout serve                                         # start the server
scout serve --port 9000                             # custom port
scout scrape https://example.com/page               # single page
scout map https://example.com --pages 200           # URL discovery
scout crawl https://example.com/products \          # multi-page
  --depth 2 --pages 50
scout extract https://example.com/product/123 \     # structured extraction
  --llm-key $LLM_API_KEY
scout screenshot https://example.com                # visual capture
```
