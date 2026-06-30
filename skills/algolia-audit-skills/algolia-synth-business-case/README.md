# algolia-synth-business-case

> Build the Algolia search ROI business case for a specific prospect, broken into 6 revenue components with conservative and moderate scenarios.

**Version:** 2.0.0 · **Layer/Phase:** Phase 4 — Sales Activation · **Suite:** Algolia Search Audit

## What it does

Takes completed audit research and turns it into a structured business case deliverable. It breaks the search revenue opportunity into six components: conversion lift, AOV increase, bounce rate reduction, no-results recovery, latency/speed gain, and long-tail discovery. All dollar figures are computed deterministically by `calculate-roi.py --components` — the skill never multiplies by hand. The output pre-fills known values from audit data and flags exactly what the AE needs to fill in from the prospect.

## When to use

- "Build the ROI model for [company]"
- "Generate the business case"
- "Run synth-business-case"
- "Give me the component-level breakdown" for an Algolia pitch or AE sales call

## Inputs (upstream)

| File | Required? | Purpose |
|------|-----------|---------|
| `research/08-financial-profile.md` | Required — aborts if missing | Annual revenue, digital revenue share, AOV if available |
| `research/10-scoring-matrix.md` | Required | Which of the 10 search gap areas are confirmed (determines which components are ACTIVE vs CONDITIONAL) |
| `research/03-traffic-data.md` | Required | Monthly visits, bounce rate, pages per visit (SimilarWeb) |
| `research/04-competitors.md` | Optional | Competitor Algolia adoption + Golden Angle evidence for talking point |
| `deliverables/{slug}-audit-data.json` | Optional | `financials`, `traffic`, `findings` fields if the JSON exists |

If `08-financial-profile.md` is missing the skill stops and outputs an error. If `03-traffic-data.md` is missing, traffic inputs are marked `[ESTIMATE — unavailable]`.

## Outputs

`deliverables/{slug}-business-case.md` — a single Markdown file containing:

- Pre-populated inputs table (sourced + labeled [FACT] or [ESTIMATE])
- AE fill-in table (conversion rate, AOV, no-results rate, latency, NLP fail rate)
- 6 component sections, each with: status (ACTIVE/CONDITIONAL/SKIPPED), formula, conservative figure, moderate figure, source label, AE fill-in prompt
- Conservative and moderate scenario totals (verbatim from `calculate-roi.py`)
- Assumption inventory checklist
- Competitor evidence block (only if WebFetch-verified Golden Angle exists)
- AE talking point paragraph

## Data sources

| Source | Provides | Method |
|--------|----------|--------|
| `08-financial-profile.md` | Revenue, digital share, AOV (if captured) | Read upstream audit file |
| `03-traffic-data.md` | Monthly visits, bounce rate | Read upstream audit file (produced by SimilarWeb MCP) |
| `10-scoring-matrix.md` | Gap confirmation per scoring area | Read upstream audit file |
| `04-competitors.md` | Golden Angle evidence | Read upstream audit file (produced by detect-search) |
| `calculate-roi.py --components` | All 6 component dollar figures × 2 scenarios, formula strings, totals | Deterministic script — no in-LLM math |
| WebFetch | Verify competitor case study URLs before citing | Direct URL fetch (if competitor block applies) |

No-fabrication rule: any input marked `[ESTIMATE]` that AE can replace must be listed in the assumption inventory. SKIPPED components are never backfilled with guesses.

## How PRISM runs it

PRISM (the Hermes instance on the VPS) invokes this skill as Layer 3 / Step 3A of the orchestrated pipeline. The orchestrator (`algolia-search-audit`) spawns a Sonnet-class agent that reads `AGENT-CONTEXT.md` first, then calls this skill via the Skill tool with the company slug as argument. It runs after Wave 1 intelligence collection, Wave 2 query generation, and the Layer 2 browser audit are all complete and have passed their gates. Layer 3B (sales plays) reads its output.

## Dependencies

| Item | Detail |
|------|--------|
| `calculate-roi.py` | `~/.claude/skills/algolia-search-audit/scripts/` — runs `--components` with a JSON assumptions object |
| `$ALGOLIA_AUDIT_DIR` | Must be set; fallback is `$(pwd)` with a warning |
| `AGENT-CONTEXT.md` | Read before any other step — governs JSON field names, path conventions, production write declarations |

Abort condition: `08-financial-profile.md` missing → skill stops immediately, outputs error, does not produce partial output.

## Notes

- Every dollar figure in the output file must trace to a line the script emitted. The verification gate diffs the file against script output — any hand-computed number is a blocking violation.
- Components without required inputs (AOV, conversion rate) are marked SKIPPED by the script rather than fabricated. The output file explicitly names what is missing for each SKIPPED component.
- Source labels are mandatory on every data point: `[FACT — {source name}]` for verified figures, `[ESTIMATE]` for defaults, `[AE fill-in required]` when the prospect must supply the number.
