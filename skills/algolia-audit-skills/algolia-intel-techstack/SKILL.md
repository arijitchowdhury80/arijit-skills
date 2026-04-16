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

### Layer 3: Live Network Inspection (MANDATORY — confirms active search API)

This step is non-negotiable. BuiltWith detects installed JS tags, not what is actually firing in production. The only way to confirm the active search vendor is to observe the live network call.

**Procedure:**
1. Use chrome-devtools MCP to open a new browser page
2. Navigate to `https://{domain}`
3. Open the search box and type a generic product query (e.g. "shoes", "party supplies")
4. Capture all network requests: `list_network_requests()`
5. Scan for API calls that match known search vendor signatures:
   - **Algolia:** `*.algolia.net`, `*.algolianet.com`, `application-id.algolia.net/1/indexes`
   - **Elasticsearch:** `/_search`, `/api/search`, `es.{domain}`, port 9200/9243
   - **Coveo:** `*.cloud.coveo.com`, `platform.cloud.coveo.com`
   - **Bloomreach:** `*.bloomreach.com`, `*.brcloud.com`, `/api/v2/search`
   - **Constructor.io:** `*.cnstrc.com`, `ac.cnstrc.com`
   - **Searchspring:** `*.searchspring.net`, `*.searchspring.io`
   - **Lucidworks:** `*.lucidworks.com`
   - **Solr:** `/solr/`, `select?q=`
6. Record the exact endpoint URL, request payload, and response structure
7. Update `02-tech-stack.json`:
   - `search_vendor_network_confirmed`: true/false
   - `search_vendor_network_endpoint`: the exact URL observed (or null)
   - `search_vendor_status`: upgrade to `"ACTIVE"` if network confirms; keep `"TAG_ONLY"` if not observed
   - `network_check_date`: today's date
   - `network_check_note`: what was observed or why it could not be confirmed (WAF block, login-gated, etc.)

**If WAF/bot detection blocks the request:**
- Document the block: `network_check_note: "Blocked by {WAF vendor} — stealth mode required in Phase 2"`
- Do NOT skip — record the block as data. A WAF block is itself a finding.
- Set `search_vendor_status = "UNCONFIRMED_WAF_BLOCK"`

### Final classification
Combine Layers 1+2+3:
- BuiltWith PRESENT + SimilarWeb confirms + Network observed → `search_vendor_status = "ACTIVE"`
- BuiltWith PRESENT + Network NOT observed → `search_vendor_status = "TAG_ONLY"`
- Network observed but NOT in BuiltWith → `search_vendor_status = "ACTIVE_UNTAGGED"` (shadow deployment)
- WAF blocked network check → `search_vendor_status = "UNCONFIRMED_WAF_BLOCK"`
- Nothing found anywhere → `search_vendor_status = "UNDETECTED"`

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
- `search_vendor_status` is one of: ACTIVE | ACTIVE_LAYER1 | ACTIVE_UNTAGGED | TAG_ONLY | REMOVED | UNDETECTED | UNCONFIRMED_WAF_BLOCK
- `search_vendor_network_confirmed` field present (true/false)
- `search_vendor_network_endpoint` field present (URL string or null)
- `network_check_date` field present
- `ecommerce_platform` is not null
- `tech_stack_summary` string present
