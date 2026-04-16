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

## Phase 5a-ANGLES: Extract strategic_angles (MANDATORY — run BEFORE generate-audit-data.py patch)

`strategic_angles` has been empty or wrong on every audit because these instructions were missing. Fix this now.

**EXTRACT — do not synthesize.** Open `research/06-strategic-context.md`. All angles must come from that file. Do not invent angles not in it.

1. Read section **"1. Algolia-Specific Strategic Angles"** in `06-strategic-context.md`
2. Read section **"7. Objection Pre-Emption"** in the same file — this is where `objection` + `objection_counter` come from
3. For each angle heading (e.g. "Angle 1 — The NikeAI Gap"), write one JSON object:

```json
{
  "label":             "The angle heading — verbatim or lightly trimmed",
  "hook":              "Copy the 'Pitch angle:' sentence verbatim — do not paraphrase",
  "pain_points":       ["each bullet evidence item under the angle body"],
  "discovery_question":"One question derived from this angle's evidence — stated or brief synthesis",
  "algolia_proof":     "The Algolia case study metric cited in the body (e.g. '+35% conversion — Under Armour')",
  "objection":         "From section 7 Objection Pre-Emption table — the row matching this angle's theme",
  "objection_counter": "The evidence response from that same row",
  "source":            "The [FACT — ...] citation from the markdown body (REQUIRED)"
}
```

4. Write all extracted angles into `strategic_angles[]` in `{slug}-audit-data.json`
5. All 8 fields are required. Missing any field will fail schema validation and block the render.

---

## Phase 5a-CASE-STUDIES: Write case_studies (MANDATORY — run BEFORE generate-audit-data.py patch)

`case_studies` has been empty on every audit because these instructions were missing. Fix this now.

Write 3 Algolia customer success stories comparable to the prospect's vertical into `audit-data.json`.

**Source**: WebFetch `https://www.algolia.com/customers/` — scan for companies in the same or adjacent vertical as `company_snapshot.industry`.

**Required format for each:**
```json
{
  "vertical": "string — exact industry label e.g. 'Footwear Retail'",
  "company":  "string — Algolia customer company name",
  "result":   "string — the single headline metric e.g. '+37% conversion rate'",
  "product":  "string — which Algolia capability drove this e.g. 'NeuralSearch + Personalization'",
  "why":      "string — 1–2 sentences explaining why this case study is directly comparable to [prospect]",
  "url":      "string — https://www.algolia.com/customers/[company-slug]/"
}
```

**Matching rules (in priority order):**
1. Same vertical first (e.g., footwear retailer → footwear case studies)
2. Same retail model second (e.g., off-price → value retail)
3. Similar scale/traffic (e.g., 5M–50M monthly visits)
4. Same ecommerce platform if available
5. If no exact match exists, use closest adjacent vertical with explicit note in `why`

**Never leave `case_studies` as an empty array.** Minimum 2 entries required. If WebFetch is blocked on algolia.com/customers, use WebSearch for "[company name] algolia case study site:algolia.com".

After writing, validate: `python3 validate-json-schema.py {slug}`

---

## Phase 5a-NEW: Write new IA fields (run AFTER generate-audit-data.py patch)

After the JSON patcher runs, add these 3 new top-level fields to `{slug}-audit-data.json`.
Read the file, add the fields, write it back. Do not overwrite existing fields.

### Field 1: `tab_subtitles`
Personalized subtitle for each of the 5 SPA tabs. Write this:
```json
"tab_subtitles": {
  "summary":  "What you need before walking into [Company name]",
  "account":  "[Company name] at a glance — [industry], [monthly visits] monthly visitors",
  "findings": "What we found when we tested [Company name]'s search",
  "case":     "Why [Company name] should act now — [ROI headline if available, else 'The business argument']",
  "playbook": "How to win the [Company name] deal"
}
```
Replace [Company name] with `D.meta.company`. Replace other placeholders with actual data from the audit.
The subtitles must be specific to THIS company — not templates.

### Field 2: `recommended_first_play`
The single strongest recommended first action. Priority logic:
1. If `research/partner-intel.md` exists and has HIGH-confidence SI partner → type = "partner_warm_intro"
2. Else if golden_angle has competitors_using_algolia → type = "competitive"
3. Else if intelligence_signals has exec/funding signal → type = "timing"
4. Else use first strategic_angle → type = "strategic_angle"

Write this:
```json
"recommended_first_play": {
  "type": "partner_warm_intro | strategic_angle | competitive | timing",
  "headline": "[Short headline, max 6 words]",
  "detail": "[1-2 sentence detail explaining the play]",
  "urgency": "high | medium | low",
  "source": "partner_intel | competitors | intelligence_signals | strategic_angles"
}
```

### Field 3: `partner_intel`
Read `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/partner-intel.json` if it exists.
If the file exists: copy its top-level content into `audit-data.json.partner_intel`.
If the file does NOT exist: write `"partner_intel": null`.

```json
"partner_intel": {
  "tech_partners": [...from partner-intel.json...],
  "si_partners": [...from partner-intel.json...],
  "immediate_action": "...",
  "co_sell_recommendation": "...",
  "crossbeam_data_available": true|false,
  "source_label": "..."
}
```
OR if file missing:
```json
"partner_intel": null
```

After writing all 3 fields, run the validator again:
```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/validate-json-schema.py {slug} "$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/"
```
Expected: PASS with up to 3 WARNs about the new fields (if they were missing, they're now present).

---

## ⚠️ Phase 5a-PATCH — Run generate-audit-data.py AFTER writing audit-data.json (MANDATORY)

After the LLM writes `{slug}-audit-data.json` in Phase 5a, immediately run:

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/generate-audit-data.py \
  {slug} "$ALGOLIA_AUDIT_DIR/{CompanyName}"
```

**What it does:** Reads the scratchpad .md files and patches all deterministic fields with correctly-typed values extracted via regex — no LLM guessing involved:
- `tech_stack.full_list` → string[] (never objects)
- `traffic.top_channels` → [{source, share}] array (never dict)
- `traffic.demographics` → [{age_group, pct, color}] array (never flat object)
- `score.breakdown` → canonical 10 keys (latency, typo_tolerance, etc.)
- `score.overall` → recalculated from weighted formula
- `competitors[]` → correct schema per row

The script also runs `validate-json-schema.py` automatically. If validation fails → **STOP and fix before rendering.** Do not proceed to Phase 5b with a broken JSON.

**Why this exists:** The LLM reliably writes synthesis content (signals, matrix narrative, exec quotes) but repeatedly writes wrong data types for structural fields (objects instead of strings, wrong key names). This script is the type-safety layer. It cannot produce the wrong format because it reads structured markdown, not generates from memory.

---

## Renderer validation chain (all mandatory before rendering)
1. **generate-audit-data.py** (Phase 5a-patch above) → patches types + runs schema validation
2. check-style-tokens.py → blocks if raw inline styles in template
3. render-audit.ts → runs schema gate again internally
4. test-spa-runtime.js → verifies SPA renders without blank sections

## Full Methodology
See `~/.claude/skills/algolia-audit-report/REFERENCE.md` for:
- 10-area scoring rubric with HIGH/MEDIUM/LOW criteria
- audit-data.json field-by-field mapping
- Report structure (all required sections)
- Gate 3, Gate 4, Gate 4.5, Gate 5, Gate 6 checklists
- AE Playbook structure (BLUF + MEDDPICC + discovery questions + objections + ROI)
- Visual standards (speedometer score, revenue funnel SVG, annotation circles)
