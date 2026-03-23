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

## Step 2: Skill Enrichment

The script marks these fields as `[COLLECT_VIA_SKILL]`. Fill each using the tool specified:

### hq, founded, employee_count, public_private
- Tool: WebSearch
- Query: `"{CompanyName}" headquarters founded employees public OR private`
- Label: `[FACT — source URL, date]` if confirmed | `[ESTIMATE — source, date]` if inferred

### vertical, business_model
- Tool: WebSearch + classify from description
- Query: `"{CompanyName}" ecommerce retail vertical industry`
- Label: `[FACT — company website, date]`

### twitter_handle
- Tool: WebSearch
- Query: `"{CompanyName}" Twitter OR X.com official account`
- Label: `[FACT — Twitter/X, date]` if confirmed

### executives
- Tool: WebSearch
- Query: `"{CompanyName}" CEO CTO CDO "VP Digital" "VP Commerce" executives 2025 2026`
- For each named executive: confirm name + title + LinkedIn URL
- Label: `[FACT — source URL, date]`
- RULE: Named sources only. No "a spokesperson said."

### ir_url (public companies only)
- Tool: WebSearch
- Query: `"{CompanyName}" investor relations IR page`
- Label: `[FACT — direct URL, date]`

After enrichment: update BOTH `01-company-context.md` AND `01-company-context.json` with all filled fields.
Set `meta.skill_enrichment_completed = true` in the JSON.

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
