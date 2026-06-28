---
name: algolia-intel-hiring
description: Layer 1H hiring signals module. Identifies ICP-relevant open roles by WebFetching the company's careers page and WebSearching job boards. No Apify/LinkedIn dependency. Classifies by tier (Economic Buyer, Technical Buyer, Champion) and flags vacancy signals. Produces 09d-hiring-signals.md and 09d-hiring-signals.json. Run in Wave 1 after company context is available.
layer: 1-intelligence
module_id: 1H
reads_from:
  - 01-company-context.json
writes_to:
  - 09d-hiring-signals.md
  - 09d-hiring-signals.json
skill_enrichment: true
version: 3.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1H
- **Model tier:** agent for COLLECTION (careers pages vary too much to script) +
  deterministic script `collect-hiring.py` for CLASSIFICATION (tier + ICP score + dedup)
- **Reads from:** `01-company-context.json` (company_name, domain, careers_url)
- **Script:** `collect-hiring.py` — `classify_roles()` does tier/ICP/dedup deterministically

---

## No Apify. No LinkedIn Scraping.

LinkedIn scraping (Apify) has been removed. It consistently returned 0 ICP-relevant data across all tested companies due to bot-detection and algorithmic sampling. It could not produce verifiable source URLs.

**This module now uses two WebSearch/WebFetch layers only:**
- Every role must have a direct URL pointing to the company's own careers portal or a major job board listing
- Every citation labeled `[FACT — WebFetch/WebSearch on {source_url}, {date}]`
- No unlinkable data. No LinkedIn-only citations.

---

## Layer 1: WebFetch on Company Careers Page

Attempt to directly fetch the company's careers page. Get the URL from `01-company-context.json → careers_url`, or construct it:
- `https://jobs.{domain}` (e.g., `https://jobs.nike.com`)
- `https://www.{domain}/careers`
- `https://careers.{domain}`

Use WebFetch to load the page. Parse job listings from the HTML.

**If the careers portal is protected (PerimeterX, iCIMS, Workday login wall):** Layer 1 returns 0 — document this and proceed to Layer 2.

Label all Layer 1 results: `[FACT — WebFetch on {careers_url}, {date}]`

---

## Layer 2: WebSearch on Job Boards (MANDATORY — always runs)

Run targeted WebSearch queries regardless of Layer 1 results. Focus on ICP role keywords.

**Query pattern — run all three:**
```
site:{domain}/careers OR site:jobs.{domain} director OR VP OR "head of" digital OR ecommerce OR commerce
site:{domain}/careers OR site:jobs.{domain} engineer OR architect OR "product manager" ecommerce OR search OR platform
"{company_name}" "product manager" OR "software engineer" OR "IT manager" OR "ecommerce" site:ziprecruiter.com OR site:indeed.com OR site:linkedin.com/jobs
```

**If company careers portal is not search-indexed** (iCIMS, Workday, Greenhouse behind auth):
- Use job board fallback: `"{company name}" [ICP role] site:ziprecruiter.com OR site:indeed.com`
- These return real postings with direct URLs — treat as FACT-grade

Label all Layer 2 results: `[FACT — WebSearch on {source}, {date}]`

---

## ICP Classification — DETERMINISTIC (do NOT classify by hand)

Tier + ICP-score + cross-layer dedup are done by `collect-hiring.py`, **not** by LLM
keyword-guessing. Your job is to *collect* roles; the script *classifies* them. This makes
the same role tier the same way every run.

**Step A — assemble the collected roles into a JSON array.** For every role found in Layer 1
and Layer 2, emit one object. Include the `layer` (1 or 2) so the script can dedup across them
and record where each role was seen:

```json
[
  {"title": "VP, Digital & Ecommerce", "desc": "<2-3 sentence JD summary>",
   "url": "https://...", "location": "City, ST", "job_id": "REQ-123",
   "layer": 1, "source": "careers page"},
  {"title": "Senior Software Engineer, Search", "desc": "...", "url": "https://...",
   "location": "Remote", "layer": 2, "source": "Indeed"}
]
```
Write this to `roles-raw.json` in the research dir.

**Step B — run the classifier:**
```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-hiring.py \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/roles-raw.json" \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  --company-name "{CompanyName}"
```
It writes `09d-hiring-classified.json` with, per role: `tier` (1–4), `tier_name`
(Economic Buyer / Technical Buyer / Champion / Context), `icp_score` (0–10),
`icp_keywords`, `seen_in_layers`, `dedup_collapsed`, and a `tier_summary`.

**Tier reference (what the script enforces — for your understanding, not for hand-scoring):**
- **Tier 1 — Economic Buyer:** VP/SVP/Director Digital, Ecommerce, Commerce, DTC, NDDC, Head of Digital, CDO, GM Digital
- **Tier 2 — Technical Buyer:** Search/Platform Engineer, Lead/Sr/Staff SWE (ecommerce/search/platform), Solutions Architect (commerce), Engineering Manager (ecommerce/platform)
- **Tier 3 — Champion:** Product Manager (Digital/Ecommerce/Search), UX/Product Designer (digital), CRO/Conversion Manager, Personalization Manager, Digital Analytics Lead
- **Tier 4 — Context:** everything else (operations, logistics, retail associate, supply chain)
- Score modifiers (applied by the script): +1 per HIGH ICP keyword, +0.5 per MED keyword in the description.

**Cross-layer dedup is automatic:** a role found in both Layer 1 and Layer 2 (same `job_id`,
or same normalized title+location) is kept ONCE, with `seen_in_layers: [1, 2]` and the richer
description. Do not hand-merge duplicates.

Classified roles carry the label `[OBSERVED — collect-hiring.classify, {date}]`
(`collection_method: agent_webfetch_websearch+deterministic_classify`). Only the *significance*
call ("is this vacancy a real buying signal") stays LLM judgment.

---

## Writing the Output

Read `09d-hiring-classified.json` (produced by the script in Step B). Use its `tier`,
`icp_score`, and `seen_in_layers` fields verbatim — do NOT re-tier or re-score by hand.

Write `09d-hiring-signals.md` with:
- Collection summary (Layer 1 result, Layer 2 result, total roles in, deduped count out)
- Tier 1–2 vacancy signals (score ≥7) with: tier, score, job ID, direct URL, location, description summary, Algolia relevance, source citation
- Tier 3 champion signals (condensed)
- Tier 4 context roles (list only)
- Buying committee assessment (Economic Buyer, Technical Buyer, Champion — in-seat or vacant) — this is the LLM *significance* call
- ICP summary table (from `tier_summary`)
- Data confidence table per role
- Layer collection notes (note any roles with `dedup_collapsed: true` seen in both layers)

Write `09d-hiring-signals.json` (carry the script's classification through, add the LLM significance call):
```json
{
  "meta": {"skill_enrichment_completed": true, "layer1_count": N, "layer2_count": N,
           "collection_method": "agent_webfetch_websearch+deterministic_classify"},
  "tier_summary": {"tier1": N, "tier2": N, "tier3": N, "tier4": N},
  "buying_committee": {"economic_buyer": "...", "technical_buyer": "..."}
}
```
`tier_summary` MUST equal the script's `tier_summary` (deterministic — no hand edits).

---

## Verification Gate

Pass criteria:
- `09d-hiring-signals.md` ≥ 2000 bytes
- Both Layer 1 and Layer 2 documented (even if Layer 1 = 0)
- Every role has a direct URL — no role without a source link
- All citations are `[FACT — WebFetch/WebSearch on {url}, {date}]`
- No Apify or LinkedIn-only citations
- `09d-hiring-classified.json` exists (script ran) and `tier_summary` in the `.md`/`.json` matches it
- `tier_summary` has all 4 tiers
- `buying_committee` has `economic_buyer` and `technical_buyer`
- `meta.skill_enrichment_completed = true`
