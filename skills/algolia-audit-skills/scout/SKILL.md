---
name: scout
description: Use Scout to gather company intelligence from real websites. Scout is a self-hosted web intelligence platform at http://localhost:8421. It is NOT a general-purpose scraper — it is optimised for specific company intelligence use cases: About page, executive team, hiring openings, investor relations, and PDF reports/presentations. Always invoke Scout instead of WebFetch or raw curl when the goal is any of these five intelligence types, even when the user just says "find the leadership team" or "get their investor deck" without mentioning Scout explicitly. Scout handles JS-rendered pages, stealth mode, PDF extraction, and sitemap discovery that basic fetch tools cannot.
layer: 0-infrastructure
type: server-backed
server_port: 8421
health_check: "curl -s http://localhost:8421/health"
start_command: "scout serve"
requires_install: true
version: 1.1
---

# Scout — Company Intelligence Platform

Scout is a self-hosted web intelligence platform that gives Claude the ability to crawl real company websites with stealth mode, JS rendering, and PDF extraction. It runs locally at `http://localhost:8421` and wraps Crawl4AI with Playwright.

**Always check health first:**
```bash
curl -s http://localhost:8421/health
```
If not running: `scout serve` (see [README.md](README.md) for install steps)

**Auth:** Every endpoint except `/health` requires `X-API-Key: $SCOUT_API_KEY`.

> Local dev default: `SCOUT_API_KEY=dev-key`. Set a real key in `.env` before sharing or deploying.

---

## Full Company Intelligence Profile

When asked to research a company, gather all five intelligence types in one run. **Map once, then scrape everything from that map.**

```bash
# Step 1: discover the site structure
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com", "max_pages": 300}'

# Step 2: from the urls[] list, identify pages for each section:
#   About:      /about, /about-us, /company, /who-we-are
#   Leadership: /team, /leadership, /management, /about/team, /about/leadership
#   Careers:    /careers, /jobs, /join-us
#   Investors:  /investors, /investor-relations, /ir
#   PDFs:       any urls ending in .pdf or /reports/, /presentations/

# Step 3: scrape each identified section
```

**Output structure:**
```markdown
## Company Intelligence — [Company] ([date])

### About
[mission, HQ, founding, size]

### Executive Team
| Name | Title |
|---|---|

### Open Roles
[department: role — location]

### Investor Relations
[IR page URL, stock ticker, earnings dates, SEC filings link]

### Reports & Documents
| Document | Type | URL |
|---|---|---|
```

---

## The Core Pattern: Map → Filter → Scrape

For a single intelligence type:
1. **Map** the domain to discover the URL structure
2. **Filter** the returned `urls[]` to the section you need
3. **Scrape** the relevant pages

Don't guess URLs. Map first — company sites vary wildly (`/team` vs `/about/leadership` vs `/company/management`).

```bash
# Step 1: discover the site
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com", "max_pages": 200}'

# Step 2: scrape the relevant section
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/about/team", "use_js": true}'
```

---

## Intelligence Playbooks

### 1. About / Company Overview

**What you're looking for:** founding story, mission, product description, headquarters, company size.

**Common URL patterns:** `/about`, `/about-us`, `/company`, `/who-we-are`, `/our-story`

```bash
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com", "max_pages": 100, "url_pattern": "/about"}'

curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/about", "use_js": true}'
```

---

### 2. Executive / Leadership Team

**What you're looking for:** C-suite names + titles, board members, VP-level leadership.

**Common URL patterns:** `/team`, `/leadership`, `/management`, `/about/team`, `/about/leadership`

```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/about/leadership", "use_js": true}'
```

Team pages often lose structure when converted to markdown. If content is sparse, request raw HTML and parse name/title card patterns directly:

```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/about/leadership", "use_js": true, "formats": ["raw_html"]}'
```

---

### 3. Hiring / Open Roles

**What you're looking for:** open positions, departments, locations, job descriptions.

**Common URL patterns:** `/careers`, `/jobs`, `/work-with-us`, `/join-us`, `/join`

```bash
curl -s --max-time 120 -X POST http://localhost:8421/crawl \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/careers", "max_depth": 2, "max_pages": 30, "url_pattern": "/careers"}'
```

Many companies redirect careers to third-party ATS platforms (Greenhouse, Lever, Workday). If the page redirects externally, scrape the landing page only — external job boards are not Scout's scope.

---

### 4. Investor Relations

**What you're looking for:** IR landing page, investor contact, financial calendar, press releases.

**Common URL patterns:** `/investors`, `/investor-relations`, `/ir`, `/financials`

```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/investors", "use_js": true}'
```

---

### 5. Reports and PDF Documents

**What you're looking for:** annual reports, quarterly results, investor presentations, whitepapers.

Map the IR section first to surface PDF URLs, then scrape each one directly:

```bash
# Find PDFs
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/investors", "max_pages": 200}'
# Filter urls[] for entries ending in .pdf

# Scrape a PDF — returns extracted text as markdown
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/reports/annual-2024.pdf"}'
```

---

## Multi-Company Batch

Run companies sequentially — Scout is single-instance and not designed for parallel crawls:

```bash
for company in company-a.com company-b.com company-c.com; do
  echo "=== $company ==="
  curl -s --max-time 60 -X POST http://localhost:8421/map \
    -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
    -d "{\"url\": \"https://$company\", \"max_pages\": 100}" | jq '.urls[] | select(test("team|leadership|about"))'
done
```

---

## API Quick Reference

| Endpoint | Use case | Timeout |
|---|---|---|
| `GET /health` | Liveness check (no auth) | instant |
| `POST /scrape` | One page — markdown + links + metadata | 45s |
| `POST /map` | Discover all URLs on a domain | 60s |
| `POST /crawl` | BFS multi-page crawl of a section | 120s |
| `POST /extract` | Structured fields via LLM or CSS selectors | 60s |
| `POST /screenshot` | Full-page PNG (base64) | 30s |

**Error reference:**

| Error | Fix |
|---|---|
| `"Crawl failed"` / timeout | Add `"use_js": true`, increase `"timeout_ms"` |
| `"No LLM API key"` on `/extract` | Use `css_schema` instead, or set `LLM_API_KEY` in `.env` |
| HTTP 403 | Wrong or missing `X-API-Key` — check `SCOUT_API_KEY` in `.env` |
| HTTP 422 | Malformed JSON body |
| Sparse/empty markdown | Page is JS-rendered — retry with `"use_js": true` |

---

## CLI

```bash
scout serve                           # start the server (default port 8421)
scout serve --port 9000               # custom port
scout scrape https://company.com/about
scout map https://company.com --pages 200
scout crawl https://company.com/careers --depth 2 --pages 30
scout extract https://company.com/team --llm-key $LLM_API_KEY
scout screenshot https://company.com
```
