---
name: algolia-intel-techstack
description: Layer 1B tech stack detection module. Identifies the current search vendor, ecommerce platform, analytics stack, CDN/WAF, and removed technologies using BuiltWith MCP (all 7 endpoints). Produces 02-tech-stack.md and 02-tech-stack.json. Critical: determines whether this is a displacement, existing customer expansion, or greenfield audit. Run in Wave 1 alongside other independent modules.
layer: 1-intelligence
module_id: 1B
script: collect-techstack.py
reads_from:
  - 01-company-context.json
writes_to:
  - 02-tech-stack.md
  - 02-tech-stack.json
mcp_required:
  - builtwith: "all 7 endpoints — domain-lookup, relationships, recommendations, financial, social, trust, keywords"
  - similarweb: "get-website-content-technologies-agg (cross-check)"
skill_enrichment: true
version: 1.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md` before any action.

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1B
- **Model tier:** programmatic (collect-techstack.py handles all BuiltWith calls)
- **Reads from:** `01-company-context.json` (domain)
- **Writes to:** `02-tech-stack.md` + `02-tech-stack.json`

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-techstack.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/"
```

The script calls all 7 BuiltWith endpoints. BuiltWith response can be 190KB+ — the script uses `parse-builtwith.js` to filter before writing. Capture stdout JSON.

---

## Step 2: Skill Enrichment — Search Vendor Classification

This is the critical enrichment step. Search vendor detection uses TWO mandatory layers:

### Layer 1: BuiltWith detection (from script output)
Read `search_vendor` and `search_vendor_status` from `02-tech-stack.json`.
- `TAG_ONLY` = JS tag present but may not be active in production
- `ACTIVE` = confirmed via Layer 2 (see below)
- `REMOVED` = previously detected, no longer present

### Layer 2: SimilarWeb technology cross-check
- MCP call: `get-website-content-technologies-agg(domain="{domain}")`
- Cross-reference with BuiltWith results
- Note any discrepancies

### Final classification
Combine Layers 1+2:
- If BuiltWith says PRESENT + SimilarWeb confirms → `search_vendor_status = "ACTIVE_LAYER1"`
- If only BuiltWith → `search_vendor_status = "TAG_ONLY"`
- Layer 2 network confirmation (ACTIVE) happens in algolia-audit-browser Step 2a

### Existing customer handling
If `search_vendor == "Algolia"`:
- **DO NOT ABORT** — mark `algolia_detected = true` and continue
- Note: could be expansion opportunity (other brands, other use cases)
- Continue collecting all tech stack data

Update `02-tech-stack.json` with the final classification. Set `meta.skill_enrichment_completed = true`.

---

## Verification Gate

Pass criteria:
- Both files exist and `02-tech-stack.md` ≥ 2000 bytes
- `search_vendor` field is not null (can be "none-detected")
- `search_vendor_status` is one of: ACTIVE_LAYER1 | TAG_ONLY | REMOVED | UNDETECTED
- `ecommerce_platform` is not null
- `tech_stack_summary` string present
