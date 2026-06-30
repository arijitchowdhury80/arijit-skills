# algolia-intel-company

> Collect company overview, vertical classification, executive team, and key URLs for an Algolia audit prospect — always the first module to run.

**Version:** 2.0.0 · **Layer/Phase:** Layer 1A / Wave 1 · **Suite:** Algolia Search Audit

## What it does

Runs `collect-company.py` against the prospect's domain to produce the foundational company context file that every downstream module reads. Scout scrapes the company's own site first (about page, leadership pages, careers, investor relations). For any field Scout cannot fill, the module falls back to Gemini-grounded Google Search to fill gaps — never inventing data. A third step (portfolio detection) identifies parent entities, holding companies, and sibling brands via grounded search and direct WebFetch.

## When to use

- Starting any new Algolia Search Audit — this is always the first module.
- Company context (`01-company-context.json`) is missing from the audit workspace and a downstream module is blocked waiting for it.

## Inputs (upstream)

This is the first module in the pipeline. It reads nothing from upstream. Inputs are:
- `domain` — the prospect's primary web domain (e.g. `dsw.com`)
- `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/` — output directory

## Outputs

Two files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

| File | Key fields |
|---|---|
| `01-company-context.md` | Company narrative, executive list, parent/portfolio section |
| `01-company-context.json` | `company_name`, `domain`, `vertical`, `executives[]`, `parent_entity`, `is_conglomerate`, `portfolio_brands[]`, `primary_market`, `meta.skill_enrichment_completed` |

Verification gate: both files must exist; JSON must have `meta.skill_enrichment_completed = true`, non-null `company_name`/`domain`/`vertical`, and at least one executive with name + title.

## Data sources

| Source | Provides | Method |
|---|---|---|
| Scout (`localhost:8421`) | Description, LinkedIn URL, Twitter handle, executive list, careers URL, IR URL + PDF links | Scout direct-fetch of `/about`, `/leadership`, `/careers`, `/investors` pages; JS-rendered + stealth |
| Gemini-grounded Google Search (`gemini_search.py`) | HQ, founded, employee count, public/private status, vertical, executives (when Scout returns empty or degraded) | `gemini_search.py` — returns `{answer, citations, grounded}`; used only when `grounded: true`; null otherwise |
| WebFetch | Parent company and sibling brand pages (`/brands`, `/about/brands`, `/our-brands`) | Direct URL fetch |

No-fabrication gate: if `gemini_search.py` returns `"grounded": false`, the field stays null — ungrounded model knowledge is never used.

Scout degradation note: on Squarespace/JS bio-card CMS sites, Scout may return near-empty markdown even on a successful fetch. The script detects this (`scout_degraded: true` in JSON) and falls back to raw HTML parsing, labeling results `[OBSERVED]` rather than `[FACT]`. Degraded fields are re-verified via grounded search.

## How PRISM runs it

PRISM (the Hermes instance on the VPS) invokes this skill via the claude-cli executor as the first step of any audit run. It must complete before any other Wave-1 module starts, since all other modules read `01-company-context.json` for company name, domain, vertical, and executive data. The orchestrator (`algolia-audit-research`) gates all subsequent Wave-1 dispatches on this module's verification gate passing.

## Dependencies

| Item | Detail |
|---|---|
| Script | `~/.claude/skills/algolia-search-audit/scripts/collect-company.py` |
| Scout | `http://localhost:8421` — must be reachable on the VPS |
| `gemini_search.py` | `~/.claude/skills/algolia-search-audit/scripts/gemini_search.py` — requires `GEMINI_API_KEY` |
| Env | `ALGOLIA_AUDIT_DIR`, `GEMINI_API_KEY` |
| Abort condition | If `collect-company.py` exits with `status == "failed"`, alert and stop — do not continue to other modules |

## Notes

- The `--ticker` flag is optional; pass it when the ticker is known to pre-populate financial routing metadata.
- `scout_degraded: true` in the JSON means raw-HTML fallback was used — downstream factcheck reads this flag.
- Portfolio detection (Step 3) is an LLM-only step: no additional script is needed beyond `gemini_search.py` + WebFetch.
