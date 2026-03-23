---
name: algolia-intel-hiring
description: Layer 1H hiring signals module. Identifies ICP-relevant open roles using LinkedIn Jobs (Apify), careers page WebFetch, and Indeed. Classifies by tier (Economic Buyer, Technical Buyer, Champion) and flags vacancy signals. Produces 09d-hiring-signals.md and 09d-hiring-signals.json. Run in Wave 1 after company context is available.
layer: 1-intelligence
module_id: 1H
script: collect-hiring.py
reads_from:
  - 01-company-context.json
writes_to:
  - 09d-hiring-signals.md
  - 09d-hiring-signals.json
mcp_required:
  - apify: "curious_coder/linkedin-jobs-scraper"
skill_enrichment: false
version: 1.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1H
- **Model tier:** programmatic
- **Reads from:** `01-company-context.json` (company_name, linkedin_url, domain)

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-hiring.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  --company-name "{CompanyName}"
```

If Apify MCP unavailable: script uses WebSearch fallback. Data labeled `[WEBSEARCH]` not `[FACT]`.

Script reads `01-company-context.json` automatically from output_dir.

---

## No Skill Enrichment Required

Fully programmatic. ICP classification (Tiers 1-4) and vacancy signal detection are deterministic.

---

## Verification Gate

Ensure `09d-hiring-signals.json` has `meta` block (use `meta`, NOT `meta`):
```json
{"meta": {"skill_enrichment_completed": true}, "tier_summary": {"tier1": N, "tier2": N, "tier3": N, "tier4": N}, "buying_committee": {"economic_buyer": "...", "technical_buyer": "..."}}
```

Pass: `09d-hiring-signals.md` ≥2000 bytes (NOT `07-hiring-signals.md`), `tier_summary` has all 4 tiers (tier1-tier4), `buying_committee` has `economic_buyer` and `technical_buyer` fields, `meta.skill_enrichment_completed = true`.
