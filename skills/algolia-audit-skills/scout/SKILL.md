---
name: scout
description: Use Scout to gather company intelligence from real websites. Scout is PRISM's purpose-built web intelligence platform at http://localhost:8421. It is NOT a general-purpose scraper — it is optimised for specific company intelligence use cases: About page, executive team, hiring openings, investor relations, and PDF reports/presentations. Always invoke Scout instead of WebFetch or raw curl when the goal is any of these five intelligence types, even when the user just says "find the leadership team" or "get their investor deck" without mentioning Scout explicitly. Scout handles JS-rendered pages, stealth mode, PDF extraction, and sitemap discovery that basic fetch tools cannot.
layer: 0-infrastructure
type: server-backed
server_port: 8421
health_check: "curl -s http://localhost:8421/health"
start_command: "scout serve"
requires_install: true
install_script: install-skill.sh
version: 1.1
---

# Scout — Company Intelligence Platform

Scout is your intelligence layer for gathering specific, structured company data from websites. It runs locally at `http://localhost:8421` and wraps Crawl4AI with Playwright.

**Always check health first:**
```bash
curl -s http://localhost:8421/health
```
If not running: `scout serve` (requires install — see [README.md](README.md))

**Auth:** Every endpoint except `/health` needs `X-API-Key: $SCOUT_API_KEY`.

> Local dev default: `SCOUT_API_KEY=dev-key`. Set a real key in `.env` before sharing or deploying.

---

## Full Company Intelligence Profile

When asked to research a company, gather all five intelligence types in one run. **Map once, then scrape everything you need from that map.**

```bash
# Step 1: one map call — get the whole site structure
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com", "max_pages": 300}'

# Step 2: from the urls[] list, identify pages for each section:
#   - About/company: /about, /about-us, /company, /who-we-are
#   - Leadership: /team, /leadership, /management, /about/team, /about/leadership
#   - Careers: /careers, /jobs, /join-us
#   - Investors: /investors, /investor-relations, /ir
#   - PDFs: any urls ending in .pdf or /reports/, /presentations/

# Step 3: scrape each identified section — 5 scrape calls, one per intelligence type
```

**Output structure for a full profile:**
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
2. **Filter** results to the section you need
3. **Scrape** the relevant pages

Don't guess URLs. Map first — company sites vary wildly (`/team` vs `/about/leadership` vs `/company/management`).

```bash
# Step 1: discover the site
curl -s --max-time 60 -X POST http://localhost:8421/map \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com", "max_pages": 200}'

# Step 2: look through urls[] for the right section, then scrape it
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

If markdown is sparse, request raw HTML and parse name/title card patterns:
```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/about/leadership/", "use_js": true, "formats": ["raw_html"]}'
```

---

### 3. Hiring / Open Roles

**Common URL patterns:** `/careers`, `/jobs`, `/work-with-us`, `/join-us`

```bash
curl -s --max-time 120 -X POST http://localhost:8421/crawl \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/careers", "max_depth": 2, "max_pages": 30, "url_pattern": "/careers"}'
```

---

### 4. Investor Relations

**Common URL patterns:** `/investors`, `/investor-relations`, `/ir`

```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/investors", "use_js": true}'
```

---

### 5. Reports and PDF Documents

Scout's `/scrape` handles PDFs natively — pass the direct PDF URL:
```bash
curl -s -X POST http://localhost:8421/scrape \
  -H "Content-Type: application/json" -H "X-API-Key: $SCOUT_API_KEY" \
  -d '{"url": "https://company.com/reports/annual-2024.pdf"}'
```

---

## Multi-Company Intelligence (Batch)

Run sequentially — Scout is single-instance, not designed for parallel crawls:

```bash
for company in algolia.com adobe.com shopify.com; do
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
| `/scrape` | One page (including PDFs) | 45s |
| `/map` | Discover all URLs on a domain | 60s |
| `/crawl` | Multi-page deep crawl of a section | 120s |
| `/extract` | Structured fields via LLM or CSS selectors | 60s |
| `/screenshot` | Visual capture | 30s |

**Error reference:**

| Error | Fix |
|---|---|
| `"Crawl failed"` / timeout | Add `"use_js": true`, increase `"timeout_ms"` |
| `"No LLM API key"` on `/extract` | Use `css_schema` instead, or set `LLM_API_KEY` in `.env` |
| HTTP 403 | Missing or wrong `X-API-Key` — check `SCOUT_API_KEY` in `.env` |
| HTTP 422 | Malformed JSON body |
| Sparse/empty markdown | JS-rendered page — retry with `"use_js": true` |

---

## CLI Alternative

```bash
scout serve                           # start the server (port 8421)
scout serve --port 9000               # custom port
scout scrape https://company.com/about
scout map https://company.com --pages 200
scout crawl https://company.com/careers --depth 2 --pages 30
scout extract https://company.com/team --llm-key $LLM_API_KEY
```
