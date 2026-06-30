# algolia-intel-industry

> Collect vertical industry benchmarks, trend data, and expert analyst quotes for a prospect's specific industry, then generate an Algolia-specific positioning angle grounded in those findings.

**Version:** 2.0.0 · **Layer/Phase:** Wave 1 Intel Module · **Suite:** Algolia Search Audit

## What it does

Runs a two-step pipeline to build the industry-intelligence layer of an audit. First, `collect-industry.py` fires Gemini-grounded search queries to pull benchmark stats (Baymard, Forrester, NRF), 2025–2026 trend data, and named analyst quotes for the prospect's vertical. Then, LLM enrichment fills two fields the script cannot generate mechanically: `algolia_angle` (one sentence connecting the top industry trend to why this specific company needs Algolia now) and `competitor_search_landscape` (what search investments competitors in the vertical are making). A 24-month staleness gate is enforced at collection time; any result older than 24 months is excluded.

## When to use

- User explicitly invokes `algolia-intel-industry` for a named company.
- User asks for "industry intelligence" or "industry benchmarks" for an audit prospect.
- User wants bigger-picture vertical context for a sales narrative.
- `industry-intel.md` is missing from the audit workspace and needs to be produced.
- Distinct from `algolia-intel-competitors` (specific companies) and financial profile (company financials) — this skill covers the broader vertical and what's happening across the industry.

## Inputs (upstream)

- `$ARGUMENTS` — company slug; resolves to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`
- `01-company-context.json` — reads `vertical`, `primary_market`, `company_name` (graceful if missing; `--vertical` flag can override)
- `04-competitors.md` — read during LLM enrichment for `competitor_search_landscape` (optional; used if present)

## Outputs

Two paired files under `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

- `industry-intel.md` — human-readable report with sections: Vertical Overview, Key Benchmarks table (with FACT/ESTIMATE labels and source URLs), 2025–2026 Trends, Expert Quotes, Algolia Vertical Positioning, Sources.
- `industry-intel.json` — machine-readable version with fields: `vertical`, `primary_market`, `benchmarks[]`, `trends_2025_2026[]`, `expert_quotes[]`, `trend_headline`, `trend_source_url`, `algolia_angle`, `competitor_search_landscape`, `_meta`.

## Data sources

| Source | Provides | Method |
|--------|----------|--------|
| Gemini-grounded Google search (`collect-industry.py`) | Benchmark stats, trend data, analyst quotes for the vertical | `gemini_search` primary path; `grounded: true` required for `[FACT]` labels — `grounded: false` leaves the field null, never falls back to ungrounded model knowledge |
| `gemini_search.py` | Fallback benchmark/trend/quote queries when script collection fails | Direct invocation with staleness gate; same no-fabrication rule applies |
| Scout (`http://localhost:8421`) | Full markdown content from benchmark pages (Baymard, Forrester, NRF) | `industry_fallback_filter.py scout <url>` guard; Scout-first, WebFetch fallback when Scout returns degraded/empty markdown |
| WebFetch | Benchmark page content when Scout is degraded or below threshold | Fallback from Scout; label `[FACT — via WebFetch, date, url]` only when stat is confirmed on the fetched page |

## How PRISM runs it

PRISM (the Hermes instance on the VPS) invokes this skill via the claude-cli executor as part of the `algolia-audit-research` Wave 1 orchestration. It runs after `algolia-intel-company` (which provides the `vertical` and `primary_market` fields needed by the collection script) and benefits from `algolia-intel-competitors` being complete so the `competitor_search_landscape` enrichment step has data to work from. The output files land in the company's research directory and are consumed downstream by the report-generation phase (`algolia-audit-report`) for benchmark citations and vertical positioning copy.

## Dependencies

- `collect-industry.py` — primary collection script (`~/.claude/skills/algolia-search-audit/scripts/`)
- `gemini_search.py` — fallback search helper (same scripts directory)
- `industry_fallback_filter.py` — 24-month age-gate filter for fallback results and Scout degradation guard
- `GEMINI_API_KEY` — required for Gemini-grounded search
- Scout at `http://localhost:8421` — for benchmark-page content fetching (co-hosted on VPS)
- `01-company-context.json` upstream output; `--vertical` flag substitutes if JSON is missing

## Notes

- The 24-month staleness gate is enforced by `collect-industry.py` on the Gemini-grounded path. The `gemini_search.py` fallback has NO built-in age filter — `industry_fallback_filter.py` must be run on every fallback result before use to preserve the same freshness guarantee.
- Scout is embedded ONLY for industry-benchmark pages (Baymard, Forrester, NRF) — the one proven Scout win for this skill. For all other URL types, use WebFetch directly.
- Anonymous expert quotes are not permitted in deliverables. Entries without a named speaker are removed during LLM enrichment (Step 2c Task 4).
- Verification gate: `industry-intel.md` ≥ 1000 bytes, `benchmarks[]` non-empty, `primary_market` non-null, `algolia_angle` non-null and non-empty, `vertical` non-empty, `_meta` present in JSON. Any gate failure stops execution.
