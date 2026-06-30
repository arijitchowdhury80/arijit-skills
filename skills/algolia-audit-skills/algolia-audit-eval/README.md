# algolia-audit-eval

> Score the output of any Algolia audit skill or module across 5 quality dimensions.

**Version:** 2.0.0 · **Layer/Phase:** Phase 3 — Quality Scoring · **Suite:** Algolia Search Audit

## What it does

Runs a structured 5-dimension eval against the output files of any `algolia-audit-*` skill and produces a scored report with a pass/fail verdict. It checks whether required output files exist and meet minimum size thresholds (completeness), whether every data point has a source URL (source density), whether the skill followed its own SKILL.md instructions (instruction adherence), whether a spot-check of 3 data points matches the source scratchpad files (data accuracy), and whether any numbers appear in deliverables without a verifiable source (no fabrication). The mechanical dimensions are handled by a shared deterministic script; only instruction adherence requires LLM judgment.

## When to use

- After a skill run completes and you want to know if the output meets the pass threshold (≥7.0/10)
- After shipping a fix or building a new audit sub-skill, before declaring it production-ready
- After each wave of fixes during a standardisation run (to confirm fixes worked)
- Before any integration test between audit phases

Covers all `algolia-audit-*` modules: research, browser, report, factcheck, financials, live-signals, and others.

## Inputs (upstream)

Takes two arguments: `$1` = skill name to evaluate, `$2` = company slug for test data.

Example: `algolia-audit-eval algolia-audit-research Costco`

Reads whichever files the target skill is expected to produce. Specific file expectations per skill:

| Skill | Expected files | Threshold |
|-------|---------------|-----------|
| `algolia-audit-research` | 12 scratchpad files (01–12) in `research/` | > 2000 bytes each |
| `algolia-audit-browser` | ≥ 10 screenshots in `deliverables/screenshots/` | > 10000 bytes each |
| `algolia-audit-report` | `audit-data.json` + `index.html` in `deliverables/` | > 50000 bytes each |
| `algolia-audit-factcheck` | `factcheck-report.md` + `correction-manifest.md` + `skill-feedback.md` | > 1000 bytes each |
| `algolia-live-signals` | `09b-*.md` + `09c-*.md` in `research/` | > 1000 bytes each |

## Outputs

One file written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/eval/`:

| File | Contents |
|------|----------|
| `{skill-name}-eval-report.md` | Score (X.X/10), per-dimension breakdown, failures, warnings, recommended action |

The report must be ≥ 4000 bytes. It is not a deliverable for the prospect — it is a quality gate for the audit operator and for PRISM.

## Data sources

| Source | Provides | Method |
|--------|----------|--------|
| `factcheck_mechanical.py` | Completeness counts, source density, data accuracy spot-check, no-fabrication check | Script (run first; JSON output feeds Dims 1, 2, 4, 5) |
| Target skill's output files | All scoring inputs | Direct file read and bash checks |

No MCP calls or external web lookups are made. The eval is entirely local.

## How PRISM runs it

PRISM can invoke this skill at any checkpoint in the pipeline to confirm a phase meets quality standards before proceeding. It is not a mandatory pipeline stage for every audit run — it is used during development, after fixes, and as a pre-integration gate. PRISM passes the skill name and company slug as arguments; paths are derived from `$ALGOLIA_AUDIT_DIR`.

## Dependencies

**Script:**
- `factcheck_mechanical.py` (at `~/.claude/skills/algolia-audit-factcheck/scripts/`) — the shared mechanical evaluation engine. Must run first. Its JSON output is mapped into Dimensions 1, 2, 4, and 5. Dimension 3 (instruction adherence) is the only dimension that requires LLM judgment.

**Env / keys:** `$ALGOLIA_AUDIT_DIR` must be set; falls back to current working directory with a warning.

**No MCP servers or API keys required.**

## Notes

- SCORE = (passing_checks / total_checks_run) × 10. Never estimate a score — always show the formula with actual counts.
- CONFIDENCE reflects how many checks ran (coverage), not the score itself. A 10/10 score with LOW confidence means everything that was checked passed, but coverage was partial.
- Pass threshold is ≥7.0. Below 7.0, the eval report lists specific failures with recommended fixes and the skill is not considered production-ready.
- The instruction adherence checklist (Dimension 3) is skill-specific. For `algolia-audit-research`, it checks CHECKPOINT.md step completion, wave execution pattern, MCP-first data collection, and minimum file sizes. For `algolia-audit-report`, it checks Step 0 data refresh, renderer invocation via Skill tool, JSON schema validation, and all 6 deliverables being present. See SKILL.md for the full per-skill checklist.
- Eval reports are written to `eval/` and never overwrite research or deliverable files.
