---
name: algolia-synth-business-case
description: Use when asked to generate, build, or run an Algolia search ROI business case for a specific prospect company. Invoke for requests like 'build the ROI model', 'generate the business case', 'run synth-business-case', or 'give me the component-level breakdown' for an Algolia pitch or AE sales call. Breaks search revenue opportunity into 6 components — conversion lift, AOV increase, bounce reduction, no-results recovery, speed gain, long-tail discovery — with formulas pre-filled from audit research data. Outputs {slug}-business-case.md with conservative + moderate scenarios and fill-in-the-blank prompts for AE/BDR to replace estimates with prospect's actual numbers. Distinct from: audit reports (scoring + findings), AE playbooks (talking points + objection handling), and one-pagers (executive summaries).
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md` before taking any other step.

---

## PLATFORM RULES (from AGENT-CONTEXT.md)

- Skill naming: `algolia-{layer}-{function}` — this skill is `algolia-synth-business-case`
- NEVER hardcode the Google Drive path. Use `$ALGOLIA_AUDIT_DIR`.
- NEVER write a number without the formula that produces it.
- State PRODUCTION or TEST before every write operation.
- Source citations required on every data point.

---

## MANDATORY RULE: The SCRIPT does the math, not you

**You do NOT compute any ROI dollar figure by hand.** All 6 components × 2 scenarios
are computed deterministically by `calculate-roi.py --components`. Your job is to:
1. EXTRACT the labeled assumptions from the research files (and mark AE fill-ins),
2. PASS them to the script,
3. WRITE the narrative around the numbers the script returns — verbatim.

Every dollar figure must show its formula — but you copy the `formula_conservative` /
`formula_moderate` strings the script emits; you never multiply anything yourself.
If any input is an estimate, label it `[ESTIMATE]`. If verified from a named source,
label it `[FACT — {source}]`. A number you computed by hand is a violation. A number
the script did not emit is a violation. Do not write it.

---

## Invocation

```
/algolia-synth-business-case <company-slug>
```

Example: `/algolia-synth-business-case costco`

---

## Path Resolution

```bash
# At execution start — resolve AUDIT_DIR
if [ -z "$ALGOLIA_AUDIT_DIR" ]; then
  AUDIT_DIR="$(pwd)"
  echo "WARNING: ALGOLIA_AUDIT_DIR not set — using current directory: $AUDIT_DIR"
else
  AUDIT_DIR="$ALGOLIA_AUDIT_DIR"
fi
```

- Company slug from `$ARGUMENTS` → resolve to folder name in `$AUDIT_DIR`
- Match slug case-insensitively. If ambiguous, list candidates and stop.

---

## Input Files (read in this order)

| File | Fields used | Required? |
|------|-------------|-----------|
| `$AUDIT_DIR/{Company}/research/08-financial-profile.md` | Annual revenue, digital revenue share, estimated digital revenue, existing ROI figures | Required |
| `$AUDIT_DIR/{Company}/research/10-scoring-matrix.md` | Which of the 10 search gap areas are present (determines which components apply) | Required |
| `$AUDIT_DIR/{Company}/research/03-traffic-data.md` | Monthly visits, bounce rate, pages per visit (SimilarWeb) | Required |
| `$AUDIT_DIR/{Company}/research/04-competitors.md` | Competitor Algolia adoption + Golden Angle evidence | Optional |
| `$AUDIT_DIR/{Company}/deliverables/{slug}-audit-data.json` | `financials`, `traffic`, `findings` fields | Optional (use if exists) |

If `08-financial-profile.md` is missing: STOP. Output an error message. Do not proceed.
If `03-traffic-data.md` is missing: mark traffic inputs as `[ESTIMATE — unavailable]`.

---

## Output File

**Declares PRODUCTION write:**
> "This writes to PRODUCTION: {Company} — generating business case deliverable from completed audit data."

Output path: `$AUDIT_DIR/{Company}/deliverables/{slug}-business-case.md`

---

## Step 1: Extract Pre-populated Inputs

From the input files, extract and record:

| Input | Source file | JSON field (if audit-data.json) | Label |
|-------|-------------|----------------------------------|-------|
| Annual revenue | 08-financial-profile.md | `financials.annual_revenue` | [FACT — source name] or [ESTIMATE] |
| Digital revenue share | 08-financial-profile.md | `financials.digital_share` | [FACT] or [ESTIMATE] |
| Estimated digital revenue | Calculated: `annual_revenue × digital_share` | — | Show formula |
| Monthly visits | 03-traffic-data.md | `traffic.monthly_visits` | [FACT — SimilarWeb MCP] |
| Bounce rate | 03-traffic-data.md | `traffic.bounce_rate` | [FACT — SimilarWeb MCP] |
| Search usage rate | Industry standard 15% unless better data available | — | [ESTIMATE — industry standard] |
| AOV (average order value) | 08-financial-profile.md if present | — | [FACT] or [ESTIMATE] or [AE fill-in required] |
| Conversion rate | 08-financial-profile.md if present | — | [FACT] or [ESTIMATE] or [AE fill-in required] |

Note: If AOV or conversion rate are not in the research files, mark them as AE fill-in — do NOT invent numbers.

---

## Step 2: Determine Applicable Components

Read `10-scoring-matrix.md`. Map scoring gaps to components:

| Scoring gap area | Applicable component |
|-----------------|---------------------|
| `intent_detection` | Component 1 (Conversion Lift) |
| `merchandising_consistency` | Component 2 (AOV Increase) |
| `query_suggestions_empty_state` | Component 3 (Bounce Rate Reduction) |
| `semantic_nlp_search` | Component 4 (No-Results Recovery) + Component 6 (Long-Tail Discovery) |
| `latency` | Component 5 (Speed / Latency Gain) |
| `dynamic_facets_personalization` | Component 2 (AOV Increase) |
| `recommendations_merchandising` | Component 2 (AOV Increase) |
| `typo_tolerance` | Component 4 (No-Results Recovery) |

Mark components as ACTIVE (gap confirmed) or CONDITIONAL (gap not confirmed — include as potential upside).

---

## Step 3: Calculate the 6 ROI Components — RUN THE SCRIPT

**Do not multiply anything by hand.** Assemble the labeled assumptions you extracted
in Step 1–2 into a JSON object and pass it to `calculate-roi.py --components`. The
script computes all 6 components × conservative + moderate, returns the per-component
formula strings and the totals, and SKIPS any component whose required input is absent
(it never fabricates a missing AOV or conversion rate).

```bash
# Assemble assumptions — ONLY values you can cite or that are AE fill-ins you have.
# Omit anything you do not have; the script will SKIP the dependent component
# rather than invent a number. current_conversion drives Component 2 only.
python3 ~/.claude/skills/algolia-search-audit/scripts/calculate-roi.py --components \
  --assumptions '{
    "monthly_visits": <from 03-traffic-data.md, FACT>,
    "aov": <from 08-financial-profile.md or AE fill-in>,
    "search_usage_rate": 0.15,
    "current_conversion": <AE fill-in — omit if unknown>,
    "no_results_rate": 0.05,
    "nlp_fail_rate": 0.20
  }'
```

Per-component improvement rates (conversion delta, AOV delta, bounce delta, delay
buckets, recovery rates, the moderate-scenario bumps) are the SKILL.md baselines and
are built into the script. To override a baseline for a specific prospect, add the
matching key from `COMPONENT_DEFAULTS` (e.g. `"c1_conv_delta_conservative": 0.18`) to
the assumptions JSON — but only with a cited reason.

Then, for each component, write into the output file:
1. Status: copy the `status` the script returned (ACTIVE / CONDITIONAL / SKIPPED).
   You may upgrade CONDITIONAL→ACTIVE by passing `"c2_status": "ACTIVE"` etc. when the
   scoring matrix confirms the gap — that ACTIVE/CONDITIONAL judgment is yours, the
   arithmetic is the script's.
2. What it measures (the reference description below).
3. The `formula_conservative` and `formula_moderate` strings — verbatim from the script.
4. The `conservative` / `moderate` dollar figures — verbatim from the script.
5. Algolia improvement range with source (the reference notes below).
6. AE fill-in prompt (what to ask the prospect).

The component descriptions below are REFERENCE for steps 2/5/6 only — they are NOT a
licence to recompute the dollar figures. Numbers come from the script, full stop.

---

### Component 1: Search Conversion Lift

**What it measures:** Sessions that start with search convert at a higher rate when search returns relevant results.

**Formula:**
```
Monthly search sessions × conversion_delta × AOV × 12 = annual_impact
Monthly search sessions = monthly_visits × search_usage_rate
```

**Algolia improvement range:**
- Conservative: +15% conversion rate lift
- Moderate: +20% conversion rate lift
- Source: Verify before citing — WebFetch an Algolia case study URL from `04-competitors.md` or `algolia.com/customers`
- Label result: [FACT — {case study company}] if verified, [ESTIMATE — Algolia claimed range] if unverified

**AE fill-in:** "What is your current search-to-purchase conversion rate?"

**Pre-filled calculation (conservative):**
```
{X}M visits × {search_usage_rate}% search usage = {Y}K monthly search sessions
{Y}K sessions × +15% conversion delta × $[AOV — fill in] × 12 = $[result]M/year
```

---

### Component 2: Average Order Value Increase

**What it measures:** Basket size increases when search surfaces higher-value, personalized, or complementary items.

**Formula:**
```
Search-initiated orders/month × AOV_delta × 12 = annual_impact
Search-initiated orders/month = monthly_search_sessions × current_search_conversion_rate
```

**Algolia improvement range:**
- Conservative: +5% AOV when personalization/merchandising active
- Moderate: +10% AOV with full recommendations
- Source: Verify before citing — seek Algolia personalization case study
- Label: [FACT] or [ESTIMATE — industry average]

**AE fill-in:** "What is your average order value for search-initiated sessions vs. browse sessions?"

**Active if:** `dynamic_facets_personalization` or `recommendations_merchandising` gaps confirmed in scoring matrix.

---

### Component 3: Bounce Rate Reduction

**What it measures:** Visitors who land on search results and immediately leave — recovered when search returns relevant results.

**Formula:**
```
Monthly visits × search_usage_rate × bounce_delta × recovery_conversion × AOV × 12 = annual_impact
bounce_delta = [current_bounce_rate - target_bounce_rate]
recovery_conversion = 0.10 [ESTIMATE — 10% of recovered bounces convert]
```

**Algolia improvement range:**
- Conservative: Reduce search bounce rate by 10 percentage points
- Moderate: Reduce by 15 percentage points
- Source: Verify before citing
- Label: [ESTIMATE — no universal benchmark]

**Data available:** Bounce rate from `03-traffic-data.md` → use as input labeled [FACT — SimilarWeb MCP]

**AE fill-in:** "What % of your site sessions result in a bounce after viewing search results?"

**Pre-filled calculation (conservative):**
```
{X}M monthly visits × {search_usage_rate}% search usage × 10pp bounce delta × 10% recovery conversion × $[AOV] × 12 = $[result]M/year
```

---

### Component 4: No-Results Recovery

**What it measures:** Revenue currently lost from search queries that return zero results — the prospect walks away.

**Formula:**
```
Monthly searches × no_results_rate × AOV × recovery_rate × 12 = annual_impact
recovery_rate = 0.15 [ESTIMATE — 15% of recovered no-results convert, conservative]
```

**Algolia improvement range:**
- Baymard Institute: 34% of e-commerce sites fail basic search adequacy (cite: https://baymard.com/lists/cart-abandonment-rate)
- Conservative no-results rate to use if unknown: 5% [ESTIMATE — industry average]
- With Algolia typo tolerance + synonym matching: reduce no-results rate by 60-80%
- Source: Verify Baymard citation before using. Label [FACT — Baymard] if URL confirmed, [ESTIMATE] if not.

**AE fill-in:** "What % of searches on your site return zero results today? (Check site search analytics.)"

**Active if:** `typo_tolerance` or `semantic_nlp_search` gaps confirmed.

---

### Component 5: Speed / Latency Gain

**What it measures:** Revenue recovered from sessions lost because slow search drives abandonment.

**Formula:**
```
Monthly visits × search_usage_rate × latency_impact_rate × AOV × 12 = annual_impact
latency_impact_rate = sessions_lost_per_100ms_delay × number_of_delay_buckets
```

**Research benchmark:**
- Amazon internal study: 100ms of added latency = 1% revenue loss
- Citation: Widely cited; original source is Amazon internal (2006). Use with label [ESTIMATE — Amazon 2006, widely cited] unless a primary URL can be verified.
- Algolia p99 latency: <100ms globally (verify at https://status.algolia.com or algolia.com/products/search/)

**AE fill-in:** "What is your current average search response time? (P50 and P99 if available.)"

**Active if:** `latency` gap confirmed in scoring matrix.

**Pre-filled calculation (conservative, 200ms baseline → 100ms target):**
```
{X}M visits × {search_usage_rate}% search usage × 1% revenue impact per 100ms × 1 delay bucket × 12 = $[result]M/year
```

---

### Component 6: Long-Tail Discovery

**What it measures:** Revenue from queries that currently fail because they use natural language, synonyms, or multi-word phrases the current search engine cannot handle.

**Formula:**
```
Monthly searches × nlp_fail_rate × AOV × recovery_rate × 12 = annual_impact
nlp_fail_rate = [% of searches that are conversational/multi-word/synonym-dependent — AE fill-in]
recovery_rate = 0.12 [ESTIMATE — 12% of recovered NLP fails convert]
```

**Algolia improvement:** NLP + semantic search + synonym expansion addresses multi-word, intent-based, and synonym queries.
- Estimate: 20-30% of searches at most e-commerce sites are long-tail or NLP-dependent [ESTIMATE — industry range]
- Source: Seek Algolia NLP case study; label [FACT] only if URL verified.

**AE fill-in:** "What % of searches are conversational or multi-word? What % use category/attribute combos?"

**Active if:** `semantic_nlp_search` gap confirmed.

---

## Step 4: Totals — COPY from the script

Do NOT add the components yourself. The script already returns `totals.conservative`,
`totals.moderate`, and the `*_formula` strings that sum the active components. Copy
them verbatim. SKIPPED components are excluded from the totals by the script — if a
component is SKIPPED, say so explicitly in the output ("not modeled — missing {input}"),
do not silently drop it or backfill a guess.

### Conservative Total
Copy `totals.conservative` and `totals.conservative_formula` from the script output.

### Moderate Total
Copy `totals.moderate` and `totals.moderate_formula` from the script output.

### ASSUMPTION INVENTORY
List every input labeled [ESTIMATE] that AE should replace with actual numbers:
- [ ] Conversion rate (Component 1, 2)
- [ ] Average order value (all components)
- [ ] Search usage rate (all components) — default 15% [ESTIMATE]
- [ ] No-results rate (Component 4) — default 5% [ESTIMATE]
- [ ] NLP fail rate (Component 6) — default 20% [ESTIMATE]
- [ ] Bounce recovery conversion (Component 3) — default 10% [ESTIMATE]
- [ ] NLP recovery rate (Component 6) — default 12% [ESTIMATE]

---

## Step 5: Competitor Evidence Block (if applicable)

Read `04-competitors.md`. If a direct competitor uses Algolia and has a documented result:

```
Competitor Evidence:
{CompetitorName} switched to Algolia and achieved {result}.
Source: {URL — WebFetch confirmed before citing}
Label: [FACT — verified case study] or [UNVERIFIED — do not cite until confirmed]

AE Talking Point: "Your competitor {CompetitorName} solved this exact problem with Algolia.
The result was {metric}. That's the business case."
```

If no competitor evidence: omit this section entirely. Do not fabricate.

---

## Step 6: Write Output File

Declare workspace: "This writes to PRODUCTION: {Company} — business case deliverable."

Write to `$AUDIT_DIR/{Company}/deliverables/{slug}-business-case.md`.

---

## Output Template

```markdown
# Business Case — {Company}
*Generated: {date} | Skill: algolia-synth-business-case | Sources: 08-financial-profile.md + 03-traffic-data.md + 10-scoring-matrix.md*

---

## Pre-populated Inputs (from audit data)

| Input | Value | Source | Label |
|-------|-------|--------|-------|
| Annual revenue | ${X}B | 08-financial-profile.md | [FACT — {source}] or [ESTIMATE] |
| Digital revenue share | {X}% | 08-financial-profile.md | [FACT] or [ESTIMATE] |
| Estimated digital revenue | ${X}B × {X}% = ${Y}B | Calculated | Show formula |
| Monthly visits | {X}M | 03-traffic-data.md | [FACT — SimilarWeb MCP] |
| Bounce rate | {X}% | 03-traffic-data.md | [FACT — SimilarWeb MCP] |
| Search usage rate | 15% | Industry standard | [ESTIMATE — no site-specific data] |

---

## AE Fill-In Required (get these from the prospect)

| Input | Prompt for prospect | Your number |
|-------|---------------------|-------------|
| Search-to-purchase conversion rate | "What % of search sessions lead to a purchase?" | ______% |
| Average order value | "What is your AOV for search-initiated sessions?" | $______ |
| No-results rate | "What % of searches return zero results?" | ______% |
| Search response time (P99) | "What is your current search latency at P99?" | ______ms |
| Conversational search rate | "What % of searches are multi-word or natural language?" | ______% |

---

## Component 1: Search Conversion Lift
**Status:** ACTIVE / CONDITIONAL
**Gap confirmed:** intent_detection scored {X}/10 in scoring matrix

Formula: `monthly_visits × search_usage_rate × conversion_delta × AOV × 12`
Pre-filled: `{X}M × 15% × conversion_delta × $[AOV] × 12`
Conservative (+15% lift): `{X}M × 0.15 × 0.15 × $[AOV] × 12 = $[result]M/year` [inputs: ESTIMATE + AE fill-in]
Moderate (+20% lift): `{X}M × 0.15 × 0.20 × $[AOV] × 12 = $[result]M/year`
Source: [{case study company if verified} — {URL}] [{FACT/ESTIMATE label}]

---

## Component 2: Average Order Value Increase
**Status:** ACTIVE / CONDITIONAL
**Gap confirmed:** merchandising_consistency / dynamic_facets_personalization scored {X}/10

Formula: `monthly_search_sessions × current_conversion × AOV_delta × 12`
Pre-filled: `{X}M × 15% × [fill in conversion] × AOV_delta × 12`
Conservative (+5% AOV): `[formula with inputs] = $[result]M/year` [ESTIMATE]
Moderate (+10% AOV): `[formula with inputs] = $[result]M/year` [ESTIMATE]
Source: [{URL if verified}] [{FACT/ESTIMATE label}]

---

## Component 3: Bounce Rate Reduction
**Status:** ACTIVE / CONDITIONAL
**Data:** Bounce rate = {X}% [FACT — SimilarWeb MCP]

Formula: `monthly_visits × search_usage_rate × bounce_delta × recovery_conversion × AOV × 12`
Pre-filled: `{X}M × 15% × 10pp delta × 10% recovery × $[AOV] × 12`
Conservative (10pp bounce reduction, 10% recovery): `[formula] = $[result]M/year` [ESTIMATE]
Moderate (15pp bounce reduction, 12% recovery): `[formula] = $[result]M/year` [ESTIMATE]

---

## Component 4: No-Results Recovery
**Status:** ACTIVE / CONDITIONAL
**Gap confirmed:** typo_tolerance / semantic_nlp_search scored {X}/10

Formula: `monthly_searches × no_results_rate × AOV × recovery_rate × 12`
Pre-filled: `{X}M × 5% [ESTIMATE] × $[AOV] × 15% recovery × 12`
Conservative: `[formula] = $[result]M/year`
Moderate: `[formula with 8% no-results rate] = $[result]M/year`
Benchmark: Baymard Institute — 34% of e-commerce sites fail basic search adequacy
Source: [https://baymard.com — verify before citing] [FACT/ESTIMATE label]

---

## Component 5: Speed / Latency Gain
**Status:** ACTIVE / CONDITIONAL
**Gap confirmed:** latency scored {X}/10

Formula: `monthly_visits × search_usage_rate × (current_latency_ms - 100ms) / 100ms × 1% × AOV × 12`
Pre-filled: `{X}M × 15% × [current_latency_delta / 100ms] × 1% × $[AOV] × 12`
Conservative (200ms baseline → 100ms, 1 delay bucket): `[formula] = $[result]M/year` [ESTIMATE]
Moderate (400ms baseline → 100ms, 3 delay buckets): `[formula] = $[result]M/year` [ESTIMATE]
Benchmark: Amazon — 100ms latency = 1% revenue loss [ESTIMATE — Amazon 2006, widely cited; no verified primary URL]

---

## Component 6: Long-Tail Discovery
**Status:** ACTIVE / CONDITIONAL
**Gap confirmed:** semantic_nlp_search scored {X}/10

Formula: `monthly_searches × nlp_fail_rate × AOV × recovery_rate × 12`
Pre-filled: `{X}M × 20% NLP fail [ESTIMATE] × $[AOV] × 12% recovery × 12`
Conservative (20% NLP fail rate, 12% recovery): `[formula] = $[result]M/year` [ESTIMATE]
Moderate (30% NLP fail rate, 15% recovery): `[formula] = $[result]M/year` [ESTIMATE]

---

## Total Conservative Scenario

`C1 + C2 + C3 + C4 + C5 + C6 = $[total]M/year`

Full expansion:
- C1: $[X]M (monthly_visits × 15% × 0.15 × $AOV × 12)
- C2: $[X]M (monthly_search_sessions × conversion × 0.05 × $AOV × 12)
- C3: $[X]M (monthly_visits × 15% × 10pp × 10% × $AOV × 12)
- C4: $[X]M (monthly_searches × 5% × $AOV × 15% × 12)
- C5: $[X]M (monthly_visits × 15% × 1 bucket × 1% × $AOV × 12)
- C6: $[X]M (monthly_searches × 20% × $AOV × 12% × 12)
= **$[total]M/year conservative**

CRITICAL ASSUMPTIONS — AE must replace with real numbers to validate:
- [ ] AOV used: $[value] [ESTIMATE or source]
- [ ] Conversion rate used: [value]% [ESTIMATE or source]
- [ ] All [ESTIMATE] inputs listed above

---

## Total Moderate Scenario

`C1 + C2 + C3 + C4 + C5 + C6 = $[total]M/year`
[Show formula expansion — same structure as conservative]

---

## Competitor Evidence

[Include only if Golden Angle exists in 04-competitors.md AND case study URL is WebFetch-confirmed]
[If no verified evidence: omit section entirely — do not fabricate]

---

## AE Talking Point

"Based on {Company}'s ${X}B digital revenue and {X}M monthly visitors,
the biggest search opportunity is [Component N — name the specific gap].
If we can improve [metric] by [X]% — which is the Algolia average for sites with this gap —
that's ${Y}M/year. Replace those estimates with your actual [AOV / conversion rate]
and the number only goes up. That's the conversation."

---

*All figures derived from: audit research files + industry benchmarks. [ESTIMATE] inputs must be replaced with prospect's actual numbers before presenting to executive stakeholders.*
*Generated by algolia-synth-business-case | {date}*
```

---

## Verification Gate

After writing the output file, verify:

```bash
# Check file exists and has content
wc -c "$AUDIT_DIR/{Company}/deliverables/{slug}-business-case.md"
# Must be ≥ 4000 bytes

# Check all 6 components present
grep -c "^## Component" "$AUDIT_DIR/{Company}/deliverables/{slug}-business-case.md"
# Must return 6
```

Pass conditions:
- File size ≥ 4000 bytes
- All 6 components present (grep returns 6)
- No component section contains a dollar figure without a preceding formula line
- Every [ESTIMATE] input listed in the ASSUMPTION INVENTORY
- **Every dollar figure in the file matches a figure emitted by `calculate-roi.py
  --components`.** Re-run the script and diff: if a number in the file is not in the
  script output, you computed it by hand — that is a BLOCKING violation. Replace it
  with the script's figure or mark the component SKIPPED.

If any condition fails: append a `## VERIFICATION FAILURES` section to the file listing what is missing. Do not silently pass.
