# algolia-intel-traffic

> Collect the full traffic and engagement profile for an audit prospect via SimilarWeb MCP — visits, channels, keywords, referrals, geography, demographics, and popular pages.

**Version:** 2.0.0 · **Layer/Phase:** Layer 1C / Wave 1 · **Suite:** Algolia Search Audit

## What it does

Runs `collect-traffic.py` which calls all required SimilarWeb API endpoints — no skipping. Collects monthly visits, bounce rate, device split, 7-channel marketing breakdown, organic and paid keyword lists (Search 3.0 v4 endpoints only — v1 deprecated Feb 2025), incoming and outgoing referrals, top countries, demographics (when the plan allows), and popular pages. If SimilarWeb returns fewer than 3 successful endpoints, the module falls back to Gemini-grounded Google Search for traffic estimates. A `03-traffic-data.json` file is always written, even in fully degraded mode.

## When to use

- Any Algolia Search Audit, Wave 1 — no upstream module dependencies; can run immediately alongside `algolia-intel-company`.
- Needed before scoring search traffic patterns, keyword intent, and channel mix in the final report.

## Inputs (upstream)

This module has no upstream file dependencies. Inputs are:
- `domain` — the prospect's primary web domain
- `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/` — output directory

## Outputs

Two files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

| File | Key fields |
|---|---|
| `03-traffic-data.md` | Narrative traffic summary with labeled data points |
| `03-traffic-data.json` | `monthly_visits_raw`, `bounce_rate`, `avg_visit_duration_seconds`, `device_split`, `global_rank`, `category_rank`, `top_channels[]`, `organic_search` (branded/non-branded keywords), `paid_search`, `referrals`, `outgoing_traffic`, `geography.top_countries[]`, `demographics`, `popular_pages[]`, `meta` |

Verification gate: both files exist; `03-traffic-data.md` ≥1000 bytes; `meta.skill_enrichment_completed = true`; a `[FACT]` or `[ESTIMATE]` label present. Full pass requires `sources_succeeded ≥ 3`; degraded pass is acceptable when SimilarWeb returns fewer.

## Data sources

| Source | Provides | Method |
|---|---|---|
| SimilarWeb MCP | All traffic metrics — visits, bounce rate, device split, channels, v4 keywords, referrals (desktop + mobile), outgoing traffic, geography, demographics, popular pages | `collect-traffic.py` calls all endpoints; 403 = plan limitation (logged, not a data point); demographics 403 = graceful skip |
| Gemini-grounded Google Search (`gemini_search.py`) | Traffic estimate when SimilarWeb returns `sources_succeeded < 3` or `monthly_visits_raw = null` | `gemini_search.py` with SimilarWeb/Semrush-targeted queries; used only when `grounded: true`; labeled `[ESTIMATE]`; null otherwise |

No-fabrication gate: fallback estimates from `gemini_search.py` used only when `"grounded": true`. If `"grounded": false`, field stays null. Referring industries are not available via SimilarWeb API (UI only) — the `referrals.top_referring_industries` field is always set to the fixed string noting this limitation; do not attempt API collection.

## How PRISM runs it

PRISM invokes this skill via the claude-cli executor as part of Wave 1, running it in parallel with other independent modules (`algolia-intel-company`, `algolia-intel-techstack`). No module must complete before this one starts. The output feeds the traffic and keyword analysis sections of the audit report, and the outgoing traffic data provides search-abandonment signals used in scoring.

## Dependencies

| Item | Detail |
|---|---|
| Script | `~/.claude/skills/algolia-search-audit/scripts/collect-traffic.py` |
| SimilarWeb MCP | Required for full data; 403 responses degrade gracefully; `SIMILARWEB_API_KEY` env var |
| `gemini_search.py` | `~/.claude/skills/algolia-search-audit/scripts/gemini_search.py` — requires `GEMINI_API_KEY`; only invoked in degraded mode |
| Env | `ALGOLIA_AUDIT_DIR`, `SIMILARWEB_API_KEY`, `GEMINI_API_KEY` |

## Notes

- SimilarWeb Search 1.0 keyword endpoints (`/v1/.../organic-search`, `/v1/.../paid-search`, `/v1/.../branded`, `/v1/.../non-branded`) were deprecated February 28, 2025. Use only the unified v4 keywords endpoint (`/v4/website-analysis/keywords`).
- Demographics endpoints may return 403 on non-Business SimilarWeb plans — this is expected; log as unavailable and continue.
- Referring industries (category groupings of referral sources) are not available via the API — UI only. Collect via dashboard screenshot if available and attach to the research folder.
- `03-traffic-data.json` must always be written, even when all SimilarWeb calls fail. Use `meta.degraded_mode = true` and document the reason.
