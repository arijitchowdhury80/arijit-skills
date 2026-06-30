# algolia-intel-partner

> Map the co-sell tech partner landscape and identify SI/consulting firms with existing C-suite relationships at an Algolia audit prospect, then produce a concrete sales-action plan.

**Version:** 2.0.0 · **Layer/Phase:** Wave 1 Intel Module · **Suite:** Algolia Search Audit

## What it does

Builds the partner intelligence layer of an audit by covering two distinct partner types. Tech partners are platforms the prospect already uses that have Algolia co-sell or referral agreements (Adobe, Salesforce, Shopify, SAP, commercetools, BigCommerce, and others) — detected from the prospect's tech stack and confirmed via Crossbeam MCP. SI/implementation partners are systems integrators and consulting firms with existing C-suite relationships at the account; these are discovered dynamically through open-web and tech-stack-bridged Gemini-grounded search queries, never from a hardcoded name list. The output is a structured `partner-intel.md` with labeled evidence for every claim and a concrete sales action plan.

## When to use

- User asks to run partner intelligence, partner discovery, or find co-sell/ecosystem partners for a prospect.
- Need to map which platforms in Algolia's tech partner network the prospect uses.
- Need to identify SI or consulting firms with existing C-suite relationships at the target company.
- Querying Crossbeam for account overlap on a prospect.
- `partner-intel.md` is missing from the audit workspace.
- Preparing a co-sell or relationship-based sales motion for an AE/BDR.

## Inputs (upstream)

- `$ARGUMENTS` — company slug; resolves to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`
- `02-tech-stack.md` — required input; extracts all detected platforms (CMS/DXP, commerce engine, CDN, analytics, personalization, search provider) to cross-reference against the Algolia tech partner list and drive tech-stack-bridged SI discovery queries

## Outputs

Single file: `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/partner-intel.md`

Sections:
- **Section A** — Tech Partners (Co-Sell Motions): platforms confirmed in stack with Algolia agreements (A1), Crossbeam account overlap (A2), future opportunities not yet in stack (A3)
- **Section B** — SI/Implementation Partners (Relationship Access): high-confidence relationships with ≥1 grounded citation (B1), potential SIs to investigate (B2)
- **Section C** — Sales Action Plan: immediate action within 1 week and secondary actions within 1 month, each naming the partner, the contact, and the ask
- **Section D** — Data Quality Notes: explicit gaps (Crossbeam unavailable, no grounded evidence, incomplete stack data)
- **Sources** table with URL, type, date, and section used

## Data sources

| Source | Provides | Method |
|--------|----------|--------|
| Crossbeam MCP | Tech partner and SI/agency account overlap for the prospect | Direct MCP query; label `[FACT — Crossbeam MCP, date]`; if unavailable, skill falls back to tech stack + gemini_search.py and notes the gap |
| `02-tech-stack.md` | Detected platforms for tech partner cross-reference and as bridge terms in SI discovery queries | Read upstream output; label `[FACT — 02-tech-stack.md, date]` |
| `gemini_search.py` | SI partner relationships via open-discovery and tech-stack-bridged queries; tech partner confirmation | Gemini-grounded search; `grounded: true` required; label `[GEMINI_SEARCH — citation url, date]`; skip entirely if `grounded: false` |
| WebFetch | Annual reports or primary sources that name implementation partners by name | Direct fetch of known URLs; label `[WEBFETCH — source URL, date]` |

## How PRISM runs it

PRISM invokes this skill via the claude-cli executor as part of Wave 1 research. It depends on `algolia-intel-techstack` completing first to produce `02-tech-stack.md`. Crossbeam MCP must be available on the executor environment for full partner overlap data; if unavailable, the skill degrades gracefully to tech stack analysis and Gemini-grounded search and records the gap in Section D. The output `partner-intel.md` feeds downstream sales enablement skills — the AE playbook (`algolia-synth-sales-plays`) and ABX campaign (`algolia-campaign-abx`) reference co-sell angles from Section C.

## Dependencies

- `gemini_search.py` — Gemini-grounded search helper (`~/.claude/skills/algolia-search-audit/scripts/`)
- Crossbeam MCP — primary SI discovery source; skill degrades gracefully if unavailable
- `GEMINI_API_KEY` — required for Gemini-grounded search queries
- `02-tech-stack.md` — required upstream input (from `algolia-intel-techstack`); skill cannot run without it

## Notes

- SI partners are discovered DYNAMICALLY. Queries must not hardcode SI firm names as search terms — the SI name must come out of the search result, not into the query. The reference registry of known Algolia SI partners (Slalom, Grid Dynamics, EPAM, Publicis Sapient, Deloitte Digital, Accenture, IBM iX, Merkle, Capgemini, ThoughtWorks, Perficient, Valtech, and others) is used only to recognise whether a firm that surfaced in discovery is a known Algolia SI partner. A firm absent from the list but named in the prospect's own signals is still a valid, higher-signal candidate.
- Every data point in `partner-intel.md` must carry a label (`[FACT]`, `[GEMINI_SEARCH]`, `[WEBFETCH]`, or `[ESTIMATE]`). Unlabeled claims are not permitted.
- Verification gate: file ≥ 2000 bytes, Section A present, Section B present, Sources section with ≥1 URL. Any gate failure stops execution.
