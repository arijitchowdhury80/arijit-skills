---
name: algolia-audit-report
description: Use when a company's Algolia Search Audit workspace is already fully populated (research files and browser screenshots in place) and the goal is to generate the final deliverable package: score the 10 search areas, produce the McKinsey deck, dual-view landing page, PDF book, AE pre-call playbook, and strategic signal brief. Triggers when the user says research and browser testing are done and wants to render, score, or output the full audit report and deliverables. Not for starting new audits, running browser tests, doing pre-audit research, or editing individual files.
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## ⚠️ STEP 0 — MANDATORY DATA REFRESH (do this BEFORE anything else)
Re-read these 5 files NOW before executing any phase:
1. `03-traffic-data.md` | 2. `04-competitors.md` | 3. `08-financial-profile.md` | 4. `10-scoring-matrix.md` | 5. `11-investor-intelligence.md`
Copy-paste mandate: Never reconstruct financial figures, quotes, or competitor data from memory. Always copy exact values from scratchpad files.

## ⚠️ MANDATORY PRE-WRITE RULE
If you cannot cite a source URL for a data point RIGHT NOW — do not write it. Not flagged. Not hedged. Simply: do not write it.

---

## Input
$ARGUMENTS — company slug (e.g., costco). Workspace at `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`
Optional: --deliverable {name} | --skip-pdf

## Required Workspace Files
All 12 scratchpad files (01-12) + screenshots/ (≥10 PNG) must exist before starting.
Run validate-workspace.sh first: `bash ~/.claude/skills/algolia-search-audit/scripts/validate-workspace.sh "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/"`

## Output (8 deliverables → $ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/)
| File | Audience | How generated |
|------|----------|--------------|
| {slug}-audit-data.json | Internal | Claude writes from scratchpad |
| {slug}/index.html | AE/SE/BD | render-audit.ts site |
| {slug}/ae-report.html | AE | render-audit.ts ae-report |
| {slug}/battle-card.html | AE/SE | render-audit.ts battle-card |
| {slug}/leave-behind.html | Prospect | render-audit.ts leave-behind |
| {slug}-leave-behind.pdf | Prospect | generate-pdf.sh leave-behind |
| {slug}-playbook.md | AE/BDR/Partner | Claude writes (merged AE brief + sales plays) |
| {slug}-strategic-signal-brief.md | LLM/CRM | Claude writes |

## Execution Phases
Phase 3: Score 10 areas → 10-scoring-matrix.md (see REFERENCE.md for scoring criteria)
Phase 4: Generate main report → {slug}-search-audit.md
Phase 5a: Write audit-data.json (validate with validate-json-schema.py before render)
Phase 5b: Run renderer → deno run --allow-read --allow-write --allow-net scripts/render-audit.ts {slug} all
Phase 5c: Generate PDF (skip if --skip-pdf) → bash scripts/generate-pdf.sh {slug} leave-behind
Phase 5d+e: Write playbook.md + signal-brief.md

## ⚠️ CAPABILITY MATRIX — MANDATORY RULES (Phase 5a, before writing audit-data.json)

The SPA capability matrix uses 4 FIXED row keys: `nike_has`, `asics_has`, `on_running_has`, `new_balance_has`.
These key names are hardcoded in the renderer — do NOT invent custom keys (e.g., `shoe_carnival`, `zappos_has`).

**Every company that is NOT Brooks Running MUST set `competitive_synthesis.matrix_col_labels`** to map those 4 keys to the actual competitor names for this company. Example for DSW:
```json
"matrix_col_labels": {
  "nike_has": "Zappos",
  "asics_has": "Macy's",
  "on_running_has": "Famous Footwear",
  "new_balance_has": "Steve Madden"
}
```

And the `positioning_matrix` rows MUST use these exact field names (SPA and validator both enforce them):
```json
{
  "capability": "NLP / Semantic Search",
  "prospect_today": "0/10 — keyword-only",
  "prospect_with_algolia": "NeuralSearch (semantic + typo-tolerant)",
  "nike_has": "Amazon AI search (unavailable to competitors)",
  "asics_has": "Macy's: Monetate + custom search",
  "on_running_has": "Famous Footwear: basic keyword",
  "new_balance_has": "Steve Madden: keyword only",
  "algolia_delta": "Critical gap"
}
```
Never use `dimension` (wrong — SPA reads `capability`), never use `dsw` (wrong — SPA reads `prospect_today`), never use custom keys like `shoe_carnival` (wrong — SPA only reads `nike_has`/`asics_has`/`on_running_has`/`new_balance_has`).

If `matrix_col_labels` is null or missing → the SPA renders **Nike / Asics / On Running / New Balance** regardless of the actual company. This is always wrong for non-running-shoe companies. Validate with:
```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/validate-json-schema.py {slug} "$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/"
```
The schema validator will flag a missing `matrix_col_labels` as a blocking error.

---

## Renderer validation chain (all mandatory before rendering)
1. validate-json-schema.py {slug} → blocks if wrong field names or wrong score math
2. check-style-tokens.py → blocks if raw inline styles in template
3. render-audit.ts → runs both gates again internally
4. test-spa-runtime.js → verifies SPA renders without blank sections

## Full Methodology
See `~/.claude/skills/algolia-audit-report/REFERENCE.md` for:
- 10-area scoring rubric with HIGH/MEDIUM/LOW criteria
- audit-data.json field-by-field mapping
- Report structure (all required sections)
- Gate 3, Gate 4, Gate 4.5, Gate 5, Gate 6 checklists
- AE Playbook structure (BLUF + MEDDPICC + discovery questions + objections + ROI)
- Visual standards (speedometer score, revenue funnel SVG, annotation circles)
