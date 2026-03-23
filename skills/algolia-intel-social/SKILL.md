---
name: algolia-intel-social
description: Layer 1I social signals module. Scrapes LinkedIn company posts and Twitter/X posts via Apify to surface strategic signals — tech investment, search pain, international expansion, exec priorities. Scores each post for Algolia relevance. Produces 09b-social-signals.md and 09b-social-signals.json.
layer: 1-intelligence
module_id: 1I
script: collect-social.py
reads_from:
  - 01-company-context.json
writes_to:
  - 09b-social-signals.md
  - 09b-social-signals.json
mcp_required:
  - apify: "harvestapi/linkedin-company-posts, apidojo/tweet-scraper"
skill_enrichment: false
version: 1.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1I
- **Model tier:** programmatic
- **Reads from:** `01-company-context.json` (linkedin_url, twitter_handle)

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-social.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  --company-name "{CompanyName}"
```

Known issue: LinkedIn posts actor may return 0 for some companies — document in errors, continue.

**APIFY_TOKEN fallback (MANDATORY):** If `APIFY_TOKEN not set` error appears or Apify returns 0 results on BOTH platforms:
1. Run WebSearch: `site:linkedin.com/posts "{CompanyName}" 2025 2026`
2. Run WebSearch: `"{CompanyName}" CEO LinkedIn post announcement 2025 2026`
3. Run WebSearch: `twitter.com "{CompanyName}" announcement tech investment 2025`
4. Add any posts found with `[WEBSEARCH — url, date]` label to the MD file
5. Set `qualifying_signals_count` based on posts found via WebSearch

**Platform Notes section REQUIRED** in every 09b-social-signals.md output — even if 0 results. Document: which platforms scraped, how many posts found, any errors (e.g., "APIFY_TOKEN not set").

---

## Step 2: Write JSON with meta

After script completes, ensure `09b-social-signals.json` has `meta` block (use `meta`, NOT `meta`):
```json
{
  "meta": {
    "skill_enrichment_completed": true,
    "degraded_mode": false,
    "collection_date": "YYYY-MM-DD"
  },
  "qualifying_signals_count": N,
  "signals": [...]
}
```

---

## Verification Gate

Pass: `09b-social-signals.md` ≥1000 bytes, file exists, Platform Notes section present, `meta.skill_enrichment_completed = true` in JSON. (Zero qualifying signals is acceptable — documented.)
