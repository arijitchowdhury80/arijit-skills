---
name: algolia-audit-eval
version: 2.0.0
description: Use when asked to eval or score the output of an Algolia Search Audit skill or module. Triggers when someone wants to know if a module output is good enough, meets the pass threshold, or needs more work — specifically scoring across the 5 quality dimensions (completeness, source density, instruction adherence, data accuracy, no fabrication). Also invoke after shipping a fix or building a new audit sub-skill to confirm quality before declaring it production-ready. Covers any algolia-audit-* or algolia-intel-* module output: research, report, browser, factcheck, financial profiles, live signals (social/news), and others.
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Input
$ARGUMENTS — skill name to evaluate (e.g., algolia-audit-research) + company slug for test data
Example: `algolia-audit-research Costco`

## Output
$ALGOLIA_AUDIT_DIR/{CompanyName}/eval/{skill-name}-eval-report.md

## Path
$AUDIT_DIR = $ALGOLIA_AUDIT_DIR

## Scoring Rule (non-negotiable)
SCORE = (passing_checks / total_checks_run) × 10
NEVER estimate or guess a score. Show: N passing / M total = score.
CONFIDENCE reflects how many checks ran (coverage), not the score.

---

## Phase 0: Setup

```bash
# Resolve AUDIT_DIR
if [ -z "$ALGOLIA_AUDIT_DIR" ]; then
  AUDIT_DIR="$(pwd)"
  echo "WARNING: ALGOLIA_AUDIT_DIR not set — using current directory: $AUDIT_DIR"
else
  AUDIT_DIR="$ALGOLIA_AUDIT_DIR"
fi

# Parse arguments
SKILL_NAME="$1"          # e.g., algolia-audit-research
COMPANY_NAME="$2"        # e.g., Costco
COMPANY_DIR="$AUDIT_DIR/$COMPANY_NAME"
EVAL_DIR="$COMPANY_DIR/eval"
REPORT_FILE="$EVAL_DIR/${SKILL_NAME}-eval-report.md"

mkdir -p "$EVAL_DIR"
echo "Evaluating: $SKILL_NAME on $COMPANY_NAME"
echo "Output: $REPORT_FILE"
```

**Declare workspace type before writing:**
"This writes to PRODUCTION: {CompanyName}/eval/ — eval reports do not overwrite research or deliverable files."

---

## Mechanical dimensions — run the shared script FIRST

Dimensions 1 (completeness), 2 (source density), 4 (data accuracy spot-check) and 5 (no fabrication)
are mechanical and are implemented deterministically by the shared factcheck/eval engine. **Run it
first** and read its JSON instead of re-deriving these counts by hand:

```bash
python3 ~/.claude/skills/algolia-audit-factcheck/scripts/factcheck_mechanical.py \
  --audit-dir "$AUDIT_DIR" --company "$COMPANY_NAME"
# JSON.dimensions.{completeness,source_density,no_fabrication,data_accuracy} feed Dims 1/2/5/4.
```

Map the script's numbers into the per-dimension formulas below (e.g. Dim 1 score =
`completeness.passing / completeness.total × 2`; Dim 5 = `2.0` when `no_fabrication.blocking` is
false). Dimension 3 (instruction adherence) stays an LLM judgment — it is NOT in the script.

## The 5 Evaluation Dimensions

### Dimension 1: Completeness (2 points)
Does the output contain all required files/sections?
Check: All expected output files exist AND are above minimum byte thresholds.

```bash
# For algolia-audit-research:
PASS_COUNT=0
TOTAL=12
for f in 01 02 03 04 05 06 07 08 09 10 11 12; do
  FILE=$(ls "$AUDIT_DIR/$COMPANY_NAME/research/${f}-"*.md 2>/dev/null | head -1)
  SIZE=$(wc -c < "$FILE" 2>/dev/null || echo 0)
  if [ "$SIZE" -gt 2000 ]; then
    echo "PASS: $FILE (${SIZE}b)"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "FAIL: $FILE (${SIZE}b — below 2000b threshold)"
  fi
done
echo "Completeness: $PASS_COUNT of $TOTAL files pass threshold"
```

**Skill-specific file expectations:**

| Skill | Expected files | Threshold |
|-------|---------------|-----------|
| algolia-audit-research | 12 scratchpad files (01–12) in research/ | >2000 bytes each |
| algolia-audit-browser | ≥10 screenshots in deliverables/screenshots/ | >10000 bytes each |
| algolia-audit-report | audit-data.json + index.html in deliverables/ | >50000 bytes each |
| algolia-audit-factcheck | factcheck-report.md + correction-manifest.md + skill-feedback.md | >1000 bytes each |
| algolia-live-signals | 09b-*.md + 09c-*.md in research/ | >1000 bytes each |

**Score formula:** (files_passing_threshold / expected_file_count) × 2

---

### Dimension 2: Source Density (2 points)
Does every data point have a source URL?
Check: Count [FACT], [ESTIMATE], [OBSERVED] labels AND count source URLs. Bare numbers without labels are a failure signal.

```bash
LABELED=$(grep -rh "\[FACT\]\|\[ESTIMATE\]\|\[OBSERVED\]" "$AUDIT_DIR/$COMPANY_NAME/research/"*.md 2>/dev/null | wc -l)
URLS=$(grep -rch "https://" "$AUDIT_DIR/$COMPANY_NAME/research/"*.md 2>/dev/null | awk '{sum+=$1}END{print sum}')
echo "Labeled claims: $LABELED | Source URLs: $URLS"
# Pass threshold: ≥15 source URLs across all files
```

**Pass condition:** ≥15 source URLs across all output files.
**Score formula:** min(URLS/15, 1) × 2

---

### Dimension 3: Instruction Adherence (2 points)
Did the skill follow its own SKILL.md instructions?
Check specific rules for the skill being evaluated.

**Checklist per skill:**

**algolia-audit-research:**
- [ ] CHECKPOINT.md shows all 14 steps executed
- [ ] Wave 1–4 parallel execution pattern used (not sequential)
- [ ] MCP tools called before Gemini-grounded search (gemini_search.py) fallback
- [ ] Each scratchpad file ≥2000 bytes (not stubs)

**algolia-audit-report:**
- [ ] STEP 0 data refresh executed (CHECKPOINT.md confirms)
- [ ] Renderer called via Skill tool (not manual HTML written inline)
- [ ] audit-data.json validated against schema before HTML render
- [ ] All 6 deliverable files generated

**algolia-audit-factcheck:**
- [ ] All 7 dimensions explicitly listed in output
- [ ] Score shows explicit math (N passing / M total)
- [ ] External verification performed (API re-calls, not read-only)
- [ ] correction-manifest.md + skill-feedback.md both written

**algolia-audit-browser:**
- [ ] Screenshots saved to disk immediately (not deferred)
- [ ] Screenshot naming convention: {nn}-{query-slug}.png
- [ ] ≥10 screenshots on disk
- [ ] CAPTCHA/WAF recovery steps followed if triggered

**algolia-live-signals:**
- [ ] 09b-hiring-signals.md written
- [ ] 09c-trigger-events.md written
- [ ] All 3 output files present

```bash
RULES_FOLLOWED=0
RULES_CHECKED=4   # adjust per skill
# Score each rule above as pass (1) or fail (0)
echo "Adherence: $RULES_FOLLOWED of $RULES_CHECKED rules followed"
```

**Score formula:** (rules_followed / rules_checked) × 2

---

### Dimension 4: Data Accuracy (2 points)
Spot-check 3 specific data points against their source scratchpad files.

1. **Revenue figure**: Find a revenue figure in a deliverable → verify it matches `08-financial-profile.md` exactly (same number, same year)
2. **Traffic stat**: Find a traffic/visits figure in a deliverable → verify it matches `03-traffic-data.md` exactly (same number, same period)
3. **Executive quote**: Find an exec quote in a deliverable → verify it matches `11-investor-intelligence.md` exactly (same speaker, same title, same wording)

```bash
SPOT_CHECKS_PASSED=0
SPOT_CHECKS_TOTAL=3

# Check 1: Revenue
REVENUE_IN_REPORT=$(grep -o '\$[0-9,.]*[BMK]*' "$AUDIT_DIR/$COMPANY_NAME/deliverables/"*report*.md 2>/dev/null | head -1)
REVENUE_IN_SCRATCHPAD=$(grep "$REVENUE_IN_REPORT" "$AUDIT_DIR/$COMPANY_NAME/research/08-financial-profile.md" 2>/dev/null | wc -l)
[ "$REVENUE_IN_SCRATCHPAD" -gt 0 ] && SPOT_CHECKS_PASSED=$((SPOT_CHECKS_PASSED + 1)) && echo "PASS: Revenue match" || echo "FAIL: Revenue mismatch or not found"

# Checks 2 and 3: similar pattern for traffic and quote
echo "Accuracy: $SPOT_CHECKS_PASSED of $SPOT_CHECKS_TOTAL spot-checks passed"
```

**Score formula:** (spot_checks_passed / 3) × 2

---

### Dimension 5: No Fabrication (2 points)
Are there any data points without verifiable sources?

Check each of the following:
- Numbers in deliverables without a corresponding [FACT] or [ESTIMATE] label in source scratchpad files
- `impact_stat` fields with content but no `impact_stat_source` URL
- Case study metrics not traceable to a verified URL in the bibliography
- Executive quotes with no source document (10-K, earnings call transcript, etc.)

```bash
FABRICATION_COUNT=0
TOTAL_CHECKED=0

# Check impact_stat fields without source
UNSOURCED_STATS=$(grep -c '"impact_stat":' "$AUDIT_DIR/$COMPANY_NAME/deliverables/"*audit-data.json 2>/dev/null)
SOURCED_STATS=$(grep -c '"impact_stat_source": "http' "$AUDIT_DIR/$COMPANY_NAME/deliverables/"*audit-data.json 2>/dev/null)
MISSING=$((UNSOURCED_STATS - SOURCED_STATS))
FABRICATION_COUNT=$((FABRICATION_COUNT + MISSING))
TOTAL_CHECKED=$((TOTAL_CHECKED + UNSOURCED_STATS))

# Check for bare numbers in research files without labels
BARE_NUMBERS=$(grep -rh "^[0-9]\|[^[][$][0-9]\|[0-9]%[^A-Za-z]" "$AUDIT_DIR/$COMPANY_NAME/research/"*.md 2>/dev/null | grep -v "\[FACT\]\|\[ESTIMATE\]\|\[OBSERVED\]" | wc -l)
echo "Unsourced impact_stats: $MISSING | Potentially bare numbers: $BARE_NUMBERS"
echo "Fabrication check: $FABRICATION_COUNT issues found out of $TOTAL_CHECKED checked"
```

**Score formula:** (1 - fabrication_count/total_checked) × 2. Zero fabrications = 2.0.
If total_checked = 0, score = 2.0 (no claims to verify — not a failure).

---

## Score Aggregation

After running all 5 dimensions, sum the scores:

```
Dim 1 Completeness:    {n1}/2.0
Dim 2 Source Density:  {n2}/2.0
Dim 3 Adherence:       {n3}/2.0
Dim 4 Data Accuracy:   {n4}/2.0
Dim 5 No Fabrication:  {n5}/2.0
─────────────────────────────────
TOTAL:  {sum}/10.0

Calculation: ({n1} + {n2} + {n3} + {n4} + {n5}) / 10 = {score}
```

**Pass:** ≥7.0
**Fail:** <7.0 → list specific failures with recommended fixes

---

## Output Format

Write the following to `$EVAL_DIR/{skill-name}-eval-report.md`:

```markdown
# Eval Report — {Skill Name} on {Company}
*Generated: {date} | Evaluating: {skill name} | Auditor: algolia-audit-eval*

## Score: {X.X}/10 — {PASS/FAIL}
Calculation: ({d1} + {d2} + {d3} + {d4} + {d5}) / 10 = {score}

## Dimension Results
| # | Dimension | Detail | Score |
|---|-----------|--------|-------|
| 1 | Completeness | {N} of {M} files pass threshold | {n}/2.0 |
| 2 | Source Density | {N} URLs, {M} labeled claims | {n}/2.0 |
| 3 | Adherence | {N} of {M} rules followed | {n}/2.0 |
| 4 | Data Accuracy | {N} of 3 spot-checks pass — {what was checked} | {n}/2.0 |
| 5 | No Fabrication | {N} unsourced claims found | {n}/2.0 |

## Failures (must fix before marking skill complete)
{List any dimension that scored <1.5 with specific issue and recommended fix}
{If none: "No failures."}

## Warnings (should fix)
{List any dimension that scored 1.5–1.9 with specific issue}
{If none: "No warnings."}

## Recommended Action
{PASS → skill is production-ready} or {FAIL → list specific fixes required with file references}
```

---

## When to Run
- After every Wave of Phase C fixes (validate fixes work)
- After building each new Phase E module
- Before declaring any skill "production-ready"
- Before any Phase D integration test

---

## Verification Gate
After writing the eval report, verify:

```bash
REPORT_SIZE=$(wc -c < "$REPORT_FILE" 2>/dev/null || echo 0)
[ "$REPORT_SIZE" -gt 4000 ] && echo "PASS: Report is ${REPORT_SIZE}b (≥4000b)" || echo "FAIL: Report is ${REPORT_SIZE}b (below 4000b threshold)"
```

Pass condition: ≥4000 bytes. All 5 dimensions have explicit scoring formulas. Score aggregation formula shown.
