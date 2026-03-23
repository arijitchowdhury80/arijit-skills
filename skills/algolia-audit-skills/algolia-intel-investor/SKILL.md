---
name: algolia-intel-investor
description: Layer 1G investor and executive intelligence module. Captures verbatim executive quotes from earnings calls, SEC 10-K MD&A and risk factors, and Yahoo Finance news feed. Produces 11-investor-intelligence.md and 11-investor-intelligence.json. Run in Wave 1 for public companies. For private companies, uses CEO/founder interview transcripts via WebFetch.
layer: 1-intelligence
module_id: 1G
script: collect-investor.py
reads_from:
  - 01-company-context.json
writes_to:
  - 11-investor-intelligence.md
  - 11-investor-intelligence.json
mcp_required:
  - yahoo_finance: "get_yahoo_finance_news for news feed"
  - websearch: "earnings call transcripts"
skill_enrichment: true
version: 1.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1G
- **Model tier:** data_enrichment (claude-haiku-4-5)

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-investor.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  [--ticker TICKER] \
  [--private]
```

---

## Step 2: Skill Enrichment — ALL Sources (not fallback chain)

### For public companies:
1. **Earnings call transcripts** — WebSearch `"{Company}" Q4 2025 earnings call transcript`, WebFetch Motley Fool/Seeking Alpha — last 3 quarters, ANY named speaker
   Label: `[FACT — {source} transcript WebFetch, {date}]`

2. **SEC EDGAR 10-K** — WebFetch sec.gov directly (SEC EDGAR MCP does NOT exist — use direct HTTP WebFetch)
   URL: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K&count=1`
   Extract: MD&A section + Risk Factors (digital/technology items)
   Label: `[FACT — SEC EDGAR 10-K WebFetch, {date}, {URL}]`

3. **Yahoo Finance news** — get_yahoo_finance_news(ticker)
   Label: `[FACT — Yahoo Finance MCP news, {date}]`

### For private companies:
- No SEC EDGAR, no Yahoo Finance
- Replace with: CEO/founder podcast interviews, conference talks, company blog, press releases
- Label: `[WEBFETCH — {source}, {date}]`

### Quote rules:
- VERBATIM only if WebFetch confirms exact text. Use quotation marks.
- If not WebFetched: use *said that* notation. NO quotation marks.
- Named speaker + title + source URL + date — every quote.
- NO anonymous sources.

---

## Verification Gate

Ensure `11-investor-intelligence.json` has `meta` block (use `meta`, NOT `meta`):
```json
{"meta": {"skill_enrichment_completed": true}, "executive_quotes": [...]}
```

Pass: Both files exist, `11-investor-intelligence.md` ≥3000 bytes, at least 3 executive quotes each with `speaker`, `title`, `source_url` fields, no anonymous sources, `meta.skill_enrichment_completed = true`.
