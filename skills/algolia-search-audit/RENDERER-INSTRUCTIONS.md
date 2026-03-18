# Algolia Search Audit — Renderer System Instructions
**Version**: 2.0 · **Updated**: 2026-03-17
**Purpose**: Master reference for any Claude session building or running the renderer pipeline.

---

## What This System Does

Claude generates ONE file during an audit: `{company}-audit-data.json`
A renderer script reads that JSON + a static HTML template → produces final HTML.
Chrome headless prints the HTML to PDF.

Claude NEVER writes layout HTML. Claude NEVER generates SVG geometry.
Claude NEVER touches the funnel points, the logo paths, or the page structure.

---

## File Map

```
~/.claude/skills/algolia-search-audit/
├── SKILL.md                              ← Main audit skill (read this first for context)
├── RENDERER-INSTRUCTIONS.md             ← THIS FILE
├── templates/
│   ├── book-template.html               ← Full audit binder (30-36 pages, internal)
│   ├── ae-action-report-template.html   ← 1-page AE action card (internal)
│   ├── strategic-battle-card-template.html  ← Landscape battle card (internal)
│   ├── prospect-leave-behind-template.html  ← 3-page prospect-facing leave-behind
│   ├── components.css                   ← Shared brand CSS (used by binder only)
│   └── audit-data.schema.json           ← JSON data schema (CREATE THIS — see Step 1)
└── scripts/
    ├── render-audit.ts                  ← Deno renderer (CREATE THIS — see Step 2)
    └── generate-pdf.sh                  ← Chrome PDF generator (CREATE THIS — see Step 3)
```

---

## Templates Reference

| Template | Format | Pages | Audience | Internal? | Key Tokens |
|----------|--------|-------|----------|-----------|------------|
| `book-template.html` | PDF | 30-36 | SE, AE | Yes | All tokens |
| `ae-action-report-template.html` | PDF | 1 | AE, BD | Yes | Subset (no full financials) |
| `strategic-battle-card-template.html` | PDF landscape | 1 | AE, SE | Yes | Signals + comparison |
| `prospect-leave-behind-template.html` | PDF | 3 | Prospect | No | Sanitized (no hiring/earnings) |

---

## Step 1: Create audit-data.schema.json

Create `~/.claude/skills/algolia-search-audit/templates/audit-data.schema.json` with the
following structure. This is what Claude outputs during every audit run.

```json
{
  "meta": {
    "company": "string",
    "domain": "string",
    "audit_date": "YYYY-MM-DD",
    "audited_by": "string — AE name",
    "version": "string — e.g. v1",
    "data_vintage": {
      "similarweb": "YYYY-MM-DD",
      "builtwith": "YYYY-MM-DD",
      "yahoo_finance": "YYYY-MM-DD"
    }
  },
  "cover": {
    "photo_url": "string — absolute HTTPS URL to company storefront/HQ photo",
    "company_logo_url": "string — absolute HTTPS URL to company logo PNG/SVG. Try https://logo.clearbit.com/{domain} first.",
    "status_line": "string"
  },
  "score": {
    "overall": "number 0-10 (one decimal)",
    "verdict": "string — e.g. 'Needs Significant Work'",
    "verdict_class": "string — 'critical' | 'moderate' | 'ok'",
    "breakdown": {
      "query_understanding": "number",
      "results_quality": "number",
      "no_results_handling": "number",
      "facets_and_filtering": "number",
      "personalization": "number",
      "performance": "number"
    },
    "critical_count": "number",
    "moderate_count": "number"
  },
  "company_snapshot": {
    "industry": "string",
    "hq": "string",
    "employees": "string",
    "revenue": "string — formatted e.g. '$14.2B'",
    "revenue_source": "string — URL",
    "revenue_source_label": "string — e.g. 'Yahoo Finance'",
    "founded": "string",
    "ticker": "string",
    "current_search_vendor": "string",
    "ecommerce_platform": "string",
    "monthly_visits": "string — formatted e.g. '14.2M'",
    "visits_source": "string — URL"
  },
  "executives": [
    {
      "name": "string",
      "title": "string",
      "quote": "string — exact quote, no paraphrase",
      "quote_source": "string — URL to transcript/10-K/press release",
      "quote_source_label": "string — e.g. 'Q3 2025 Earnings Call'",
      "quote_date": "string — YYYY-MM",
      "relevance": "string — why this quote matters to search strategy"
    }
  ],
  "intelligence_signals": [
    {
      "type": "string — exec | media | funding | industry-risk | industry-opp | competitor | customer | partner | hiring",
      "badge_label": "string — e.g. 'Exec Statement' | 'Media Quote' | 'Funding Event' | 'Industry Risk' | 'Industry Opportunity' | 'Competitor Move' | 'Customer Signal' | 'Partner Signal' | 'Hiring Signal'",
      "text": "string — the signal text or quote",
      "source_name": "string — name/attribution",
      "source_url": "string — URL",
      "source_date": "string — YYYY-MM-DD",
      "relevance": "string — why this creates urgency for Algolia"
    }
  ],
  "competitors": [
    {
      "name": "string",
      "domain": "string",
      "search_vendor": "string",
      "monthly_traffic": "string",
      "traffic_rank": "number",
      "notes": "string"
    }
  ],
  "findings": [
    {
      "id": "string — e.g. 'F01'",
      "title": "string — max 60 chars",
      "severity": "critical | moderate | positive",
      "category": "string — e.g. 'Semantic Search'",
      "tested_query": "string — exact query typed",
      "expected_behavior": "string",
      "actual_behavior": "string",
      "impact_stat": "string — e.g. '0 relevant results'",
      "impact_stat_source": "string — URL (use audit screenshot path or Baymard/Forrester citation)",
      "screenshot_file": "string — relative path e.g. 'screenshots/03-nlp-test.png'",
      "prospect_description": "string — non-technical description for prospect-facing docs",
      "algolia_solution": "string",
      "algolia_case_study_url": "string — URL",
      "algolia_case_study_company": "string",
      "algolia_case_study_result": "string — e.g. '+37% conversion'"
    }
  ],
  "gap_pairs": [
    {
      "said_quote": "string — exec quote about digital/search/CX promise",
      "said_attr": "string — Name, Title",
      "said_source_url": "string — URL",
      "said_source_label": "string",
      "said_date": "string",
      "found_title": "string — 1-line audit finding that contradicts the promise",
      "found_evidence": "string — query tested + screenshot reference"
    }
  ],
  "toc": [
    {
      "act": "string — e.g. 'ACT I: THE VERDICT'",
      "sections": [
        { "title": "string", "anchor": "string — CSS id", "page": "number" }
      ]
    }
  ],
  "financials": {
    "ticker": "string",
    "market_cap": "string",
    "revenue_3y": [{ "year": "string", "revenue": "string" }],
    "total_digital_revenue": "string — formatted e.g. '$14.2B'",
    "ecommerce_revenue_est": "string — formatted e.g. '$4.2B'",
    "search_roi_est": "string — formatted e.g. '$210M/yr'",
    "search_addressable": "string — formatted, 15% of digital",
    "conservative_lift_label": "string — formatted, 5% of addressable",
    "revenue_source": "string — URL",
    "revenue_source_label": "string"
  },
  "traffic": {
    "monthly_visits": "string",
    "visit_duration": "string",
    "bounce_rate": "string",
    "pages_per_visit": "string",
    "top_channels": [{ "channel": "string", "share": "string" }],
    "source_url": "string"
  },
  "tech_stack": {
    "ecommerce_platform": "string",
    "cms": "string",
    "search_provider": "string",
    "personalization": "string",
    "analytics": "string",
    "tag_manager": "string",
    "tech_stack_summary": "string — short e.g. 'Salesforce Commerce / Lucidworks / Adobe Analytics'",
    "source_url": "string"
  },
  "ae_fields": {
    "ae_name": "string",
    "ae_email": "string",
    "next_step_action": "string — specific single action",
    "next_step_owner": "string",
    "next_step_date": "string",
    "urgency_level": "string — 'high' | 'medium' | 'low'",
    "urgency_label": "string — e.g. 'High Urgency'",
    "urgency_color": "string — hex color",
    "talk_track_opener": "string — opening line for the call",
    "talk_track_cta": "string — closing ask"
  },
  "next_steps": [
    {
      "step_num": "number",
      "title": "string",
      "description": "string"
    }
  ],
  "methodology": "string — 1 paragraph describing audit method",
  "bibliography": [
    { "n": "number", "label": "string", "url": "string", "accessed": "string" }
  ]
}
```

---

## Step 2: Create render-audit.ts

Create `~/.claude/skills/algolia-search-audit/scripts/render-audit.ts`

This Deno script:
1. Reads `{company-slug}-audit-data.json` from cwd
2. Reads the appropriate template from `~/.claude/skills/algolia-search-audit/templates/`
3. Replaces ALL `{{TOKEN}}` placeholders with values from JSON
4. Generates dynamic HTML for findings, signals, gap pairs, TOC, score bars
5. Warns if any `{{TOKEN}}` remains unreplaced
6. Writes the output HTML to cwd

### Usage
```bash
# Full binder
deno run --allow-read --allow-write render-audit.ts {company-slug} binder

# AE action report
deno run --allow-read --allow-write render-audit.ts {company-slug} ae-report

# Battle card
deno run --allow-read --allow-write render-audit.ts {company-slug} battle-card

# Prospect leave-behind
deno run --allow-read --allow-write render-audit.ts {company-slug} leave-behind
```

### Token map (applies to all templates)

All `{{TOKEN}}` names and their JSON paths:

| Token | JSON Path |
|-------|-----------|
| `{{ALGOLIA_LOGO_BLUE}}` | Hardcoded base64 in renderer — see Logo section below |
| `{{ALGOLIA_LOGO_WHITE}}` | Hardcoded base64 in renderer — see Logo section below |
| `{{COMPANY_NAME}}` | `meta.company` |
| `{{DOMAIN}}` | `meta.domain` |
| `{{AUDIT_DATE}}` | `meta.audit_date` |
| `{{AUDITED_BY}}` | `meta.audited_by` |
| `{{DATA_VINTAGE_NOTE}}` | Built from `meta.data_vintage` fields |
| `{{COVER_PHOTO_URL}}` | `cover.photo_url` · Fallback: Unsplash generic city photo URL |
| `{{COMPANY_LOGO_URL}}` | `cover.company_logo_url` · Fallback: `https://logo.clearbit.com/{domain}` |
| `{{OVERALL_SCORE}}` | `score.overall` |
| `{{SCORE_VERDICT}}` | `score.verdict` |
| `{{SCORE_VERDICT_CLASS}}` | `score.verdict_class` |
| `{{CRITICAL_COUNT}}` | `score.critical_count` |
| `{{MODERATE_COUNT}}` | `score.moderate_count` |
| `{{FINDINGS_COUNT}}` | `findings.length` |
| `{{INDUSTRY}}` | `company_snapshot.industry` |
| `{{HQ}}` | `company_snapshot.hq` |
| `{{EMPLOYEES}}` | `company_snapshot.employees` |
| `{{REVENUE}}` | `company_snapshot.revenue` |
| `{{REVENUE_SOURCE}}` | `company_snapshot.revenue_source` |
| `{{REVENUE_SOURCE_LABEL}}` | `company_snapshot.revenue_source_label` |
| `{{FOUNDED}}` | `company_snapshot.founded` |
| `{{TICKER}}` | `company_snapshot.ticker` |
| `{{SEARCH_VENDOR}}` | `company_snapshot.current_search_vendor` |
| `{{ECOMMERCE_PLATFORM}}` | `company_snapshot.ecommerce_platform` or `tech_stack.ecommerce_platform` |
| `{{MONTHLY_VISITS}}` | `company_snapshot.monthly_visits` |
| `{{VISITS_SOURCE}}` | `company_snapshot.visits_source` |
| `{{SW_VINTAGE}}` | `meta.data_vintage.similarweb` |
| `{{TECH_STACK_SUMMARY}}` | `tech_stack.tech_stack_summary` |
| `{{TOTAL_DIGITAL_REVENUE}}` | `financials.total_digital_revenue` |
| `{{SEARCH_ADDRESSABLE}}` | `financials.search_addressable` |
| `{{CONSERVATIVE_LIFT_LABEL}}` | `financials.conservative_lift_label` |
| `{{SEARCH_ROI}}` | `financials.search_roi_est` |
| `{{URGENCY_LEVEL}}` | `ae_fields.urgency_level` |
| `{{URGENCY_LABEL}}` | `ae_fields.urgency_label` |
| `{{URGENCY_COLOR}}` | `ae_fields.urgency_color` |
| `{{NEXT_STEP_ACTION}}` | `ae_fields.next_step_action` |
| `{{NEXT_STEP_OWNER}}` | `ae_fields.next_step_owner` |
| `{{NEXT_STEP_DATE}}` | `ae_fields.next_step_date` |
| `{{TALK_TRACK_OPENER}}` | `ae_fields.talk_track_opener` |
| `{{TALK_TRACK_CTA}}` | `ae_fields.talk_track_cta` |
| `{{AE_NAME}}` | `ae_fields.ae_name` |
| `{{AE_EMAIL}}` | `ae_fields.ae_email` |
| `{{TEST_QUERY_COUNT}}` | `findings.length` (or explicit field) |
| `{{CASE_STUDY_COMPANY}}` | Derived from best-matching finding's case study |
| `{{CASE_STUDY_URL}}` | From best-matching finding |
| `{{CASE_STUDY_RESULT_STAT}}` | From best-matching finding |

### Dynamic HTML blocks — renderer must generate these

**`{{TOC_CONTENT}}`** — Generated from `data.toc` array:
```html
<div class="toc__act">
  <div class="toc__act-title">ACT I: THE VERDICT</div>
  <div class="toc__entry"><a href="#ch-bottom-line">The Bottom Line</a><span class="toc__page">3</span></div>
  ...
</div>
```

**`{{FINDING_CARDS}}`** (ae-report) / **`{{FINDINGS_SECTIONS}}`** (binder) / **`{{PROSPECT_FINDING_CARDS}}`** (leave-behind):
Generated from `data.findings` array. See each template for the exact HTML structure in the embedded comments.
- Binder: Full TEF layout with screenshot image, impact stat, solution, case study link
- AE report: Compact card with stat + conversation starter
- Leave-behind: Text-only card, NO screenshots, NO internal intel

**`{{INTELLIGENCE_SIGNALS}}`** (battle card) / **`{{SIGNAL_CARDS}}`** (ae-report):
Generated from `data.intelligence_signals` array. Signal type → CSS class mapping:

| JSON type | CSS class |
|-----------|-----------|
| `exec` | `signal--exec` |
| `media` | `signal--media` |
| `funding` | `signal--funding` |
| `industry-risk` | `signal--industry-risk` |
| `industry-opp` | `signal--industry-opp` |
| `competitor` | `signal--competitor` |
| `customer` | `signal--customer` |
| `partner` | `signal--partner` |
| `hiring` | `signal--hiring` |

**`{{GAP_PAIRS}}`** — Generated from `data.gap_pairs`. Each pair = 1 `.gap-pair` block.

**`{{SCORE_BARS}}`** / **`{{SCORE_HEATMAP}}`** — Generated from `data.score.breakdown`.
Bar width = `(score / 10 * 100)%`. Color class: critical = score < 4, moderate = 4–6, ok = > 6.

**`{{FEATURE_COMPARISON_ROWS}}`** — Generated from findings where a specific capability was tested.

**`{{SCORE_BARS}}`** (leave-behind) — One row per `score.breakdown` field.

### Logo handling

The renderer must embed Algolia logos as base64 data URIs so the HTML is fully self-contained.

Fetch the Algolia SVG logos once and hardcode them in the renderer:

```typescript
// Minimal Algolia wordmark SVGs (use these until official assets are available)
const ALGOLIA_BLUE_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 32">
  <text x="0" y="25" font-family="'Source Sans Pro','Helvetica Neue',Helvetica,sans-serif"
    font-size="27" font-weight="900" fill="#003DFF" letter-spacing="-0.5">algolia</text>
</svg>`;

const ALGOLIA_WHITE_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 32">
  <text x="0" y="25" font-family="'Source Sans Pro','Helvetica Neue',Helvetica,sans-serif"
    font-size="27" font-weight="900" fill="#FFFFFF" letter-spacing="-0.5">algolia</text>
</svg>`;

// Base64 encode
const b64Blue  = btoa(ALGOLIA_BLUE_SVG);
const b64White = btoa(ALGOLIA_WHITE_SVG);

tokens["ALGOLIA_LOGO_BLUE"]  = `data:image/svg+xml;base64,${b64Blue}`;
tokens["ALGOLIA_LOGO_WHITE"] = `data:image/svg+xml;base64,${b64White}`;
```

IMPORTANT: If you can WebFetch the real Algolia logo SVG, use that instead. The above is a fallback.

### Unreplaced token check

After all replacements, scan for any remaining `{{...}}` patterns:
```typescript
const unreplaced = html.match(/\{\{[A-Z_]+\}\}/g);
if (unreplaced) {
  const unique = [...new Set(unreplaced)];
  console.warn(`⚠ ${unique.length} unreplaced tokens: ${unique.join(", ")}`);
  // Do NOT write the file if critical tokens are unreplaced
  // Critical tokens: COMPANY_NAME, OVERALL_SCORE, FINDINGS_SECTIONS
}
```

---

## Step 3: Create generate-pdf.sh

Create `~/.claude/skills/algolia-search-audit/scripts/generate-pdf.sh`

```bash
#!/bin/bash
# Usage: ./generate-pdf.sh <company-slug> <template>
# template: binder | ae-report | battle-card | leave-behind
# Example: ./generate-pdf.sh costco binder
# Requires: Google Chrome installed

SLUG="$1"
TEMPLATE="${2:-binder}"
PORT=8766

case "$TEMPLATE" in
  binder)       HTML="${SLUG}-book.html";         PDF="${SLUG}-book.pdf" ;;
  ae-report)    HTML="${SLUG}-ae-report.html";     PDF="${SLUG}-ae-report.pdf" ;;
  battle-card)  HTML="${SLUG}-battle-card.html";   PDF="${SLUG}-battle-card.pdf" ;;
  leave-behind) HTML="${SLUG}-leave-behind.html";  PDF="${SLUG}-leave-behind.pdf" ;;
  *) echo "Unknown template: $TEMPLATE"; exit 1 ;;
esac

if [ ! -f "$HTML" ]; then
  echo "ERROR: $HTML not found. Run render-audit.ts first."
  exit 1
fi

CHROME=$(which "Google Chrome" 2>/dev/null || \
         which google-chrome 2>/dev/null || \
         which chromium 2>/dev/null || \
         echo "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

python3 -m http.server $PORT --directory "$(pwd)" &
SERVER_PID=$!
sleep 1

# Battle card uses landscape
if [ "$TEMPLATE" = "battle-card" ]; then
  PAPER="--print-to-pdf-paper-width=11 --print-to-pdf-paper-height=8.5"
else
  PAPER=""
fi

"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-sandbox \
  --print-to-pdf="$(pwd)/$PDF" \
  --no-pdf-header-footer \
  --run-all-compositor-stages-before-draw \
  --virtual-time-budget=8000 \
  $PAPER \
  "http://localhost:$PORT/$HTML"

kill $SERVER_PID 2>/dev/null

if [ -f "$PDF" ]; then
  SIZE=$(du -h "$PDF" | cut -f1)
  echo "✓ $PDF ($SIZE)"
else
  echo "ERROR: PDF generation failed for $TEMPLATE"
  exit 1
fi
```

Make executable: `chmod +x generate-pdf.sh`

---

## How Claude populates audit-data.json during an audit run

### Rules Claude MUST follow when writing the JSON

1. **cover.photo_url** — Must be an absolute HTTPS URL to a real company storefront/HQ photo.
   Search: `{company} storefront exterior OR headquarters photo site:wikimedia.org OR site:commons.wikimedia.org`
   Never use a file:// path. Never use a relative path.

2. **cover.company_logo_url** — Try `https://logo.clearbit.com/{domain}` first.
   WebFetch it to confirm it returns an image (not 404). If 404, WebSearch for official logo URL.

3. **Every finding MUST have**:
   - `screenshot_file` — relative path to existing file in `screenshots/`
   - `impact_stat_source` — URL to source of the impact number
   - `algolia_case_study_url` — URL to relevant case study on algolia.com/customers
   - `tested_query` — exact query string typed during audit
   - `algolia_case_study_result` — specific metric e.g. "+37% conversion"

4. **Every executive in `executives[]` MUST have**:
   - `quote_source` — direct URL to transcript, 10-K, press release, or video
   - `quote_date` — YYYY-MM format
   - The quote must be exact, not paraphrased

5. **Every intelligence_signal MUST have**:
   - `source_url` — URL to the original source
   - `source_date` — YYYY-MM-DD
   - `relevance` — specific connection to why this matters for Algolia

6. **meta.data_vintage** — Must contain actual dates from API responses, not today's date.
   Check SimilarWeb response metadata for `last_updated` or similar field.

7. **financials.search_roi_est** — Calculate as: `ecommerce_revenue * 0.15 * 0.05`
   Where `ecommerce_revenue` = `total_digital_revenue * [ecom share if known, else 0.30]`

8. **DO NOT fabricate** any URL, quote, statistic, or case study result.
   If a field cannot be verified, set it to `null` — do not guess.

---

## Quality gates before declaring done

After running render-audit.ts, verify:

```bash
# 1. No unreplaced tokens
grep -o '{{[A-Z_]*}}' {company}-book.html | sort | uniq
# Expected: empty output

# 2. Binder PDF size check
ls -lh {company}-book.pdf
# Expected: > 2MB for a full binder with screenshots

# 3. AE report PDF size check
ls -lh {company}-ae-report.pdf
# Expected: 200KB - 1MB (1 page)

# 4. All screenshot references exist on disk
grep -o 'screenshots/[^"]*' {company}-audit-data.json | while read f; do
  [ -f "$f" ] || echo "MISSING: $f"
done
# Expected: no output

# 5. Cover photo URL accessible
# Run WebFetch on cover.photo_url — should return HTTP 200 with image content-type

# 6. Company logo URL accessible
# Run WebFetch on cover.company_logo_url — should return HTTP 200 with image content-type
```

---

## Remaining template work (NOT YET BUILT — needs separate session)

These templates still need to be created following the same JSON → renderer → HTML → PDF pattern:

| Template | Priority | Notes |
|----------|----------|-------|
| `se-technical-brief-template.html` | High | 2-3pp. Architecture fit, integration complexity per finding, tech stack diagram. |
| `roi-one-pager-template.html` | High | 1pp. CFO-facing. Revenue → search-addressable → lift math. Clean, minimal. |
| `strategic-signal-brief-template.html` | Medium | 1pp dense. Signal density > narrative. Downstream LLM-ready format. |
| `champion-enablement-template.html` | Medium | 2pp. Non-technical language. Budget framing, stakeholder map, sample VP email. |
| `outreach-email-template.html` | Medium | Subject line + 3-para body. Built from top finding + exec quote + competitor signal. |
| `battle-card-internal-deck.md` | Low | Marp deck version of battle card for screen presentations. |
| `executive-microsite/` | Low (SaaS) | React component. Interactive, trackable link. The SaaS MVP starting point. |

---

## Adding a new template — checklist

1. Create `{name}-template.html` in `templates/`
2. Use only `{{TOKEN}}` placeholders from the token map above — no new tokens unless added to schema
3. All logos via `{{ALGOLIA_LOGO_BLUE}}` / `{{ALGOLIA_LOGO_WHITE}}` — no external file refs
4. All SVG geometry frozen — never let Claude regenerate SVG points
5. All prospect-facing templates: strip internal signals (no hiring, no earnings quotes, no competitor intel)
6. Add a `{{DISCLAIMER}}` slot to all prospect-facing templates
7. Register the template in `render-audit.ts` case statement
8. Register the template in `generate-pdf.sh` case statement
9. Add an entry to the template table in this file

---

## The ABX platform vision

This renderer system is the foundation of a future SaaS ABX platform.
Each template = a software module. Each JSON field = a database column.
The migration path:

```
Phase 1 (now):   Claude Code skill + Deno renderer + Chrome PDF
Phase 2 (next):  Shared MCP proxy server (BuiltWith, SimilarWeb keys centralized)
Phase 3 (later): React + Supabase SaaS — same JSON schema, React renderer replaces Deno
Phase 4 (later): Executive microsite as shareable URL, audit history DB, Okta SSO
```

The JSON schema defined here IS the data model for the future database.
Every field added to the schema should be designed as if it will become a DB column.

See `tasks.md` in the working directory for the full implementation roadmap.
