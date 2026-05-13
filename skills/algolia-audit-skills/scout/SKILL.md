---
name: scout
description: Use Scout to scrape, crawl, extract, screenshot, or prepare Algolia-ready product records from public websites. Scout is a standalone Crawl4AI-based package that can run as a CLI or a local HTTP service at http://localhost:8421. Invoke Scout when web content needs JavaScript rendering, sitemap discovery, multi-page crawling, structured extraction, PDF text extraction, product catalog crawling, or durable run artifacts. Use it instead of raw curl/WebFetch for company research, careers/investor pages, product catalogs, and demo data preparation.
layer: 0-infrastructure
type: server-backed
server_port: 8421
health_check: "curl -s http://localhost:8421/health"
start_command: "scout serve"
requires_install: true
version: 2.0
---

# Scout

Scout is a standalone web scraping and product intelligence platform built on
Crawl4AI. This skill is only the agent playbook. Scout also works directly from
terminal, Docker, HTTP, and Python.

## Health Check

Always check whether the local service is running before HTTP calls:

```bash
curl -s http://localhost:8421/health
```

If it is not running:

```bash
scout serve
```

All HTTP endpoints except `/` and `/health` require:

```text
X-API-Key: dev-key
```

Use `$SCOUT_API_KEY` instead when configured.

## When To Use Scout

Use Scout for:

- JS-rendered pages that basic fetch tools miss
- URL discovery before scraping
- Multi-page section crawls
- PDFs that need text extraction
- Product catalog crawling and Algolia-ready records
- Company pages: about, leadership, careers, investor relations
- Durable run artifacts instead of hidden `/tmp` files

## Front Doors

### CLI

Use CLI for standalone terminal work. It does not require `scout serve`.

```bash
scout scrape https://example.com/about
scout map https://example.com --pages 200
scout crawl https://example.com/careers --depth 2 --pages 30
scout products "men shirts" --site example.com --output-dir ./scout-runs/men-shirts
```

### HTTP

Use HTTP when another tool or agent needs a stable local service.

```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${SCOUT_API_KEY:-dev-key}" \
  -d '{"url": "https://example.com/about", "use_js": true}'
```

## Core Pattern

For most web research:

1. Map the domain.
2. Filter URLs to the relevant section.
3. Scrape or crawl those URLs.
4. Preserve source URLs in the final answer.

```bash
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${SCOUT_API_KEY:-dev-key}" \
  -d '{"url": "https://company.com", "max_pages": 200}'
```

## Product Catalog To Algolia

Use `/products` or `scout products` when the user asks for products, catalog
records, demo data, PDP/search data, or Algolia indexing prep.

Prefer explicit target sites. If the user says only "Scout Estee Lauder", use
`--site esteelauder.com` if obvious; otherwise ask for the target domain.

CLI:

```bash
scout products "top products" \
  --site esteelauder.com \
  --limit-per-category 10 \
  --max-categories 10 \
  --output-dir ./scout-runs/estee-lauder
```

HTTP:

```bash
curl -s --max-time 180 -X POST http://localhost:8421/products \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${SCOUT_API_KEY:-dev-key}" \
  -d '{
    "query": "top products",
    "site": "esteelauder.com",
    "limit_per_category": 10,
    "max_categories": 10,
    "output_dir": "./scout-runs/estee-lauder",
    "persist": true
  }'
```

Product runs write:

```text
manifest.json
urls.json
extracted/products.raw.jsonl
algolia/products.json
algolia/products.ndjson
algolia/settings.json
report.md
```

Use `algolia/products.json` for inspection and `algolia/products.ndjson` for
bulk indexing pipelines.

## Company Intelligence Playbooks

### About / Company

Map first, then scrape likely about pages:

```bash
scout map https://company.com --pages 200 --pattern about
scout scrape https://company.com/about --js
```

Extract mission, founding, headquarters, product summary, and source URL.

### Leadership

```bash
scout map https://company.com --pages 200
scout scrape https://company.com/about/leadership --js
```

If markdown is sparse, request raw HTML:

```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${SCOUT_API_KEY:-dev-key}" \
  -d '{"url": "https://company.com/about/leadership", "use_js": true, "formats": ["raw_html"]}'
```

### Careers

```bash
scout crawl https://company.com/careers --depth 2 --pages 30 --pattern careers --js
```

### Investor Relations

```bash
scout map https://company.com --pages 200 --pattern investor
scout scrape https://company.com/investors --js
```

### PDFs

Pass direct PDF URLs to scrape:

```bash
scout scrape https://company.com/reports/annual-report.pdf
```

## Error Handling

| Symptom | Fix |
|---|---|
| Connection refused | Run `scout serve` |
| HTTP 403 | Add `X-API-Key` header |
| Sparse markdown | Retry with `use_js=true` or `--js` |
| Content still missing | Add `wait_for` selector or request raw HTML |
| Product run writes nowhere | Pass `--output-dir` or set `"persist": true` with `output_dir` |

## Answering Users

When returning scraped results, include:

- What Scout command or endpoint was used
- Where artifacts were written, if any
- Source URLs
- Any extraction caveats, such as missing JSON-LD or sparse page content
