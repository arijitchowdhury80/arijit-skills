---
name: algolia-intel-news
description: Layer 1J news signals module. Scrapes Google News via Apify (3 targeted queries) and company RSS/newsroom feeds. Catches leadership changes, funding events, tech investments, product launches in the last 60 days. Produces 09c-news-signals.md and 09c-news-signals.json.
layer: 1-intelligence
module_id: 1J
script: collect-news.py
reads_from:
  - 01-company-context.json
writes_to:
  - 09c-news-signals.md
  - 09c-news-signals.json
mcp_required:
  - apify: "data_xplorer/google-news-scraper-fast"
skill_enrichment: false
version: 2.0.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1J
- **Model tier:** programmatic
- **Reads from:** `01-company-context.json` (company_name, domain)

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-news.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  --company-name "{CompanyName}"
```

3 queries run: digital/ecommerce/tech | executive/leadership | launch/expansion/AI
Lookback: 60 days.

**Collection method + degradation (read the script's stdout JSON):**
- `collection_method: "gemini_search"` → `[FACT]`-grade primary (script uses Gemini-grounded search).
- `collection_method: "google_news_rss_fallback"` + `degraded: true` → Gemini-grounded search
  unavailable, so articles came from the Google News RSS fallback. Their per-article labels are
  `[OBSERVED — Google News RSS fallback, {date}]`, NOT `[FACT]`. The `.md` carries a loud
  DEGRADED banner. This is a real freshness/coverage downgrade — never silent. Carry the
  `collection_method` + `degraded` flags into the JSON `meta`, and treat degraded articles
  as amber when downstream synthesis cites them.

---

## No Skill Enrichment Required

Fully programmatic. Category classification is deterministic.

---

## Write 09c-news-signals.json

After the script runs, write `09c-news-signals.json` with this EXACT top-level structure. **No deviations.**

```json
{
  "meta": {
    "skill_enrichment_completed": true,
    "domain": "{domain}",
    "company_name": "{CompanyName}",
    "collection_method": "gemini_search|google_news_rss_fallback",
    "degraded": false,
    "total_articles": 0
  },
  "lookback_days": 60,
  "collection_date": "YYYY-MM-DD",
  "articles": [
    {"title": "...", "url": "...", "date": "YYYY-MM-DD", "source": "...", "category": "...", "relevance_signal": "..."}
  ]
}
```

**CRITICAL:** `lookback_days` and `collection_date` are TOP-LEVEL keys. NEVER nest them inside `meta`. Use `meta` (not `_meta`).

## Verification Gate

Pass: `09c-news-signals.md` ≥1000 bytes, `lookback_days: 60` at top level in JSON, `collection_date` at top level, all articles have `url` and `category`, `meta.skill_enrichment_completed = true`. Zero articles is acceptable.
