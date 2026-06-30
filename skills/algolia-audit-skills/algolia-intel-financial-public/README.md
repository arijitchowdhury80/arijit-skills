# algolia-intel-financial-public

> Collect 3-year revenue trend, EBITDA margin, and executive language on tech investment for public companies — using Yahoo Finance, SEC EDGAR 10-Ks, and earnings call transcripts.

**Version:** 2.0.0 · **Layer/Phase:** Layer 1E / Wave 1 · **Suite:** Algolia Search Audit

## What it does

Runs `collect-financials.py --company-type public` against a stock ticker to pull 3 years of revenue and margin data from Yahoo Finance (no API key required). Then enriches with two additional mandatory sources: the SEC EDGAR 10-K MD&A section for digital/ecommerce revenue breakdowns and technology investment mentions (not available from Yahoo Finance), and earnings call transcripts for verbatim executive quotes on search, digital, and platform investments. All three sources are required — none substitutes for another.

## When to use

- The prospect is a public company with SEC filings and a known stock ticker.
- For private companies (no ticker, no SEC filings), use `algolia-intel-financial-private` instead.

## Inputs (upstream)

| File | Used for |
|---|---|
| `01-company-context.json` | Company name, ticker (if known), public/private classification |

The script also accepts the ticker as a positional argument directly when known.

## Outputs

Two files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

| File | Key fields |
|---|---|
| `08-financial-profile.md` | Revenue 3-year trend, margin analysis with gross-margin % formula, digital/ecommerce revenue by year, tech investment mentions, verbatim exec quotes |
| `08-financial-profile.json` | Top-level: `revenue_fy2025`, `revenue_fy2024`, `revenue_fy2023`, `margin_zone` (RED/YELLOW/GREEN), `roi_formula_shown`; nested: `financials`, `executive_quotes[]`, `analyst_consensus`, `meta` |

Verification gate: both files ≥5000 bytes; `revenue_fy2025` at top level in JSON (not null); at least 3 `[FACT — yfinance` labels; `margin_zone` and `roi_formula_shown` at top level; `meta.skill_enrichment_completed = true`.

## Data sources

| Source | Provides | Method |
|---|---|---|
| Yahoo Finance (`yfinance` library) | 3-year revenue, EBITDA margin, gross margin, analyst consensus | `collect-financials.py` — Python `yfinance` library; no MCP, no API key |
| SEC EDGAR 10-K (WebFetch) | Digital/ecommerce revenue ($ + % of total), technology investment figures, digital growth guidance — last 3 annual filings | Direct WebFetch of EDGAR filing index + document |
| Earnings call transcripts (Gemini-grounded + WebFetch) | Verbatim exec quotes on search/digital/platform spend — last 3 quarters | `gemini_search.py` locates transcript sources; WebFetch retrieves them from Motley Fool / Seeking Alpha / company IR |

No-fabrication gate: grounded search results used only when `"grounded": true`. If `"grounded": false`, the quote is excluded. Blank stays blank — do not substitute yfinance total revenue for missing digital breakdown; state explicitly when 10-K does not break out digital separately.

## How PRISM runs it

PRISM invokes this skill via the claude-cli executor in Wave 1, after `algolia-intel-company` (1A) has confirmed the company is public and provided the ticker. It runs in parallel with other Wave-1 modules that do not depend on financial data. The overwrite guard (`BUG-5`) prevents a private-path profile from being silently clobbered if both paths are triggered in error.

## Dependencies

| Item | Detail |
|---|---|
| Script | `~/.claude/skills/algolia-search-audit/scripts/collect-financials.py` |
| `gemini_search.py` | `~/.claude/skills/algolia-search-audit/scripts/gemini_search.py` — requires `GEMINI_API_KEY` |
| Python packages | `yfinance` — no external API key required |
| Upstream | `01-company-context.json` must exist; ticker must be known |
| Overwrite guard | Script exits 2 if `08-financial-profile.md` already exists as a private-path file; use `--force` only after confirming routing is correct (backs up to `.private.bak`) |

## Notes

- `roi_formula_shown` must always be present in JSON — set `true` if the MD file shows a gross margin % calculation, `false` otherwise; never omit.
- `margin_zone`: GREEN = EBITDA margin >20%, YELLOW = 10–20%, RED = ≤10% (computed from `info.ebitdaMargins` by `collect-financials.py` — not gross margin).
- `revenue_fy*` fields and `margin_zone` must be top-level JSON keys — never nested inside `financials` or `margins`.
- Do not use grounded search as a substitute for financial data that yfinance cannot return — if yfinance returns no data for a field, record blank and continue.
