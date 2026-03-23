---
name: algolia-intel-financial-private
description: Layer 1F financial intelligence for PRIVATE companies. Estimates revenue using 6-source waterfall — ecdb.com, PitchBook/Crunchbase, LinkedIn headcount, trade press, Inc 5000/Deloitte Fast 500, job posting volume. All figures labeled [ESTIMATE]. Produces 08-financial-profile.md and 08-financial-profile.json. Only for private companies with no SEC filings.
layer: 1-intelligence
module_id: 1F
script: collect-financials.py
reads_from:
  - 01-company-context.json
writes_to:
  - 08-financial-profile.md
  - 08-financial-profile.json
mcp_required:
  - websearch: "ecdb.com, trade press, ranking lists"
skill_enrichment: true
version: 1.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1F
- **Model tier:** data_enrichment (claude-haiku-4-5)
- **Use only for:** Private companies. For public companies (with ticker), use `algolia-intel-financial-public`.

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-financials.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  --private
```

---

## Step 2: Skill Enrichment — 6-Source Waterfall (ALL sources, not fallback)

Run all 6 sources simultaneously:

1. **ecdb.com/PitchBook/Crunchbase** — WebFetch for revenue estimate
   Label: `[ESTIMATE — ecdb.com WebFetch, {date}]`

2. **LinkedIn headcount** — WebFetch linkedin.com/company/{slug}
   Label: `[ESTIMATE — LinkedIn, {date}]`

3. **CEO/founder interviews** — WebSearch + WebFetch transcripts
   Label: `[WEBFETCH — {source}, {date}]`

4. **Trade press** — WebSearch Retail Dive, WWD, TechCrunch
   Label: `[WEBSEARCH — {source}]`

5. **Inc 5000/Deloitte Fast 500** — WebSearch
   Label: `[ESTIMATE — ranking list, {date}]`

6. **Job posting volume** — count from hiring signals as proxy
   Label: `[OBSERVED — hiring signals, {date}]`

Confidence: HIGH = 3+ sources agree within 20% | MEDIUM = 2 sources | LOW = single mention

All figures must use `[ESTIMATE]` label. Never use `[FACT]` for private company revenue.

Write `08-financial-profile.json` with this EXACT top-level structure. **No deviations — do not nest these fields inside `meta`.**

```json
{
  "meta": {
    "skill_enrichment_completed": true,
    "company_type": "private",
    "yahoo_finance_used": false
  },
  "revenue_confidence": "HIGH|MEDIUM|LOW",
  "revenue_sources": ["ecdb", "trade_press", "linkedin_headcount"],
  "sources_succeeded": ["ecdb", "trade_press"],
  "sources_failed": [],
  "company_overview": { "...all company fields here..." },
  "financials": { "...revenue trend, margins, etc..." }
}
```

**CRITICAL:** `revenue_confidence`, `revenue_sources`, `sources_succeeded`, and `sources_failed` are **TOP-LEVEL** keys — NOT inside `meta` or any other nested object. Use `meta` (not `_meta`).

---

## Verification Gate

Pass: Both files ≥3000 bytes, revenue estimate present with [ESTIMATE] label, `revenue_confidence` at top level in JSON, `revenue_sources` array at top level (≥2 entries), `meta.skill_enrichment_completed = true`, `sources_succeeded` does NOT include `yahoo_finance`.
