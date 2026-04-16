# Agent Context — Mandatory Pre-Read for Every Agent
<!-- Every agent that edits skills, scripts, or templates MUST read this first. -->
<!-- These are hard constraints, not guidelines. Violations break the platform. -->

## 1. JSON Field Names — CANONICAL (use exactly these, never invent new ones)

### Top-level fields in audit-data.json (29 total)
meta | cover | score | company_snapshot | executives | intelligence_signals |
competitors | findings | gap_pairs | toc | financials | traffic | tech_stack |
ae_fields | next_steps | methodology | bibliography |
competitive_synthesis | golden_angle | strategic_angles | hiring | icp_mapping |
abx_sequence | case_studies | demos |
partner_intel |
tab_subtitles |
recommended_first_play |
industry_context

### Finding object fields (15 — EXACT names, case-sensitive)
id | title | severity | category | tested_query | expected_behavior |
actual_behavior | impact_stat | impact_stat_source | screenshot_file |
prospect_description | algolia_solution | algolia_case_study_url |
algolia_case_study_company | algolia_case_study_result

### Score object fields
overall | verdict | breakdown | breakdown_labels | breakdown_severity |
critical_count | moderate_count | low_count | formula_shown | source

### Score breakdown keys (10 areas — EXACT)
latency | typo_tolerance | query_suggestions_empty_state | intent_detection |
merchandising_consistency | content_commerce_ux | semantic_nlp_search |
dynamic_facets_personalization | recommendations_merchandising | search_intelligence

### Traffic object fields
monthly_visits | bounce_rate | pages_per_visit | visit_duration |
top_channels (ARRAY [{source, share}] — NOT an object) |
device_share ({mobile, desktop}) | demographics | source | source_url |
search_abandonment ({google_outbound_pct, google_outbound_mom_change, narrative}) |
ai_referral ({chatgpt_pct, chatgpt_mom, gemini_pct, total_ai_pct, narrative}) |
top_referrers (ARRAY [{domain, share_pct, mom_change}]) |
paid_search ({share_of_total_pct, top_keywords[], competitor_bidding, narrative}) |
competitor_traffic (ARRAY [{domain, visits_3mo}]) |
organic_search ({share_of_total_pct, branded_pct, non_branded_pct, top_non_branded_keywords[]}) |
geo_distribution (ARRAY [{country, traffic_share_pct, mom_change}]) |
outgoing_traffic (ARRAY [{domain, share_pct, mom_change}]) |
rankings ({global_rank, country_rank_us, industry_rank, industry_category}) |
referrals ({share_of_total_pct, top_referring_sites[], top_referring_industries[]}) |
referring_industries (ARRAY [{industry, share_pct}]) |
global_rank (number — convenience field for KPI tile) |
category_rank (number — convenience field for KPI tile) |
category (string — industry category name)

### Financials object extended fields (added via lift_financial_json)
analyst_consensus ({rating, mean_score, analysts_count, price_target_median, price_current, upside_pct, raw}) |
margins ({gross_margin_pct, ebitda_margin_pct, operating_margin_pct, net_margin_pct, margin_zone}) |
balance_sheet ({total_assets, total_debt, cash_and_equivalents, total_assets_fmt, total_debt_fmt, cash_fmt}) |
digital_revenue ({latest_year, estimated_amount, pct_of_total, yoy_change_pct, confidence})

### Tech Stack object extended fields (added via lift_techstack_json)
ai_search_gap ({app_has_ai, web_has_ai, app_ai_name, app_platform, app_ai_description, web_search_vendor, narrative}) |
data_acquisitions (ARRAY [{company, year, purpose}]) |
architecture_notes (string)

### Intelligence signal object extended fields (added via enrich_signals)
urgency_score (number 1-10 — higher = more urgent; leadership change → 9-10, social → 4) |
category_tag (string — ai_disruption | digital_transformation | cost_pressure | leadership_change | competitive_threat | tech_investment | expansion | strategic_signal)

### Hiring object extended fields (added via parse_hiring_extended)
total_open_roles (number) | icp_roles_count (number) |
null_signal_note (string — auto-generated when icp_roles_count == 0; absence IS a signal)

### Partner Intel object extended fields (added via parse_partner_extended)
unconfirmed_partners (ARRAY [{name, evidence, next_step, confidence: "INVESTIGATE"}]) |
sales_action_plan (ARRAY [{action, detail, contact_name, contact_title, priority}]) |
cio_background_signal (string — CIO former employer signal)

---

## 2. CSS Classes — USE ONLY THESE (defined in algolia-brand.css and index-template.html)

| Class | Use for |
|-------|---------|
| `.dp-tile` | Group related sections with light blue gradient card |
| `.card-3d` | White shadow card (case studies, findings) |
| `.card-3d--no-lift` | 3D card without translateY on hover |
| `.feature-grid` | Aceternity-style grid for signals/hiring/timing |
| `.feature-card` | Card within feature-grid |
| `.feature-card--high` | Red urgent variant |
| `.feature-card--medium` | Amber warning variant |
| `.feature-card--positive` | Green positive variant |
| `.feature-card--urgent` | Red urgent variant (alias) |
| `.feature-card--warning` | Amber warning variant (alias) |
| `.fc-icon` | Icon area within feature-card |
| `.fc-title-row` | Title row with accent bar |
| `.fc-accent-bar` | Left accent bar in feature-card |
| `.fc-title` | Title text within feature-card |
| `.fc-desc` | Description text within feature-card |
| `.fc-source` | Source line within feature-card |
| `.glow-card` | Interactive card with mouse-track glow |
| `.bounce-card` | Bounce/rotate on hover card |
| `.bounce-card--red` | Red variant |
| `.bounce-card--amber` | Amber variant |
| `.bounce-card--green` | Green variant |
| `.bounce-card__content` | Content area within bounce-card |
| `.bounce-card__gradient` | Gradient reveal area within bounce-card |
| `.bounce-card__amount` | Big dollar amount text |
| `.bounce-card__amount-sub` | Sub-label under amount |
| `.ab-container` | Animated background container |
| `.ab-highlight` | Sliding highlight element |
| `.ab-item` | Item within ab-container |
| `.proof-pill` | Hero-pill style case study badge |
| `.proof-pill--green` | Green variant |
| `.proof-pill--blue` | Blue variant |
| `.proof-pill--white` | White variant (on dark backgrounds) |
| `.proof-pill__badge` | Badge portion of proof-pill |
| `.proof-pill__label` | Label portion of proof-pill |
| `.inline-src` | Blue source citation pill |
| `.src-tag` | Source badge (SW / BW / YF / SEC) |
| `.severity--high` | Red severity cell |
| `.severity--medium` | Amber severity cell |
| `.severity--low` | Green severity cell |
| `.annotated-screenshot` | Screenshot wrapper with annotations |
| `.annotation-circle` | Red circle callout on screenshots |
| `.annotation-callout` | Labeled callout with pointer |
| `.finding-card-gradient__title` | Finding card title |
| `.finding-card-gradient__desc` | Finding card description |
| `.unverified-warning` | Red badge for unverified data points |
| `.unverified-wrapper` | Amber wrapper for web-search-only data |
| `.tab-subtitle` | Subtitle line shown under active tab button |
| `.section-strip` | Sticky horizontal section pill navigation bar |
| `.section-strip__pill` | Individual navigation pill within section strip |
| `.section-strip__pill--active` | Active/highlighted pill (Algolia Blue) |
| `.highlights-grid` | 4-card "get the highlights" grid on Summary tab |
| `.highlight-card` | Individual card within highlights-grid |
| `.highlight-card__icon` | Icon/emoji cell in highlight card |
| `.highlight-card__stat` | Primary stat display in highlight card |
| `.highlight-card__label` | Secondary label in highlight card |
| `.section-subtitle` | Personalized subtitle line under every section title |

**NEVER** invent new CSS classes. If you need a style, check if an existing class works.

---

## 3. T.* Typography Tokens — USE THESE, NEVER raw font-size/color/weight

| Token | Use for |
|-------|---------|
| `T.eyebrow` | Section labels (12px, uppercase, gray) |
| `T.eyebrowBlue` | Section labels in Algolia Blue |
| `T.eyebrowCol(color)` | Section labels in custom color |
| `T.body` | Body text (16px, gray) |
| `T.bodySm` | Secondary body (14px, gray) |
| `T.italic` | Quoted text (14px, italic) |
| `T.compact` | Dense info (12px, gray) |
| `T.h5` | Section headings (18px, bold) |
| `T.title` | Card titles (16px, bold) |
| `T.labelBlue` | Emphasis in Algolia Blue (14px) |
| `T.labelRed` | Alert labels |
| `T.labelGreen` | Success labels |
| `T.labelCol(color)` | Emphasis in custom color |

**NEVER write:** `style="font-size:14px"` or `style="color:#003DFF"` or `style="font-weight:600"`
**ALWAYS write:** `style="${T.labelBlue}"` or `style="${T.body}"`

---

## 4. JavaScript Function Names — USE THESE (defined in index-template.html)

| Function | What it renders |
|----------|----------------|
| `proofPill(url, company, result, variant)` | Evidence badge (variant: 'green'/'white'/'blue') |
| `renderGoldenAngleCard(ga)` | "Competitor uses Algolia" callout |
| `renderBerkshire(f)` | Investor/ownership note |
| `renderTopbar(D)` | Scrolling disclaimer bar |
| `renderNavItem(item, isChild)` | Left-rail nav item |
| `renderSections(D)` | Main content orchestrator |

**NEVER recreate these inline.** If you need one of these effects, call the function.

---

## 5. Module + File Naming Conventions

| Type | Convention | Examples |
|------|-----------|---------|
| Skills | `algolia-{layer}-{function}` | `algolia-intel-traffic`, `algolia-synth-scoring` |
| Scripts | kebab-case .js/.py/.sh | `audit-browser.js`, `parse-builtwith.js` |
| Output JSON | `{company-slug}-audit-data.json` | `costco-audit-data.json` |
| Scratchpad files | `{nn}-{slug}.md` (01-12) | `01-company-context.md`, `09-browser-findings.md` |
| Deliverable HTML | `{slug}-{type}.html` | `costco-ae-report.html` |
| Factcheck outputs | `{slug}-factcheck-report.md` | `costco-factcheck-report.md` |

---

## 6. Sub-skill Invocation Pattern — CORRECT vs WRONG

### CORRECT — Orchestrator uses Agent tool (isolated context window)
```
Spawn Agent:
  description: "algolia-audit-research for {CompanyName}"
  prompt: """
  MANDATORY FIRST: Read ~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md
  Use Skill tool: skill="algolia-audit-research", args="{slug}"
  Write progress to $ALGOLIA_AUDIT_DIR/{CompanyName}/audit-progress.jsonl
  """
Wait for agent to complete.
VERIFY: ls "$ALGOLIA_AUDIT_DIR/{Company}/research/*.md" | wc -l
If output < 12: STOP. Sub-skill did not execute. Alert user. Do not proceed.
If output ≥ 12: proceed to Phase 2.
```

### CORRECT — Sub-skill itself (inside the spawned agent) uses Skill tool
```
Use the Skill tool: skill="algolia-audit-research", args="{url}"
```

### WRONG — Orchestrator directly uses Skill tool (shares context window)
```
Use the Skill tool: skill="algolia-audit-research", args="{url}"   ← WRONG for orchestrator
```

### WRONG — Never write this
```
Read ~/.claude/skills/algolia-audit-research/SKILL.md and execute all Phase 0 + Phase 1 instructions.
```

### WRONG — Never write this either
```
Follow the instructions in the algolia-audit-research skill.
```

### Verification gate required after EVERY sub-skill call
| Sub-skill | Verification command | Pass condition |
|-----------|---------------------|---------------|
| algolia-audit-research | `ls research/*.md \| wc -l` | ≥ 12 files |
| algolia-live-signals | `ls research/09b-*.md research/09c-*.md` | both exist |
| algolia-audit-browser | `ls deliverables/screenshots/*.png \| wc -l` | ≥ 10 files |
| algolia-audit-report | `ls deliverables/costco-audit-data.json deliverables/costco/index.html` | both exist |
| algolia-audit-factcheck | `cat research/FACTCHECK_GATE.md \| grep ACTION` | ACTION present |
| render-audit.ts (SPA) | `grep -c "Algolia Brand CSS" deliverables/index.html` | ≥ 1 |

---

## 7. Path Convention — NEVER hardcode

### WRONG (never write this path)
`~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit`

### CORRECT
`$ALGOLIA_AUDIT_DIR`

### $ALGOLIA_AUDIT_DIR value
`/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit`

### SPA path (CRITICAL — slug appears ONCE, not twice)
- **Local:** `$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/index.html`
- **Vercel:** `https://algolia-arian-v2.vercel.app/{slug}/index.html`
- **Audit data:** `$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/{slug}-audit-data.json`
- **WRONG (slug twice):** `$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/{slug}/index.html` ← NEVER DO THIS

### Fallback pattern (add to every skill that uses paths)
```bash
# At start of skill execution:
if [ -z "$ALGOLIA_AUDIT_DIR" ]; then
  AUDIT_DIR="$(pwd)"
  echo "⚠️ ALGOLIA_AUDIT_DIR not set — using current directory: $AUDIT_DIR"
else
  AUDIT_DIR="$ALGOLIA_AUDIT_DIR"
fi
```

---

## 8. Test Isolation — CRITICAL RULE

**Tests must NEVER write to production workspaces.**

| Workspace type | Path | Rule |
|---------------|------|------|
| PRODUCTION | `$ALGOLIA_AUDIT_DIR/{CompanyName}/` | Real audit data. NEVER overwritten by isolation tests or spot-checks. |
| TEST | `$ALGOLIA_AUDIT_DIR/.test/{CompanyName}/` | Isolation tests only. Freely created and overwritten. |

**Before any write operation, declare its workspace type:**
- "This writes to PRODUCTION: [company] — [reason it is safe to overwrite]"
- "This writes to TEST: [company] — isolation test only"

**Integration tests use FRESH companies only** — companies with no existing workspace (no prior audit data to corrupt). Brooks Running and DSW have no existing workspaces. Use them for Phase D. Never run integration tests against Costco, TheRealReal, or Tapestry — they have real audit history.

**Failure mode that caused this rule:** B1 isolation test overwrote the production Costco workspace, degrading 5 of 12 scratchpad files. No git history, no restore. Data lost. This is unacceptable.

---

## 9. What Agents Must NEVER Do

| ❌ Never | ✅ Instead |
|---------|----------|
| Invent a new JSON field name | Check audit-data.schema.json first |
| Write raw inline font-size/color/weight | Use T.* tokens |
| Hardcode the Google Drive path | Use $ALGOLIA_AUDIT_DIR |
| Reference SEC EDGAR MCP | Use WebFetch of sec.gov directly |
| Write "Read SKILL.md and execute" | Use Skill tool with verification gate |
| Create a new CSS class | Use existing classes from algolia-brand.css |
| Add a new SPA section without schema update | Schema first → render function → CSS → register |
| Write HTML in SKILL.md instructions | HTML only goes in templates — never in skill files |
| Run isolation tests against a production workspace | Create $ALGOLIA_AUDIT_DIR/.test/{Company}/ first |
| Overwrite existing audit files without declaring workspace type | State PRODUCTION or TEST before writing |
| **Write `index.html` directly using the Write tool** | **Run `render-audit.ts` — it is the ONLY permitted way to produce SPA output** |

### SPA Output Rule — Zero Exceptions

`$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/index.html` MUST be produced by:
```
cd ~/.claude/skills/algolia-search-audit/scripts
deno run --allow-read --allow-write --allow-net render-audit.ts {slug} site
```

**Why this is non-negotiable:** `render-audit.ts` injects `algolia-brand.css` (`.proof-pill`, `.glow-card`, all brand classes) and `window.AUDIT_DATA` into the output. Writing `index.html` directly bypasses both injections — the SPA renders with broken styling and no data.

**After every render, verify the injection succeeded:**
```bash
grep -c "Algolia Brand CSS" "$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/index.html"
# Must return ≥ 1. If 0: render failed silently. Do NOT proceed.
```

**The failure mode that created this rule:** DSW SPA was written directly to fix a wrong path. Brand CSS was never injected. `.proof-pill` classes rendered as unstyled plain links. The bug was not caught because STATUS.md accepted "rebuilt" as done without a verification step.
