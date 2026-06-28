---
name: algolia-intel-company
description: Layer 1A company context module. Collects company overview, vertical classification, executive team, and key URLs for an Algolia Search Audit prospect. Run first — all downstream modules read from this output. Produces 01-company-context.md and 01-company-context.json. Invoke when starting any new audit or when company context is missing from the workspace.
layer: 1-intelligence
module_id: 1A
script: collect-company.py
reads_from:
  - none
writes_to:
  - 01-company-context.md
  - 01-company-context.json
mcp_required:
  - builtwith: "keywords-api for SEO meta"
  - websearch: "executives, HQ, founding, vertical"
skill_enrichment: true
version: 1.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md` before any action.

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1 — no dependencies)
- **Module ID:** 1A
- **Model tier:** data_enrichment (claude-haiku-4-5 per platform.config.json)
- **Reads from:** nothing — this is always the first module
- **Writes to:** `01-company-context.md` + `01-company-context.json`
- **Script:** `collect-company.py` (handles BuiltWith API + website WebFetch)

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-company.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  --company-name "{CompanyName}" \
  [--ticker TICKER if known]
```

Capture stdout JSON. If `status == "failed"` → alert user and stop.

---

## Step 2: Scout Direct-Fetch Enrichment (PRIMARY — runs before WebSearch)

The script already invokes `scout_company.py` automatically (Step 4 in `collect-company.py`), which scrapes:
- `/about` or `/about-us` → `description`, `linkedin_url`, `twitter_handle`
- `/leadership`, `/about/leadership`, `/about/team`, etc. → `executives[]` (name + title)
- `/careers`, `/jobs`, etc. → `careers_url`
- `/investors`, `/ir` → `ir_url` + PDF links

Check `scout_data` in the JSON output. For each field Scout successfully populated, label it:
`[FACT — Scout scrape {url}, {date}]`

**Only proceed to WebSearch (Step 2b) for fields Scout could not fill.**

### Scout degradation check (F1 — MANDATORY, do not skip)

Scout's markdown conversion returns EMPTY (~1–4 chars) on Squarespace / JS bio-card CMSes
even when it fetched the page fine. The script now **detects this and falls back to parsing
`raw_html`** instead of silently returning nothing. When that happens it is LOUD:

- Stderr shows `⚠⚠ Scout markdown DEGRADED on [pages] — raw_html fallback used (F1)`.
- `01-company-context.json` carries `scout_degraded: true`, `scout_collection_method:
  "scout_raw_html_fallback"`, and `scout_degraded_sources: [...]`.
- Every field recovered from the raw_html fallback is labeled
  `[OBSERVED — Scout raw_html fallback (markdown degraded), {date}]`, **not** `[FACT]`.

If `scout_degraded == true`:
1. Treat the affected fields (description, executives, social) as `[OBSERVED]`-grade, not `[FACT]`.
2. **Re-verify them in Step 2b via WebFetch/WebSearch** — the raw_html parse is best-effort,
   not authoritative. Prefer a clean WebFetch table of executives over the raw_html heuristic
   when both exist (per F-scout-ab-evidence.md, WebFetch wins on Squarespace leadership pages).
3. Keep the `scout_degraded` flag in the final JSON — never drop it. Downstream factcheck reads it.

## Step 2b: WebSearch Fallback Enrichment

For any field still null after Scout, use WebSearch:

### hq, founded, employee_count, public_private
- Tool: WebSearch
- Query: `"{CompanyName}" headquarters founded employees public OR private`
- Label: `[FACT — source URL, date]` if confirmed | `[ESTIMATE — source, date]` if inferred

### vertical, business_model
- Tool: WebSearch + classify from description
- Query: `"{CompanyName}" ecommerce retail vertical industry`
- Label: `[FACT — company website, date]`

### twitter_handle (if Scout returned null)
- Tool: WebSearch
- Query: `"{CompanyName}" Twitter OR X.com official account`
- Label: `[FACT — Twitter/X, date]` if confirmed

### executives (if Scout returned empty or incomplete list)
- Tool: WebSearch
- Query: `"{CompanyName}" CEO CTO CDO "VP Digital" "VP Commerce" executives 2025 2026`
- For each named executive: confirm name + title + LinkedIn URL
- Label: `[FACT — source URL, date]`
- RULE: Named sources only. No "a spokesperson said."

### ir_url (public companies only, if Scout returned null)
- Tool: WebSearch
- Query: `"{CompanyName}" investor relations IR page`
- Label: `[FACT — direct URL, date]`

After enrichment: update BOTH `01-company-context.md` AND `01-company-context.json` with all filled fields.
Set `meta.skill_enrichment_completed = true` in the JSON.

---

## Step 3: Portfolio / Sub-brand Detection

This is an LLM-only step — no Python script. Uses Tavily search + WebFetch to identify parent entities and sibling brands.

### 3a. Tavily Search
Run a Tavily search with `search_depth="advanced"` and `include_raw_content=True`:
- Query 1: `"{CompanyName}" brands portfolio subsidiary owned by`
- Query 2: `"{ParentEntity}" brands` (if a parent entity was mentioned in Step 2 enrichment)

### 3b. WebFetch Direct Pages
Attempt to fetch these URLs (in order, stop on first 200):
1. `https://{domain}/brands`
2. `https://{domain}/about/brands`
3. `https://{domain}/our-brands`

### 3c. Extract and Classify

From the Tavily results and WebFetch content, extract:

**`parent_entity`** — Name of the holding company if the audit domain is owned by a larger entity.
- Example: DSW → `"Designer Brands Inc."`. Coach → `null` (Tapestry IS the holding entity being pitched).
- Set to `null` if no parent entity exists.

**`parent_entity_source`** — URL where parent entity ownership is confirmed.

**`parent_entity_label`** — `[FACT — {source_domain} via Tavily, {date}]` or `null`.

**`is_conglomerate`** — Boolean:
- `true` = the company being audited IS the holding entity (e.g., Tapestry is pitched directly as the conglomerate owning Coach/Kate Spade/Stuart Weitzman)
- `false` = the audit domain is an operating brand, even if a parent entity exists (DSW = `false`; Designer Brands owns DSW but DSW.com is what we're pitching)
- Single-brand independent companies = `false`

**`portfolio_brands[]`** — Array of brands in the portfolio:
- For conglomerates (`is_conglomerate: true`): list all owned operating brands
- For operating brands with a parent (`is_conglomerate: false`): list sibling brands under the same parent entity
- For single-brand companies with no parent: set to `[]`
- Each entry: `{ "name": string, "domain": string, "is_audit_target": boolean, "source": "[FACT — URL via Tavily, date]" }`
- Set `is_audit_target: true` ONLY for the brand whose domain matches the audit domain
- Minimum domain confidence: must be a real domain (.com/.net/.co.uk etc.), not a guess

**`primary_market`** — Derive from HQ location if not already present:
- `"US"` | `"UK"` | `"EU"` | `"CA"` | `"AU"` | `null`

### 3d. Write to JSON

Add these fields to `01-company-context.json`:
```json
"primary_market": "US",
"parent_entity": "Designer Brands Inc.",
"parent_entity_source": "https://www.designerbrands.com/",
"parent_entity_label": "[FACT — designerbrands.com via Tavily, 2026-03-23]",
"is_conglomerate": false,
"portfolio_brands": [
  {
    "name": "DSW",
    "domain": "dsw.com",
    "is_audit_target": true,
    "source": "[FACT — designerbrands.com/brands via Tavily, 2026-03-23]"
  },
  {
    "name": "Vince Camuto",
    "domain": "vincecamuto.com",
    "is_audit_target": false,
    "source": "[FACT — designerbrands.com/brands via Tavily, 2026-03-23]"
  }
]
```

For a single-brand company with no parent:
```json
"primary_market": "US",
"parent_entity": null,
"parent_entity_source": null,
"parent_entity_label": null,
"is_conglomerate": false,
"portfolio_brands": []
```

Update `01-company-context.md` with a "Parent & Portfolio" section summarising findings.

### 3e. Verification Gate Addition

After Step 3, re-verify `01-company-context.json` contains:
- `portfolio_brands` key present (value may be `[]` for single-brand companies)
- `is_conglomerate` is non-null boolean
- `primary_market` is non-null
- If `portfolio_brands` has entries: at least one entry has `is_audit_target: true`

---

## Verification Gate

```bash
ls -la "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/01-company-context.md"
ls -la "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/01-company-context.json"
```

Pass criteria:
- Both files exist
- `01-company-context.md` ≥ 1500 bytes
- `01-company-context.json` is valid JSON with `meta.skill_enrichment_completed = true`
- `company_name`, `domain`, `vertical` are not null in JSON
- At least 1 executive with name + title present

Gate PASS → proceed. Gate FAIL → alert: "Module 1A incomplete. Required before any other module."
