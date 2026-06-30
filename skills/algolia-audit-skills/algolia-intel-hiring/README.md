# algolia-intel-hiring

> Identifies ICP-relevant open roles by scraping the company's own careers page and running Gemini-grounded searches on third-party job boards — no Apify or LinkedIn dependency.

**Version:** 3.0.0 · **Layer/Phase:** Layer 1H / Wave 1 · **Suite:** Algolia Search Audit

## What it does

Collects open roles from two layers: Layer 1 uses Scout to scrape the target company's own careers/jobs page (handling JS-rendered portals like Workday and iCIMS with markdown + raw_html fallback); Layer 2 uses Gemini-grounded search to find the same types of roles on third-party job boards (Indeed, LinkedIn Jobs, ZipRecruiter). All collected roles are then classified deterministically by `collect-hiring.py` — assigning each role a tier (Economic Buyer, Technical Buyer, Champion, or Context), an ICP score, and deduplicating across layers. The buying committee assessment (which seats are filled vs. vacant) is the only judgment call left to the LLM.

LinkedIn scraping via Apify was removed entirely: it consistently returned 0 ICP-relevant results across tested companies due to bot-detection and unverifiable source URLs.

## When to use

- Run in Wave 1 after `algolia-intel-company` has produced `01-company-context.json`.
- Use to map the buying committee at a prospect before a discovery call.
- Use when identifying which economic buyer, technical buyer, and champion seats are open vs. in-seat.

## Inputs (upstream)

- `01-company-context.json` — reads `company_name`, `domain`, and `careers_url`.
- If `careers_url` is absent, the module constructs fallback URLs: `https://jobs.{domain}`, `https://www.{domain}/careers`, `https://careers.{domain}`.

## Outputs

Files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

- `roles-raw.json` — all roles collected from Layer 1 and Layer 2, before classification.
- `09d-hiring-classified.json` — script output: `tier` (1–4), `tier_name`, `icp_score`, `icp_keywords`, `seen_in_layers`, `dedup_collapsed`, `tier_summary`.
- `09d-hiring-signals.md` — collection summary; tier 1–2 vacancy signals (score ≥7) with tier, score, job ID, URL, location, description summary, Algolia relevance, and source citation; tier 3 champion signals (condensed); tier 4 context roles (list only); buying committee assessment; ICP summary table; data confidence table.
- `09d-hiring-signals.json` — carries classifier output through; adds LLM buying committee assessment. `tier_summary` must match the classifier exactly — no hand edits.

## Data sources

| Source | Provides | Method |
|---|---|---|
| Scout (`POST {SCOUT_URL}/scrape`) | Job listings from the company's own careers portal; handles JS/Workday/iCIMS and falls back to `raw_html` | Layer 1 — direct scrape of `careers_url`; label: `[FACT — Scout scrape {careers_url}, {date}]` |
| Gemini-grounded search (`scripts/gemini_search.py`) | Matching roles listed on Indeed, LinkedIn Jobs, ZipRecruiter; 3 targeted queries per run | Layer 2 — open-web search; no-fabrication gate: if `grounded: false`, role is skipped entirely |

## How PRISM runs it

PRISM (the Hermes instance on the VPS) invokes this skill via the claude-cli executor as part of the Wave 1 research phase orchestrated by `algolia-audit-research`. It must run after `algolia-intel-company` (needs `01-company-context.json`). The module runs Layer 1 Scout scrape first, then Layer 2 Gemini-grounded queries regardless of Layer 1 results, writes `roles-raw.json`, calls `collect-hiring.py classify_roles()` deterministically, and writes all four output files before signaling completion.

## Dependencies

- **Scripts:** `collect-hiring.py` (classification — `classify_roles()`), `scripts/gemini_search.py` (Layer 2 grounded search)
- **Services:** Scout at `$SCOUT_URL` (default: `http://localhost:8421`)
- **Env keys:** `SCOUT_URL`, `SCOUT_API_KEY`, Gemini API credentials for `gemini_search.py`
- **Abort conditions:** None — if Layer 1 returns nothing (hard login wall / bot wall), the module documents Layer 1 count as 0 and proceeds to Layer 2.

## Notes

- Every role must have a direct URL (careers portal or job-board listing). No role ships without a source link.
- Deduplication across layers is handled by the script. A role found in both layers is kept once with `seen_in_layers: [1, 2]`. Do not merge duplicates by hand.
- Tier scoring is deterministic: `+1` per HIGH ICP keyword, `+0.5` per MED keyword in the description. Do not re-score or re-tier by hand.
- Layer 2 results are only accepted when `grounded: true` from `gemini_search.py`. Ungrounded model knowledge is never used.
- Verification gate: `09d-hiring-signals.md` ≥ 2000 bytes; both layers documented; every role has a direct URL; `09d-hiring-classified.json` exists; `tier_summary` matches across `.md`, `.json`, and classifier output; `meta.skill_enrichment_completed = true`.
