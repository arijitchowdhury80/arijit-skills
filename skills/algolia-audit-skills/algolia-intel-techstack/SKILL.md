---
name: algolia-intel-techstack
description: Layer 1B tech stack detection module. Identifies the current search vendor, ecommerce platform, analytics, tag manager, CDN/WAF, personalization, payment, frontend framework and hosting via detect-search --full-tech (keyless multi-page network packet inspection) with optional SimilarWeb cross-check. Produces 02-tech-stack.md and 02-tech-stack.json. Critical: determines whether this is a displacement, existing customer expansion, or greenfield audit. Run in Wave 1 alongside other independent modules.
layer: 1-intelligence
module_id: 1B
script: collect-techstack.py
reads_from:
  - 01-company-context.json
writes_to:
  - 02-tech-stack.md
  - 02-tech-stack.json
data_sources:
  - detect-search: "detect-search.js --full-tech multi-page network fingerprint (keyless, primary)"
  - similarweb_api: "OPTIONAL REST cross-check — api.similarweb.com /content/technologies (SIMILARWEB_API_KEY); not an MCP; skipped gracefully if unset"
depends_on_skill:
  - detect-search: "canonical search-vendor oracle — Layer 3 network verdict (primary)"
skill_enrichment: true
version: 2.0.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md` before any action.

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1B
- **Model tier:** programmatic (collect-techstack.py)
- **Reads from:** `01-company-context.json` (domain)
- **Writes to:** `02-tech-stack.md` + `02-tech-stack.json`

---

## Step 1: Run Script (does the full network fingerprint itself)

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-techstack.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/"
```

This is now the WHOLE tech-stack detection — no separate manual detect-search call needed.
The script invokes `detect-search.js --full-tech` (live **multi-page** network fingerprint:
home → category(PLP) → product(PDP) → search-results → cart) and runs it through
`map-detect-tech.py`, writing the COMPLETE **`02-tech-stack.json`** + `02-tech-stack.md`:
search vendor + ecommerce platform + analytics + tag-manager + CDN/WAF + personalization +
payment + CDP + frontend framework + hosting, each with **confidence** (`confirmed` /
`likely` / `likely-opendb`) + evidence + the pages it was seen on. Keyless. SimilarWeb is an
optional cross-check only (if `SIMILARWEB_API_KEY` is set).

Capture stdout JSON (summary: `tech_count`, `search_vendors`, `algolia_detected`, `pages_visited`).
The `02-tech-stack.json` is already complete — Step 2 below is interpretation, not re-collection.

No fabrication. Client-side only (backend tech invisible — same as BuiltWith). No historical/
"removed tech" — a live load sees only the current state.

---

## Step 2: Skill Enrichment — Search Vendor Classification

This is the critical enrichment step. Search vendor detection uses TWO mandatory layers:

### Layer 1: SimilarWeb technology cross-check (OPTIONAL — the pipeline is keyless without it)
- REST API: `api.similarweb.com/v1/website/{domain}/content/technologies` (`SIMILARWEB_API_KEY`); skipped gracefully if unset. Not an MCP.
- Records ecommerce platform, analytics, CDN/WAF, and any detected search vendor tags
- A tag detected here = `TAG_ONLY` (may not be active in production — Layer 2 is the truth)

### Layer 2: Live Network Inspection via `detect-search` (MANDATORY — canonical vendor oracle)

This step is non-negotiable. The only way to confirm the active search vendor is to observe the live network call. Passive tag detection does not reflect what is actually firing in production.

**Do NOT pattern-match network traffic by hand in the LLM.** The canonical, deterministic oracle for "what search vendor is this site actually running" is the **`detect-search` skill** — a Playwright packet-inspection detector (30+ vendor signatures, deep app_id / index / api_key extraction, catches proxied first-party setups, zero-FP per project memory). It returns the vendor verdict deterministically.

**Procedure (deterministic — two scripts, no LLM pattern-matching):**

```bash
# 1. Run the canonical oracle. Triggers a real search interaction and inspects packets.
node ~/.claude/skills/detect-search/detect-search.js "https://{domain}" \
  --type-query "shoes" > /tmp/ds_{slug}.json

# 2. Map its verdict into the canonical 02-tech-stack.json search-vendor fields.
python3 ~/.claude/skills/algolia-search-audit/scripts/map-detect-search.py \
  --detect /tmp/ds_{slug}.json \
  --builtwith-vendor ""
```

Note: `--builtwith-vendor ""` passes an empty string since BuiltWith is not in the pipeline. The `search_vendor_builtwith` and `search_vendor_agreement` output fields will be empty/false; this is correct.

`map-detect-search.py` emits, deterministically, the exact fields below — merge them into `02-tech-stack.json`:
- `search_vendor` — canonical display name (network verdict)
- `search_vendor_status` — `ACTIVE` (network-confirmed) | `UNCONFIRMED_WAF_BLOCK` | `UNDETECTED`
- `search_vendor_oracle: "detect-search"`
- `search_vendor_network_confirmed` (bool) and `search_vendor_network_endpoint` (URL or null)
- `search_vendor_details` — app_id, api_key, indexes, agent (where the vendor exposes them)
- `search_vendor_builtwith` + `search_vendor_agreement` — empty (BuiltWith not in pipeline)
- `network_check_date`, `network_check_note`, `algolia_detected`

**If `detect-search` reports `bot_blocked: true` (WAF):**
- The mapper sets `search_vendor_status = "UNCONFIRMED_WAF_BLOCK"` automatically.
- Do NOT skip — a WAF block is itself a finding. Record `network_check_note` ("stealth retry needed in Phase 2").

**Only edge cases go back to the LLM:** if `detect-search` returns `UNDETECTED` but Layer 1 (SimilarWeb) strongly suggests a search vendor tag (TAG_ONLY shadow deployment), the LLM reconciles using the recorded fields — it does NOT invent a vendor.

### Final classification
`detect-search` is the authoritative network signal:
- `detect-search` ACTIVE → `search_vendor_status = "ACTIVE"` (network-confirmed)
- SimilarWeb tag PRESENT + `detect-search` UNDETECTED → `search_vendor_status = "TAG_ONLY"`
- `detect-search` ACTIVE but vendor not in SimilarWeb → `search_vendor_status = "ACTIVE_UNTAGGED"` (shadow deployment)
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
