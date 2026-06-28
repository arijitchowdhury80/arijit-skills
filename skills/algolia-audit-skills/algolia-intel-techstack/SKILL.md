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
  - builtwith: "all 7 endpoints — domain-lookup, relationships, recommendations, financial, social, trust, keywords (SECONDARY search-vendor signal)"
  - similarweb: "get-website-content-technologies-agg (cross-check)"
depends_on_skill:
  - detect-search: "canonical search-vendor oracle — Layer 3 network verdict (primary)"
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

### Layer 3: Live Network Inspection via `detect-search` (MANDATORY — canonical vendor oracle)

This step is non-negotiable. BuiltWith detects installed JS tags, not what is actually firing in production. The only way to confirm the active search vendor is to observe the live network call.

**Do NOT pattern-match network traffic by hand in the LLM.** The canonical, deterministic oracle for "what search vendor is this site actually running" is the **`detect-search` skill** — a Playwright packet-inspection detector (30+ vendor signatures, deep app_id / index / api_key extraction, catches proxied first-party setups, zero-FP per project memory). It returns the vendor verdict deterministically. BuiltWith (Layer 1) is the SECONDARY signal; `detect-search` is primary.

**Procedure (deterministic — two scripts, no LLM pattern-matching):**

```bash
# 1. Run the canonical oracle. Triggers a real search interaction and inspects packets.
node ~/.claude/skills/detect-search/detect-search.js "https://{domain}" \
  --type-query "shoes" > /tmp/ds_{slug}.json

# 2. Map its verdict into the canonical 02-tech-stack.json search-vendor fields.
#    Pass the Layer-1 BuiltWith vendor so agreement/disagreement is recorded.
python3 ~/.claude/skills/algolia-search-audit/scripts/map-detect-search.py \
  --detect /tmp/ds_{slug}.json \
  --builtwith-vendor "{search_vendor_from_layer1_or_empty}"
```

`map-detect-search.py` emits, deterministically, the exact fields below — merge them into `02-tech-stack.json`:
- `search_vendor` — canonical display name (network truth wins over BuiltWith)
- `search_vendor_status` — `ACTIVE` (network-confirmed) | `UNCONFIRMED_WAF_BLOCK` | `UNDETECTED`
- `search_vendor_oracle: "detect-search"`
- `search_vendor_network_confirmed` (bool) and `search_vendor_network_endpoint` (URL or null)
- `search_vendor_details` — app_id, api_key, indexes, agent (where the vendor exposes them)
- `search_vendor_builtwith` + `search_vendor_agreement` — the secondary BuiltWith signal and whether it agrees
- `network_check_date`, `network_check_note`, `algolia_detected`

**If `detect-search` reports `bot_blocked: true` (WAF):**
- The mapper sets `search_vendor_status = "UNCONFIRMED_WAF_BLOCK"` automatically.
- Do NOT skip — a WAF block is itself a finding. Record `network_check_note` ("stealth retry needed in Phase 2").

**Only edge cases go back to the LLM:** if `detect-search` returns `UNDETECTED` but Layer 1/2 strongly suggest a tag (TAG_ONLY shadow deployment), or the two signals disagree (`search_vendor_agreement: false`), the LLM reconciles using the recorded fields — it does NOT invent a vendor.

### Final classification
Combine Layers 1+2+3, with `detect-search` as the authoritative network signal:
- `detect-search` ACTIVE → `search_vendor_status = "ACTIVE"` (network-confirmed; takes precedence over BuiltWith)
- BuiltWith PRESENT + `detect-search` UNDETECTED → `search_vendor_status = "TAG_ONLY"`
- `detect-search` ACTIVE but vendor NOT in BuiltWith → `search_vendor_status = "ACTIVE_UNTAGGED"` (shadow deployment)
- `detect-search` `bot_blocked` → `search_vendor_status = "UNCONFIRMED_WAF_BLOCK"`
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
- `search_vendor_oracle` field present (should be `"detect-search"` when Layer 3 ran)
- `search_vendor_network_confirmed` field present (true/false)
- `search_vendor_network_endpoint` field present (URL string or null)
- `network_check_date` field present
- `ecommerce_platform` is not null
- `tech_stack_summary` string present
