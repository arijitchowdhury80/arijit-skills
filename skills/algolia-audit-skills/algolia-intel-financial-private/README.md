# algolia-intel-financial-private

> Estimate revenue for private companies using a 6-source waterfall — all figures labeled [ESTIMATE], confidence tier computed deterministically, never by prose judgment.

**Version:** 2.0.0 · **Layer/Phase:** Layer 1F / Wave 1 · **Suite:** Algolia Search Audit

## What it does

Runs `collect-financials.py --private` to initiate the output file structure, then runs all 6 sources in parallel: ecdb.com/PitchBook/Crunchbase (WebFetch), LinkedIn headcount (WebFetch), CEO/founder interview transcripts (Gemini-grounded search + WebFetch), trade press (Gemini-grounded search), Inc 5000/Deloitte Fast 500 rankings (Gemini-grounded search), and job posting volume from hiring signals. All 6 outputs are fed into `reconcile_financials.py`, which computes a confidence tier (HIGH/MEDIUM/LOW) and a revenue range deterministically. No single-point estimates — always min/median/max.

## When to use

- The prospect is a private company with no stock ticker and no SEC filings.
- For public companies (ticker + SEC filings), use `algolia-intel-financial-public` instead.

## Inputs (upstream)

| File | Used for |
|---|---|
| `01-company-context.json` | Company name, domain, employee count baseline, hiring signals reference |

## Outputs

Two files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

| File | Key fields |
|---|---|
| `08-financial-profile.md` | Revenue estimate range (min/median/max), confidence tier, source breakdown, all figures labeled `[ESTIMATE]` |
| `08-financial-profile.json` | Top-level: `revenue_confidence` (HIGH/MEDIUM/LOW), `revenue_sources[]`, `sources_succeeded[]`, `sources_failed[]`; nested: `company_overview`, `financials`; `meta.company_type = "private"` |

Verification gate: both files ≥3000 bytes; revenue estimate present with `[ESTIMATE]` label; `revenue_confidence` at top level in JSON; `revenue_sources[]` at top level with ≥2 entries; `sources_succeeded` does NOT include `yahoo_finance`; `meta.skill_enrichment_completed = true`.

## Data sources

| Source | Provides | Method |
|---|---|---|
| ecdb.com / PitchBook / Crunchbase | Revenue estimate | WebFetch direct |
| LinkedIn | Employee headcount (revenue proxy) | WebFetch `linkedin.com/company/{slug}` |
| CEO/founder interviews | Revenue mentions, growth language | `gemini_search.py` locates transcripts; WebFetch retrieves them |
| Trade press (RetailDive, WWD, TechCrunch) | Revenue or funding figures | `gemini_search.py` with site-scoped queries; `grounded: true` required |
| Inc 5000 / Deloitte Fast 500 | Ranking-implied revenue bracket | `gemini_search.py`; `grounded: true` required |
| Job posting volume | Revenue proxy (hiring activity) | Count from hiring signals module output |

No-fabrication gate: all `gemini_search.py` results used only when `"grounded": true`. Revenue from trade press, ranking lists, and interviews still carries `[ESTIMATE]` — the `[ESTIMATE]` label applies to all private-company revenue figures regardless of source. Never use `[FACT]` for private company revenue.

## How PRISM runs it

PRISM invokes this skill via the claude-cli executor in Wave 1, routing to it only when `algolia-intel-company` (1A) confirms the company is private. It runs in parallel with other Wave-1 modules. The overwrite guard (`BUG-5`) prevents a public-path profile from being clobbered if both paths fire. The `reconcile_financials.py` script must be called — do not judge confidence tier in prose.

## Dependencies

| Item | Detail |
|---|---|
| Script | `~/.claude/skills/algolia-search-audit/scripts/collect-financials.py` (run with `--private`) |
| `gemini_search.py` | `~/.claude/skills/algolia-search-audit/scripts/gemini_search.py` — requires `GEMINI_API_KEY` |
| `reconcile_financials.py` | `~/.claude/skills/algolia-search-audit/scripts/reconcile_financials.py` — mandatory; computes confidence tier and range from candidate array |
| Upstream | `01-company-context.json` must exist and classify the company as private |
| Overwrite guard | Script exits 2 if `08-financial-profile.md` already exists as a public-path file; use `--force` only after confirming company is genuinely private (backs up to `.public.bak`) |

## Notes

- Report the revenue as a range (min/median/max) — never collapse to a single point estimate.
- `revenue_confidence`, `revenue_sources`, `sources_succeeded`, and `sources_failed` are top-level JSON keys — not nested inside `meta` or any other object.
- Yahoo Finance must never appear in `sources_succeeded` — this module does not use it.
- Job posting volume as a revenue proxy (Source 6) is always labeled `[OBSERVED]`, not `[ESTIMATE]`.
