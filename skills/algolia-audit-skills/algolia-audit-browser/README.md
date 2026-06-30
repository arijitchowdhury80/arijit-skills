# algolia-audit-browser

> Live browser-based search testing on a prospect's website, with screenshot evidence of every finding.

**Version:** 2.0.0 · **Layer/Phase:** Phase 2 — Browser Testing · **Suite:** Algolia Search Audit

## What it does

Visits the prospect's website with a real browser, runs 20 structured search test steps, and captures screenshots of each result. The 12 core steps (2a–2l) cover fundamental search behaviour: homepage layout, empty state, SAYT/autocomplete, full results, typo tolerance, synonym handling, no-results handling, non-product content, intent detection, merchandising consistency, federated search, and mobile experience. Eight additional steps (2m–2t) map each gap to an Algolia product: NeuralSearch, Dynamic Faceting, Query Suggestions, Rules Engine, Personalization, Recommend, and Analytics. The skill also verifies the prospect's and competitors' actual search vendors by inspecting live network requests during search — the only reliable detection method.

## When to use

- Phase 1 research is complete and the three required files exist (`01-company-context.md`, `02-tech-stack.md`, `05-test-queries.md`)
- You need hands-on evidence of search gaps before scoring and report generation
- Resuming an interrupted browser session: `algolia-audit-browser costco --resume-from 2c`

## Inputs (upstream)

Phase 1 must be complete. The skill checks for these files at `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/` and stops with an error if any are missing:

| File | Used for |
|------|----------|
| `01-company-context.md` | Company URL and vertical |
| `02-tech-stack.md` | Detected search vendor tags to verify in Step 2a½ |
| `05-test-queries.md` | Query list used across all 20 test steps |

## Outputs

All outputs land under `$ALGOLIA_AUDIT_DIR/{CompanyName}/`:

| Output | Location | Notes |
|--------|----------|-------|
| Screenshots (≥10 PNG) | `deliverables/screenshots/` | Named `{nn}-{slug}.png`; minimum 10, each >100KB |
| `09-browser-findings.md` | `research/` | One section per step, with screenshot file path, query, result count, and observation |
| CHECKPOINT.md updates | `research/` | Updated after every step; includes recovery command |

## Data sources

| Source | Provides | Method |
|--------|----------|--------|
| Playwright + stealth plugin | Browser automation bypassing WAF (Akamai, Cloudflare, Imperva, PerimeterX) | `audit-browser.js` (primary) |
| Chrome MCP | Network request inspection for search vendor verification; supplementary page analysis | CDP — used alongside Playwright, not for WAF-prone pages |

No external APIs are called. All findings come from live browser interaction with the prospect's website.

## How PRISM runs it

PRISM invokes this skill via the claude-cli executor after Phase 1 completes. It is the second stage of the pipeline; it must not run until all three required Phase 1 files are present and populated. PRISM passes the company slug as the argument. The skill runs all 20 steps sequentially by default; parallel execution is available via the `claudesp` runner with agent teams enabled on the VPS executor.

## Dependencies

**Scripts:**
- `audit-browser.js` — general-purpose Playwright stealth browser runner; configured via CLI flags or a per-company `browser-config.json` (custom selector, search URL template, query overrides). Never fork the script; use parameters.
- Accepts `--step`, `--all-steps`, `--headed`, `--search-selector`, `--search-url-template`, `--mode url`, `--config` flags.

**Runtime requirements:**
- Node.js ≥ 18
- `playwright-extra` + `puppeteer-extra-plugin-stealth` (installed via `npm install` in the skill dir)
- Chromium (`npx playwright install chromium`)
- `$ALGOLIA_AUDIT_DIR` env var set

**No MCP API keys required** for the browser steps themselves. Chrome MCP is used for network inspection (Step 2a½).

**Gate 2 (blocking before Phase 3):**
- `ls screenshots/ | wc -l` must return ≥ 10
- No screenshots < 50KB (WAF error page indicator)
- No zero-byte files
- Every finding in `09-browser-findings.md` must reference a file path on disk, not a Chrome MCP session imageId

## Notes

- Chrome MCP (CDP) injects detectable fingerprints (`navigator.webdriver=true`) and is blocked by aggressive WAFs in under 100ms. Playwright stealth patches ~12 fingerprinting vectors. If Playwright stealth is also blocked, escalate: headed mode → manual CAPTCHA solve → document "WAF blocked".
- WAF error pages are typically < 50KB. Real content with product images is typically > 100KB. Gate 2 enforces this check.
- Screenshots are the primary audit evidence. Chrome MCP imageIds are session-bound and become useless when the session ends. Always persist to disk immediately after capture and verify with `ls -la`.
- For sites where typing triggers WAF detection, use `--mode url` with a `--search-url-template` to navigate directly to results pages instead of typing queries.
- Step 2a½ is the ONLY reliable way to confirm a search vendor is active. A SimilarWeb "TAG DETECTED" label from Phase 1 only means a JS tag was present — it does not confirm the vendor is handling live search traffic.
