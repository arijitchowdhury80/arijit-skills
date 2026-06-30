# algolia-audit-factcheck

> Quality gate for Algolia Search Audit deliverables — returns a PROCEED/WARN/BLOCKED verdict before prospect or AE handoff.

**Version:** 2.0.0 · **Layer/Phase:** Phase 3 — Fact-Check Gate · **Suite:** Algolia Search Audit

## What it does

Verifies every factual claim in the audit deliverables against its original source. It re-calls the same MCP APIs used during Phase 1 (SimilarWeb, Yahoo Finance), WebFetches every source URL cited in the deliverables, checks investor quotes against their original transcripts, and confirms case study metrics are live and accurate. Cross-file consistency (whether the same number appears correctly across the report, SPA, AE brief, and signal brief) is only 10% of the job — external verification of the information itself is the other 90%. Produces a scored report, a machine-readable correction manifest, a FACTCHECK_GATE.md verdict file, and a skill-feedback document identifying systemic root causes.

## When to use

- Audit report generation is complete (all 9 deliverables produced by `algolia-audit-report`)
- Before sharing any deliverable with a prospect or AE
- After fixing issues from a previous factcheck run to re-score
- When you need to know if stats in the deck match the main report, or if source URLs are still live

Not for running the audit, generating reports, or checking individual files in isolation.

## Inputs (upstream)

Reads from `$ALGOLIA_AUDIT_DIR/{CompanyName}/`:

| Input | Used for |
|-------|----------|
| All 12 scratchpad files (`research/01–12`) | Ground truth for all claim verification |
| `{slug}-audit-data.json` | Structured data: findings, scores, signals, quotes, ROI |
| `{slug}/index.html`, `ae-report.html`, `battle-card.html`, `leave-behind.html` | Cross-file consistency checks |
| `{slug}-ae-precall-brief.md`, `{slug}-strategic-signal-brief.md` | Citation coverage, quote traceability |
| `research/09-browser-findings.md` + `screenshots/` | Browser observation fidelity |
| `research/10-scoring-matrix.md` | Scoring completeness gate |

## Outputs

4 files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/` (and one to `research/`):

| File | Purpose |
|------|---------|
| `{slug}-factcheck-report.md` | 20-dimension scored verification report with per-claim status |
| `{slug}-correction-manifest.md` | Atomic fix list: file + field + wrong value + correct value |
| `research/FACTCHECK_GATE.md` | Machine-readable gate — orchestrator reads this to decide whether to stage/publish |
| `{slug}-skill-feedback.md` | Root-cause patterns + specific SKILL.md text changes to prevent recurrence |

`FACTCHECK_GATE.md` format:
```
SCORE: {x.x}
CONFIDENCE: HIGH|MODERATE|LOW
ACTION: PROCEED|WARN|BLOCKED
BLOCKING_COUNT: {n}
WARNING_COUNT: {n}
```

## Data sources

| Source | Provides | Method |
|--------|----------|--------|
| SimilarWeb MCP | Re-verification of traffic, tech, competitor data | MCP re-call with same params as Phase 1 (Standard/Full tier) |
| Yahoo Finance MCP | Re-verification of financial figures | MCP re-call (Standard/Full tier) |
| WebFetch | Quote verification against transcripts; source URL liveness; impact stat confirmation | Direct URL fetch — mandatory for every non-empty `impact_stat` field |
| detect-search | Competitor search vendor re-verification | Network inspection (Full tier) |
| `factcheck_mechanical.py` | Completeness counts, source density, placeholder detection, money spot-check | Script — run first, before any LLM verification |

## How PRISM runs it

PRISM runs this skill after `algolia-audit-report` completes. It reads `FACTCHECK_GATE.md` to decide the next action: PROCEED stages the audit for review and potential publish; WARN stages with a required acknowledgment gate; BLOCKED halts the pipeline until issues are corrected and the factcheck is re-run. PRISM passes the company name as the argument and optionally `--tier standard` for time-constrained runs.

## Dependencies

**Script:**
- `factcheck_mechanical.py` (at `~/.claude/skills/algolia-audit-factcheck/scripts/`) — deterministic script covering completeness, source density, no-fabrication placeholder grep, money spot-check, and optional URL liveness (`--check-urls --url-sample 8`). Must run before any LLM-based verification. Exit 0 = no mechanical blocker; exit 2 = BLOCKED.

**MCP servers required:**
- SimilarWeb MCP (Standard and Full tiers)
- Yahoo Finance MCP (Standard and Full tiers)

**No additional env keys** beyond what Phase 1 used. `$ALGOLIA_AUDIT_DIR` must be set.

**Execution tiers:**

| Tier | Time | External calls | What runs |
|------|------|----------------|-----------|
| Quick | ~3–5 min | 0 | Read-only: consistency + math + reference data only (Dims 1–3) |
| Standard | ~15 min | ~15–20 | + SimilarWeb re-calls + WebFetch sample URLs |
| Full (default) | ~30–40 min | ~30–40 | + all source URLs + competitor APIs + browser re-tests |

**Agent topology (Standard/Full):**
- Agent 1: Claim registry + Dims 1–3 (sequential, must complete first)
- Agents 2–4: API data accuracy, source citations + investor quotes, browser fidelity (parallel)
- Agent 5: Pattern analysis (after Agents 2–4)
- Team lead: Score aggregation + 4 output files

**Blocking conditions (checked before all 20 dimensions):**
- ABX campaign touches contain placeholder bodies ("Pending", TBD, or < 100 chars)
- `10-scoring-matrix.md` is a stub (scoring not run)
- `icp_mapping.priority_to_product` items have no `evidence` or `proof_url`
- `strategic_angles` is an empty array or missing required fields
- `findings` is empty despite browser testing having been done

## Notes

- The impact stat verification check runs at every tier, including Quick. It is always an external call: WebFetch the `impact_stat_source` URL and confirm the exact number appears on that page. A stat with a plausible-looking URL that doesn't actually contain the number is a BLOCKING failure — this is the single highest-frequency hallucination vector in the audit pipeline.
- The evidence tier system classifies every claim as AUTHENTIC (MCP/SEC/official IR), WEBFETCH (third-party page verified), WEBSEARCH (Gemini-grounded, URL cited but not WebFetch-confirmed), or NO_SOURCE (→ DROP). An unflagged Tier 2 (WEBSEARCH) claim is penalised the same as a Tier 3 (NO_SOURCE) removal.
- SimilarWeb data has a 15% tolerance band — monthly estimates drift naturally. A ±15% re-call result is `[STALE]`, not `[DISC]`. Drifts over 30% are `[DISC]` and blocking.
- When re-calling SimilarWeb, always use the same `web_source`, `country`, and date range parameters recorded in `03-traffic-data.md`. Comparing a `total` value against a `desktop` re-call is not a discrepancy — it is a methodology error by the verifier.
- `skill-feedback.md` is mandatory even when ACTION is PROCEED. At minimum, it must state "no critical patterns found" and list what was verified correctly.
