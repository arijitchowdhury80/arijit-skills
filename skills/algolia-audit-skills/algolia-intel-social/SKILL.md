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
version: 2.0.0
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

**APIFY_TOKEN fallback (MANDATORY):** The script reports `collection_method` in its stdout
JSON: `"apify"` (real collection) or `"apify_token_missing"` (degraded — `degraded: true`,
loud stderr `⚠⚠ Social DEGRADED`, and a DEGRADED banner in the `.md`). An empty signal list
under `apify_token_missing` means NOT-COLLECTED, not "no signals exist."

If `collection_method == "apify_token_missing"` OR Apify returned 0 on BOTH platforms:

Run the following three queries via `gemini_search.py` (WebSearch is retired here — use the grounded helper):
```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
  --system "Find recent LinkedIn company posts and announcements. Return only grounded results with citation URLs." \
  'site:linkedin.com/posts "{CompanyName}" 2025 2026'

python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
  --system "Find recent executive announcements and company posts. Return only grounded results with citation URLs." \
  '"{CompanyName}" CEO LinkedIn post announcement 2025 2026'

python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
  --system "Find recent company social media announcements and tech investment posts. Return only grounded results with citation URLs." \
  'twitter.com "{CompanyName}" announcement tech investment 2025'
```
1. Add any posts found with `[OBSERVED — <citation url from gemini_search.py>, date]` label when `grounded: true`; skip if `grounded: false` — never use ungrounded model knowledge (amber, not `[FACT]`)
2. Set `qualifying_signals_count` based on posts found via gemini_search.py
3. Set `meta.degraded_mode = true` and `meta.collection_method` to the script's value — never drop it

**Platform Notes section REQUIRED** in every 09b-social-signals.md output — even if 0 results. Document: which platforms scraped, how many posts found, any errors (e.g., "APIFY_TOKEN not set").

---

## Step 2: Write JSON with meta

After script completes, ensure `09b-social-signals.json` has `meta` block (use `meta`, NOT `meta`):
```json
{
  "meta": {
    "skill_enrichment_completed": true,
    "degraded_mode": false,
    "collection_method": "apify|apify_token_missing",
    "collection_date": "YYYY-MM-DD"
  },
  "qualifying_signals_count": N,
  "signals": [...]
}
```

---

## Verification Gate

Pass: `09b-social-signals.md` ≥1000 bytes, file exists, Platform Notes section present, `meta.skill_enrichment_completed = true` in JSON. (Zero qualifying signals is acceptable — documented.)
