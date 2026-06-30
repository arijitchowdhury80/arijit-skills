# algolia-intel-investor

> Captures verbatim executive quotes from earnings calls, SEC 10-K filings, and Yahoo Finance — grounded and recency-gated to January 2025 or later — plus trade press media quotes enriched with Algolia pitch context.

**Version:** 2.0.0 · **Layer/Phase:** Layer 1G / Wave 1 · **Suite:** Algolia Search Audit

## What it does

Runs `collect-investor.py` to bootstrap the output files, then enriches them through three live sources: earnings call transcripts (located via Gemini-grounded search, fetched verbatim via WebFetch from Motley Fool / Seeking Alpha), SEC EDGAR 10-K (direct WebFetch from sec.gov for MD&A and digital/technology risk factors), and Yahoo Finance news (via MCP). For private companies, those three sources are replaced by CEO/founder podcast interviews, conference talks, company blogs, and press releases fetched via WebFetch. Every verbatim quote candidate is run through `ground_quotes.py` — a deterministic gate that confirms the quote is an exact substring of the fetched source text AND is dated January 2025 or later. Quotes failing either check are rejected and must not ship with quotation marks.

## When to use

- Run in Wave 1 after `algolia-intel-company` has produced `01-company-context.json`.
- Use for public companies with a known ticker to extract exec strategic priorities in their own words from recent earnings calls and SEC filings.
- Use for private companies to source CEO/founder signals from trade press, podcasts, and conference transcripts.

## Inputs (upstream)

- `01-company-context.json` — reads company name, domain, and (for public companies) stock ticker.
- Script flags: `--ticker TICKER` for public companies; `--private` for private companies.

## Outputs

Files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

- `11-investor-intelligence.md` — verbatim executive quotes (speaker, title, source URL, date); MD&A and risk factor excerpts; Media Quotes (Trade Press) section with Algolia pitch context and relevance tags.
- `11-investor-intelligence.json` — `executive_quotes[]`, `media_quotes[]` (each with `context` and `algolia_relevance` fields enriched by LLM), `_meta.skill_enrichment_completed = true`. Uses `_meta` with underscore — not `meta`.

## Data sources

| Source | Provides | Method |
|---|---|---|
| Gemini-grounded search (`scripts/gemini_search.py`) | Earnings call transcript URLs (last 3 quarters) | Locates Motley Fool / Seeking Alpha transcripts; citations used as WebFetch targets |
| WebFetch (earnings transcripts) | Verbatim executive quotes extracted from transcript text | Direct HTTP fetch of located transcript URLs |
| WebFetch (SEC EDGAR 10-K) | MD&A section + Risk Factors (digital/technology items) | `https://www.sec.gov/cgi-bin/browse-edgar?...&type=10-K&count=1` — SEC EDGAR MCP does not exist; direct WebFetch only |
| Yahoo Finance MCP (`get_yahoo_finance_news`) | Recent news feed for the ticker | MCP tool call; public companies only |
| `collect-exec-media.py` + `scripts/gemini_search.py` | Trade press quotes from CEO/CMO/CTO | Script first; Gemini-grounded fallback if script returns zero or is unavailable |
| `ground_quotes.py` | Verbatim verification gate | Exact-substring check against fetched source text + January 2025 recency floor; exits non-zero on rejection |
| WebFetch (private companies) | CEO/founder podcast, conference, blog, press release transcripts | Replaces all three public-company sources above |

## How PRISM runs it

PRISM (the Hermes instance on the VPS) invokes this skill via the claude-cli executor in Wave 1 alongside other intel modules, after `algolia-intel-company` has completed. The module sequences three steps: (1) `collect-investor.py` bootstraps output files; (2) skill enrichment fetches earnings transcripts, SEC 10-K, and Yahoo Finance news; (3) `collect-exec-media.py` collects trade press media quotes and the LLM enriches `context` and `algolia_relevance` fields. PRISM enforces the `ground_quotes.py` gate before any quote ships with quotation marks.

## Dependencies

- **Scripts:** `collect-investor.py`, `collect-exec-media.py`, `ground_quotes.py`, `scripts/gemini_search.py`
- **MCP servers:** Yahoo Finance MCP (`get_yahoo_finance_news`) for public companies
- **Env keys:** Gemini API credentials for `gemini_search.py`
- **No EDGAR MCP:** sec.gov is accessed via direct WebFetch only
- **Abort conditions:** None per se — quotes rejected by `ground_quotes.py` are dropped, not retried; the module completes with whatever passes the gate.

## Notes

- The recency floor is hard: January 2025. No exceptions. Quotes older than 12 months are dropped entirely; undated quotes fail closed.
- Use `*said that*` notation (not quotation marks) for any quote where verbatim text cannot be confirmed by WebFetch.
- For private companies, all Step 2 sources (earnings calls, EDGAR, Yahoo Finance) are replaced by WebFetch of CEO/founder interviews, conference talks, company blogs, and press releases. Label: `[WEBFETCH — {source}, {date}]`.
- Media quotes from the Gemini fallback use `[ESTIMATE — {Publication} via Gemini search, {date}, {URL}]`.
- Use `_meta` (with underscore) in `11-investor-intelligence.json` — not `meta`.
- Verification gate: both files exist; `11-investor-intelligence.md` ≥ 3000 bytes; at least 3 executive quotes each with `speaker`, `title`, `source_url`; no anonymous sources; `_meta.skill_enrichment_completed = true`; `media_quotes` key present (array may be empty).
