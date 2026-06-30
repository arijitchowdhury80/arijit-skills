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
  {TICKER} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  --company-type public
```

The first positional arg is the TICKER; the second is the research dir.
`--company-type public` stamps a `<!-- company_type: public -->` marker into
`08-financial-profile.md`.

**BUG-5 overwrite guard:** if `08-financial-profile.md` already exists and was written
by the PRIVATE path (1F), the script REFUSES to overwrite it and exits 2 — this stops a
public/private routing misclassification (or a stray re-run) from silently clobbering
the other path's profile. If you genuinely intend to replace a private profile with a
public one, re-run with `--force`; the script backs up the existing file to
`08-financial-profile.private.bak` first. A same-type refresh (public over public) is
allowed without `--force`.

If Yahoo Finance MCP is NOT available: STOP. Alert: "Yahoo Finance MCP required. Configure MCP and retry."
Do NOT use grounded search as a substitute for financial data.

---

## Step 2: Skill Enrichment — SEC 10-K Digital Revenue + Earnings Transcripts

**Source B — SEC EDGAR 10-K (digital/ecommerce financial signals):**

Yahoo Finance API only provides total revenue. Digital/ecommerce revenue breakdowns, technology investment figures, and digital channel percentages live in the 10-K filing (MD&A section). These are REQUIRED for the financial profile.

```
WebFetch: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K&count=3
→ Find the last 3 annual filings → WebFetch each filing document
```

From the 10-K MD&A, extract for EACH year reported:
- Digital/ecommerce revenue (absolute $ AND % of total) — search for "digital", "ecommerce", "e-commerce", "online", "digital sales", "digital channel"
- Technology investment mentions — search for "technology", "platform investment", "digital transformation", "IT spend"
- Search/discovery platform mentions — search for "search", "personalization", "product discovery"
- Any forward guidance on digital growth targets

Write these to the financial profile with year labels:
```
Digital Revenue FY2025: ${X}M ({Y}% of total) [FACT — SEC EDGAR 10-K FY2025, {URL}]
Digital Revenue FY2024: ${X}M ({Y}% of total) [FACT — SEC EDGAR 10-K FY2024, {URL}]
Digital Revenue FY2023: ${X}M ({Y}% of total) [FACT — SEC EDGAR 10-K FY2023, {URL}]
```

If the 10-K does NOT break out digital revenue separately: state this explicitly and note which segment reporting they use. Do NOT leave this field blank or assume $0.

Label: `[FACT — SEC EDGAR 10-K WebFetch, {date}, {URL}]`

**Source C — Earnings call transcripts (exec language on tech investment):**
- Run the grounded search helper (NOT WebSearch — retired) to locate transcript sources:
  ```bash
  python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
    --system "Return only facts supported by Google Search results. Cite each fact." \
    "{Company} Q4 2025 earnings call transcript"
  ```
  Use the cited URLs from the JSON output to WebFetch the transcripts. Try last 3 quarters.
  **Grounding rule:** only label a quote `[FACT — <citation url>, <date>]` when `"grounded": true` and a cited source supports it. If `"grounded": false`, do not include the quote.
- WebFetch: Motley Fool / Seeking Alpha / company IR
- Look specifically for: exec comments on search/digital/platform investments, technology spend, digital revenue guidance
- Extract verbatim quotes from ANY named speaker about these topics
- Label: `[FACT — {source} transcript WebFetch, {date}]`

All three sources (Yahoo Finance MCP, SEC EDGAR 10-K, earnings transcripts) are required. None substitutes for another.

---

## Step 3: Write 08-financial-profile.json

Write `08-financial-profile.json` with this EXACT top-level structure. **No deviations — do not nest these fields inside `financials`, `margins`, or any other object.**

```json
{
  "meta": {
    "skill_enrichment_completed": true,
    "collection_date": "YYYY-MM-DD",
    "ticker": "{TICKER}",
    "company_type": "public"
  },
  "revenue_fy2025": 3009000000,
  "revenue_fy2024": 3075000000,
  "revenue_fy2023": 3315000000,
  "margin_zone": "RED|YELLOW|GREEN",
  "roi_formula_shown": true,
  "financials": {
    "...all other financial fields (revenue trend, margins, EBITDA, etc.)..."
  },
  "executive_quotes": ["..."],
  "analyst_consensus": "..."
}
```

**CRITICAL:**
- `revenue_fy2025`, `revenue_fy2024`, `revenue_fy2023`, `margin_zone`, and `roi_formula_shown` are **TOP-LEVEL keys** — NEVER nest them inside `financials.*` or `margins.*`
- `roi_formula_shown` MUST always be present. Set to `true` if gross margin % calculation appears in the MD file, `false` otherwise. Never omit this field.
- Use `meta` NOT `_meta`

`roi_formula_shown` = `true` whenever a Gross Margin % calculation is shown in the MD file.

`margin_zone` classification:
- GREEN: Gross margin > 40%
- YELLOW: Gross margin 20-40%
- RED: Gross margin < 20%

---

## Verification Gate

Pass: Both files ≥5000 bytes, `revenue_fy2025` at **top level** in JSON (not null), at least 3 `[FACT — Yahoo Finance MCP` labels, `meta.skill_enrichment_completed = true`, `margin_zone` and `roi_formula_shown` at top level.
