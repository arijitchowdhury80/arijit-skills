---
name: algolia-audit-factcheck
version: 2.0.0
description: Use to validate Algolia Search Audit deliverables before sharing with a prospect or AE. Triggers when you need to: check whether stats in the deck match the main report, verify source citations are live links, confirm investor quotes against original transcripts, catch cross-file inconsistencies across the 6 deliverable files, or get a PROCEED/WARN/BLOCKED gate verdict before a pitch or handoff. Run this after the audit is complete — it's the quality gate step that tells you if the audit is safe to share. Not for running the audit itself, generating reports, or checking individual files in isolation.
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Input
$ARGUMENTS — company name (e.g., Costco). Workspace at $ALGOLIA_AUDIT_DIR/{CompanyName}/
Optional: --tier quick|standard|full (default: full) | --dim {1,4} to run specific dimensions

## Evidence Tier System (applies to EVERY claim)
| Tier | Definition | Action |
|------|-----------|--------|
| AUTHENTIC | MCP API, SEC EDGAR, official IR, official press release | Keep — cite normally |
| WEBFETCH | Third-party article WebFetched — claim appears on page | Keep — label with source URL |
| WEBSEARCH | Found via Gemini-grounded search (gemini_search.py) — URL citation provided but not WebFetch-verified | Keep — amber ⚠️ warning label |
| NO_SOURCE | No verifiable source exists | **DROP — remove entirely. No hedging.** |

## ⚠️ COMPLETENESS GATE — BLOCKING CHECKS (run BEFORE all other dimensions)

These are BLOCKED (not WARN) if any of the following are true. Do not proceed to scoring dimensions until all pass.

### BLOCKED — ABX Campaign Incomplete
Check `audit-data.json → abx_sequence.touches`. Every touch must have a `body` field that is NOT:
- Empty string `""`
- `null`
- Any string containing "Pending" or "pending" or "TBD"
- Fewer than 100 characters

If ANY touch body is a placeholder → **BLOCKED: ABX campaign not generated. Run `algolia-campaign-abx` before factcheck.**

### BLOCKED — Scoring Not Run
Check `research/10-scoring-matrix.md`. File must:
- Exist
- Be ≥ 30 lines
- Contain actual numeric scores (e.g., `2/10`, `4/10`) — not just "Phase 3 — not yet run"

If scoring file is a stub → **BLOCKED: Scoring not complete. Run Phase 3 (10-area scoring) before factcheck.**

### BLOCKED — Discovery Questions Have No Citations
Check `audit-data.json → icp_mapping.priority_to_product`. Every item must have:
- `evidence` or `exact_quote` (non-empty) — the exec quote that justifies the question
- `proof_url` when `proof_company` is set

If Q cards have no evidence → **BLOCKED: Discovery questions unverifiable. Add exec quote + source URL to each.**

### BLOCKED — Strategic Angles Unpopulated
Check `audit-data.json → strategic_angles`. Must be a non-empty array. Each angle must have `hook`, `discovery_question`, `source`, and `algolia_proof`. If empty array or any required field missing → **BLOCKED: Run audit-report Phase 5a to generate strategic angles.**

### BLOCKED — Findings Unpopulated (if browser testing was done)
If `research/09-browser-findings.md` exists with ≥ 50 lines, then `audit-data.json → findings` must be a non-empty array. If findings is `[]` despite browser testing having been done → **BLOCKED: Browser findings not loaded into audit-data.json.**

---

## Mechanical dimensions — run the script FIRST (deterministic, not by hand)

The mechanical dimensions (completeness, source-density, cross-file money consistency,
no-fabrication placeholder/unsourced-impact grep, a money spot-check, and optional URL liveness)
are implemented as a deterministic script. **Run it before doing any LLM verification** and read its
JSON — do NOT re-derive these counts by hand (that is non-deterministic and the whole point of the
script is reproducibility):

```bash
python3 ~/.claude/skills/algolia-audit-factcheck/scripts/factcheck_mechanical.py \
  --audit-dir "$ALGOLIA_AUDIT_DIR" --company "{CompanyName}" [--check-urls --url-sample 8]
# exit 0 = no mechanical blocker; exit 2 = BLOCKED (placeholder / missing required file / dead URL)
# JSON.mechanical_action is PROCEED|BLOCKED — feed BLOCKED reasons straight into FACTCHECK_GATE.md
```

The script covers ONLY mechanical truths. The **judgment** dimensions below (quote-vs-transcript
authenticity, "does this claim match the evidence", competitive-claim accuracy) stay on the LLM and
are NOT in the script. If the script says BLOCKED, the gate is BLOCKED regardless of LLM dimensions.

## 20 Verification Dimensions
**Group A (Intelligence modules 1-11):** Company context, tech stack, traffic params, competitor claims, financial integrity, investor quote verification, hiring URL validity, social currency, news freshness, industry benchmarks, partner data
**Group B (Browser — Dim 12):** Screenshots on disk, file sizes >50KB, queries match claims
**Group C (Synthesis — Dims 13-17):** Scoring justification, competitive claims, ROI math, sales play specificity, case study vertical relevance
**Group D (Deliverables — Dims 18-20):** Source coverage, cross-deliverable consistency, arithmetic
**Group E (Completeness + Citations — Dims 21-23):** ABX campaign populated, citation baseline (all source_url fields present), discovery question evidence attached

## Execution Tiers
| Tier | Time | External calls | What runs |
|------|------|---------------|-----------|
| Quick | ~3-5 min | 0 | Dims 1-3: consistency + math + reference data only |
| Standard | ~15 min | ~15-20 | + SimilarWeb re-calls + WebFetch sample URLs |
| Full (default) | ~30-40 min | ~30-40 | + all source URLs + competitor APIs + browser re-tests |

**External verification is 90% of the job. Cross-file consistency is 10%.**

## Output
4 files — ALL MANDATORY. Do not skip any. Write them in this order:

1. `deliverables/{slug}-factcheck-report.md` — 20-dimension scored report (write first)
2. `deliverables/{slug}-correction-manifest.md` — atomic corrections with file+field references
3. `research/FACTCHECK_GATE.md` — machine-readable gate (PROCEED/WARN/BLOCKED) — write LAST
4. `deliverables/{slug}-skill-feedback.md` — MANDATORY: root cause patterns for SKILL.md improvement

**`skill-feedback.md` is not optional.** Every fact-check run must identify at least 3 systemic patterns (not one-off errors) that caused issues, and propose specific SKILL.md text changes to prevent recurrence. Even if ACTION is PROCEED, write the file with "no critical patterns found" plus any minor improvements observed.

Format for `skill-feedback.md`:
```markdown
# Skill Feedback — {Company} Factcheck
## Root Cause Patterns Found
### Pattern 1: {name}
- Cause: {what the skill did wrong}
- Affected files: {list}
- Fix: Add to {skill-name}/SKILL.md: "{specific text to add}"

## Patterns NOT Found (confirmed working correctly)
- {list what was verified correct}
```

## FACTCHECK_GATE.md format (write this last — orchestrator reads it)
```
SCORE: {x.x}
CONFIDENCE: HIGH|MODERATE|LOW
ACTION: PROCEED|WARN|BLOCKED
BLOCKING_COUNT: {n}
WARNING_COUNT: {n}
```
BLOCKED if any [INCORRECT] or [DISCREPANT] items. Score ≥9.0 = HIGH CONFIDENCE.

## Full Methodology
See `~/.claude/skills/algolia-audit-factcheck/REFERENCE.md` for:
- All 20 dimension specifications with verification procedures
- Claim registry format and population instructions
- Scoring formula (per-dimension + weighted overall)
- Agent team architecture (5-agent parallel for standard/full tiers)
- Output file templates (factcheck report, correction manifest, skill feedback)
- Impact stat verification procedure (BLOCKING — runs every tier)
- FACTCHECK_GATE.md examples (passing + blocked)

---

## Dim 21 — ABX Campaign Completeness
For each touch in `abx_sequence.touches`: verify body is real content (≥100 chars, no "Pending" placeholder). Verify contacts list has at least 2 people with `id` and `title`. Verify Loom script exists if a Loom touch is present.
PASS = all touches have real bodies + contacts mapped. FAIL = any placeholder body.

## Dim 22 — Citation Baseline (applies across all sections)
Spot-check 5 random items from each of: `executives`, `intelligence_signals`, `strategic_angles`, `icp_mapping.priority_to_product`, `findings`, `case_studies`.
For each: verify `source_url` (or equivalent) exists and is a real URL. WebFetch 3 of them to confirm HTTP 200 and content matches claim.
PASS = all checked items have URLs, checked URLs return content. FAIL = any missing URL on a factual claim.

## Dim 23 — Scoring Matrix Completeness
Read `research/10-scoring-matrix.md`. Verify it contains scores for all 10 areas (latency, typo_tolerance, query_suggestions_empty_state, intent_detection, merchandising_consistency, content_commerce_ux, semantic_nlp_search, dynamic_facets_personalization, recommendations_merchandising, search_intelligence). Verify `audit-data.json → score.overall` is non-zero and matches the matrix.
PASS = all 10 scores present + overall calculated correctly. FAIL = stub file or missing scores.

## Scoring Rules — Non-Negotiable

**Rule 1: Show the math or don't write the number.**
Every score must show: `(sum of passed claims / total claims checked) × 10 = X/10`
Never assign a score by estimate, intuition, or gut feel.

**Rule 2: Score ≠ Confidence. Never conflate them.**
- SCORE = what fraction of CHECKED dimensions passed
- CONFIDENCE = how much of the total verification scope was completed
- 10/10 score + MODERATE confidence = everything checked passed, but coverage was partial
- 7/10 score + HIGH confidence = 30% failed, but we checked everything

**Rule 3: Quick tier scores only the 3 dimensions that ran.**
Dimensions 4-20 are UNVERIFIED (unknown), not FAILED.
Do NOT deduct points for unverified dimensions — they have no score yet.

**Rule 4: Empty impact_stat fields are CORRECT behavior.**
The pre-write rule says: no source = don't write it. Empty impact_stat = rule followed.
This is a PASS, not a warning or deduction.
