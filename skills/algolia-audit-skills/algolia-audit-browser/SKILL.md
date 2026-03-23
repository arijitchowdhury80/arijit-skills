---
name: algolia-audit-browser
description: Use when the goal is live browser-based search testing on a prospect's website: visiting the site with a real browser, typing queries to observe autocomplete/SAYT behavior, NLP/semantic understanding (e.g., 'black yoga pants under 100'), typo tolerance, zero-results handling, federated search, intent detection, personalization, and recommendations, then capturing screenshots of each finding as evidence. This is the Phase 2 hands-on browser phase of an Algolia search audit and requires Phase 1 research to be complete first. Works around WAF/bot detection (Akamai, Cloudflare, Imperva) using Playwright stealth mode. Produces a screenshots folder and browser-findings document.
---

## MANDATORY FIRST ACTION — Platform Constitution

**Before executing any step in this skill:**

Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

This file defines the platform rules: JSON field names, CSS classes, T.* tokens, function names, naming conventions, sub-skill invocation pattern (Skill tool + verification gate), path convention ($ALGOLIA_AUDIT_DIR). These rules apply to every action this skill takes. No exceptions.

---
## CANONICAL PATH DEFINITIONS

The skill uses a user-configured audit directory. Set this once:

```bash
export ALGOLIA_AUDIT_DIR="/path/to/your/Algolia Search Audit"
# Example: export ALGOLIA_AUDIT_DIR="~/Documents/Algolia Search Audit"
# Add to ~/.zshrc or ~/.bashrc to persist across sessions
```

**Required folder structure** (structure is enforced, base path is user-configured):
```
$ALGOLIA_AUDIT_DIR/{CompanyName}/
├── research/          ← scratchpads 01-12, CHECKPOINT.md, FACTCHECK_GATE.md
├── factcheck/         ← factcheck dimension files (never published)
├── scripts/           ← company-specific scripts only
└── deliverables/
    ├── index.html                ← SPA
    ├── screenshots/              ← browser audit screenshots
    ├── ae-report.html
    ├── battle-card.html
    └── leave-behind.html
```

**Published to GitHub/Vercel:**
```
$ALGOLIA_ARIAN_DIR/{slug}/                ← mirrors $ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/
├── index.html
├── screenshots/
├── ae-report.html
├── battle-card.html
└── leave-behind.html
$ALGOLIA_ARIAN_DIR/{slug}-audit-data.json  ← JSON stays at root
```

**If ALGOLIA_AUDIT_DIR is not set:** Use current working directory. Run: `export ALGOLIA_AUDIT_DIR="$(pwd)"`


## Input

`$ARGUMENTS` — company slug or workspace path (e.g., `costco` or `./costco-audit-workspace`)

Resolves workspace at: `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`

`$ALGOLIA_AUDIT_DIR = $ALGOLIA_AUDIT_DIR`

If `--resume-from {step}` is passed (e.g., `--resume-from 2c`), skip all prior steps without re-running them. Jump directly to the named step and continue sequentially through 2t.

**Required files (Phase 1 must be complete):**
- `01-company-context.md` — for company URL and vertical
- `02-tech-stack.md` — for any detected search vendor tags to verify in Step 2a½
- `05-test-queries.md` — test query list for all search tests

If any of these files are missing, stop and warn the user: "Phase 1 must be completed first. Run `/algolia-search-audit {url} --phase research` to generate research scratchpad files."

---

## Output

- `screenshots/` — minimum 10 PNG files (Gate 2 requires this before proceeding to scoring)
- `09-browser-findings.md` — all browser observations, one section per step

---

## Checkpoint File

Write `$ALGOLIA_AUDIT_DIR/{{CompanyName}}/research/CHECKPOINT.md` updates after EACH step. Format:

```
# Browser Audit Checkpoint
Phase: 2 — Browser Testing
Company: {company}
Started: {ISO datetime}
Last Updated: {ISO datetime}

## Step Status
- [x] 2a: Homepage — screenshots/01-homepage.png ✅
- [x] 2a½: Search vendor verification — BloomReach ACTIVE ✅
- [ ] 2b: Empty State — IN PROGRESS
- [ ] 2c: SAYT — PENDING
- [ ] 2d: Full Results — PENDING
- [ ] 2e: Typo Tolerance — PENDING
- [ ] 2f: Synonym — PENDING
- [ ] 2g: No Results — PENDING
- [ ] 2h: Non-Product Content — PENDING
- [ ] 2i: Intent Detection — PENDING
- [ ] 2j: Merchandising Consistency — PENDING
- [ ] 2k: Federated Search — PENDING
- [ ] 2l: Mobile Experience — PENDING
- [ ] 2m: Semantic / NLP — PENDING
- [ ] 2n: Dynamic Facets — PENDING
- [ ] 2o: Popular & Recent Searches — PENDING
- [ ] 2p: Dynamic Categories — PENDING
- [ ] 2q: Personalization — PENDING
- [ ] 2r: Recommendations — PENDING
- [ ] 2s: Banners & Rules — PENDING
- [ ] 2t: Analytics Visibility — PENDING

## Screenshots Captured: {N}/10+
## Recovery Command
/algolia-audit-browser {company} --resume-from 2c
```

---

## Browser Automation: Playwright + Stealth (Primary)

**Primary method: Playwright CLI + stealth plugin** — bypasses WAF (Akamai, Cloudflare, Imperva, PerimeterX).

Why: Chrome MCP uses Chrome DevTools Protocol (CDP) which injects detectable fingerprints (`navigator.webdriver=true`, specific Chrome runtime signatures). WAFs detect this in <100ms and block with "Access Denied". Playwright + `puppeteer-extra-plugin-stealth` patches ~12 fingerprinting vectors making the browser indistinguishable from a real user. **Confirmed in B3 isolation test (2026-03-20): Chrome MCP blocked by Costco Akamai WAF after first search submit; Playwright stealth bypasses this.**

**Chrome MCP is still available** as a supplementary tool for tasks that do NOT trigger WAF (reading network requests, inspecting page structure). Use it alongside Playwright where it helps.

---

## Pre-Flight Checklist (MANDATORY)

Before starting any browser tests, verify these prerequisites.

### 1. Playwright Installation Check

```bash
cd ~/.claude/skills/algolia-search-audit && node -e "require('playwright-extra'); console.log('✓ Playwright ready')"
```

If this fails:
```bash
cd ~/.claude/skills/algolia-search-audit && npm install
npx playwright install chromium
```

### 2. Screenshots Directory

```bash
mkdir -p "$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/screenshots"
```

### 3. Node Version

```bash
node --version  # Must be ≥ 18
```

If Node is missing or old: `nvm use 18` or install from nodejs.org.

---

## Browser Execution: How Steps Run

Each browser test step uses the `audit-browser.js` script:

```bash
SKILL_DIR=~/.claude/skills/algolia-search-audit
node "$SKILL_DIR/scripts/audit-browser.js" \
  --company "{CompanyName}" \
  --url "{prospect-url}" \
  --step {step-id} \
  --audit-dir "$ALGOLIA_AUDIT_DIR" \
  --queries-file "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/05-test-queries.md"
```

The script:
1. Launches Playwright Chromium with stealth mode
2. Executes the specified test step
3. Saves screenshot directly to `$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/screenshots/`
4. Returns JSON with: `{ step, screenshot_path, observation, result_count, network_vendors }`

**To run ALL 20 steps sequentially:**
```bash
node "$SKILL_DIR/scripts/audit-browser.js" \
  --company "{CompanyName}" \
  --url "{prospect-url}" \
  --all-steps \
  --audit-dir "$ALGOLIA_AUDIT_DIR"
```

**WAF Recovery (if Playwright stealth still blocked):**

Some sites use extremely aggressive WAF (e.g., Ticketmaster). Escalation:
1. First attempt: Playwright headless + stealth (default)
2. If blocked: Playwright headed (visible browser, `--headed` flag) — slower but harder to detect
3. If still blocked: Ask user to manually solve CAPTCHA in visible browser window, then continue
4. Last resort: Document "WAF blocked automated testing" and use screenshots from manual navigation

```bash
# Headed mode (visible browser):
node audit-browser.js --company {CompanyName} --step 2a --headed
```

---

## Browser Audit Resilience

### Anti-Detection Best Practices

1. **Use Chrome MCP** (real Chrome browser with user profile) — NOT headless Puppeteer for audit testing
2. Before starting, resize window to standard desktop: `resize_window` → 1440x900
3. Navigate to homepage first, wait 3-5 seconds before any interaction
4. Type queries character-by-character with human-like timing (use `type` action, not paste)
5. Between test steps, wait 2-3 seconds (natural browsing pace)
6. **If CAPTCHA appears**:
   a. Take a screenshot of the CAPTCHA
   b. Ask the user to solve it manually in the Chrome window
   c. Wait for user confirmation, then continue
   d. Do NOT attempt to bypass or auto-solve CAPTCHAs
7. **If blocked by WAF/Cloudflare challenge**:
   a. Wait 10 seconds and retry navigation
   b. If still blocked, navigate to homepage first, then use site search
   c. If persistently blocked, note limitation in findings and proceed with available data
8. Never use Puppeteer MCP for actual audit testing — it triggers bot detection
9. Puppeteer MCP is acceptable ONLY for screenshot persistence (fallback method)
10. Cookie consent: Decline cookies when prompted (privacy-preserving)

### WAF Detection & Recovery Protocol

Many e-commerce sites use Akamai, Cloudflare, or Imperva WAF that block automated browsers. Detection signals:
- Page title contains "Access Denied", "Just a moment", "Checking your browser"
- Page body shows CAPTCHA, "ray ID", or challenge interstitial
- Screenshot file size is suspiciously small (<50KB = likely error page, not real content)
- HTTP 403/429 responses

**Recovery Steps (escalating)**:
1. **Retry with delay**: Wait 10 seconds, retry navigation
2. **Homepage-first approach**: Navigate to homepage, wait 5 seconds, THEN navigate to search
3. **Switch to real Chrome**: Kill any headless processes, use Chrome with remote debugging (see Pre-Flight step 2)
4. **User intervention**: If still blocked after 3 attempts, ask user to:
   - Manually navigate to the site in the Chrome window
   - Complete any CAPTCHA/challenge
   - Confirm when ready, then continue automation from that point
5. **Document limitation**: If site remains blocked, note in findings: "WAF blocked automated testing — limited screenshots available"

---

## Search Input Selector Resilience

E-commerce sites use various selectors for search inputs. Try these in order until one works (5-second timeout each):

```javascript
const SEARCH_SELECTORS = [
  '#SearchInput',                        // Common SFCC
  'input[type="search"]',                // Semantic HTML5
  'input[name="q"]',                     // Google-style
  'input[name="search"]',                // Generic
  'input[placeholder*="Search" i]',      // Placeholder-based (case-insensitive)
  'input[placeholder*="search" i]',      // Lowercase variant
  '[data-testid="search-input"]',        // React test ID
  '[data-testid*="search" i]',           // Partial test ID
  '.search-input',                       // Class-based
  '.searchInput',                        // CamelCase class
  '#search-input',                       // ID-based
  'input[aria-label*="Search" i]',       // Accessibility
  'header input[type="text"]',           // Header text input fallback
];

async function findSearchInput(page) {
  for (const selector of SEARCH_SELECTORS) {
    try {
      await page.waitForSelector(selector, { timeout: 5000 });
      return selector;
    } catch (e) {
      continue; // Try next selector
    }
  }
  throw new Error('No search input found with any known selector');
}
```

If all selectors fail, take a screenshot of the page and manually inspect the DOM to identify the correct selector.

---

## Screenshot Naming Convention

| Step | Filename |
|------|----------|
| 2a Homepage | `01-homepage.png` |
| 2b Empty State | `02-empty-state.png` |
| 2c SAYT | `03-sayt-{query}.png` |
| 2d Results | `04-results-{query}.png` |
| 2e Typo | `05-typo-{query}.png` |
| 2f Synonym | `06-synonym-{query}.png` |
| 2g No Results | `07-no-results.png` |
| 2h Non-Product Content | `08-non-product-{query}.png` |
| 2i Intent Detection | `09-intent-{query}.png` |
| 2j Merchandising | `10-merchandising.png` |
| 2k Federated Search | `11-federated.png` |
| 2l Mobile | `12-mobile-{query}.png` |
| 2m Semantic/NLP | `13-nlp-{query}.png` |
| 2n Dynamic Facets | `14-dynamic-facets.png` |
| 2o Popular Searches | `15-popular-searches.png` |
| 2p Dynamic Categories | `16-dynamic-categories.png` |
| 2q Personalization | `17-personalization.png` |
| 2r Recommendations | `18-recommendations.png` |
| 2s Banners | `19-banners.png` |
| 2t Analytics | `20-analytics.png` |

All files: `$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/screenshots/{nn}-{slug}.png`

---

## Screenshot Handling & Persistence

Screenshots are the #1 audit artifact — PROOF that testing was done.

> **FAILURE MODE TO AVOID**: Taking a Chrome MCP screenshot (getting imageId) but never writing to disk. Chrome MCP imageIds are SESSION-BOUND and become USELESS after the session ends. If screenshots are not on disk NOW, they will NEVER be on disk.

> **FAILURE MODE TO AVOID — EMPTY SEARCH BAR**: Screenshots of search tests where the search input appears empty (showing placeholder text like "Search" instead of the typed query). This happens when:
> 1. `form_input` is used instead of `computer` `type` — `form_input` sets `.value` programmatically which does NOT always trigger visual re-render or dispatch `input`/`keydown` events needed for SAYT
> 2. Screenshot is captured before the browser renders the typed text (race condition)
> 3. The SAYT overlay steals focus from the input field
>
> **FIX**: Always use `computer` tool with `action: "type"` for search queries. Always wait 1-2 seconds after typing before screenshot. Always verify the typed text is visible in the screenshot. For results pages this is less critical because the query appears in the page heading (e.g., `565 results for "purse"`), but for SAYT screenshots the typed text in the search bar IS the proof.

**Capture Procedure (for EACH screenshot)**:

1. Navigate & interact in Chrome MCP to desired page state
2. Take screenshot using Chrome MCP `computer` tool with `action: "screenshot"` → get imageId
3. **IMMEDIATELY persist to disk** using one of these methods (try in order):

   **Method 1 — Puppeteer MCP fallback**:
   Use `puppeteer_navigate` to same URL, then `puppeteer_screenshot` with `name: "{nn}-{slug}"`. Saves to disk automatically.

   **Method 2 — Chrome MCP download**:
   Use Chrome MCP `javascript_tool` to trigger download via html2canvas or canvas capture. Move from Downloads to `screenshots/` via Bash.

   **Method 3 — Chrome DevTools Protocol**:
   Capture viewport via canvas, convert to data URL, write base64 to disk via Bash.

4. **VERIFY file exists**: `ls -la $ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/screenshots/{nn}-{slug}.png`
5. **Log to scratchpad** in `09-browser-findings.md`:
   ```
   ### Step 2x: {Test Name}
   - Query: "{query}"
   - Screenshot: $ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/screenshots/{nn}-{slug}.png (VERIFIED ON DISK)
   - Result count: {n}
   - Observation: {what happened}
   ```

---

## Execution Mode

**Sequential mode (default for VS Code):** If CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 is NOT set (which is the case in VS Code extension), execute all 20 browser test steps sequentially: 2a → 2a½ → 2b → 2c → 2d → 2e → 2f → 2g → 2h → 2i → 2j → 2k → 2l → 2m → 2n → 2o → 2p → 2q → 2r → 2t. Sequential is the DEFAULT. Parallel execution via Agent Teams is an optimization, not a requirement.

**Parallel mode (claudesp only):** Available only when running via `claudesp` with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Enables concurrent browser steps where dependencies allow.

---

## Phase 2: Browser-Based Audit (20 Steps)

> **SCREENSHOT PERSISTENCE (mandatory)**: Before starting Phase 2, run `mkdir -p screenshots/`. Every screenshot instruction means: (1) Chrome MCP `computer` action `screenshot`, (2) IMMEDIATELY persist to disk in `screenshots/`, (3) VERIFY with `ls -la screenshots/{filename}`.

> **Scratchpad**: Append all observations to `09-browser-findings.md` after each step.

> **Checkpoint**: Update `CHECKPOINT.md` after EACH step, marking it `[x] done` with screenshot filename.

---

### CORE AUDIT (Steps 2a-2l)

Foundation of every search audit. Execute in full.

---

#### Step 2a: Initial Observations

- Navigate to the homepage
- Take a screenshot of the homepage with search bar visible → `screenshots/01-homepage.png`
- Note: Is search prominent? Icon or full bar? Position?

> After completing: update CHECKPOINT.md, mark `[x] 2a: Homepage — screenshots/01-homepage.png ✅`

---

#### Step 2a½: Search Vendor Network Verification (if vendor tag detected in Phase 1)

If `02-tech-stack.md` contains any `Status: TAG DETECTED (unverified)` entries:

1. Use Chrome MCP `read_network_requests` to start monitoring
2. Perform ONE search query and submit it
3. Check network requests for the vendor's API domain:
   - Constructor.io → `cnstrc.com` or `constructor.io`
   - Algolia → `algolia.net` or `algolianet.com`
   - BloomReach → `brsrvr.com` or `bloomreach.com`
   - Coveo → `coveo.com` or `platform.cloud.coveo.com`
   - Klevu → `klevu.com`
4. Also check which domain IS handling autocomplete/search (this reveals the ACTUAL provider)
5. Update `02-tech-stack.md`:
   - Vendor with API calls → `Status: ACTIVE (confirmed via network requests to {domain})`
   - Vendor with NO API calls → `Status: TAG ONLY (not powering search — evaluation/POC)`
   - Add actual provider if different: `Active Search Provider: {vendor} (via {api-domain})`

**Why**: SimilarWeb detects JavaScript tags, not active API usage. Uncommon Goods had Constructor.io tag since July 2025, but BloomReach (`brsrvr.com`) was actually powering all search. This step prevents false competitive intelligence.

> After completing: update CHECKPOINT.md, mark `[x] 2a½: Search vendor verification — {result} ✅`

---

#### Step 2b: Empty State Test

- Click on the search bar WITHOUT typing
- Take a screenshot → `screenshots/02-empty-state.png`
- Note: Popular searches, trending, recent searches, or nothing?

> After completing: update CHECKPOINT.md, mark `[x] 2b: Empty State ✅`

---

#### Step 2c: Search-As-You-Type (SAYT) Test

- Type a broad category query letter by letter using Chrome MCP `computer` tool with `action: "type"` (NEVER use `form_input` — it sets `.value` programmatically and does NOT trigger visual rendering or SAYT events)
- **CRITICAL — Search Bar Visibility in Screenshots**: After typing, wait 1-2 seconds for SAYT dropdown to render, then take screenshot. The typed text MUST be visible in the search input field in the screenshot. If the search bar appears empty in the screenshot despite typing:
  1. Click the search input first to ensure focus
  2. Use `computer` `action: "type"` with the query text (this simulates real keystrokes)
  3. Wait 2 seconds (`computer` `action: "wait"` `duration: 2`)
  4. Take screenshot — verify typed text is visible in the search bar
  5. If still empty, use `javascript_tool` to check the input value: `document.querySelector('input[type="search"]').value` — if it has the value but isn't rendering, try clicking the input again and re-typing
- Take a screenshot mid-typing (after 3-4 characters) showing BOTH the typed text in the search bar AND the SAYT dropdown → `screenshots/03-sayt-{query}.png`
- Note: Autocomplete speed, content (products, categories, suggestions), latency

> After completing: update CHECKPOINT.md, mark `[x] 2c: SAYT ✅`

---

#### Step 2d: Full Search Results Test

- Submit the full query and land on results page
- Take a screenshot → `screenshots/04-results-{query}.png`
- Note: Result quality, layout, filters/facets, sort options, result count
- Check: At least 4 sort options? Relevant facets with count badges?

> After completing: update CHECKPOINT.md, mark `[x] 2d: Full Results ✅`

---

#### Step 2e: Typo Tolerance Test

- Search each misspelled query from `05-test-queries.md` test list
- Take a screenshot per typo search → `screenshots/05-typo-{query}.png`
- Note: Returns results? "Did you mean..."? Or zero results?

> After completing: update CHECKPOINT.md, mark `[x] 2e: Typo Tolerance ✅`

---

#### Step 2f: Synonym / Colloquial Test

- Search synonym queries from `05-test-queries.md`
- Note: Does "couch" = "sofa"? Site understands colloquial terms?
- Take a screenshot → `screenshots/06-synonym-{query}.png`

> After completing: update CHECKPOINT.md, mark `[x] 2f: Synonym ✅`

---

#### Step 2g: No Results Test

- Search nonsense query ("asdfghjk")
- Take a screenshot → `screenshots/07-no-results.png`
- Note: Suggestions? Popular products? Just "no results found"?

> After completing: update CHECKPOINT.md, mark `[x] 2g: No Results ✅`

---

#### Step 2h: Non-Product Content Test

- Search "return policy", "customer service", "store hours"
- Take a screenshot → `screenshots/08-non-product-{query}.png`
- Note: Content/help pages returned? Or only products (or nothing)?

> After completing: update CHECKPOINT.md, mark `[x] 2h: Non-Product Content ✅`

---

#### Step 2i: Intent Detection Test

- Brand name → redirect to brand page or filter?
- Category name → suggest category?
- Attribute + product ("black chest", "red shoes") → apply filters?
- Take a screenshot → `screenshots/09-intent-{query}.png`

> After completing: update CHECKPOINT.md, mark `[x] 2i: Intent Detection ✅`

---

#### Step 2j: Merchandising Consistency Test

- Search a category term, then navigate to same category via menu
- Take screenshots of both views → `screenshots/10-merchandising.png`
- Note: Same products? Same order? Different merchandising?

> After completing: update CHECKPOINT.md, mark `[x] 2j: Merchandising Consistency ✅`

---

#### Step 2k: Federated Search Check

- During SAYT, note: Products, categories, content pages, brand pages? Or products-only?
- Take a screenshot → `screenshots/11-federated.png`

> After completing: update CHECKPOINT.md, mark `[x] 2k: Federated Search ✅`

---

#### Step 2l: Mobile Experience

- Resize browser to mobile viewport
- Quick search test
- Note: Mobile search experience quality, responsiveness
- Take a screenshot → `screenshots/12-mobile-{query}.png`

> After completing: update CHECKPOINT.md, mark `[x] 2l: Mobile Experience ✅`

---

### ALGOLIA VALUE-PROP TESTS (Steps 2m-2t)

Map to Algolia products for strategic differentiation.

---

#### Step 2m: Semantic / Natural Language Search (→ Algolia NeuralSearch)

- Test 2-3 NLP queries: conversational, multi-attribute, question-format
- Compare with keyword-equivalent queries
- Take screenshots → `screenshots/13-nlp-{query}.png`
- Note: Intent understanding or just keyword-match?

> After completing: update CHECKPOINT.md, mark `[x] 2m: Semantic/NLP ✅`

---

#### Step 2n: Dynamic Facets & Filtering (→ Algolia Dynamic Faceting)

- Search 2-3 different categories, observe filter panels
- Take screenshots → `screenshots/14-dynamic-facets.png`
- Note: Filters change by category context? Or static/generic?

> After completing: update CHECKPOINT.md, mark `[x] 2n: Dynamic Facets ✅`

---

#### Step 2o: Popular & Recent Searches (→ Algolia Query Suggestions)

- Click search bar → popular/trending suggestions?
- Search, navigate away, return → recent searches shown?
- Take screenshots → `screenshots/15-popular-searches.png`

> After completing: update CHECKPOINT.md, mark `[x] 2o: Popular & Recent Searches ✅`

---

#### Step 2p: Dynamic Search Categories (→ Algolia Federated Search + Rules)

- While typing, observe dynamic category suggestions (e.g., "nike" → "Nike Running Shoes")
- Take screenshot if present → `screenshots/16-dynamic-categories.png`

> After completing: update CHECKPOINT.md, mark `[x] 2p: Dynamic Categories ✅`

---

#### Step 2q: Personalization Signals (→ Algolia Personalization)

- Browse a specific category (click 3-4 products), then search a broad term
- Look for: "Recommended for you", personalized carousels, re-ranked results
- Take a screenshot → `screenshots/17-personalization.png`

> After completing: update CHECKPOINT.md, mark `[x] 2q: Personalization ✅`

---

#### Step 2r: Recommendations / FBT (→ Algolia Recommend)

- Navigate to 2-3 product detail pages
- Take screenshots of recommendation sections → `screenshots/18-recommendations.png`
- Note: "Frequently bought together", "Similar items" — relevant or generic?

> After completing: update CHECKPOINT.md, mark `[x] 2r: Recommendations ✅`

---

#### Step 2s: Banners & Merchandising Rules (→ Algolia Rules Engine)

- Search seasonal/campaign terms ("sale", "clearance")
- Search brand name → curated brand experience?
- Take screenshots of promotional content → `screenshots/19-banners.png`

> After completing: update CHECKPOINT.md, mark `[x] 2s: Banners & Rules ✅`

---

#### Step 2t: Analytics Visibility (→ Algolia Analytics)

- Look for: "trending" badges, "bestseller" tags, "most searched" labels
- Note: Visible analytics signals = strength; none = gap
- Take a screenshot → `screenshots/20-analytics.png`

> After completing: update CHECKPOINT.md, mark `[x] 2t: Analytics Visibility ✅`

---

## Gate 2: Screenshot Verification (BLOCKING)

Before marking Phase 2 complete, ALL of the following checks must pass:

**Check 1 — Minimum count (HARD GATE)**:
```bash
ls screenshots/ | wc -l
```
If result < 10: **STOP. Do NOT proceed to Phase 3.**
Print: "SCREENSHOT GATE FAILED: Only {N} screenshots on disk. Required: 10+."
Re-attempt screenshot capture for any missing files. Re-run the count. If STILL < 10, ask the user for guidance before proceeding.

**Check 2 — Zero-byte files**:
```bash
find screenshots/ -empty | wc -l
```
Must return 0. Delete and re-capture any empty files.

**Check 3 — Disk path verification**:
Each entry in `09-browser-findings.md` must include `Screenshot: $ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/screenshots/{nn}-{slug}.png (VERIFIED ON DISK)`. Entries with Chrome MCP imageIds like `ss_XXXXXXX` instead of file paths indicate persistence failure — fix immediately.

**Check 4 — WAF/Error Page Detection**:
```bash
echo "=== Screenshot Quality Check ==="
for f in screenshots/*.png; do
  size=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null)
  if [ "$size" -lt 50000 ]; then
    echo "WARNING: $f is only ${size} bytes — likely error page or blank"
  elif [ "$size" -lt 100000 ]; then
    echo "REVIEW: $f is ${size} bytes — may be sparse content"
  else
    echo "OK: $f is ${size} bytes"
  fi
done
```

Pass criteria:
- At least 10 screenshots > 100KB each (real content with product images)
- No screenshots < 50KB (these are WAF "Access Denied" or error pages)
- If multiple screenshots are flagged as potential error pages:
  1. Open one in a viewer to visually confirm
  2. If confirmed as error page, re-run browser tests with WAF Recovery Protocol
  3. If site is persistently blocked, document limitation and proceed with available data

**Gate 2 checklist**:
- [ ] `ls screenshots/ | wc -l` returns ≥ 10
- [ ] All 12 core steps executed (2a-2l)
- [ ] All 8 Algolia value-prop steps executed (2m-2t)
- [ ] Every screenshot referenced in `09-browser-findings.md` exists as a real file on disk
- [ ] Each finding category has ≥ 1 screenshot
- [ ] No screenshot is < 50KB (suspicious — likely WAF error page)

---

## Scratchpad Format for 09-browser-findings.md

Use this format consistently for all 20 steps:

```markdown
# Browser Findings — {Company}
Audit Date: {ISO date}
Auditor: Algolia (Claude Code)
Workspace: $ALGOLIA_AUDIT_DIR/{{CompanyName}}/research/

---

## CORE AUDIT

### Step 2a: Initial Observations
- Screenshot: screenshots/01-homepage.png (VERIFIED ON DISK)
- Search bar: {prominent / icon-only / hidden}
- Position: {top-center / top-right / other}
- Observation: {what was noted}

### Step 2a½: Search Vendor Network Verification
- Vendor tags found in 02-tech-stack.md: {list or "none"}
- Network requests monitored: {yes/no}
- Result: {vendor ACTIVE / vendor TAG ONLY / no vendors detected}
- Active provider: {vendor name} (via {api-domain})
- 02-tech-stack.md updated: {yes/no}

### Step 2b: Empty State Test
- Screenshot: screenshots/02-empty-state.png (VERIFIED ON DISK)
- Observation: {popular searches shown / trending / nothing}

### Step 2c: SAYT Test
- Query: "{query typed}"
- Screenshot: screenshots/03-sayt-{query}.png (VERIFIED ON DISK)
- Typed text visible in screenshot: {yes/no}
- Observation: {autocomplete speed, content types, latency}

[... repeat for all 20 steps ...]

---

## SUMMARY

### Key Gaps Found
1. {gap 1}: {evidence}
2. {gap 2}: {evidence}
...

### Algolia Opportunities
| Product | Evidence from Testing |
|---------|----------------------|
| NeuralSearch | {NLP test result} |
| Dynamic Faceting | {facet test result} |
| Recommend | {recs test result} |
| Rules Engine | {merchandising result} |
| Query Suggestions | {empty state result} |

### Overall Assessment
- Typo tolerance: {FAIL/PARTIAL/PASS}
- NLP / semantic: {FAIL/PARTIAL/PASS}
- Federated search: {FAIL/PARTIAL/PASS}
- No-results handling: {FAIL/PARTIAL/PASS}
- Personalization: {FAIL/PARTIAL/PASS}
- Recommendations: {FAIL/PARTIAL/PASS}
```

---

## Completion

After passing Gate 2, write CHECKPOINT.md final status:

```
# Browser Audit Checkpoint
Phase: 2 — Browser Testing
Company: {company}
Status: COMPLETE
Completed: {ISO datetime}

## All Steps: DONE
## Screenshots: {N} files on disk
## Gate 2: PASSED
```

Then output:
```
Phase 2 complete.
Screenshots: {N} files in screenshots/
Key gaps found: [summary of top 3 gaps from 09-browser-findings.md]

Next: Run /algolia-search-audit {company} --phase deliverables for scoring and report generation,
OR run the full scoring phase with /algolia-search-audit {company} --phase searchaudit (if Phase 1 is already done).
```

---

## Lessons Learned

### Tapestry/Coach Audit (2026-02-23) — WAF Blocking & Chrome Recovery

**Problem**: Coach.com uses Akamai WAF which blocked all automated browser attempts. Screenshots were ~30KB (error pages) instead of >100KB (real content). Page titles contained "Access Denied".

**Resolution sequence**:
1. Verified Chrome MCP was missing from `~/.claude/mcp_settings.json`
2. Added Chrome MCP configuration, user restarted Claude Code
3. If Chrome MCP still fails (WAF detecting automation signatures):
   - Launch real Chrome: `open -a "Google Chrome" --args --remote-debugging-port=9222`
   - Install puppeteer-core: `npm install puppeteer-core`
   - Connect: `puppeteer.connect({ browserURL: 'http://127.0.0.1:9222' })`
   - Use human-like typing delays (50-150ms between keystrokes)
4. Successfully captured 15 valid screenshots (all >100KB)

**Key symptoms of WAF blocking**:
- Screenshots are <30KB
- Page titles contain "Access Denied", "403", or "Bot Detection"
- Multiple identical error pages despite different URLs

**When to escalate**: After 3 WAF-blocked attempts with different approaches, ask the user to manually navigate to the site in Chrome, then connect via remote debugging.

### Screenshot Quality Check (Gate 2 addition)

After every screenshot, verify:
- File size > 100KB (error pages are typically 10-30KB)
- Page title does NOT contain "Access Denied", "403", "Error", "Bot"
- Screenshot shows actual search results, not a blank/error page

If a screenshot fails quality check: re-attempt with a delay, then try human-like interaction pattern before recording the finding.

### Search Input Selector Resilience

When `input[type="search"]` fails, try in order:
1. `input[name="q"]`
2. `input[placeholder*="search" i]`
3. `[data-testid*="search"] input`
4. `.search-bar input`
5. `#search input`
6. Ask user to manually click the search box, then type via Chrome MCP `type_text`
