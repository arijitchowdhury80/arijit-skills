# algolia-intel-news

> Collects company news from the last 60 days — leadership changes, funding events, tech investments, product launches — via targeted searches across three query categories.

**Version:** 2.0.0 · **Layer/Phase:** Layer 1J / Wave 1 · **Suite:** Algolia Search Audit

## What it does

Runs `collect-news.py` with three targeted queries covering digital/ecommerce/tech news, executive/leadership changes, and launches/expansion/AI initiatives. The primary source is **Google News RSS** — keyless keyword search returning dated, sourced articles labeled `[FACT — Google News, {date}]`. The company's own RSS/newsroom feeds supplement it. No external search API key is required (Tavily and Apify are not used). Category classification is fully deterministic. The lookback window is 60 days; zero articles is a real null result, never padded.

## When to use

- Run in Wave 1 after `algolia-intel-company` has produced `01-company-context.json`.
- Use to catch time-sensitive signals — executive departures, funding rounds, platform migrations, or AI/tech announcements — before a discovery or outreach call.
- Use when checking for recent events that change the sales narrative for this prospect.

## Inputs (upstream)

- `01-company-context.json` — reads `company_name` and `domain`.

## Outputs

Files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

- `09c-news-signals.md` — categorized news articles with relevance signals; an explicit "no articles found" note if the 60-day window is empty.
- `09c-news-signals.json` — structured output with exact top-level shape: `meta` (domain, company_name, collection_method, total_articles), `lookback_days: 60` (top-level, not nested in meta), `collection_date` (top-level), `articles[]` (title, url, date, source, category, relevance_signal).

## Data sources

| Source | Provides | Method |
|---|---|---|
| Google News RSS (`collect-news.py`) | Dated, sourced news articles across 3 query categories | Primary — keyless keyword search; `collection_method: "google_news_rss"`; labels `[FACT — Google News, {date}]` |
| Company RSS/newsroom feeds | Headlines from the company's own `/press`, `/newsroom`, `/news`, `/blog` | Supplementary — direct HTTP; labels `[FACT — {domain} newsroom, {date}]` |

## How PRISM runs it

PRISM (the Hermes instance on the VPS) invokes this skill via the claude-cli executor in Wave 1 alongside other intel modules, after `algolia-intel-company` has completed. The script is called with the domain and research directory; it runs all three queries, writes `09c-news-signals.json` (JSON structure is fixed — deviations fail the verification gate), and the module writes `09c-news-signals.md`. Because the source is keyless, no credentials need to be provisioned on the executor for this module.

## Dependencies

- **Script:** `collect-news.py`
- **Env keys:** none — Google News RSS and company newsroom feeds are keyless.
- **Abort conditions:** None. Zero articles in the 60-day window is a valid result (recorded as an explicit null), not an error.

## Notes

- `lookback_days` and `collection_date` are TOP-LEVEL keys in the JSON — never nest them inside `meta`. A mis-nested structure fails the verification gate.
- Use `meta` key (not `_meta`) in this module's JSON output.
- Degraded-mode articles (RSS fallback) are amber confidence — label as `[OBSERVED]`, not `[FACT]`, when citing in the report.
- Verification gate: `09c-news-signals.md` ≥ 1000 bytes; `lookback_days: 60` at top level in JSON; `collection_date` at top level; all articles have `url` and `category`; `meta.skill_enrichment_completed = true`. Zero articles is acceptable if documented.
