# algolia-intel-news

> Collects company news from the last 60 days — leadership changes, funding events, tech investments, product launches — via targeted searches across three query categories.

**Version:** 2.0.0 · **Layer/Phase:** Layer 1J / Wave 1 · **Suite:** Algolia Search Audit

## What it does

Runs `collect-news.py` with three targeted queries covering digital/ecommerce/tech news, executive/leadership changes, and launches/expansion/AI initiatives. The primary collection method is Gemini-grounded search, which returns `[FACT]`-grade articles. If Gemini-grounded search is unavailable, the script falls back to a Google News RSS feed — articles from the fallback are labeled `[OBSERVED]` and carry a DEGRADED banner in the output, so downstream synthesis knows the confidence level. Category classification of articles is fully deterministic. The lookback window is 60 days.

## When to use

- Run in Wave 1 after `algolia-intel-company` has produced `01-company-context.json`.
- Use to catch time-sensitive signals — executive departures, funding rounds, platform migrations, or AI/tech announcements — before a discovery or outreach call.
- Use when checking for recent events that change the sales narrative for this prospect.

## Inputs (upstream)

- `01-company-context.json` — reads `company_name` and `domain`.

## Outputs

Files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

- `09c-news-signals.md` — categorized news articles with relevance signals; DEGRADED banner if RSS fallback was used.
- `09c-news-signals.json` — structured output with exact top-level shape: `meta` (domain, company_name, collection_method, degraded, total_articles), `lookback_days: 60` (top-level, not nested in meta), `collection_date` (top-level), `articles[]` (title, url, date, source, category, relevance_signal).

## Data sources

| Source | Provides | Method |
|---|---|---|
| Gemini-grounded search (via `collect-news.py`) | News articles across 3 query categories; returns `[FACT]`-grade results when `grounded: true` | Primary — `collection_method: "gemini_search"` in script output |
| Google News RSS feed | News articles when Gemini-grounded search is unavailable | Fallback — `collection_method: "google_news_rss_fallback"`; labels become `[OBSERVED — Google News RSS fallback, {date}]`; carries `degraded: true` flag |

## How PRISM runs it

PRISM (the Hermes instance on the VPS) invokes this skill via the claude-cli executor in Wave 1 alongside other intel modules, after `algolia-intel-company` has completed. The script is called with the domain and research directory; it runs all three queries, writes `09c-news-signals.json` (JSON structure is fixed — deviations fail the verification gate), and the module writes `09c-news-signals.md`. The `collection_method` and `degraded` flags are carried through to the audit report to signal article confidence to downstream modules.

## Dependencies

- **Script:** `collect-news.py`
- **MCP servers:** Apify (`data_xplorer/google-news-scraper-fast`) — listed as required in frontmatter
- **Env keys:** Gemini API credentials (for primary Gemini-grounded search path in the script)
- **Abort conditions:** None — if Gemini-grounded search is unavailable, the script falls back to RSS rather than aborting.

## Notes

- `lookback_days` and `collection_date` are TOP-LEVEL keys in the JSON — never nest them inside `meta`. A mis-nested structure fails the verification gate.
- Use `meta` key (not `_meta`) in this module's JSON output.
- Degraded-mode articles (RSS fallback) are amber confidence — label as `[OBSERVED]`, not `[FACT]`, when citing in the report.
- Verification gate: `09c-news-signals.md` ≥ 1000 bytes; `lookback_days: 60` at top level in JSON; `collection_date` at top level; all articles have `url` and `category`; `meta.skill_enrichment_completed = true`. Zero articles is acceptable if documented.
