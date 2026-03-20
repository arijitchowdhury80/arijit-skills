---
name: algolia-audit-report
description: Run Phase 3-5 of Algolia Search Audit. Scores search gaps, generates audit-data.json, runs the renderer pipeline (SPA + HTML deliverables + PDF), and writes AE Pre-Call Brief and Strategic Signal Brief. Requires Phase 1 + Phase 2 workspace to exist.
---

## CANONICAL PATH DEFINITIONS

```
AUDIT_DIR  = ~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit
ARIAN_DIR  = ~/algolia-arian-v2
SKILLS_DIR = ~/.claude/skills/algolia-search-audit
```

**Every audit MUST use this structure:**
```
$AUDIT_DIR/{CompanyName}/
├── research/          ← scratchpads 01-12, CHECKPOINT.md, FACTCHECK_GATE.md
├── factcheck/         ← factcheck dimension files (never published)
├── scripts/           ← company-specific scripts only
└── deliverables/
    ├── index.html                ← SPA
    ├── screenshots/              ← browser audit screenshots
    ├── ae-report.html
    ├── battle-card.html
    ├── leave-behind.html
    └── {slug}-*.md               ← markdown reports
```

**Published to GitHub/Vercel:**
```
$ARIAN_DIR/{slug}/                ← mirrors $AUDIT_DIR/{CompanyName}/deliverables/
├── index.html
├── screenshots/
├── ae-report.html
├── battle-card.html
└── leave-behind.html
$ARIAN_DIR/{slug}-audit-data.json ← JSON stays at root
```



# Algolia Audit — Phase 3-5: Scoring & Deliverables

Standalone sub-skill. Reads existing scratchpad files and browser findings produced by `/algolia-search-audit --phase research` and `--phase searchaudit`. Produces all scored output and final deliverables.

**Do not run this if Phase 1 scratchpad files or Phase 2 browser findings are missing — it will produce hallucinated data.**

## Input

`$ARGUMENTS` — company slug (e.g., `costco`). Workspace at `$AUDIT_DIR/Costco/research/`

`$AUDIT_DIR = ~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit`

Optional flags:
- `--deliverable {name}` — generate only one deliverable: `site` | `ae-report` | `battle-card` | `leave-behind` | `aebrief` | `signalbrief`
- `--skip-pdf` — skip PDF generation (faster iteration on HTML deliverables)

## Required Workspace Files

All files below must exist before starting. If any are missing, warn the user and stop.

```
$AUDIT_DIR/{CompanyName}/research/
├── 01-company-context.md       ← Company overview, ticker, executives, case studies
├── 02-tech-stack.md            ← BuiltWith + SimilarWeb technology findings
├── 03-traffic-data.md          ← SimilarWeb traffic metrics (with API Parameters header)
├── 04-competitors.md           ← Competitor matrix with verified search providers
├── 05-test-queries.md          ← Vertically calibrated test queries
├── 06-strategic-context.md     ← Strategic angles + trigger events
├── 07-hiring-signals.md        ← Hiring signals + buying committee map
├── 08-financial-profile.md     ← 3-year financial trends, ROI estimate
├── 09-browser-findings.md      ← Phase 2 browser test observations
├── 10-scoring-matrix.md        ← (written by Phase 3 in this skill)
├── 11-investor-intelligence.md ← Executive quotes from SEC/earnings calls
├── 12-icp-priority-mapping.md  ← ICP-to-Priority mapping synthesis
└── screenshots/                ← Must contain ≥10 verified .png files
```

## Output Files (8 deliverables)

| File | Format | Audience | How Generated |
|------|--------|----------|---------------|
| `{company}-audit-data.json` | JSON | Internal (source of truth) | Claude writes from scratchpad |
| `{company}/index.html` | HTML SPA | AE, SE, BD | `render-audit.ts site` |
| `{slug}/ae-report.html` | HTML | AE action card | `render-audit.ts ae-report` |
| `{slug}/battle-card.html` | HTML | AE/SE deal room | `render-audit.ts battle-card` |
| `{slug}/leave-behind.html` | HTML | Prospect-facing | `render-audit.ts leave-behind` |
| `{company}-leave-behind.pdf` | PDF | Prospect-facing | `generate-pdf.sh leave-behind` |
| `{company}-ae-precall-brief.md` | Markdown | AE internal | Claude writes |
| `{company}-strategic-signal-brief.md` | Markdown | Downstream LLM | Claude writes |

Also retained: `{company}-search-audit.md` — Phase 4 full research report.

## Checkpoint

Write/update `$AUDIT_DIR/{CompanyName}/research/CHECKPOINT.md` at each phase boundary:
- Phase 3 complete: scoring matrix written
- Phase 4 complete: audit report written + Gate 4 passed
- Phase 5a complete: audit-data.json written + validated
- Phase 5b complete: renderer executed + output verified
- Phase 5c complete: PDF generated
- Phase 5d+e complete: AE brief + signal brief written

## MCP Servers Required

No MCP data collection. All data read from scratchpad files.
Chrome headless used only for PDF generation in Step 5c.

---

## Pre-Deliverable Data Refresh (MANDATORY — run before EACH deliverable)

Context compaction corrupts numerical data in memory. Before generating EACH deliverable file (Phase 4 and Steps 5a through 5e), re-read these 5 critical scratchpad files:

1. `Read 03-traffic-data.md` — Exact traffic source percentages, demographics (all 6 age brackets)
2. `Read 04-competitors.md` — Exact competitor names, bounce rates, traffic volumes, search providers
3. `Read 08-financial-profile.md` — Exact revenue, EBITDA, margin zone, ROI figures
4. `Read 10-scoring-matrix.md` — Exact scores per area, severity distribution, overall score
5. `Read 11-investor-intelligence.md` — Exact quotes with speaker names, titles, source URLs

**Copy-paste mandate (non-negotiable)**:
- ROI calculations: Copy-paste the EXACT revenue base, digital share %, and ROI table directly from `08-financial-profile.md`. Never reconstruct financial figures from context memory.
- Quotes: Copy-paste the EXACT attribution (Speaker, Title, Source Name, URL) from `11-investor-intelligence.md`. Never rely on context memory for source attributions.
- Traffic: Copy-paste the EXACT percentages from `03-traffic-data.md`. Never regenerate plausible-looking numbers that sum to 100%.
- Data tables: For ANY table containing competitor data, traffic breakdowns, demographics, or financials — COPY the exact table from the scratchpad. Never regenerate tables from memory (column-scrambling risk).

**Spot-check after each deliverable**: Grep for 3 values — Paid Search % from scratchpad 03, first-competitor bounce rate from scratchpad 04, revenue figure from scratchpad 08. If any spot-check fails, re-read the scratchpad and correct before proceeding.

**Why this exists**: Uncommon Goods audit (2026-02-24) had $179M propagate through 8 data points when the actual value was $227M (27% error). TheRealReal audit (2026-02-23) content spec generated after compaction had 12 data errors — competitor bounce rates scrambled, demographics wrong.

---

## Phase 3: Score the Audit (10 Areas)

> Write the complete scoring matrix to `10-scoring-matrix.md`.

For each of the 10 challenge areas, assign a score (0–10) and severity (HIGH / MEDIUM / LOW) based on browser findings in `09-browser-findings.md`.

### Core Challenge Areas (1–6)

| Area | HIGH Severity | MEDIUM Severity | LOW Severity |
|------|--------------|----------------|--------------|
| **1. Latency** | >500ms or full page reload | 300–500ms | <300ms |
| **2. Typo Tolerance** | No typo handling — misspellings return zero results | Partial handling — some typos corrected | Good tolerance across tested queries |
| **3. Query Suggestions / Empty State** | Blank empty state AND poor no-results page | One of the two is lacking | Both empty state and no-results are well-handled |
| **4. Intent Detection** | No category, brand, or attribute detection | Partial detection — some intent types handled | Good detection across brand, category, attribute intents |
| **5. Merchandising Consistency** | Major differences between search and browse views | Minor inconsistencies | Consistent results and ranking across both |
| **6. Content Commerce / Front-End UX** | No federated search AND poor UX | Some federated OR some UX issues | Good federated search + polished UX |

### Algolia Value-Prop Areas (7–10)

| Area | HIGH Severity | MEDIUM Severity | LOW Severity |
|------|--------------|----------------|--------------|
| **7. Semantic / NLP Search** | Pure keyword match — conversational queries fail | Partial NLP — some intent understood | Good semantic understanding across tested NLP queries |
| **8. Dynamic Facets & Personalization** | Static filters + zero personalization | Some dynamic facets OR some personalization | Dynamic filters by context + visible personalization signals |
| **9. Recommendations & Merchandising** | No recommendations AND no banners | Some recommendations OR some rules | Relevant recommendations + active merchandising rules |
| **10. Search Intelligence** | No trending/popular/analytics signals | 1–2 analytics signals present | 3+ analytics signals visible |

### Overall Score Calculation Formula

Use a weighted average where HIGH-severity areas receive 2× weight, penalizing critical gaps:

```
For each of the 10 areas:
  weight = 2.0 if severity == HIGH
  weight = 1.0 if severity == MEDIUM
  weight = 0.5 if severity == LOW

overall_score = sum(score_i × weight_i) / sum(weight_i)
```

**Example**: Scores [8, 8, 4, 4, 9, 2, 2, 5, 2, 4] with severity [LOW, LOW, HIGH, MEDIUM, LOW, HIGH, HIGH, MEDIUM, HIGH, MEDIUM]:
- Numerator: 8(0.5) + 8(0.5) + 4(2) + 4(1) + 9(0.5) + 2(2) + 2(2) + 5(1) + 2(2) + 4(1) = 45.5
- Denominator: 0.5 + 0.5 + 2 + 1 + 0.5 + 2 + 2 + 1 + 2 + 1 = 12.5
- Score: 45.5 / 12.5 = **3.6/10**

**Always show the formula, all 10 inputs, and the full calculation in `10-scoring-matrix.md`.** This makes the score reproducible and verifiable by the fact-check skill.

### Gate 3: Verify Before Writing Report (BLOCKING)

- [ ] All 10 areas scored with evidence (screenshot file reference per finding)
- [ ] Severity assigned for all 10 areas (HIGH / MEDIUM / LOW)
- [ ] Overall score calculated with formula shown
- [ ] `10-scoring-matrix.md` written

---

## Phase 4: Generate Main Report

Create `{company}-search-audit.md`. Re-read all 5 critical scratchpad files before starting (Pre-Deliverable Data Refresh above).

### Report Structure

```markdown
# {Company Name} — Algolia Search Audit
**Date**: {today's date}
**Website**: {url}
**Prepared by**: Algolia

---

## Executive Summary
{2–3 sentence overview: top gaps, biggest opportunities, overall score}

## Strategic Intelligence

> **Why Now**: {1-sentence timing thesis}

### Timing Signals
| Signal | Evidence | Source | Implication |
|--------|----------|--------|-------------|

### Trigger Events
| Trigger | Opening Line for AE | Source |

### ⚠️ Caution Signals (shown only when detected)

## In Their Own Words (Investor Intelligence)

> {Quote #1 — verbatim}
> — {Speaker Name}, {Title}, {Source + Date}

**What we found**: {matching audit finding}
**Algolia solution**: {product + expected impact}

> {Quote #2 — verbatim}
> — {Speaker Name}, {Title}, {Source + Date}

**What we found**: {matching audit finding}
**Algolia solution**: {product + expected impact}

### Forward Guidance
### Risk Factors Mentioning Digital/Technology

## Company Context
## Technology Stack Deep Dive
## Competitor Landscape
## Financial Profile
## Strategic Leadership
## Buying Committee (Deal Stakeholders)
## Hiring Signal Analysis
## Revenue Impact Estimate
## ICP-to-Priority Mapping

## Search Audit Findings
### Audit Recap (10-row scoring table)
### Detailed Findings
{Per gap: query tested → what happened → screenshot reference → why it matters + SAIM stat → Algolia solution}

## Opportunities
## Algolia Value-Prop Assessment (7-row product table)
## How Algolia Can Help
## Next Steps
```

### "In Their Own Words" Formatting Rules

Each entry in the "In Their Own Words" section must follow this exact format:
- Block-quote the verbatim text (use `>` markdown)
- Attribution line: `— {Speaker Name}, {Title}, {Source Name}, {Month YYYY}`
- Then two lines: **What we found** (the contradicting or supporting audit gap), **Algolia solution** (specific product with expected result)
- Source URL must be linked inline on the attribution line

### Quote Attribution Standards (MANDATORY — Gate 4)

A quote with wrong attribution or wrong wording damages credibility more than no quote at all.

**Rule 1 — Verbatim or nothing**: Use `"quotation marks"` ONLY for exact verbatim text verified at source. If you cannot confirm exact wording via WebFetch or document text, do NOT use quotation marks.

**Rule 2 — Paraphrases must be labeled**: When summarizing without exact wording, use *[Name] said that...* or *[Name] noted that...* — never quote marks.

**Rule 3 — Attribution completeness**: Every quoted statement must include: Speaker Name, Speaker Title at time of statement, Source Type (earnings call / 10-K / investor day / interview), Source Name (e.g., "Q3 FY2025 Earnings Call"), Date, and URL.

**Rule 4 — WebFetch before you quote**: Before including ANY executive quote in a deliverable, WebFetch the source URL and confirm the exact text. Do not rely on context memory — memory paraphrases.

**Rule 5 — No constructed quotes**: Never synthesize a quote by combining phrases from different parts of a document. Quote a single contiguous statement.

### Case Study Verification Gate (MANDATORY)

Before citing ANY Algolia case study in any deliverable:

1. WebFetch the exact URL (e.g., `algolia.com/customers/{company}/`)
2. If 404: search `algolia.com/customers/` for the correct variant (e.g., `/gymshark-recommend/` not `/gymshark/`)
3. Extract the EXACT metric from the live page — specific number, what it measures (conversion rate vs revenue vs order rate vs CTR), and which Algolia product was used
4. Extract the EXACT timeframe — only if explicitly stated. If no timeframe is mentioned, do NOT add one.
5. Record in scratchpad before propagating:
   ```
   CASE STUDY: {Company}
   URL: {verified live URL}
   METRIC: {exact metric from page, e.g., "+37% conversion rate improvement"}
   PRODUCT: {exact Algolia product name from page}
   TIMEFRAME: {from page, or "NOT STATED"}
   CONTEXT: {qualifying context if stated}
   ```

**Forbidden patterns** (caused 5 of 6 case study errors in Oriental Trading audit 2026-02-24):
- Adding timeframes not on the page (e.g., "in 6 months")
- Changing metric types (e.g., "conversion rate" → "revenue")
- Changing product names (e.g., "Algolia Recommend" → "Algolia Personalization")
- Using parent URLs when case study lives at a variant
- Citing a specific percentage when source says "double-digit"

### Link Verification Gate (MANDATORY)

Before finalizing the report, extract ALL URLs and WebFetch each one. If 404/403:
1. Search for the correct URL
2. If found, replace with correct URL
3. If not found, remove citation and mark claim as unverifiable

### Gate 4: After Phase 4 — Verify Before Generating Deliverables (BLOCKING)

**Report must contain ALL sections**:
- [ ] Executive Summary
- [ ] Strategic Intelligence (Timing Signals + Trigger Events)
- [ ] In Their Own Words (with speaker names + titles for every quote)
- [ ] Company Context
- [ ] Technology Stack Deep Dive
- [ ] Competitor Landscape
- [ ] Financial Profile
- [ ] Strategic Leadership
- [ ] Buying Committee
- [ ] Hiring Signal Analysis
- [ ] Revenue Impact Estimate
- [ ] ICP-to-Priority Mapping
- [ ] Audit Recap (10-row scoring table)
- [ ] Detailed Findings (each with screenshot reference)
- [ ] Opportunities
- [ ] Algolia Value-Prop Assessment
- [ ] How Algolia Can Help
- [ ] Next Steps
- [ ] Source URLs throughout

**Gate 4 Quote Checklist**:
- [ ] Every quoted statement WebFetched at its source URL within this session
- [ ] Exact wording matches the source document (not paraphrased)
- [ ] Attribution includes: Name, Title, Source Name, Date, URL
- [ ] No statement in quotation marks sourced from WebSearch snippets (those are summaries, not verbatim)
- [ ] "In Their Own Words" section: every entry has a direct source URL that resolves to the document

### Gate 4.5: MANDATORY Fact Verification (BLOCKING — prevents hallucinated data)

> This gate is non-negotiable. Do not proceed to Phase 5 without completing all checks.

**4.5.1 Revenue Data Verification**:
- [ ] Revenue figure verified against primary source (ecdb.com, SEC filing, or company IR)
- [ ] Revenue year matches current/prior fiscal year (not older)
- [ ] If private company: source explicitly named, confidence marked MEDIUM or LOW
- [ ] Revenue cross-referenced against 2nd source if available

**4.5.2 Source Freshness Validation**:
- [ ] Financial data: source < 12 months old
- [ ] Employee count: source < 12 months old
- [ ] Traffic data: source < 3 months old (SimilarWeb refreshes monthly)
- [ ] Tech stack: source < 6 months old
- [ ] No sources older than 2 years used for any current-state claim

**4.5.3 Cross-Reference Validation**:
- [ ] Revenue cross-referenced (if only 1 source: mark LOW confidence in deliverables)
- [ ] Employee count cross-referenced OR removed from deliverables
- [ ] Any metric with >20% discrepancy between sources: flagged with confidence warning

**4.5.4 Unverifiable Data Handling**:
If a data point CANNOT be verified against a primary source:
1. Remove it from deliverables entirely, OR
2. Mark it explicitly as `[UNVERIFIED - USE WITH CAUTION]`
3. Never present unverified data as fact

**Blocking condition**: If any of 4.5.1–4.5.4 fails, DO NOT proceed to Phase 5. Fix data first.

---

## Phase 5: Generate Deliverables (Renderer Pipeline)

The renderer is deterministic — Claude NEVER generates layout HTML. Claude writes only `audit-data.json`. The renderer handles all HTML structure, SVG geometry, and brand standards.

### Step 5a: Write audit-data.json

**Pre-requisite**: Complete the Pre-Deliverable Data Refresh (re-read all 5 critical scratchpad files).

Write `{company}-audit-data.json` to the working directory. Schema reference: `~/.claude/skills/algolia-search-audit/templates/audit-data.schema.json`

**Field-by-field mapping**:

| JSON Field | Source Scratchpad | Key Rules |
|------------|------------------|-----------|
| `meta.company` | `01-company-context.md` | Display name, e.g. "Costco Wholesale" |
| `meta.domain` | URL from audit input | e.g. "costco.com" |
| `meta.audit_date` | Today's date | YYYY-MM-DD |
| `meta.audited_by` | AE name (ask if unknown) | |
| `meta.data_vintage.*` | API response metadata | NOT today's date — use actual API dates |
| `cover.photo_url` | WebSearch | Search: `{company} storefront exterior OR headquarters site:wikimedia.org`. Must be absolute HTTPS URL. |
| `cover.company_logo_url` | `https://logo.clearbit.com/{domain}` | WebFetch to verify 200 OK. If 404, WebSearch for official logo URL. |
| `score.overall` | `10-scoring-matrix.md` | Copy exact value |
| `score.overall` | `10-scoring-matrix.md` | Copy exact weighted value |
| `score.breakdown.*` | `10-scoring-matrix.md` | **10 areas** — see breakdown keys below |
| `score.breakdown_labels.*` | `10-scoring-matrix.md` | Human-readable label per area key |
| `score.breakdown_severity.*` | `10-scoring-matrix.md` | HIGH / MEDIUM / LOW per area |
| `score.critical_count` | `10-scoring-matrix.md` | Count of HIGH severity areas |
| `score.moderate_count` | `10-scoring-matrix.md` | Count of MEDIUM severity areas |
| `company_snapshot` | `01-company-context.md` + `08-financial-profile.md` | Revenue, employees, founded, ticker, HQ |
| `company_snapshot.current_search_vendor` | `02-tech-stack.md` | From ACTIVE (confirmed) network inspection — NOT "TAG ONLY" |
| `company_snapshot.monthly_visits` | `03-traffic-data.md` | Include `/mo` suffix in value |
| `executives[]` | `11-investor-intelligence.md` | Exact quote, no paraphrase. URL required. quote_date (YYYY-MM). |
| `intelligence_signals[]` | ALL scratchpad files + `09b-social-signals.md` + `09c-news-signals.md` | See signal mining rules below. Include social posts (type: "media") and news (type: "funding"/"industry-opp") if Apify files exist. Always include `source_url` (direct LinkedIn/Twitter/article URL). |
| `competitors[]` | `04-competitors.md` | Top 5 with verified search vendor |
| `findings[]` | `09-browser-findings.md` + `10-scoring-matrix.md` | See finding rules below |
| `gap_pairs[]` | `11-investor-intelligence.md` + `09-browser-findings.md` | Pair exec quote to contradicting audit finding |
| `financials` | `08-financial-profile.md` | COPY-PASTE exact figures. Include: `margin_zone`, `roi_scenarios{}` (conservative/moderate/optimistic), `roi_multiple`, `payback_period`, `berkshire_note` (if applicable), `algolia_annual_cost_est` |
| `financials.roi_scenarios` | `08-financial-profile.md` | Object with conservative/moderate/optimistic keys, each with `annual_impact`, `scenario_desc`, `source` |
| `traffic` | `03-traffic-data.md` | COPY-PASTE exact percentages. If SimilarWeb blocked, set null and explain in `source_url` |
| `tech_stack` | `02-tech-stack.md` | |
| `hiring` | `07-hiring-signals.md` | Full object: `total_open_roles`, `buying_committee[]`, `engagement_phases[]`, `objection_counters[]`, `build_vs_buy`, `run_research_lab` (if exists) |
| `strategic_angles[]` | `06-strategic-context.md` + `12-icp-priority-mapping.md` | 4 angles with `label`, `hook`, `pain_points[]`, `discovery_question`, `algolia_proof` |
| `icp_mapping` | `12-icp-priority-mapping.md` | Full object: `priority_to_product[]`, `outreach_sequence[]`, `anchor_lines[]` |
| `competitive_synthesis` | `04-competitors.md` + research | `scenario`, `competitor_tiers[]`, `experience_debt{}`, `positioning_matrix[]`, `positioning_statements{}`, `the_ask`, `roi_by_scenario{}` |
| `golden_angle` | `04-competitors.md` | Competitors confirmed using Algolia via BuiltWith + Shoe Carnival footwear case study if applicable |
| `ae_fields` | `12-icp-priority-mapping.md` + AE info | Urgency level, talk track opener, CTA |
| `next_steps` | `12-icp-priority-mapping.md` | 3 specific action steps with title + description |
| `bibliography` | ALL scratchpad files | Every URL cited, numbered sequentially |

**Score breakdown keys** (10 areas — use EXACTLY these key names):
```
latency | typo_tolerance | query_suggestions_empty_state | intent_detection |
merchandising_consistency | content_commerce_ux | semantic_nlp_search |
dynamic_facets_personalization | recommendations_merchandising | search_intelligence
```

**Buying committee object structure** (per role in `hiring.buying_committee[]`):
```json
{ "role": "Technical Buyer", "name": "...", "status": "OPEN/WARM/COLD",
  "signal": "hot/warm/cold", "message": "...", "job_url": "...", "salary_range": "..." }
```

**Engagement phases structure** (3 phases in `hiring.engagement_phases[]`):
```json
{ "phase": 1, "label": "Pre-Hire", "target": "IT Leadership",
  "message": "...", "timing": "..." }
```

**Finding rules** — each finding MUST have:
- `id`: F01, F02, ... in severity order (critical first)
- `screenshot_file`: relative path e.g. `screenshots/03-nlp-test.png` — MUST exist on disk
- `impact_stat`: MUST be a verbatim quote or paraphrase from a real, publicly accessible URL
  - **Before writing any impact_stat**: WebFetch the source URL and confirm the stat appears on that page
  - If the stat cannot be verified at a live URL: leave `impact_stat` as `""` and `impact_stat_source` as `""`
  - **NEVER write a plausible-sounding stat and attach a plausible-sounding URL** — verify first, write second
  - Acceptable sources: Baymard (free articles at baymard.com/blog), Algolia blog, McKinsey (free summaries), Salesforce State of Connected Customer (free), Forrester (free summaries)
  - Paywalled content: do NOT cite if you cannot read the full stat on the page
- `impact_stat_source`: URL to Baymard/Forrester/industry benchmark. Do NOT fabricate. Must have been WebFetched and confirmed to contain the stat before being written here.
- `algolia_case_study_url`: Verified live URL from Case Study Verification Gate
- `algolia_case_study_result`: Exact metric from live case study page (not paraphrased)
- `tested_query`: Exact query string typed during browser audit
- `severity`: `critical` | `moderate` | `positive`

**Intelligence signal mining** — one entry per insight type:

| Signal type | Source scratchpad | What to capture |
|-------------|------------------|-----------------|
| `exec` | `11-investor-intelligence.md` | CEO/CFO/CMO earnings call or 10-K quote about digital/CX |
| `media` | `06-strategic-context.md` | Named executive quoted in press, podcast, or interview |
| `funding` | `01-company-context.md` | Recent funding round, IPO, M&A, credit facility |
| `industry-risk` | `06-strategic-context.md` | Market headwind or competitive threat they face |
| `industry-opp` | `06-strategic-context.md` | Market tailwind or growth opportunity |
| `competitor` | `04-competitors.md` | A competitor making a move that creates urgency |
| `customer` | `06-strategic-context.md` | Customer satisfaction signal, NPS data, review trend |
| `partner` | `02-tech-stack.md` | Partner technology change or displacement signal |
| `hiring` | `07-hiring-signals.md` | Active hiring in search/personalization/digital |

Each signal MUST have `source_url` and `source_date`. Mark `relevance` as WHY this creates urgency for Algolia.

**ROI calculation** (if not already in `08-financial-profile.md`):
```
ecom_revenue = total_digital_revenue × 0.30  (or known ecom share if available)
search_addressable = ecom_revenue × 0.15
conservative_lift = search_addressable × 0.05
search_roi_est = format as "$XXM/yr"
```

**Validate before running renderer**:
```bash
ls -la {company}-audit-data.json

python3 -c "
import json
with open('{company}-audit-data.json') as f:
    d = json.load(f)
assert d['meta']['company'], 'company missing'
assert d['score']['overall'], 'score missing'
assert len(d['findings']) >= 3, f'only {len(d[\"findings\"])} findings'
assert all(f.get('screenshot_file') for f in d['findings']), 'finding missing screenshot_file'
print(f'✓ {len(d[\"findings\"])} findings, {len(d.get(\"intelligence_signals\", []))} signals, {len(d.get(\"executives\", []))} exec quotes')
"
```

### Step 5b: Run the Renderer (SPA + All HTML Deliverables)

```bash
SLUG="{company-slug}"
SCRIPTS=~/.claude/skills/algolia-search-audit/scripts

# Generate all HTML deliverables
deno run --allow-read --allow-write "${SCRIPTS}/render-audit.ts" "$SLUG" all
```

Templates used by the renderer (reference only — do not modify):
- `~/.claude/skills/algolia-search-audit/templates/index-template.html` → SPA
- `~/.claude/skills/algolia-search-audit/templates/ae-action-report-template.html` → AE report
- `~/.claude/skills/algolia-search-audit/templates/strategic-battle-card-template.html` → battle card
- `~/.claude/skills/algolia-search-audit/templates/prospect-leave-behind-template.html` → leave-behind
- `~/.claude/skills/algolia-search-audit/templates/components.css` → shared styles

**Verify output after running**:
```bash
# Check all files generated
ls -lh ${SLUG}/index.html ${SLUG}-ae-report.html ${SLUG}-battle-card.html \
       ${SLUG}-leave-behind.html

# Check SPA has data injected
grep -c 'window.AUDIT_DATA' ${SLUG}/index.html
# Expected: 1

# Check no unreplaced tokens in SPA
grep -o '{{[A-Z_]*}}' ${SLUG}/index.html | sort | uniq
# Expected: empty output
```

If renderer reports unreplaced tokens: for non-critical tokens proceed. For critical tokens (COMPANY_NAME, OVERALL_SCORE), check JSON field names match schema exactly.

### Step 5c: Generate PDF

```bash
cd "{working-directory}"
chmod +x ~/.claude/skills/algolia-search-audit/scripts/generate-pdf.sh
bash ~/.claude/skills/algolia-search-audit/scripts/generate-pdf.sh "$SLUG" leave-behind
```

Skip this step if `--skip-pdf` flag was provided.

**Verify**:
```bash
ls -lh ${SLUG}-leave-behind.pdf
# Expected: > 100KB
```

### Step 5d: AE Pre-Call Brief

Generate `{company}-ae-precall-brief.md` — AE-facing internal document, NOT for prospect. Every data point must have an inline hyperlink.

**Structure**:
1. **Executive Cheat Sheet** (5 bullets): Revenue + margin zone, business model, digital focus, top gap, opportunity + ROI
2. **Financial Profile** — 3-year trend table with hyperlinked source figures
3. **Key Executives** — Name, title, tenure, background, with LinkedIn/source URLs
4. **Recent News & Trigger Events** — bullet list with source links and publication dates
5. **Audit Highlights** — top 3 findings with evidence (screenshot references, query tested, result count)
6. **Discovery Questions** — 6–8 questions derived from audit findings and margin zone analysis
7. **Stakeholder Targets** — buying committee map (Economic Buyer, Technical Buyer, User Buyer, Champion)
8. **Pilot Strategy** — margin-zone-aware scope, KPIs, budget framing
9. **Competitive Context** — golden angle if any competitor uses Algolia
10. **Speaking Their Language** — discovery questions using company's OWN language from SEC filings/earnings calls, anchored to `12-icp-priority-mapping.md`

**Citation format**: Inline markdown hyperlinks `[Source](URL)` on every data point.

### Step 5e: Strategic Signal Brief

Generate `{company}-strategic-signal-brief.md` — 1-page brief for downstream LLM consumption. Every line is standalone with full context. Optimized for signal density, not narrative flow.

**Structure**:
```
## {Company} — Algolia Strategic Signal Brief
Generated: {date}

### 60-Second Story
{3–4 sentences: who they are, the gap, the timing, the ask}

### Timing Signals
- {signal 1} SOURCE: {url} DATE: {YYYY-MM-DD}
- {signal 2} SOURCE: {url} DATE: {YYYY-MM-DD}

### In Their Own Words
- SPEAKER: {Name} TITLE: {Title} QUOTE: "{exact quote}" SOURCE: {url} DATE: {YYYY-MM}
- SPEAKER: {Name} TITLE: {Title} QUOTE: "{exact quote}" SOURCE: {url} DATE: {YYYY-MM}

### People (Buying Committee)
- ROLE: {Economic Buyer} NAME: {Name} TITLE: {Title} SIGNAL: {why hot/warm} URL: {linkedin}

### Money
- REVENUE: ${X}M [{FACT/ESTIMATE}] SOURCE: {url}
- EBITDA MARGIN: {X}% ZONE: {Red/Yellow/Green} SOURCE: {url}
- SEARCH ROI EST: ${X}M/yr (formula: {inputs})

### Search Gaps Found
- GAP: {gap name} QUERY: "{tested query}" RESULT: {observed result} SCREENSHOT: screenshots/{nn}-{slug}.png
- GAP: ...

### Hiring Intelligence
- ROLE: "{job title}" URL: {careers page url} SIGNAL: {interpretation}

### Competitive Landscape
- COMPETITOR: {name} SEARCH VENDOR: {vendor} METHOD: {BuiltWith + Network / BuiltWith only} USES ALGOLIA: {Yes/No}

### ICP-to-Priority Mapping
- THEIR PRIORITY: "{exec quote}" → ALGOLIA: {product} → QUESTION: "{discovery question}"

### The Angle
{1–2 sentences: the strongest reason for this specific prospect to act now}

### Sources
[numbered list of all URLs used]
```

**Citation format**: `SOURCE: {url}` on every standalone line.

---

## Gate 5: Deliverable Completeness (BLOCKING)

Run the full validation script before declaring the audit complete:

```bash
SLUG="{company-slug}"
echo "========== GATE 5 VALIDATION =========="

# 5.1 audit-data.json exists and is valid JSON
python3 -c "import json; d=json.load(open('${SLUG}-audit-data.json')); print(f'✓ JSON valid: {len(d[\"findings\"])} findings, score {d[\"score\"][\"overall\"]}')" \
  && echo "   ✅ 5.1 JSON valid" || echo "   ⛔ 5.1 JSON MISSING OR INVALID"

# 5.2 SPA exists and has data injected
[ -f "${SLUG}/index.html" ] && grep -q 'window.AUDIT_DATA' "${SLUG}/index.html" \
  && echo "   ✅ 5.2 SPA index.html has data" || echo "   ⛔ 5.2 SPA MISSING OR NO DATA"

# 5.3 No unreplaced tokens in SPA
token_count=$(grep -o '{{[A-Z_]*}}' "${SLUG}/index.html" 2>/dev/null | wc -l | tr -d ' ')
echo "   Unreplaced tokens in SPA: $token_count (required: 0)"
[ "$token_count" -eq 0 ] && echo "   ✅ 5.3 No unreplaced tokens" || echo "   ⚠️  5.3 $token_count unreplaced tokens"

# 5.4 All HTML deliverables exist
for f in "${SLUG}-ae-report.html" "${SLUG}-battle-card.html" "${SLUG}-leave-behind.html"; do
  [ -f "$f" ] && echo "   ✅ 5.4 $f exists" || echo "   ⛔ 5.4 $f MISSING"
done

# 5.5 Leave-behind PDF exists and is > 100KB
pdf_size=$(stat -f%z "${SLUG}-leave-behind.pdf" 2>/dev/null || stat -c%s "${SLUG}-leave-behind.pdf" 2>/dev/null || echo 0)
echo "   PDF size: ${pdf_size} bytes (required: >100KB)"
[ "$pdf_size" -ge 100000 ] && echo "   ✅ 5.5 PDF generated" || echo "   ⛔ 5.5 PDF MISSING OR TOO SMALL"

# 5.6 Screenshots
screenshot_count=$(ls screenshots/ 2>/dev/null | wc -l | tr -d ' ')
echo "   Screenshots on disk: $screenshot_count (required: 10+)"
[ "$screenshot_count" -ge 10 ] && echo "   ✅ 5.6 Screenshots OK" || echo "   ⛔ 5.6 SCREENSHOT GATE FAILED"

# 5.7 Findings have screenshot references in JSON
screenshot_refs=$(grep -c '"screenshot_file"' "${SLUG}-audit-data.json" 2>/dev/null || echo 0)
echo "   Findings with screenshots in JSON: $screenshot_refs (required: 3+)"
[ "$screenshot_refs" -ge 3 ] && echo "   ✅ 5.7 Screenshot refs in JSON" || echo "   ⛔ 5.7 FINDINGS MISSING SCREENSHOTS"

# 5.8 AE brief + signal brief exist
[ -f "${SLUG}-ae-precall-brief.md" ] && echo "   ✅ 5.8 AE brief exists" || echo "   ⛔ 5.8 AE BRIEF MISSING"
[ -f "${SLUG}-strategic-signal-brief.md" ] && echo "   ✅ 5.8 Signal brief exists" || echo "   ⛔ 5.8 SIGNAL BRIEF MISSING"

# 5.9 AE brief has hyperlinks
ae_links=$(grep -c '](http' "${SLUG}-ae-precall-brief.md" 2>/dev/null || echo 0)
echo "   AE brief hyperlinks: $ae_links (required: 15+)"
[ "$ae_links" -ge 15 ] && echo "   ✅ 5.9 AE brief citations" || echo "   ⚠️  5.9 AE brief may have few citations"

# 5.10 Zero-byte screenshots check
zero_byte=$(find screenshots/ -empty 2>/dev/null | wc -l | tr -d ' ')
echo "   Zero-byte screenshots: $zero_byte (required: 0)"
[ "$zero_byte" -eq 0 ] && echo "   ✅ 5.10 No empty screenshots" || echo "   ⛔ 5.10 EMPTY SCREENSHOTS DETECTED"

echo "========================================"
```

# 5.11 Main report citation count
report_links=$(grep -c '](http' "${SLUG}-search-audit.md" 2>/dev/null || echo 0)
echo "   Report hyperlinks: $report_links (required: 20+)"
[ "$report_links" -ge 20 ] && echo "   ✅ 5.11 Report citations OK" || echo "   ⚠️  5.11 Report may have insufficient citations"

echo "========================================"
```

**Blocking failures**: If 5.1, 5.2, 5.5, 5.6, or 5.8 fail — DO NOT mark audit complete. Fix before proceeding.

**After Gate 5 passes**, output:
```
✅ Gate 5 PASSED — all deliverables verified.
Recommended next step: /algolia-audit-factcheck {company-slug}
(Standard tier — re-calls SimilarWeb/BuiltWith APIs, verifies source URLs, checks quote attribution)
```

### Gate 6: Statistic Source Verification (BLOCKING)

Every quantitative statistic cited with an external source URL must be verified at source:

1. WebFetch the URL
2. Search the page text for the exact number/percentage
3. If NOT found on the page: find the real source URL, or REMOVE the stat entirely
4. NEVER cite a statistic with a URL where the stat doesn't appear on that page

**Algolia corporate stats freshness** — always verify against latest from algolia.com:
- Customer count: check `algolia.com/customers/` (currently 18,000+ as of 2026-02)
- Searches/year: use 1.75T (or check `algolia.com/about/`)
- Records indexed: use 30 billion (or check for updates)

Checklist:
- [ ] All cited percentages/numbers verified at source URL
- [ ] Algolia corporate stats match current published figures
- [ ] No fabricated statistics (numbers that don't appear on cited page)

---

## Key Reference Data (SAIM — Search Audit Impact Map)

| Issue | Statistic | Algolia Case Study |
|-------|-----------|-------------------|
| No typo tolerance | 1 in 6 queries have typos | Lacoste: 37% increase in search revenue |
| Slow search | 39% leave if too slow; 100ms delay = 1% revenue loss | Under Armour: <20ms latency |
| No federated search | 68% would return to site with good search | Staples: improved content discoverability |
| No personalization | 80% prefer personalized experiences; 10–15% revenue lift | Gymshark: increased conversion |
| Poor relevance | 72% of sites have mediocre/broken relevance | Decathlon: 50% search conversion boost |
| No/bad filters | 43% lack sufficient filtering; filter users convert 2x | Birkenstock: dynamic faceting |
| Missing sort options | 46% missing at least one key sort option | Algolia Sort By Replicas |
| Browse/search inconsistency | Erodes user trust | Algolia unified index |
| No results pages | 12% of searches → no results; 75% leave | Herschel: 80% no-results reduction |
| Out of stock at top | Wastes real estate, frustrates users | Algolia custom ranking |
| Irrelevant recommendations | Recommendations drive 31% of e-commerce revenue | Algolia Recommend ML models |
| Not factoring reviews | 93% say reviews influence purchase | Algolia custom ranking with ratings |

## Vertical-to-Case-Study Mapping (MANDATORY)

Do NOT default to Lacoste/Decathlon for every audit. Select case studies matching the prospect's vertical.

| Prospect Vertical | Primary Case Study | Secondary Case Study |
|-------------------|-------------------|---------------------|
| Curated Marketplace / Gift Retail | Huckberry (+9.4% revenue) | Big W (+7% conversion) |
| Artisan / Handmade | Huckberry (+9.4% revenue) | Zenni (+34% search revenue) |
| Home Goods / Decor | Big W (+7% conversion) | Huckberry (+9.4% revenue) |
| Fashion / Apparel | Lacoste (+37% conversion) | Gymshark (+150% mobile orders) |
| Sporting Goods | Decathlon (+50% conversion) | Under Armour (<20ms latency) |
| Eyewear / Specialty Retail | Zenni (+9% conversion, +34% search revenue) | Big W (+7% conversion) |
| Auto Parts | O'Reilly Auto (+performance) | Zenni (+34% search revenue) |
| Luxury / Premium | Lacoste (+37% conversion) | Harry Rosen (+360% conversion) |
| B2B / Industrial | Grainger (federated search) | Staples (content discoverability) |
| General Retail | Big W (+7% conversion) | Zenni (+9% conversion) |

### Verified Case Study URLs (as of 2026-02)

| Company | URL |
|---------|-----|
| Huckberry | https://www.algolia.com/customers/huckberry |
| Big W | https://www.algolia.com/customers/bigw |
| Gymshark | https://www.algolia.com/customers/gymshark-recommend |
| Lacoste | https://www.algolia.com/customers/lacoste |
| Decathlon | https://www.algolia.com/customers/decathlon-singapore |
| Zenni | https://www.algolia.com/blog/ecommerce/how-3-retailers-are-using-ai-powered-search-and-discovery-to-crush-their-numbers |

Always WebFetch the URL before citing — do not assume it is still live.

---

## ICP-to-Priority Mapping (Step 14 Output)

Read `12-icp-priority-mapping.md` to extract the "Speaking Their Language" framing for the AE brief and signal brief. The format is:

```
## ICP-to-Priority Mapping — "Speaking Their Language"

### Priority-to-Product Map
| Their Stated Priority | Source | Algolia Solution | Discovery Question |
|---|---|---|---|
| "{exact quote from executive}" | Q4 2025 Earnings | NeuralSearch | "You told investors X — we can help with Y" |

### Anchor Points for AE
1. "{Company} told investors {X} — we can accelerate that with {product}"
```

Use these anchor points verbatim in the AE brief Section 10 ("Speaking Their Language") and in the signal brief ICP Mapping section. The goal is to use the prospect's exact language — not Algolia's language — to frame the value prop.

---

## Completion Output

After all gates pass, output a delivery summary:

```
Audit Deliverables — {Company Name}
Score: {X.X}/10 — {verdict: Critical Gaps Found / Moderate Issues / Strong Baseline}
Top 3 Gaps: {gap1}, {gap2}, {gap3}

Deliverables:
  {company}-search-audit.md     ({size})
  {company}-audit-data.json     ({size})
  {company}/index.html          ({size})
  {company}-ae-report.html      ({size})
  {company}-battle-card.html    ({size})
  {company}-leave-behind.html   ({size})
  {company}-leave-behind.pdf    ({size})
  {company}-ae-precall-brief.md ({size})
  {company}-strategic-signal-brief.md ({size})

Screenshots: {N} files on disk
Gate 5: PASSED (or list failing checks)
```

---

## SPA Visual Components (index-template.html — v2.9)

These components are implemented in `index-template.html` and rendered via `render-audit.ts`. They are NOT in the PDF book — SPA only.

### Minimum Font Size: 13px (MANDATORY)
No font-size below 13px anywhere in the SPA. The Python enforcement script:
```bash
python3 -c "
import re, sys
html = open('file.html').read()
def bump(m):
    v = float(m.group(1))
    return f'font-size:{max(v, 13):.0f}px'
html = re.sub(r'font-size:(\d+(?:\.\d+)?)px', bump, html)
open('file.html','w').write(html)
"
```

### Company Snapshot: Animated Gradient Blobs
Dark 3-layer layout (dark panel / stats strip / context row). Animated blobs generated by `gradientBlobs(colors, speed, opacity)` JS helper.
- **Panel blobs**: Algolia brand colors `['#003DFF','#5468FF','#00C8FF','#7C3AED']`, speed 22, opacity 0.13
- **Stats strip per-card blobs**: Per-card color palettes, speed 12, opacity 0.22
- **CSS keyframe**: `@keyframes cs-blob-move` with 5 bezier waypoints using CSS custom properties `--tx-1..4` / `--ty-1..4`
- **Blob filter**: `filter: blur(52px)` on each blob
- **Z-index**: blob layer z-index 0, content z-index 2 (`.cs-stats-item__inner`)

### Executive Summary: Softened Aurora Background
Aceternity Aurora translated to vanilla CSS. Key values (softened from original):
- `opacity: 0.22` (NOT 0.45 — too distracting)
- `filter: blur(18px) invert(1)` on base layer
- `mix-blend-mode: difference` on `::after`
- `-webkit-mask-image: radial-gradient(ellipse at 100% 0%, black 5%, transparent 50%)` — concentrates glow top-right
- `animation: aurora 120s linear infinite` (NOT 60s — too fast)
- Colors: `#003DFF #A5B4FC #93C5FD #C4B5FD #5468FF`

### Financial Profile: Scroll-Animated Timeline
3-year revenue as vertical timeline. IntersectionObserver drives node reveal + revenue bar animation.
- **CSS classes**: `.fin-timeline`, `.tl-node`, `.tl-card`, `.tl-rev-bar`, `.tl-roi-callout`
- **Activation**: `.tl-node--visible` added by IntersectionObserver at 25% threshold
- **Bar fill**: CSS `transition: width 1s cubic-bezier(0.4, 0, 0.2, 1) 0.3s` on `.tl-rev-bar__fill`, width from CSS var `--bar-pct`
- **Track fill**: `#fin-fill` height driven by scroll position via `window.addEventListener('scroll')`
- **Per node content**: revenue (large), digital revenue metric, search-driven metric, signal bullets, ROI callout on FY2025
- **Data source**: Read from `revenue_3y[]` in `audit-data.json` + hardcoded year-specific context in `sectionFinancials()`

### Inline Source Citations: `.inline-src` Pills
Every finding and stat must have a source pill, not raw text. Classes:
- `.inline-src` — blue pill, 11px, `background: rgba(0,61,255,0.06)`, `border: 1px solid rgba(0,61,255,0.15)`
- `.src-tag` — eyebrow-level source badge (SW / BW / YF / SEC)
- Findings: case study link rendered as green `.inline-src` pill

### SPA Init Order
```javascript
requestAnimationFrame(() => {
  initScrollSpy();
  initLightbox();
  initFinTimeline();  // ← added for timeline
});
```

---

## Visual Standards (v2.8 — Enhanced Visuals)

The PDF book must match NotebookLM-quality visuals. The `components.css` library includes 35 component types. These 7 standards apply to every audit book.

### 1. Score Meter (Speedometer Style)

The overall score MUST be displayed as a **speedometer-style meter** with red/yellow/green zones and a rotating needle.

**Component**: `.score-meter`

```html
<div class="score-meter" style="text-align: center;">
  <svg viewBox="0 0 200 140" style="width: 280px; height: auto;">
    <path d="M 20 100 A 80 80 0 0 1 100 20" fill="none" stroke="#DC2626" stroke-width="16" stroke-linecap="round"/>
    <path d="M 100 20 A 80 80 0 0 1 140 34" fill="none" stroke="#F59E0B" stroke-width="16"/>
    <path d="M 140 34 A 80 80 0 0 1 180 100" fill="none" stroke="#10B981" stroke-width="16" stroke-linecap="round"/>
    <!-- Needle — ROTATION FORMULA: -90 + (180 × score/10) -->
    <g transform="rotate({{NEEDLE_ROTATION}} 100 100)">
      <line x1="100" y1="100" x2="100" y2="30" stroke="#21243D" stroke-width="4" stroke-linecap="round"/>
      <circle cx="100" cy="100" r="8" fill="#21243D"/>
    </g>
    <text x="100" y="88" text-anchor="middle" font-size="32" font-weight="900" fill="#DC2626">{{SCORE}}</text>
    <text x="100" y="108" text-anchor="middle" font-size="12" font-weight="600" fill="#6B7280">out of 10</text>
    <text x="35" y="125" font-size="10" fill="#DC2626" font-weight="600">Critical</text>
    <text x="90" y="135" font-size="10" fill="#F59E0B" font-weight="600">Needs Work</text>
    <text x="155" y="125" font-size="10" fill="#10B981" font-weight="600">Good</text>
  </svg>
</div>
```

**Needle rotation**: `rotation = -90 + (180 × score / 10)`. Score 4.0 → rotate(-18). Score 5.0 → rotate(0). Score 7.0 → rotate(36).

**Color by score**: ≤4 → `#DC2626` (red). 5-6 → `#F59E0B` (amber). ≥7 → `#10B981` (green).

### 2. Severity Heatmap Table

Appendix A scoring table MUST use color-coded cells: HIGH = red, MED = amber, LOW = green.

**Cell classes**: `.severity--high`, `.severity--medium`, `.severity--low`, `.score-cell--N` (N=1-10).

### 3. Tapered Revenue Funnel

Revenue waterfall MUST be a tapered SVG funnel with 3 tiers (not CSS rectangles, not 4 tiers).

```html
<!-- CRITICAL: Bottom tier MUST be ≥100px wide to fit "$X.XM/year" text -->
<svg viewBox="0 0 500 320">
  <polygon points="40,10 460,10 400,90 100,90" fill="#c7d2fe"/>           <!-- Tier 1 -->
  <polygon points="100,100 400,100 340,180 160,180" fill="#a5b4fc"/>     <!-- Tier 2 -->
  <polygon points="160,190 340,190 305,280 195,280" fill="#818cf8"/>     <!-- Tier 3: 110px bottom — DO NOT NARROW -->
</svg>
```

**Anti-pattern** (causes text clipping — never use): 4 tiers with 40px bottom.

### 3a. Cover Page Logo Positioning

- **Algolia logo**: `position: absolute; bottom: 40px; left: 40px; height: 32px; z-index: 10`
- **Company logo**: `position: absolute; top: 40px; right: 40px; height: 40px; max-width: 180px; z-index: 10`

Never use flex row for logos — they will disappear behind background images without explicit absolute positioning.

### 3b. Pilot Success Metrics (The Ask Page)

Ch 4 MUST include a "Pilot Success Metrics" table alongside the timeline:

| Metric | Target |
|--------|--------|
| Search Conversion Rate | +10-15% |
| Zero-Results Rate | Reduce by 30-50% |
| Time-to-First-Click | Reduce by 20% |
| NLP Query Success | Measure "gift for mom" type queries |

Layout: two-column — left: timeline, right: KPI table + ROI callout.

### 4. Real Data Charts

Traffic sources, demographics, and competitor comparisons MUST use actual SVG charts:
- `.donut-multi` — multi-segment donut for traffic sources (circumference = 2π×40 = 251.33; each segment = `stroke-dasharray = (pct/100 × 251.33) (251.33 - that)`)
- `.demographics-chart` — age/gender pie with legend
- `.bar-chart-h` — horizontal bar for competitor comparison

### 5. Annotated Screenshots

Every finding screenshot MUST have visual callouts:
- `.annotation-circle` — red circle highlighting area of concern (`--sm`, `--md`, `--lg`, `--xl`)
- `.annotation-callout` — labeled callout with directional pointer (`--left`, `--right`, `--top`, `--bottom`)
- `.annotation-number` — numbered badge for multiple issues

```html
<div class="annotated-screenshot">
  <img src="screenshots/05-typo.png" alt="Typo test">
  <div class="annotation-circle annotation-circle--lg" style="top: 45%; left: 30%; transform: translate(-50%,-50%);"></div>
  <div class="annotation-callout annotation-callout--left" style="top: 45%; right: 10px;">1 RESULT</div>
</div>
```

### 6. Gap Diagrams

"Strategy vs Execution" MUST be visualized using `.gap-diagram` (two columns connected by broken bridge) or `.radar-chart` (5-axis, expected=green overlay vs actual=red).

### 7. Enhanced Flow Diagrams

Architecture flows: use `.flow-enhanced--pipeline` with gradient connectors and directional arrows. Box types: `--source` (gray), `--algolia` (blue-purple gradient), `--destination` (green gradient).

### Visual Standards Gate (add to Gate 5 checklist)

- [ ] Cover page: dual logos (absolute positioned) + company photo background + `© Algolia Confidential` footer
- [ ] Every chapter: `.page-header` (Algolia logo left + company logo right) + `.page-footer` (confidential + page number)
- [ ] Findings: `.finding__body--70-30` grid (7fr 3fr) — hero screenshot left, analysis right
- [ ] Score gauge: speedometer SVG with arc zones (not just a number)
- [ ] Appendix A: `.severity-heatmap` with color-coded cells
- [ ] Revenue funnel: 3-tier tapered SVG (not CSS, not 4-tier)
- [ ] Traffic sources: `.donut-multi` chart (not table)
- [ ] At least 5 screenshots have `.annotation-circle` or `.annotation-callout`
- [ ] All icons: SVG only (no emoji or Unicode in body content)

**Page dimensions**: Each `.chapter` is exactly `8.5in × 11in` (letter size), `overflow: hidden`, `page-break-after: always`.

**SVG text visibility**: NEVER use `fill="#5A5E9A"` (too light). Use `fill="#4B5563"` or `fill="#21243D"`. Minimum 11px labels, 13px important text, always `font-weight: 600+`.

---

## Lessons Learned

### TheRealReal Audit (2026-02-23) — Post-Compaction Data Hallucination

**Problem**: Content spec generated after context compaction had 12 data errors. Traffic sources summed to 100% but with wrong individual values. Competitor bounce rates assigned to wrong companies.

**Root cause**: Model regenerated internally consistent but factually wrong numbers from lossy memory.

**Fix applied**: Pre-Deliverable Data Refresh mandate — re-read ALL 12 scratchpad files before each deliverable. Data Table Freeze Rule — copy competitor tables verbatim from scratchpad 04, never regenerate.

### Uncommon Goods Audit (2026-02-24) — Incomplete Book Generation

**Problem**: Book PDF was 21 pages instead of 30+. ~10 chapters silently skipped (Tech Stack, AI Gap, Strategic Triggers, Appendices C-F).

**Root causes**:
1. Context window nearly full from reading 12 scratchpad files (~35K tokens)
2. No chapter-level verification gate — only phase-level gates existed
3. No incremental disk writes — tried to populate entire HTML at once

**Fixes applied**:
1. Book Chapter Checklist in workspace manifest — all 21+ chapters tracked with `[ ]`/`[x]`
2. Phase 5a split into 6 sub-phases (Act I → Act II → Act III → Act IV → Appendices → Final gate)
3. Gate 5: `grep -c 'class="chapter"'` must return ≥25; PDF page count must be ≥28
4. Blocking gates: audit cannot complete if chapter/page checks fail

**Key lesson**: Any task that fills context MUST have incremental disk writes with verification after each sub-phase. Context compaction is the #1 enemy of long multi-phase tasks.

### Quote Attribution (Uncommon Goods, 2026-02-24)

**Problem**: Partnership Economy Podcast quote attributed to "CNBC" across 3 deliverables because source was reconstructed from memory instead of re-read from scratchpad.

**Fix**: Before including ANY executive quote, re-read `11-investor-intelligence.md`. Copy exact attribution: Speaker Name, Title, Source Name, URL. Never rely on context memory for source attributions.

### Uncommon Goods — Fabricated Statistic (2026-02-24)

**Problem**: "77% of consumers prefer brands with ESG commitments" cited from a Sendoso page — number does not appear anywhere on that page.

**Fix**: Gate 6 (Statistic Source Verification) — for every quantitative stat, WebFetch the URL and confirm the number appears on the page. If not found: find the real source or remove the stat.
