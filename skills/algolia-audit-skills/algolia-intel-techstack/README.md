# algolia-intel-techstack

> Detects the prospect's live technology stack — search vendor, ecommerce platform, analytics, tag manager, CDN/WAF, personalization, payment, frontend framework, hosting — and decides whether this audit is a displacement, an expansion, or greenfield.

**Version:** 2.0.0 · **Layer/Phase:** Layer 1B / Wave 1 · **Suite:** Algolia Search Audit

## What it does

Runs one script that performs a full, keyless network fingerprint of the prospect's site and writes the complete tech-stack files. It invokes `detect-search.js --full-tech` — a live **multi-page** packet inspection (home → category/PLP → product/PDP → search-results → cart) — and maps the result into the audit schema via `map-detect-tech.py`. Every technology is recorded with a confidence level (`confirmed` / `likely` / `likely-opendb`), evidence, and the pages it was seen on. The active search vendor is then confirmed by the `detect-search` skill as the canonical network oracle. No API key is required; SimilarWeb is an optional cross-check only.

## When to use

- Run in Wave 1 after `algolia-intel-company` has produced `01-company-context.json`.
- Use to establish the single most important framing fact of the audit: **what search vendor is live** (Algolia displacement target, existing-Algolia expansion, or no search vendor = greenfield).
- Use whenever `02-tech-stack.md`/`.json` is missing from the workspace.

## Inputs (upstream)

- `01-company-context.json` — reads the company `domain`.

## Outputs

Files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

- `02-tech-stack.md` — human-readable stack summary (≥2000 bytes to pass the gate).
- `02-tech-stack.json` — complete structured stack: search vendor + ecommerce platform + analytics + tag manager + CDN/WAF + personalization + payment + CDP + frontend framework + hosting, each with confidence/evidence/pages; plus the search-vendor verdict fields (`search_vendor`, `search_vendor_status`, `search_vendor_oracle`, `search_vendor_network_confirmed`, `search_vendor_network_endpoint`, `search_vendor_details`, `algolia_detected`).

## Data sources

| Source | Provides | Method |
|---|---|---|
| **detect-search** (`detect-search.js --full-tech`) | Full multi-page tech fingerprint + canonical search-vendor verdict | Keyless Playwright network packet inspection (primary); 30+ vendor signatures, deep app_id/index/api_key extraction, catches proxied first-party setups |
| **SimilarWeb REST API** (`SIMILARWEB_API_KEY`) | Optional tech cross-check (ecommerce platform, analytics, CDN/WAF, search tags) | `api.similarweb.com/v1/website/{domain}/content/technologies` — **not an MCP**; skipped gracefully if the key is unset |

No fabrication: client-side only (backend tech is invisible, same limitation BuiltWith had); a live load reflects current state only — no historical "removed tech". BuiltWith is fully retired from this module.

## How PRISM runs it

PRISM (the Hermes instance on the VPS) invokes this skill via the claude-cli executor in Wave 1, after `algolia-intel-company`. The collector runs the `detect-search` fingerprint itself, so the only hard dependency is the `detect-search` skill being installed and runnable on the executor. Because detection is keyless, no credentials need provisioning unless the optional SimilarWeb cross-check is wanted.

## Dependencies

- **Script:** `collect-techstack.py` (calls `detect-search.js --full-tech` → `map-detect-tech.py`; vendor verdict via `map-detect-search.py`).
- **Skill dependency:** `detect-search` — the canonical search-vendor oracle (must be installed).
- **Env keys:** none required. `SIMILARWEB_API_KEY` optional (cross-check only).
- **Existing-customer handling:** if `search_vendor == "Algolia"`, set `algolia_detected = true` and **continue** (expansion opportunity) — do not abort.

## Notes

- A WAF/bot block is a finding, not a failure: `search_vendor_status = "UNCONFIRMED_WAF_BLOCK"`, flagged for a stealth retry in Phase 2.
- `detect-search` is authoritative over passive SimilarWeb tags: a tag with no live network call = `TAG_ONLY`; a live call with no tag = `ACTIVE_UNTAGGED` (shadow deployment).
