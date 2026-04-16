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
- **Model tier:** agent (no script dependency)
- **Reads from:** `01-company-context.json` (company_name, domain, careers_url)

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

## ICP Classification

Classify every role found into Tier 1–4 based on title + description:

**Tier 1 — Economic Buyer (score 7–10):**
VP/SVP/Director of Digital, Ecommerce, Commerce, DTC, NDDC, Head of Digital, CDO, GM Digital, Senior Director Digital/Commerce

**Tier 2 — Technical Buyer (score 7–10):**
Search Engineer, Platform Engineer, Lead/Senior/Staff Software Engineer (ecommerce/commerce/platform/search), Solutions Architect (ecommerce/commerce), Engineering Manager (ecommerce/platform), Technical Lead (commerce/headless)

**Tier 3 — Champion (score 5–7):**
Product Manager (Digital/Ecommerce/Search/Platform), UX/Product Designer (digital), Senior Manager Digital Platforms, CRO/Conversion Manager, Personalization Manager, Digital Analytics Manager/Lead

**Tier 4 — Context (score 1–4):**
Everything else — operations, logistics, design, admin, retail associate, supply chain

Score modifiers: +1 per ICP keyword in description (search, NLP, personalization, ecommerce, product discovery, Algolia, Elasticsearch, composable commerce)

---

## Writing the Output

Write `09d-hiring-signals.md` with:
- Collection summary (Layer 1 result, Layer 2 result, total ICP roles)
- Tier 1–2 vacancy signals (score ≥7) with: tier, score, job ID, direct URL, location, description summary, Algolia relevance, source citation
- Tier 3 champion signals (condensed)
- Tier 4 context roles (list only)
- Buying committee assessment (Economic Buyer, Technical Buyer, Champion — in-seat or vacant)
- ICP summary table
- Data confidence table per role
- Layer collection notes

Write `09d-hiring-signals.json`:
```json
{
  "meta": {"skill_enrichment_completed": true, "layer1_count": N, "layer2_count": N},
  "tier_summary": {"tier1": N, "tier2": N, "tier3": N, "tier4": N},
  "buying_committee": {"economic_buyer": "...", "technical_buyer": "..."}
}
```

---

## Verification Gate

Pass criteria:
- `09d-hiring-signals.md` ≥ 2000 bytes
- Both Layer 1 and Layer 2 documented (even if Layer 1 = 0)
- Every role has a direct URL — no role without a source link
- All citations are `[FACT — WebFetch/WebSearch on {url}, {date}]`
- No Apify or LinkedIn-only citations
- `tier_summary` has all 4 tiers
- `buying_committee` has `economic_buyer` and `technical_buyer`
- `meta.skill_enrichment_completed = true`
