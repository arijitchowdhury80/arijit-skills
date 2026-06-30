# algolia-intel-competitors

> Identify who competes with the prospect, detect their search technology, and surface Algolia's proof set in the same vertical.

**Version:** 2.0.0 · **Layer/Phase:** Layer 1D / Wave 1 · **Suite:** Algolia Search Audit

## What it does

Runs `collect-competitors.py` to pull SimilarWeb competitor data, then enriches each competitor with a deterministic search-vendor verdict from the `detect-search` oracle (Playwright packet inspection). Grounded search via `gemini_search.py` adds public context (case studies, press mentions). A mandatory second pass scans the full Algolia customer base for companies in the same vertical — finding the Golden Angle (a competitor already using Algolia with public proof). Classifies the competitive scenario as GOLDEN, DEFENSIVE, OFFENSIVE, or MIXED.

## When to use

- Any Algolia Search Audit, Wave 1 — runs after company context is available.
- Needed before scoring the competitive angle in the final report.
- Required to populate the Golden Angle section and match Algolia case studies to the specific vertical.

## Inputs (upstream)

| File | Used for |
|---|---|
| `01-company-context.json` | Company name, domain, vertical — defines who the competitors are |
| `02-tech-stack.json` | Current search vendor of the prospect — informs competitive scenario classification |

Both files must exist before this module runs.

## Outputs

Two files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

| File | Key fields |
|---|---|
| `04-competitors.md` | Competitor profiles, search vendor per competitor, Golden Angle section, case study matches |
| `04-competitors.json` | `competitors[]` (with `search_vendor`, `search_vendor_status`, `search_vendor_details`), `golden_angle.competitors_using_algolia[]`, `competitive_scenario`, `meta.skill_enrichment_completed` |

Verification gate: both files exist, `competitive_scenario` is not null, at least 2 competitors identified.

## Data sources

| Source | Provides | Method |
|---|---|---|
| SimilarWeb browser session (`collect-similarweb-browser.js`) | Initial competitor list from SimilarWeb Competitors tab | Browser automation (`--mode competitors-discovery`) — NOT an API/MCP; replaces dead API calls; CloudFront anti-bot frequently returns 0; grounded search (gemini_search.py) is the primary path when this happens |
| `detect-search` skill | Canonical search-vendor verdict per competitor (vendor name, app ID, index names) | `detect-search.js` Playwright packet inspection + `map-detect-search.py` mapper; `UNCONFIRMED_WAF_BLOCK` recorded as-is, no LLM fallback |
| Gemini-grounded Google Search (`gemini_search.py`) | Competitor enrichment (public case studies, press statements on search tech) | `gemini_search.py` — `grounded: true` required; field stays null otherwise |
| WebFetch | Algolia customer case study pages (`algolia.com/customers/{slug}`) | Direct URL fetch for verbatim metrics and outcomes |

No-fabrication gate: `gemini_search.py` results used only when `"grounded": true`. If `detect-search` returns `UNCONFIRMED_WAF_BLOCK`, that is the recorded verdict — no LLM guessing.

## How PRISM runs it

PRISM invokes this skill via the claude-cli executor in Wave 1, after `algolia-intel-company` (1A) and `algolia-intel-techstack` (1B) have completed. The orchestrator passes the company domain and audit directory. The Golden Angle customer scan — requiring at least 3 Algolia customers in the vertical — is mandatory regardless of whether direct competitors use Algolia.

## Dependencies

| Item | Detail |
|---|---|
| Script | `~/.claude/skills/algolia-search-audit/scripts/collect-competitors.py` |
| `detect-search` | `~/.claude/skills/detect-search/detect-search.js` — Node.js, Playwright required |
| `map-detect-search.py` | `~/.claude/skills/algolia-search-audit/scripts/map-detect-search.py` |
| `gemini_search.py` | `~/.claude/skills/algolia-search-audit/scripts/gemini_search.py` — requires `GEMINI_API_KEY` |
| SimilarWeb MCP | Required; 403 responses mean competitor discovery falls through to grounded search |
| Upstream | `01-company-context.json` and `02-tech-stack.json` must exist |

## Notes

- SimilarWeb's Competitors tab frequently returns 0 results due to CloudFront bot protection — this is expected. Grounded search via `gemini_search.py` is the primary competitor-identification path in that case.
- The Algolia customer vertical scan must produce at least 3 entries when Algolia has customers in the prospect's vertical. Widen to adjacent verticals or similar business models if the direct vertical yields fewer.
- Case study metrics must be verbatim — never paraphrase numbers or outcomes from Algolia's customer pages.
