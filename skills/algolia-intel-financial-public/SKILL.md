---
name: algolia-intel-financial-public
description: Layer 1E financial intelligence for PUBLIC companies. Collects 3-year revenue trend, EBITDA margin, analyst consensus via Yahoo Finance MCP (all endpoints). Complemented by earnings call transcripts via WebFetch for executive quotes. Produces 08-financial-profile.md and 08-financial-profile.json. Only for companies with SEC filings and a stock ticker.
layer: 1-intelligence
module_id: 1E
script: collect-financials.py
reads_from:
  - 01-company-context.json
writes_to:
  - 08-financial-profile.md
  - 08-financial-profile.json
mcp_required:
  - yahoo_finance: "ALL endpoints — get_stock_info, get_financial_statement (4 variants), get_recommendations (2), get_historical_stock_prices, get_yahoo_finance_news"
skill_enrichment: true
version: 1.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1E
- **Model tier:** data_enrichment (claude-haiku-4-5)
- **Use only for:** Public companies with ticker. For private companies, use `algolia-intel-financial-private`.

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-financials.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  --ticker {TICKER}
```

If Yahoo Finance MCP is NOT available: STOP. Alert: "Yahoo Finance MCP required. Configure MCP and retry."
Do NOT use WebSearch as a substitute for financial data.

---

## Step 2: Skill Enrichment — Earnings Call Transcripts

Source B (complementary, not fallback):
- WebSearch: `"{Company}" Q4 2025 earnings call transcript` — try last 3 quarters
- WebFetch: Motley Fool / Seeking Alpha / company IR
- Extract verbatim quotes from ANY named speaker
- Label: `[FACT — {source} transcript WebFetch, {date}]`

Both Yahoo Finance MCP AND transcripts are required. Neither substitutes for the other.

---

## Step 3: Finalize JSON with meta and flat key fields

After enrichment, ensure `08-financial-profile.json` has these fields at the **TOP LEVEL** (not nested under `financials.*` or `margins.*`):

```json
{
  "meta": {
    "skill_enrichment_completed": true,
    "collection_date": "YYYY-MM-DD"
  },
  "revenue_fy2025": <number>,
  "revenue_fy2024": <number>,
  "margin_zone": "RED|YELLOW|GREEN",
  "roi_formula_shown": true
}
```

**IMPORTANT:** Use `meta` (not `_meta`). The `revenue_fy2025`, `margin_zone`, and `roi_formula_shown` fields MUST be at the top level. These are validated by the eval assertions. The script may produce nested JSON — flatten these 4 keys to top level during skill enrichment.

`roi_formula_shown` = `true` whenever a Gross Margin % calculation is shown in the MD file.

`margin_zone` classification:
- GREEN: Gross margin > 40%
- YELLOW: Gross margin 20-40%
- RED: Gross margin < 20%

---

## Verification Gate

Pass: Both files ≥5000 bytes, `revenue_fy2025` at **top level** in JSON (not null), at least 3 `[FACT — Yahoo Finance MCP` labels, `meta.skill_enrichment_completed = true`, `margin_zone` and `roi_formula_shown` at top level.
