# algolia-intel-social

> Scrapes LinkedIn company posts and Twitter/X posts to surface strategic signals — tech investment, search pain, international expansion, exec priorities — scored for Algolia relevance.

**Version:** 2.0.0 · **Layer/Phase:** Layer 1I / Wave 1 · **Suite:** Algolia Search Audit

## What it does

Runs `collect-social.py` to pull the company's recent LinkedIn and Twitter/X posts via Apify actors. Each post is scored for Algolia relevance against signals like tech investment, platform changes, international expansion, and search pain. When Apify is unavailable (`APIFY_TOKEN` missing) or returns zero results on both platforms, the module falls back to three Gemini-grounded search queries targeting the same signals. A Platform Notes section is always written — even with zero results — to document exactly what was and wasn't collected and why.

## When to use

- Run in Wave 1 after `algolia-intel-company` has produced `01-company-context.json`.
- Use to surface exec-level strategic intent and recent company announcements before a discovery call.
- Use when identifying whether the prospect has publicly signaled pain points or investment themes relevant to search.

## Inputs (upstream)

- `01-company-context.json` — reads `linkedin_url` and `twitter_handle`.

## Outputs

Files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

- `09b-social-signals.md` — qualifying signals with scores, Platform Notes section (always present), DEGRADED banner if running in fallback mode.
- `09b-social-signals.json` — `signals[]` array with `meta` block containing: `skill_enrichment_completed`, `degraded_mode`, `collection_method` (`apify` or `apify_token_missing`), `collection_date`, and `qualifying_signals_count`.

## Data sources

| Source | Provides | Method |
|---|---|---|
| Apify (`harvestapi/linkedin-company-posts`) | Recent LinkedIn company posts | Script via Apify MCP; primary when `APIFY_TOKEN` is set |
| Apify (`apidojo/tweet-scraper`) | Recent Twitter/X posts | Script via Apify MCP; primary when `APIFY_TOKEN` is set |
| Gemini-grounded search (`scripts/gemini_search.py`) | LinkedIn and Twitter signals when Apify is unavailable or returns zero results on both platforms | Fallback — 3 queries; no-fabrication gate: if `grounded: false`, post is skipped entirely |

## How PRISM runs it

PRISM (the Hermes instance on the VPS) invokes this skill via the claude-cli executor in Wave 1 alongside other intel modules, after `algolia-intel-company` has completed. The script runs first; if the `APIFY_TOKEN` is missing or both platforms return zero results, the module automatically falls back to three Gemini-grounded search queries. PRISM carries the `collection_method` and `degraded_mode` flags into the audit report so downstream synthesis knows the confidence level of each signal.

## Dependencies

- **Script:** `collect-social.py`
- **MCP servers:** Apify (`harvestapi/linkedin-company-posts`, `apidojo/tweet-scraper`)
- **Env keys:** `APIFY_TOKEN`; Gemini API credentials for `gemini_search.py` fallback
- **Fallback:** `scripts/gemini_search.py`
- **Abort conditions:** None — a missing `APIFY_TOKEN` triggers a loud DEGRADED warning and fallback, not an abort.

## Notes

- An empty signals list under `apify_token_missing` means NOT-COLLECTED, not "no signals exist." The distinction matters for downstream synthesis and report confidence labeling.
- Degraded-mode posts from the Gemini fallback are labeled `[OBSERVED — <citation url>, date]` (not `[FACT]`); treat as amber confidence when citing in the audit report.
- Platform Notes section is mandatory in every output file, even if zero results were collected.
- Known issue: the LinkedIn posts Apify actor may return 0 results for some companies even with a valid token — document in errors and continue.
- Verification gate: `09b-social-signals.md` ≥ 1000 bytes; Platform Notes section present; `meta.skill_enrichment_completed = true` in JSON. Zero qualifying signals is acceptable if documented.
