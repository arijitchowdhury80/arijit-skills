# algolia-campaign-abx

> Generate a complete Account-Based Experience (ABX) outreach package for a prospect who has received an Algolia Search Audit — 5 emails, 3 LinkedIn messages, a Loom script, and a collateral schedule.

**Version:** 2.0.0 · **Layer/Phase:** Phase 4 — Sales Activation (Layer 3D) · **Suite:** Algolia Search Audit

## What it does

Takes the completed audit deliverables and produces 10 campaign files, all personalized using live audit data: specific browser findings (exact query + result observed), verbatim executive quotes, competitor intelligence, and sourced financial figures. The campaign scope is determined by the signal tier in the playbook (Tier 1 = full 5-email + LinkedIn + Loom; Tier 2 = 3-email + LinkedIn; Tier 3 = Email 1 only). After writing the files, a deterministic script (`generate-abx-json.py`) patches `{slug}-audit-data.json` with the full campaign copy — the SPA renders directly from this JSON.

## When to use

- "Build the ABX campaign for [company]"
- "Generate the outreach package for [company]"
- "Run algolia-campaign-abx"
- Any full-pipeline run via `algolia-search-audit` (this skill runs automatically as Layer 3D)

## Inputs (upstream)

| File | Required? | Purpose |
|------|-----------|---------|
| `deliverables/{slug}-playbook.md` | Required — halts if missing | Signal tier determination + talking points |
| `research/09-browser-findings.md` | Required — halts if missing | Specific findings (exact query + result) for Email 1 hook and Loom script |
| `research/11-investor-intelligence.md` | Recommended | Executive quotes for personalization across all touches |
| `research/04-competitors.md` | Optional | Golden Angle evidence for Email 2; falls back to defensive play if absent |
| `research/08-financial-profile.md` | Optional | Revenue figures for Email 3; proceeds without if missing, noted in schedule |
| `deliverables/screenshots/` | Optional | Screenshot filenames for Loom script; Loom proceeds without if empty, noted in gate |

## Outputs

All files written to `deliverables/abx-campaign/`:

| File | Contents |
|------|----------|
| `email-1-hook.md` | SCR-structured hook email — specific browser finding + exact query tested |
| `email-2-competitor.md` | Golden Angle play (named competitor confirmed by detect-search) or Defensive play |
| `email-3-business-case.md` | Revenue-specific subject line, one ROI formula component from `calculate-roi.py` |
| `email-4-social-proof.md` | Vertical-matched case study with WebFetch-verified URL |
| `email-5-breakup.md` | Honest close, parting resource link, no urgency language |
| `linkedin-connect.md` | Connection request ≤ 300 characters, role-specific finding |
| `linkedin-followup-1.md` | Credibility-only follow-up, no ask |
| `linkedin-followup-2.md` | Soft meeting ask using competitor or business case angle |
| `loom-script.md` | Timed 2-minute video script (200–280 words), references actual screenshot filenames |
| `collateral-schedule.md` | Signal tier declaration + sequenced touch table with timing |

`{slug}-audit-data.json` → `abx_sequence.touches[]` is also populated (by `generate-abx-json.py`) so the SPA can render the campaign.

## Data sources

| Source | Provides | Method |
|--------|----------|--------|
| `{slug}-playbook.md` | Signal tier, MEDDPICC context, talking points | Read upstream Phase 4 output |
| `09-browser-findings.md` | Specific findings, screenshot file references | Read upstream Layer 2 output |
| `11-investor-intelligence.md` | Verbatim executive quotes | Read upstream Wave 1 output |
| `04-competitors.md` | Confirmed competitor search vendor (detect-search) for Email 2 | Read upstream Wave 1 output |
| `08-financial-profile.md` | Annual revenue, digital revenue figures | Read upstream Wave 1 output |
| `calculate-roi.py` | Single ROI component figure for Email 3 | Deterministic script — no in-LLM arithmetic |
| WebFetch | Verify case study URLs for Email 4 before citing | Direct URL fetch |

No-fabrication gates: Golden Angle is used only when detect-search confirmed the competitor; financial figures sourced only from `08-financial-profile.md`, Yahoo Finance, or SEC; case studies cited only when URL is WebFetch-verified.

## How PRISM runs it

PRISM invokes this skill as Layer 3D — it runs after the full Layer 3 report and deliverables step has passed its gate (`{slug}-audit-data.json` and `{slug}/index.html` both exist). The orchestrator spawns an Opus-class agent that reads `AGENT-CONTEXT.md` first, then calls this skill via the Skill tool with the company slug as argument. Layer 4 (factcheck) runs after this step and gates publication.

## Dependencies

| Item | Detail |
|------|--------|
| `generate-abx-json.py` | `~/.claude/skills/algolia-search-audit/scripts/` — patches `abx_sequence.touches[]` in the audit JSON; must exit 0 (≥ 3 touches extracted) |
| `calculate-roi.py` | Same scripts dir — provides the single revenue figure used in Email 3 |
| `algolia-brand-check` | Optional sub-skill; invoked after writing all 10 files; skipped gracefully if not installed |
| `$ALGOLIA_AUDIT_DIR` | Must be set; fallback is `$(pwd)` with a warning |
| `AGENT-CONTEXT.md` | Read before any other step — governs platform rules and `abx_sequence` JSON schema |

## Notes

- `generate-abx-json.py` is not optional — hand-assembling the JSON is a documented failure class that leaks Source notes into sendable copy, drops `video_script` (blanking the Loom panel in the SPA), and mislabels channel fields.
- Email 3 must use a figure from `calculate-roi.py` output, not in-LLM arithmetic. This is the same constraint as `algolia-synth-business-case`.
- LinkedIn messages are plain text (no Markdown — LinkedIn does not render it). Character count is included in the file.
- Loom script references must be actual filenames from `deliverables/screenshots/`; fictional filenames are a blocking violation.
- The verification gate checks all 10 files, the JSON patch, `video_script` field, and warns on `TBD` / placeholder strings before reporting completion.
