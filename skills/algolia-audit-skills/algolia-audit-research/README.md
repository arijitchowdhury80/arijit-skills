# algolia-audit-research

> Gather pre-audit intelligence on a prospect company before any browser testing.

**Version:** 2.0.0 · **Layer/Phase:** Phase 1 — Research Orchestrator · **Suite:** Algolia Search Audit

## What it does

Runs a structured 14-step research pipeline against a prospect domain. It collects company context, tech stack, web traffic, competitor landscape, hiring signals, financial data, investor quotes, live social and news signals, and ICP priority mapping — all before any browser test is run. Outputs are written as tagged, cited scratchpad files that every downstream skill reads. Progress is tracked in CHECKPOINT.md so a failed or interrupted run can be resumed.

## When to use

- Starting a new Algolia Search Audit for a prospect
- Preparing a pre-audit dossier before a discovery call
- Running phase 1 on a domain: `algolia-audit-research costco.com`
- Building all context files before Phase 2 browser testing begins
- Refreshing a single step after new information becomes available: `--refresh 9`

## Inputs (upstream)

This is the first skill in the audit pipeline. It takes only:
- `$ARGUMENTS` — prospect URL (e.g., `costco.com`)
- Optional: `--company {name}`, `--refresh {step}`, `--no-browser`

No upstream skill outputs are required. It is the entry point.

## Outputs

13+ files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

| File | Contents |
|------|----------|
| `01-company-context.md` | Company overview, leadership team, vertical, case studies |
| `02-tech-stack.md` | Search vendor (detect-search + SimilarWeb), ecommerce platform, CDN/WAF |
| `03-traffic-data.md` | SimilarWeb 11-endpoint traffic profile with API params header |
| `04-competitors.md` | Top 3–5 competitors, search providers, competitive gap analysis |
| `05-test-queries.md` | 14–18 calibrated test queries for Phase 2 |
| `06-strategic-context.md` | Strategic angles, trigger events, caution signals |
| `07-hiring-signals.md` | ICP-classified open roles, buying committee map |
| `08-financial-profile.md` | 3-year revenue trends, EBITDA margin zone, ROI estimate |
| `09-browser-findings.md` | Placeholder (populated by Phase 2) |
| `09b-social-signals.md` | LinkedIn + Twitter/X posts scored for Algolia relevance |
| `09c-news-signals.md` | Google News — last 60 days, categorized signals |
| `10-scoring-matrix.md` | Placeholder (populated by Phase 3) |
| `11-investor-intelligence.md` | Verbatim exec quotes from earnings calls/10-K/interviews |
| `12-icp-priority-mapping.md` | Exec language → Algolia product → discovery question map |
| `CHECKPOINT.md` | Step-by-step progress log with recovery command |
| `_workspace-manifest.md` | Workspace index with all 14 steps listed |

All data points carry `[FACT]`, `[ESTIMATE]`, or `[OBSERVED]` tags with source URLs at collection time.

## Data sources

| Source | Provides | Method |
|--------|----------|--------|
| detect-search | Search vendor identification via network packet inspection | Script: `collect-techstack.py` |
| SimilarWeb MCP | Traffic, engagement, demographics, keywords, referrals, tech stack | MCP (11 endpoints); script: `collect-traffic.py`, `collect-competitors.py` |
| Yahoo Finance MCP | Revenue, margins, analyst ratings, stock data (public companies) | MCP; script: `collect-financials.py` |
| Apify MCP | LinkedIn jobs, LinkedIn posts, Twitter/X posts, Google News | MCP (3 Actors); ~$0.14/audit |
| Gemini-grounded Google search | Industry benchmarks, strategic angles, trigger events, private company intel | `gemini_search.py` — no-fabrication gate: ungrounded result → empty |
| WebFetch | Earnings call transcripts, SEC EDGAR filings, Algolia customer pages, careers pages | Direct URL fetch |

BuiltWith is retired. Tech stack detection uses detect-search (primary) + SimilarWeb technologies (cross-check). WebSearch is retired for open-web research; Gemini-grounded search replaces it.

## How PRISM runs it

PRISM (the Hermes agent instance on the VPS) invokes this skill via the claude-cli executor as the first step of an audit pipeline run. It must complete in full before Phase 2 browser testing or Phase 3 report generation can start. The 14 steps run sequentially by default; parallel Wave execution (Wave 1 → Wave 2 → Wave 3 → Wave 4) is available when the `claudesp` runner and CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 are active on the VPS executor.

## Dependencies

**Scripts** (run from `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`):
- `collect-techstack.py` — Step 2 (detect-search + SimilarWeb)
- `collect-traffic.py` — Step 3 (SimilarWeb 11 endpoints)
- `collect-competitors.py` — Step 4 (SimilarWeb similar-sites)
- `collect-financials.py` — Step 9 (Yahoo Finance, public companies only)
- `calculate-roi.py` — Step 9 (ROI formula appended to 08-financial-profile.md)
- `calculate-score.py` — Phase 3 (scoring formula, called by algolia-audit-report)

**MCP servers required:**
- SimilarWeb MCP (Steps 2, 3, 4, 6)
- Yahoo Finance MCP (Steps 1, 9, 12 — public companies)
- Apify MCP (Step 8 — live signals)

**Env / keys:**
- `$ALGOLIA_AUDIT_DIR` — base directory for all audit workspaces
- SimilarWeb API key, Yahoo Finance MCP, Apify API token

**Abort condition:** If `collect-techstack.py` returns `algolia_detected=true` in the JSON output at Step 2, the audit stops immediately — the prospect is already an Algolia customer.

## Notes

- All traffic data must use a consistent `web_source` parameter across a single audit (`total` preferred; fall back to `desktop` and label all metrics accordingly). Mixing `total` and `desktop` in the same file makes fact-checking impossible.
- Article date verification is mandatory at Step 10: any news article older than 18 months is classified as "Historical Context", not a timing signal.
- SimilarWeb "TAG DETECTED" for a search vendor does not mean the vendor is active. Active status is only confirmed in Phase 2 via live network request inspection.
- The `--refresh {step}` flag re-runs only the specified step, leaving all other scratchpad files untouched.
