# algolia-audit-report

> Generate the full audit deliverable package from a completed research and browser workspace.

**Version:** 2.0.0 · **Layer/Phase:** Phase 3 — Report Generation · **Suite:** Algolia Search Audit

## What it does

Scores the prospect's search experience across 10 areas, writes a machine-readable `audit-data.json`, runs it through a deterministic renderer to produce HTML deliverables, generates a PDF leave-behind, writes an AE pre-call playbook and a strategic signal brief, and triggers the ABX campaign skill. It reads directly from the 12 Phase 1 scratchpad files and the Phase 2 browser findings — no information is synthesised from memory. Every deliverable is produced by either Claude reading from scratchpad files or by deterministic scripts; Claude never writes layout HTML.

## When to use

- All 12 Phase 1 scratchpad files are fully populated (each ≥ 30 lines)
- `09-browser-findings.md` has real findings (≥ 50 lines), not a stub
- `deliverables/screenshots/` has ≥ 8 real screenshots on disk
- `10-scoring-matrix.md` is NOT yet a stub ("Phase 3 — not yet run")
- The user says research and browser testing are done and wants the full report

Not for starting audits, running browser tests, or editing individual files in isolation.

## Inputs (upstream)

All files at `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

| File | Used in |
|------|---------|
| `01-company-context.md` | Company snapshot, executives, case studies |
| `02-tech-stack.md` | Current search vendor (ACTIVE confirmed), ecommerce platform |
| `03-traffic-data.md` | Traffic profile, channels, demographics, referrals, paid search |
| `04-competitors.md` | Competitor names, search vendors, competitive gap analysis |
| `05-test-queries.md` | Queries tested in Phase 2 |
| `06-strategic-context.md` | Strategic angles, trigger events |
| `07-hiring-signals.md` | Buying committee, open roles, objection counters |
| `08-financial-profile.md` | Revenue, EBITDA, margin zone, ROI scenarios |
| `09-browser-findings.md` | Browser observations, per-step results |
| `10-scoring-matrix.md` | Scoring area scores and severities (written by this skill in Phase 3) |
| `11-investor-intelligence.md` | Verbatim exec quotes with source URLs |
| `12-icp-priority-mapping.md` | Exec language → Algolia product → discovery question |
| `deliverables/screenshots/` | ≥8 PNG files referenced by findings |

Optionally reads `partner-intel.json` if present.

## Outputs

9 deliverables produced in `$ALGOLIA_AUDIT_DIR/{CompanyName}/`:

| File | Audience |
|------|----------|
| `{slug}-audit-data.json` | Internal — feeds the renderer |
| `{slug}/index.html` | AE/SE/BD — dual-view SPA |
| `{slug}/ae-report.html` | AE — full HTML report |
| `{slug}/battle-card.html` | AE/SE — competitive battle card |
| `{slug}/leave-behind.html` | Prospect — leave-behind |
| `{slug}-leave-behind.pdf` | Prospect — PDF version |
| `{slug}-playbook.md` | AE/BDR/Partner — BLUF + MEDDPICC + discovery Qs + objections |
| `{slug}-strategic-signal-brief.md` | LLM/CRM — signal-dense 1-pager |
| `abx-campaign/` | AE/BDR — 5-email sequence + LinkedIn + Loom script (via `algolia-campaign-abx`) |

## Data sources

| Source | Provides | Method |
|--------|----------|--------|
| Phase 1 scratchpad files (01–12) | All structured research data | Direct file read (copy-paste mandate — never from memory) |
| Phase 2 browser findings | Gap observations, screenshot references | Direct file read |
| `calculate-score.py` | Weighted overall score from 10 area scores | Script (Phase 3b) |
| `generate-audit-data.py` | Type-safe patch of structural JSON fields | Script (Phase 5a-patch) |
| `validate-json-schema.py` | Schema validation before render | Script (automatic in 5a-patch) |
| `render-audit.ts` (Deno) | HTML rendering from audit-data.json + templates | Script (Phase 5b) |
| `generate-pdf.sh` | PDF generation from leave-behind HTML | Script (Phase 5c) |
| WebFetch | Case study URL verification, Algolia customer pages | Direct fetch (mandatory before citing any case study) |
| `algolia-campaign-abx` skill | ABX email sequence generation | Skill invocation (Phase 5f) |

No open-web search is used during report generation. All content comes from Phase 1 and Phase 2 outputs. The copy-paste mandate applies: financial figures, quotes, and competitor data are copied verbatim from scratchpad files — never reconstructed from context memory.

## How PRISM runs it

PRISM invokes this skill after confirming Gate 2 (browser testing) has passed. It is the third stage of the pipeline. The skill reads `FACTCHECK_GATE.md` at the end to determine whether the audit can proceed to sharing or requires factchecking first. PRISM passes the company slug as the argument; all paths are derived from `$ALGOLIA_AUDIT_DIR`.

## Dependencies

**Scripts** (all in `~/.claude/skills/algolia-search-audit/scripts/`):
- `calculate-score.py` — required at Phase 3b; produces `overall_score` used everywhere downstream
- `generate-audit-data.py` — required at Phase 5a-patch; patches type-unsafe fields (strings, arrays, score breakdown)
- `validate-json-schema.py` — run automatically by 5a-patch; must return PASS before rendering
- `render-audit.ts` — Deno renderer; reads `audit-data.json` + templates, writes all HTML deliverables
- `generate-pdf.sh` — PDF generation; skip with `--skip-pdf`
- `validate-workspace.sh` — pre-flight workspace check

**MCP servers:** None required during Phase 3–5. WebFetch is used for case study URL verification.

**Templates** (read-only, do not modify):
- `index-template.html`, `ae-action-report-template.html`, `strategic-battle-card-template.html`, `prospect-leave-behind-template.html`, `components.css`

**Env / keys:** `$ALGOLIA_AUDIT_DIR`; Deno runtime for the renderer.

**Capability matrix constraint:** The SPA renderer uses 4 fixed column keys (`nike_has`, `asics_has`, `on_running_has`, `new_balance_has`). For any non-running-shoe company, `matrix_col_labels` in `audit-data.json` MUST map these keys to the actual competitor names; leaving it null causes the SPA to render Brooks Running defaults.

## Notes

- The weighted scoring formula (HIGH×2.0, MEDIUM×1.0, LOW×0.5) is computed only by `calculate-score.py`. Never hand-average the 10 area scores.
- The overall score written into `audit-data.json` must match the script output exactly. `generate-audit-data.py` recalculates the same formula as a consistency check — if they differ, a number was typed incorrectly.
- Context compaction corrupts numerical data in memory. The pre-deliverable data refresh (re-reading all 5 critical scratchpad files before each deliverable phase) is mandatory, not optional.
- ABX campaign generation (Phase 5f via `algolia-campaign-abx`) is not optional. The completion gate blocks if `abx_sequence.touches` contains any placeholder bodies.
- The recommended next step after this skill completes is always `/algolia-audit-factcheck {slug}`.
