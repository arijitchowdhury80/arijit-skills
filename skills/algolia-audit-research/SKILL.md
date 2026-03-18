---
name: algolia-audit-research
description: Run Phase 1 pre-audit research for Algolia Search Audit. Collects company context, tech stack, traffic, competitors, financials, hiring, and investor intelligence. No browser required (Chrome optional for Step 13). Output: {company}-audit-workspace/ with 12 scratchpad files.
---

# Algolia Audit — Phase 1 Research

This is a standalone sub-skill of `/algolia-search-audit`. It runs only Phase 0 (Workspace Setup) and Phase 1 (Pre-Audit Research, Steps 1-14) — no browser testing, no scoring, no deliverable generation. Use this sub-skill to collect all research data before running `/algolia-audit-browser` for Phase 2 browser testing, or to refresh specific research steps without re-running the full audit.

When the full audit is run end-to-end via `/algolia-search-audit`, this sub-skill's logic runs as the first stage. Running it standalone lets you front-load research, parallelize work across sessions, or refresh stale data.

## Input

Accept `$ARGUMENTS` — the prospect website URL (e.g., `costco.com`, `https://www.tapestry.com`).

Optional flags:
- `--company {name}` — Override company name if different from domain (e.g., `--company "Tapestry"` for `tapestry.com`)
- `--refresh {step}` — Re-run a specific step without re-running all steps. Step numbers match the Phase 1 step list (e.g., `--refresh 9` re-runs Financial Context Synthesis, `--refresh financials` re-runs Steps 1-financial and 9, `--refresh intel` re-runs Step 12)
- `--no-browser` — Skip Step 13 (careers page Chrome visit) if Chrome MCP is unavailable. Falls back to LinkedIn Jobs + Indeed web searches.

### `--refresh` Step Reference

| Flag | Steps Re-run | Output Files Updated |
|------|-------------|----------------------|
| `--refresh 1` or `--refresh company` | Step 1 | `01-company-context.md` |
| `--refresh 2` or `--refresh techstack` | Step 2 | `02-tech-stack.md` |
| `--refresh 3` or `--refresh traffic` | Step 3 | `03-traffic-data.md` |
| `--refresh 4` or `--refresh competitors` | Step 4 | `04-competitors.md` |
| `--refresh 5` or `--refresh queries` | Step 5 | `05-test-queries.md` |
| `--refresh 6` | Step 6 | `04-competitors.md` (appended) |
| `--refresh 6b` or `--refresh competitivegap` | Step 6b | `04-competitors.md` (appended) |
| `--refresh 7` or `--refresh strategic` | Steps 7, 10 | `06-strategic-context.md` |
| `--refresh 8` or `--refresh hiring` | Step 8 | `07-hiring-signals.md` |
| `--refresh 9` or `--refresh financials` | Step 9 (+ Step 1 financial portion) | `08-financial-profile.md` |
| `--refresh 10` or `--refresh triggers` | Step 10 | `06-strategic-context.md` (appended) |
| `--refresh 11` or `--refresh casestudies` | Step 11 | `01-company-context.md` (appended) |
| `--refresh 12` or `--refresh intel` | Step 12 | `11-investor-intelligence.md` |
| `--refresh 13` or `--refresh deephiring` | Step 13 | `07-hiring-signals.md` (appended) |
| `--refresh 14` or `--refresh icp` | Step 14 | `12-icp-priority-mapping.md` |

When `--refresh` is passed: load the existing workspace, skip all steps except the specified one(s), update only the targeted scratchpad file(s), and update CHECKPOINT.md.

## Output Directory

All output files written to `./{company}-audit-workspace/` in the current working directory:

```
{company}-audit-workspace/
├── 01-company-context.md          ← Company overview, executives, financials, vertical, case studies
├── 02-tech-stack.md               ← BuiltWith + SimilarWeb technologies deep dive
├── 03-traffic-data.md             ← SimilarWeb 11-endpoint traffic analysis
├── 04-competitors.md              ← Competitor list + search provider analysis
├── 05-test-queries.md             ← Vertical-calibrated test queries (14-18 total)
├── 06-strategic-context.md        ← Strategic angles + trigger events
├── 07-hiring-signals.md           ← Hiring signals + buying committee map
├── 08-financial-profile.md        ← 3-year trend table + ROI estimate
├── 09-browser-findings.md         ← (empty placeholder — Phase 2 writes here)
├── 10-scoring-matrix.md           ← (empty placeholder — Phase 3 writes here)
├── 11-investor-intelligence.md    ← Investor quotes, 10-K risk factors, forward guidance
├── 12-icp-priority-mapping.md     ← "Speaking Their Language" priority-to-product map
├── screenshots/                   ← (empty placeholder — Phase 2 writes here)
└── _workspace-manifest.md         ← Step status checklist (enables resume after interruption)
```

## Checkpoint File

Write `{company}-audit-workspace/CHECKPOINT.md` immediately at the start (before any API calls) and update it after EVERY completed step. This file enables resume after context reset, session timeout, or interruption.

```markdown
# Research Checkpoint
Phase: 1 — Pre-Audit Research
Company: {company}
URL: {url}
Started: {ISO datetime}
Last Updated: {ISO datetime}

## Step Status
- [ ] Step 1: Company Context — PENDING
- [ ] Step 2: Tech Stack — PENDING
- [ ] Step 3: Traffic & Engagement — PENDING
- [ ] Step 4: Competitor Identification — PENDING
- [ ] Step 5: Test Queries — PENDING
- [ ] Step 6: Competitor Search Analysis — PENDING
- [ ] Step 6b: Competitive Gap Analysis & Strategic Positioning — PENDING
- [ ] Step 7: Strategic Angle Mining — PENDING
- [ ] Step 8: Hiring Signal Detection — PENDING
- [ ] Step 9: Financial Context Synthesis — PENDING
- [ ] Step 10: Trigger Event Synthesis — PENDING
- [ ] Step 11: Vertical Matching + Case Studies — PENDING
- [ ] Step 12: Investor Intelligence — PENDING
- [ ] Step 13: Deep Hiring + Buying Committee — PENDING
- [ ] Step 14: ICP-to-Priority Mapping — PENDING

## Recovery Command
If interrupted, resume with: /algolia-audit-research {url} --refresh {next-step-number}

## Notes
{any API errors, fallbacks used, or blockers encountered}
```

Update the step line to `[x] Step N: Name — DONE (YYYY-MM-DD HH:MM)` after each step completes. Update `Last Updated` timestamp and add any blockers to Notes.

## MCP Servers Required

| MCP Server | Required? | Used In |
|------------|-----------|---------|
| BuiltWith MCP | Required | Steps 1, 2, 6 |
| SimilarWeb MCP | Required | Steps 2, 3, 4, 6 |
| Yahoo Finance MCP | Required (public cos) | Steps 1, 9, 12 |
| WebSearch | Required | Steps 1, 5-8, 10-14 |
| WebFetch | Required | Steps 11, 12 |
| Chrome MCP | Optional | Step 13 (careers page visit) — use `--no-browser` to skip |

If Yahoo Finance MCP is unavailable (private company), substitute with 6 WebSearches for financial data and label all figures `[ESTIMATE]`.

## Execution Mode: Agent Teams

When running all 14 steps (no `--refresh` flag), use Agent Teams for parallel execution. The orchestrator spawns specialized agents per wave.

**Prerequisites**:
- Install `claude-sneakpeek` to unlock Agent Teams tools: `npx @realmikekelly/claude-sneakpeek quick --name claudesp`
- Run via `claudesp` (not `claude` or VS Code extension)
- Teammates inherit the lead's permissions at spawn time

### Wave 1 — Independent Research (parallel, no dependencies)

| Agent | Steps | Tools | Output |
|-------|-------|-------|--------|
| Agent A | Step 1: Company context + financials | Yahoo Finance MCP, BuiltWith `keywords-api`, WebSearch | `01-company-context.md` |
| Agent B | Step 2: Tech stack deep dive | BuiltWith MCP (6 endpoints) + SimilarWeb `get-website-content-technologies-agg` | `02-tech-stack.md` |
| Agent C | Step 3: Traffic & engagement | SimilarWeb MCP (11 endpoints) | `03-traffic-data.md` |
| Agent D | Step 4: Competitor identification | SimilarWeb MCP (2 endpoints) | `04-competitors.md` |

### Wave 2 — Dependent Research (parallel, after Wave 1 completes)

| Agent | Steps | Reads | Output |
|-------|-------|-------|--------|
| Agent E | Steps 5+11: Test queries + vertical matching | `01-company-context.md` | `05-test-queries.md` |
| Agent F | Steps 6+6b: Competitor search analysis + competitive gap analysis | `04-competitors.md` | Appends to `04-competitors.md` |
| Agent G | Steps 7+10: Strategic angles + trigger events | All Wave 1 files | `06-strategic-context.md` |
| Agent H | Step 8: Hiring signals | `01-company-context.md` | `07-hiring-signals.md` |
| Agent I | Step 9: Financial synthesis + ROI | `01-company-context.md`, `03-traffic-data.md` | `08-financial-profile.md` |

### Wave 3 — Deep Intelligence (parallel, after Wave 1+2)

| Agent | Steps | Reads | Output |
|-------|-------|-------|--------|
| Agent J | Step 12: Investor intelligence | `01-company-context.md` (for ticker) | `11-investor-intelligence.md` |
| Agent K | Step 13: Deep hiring + buying committee | `07-hiring-signals.md` | Appends to `07-hiring-signals.md` |

### Wave 4 — Synthesis (sequential, after Wave 3)

Step 14: ICP-to-Priority Mapping. Reads `11-investor-intelligence.md` + `08-financial-profile.md` + `01-company-context.md`. Writes to `12-icp-priority-mapping.md`.

## Universal Mandates

These rules apply to ALL steps, ALL scratchpad files, with NO exceptions.

### Source Citations (MANDATORY)

Every data point written to a scratchpad file MUST have a clickable hyperlink to its source:
- Financial figures → Yahoo Finance or SEC EDGAR URL
- Traffic stats → SimilarWeb URL
- Technology claims → BuiltWith URL
- Industry benchmarks → Baymard, Forrester, or source study URL
- Competitor data → BuiltWith per competitor + SimilarWeb
- Hiring signals → Careers page URL or job posting URL
- Investor quotes → Earnings transcript, 10-K, 10-Q, or investor presentation URL
- Case studies → Algolia customer page URL

**Citation format for scratchpad files**: Inline markdown hyperlinks `[Source](URL)` on every data point. A scratchpad file without sources is INCOMPLETE.

### Fact/Estimate/Observed Tags (MANDATORY)

For every data point written to a scratchpad file, tag it as FACT, ESTIMATE, or OBSERVED:

```
Revenue: $254.2B (FY2024) [FACT]
  Source: https://finance.yahoo.com/quote/COST
Employees: ~2,000 (estimated after 2025 layoffs) [ESTIMATE]
  Source: https://www.retaildive.com/... (article discusses layoffs but not exact headcount)
New items: "10,000+ New Items" [OBSERVED]
  Source: observed on homepage during browser audit
Monthly visits: 187M [FACT]
  Source: https://www.similarweb.com/website/costco.com/
```

**Tag rules**: An [ESTIMATE] must NEVER be presented as a [FACT] in deliverables. An [OBSERVED] value from the browser must not be inflated. Deliverables must preserve these distinctions — use "estimated" or "approximately" qualifiers for [ESTIMATE] values.

### MCP-First Data Collection

Always prefer MCP server data over WebSearch. Use WebSearch ONLY for:
- Narrative context (company overview, founding story)
- Executive bios
- Hiring signals (job posting URLs, JD text)
- Earnings call transcripts (where SEC EDGAR MCP unavailable)
- Industry context not available from structured APIs

Never use WebSearch to determine tech stack, financial figures, traffic metrics, or competitor search providers.

## Data Collection Hierarchy (MANDATORY — applies to ALL Phase 1 steps)

Every data point collected in Phase 1 must come from the highest-tier source available. Never substitute a lower-tier source when a higher-tier one exists.

| Tier | Sources | Accuracy | Use For |
|------|---------|----------|---------|
| **Tier 1** | MCP APIs: BuiltWith, SimilarWeb, Yahoo Finance MCP, SEC EDGAR MCP | 95–100% | Tech stack, traffic, financials, search vendors, demographics |
| **Tier 2** | Primary sources: WebFetch on company IR pages, press releases, official blog, careers page | 90–95% | Executive quotes (must WebFetch source), case study metrics (must WebFetch case study URL) |
| **Tier 3** | Secondary sources: WebSearch for narrative context, Wikipedia, news articles | 60–80% | Company overview narrative, hiring signals, strategic angle context ONLY |

**⛔ CRITICAL RULE: NEVER use Tier 3 for structured data.** Structured data = tech stack, financial figures, traffic metrics, competitor search providers, case study metrics. Tier 3 (WebSearch) does not verify live installations, current financial state, or exact metric values.

**Gold standard example — SimilarWeb unavailability**: If SimilarWeb returns no data (API error, site not indexed), the correct behavior is:
1. Document the failure explicitly in the scratchpad: `SimilarWeb traffic: NO DATA (API returned error — site may not be indexed)`
2. Use Tier 2 fallback: WebFetch Alexa/SimilarWeb public page if available
3. Label ALL resulting estimates with `[ESTIMATE — SimilarWeb unavailable]`
4. Never silently substitute a WebSearch estimate as if it were SimilarWeb data

## Process

### Phase 0: Workspace Setup

Before starting, create the scratchpad workspace. Write CHECKPOINT.md first (before any API calls).

```
{company}-audit-workspace/
├── 01-company-context.md
├── 02-tech-stack.md
├── 03-traffic-data.md
├── 04-competitors.md
├── 05-test-queries.md
├── 06-strategic-context.md
├── 07-hiring-signals.md
├── 08-financial-profile.md
├── 09-browser-findings.md          ← create empty with header "# Browser Findings\n\n(Phase 2 — not yet run)"
├── 10-scoring-matrix.md            ← create empty with header "# Scoring Matrix\n\n(Phase 3 — not yet run)"
├── 11-investor-intelligence.md
├── 12-icp-priority-mapping.md
├── screenshots/                    ← create empty directory
└── _workspace-manifest.md
```

Create `_workspace-manifest.md` with all 14 steps listed as `[ ] pending`. Update each to `[x] done` as completed. This enables resume if context resets.

```markdown
# Workspace Manifest — {company}
URL: {url}
Created: {ISO datetime}

## Phase 1 Steps
- [ ] Step 1: Company Context
- [ ] Step 2: Tech Stack
- [ ] Step 3: Traffic & Engagement
- [ ] Step 4: Competitor Identification
- [ ] Step 5: Test Queries
- [ ] Step 6: Competitor Search Analysis
- [ ] Step 6b: Competitive Gap Analysis & Strategic Positioning
- [ ] Step 7: Strategic Angle Mining
- [ ] Step 8: Hiring Signal Detection
- [ ] Step 9: Financial Context Synthesis
- [ ] Step 10: Trigger Event Synthesis
- [ ] Step 11: Vertical Matching + Case Studies
- [ ] Step 12: Investor Intelligence
- [ ] Step 13: Deep Hiring + Buying Committee
- [ ] Step 14: ICP-to-Priority Mapping

## Phase 2 (Browser — run via /algolia-audit-browser)
- [ ] Browser testing

## Phase 3 (Scoring — run after Phase 2)
- [ ] Scoring matrix
```

**If `--refresh {step}` flag is present**: Skip Phase 0 setup (workspace already exists). Load existing scratchpad files. Run only the specified step(s). Update CHECKPOINT.md with refresh note.

---

### Phase 1: Pre-Audit Research (14 steps — no browser needed except Step 13)

> **Pattern per step**: Run MCP/API call → Write structured results to scratchpad file → Update CHECKPOINT.md → Continue to next step. This prevents context overflow from ~35K tokens of raw Phase 1 data.
>
> **Source URL capture**: For every data point written to a scratchpad file, ALSO capture the source URL AND tag it as FACT, ESTIMATE, or OBSERVED:
> ```
> Revenue: $254.2B (FY2024) [FACT]
>   Source: https://finance.yahoo.com/quote/COST
> Employees: ~2,000 (estimated after 2025 layoffs) [ESTIMATE]
>   Source: https://www.retaildive.com/... (article discusses layoffs but not exact headcount)
> New items: "10,000+ New Items" [OBSERVED]
>   Source: observed on homepage during browser audit
> Monthly visits: 187M [FACT]
>   Source: https://www.similarweb.com/website/costco.com/
> ```
>
> **Tag rules**: An [ESTIMATE] must never be presented as a [FACT] in deliverables. An [OBSERVED] value from the browser must not be inflated (e.g., "10,000+" must never become "30,000+"). Deliverables must preserve these distinctions — use "estimated" or "approximately" qualifiers for [ESTIMATE] values.

---

#### Step 1: Company Context

Gather comprehensive company intelligence:

- **Company overview** (WebSearch): What they do, industry, founding year, employee count, store/warehouse count, recent news
- **SEO keywords** (BuiltWith `keywords-api`): Meta keywords, page titles — reveals brand positioning and SEO focus
- **Financial data (3-year trends)** via **Yahoo Finance MCP** (public companies):
  - **Ticker resolution**: Use WebSearch `"{company name}" stock ticker symbol NYSE NASDAQ"` first — Yahoo Finance MCP has no search tool
  - `get_stock_info(ticker)` — sector, industry, employee count, market cap, current price, 52-week range
  - `get_financial_statement(ticker, "income_stmt")` — Revenue, Net Income, Operating Income, EBITDA (3-4 fiscal years)
  - `get_financial_statement(ticker, "balance_sheet")` — Total Assets, Total Debt, Cash
  - `get_financial_statement(ticker, "quarterly_income_stmt")` — most recent quarterly data
  - `get_recommendations(ticker, "recommendations")` — analyst consensus
  - `get_recommendations(ticker, "upgrades_downgrades")` — recent analyst rating changes
  - `get_yahoo_finance_news(ticker)` — latest news for trigger event detection
  - `get_historical_stock_prices(ticker, period="1y")` — 1-year price history
  - **Margin Zone**: Calculate from EBITDA margin → 🔴 Red (≤10%) / 🟡 Yellow (10-20%) / 🟢 Green (>20%)
  - **Fallback for private companies**: 6 WebSearches + Chrome MCP visit to IR page
- **Strategic leadership deep dive** (WebSearch):
  - **Tier 1 (mandatory)**: CEO, CFO, COO
  - **Tier 2 (critical for Algolia story)**: CTO/CIO, CDO, SVP/VP E-Commerce, SVP/VP Technology
  - **Tier 3 (buying committee context)**: VP Engineering, VP Product, Director of Search/Discovery
  - For each: Name, title, tenure, background, education, notable recognitions
- **Vertical classification**: Match to vertical-query-library.md categories
- **Confidence**: Unmarked = 2+ sources agree. ⚠️ = single source or sources disagree.

→ Write to `01-company-context.md`. Update CHECKPOINT.md: Step 1 DONE.

---

#### Step 2: Technology Stack Deep Dive

Use BuiltWith MCP comprehensively:

- `domain-lookup` — Current search provider, e-commerce platform, analytics, personalization, recommendations
- `relationships-api` — Sister/related sites
- `recommendations-api` — Technology gaps and recommendations
- `financial-api` — Revenue estimates, employee count, funding data (cross-reference Yahoo Finance)
- `social-api` — Social profile URLs (LinkedIn, Twitter, Facebook — useful for executive research)
- `trust-api` — Domain trust score, domain age (credibility signal)
- **Parse "removed" technologies** → displacement signals (e.g., "RichRelevance REMOVED" = vacuum for Algolia Recommend)
- **Parse "added" technologies in last 6 months** → if search competitor added recently, flag as ⚠️ NEGATIVE SIGNAL
- Match any detected vendor to displacement quotes in `buyer-persona-reference.md` Section 3
- Fallback: If BuiltWith credits exhausted, use SimilarWeb `get-website-content-technologies-agg`

**⛔ MANDATORY — Search Vendor Cross-Check (SimilarWeb Technologies API)**:
In ADDITION to BuiltWith, you MUST call SimilarWeb `get-website-content-technologies-agg` for the prospect domain. BuiltWith may return empty (CAPTCHA-blocked, credit-exhausted, or miscategorized). SimilarWeb Technologies is the authoritative fallback.

Filter results for search-related technologies. If ANY enterprise search platform is detected:
- **Constructor, Constructor.io** → Direct Algolia competitor
- **Algolia** → Confirm they're not already a customer (abort audit if so)
- **Coveo, Coveo Cloud** → Direct competitor
- **Bloomreach Discovery, Bloomreach Search** → Direct competitor
- **Lucidworks, Lucidworks Fusion** → Direct competitor
- **SearchSpring, Searchspring** → Direct competitor
- **Klevu, Nosto, Attraqt, Hawksearch** → Competitors

Then record in `02-tech-stack.md`:
```
## ⚠️ EXISTING SEARCH VENDOR DETECTED
Vendor: {name}
Status: INSTALLED since {first_seen_date}
Source: SimilarWeb Technologies API (verified {today's date})
```

And adjust the audit narrative:
- If Algolia detected → abort audit (existing customer)
- If competitor detected → reframe ALL deliverables from "greenfield opportunity" to "competitive displacement"
- Record vendor name, installation date, and any co-existing search technologies

**⚠️ CRITICAL: "Installed" ≠ "Active"**
SimilarWeb Technologies detects JavaScript tags on the page. A tag being present does NOT mean the vendor is actively powering search. Vendors may be in evaluation/POC mode, partially deployed, or deprecated but not yet removed.

When a search vendor tag is detected, record it as `Status: TAG DETECTED (unverified)` in `02-tech-stack.md`. The tag will be VERIFIED or REFUTED in Phase 2 (Browser Testing) via network request inspection:
- During Phase 2 search testing, monitor network requests for the vendor's API domain:
  - Constructor.io → `cnstrc.com` or `constructor.io`
  - Algolia → `algolia.net` or `algolianet.com`
  - BloomReach → `brsrvr.com` or `bloomreach.com`
  - Coveo → `coveo.com` or `platform.cloud.coveo.com`
  - Klevu → `klevu.com`
- If API calls are found → `Status: ACTIVE (confirmed via network requests)`
- If ZERO API calls → `Status: TAG ONLY (not powering search — likely evaluation/POC)`
- Update `02-tech-stack.md` after Phase 2 with verified status

**Why this exists**: Uncommon Goods audit (2026-02-24) — SimilarWeb showed Constructor.io tag installed since July 2025, but live network request inspection revealed ZERO Constructor API calls. BloomReach (`brsrvr.com`) was the actual active search provider. Constructor was in evaluation/POC mode. Without this verification, an AE would have either (a) skipped a valid prospect thinking a competitor was entrenched, or (b) entered a meeting with wrong competitive intelligence.

→ Write to `02-tech-stack.md`. Update CHECKPOINT.md: Step 2 DONE.

---

#### Step 3: Traffic & Engagement Deep Dive

Use **SimilarWeb MCP ONLY** for all traffic metrics. **DO NOT scrape or WebFetch third-party analytics sites** (Semrush, Ahrefs, SEMrush, Moz, etc.) for traffic/engagement data. These sites use different measurement methodologies than SimilarWeb, and mixing sources creates unverifiable discrepancies. All traffic, engagement, demographics, and ranking data MUST come from SimilarWeb MCP endpoints so the fact-checker can reproduce exact results with identical API calls.

Use SimilarWeb MCP with ALL of these endpoints:
- `get-websites-traffic-and-engagement` — monthly visits, bounce rate, pages per visit, avg visit duration
- `get-websites-traffic-sources` — channel breakdown (organic, direct, paid, social, referral, mail)
- `get-websites-geography-agg` — top countries by traffic share
- `get-websites-demographics-agg` — age and gender breakdown
- `get-website-analysis-keywords-agg` — top keywords driving search traffic (branded vs non-branded)
- `get-websites-audience-interests-agg` — audience interest categories
- `get-websites-website-rank` — global rank + category rank (market position)
- `get-websites-referrals-agg` — incoming referral sites (partnership signals)
- `get-pages-popular-pages-agg` — top pages by traffic share (reveals what users care about)
- `get-pages-leading-folders-agg` — top URL folders (reveals site architecture: /search/, /product/, /category/)
- `get-websites-landing-pages-agg` with `traffic_source: "organic"` — top organic landing pages (SEO focus)
- Use `country: "ww"` if `"us"` errors

**web_source STANDARDIZATION (MANDATORY)**: ALL SimilarWeb API calls for a single audit MUST use `web_source: "total"` (desktop + mobile). If "total" errors, fall back to "desktop" but record the fallback and add "(desktop only)" caveat to ALL traffic metrics. NEVER mix desktop and total values in the same scratchpad file.

**⛔ API Parameter Metadata Header (MANDATORY at top of 03-traffic-data.md)**:
```markdown
## API Parameters (for fact-check reproducibility)
- Primary Source: SimilarWeb MCP
- web_source: total (or "desktop" if total errored — note here)
- country: ww (or "us" if ww errored — note here)
- start_date: YYYY-MM
- end_date: YYYY-MM
- Secondary Sources: [list any non-MCP sources used, or "NONE"]
- Fallbacks Used: [list any parameter fallbacks, or "NONE"]
```

ALL traffic metrics in this file MUST come from the SAME API calls with the SAME parameters. Do NOT mix desktop and total values. Do NOT blend SimilarWeb and Semrush data without clearly labeling which source each metric comes from. This metadata enables the fact-checker to reproduce exact results with identical API calls.

**Why this exists**: Uncommon Goods audit (2026-02-24) had traffic source percentages (53.52% Direct, 27.01% Organic) that couldn't be matched to any single SimilarWeb web_source + country + date combination, making fact-checking impossible.

→ Write to `03-traffic-data.md`. Update CHECKPOINT.md: Step 3 DONE.

---

#### Step 4: Competitor Identification

Use SimilarWeb to find top 3-5 competitors:
- `get-websites-similar-sites-agg` — top similar sites by audience overlap
- `get-websites-keywords-competitors-agg` — keyword competitors (organic)
- Cross-reference both lists to select the top 3-5 most relevant competitors

→ Write to `04-competitors.md`. Update CHECKPOINT.md: Step 4 DONE.

---

#### Step 5: Generate Test Queries

Based on the company's vertical from Step 1:
- Look up the prospect's vertical in `vertical-query-library.md`
- Pull 10-12 queries from the matching vertical row (broad, specific, NLP, typo, non-product, brand)
- Add 4-6 company-specific queries (flagship products, house brands, specific product names found on site)
- Total: 14-18 queries (vertically calibrated)

→ Write to `05-test-queries.md`. Update CHECKPOINT.md: Step 5 DONE.

---

#### Step 6: Competitor Search Analysis

For each of the top 3-5 competitors identified in Step 4:

> **⚠️ DATA SOURCE RULE**: Search provider detection MUST use Tier 1 sources (BuiltWith MCP + network inspection). WebSearch (Tier 3) finds only public announcements — it cannot detect live tech installations and has a ~33% error rate for vendor attribution. Do NOT use WebSearch to determine a competitor's search provider.

a. **MANDATORY — BuiltWith `domain-lookup`** for each competitor domain. Record detected search provider or "not detected" explicitly.

b. **MANDATORY — Network request analysis** (most definitive method): Use Chrome MCP to visit each competitor's site, run a search query, then inspect network requests via `get_network_request` or `list_network_requests`. Look for API calls to known search vendor domains:
   - Algolia: `*.algolia.net`, `*.algolia.io`, `*.algolianet.com`
   - Coveo: `*.cloud.coveo.com`, `*.coveo.com`
   - Bloomreach: `*.bloomreach.com`, `brsrvr.com`, `*.brconnector.com`
   - Constructor.io: `*.cnstrc.com`, `*.constructor.io`
   - Searchspring: `*.searchspring.io`, `*.searchspring.net`
   - Lucidworks: `*.lucidworks.com`
   - Elasticsearch/Elastic: `*.elastic.co`
   - If network requests show Vendor A but BuiltWith shows Vendor B → trust network requests. Document discrepancy.

c. SimilarWeb `get-websites-traffic-and-engagement` for each competitor (quick check — monthly visits and bounce rate)

d. **Quick search spot-check** (optional, time permitting): Use Chrome MCP to visit 1-2 competitor sites and run a single typo query. Screenshot if competitor handles it better.

e. **GOLDEN ANGLE**: If ANY competitor uses Algolia, flag prominently. This is the strongest sales angle.

f. Create competitor matrix:
   ```
   | Competitor | Search Provider | Detection Method | Monthly Traffic | Bounce Rate | Uses Algolia? |
   ```
   Record "BuiltWith + Network" or "BuiltWith only" or "Network only" in Detection Method column.

→ Append to `04-competitors.md`. Update CHECKPOINT.md: Step 6 DONE.

**⛔ GATE 1.6 — Competitor Search Provider Verification (BLOCKING)**

Before proceeding to Step 7, verify:
- [ ] BuiltWith `domain-lookup` called for EACH competitor (not optional, not skippable)
- [ ] Network request analysis performed for at least the top 2 competitors
- [ ] Each competitor has a search provider entry that is either VERIFIED (BuiltWith + network match) or DETECTED (one source only, labeled as such) — never UNKNOWN without attempted BuiltWith call
- [ ] If BuiltWith returns no data AND network inspection is inconclusive: label as "Search provider: Undetected — requires manual verification"

**Failure mode**: If this gate is skipped and an AE walks in with wrong competitive intel, the entire strategic positioning of the audit is invalidated.

---

#### Step 6b: Competitive Gap Analysis & Strategic Positioning

After collecting competitor search provider data (Step 6), analyze the competitive landscape to answer: **"Is Algolia positioning this prospect for feature parity with competitors, or as a strategic differentiator?"**

This step transforms descriptive competitor analysis (what they have) into prescriptive strategic positioning (how Algolia maps to competitive gaps).

**6b-1: Classify Competitive Scenario**

Analyze the competitor landscape from Step 6 and classify into one of four strategic scenarios:

| Scenario | Definition | Indicators | Strategic Implication |
|----------|-----------|------------|----------------------|
| **Defensive Play (Catch Up)** | Prospect is 2+ years behind category leaders | ≥1 competitor scored 2+ points higher in search maturity, uses advanced features prospect lacks (NLP, personalization, AI) | Algolia prevents competitive disadvantage from widening. Frame as risk mitigation. |
| **Offensive Play (Leapfrog)** | Most competitors use similar/inferior search technology | Majority of competitors use platform-native search or outdated vendors, similar feature gaps as prospect | Algolia creates strategic differentiation. Frame as competitive advantage opportunity. |
| **Golden Angle** | ≥1 competitor already uses Algolia | Competitor using Algolia has measurably better search experience than prospect | Leverage social proof: "Your competitor trusts Algolia — here's what they're achieving." |
| **Mixed** | Combination of all three scenarios | Some competitors ahead (Defensive), some at parity (Offensive), some using Algolia (Golden Angle) | Multi-pronged positioning: prevent gap widening + leapfrog parity players + follow proven category leaders. |

Record the scenario classification in `04-competitors.md` with supporting evidence.

**6b-2: Quantify Experience Gap**

For the top 3-5 competitors, estimate their search experience maturity on the same 0-10 scale used in Phase 3 scoring (will be completed later). Base estimates on:
- Observed search features during spot-check (Step 6d)
- Known capabilities of their search vendor (e.g., Algolia = likely 7-9/10, platform-native = likely 3-6/10)
- Public case studies or reviews mentioning their search quality

Create comparison table:

```markdown
### Competitive Experience Gap

| Company | Est. Search Score | Search Provider | Detection Method | Advantage Over {Prospect} |
|---------|------------------|-----------------|------------------|------------------------|
| Competitor A | 8.5/10 | Algolia | BuiltWith + Network | +4.1 points (projected) |
| {Prospect} | 4.4/10 | {Current Vendor} | — | — |
| Competitor B | 5.5/10 | Platform Native | BuiltWith only | +1.1 points (projected) |
```

Note: Prospect's actual score will be determined in Phase 3. Use conservative estimates for now based on their current vendor category.

**6b-3: Build Strategic Positioning Matrix**

Create feature-by-feature competitive analysis showing where Algolia positions the prospect:

```markdown
### Strategic Positioning Matrix

| Feature/Capability | {Prospect} Current | Competitor A (Leader) | Competitor B (Parity) | Algolia Positioning |
|-------------------|-------------------|---------------------|---------------------|-------------------|
| **NLP / Semantic Search** | ❌ None | ✅ Advanced (Algolia NeuralSearch) | ❌ None | **Defensive** (close gap) + **Golden Angle** (proven) |
| **Personalization** | ❌ None | ✅ Yes (Algolia AI) | ⚠️ Basic | **Defensive** (close gap) + **Offensive** (leapfrog parity) |
| **Dynamic Faceting** | ⚠️ Static | ✅ Query-aware | ⚠️ Static | **Offensive** (leapfrog 4/5 competitors) |
| **Recommendations** | ❌ None | ✅ ML-powered | ❌ None | **Offensive** (shared gap = differentiation opportunity) |
| **Search Speed** | ⚠️ Acceptable | ✅ <50ms | ⚠️ Acceptable | **Offensive** (performance as differentiator) |
| **Mobile Experience** | ⚠️ Basic | ✅ Optimized | ⚠️ Basic | **Offensive** (mobile-first consumer expectations) |
```

Legend:
- ✅ = Present/Strong
- ⚠️ = Partial/Basic
- ❌ = Absent/Weak

**6b-4: Calculate ROI by Competitive Scenario**

Extend the base ROI calculation from Step 9 with scenario-specific framing:

```markdown
### Competitive ROI Scenarios

**Baseline ROI** (from Step 9): ${X.X}M/year

**Defensive ROI** (Close gap to leaders):
- Gap Risk: Competitors A + B capture ${Y}M incremental revenue from superior search
- Algolia Impact: Prevent ${Y × 0.5}M revenue leakage = **${defensive_roi}M/year**
- Formula: (Leader's search-driven revenue × prospect's traffic share) × 50% capture rate

**Offensive ROI** (Leapfrog parity competitors):
- Market Share Opportunity: ${Z}M addressable from competitors at parity or behind
- Algolia Impact: Capture ${Z × 0.05}M via search superiority = **${offensive_roi}M/year**
- Formula: (Combined competitor search revenue × category share) × 5% shift rate

**Golden Angle ROI** (Follow proven path):
- Competitor Using Algolia: {Competitor Name} ({their known improvement metric, e.g., "+37% search conversion"})
- Prospect Benchmark: Apply same improvement to prospect's search-driven base
- Algolia Impact: ${golden_roi}M/year (**same technology, proven results**)
- Formula: Prospect's search-addressable revenue × competitor's documented lift %
```

Use actual case study metrics from competitor deployments when available. If competitor's exact results are not public, cite Algolia's vertical-average benchmarks.

**6b-5: Generate Sales Positioning Statements**

Based on the classified scenario, create AE-ready positioning:

**Defensive Play Opening**:
> "{Prospect} is currently 2-4 years behind {Competitor A} and {Competitor B} in search intelligence. While you're growing {X%} YoY, they're converting {Y%} more search traffic with Algolia's NLP and personalization. The gap compounds — every quarter you wait, they pull further ahead. Algolia closes that gap in 90 days."

**Offensive Play Opening**:
> "Good news: {4 out of 5} of your direct competitors use platform-native search with the same gaps you have. Upgrading to Algolia creates an immediate competitive moat — NLP that understands 'gift for mom under $300', personalization that surfaces what shoppers want, and sub-50ms speed. You're not catching up — you're leapfrogging the category."

**Golden Angle Opening**:
> "{Competitor A} and {Competitor B} — {33%} of your direct competitive set — already trust Algolia to power their search. {Competitor A} saw {+metric} within {timeframe}. They chose Algolia for the same reasons you're evaluating it: [specific gap]. The difference? They're already capturing the upside."

**Mixed Scenario Opening** (most common):
> "{Prospect} faces a three-front battle: {Competitor A} is 2+ years ahead with Algolia, {Competitors B-D} are at parity with similar gaps, and {Competitor E} just deployed Algolia last year. The window to act is now — before the parity players upgrade and the gap to leaders becomes insurmountable. Algolia addresses all three fronts in one deployment."

**Objection Handling**:

| Objection | Scenario-Specific Response |
|-----------|---------------------------|
| "Our search is good enough" | **Defensive**: "Your competitors don't think so — they're outspending you on search by {X}% and capturing incremental share." **Offensive**: "Good enough = table stakes. Algolia makes search a revenue driver, not a feature." |
| "We're building in-house" | **Golden Angle**: "{Competitor A} tried that. They switched to Algolia after 18 months and saw {metric} in {timeframe}. Buy vs. build is a 24-month gap in time-to-value." |
| "Too expensive" | **ROI by scenario**: "Defensive scenario alone justifies the investment — preventing ${defensive_roi}M revenue leakage pays for Algolia {X}× over." |

→ Append competitive gap analysis to `04-competitors.md` after the competitor matrix. Update CHECKPOINT.md: Step 6b DONE.

---

#### Step 7: Strategic Angle Mining

Use WebSearch to find business context:

a. **Expansion signals**: New stores, new markets, new product lines?
b. **Digital transformation**: E-commerce investment, mobile app, headless commerce migration?
c. **Competitive pressure**: Competitors gaining share?
d. **Industry trends**: Macro trends affecting this vertical
e. **Negative signal check**: WebSearch for `"{company} layoffs 2025 2026"` + `"{company} earnings miss"` + `"{company} hiring freeze"`
f. Output: 2-3 strategic angles (1-sentence insight + 1-sentence search connection each)

→ Write to `06-strategic-context.md`. Update CHECKPOINT.md: Step 7 DONE.

---

#### Step 8: Live Intelligence — Hiring, Social & News Signals (Apify)

**⚡ REPLACES** the old WebSearch-based hiring detection. Now uses Apify for structured, real-time data from LinkedIn Jobs, LinkedIn Posts, Twitter/X, and Google News.

Run `/algolia-live-signals {slug}` which executes 3 phases:

**Phase 1 — Hiring Intelligence (LinkedIn Jobs via Apify)**
- Actor: `curious_coder/linkedin-jobs-scraper`
- Scrapes up to 50 LinkedIn job postings for the company (last 90 days)
- Classifies roles against the full ICP taxonomy:
  - Tier 1: VP/Director/Head of Digital, eCommerce, CDO, CTO
  - Tier 2: Senior Engineer (platform/search), Solutions Architect, Search Engineer
  - Tier 3: Performance Marketing, Paid Media, Merchandising, CRO, Digital Analytics
  - Keyword boosters: "search", "NLP", "personalization", "Algolia", "headless commerce"
- Flags VACANCY_SIGNAL for Tier 1-2 roles with signal score ≥ 7
- Produces structured `buying_committee[]` with LinkedIn job URLs
→ Writes `07-hiring-signals.md`

**Phase 2 — Social Signals (LinkedIn + Twitter/X via Apify)**
- Actors: `harvestapi/linkedin-company-posts` + `apidojo/tweet-scraper`
- Scrapes last 30 days of company posts (30 LinkedIn + 30 Twitter, min 20 reactions)
- Scores each post 1-10 for Algolia relevance:
  - 9-10: Direct mentions of search, personalization, discovery, conversion
  - 7-8: International expansion, AI investment, tech modernization, CX initiatives
  - 5-6: Product launches, partnerships, digital transformation (context)
  - <6: Excluded
- Categories: SEARCH_PAIN, TECH_INVESTMENT, INTERNATIONAL_EXPANSION, CONVERSION_FOCUS, EXEC_PRIORITY
→ Writes `09b-social-signals.md`

**Phase 3 — News Signals (Google News via Apify)**
- Actor: `data_xplorer/google-news-scraper-fast`
- Runs 3 queries (digital/ecommerce, leadership changes, AI/expansion) last 60 days
- Categories: LEADERSHIP_CHANGE, FUNDING_EVENT, TECH_INVESTMENT, PRODUCT_LAUNCH, INTERNATIONAL
→ Writes `09c-news-signals.md`

**Cost:** ~$0.14/audit total across all 3 phases.

**Fallback:** If Apify unavailable, fall back to WebSearch-based hiring detection (old method) and note social/news signals as "unavailable."

→ Update CHECKPOINT.md: Step 8 DONE (Apify Live Signals).

---

#### Step 9: Financial Context Synthesis + ROI Estimate

Synthesize financial data with trend visualization.

**3-Year Trend Table (required format)**:

| Metric | FY2023 | FY2024 | FY2025 | 3-Year CAGR | Trend |
|--------|--------|--------|--------|-------------|-------|
| Revenue | ${X} | ${Y} | ${Z} | X% | ↗️/↘️/→ |
| Net Income | ... | ... | ... | ... | ... |
| Operating Margin | ... | ... | ... | — | ... |
| EBITDA | ... | ... | ... | ... | ... |
| E-commerce Revenue | ... | ... | ... | ... | ... |
| E-commerce % of Total | ... | ... | ... | — | ... |
| Digital/Tech Capex | ... | ... | ... | ... | ... |

**Trend Analysis**: Calculate YoY growth rates. Flag divergences (e.g., "Revenue growing 8% but e-commerce growing 22% = digital acceleration"). Flag margin compression.

**Graph Specification (for deck)**: Multi-line indexed chart: Revenue (Algolia Purple #5468FF), E-commerce (Nebula Blue #003DFF), Net Income (Space Gray #21243D). Annotations at inflection points.

**ROI estimate formula** (show the math):
```
Revenue Addressable = Total Revenue × Digital Share × Search-Driven Share (15%)
Conservative (5% improvement) = Revenue Addressable × 0.05
Moderate (10% improvement) = Revenue Addressable × 0.10
```

- Cite benchmarks: Use **vertically-relevant case studies** from the Vertical-to-Case-Study Mapping section (NOT default Lacoste/Decathlon)
- **Guardrails**: Always show formula + inputs + sources. Label as "directional estimate." Never present as guarantee.

→ Write to `08-financial-profile.md`. Update CHECKPOINT.md: Step 9 DONE.

---

#### Step 10: Trigger Event Synthesis

Cross-reference all signals from Steps 1-9:
- Top 3 **positive trigger events** (e.g., "Search vendor removed + hiring search engineers + digital sales +20%")
- Any **⚠️ caution signals** (e.g., "Coveo added 4 months ago", "layoffs announced")

**⛔ Article Date Verification (MANDATORY for all news citations)**:

For every news article cited as a "timing signal" or "trigger event":
1. Extract the article publication date from the page content (not the URL, not the search snippet)
2. Record it next to the citation: `Source: [URL] (published [YYYY-MM-DD])`
3. If article is >18 months old, classify as "Historical Context" NOT "Timing Signal" or "Trigger Event"
4. Verify that the event described matches the timeline claimed in your deliverables (e.g., if you write "Spring 2025", confirm the article date supports this)

**Why this exists**: Uncommon Goods audit (2026-02-24) cited a Modern Retail article about catalog deprecation as a "Spring 2025" timing signal. The article was actually published in 2020 — a 5-year error that would destroy credibility with the prospect.

→ Append to `06-strategic-context.md`. Update CHECKPOINT.md: Step 10 DONE.

---

#### Step 11: Vertical Matching + Case Study Verification

Select best case studies for this prospect:
- Match prospect vertical to `buyer-persona-reference.md` Section 2
- Select primary + secondary case study
- If BuiltWith detected a specific competitor vendor, select matching displacement quote from Section 3

**MANDATORY**: WebFetch each selected case study URL NOW. Do not wait until Phase 4.
- Extract the EXACT metric from the live page (not from memory, not from a description)
- Record it in the exact format required by the Case Study Verification Gate:
  ```
  CASE STUDY: {Company}
  URL: {verified live URL — confirmed not 404}
  METRIC: {exact wording from page, e.g., "+37% conversion rate improvement"}
  PRODUCT: {exact Algolia product name from page}
  TIMEFRAME: {from page verbatim, or "NOT STATED"}
  ```
- If URL is 404: search `algolia.com/customers/` for the correct variant before selecting

→ Append to `01-company-context.md`. Update CHECKPOINT.md: Step 11 DONE.

**⛔ GATE 1.11 — Case Study Metric Verification (BLOCKING)**

Before proceeding to Step 12, verify:
- [ ] Primary case study URL confirmed live (not 404) via WebFetch
- [ ] Secondary case study URL confirmed live (not 404) via WebFetch
- [ ] METRIC field contains the exact wording from the live page — not a paraphrase, not rounded
- [ ] PRODUCT field contains the exact Algolia product name from the page
- [ ] If any metric says "double-digit" on the page: record "double-digit improvement" — do NOT convert to a specific percentage

**Failure mode**: If metrics are pulled from memory at Phase 4, there is a 66%+ chance of conflating product specs with customer testimonials, or adding timeframes not stated on the page (confirmed in Oriental Trading audit, 2026-02-24).

---

#### Step 12: Investor Intelligence

Extract the company's stated strategic priorities using their OWN words from SEC filings, earnings calls, investor presentations, and investor day transcripts. This is the most powerful sales intelligence because it is unimpeachable — they said it themselves, on the record, to investors.

**For public companies** (verified filings via **SEC EDGAR MCP** + **Yahoo Finance MCP**):

a. **Retrieve Latest 10-K AND 10-Q** — Use SEC EDGAR MCP:
   - `search_filings(ticker, filing_type='10-K')` for annual filing
   - `search_filings(ticker, filing_type='10-Q')` for most recent quarterly filing (often has more current data than 10-K)

b. **Extract Strategic Narrative (MD&A)** — Use SEC EDGAR MCP:
   - `get_section_text(accession_number, section='MD&A')` from 10-K (Item 7) AND 10-Q (Item 2)
   - Scan for: e-commerce growth targets, "digital transformation," "omnichannel," search, discovery, AI, personalization, technology investment

c. **Extract Risk Factors** — Use SEC EDGAR MCP:
   - `get_section_text(accession_number, section='Risk Factors')` (Item 1A)
   - Look for: "competition," "technology infrastructure," "cybersecurity," "customer experience," "digital capabilities"

d. **Earnings Call Transcripts** — The most quotable source. Executives speak candidly.
   - WebSearch: `"{company} Q4 2025 earnings call transcript"` — try last 3 quarters
   - WebFetch on Seeking Alpha, Motley Fool, or company IR page for actual transcript text
   - Yahoo Finance MCP: `get_yahoo_finance_news(ticker)` for earnings coverage
   - **Capture quotes from ANY named speaker** — CEO, CFO, CTO, COO, SVP, VP, or any executive on the call. Do NOT limit to CEO/CFO only.
   - **Cast a WIDE net**: Search LAST 3 QUARTERS of earnings calls. Also search for investor day presentations and analyst day transcripts.

e. **Investor Presentations & Investor Days** — Primary sources for strategic direction:
   - WebSearch: `"{company} investor day 2025 presentation"` + `"{company} investor presentation 2025 2026"`
   - WebFetch on company IR page or Seeking Alpha for slides/transcripts
   - These often contain detailed technology roadmaps and digital strategy commitments not found in 10-K filings

f. **Analyst Estimates & Ratings** — Forward-looking context:
   - Yahoo Finance MCP: `get_recommendations(ticker, "recommendations")` for analyst consensus
   - Yahoo Finance MCP: `get_recommendations(ticker, "upgrades_downgrades")` for recent changes

g. **Multi-Year Financial Trend Analysis** — 3-year trajectory reveals strategic direction:
   - Yahoo Finance MCP: `get_financial_statement(ticker, "income_stmt")` — 3-year trends
   - Yahoo Finance MCP: `get_financial_statement(ticker, "balance_sheet")` — capex, cash, debt
   - Yahoo Finance MCP: `get_financial_statement(ticker, "cashflow")` — free cash flow, capex allocation
   - Yahoo Finance MCP: `get_historical_stock_prices(ticker, period="2y")` — 2-year stock trajectory

h. **Supplemental WebSearch** (only if above steps return insufficient data):
   - `"{company} CEO keynote conference 2025 2026"` + `"{company} technology roadmap"`

**For private companies** (COMPREHENSIVE — not a lightweight fallback):

Private companies require MORE research effort, not less. Without SEC filings, you must triangulate from multiple public sources.

a. **Revenue Intelligence** (WebSearch — try ALL of these):
   - `"{company}" revenue 2024 2025 million OR billion`
   - `"{company}" annual sales estimates`
   - `site:ecdb.com "{company}"` — eCommerceDB has private company estimates
   - `site:pitchbook.com "{company}"` OR `site:crunchbase.com "{company}"` — funding/valuation implies revenue range
   - `site:builtin.com "{company}" OR site:glassdoor.com "{company}" reviews` — employee reviews sometimes mention scale
   - `"{company}" "series" funding round valuation` — late-stage valuations often correlate to revenue multiples
   - `"{company}" Inc 5000 OR "fastest growing"` — growth lists publish revenue data

b. **3-Year Trend Estimation** (for private companies):
   - Use ecdb.com year-over-year if available
   - Compare founding year + employee count + traffic trends to estimate growth trajectory
   - Note: Mark ALL private company revenue as `[ESTIMATE]` with confidence level

   **Trend Estimation Table (private company format)**:
   | Metric | FY2023 (Est.) | FY2024 (Est.) | FY2025 (Est.) | Est. CAGR | Confidence |
   |--------|---------------|---------------|---------------|-----------|------------|
   | Revenue | ~$XXM | ~$XXM | ~$XXM | X% | LOW/MED |
   | Employees | X | X | X | X% | HIGH (LinkedIn) |
   | Traffic | X.XM | X.XM | X.XM | X% | HIGH (SimilarWeb) |

c. **Technology Investment Signals** (private companies):
   - `"{company}" CTO interview OR podcast OR conference`
   - `"{company}" engineering blog` — WebFetch if found
   - `"{company}" "tech stack" OR "architecture" OR "platform"`
   - `"{company}" hiring "senior engineer" OR "staff engineer" headcount`
   - `site:techcrunch.com OR site:venturebeat.com "{company}"`
   - LinkedIn: search for company engineering leaders, note team growth

d. **CEO/Founder Voice** (critical for private companies — often ONLY source of strategic direction):
   - `"{CEO name}" interview podcast 2024 2025 2026`
   - `"{CEO name}" keynote conference`
   - `"{company}" founder story OR "how we built"`
   - `site:youtube.com "{company}" CEO`
   - WebFetch on podcast transcripts (e.g., "How I Built This", industry podcasts)

e. **Funding & Investor Intelligence**:
   - `"{company}" funding round series investors`
   - `"{company}" valuation 2024 2025`
   - If PE-backed: `"{PE firm}" "{company}" investment thesis`
   - Investor press releases often contain growth metrics

f. **Industry/Analyst Coverage**:
   - `"{company}" industry report OR market analysis`
   - `"{company}" competitor analysis`
   - Trade publication coverage (retail: NRF, RIS; tech: TechCrunch, Protocol)

**Private Company Output Template** → Write to `11-investor-intelligence.md`:
```
## Investor Intelligence — {Company} (PRIVATE)

### Company Classification
- **Ownership**: {Private / PE-backed / Family-owned / VC-backed}
- **Est. Revenue**: ${X}M ({source} — {date verified})
- **Data Confidence**: {HIGH/MEDIUM/LOW}
- **Limitation**: No SEC filings, earnings calls, or analyst coverage available

### In Their Own Words (Sourced Quotes)
| # | Speaker | Title | Quote | Source | Date | Source URL |
|---|---------|-------|-------|--------|------|-----------|
| 1 | {CEO Name} | Founder/CEO | "{quote}" | {Podcast/Interview} | {Date} | {url} |

### Technology Investment Signals
- **Engineering Team Size**: {X engineers} (LinkedIn, {date})
- **Key Hires (Last 12 months)**: {notable tech hires}
- **Tech Stack Indicators**: {from job postings, blog, BuiltWith}
- **Digital Initiatives**: {from press releases, interviews}

### Strategic Priorities (from public statements)
1. {priority — with source + URL}
```

**Extraction targets** (applies to BOTH public and private companies):
- 5-8 direct quotes from **any executive** speaking (CEO, CFO, CTO, COO, SVP, VP, or any named speaker) about digital/technology/e-commerce priorities — across MULTIPLE earnings calls and investor presentations
- Stated e-commerce revenue target or growth goal (forward guidance to Wall Street)
- Capex allocation: what % goes to digital vs. physical expansion (3-year trend)
- Risk factors mentioning technology, digital capability, or customer experience gaps
- Analyst consensus sentiment on digital transformation
- Any stated timelines for technology modernization or platform migrations
- Any mention of search, discovery, recommendations, personalization, AI in filings
- Stated priorities that map to Algolia products (even if not directly about search)

**Public Company Output Template** → Write to `11-investor-intelligence.md`:
```
## Investor Intelligence — {Company}

### In Their Own Words (Sourced Quotes)
| # | Speaker | Title | Quote | Source | Date | Source URL | Maps To |
|---|---------|-------|-------|--------|------|-----------|---------|
| 1 | {Name} | {Title} | "{exact quote}" | Q4 FY2025 Earnings Call | Feb 2025 | {url} | Algolia NeuralSearch |

### Forward Guidance
- E-commerce revenue target: {stated target or "not disclosed"}
- Digital investment: {stated capex or "not disclosed"}

### Risk Factors Mentioning Digital/Technology
- {risk factor text, paraphrased, with source}

### Strategic Priorities (from filings)
1. {priority 1 — with source + URL}
```

**Guardrails**:
- Always cite source + date + URL + speaker name + title for every quote
- Use "the company stated" not "the company believes"
- NEVER fabricate quotes — if not found, say "Limited public investor data available"
- If no investor data found at all, note it and skip section gracefully

→ Write to `11-investor-intelligence.md`. Update CHECKPOINT.md: Step 12 DONE.

---

#### Step 13: Deep Hiring Analysis + Buying Committee Mapping

Go beyond web search to actually visit the company's careers page.

**Phase A: Web Search** (from Step 8 data):
- Additional: `"{company} LinkedIn jobs e-commerce OR digital OR search"`

**Phase B: Browser Visit** (Chrome MCP):
- Navigate to company careers page
- Search for keywords: "search", "relevance", "AI", "machine learning", "e-commerce", "digital", "discovery"
- Take screenshot of search results
- Count total roles by category (Engineering, Product, Data, eCommerce, Merchandising)
- Click into 2-3 most relevant JDs and extract: skills, team, responsibilities, technologies, source URL

**If `--no-browser` flag is set**: Skip Phase B. Use LinkedIn Jobs + Indeed web searches as fallback. Label hiring data `[WEB SEARCH — careers page not visited]`.

**Phase C: Buying Committee Mapping** — Identify the actual buying committee:

| Role Type | Description | Typical Titles |
|-----------|-------------|----------------|
| **Economic Buyer** | Signs the check, owns budget | VP Digital, VP eCommerce, SVP Retail Technology, CDO |
| **Technical Buyer** | Evaluates feasibility | Director of Engineering, Head of Platform, Principal Architect |
| **User Buyer** | Daily user, feels the pain | Director of Merchandising, Head of Search Ops, eCommerce Manager |
| **Champion** | Internal advocate | Product Manager (Search/Discovery), Search Engineer |

Research Steps:
1. LinkedIn Search (WebSearch — 4 queries): `site:linkedin.com "{company}" "VP eCommerce"`, etc.
2. For each person found: Name, Title, LinkedIn URL, Tenure, Previous company, Buyer role, Priority signal
3. Prioritization: 🔥 Hot (new in role + ex-Algolia customer), 🟡 Warm (new OR search background), ⚡ Technical (deep tech), 👤 User (daily user)

**Fallback**: If careers page is behind auth, fall back to LinkedIn Jobs + Indeed web searches.

→ Append to `07-hiring-signals.md` (includes hiring analysis AND buying committee map with stakeholder table and recommended outreach sequence). Update CHECKPOINT.md: Step 13 DONE.

---

#### Step 14: ICP-to-Priority Mapping

Synthesis step — no new API calls. Cross-reference investor intelligence + financial profile + audit scoring for the most powerful framing: "You said X → We found Y → Algolia does Z"

**Input files**: `11-investor-intelligence.md`, `08-financial-profile.md`, `01-company-context.md`

Note: `10-scoring-matrix.md` is referenced here but will be empty at this stage (Phase 3 populates it). This mapping will be refined after Phase 3 browser testing adds specific audit findings.

**Process**:
1. For each stated priority from investor intelligence: find matching Algolia product
2. For each major research signal (tech gap, hiring signal, competitive landscape): find supporting investor quote (if available)
3. Create discovery questions using the company's OWN language

**Output** → Write to `12-icp-priority-mapping.md`:
```markdown
## ICP-to-Priority Mapping — "Speaking Their Language"

### Priority-to-Product Map
| Their Stated Priority | Source | Algolia Solution | Discovery Question |
|---|---|---|---|
| "{exact quote from executive}" | Q4 2025 Earnings | NeuralSearch | "You told investors X — we can help with Y" |

### Anchor Points for AE
1. "{Company} told investors {X} — we can accelerate that with {product}"
```

→ Write to `12-icp-priority-mapping.md`. Update CHECKPOINT.md: Step 14 DONE.

---

## Completion Gate

> **⛔ BLOCKING** — All checks below must pass before Phase 1 is declared complete and before browser testing begins. These gates catch bad data at the source, preventing 60 minutes of browser and deliverable work on a garbage foundation.

### Gate 1.1 — File Completeness

After Step 14, verify all 12 scratchpad files exist and have content > 500 bytes:

```bash
ls -la {company}-audit-workspace/*.md | awk '{print $5, $9}'
```

If any file is under 500 bytes or missing: re-run that step before proceeding.

### Gate 1.2 — SimilarWeb Data Quality

Check that `03-traffic-data.md` contains real traffic numbers (not N/A, not error responses):

```bash
grep -E "visits|monthly|traffic|bounce" {company}-audit-workspace/03-traffic-data.md | head -5
```

Pass criteria:
- At least 3 lines with real numeric values
- No lines containing "N/A", "unavailable", "error", or "null" for these core fields: monthly visits, bounce rate, visit duration
- If SimilarWeb returned an error: the file must document the fallback source used (Similarweb `"ww"` retry, SemRush, or direct WebSearch)

**If 03-traffic-data.md fails**: Re-call `get-websites-traffic-and-engagement` with `country: "ww"` (not `"us"`). If still fails, note limitation and proceed — do NOT block Phase 2 for private companies or low-traffic sites.

### Gate 1.3 — BuiltWith Tech Stack Quality

Check that `02-tech-stack.md` contains at least one confirmed technology in each of: search, e-commerce platform, analytics:

```bash
grep -E "search|platform|analytics|commerce" {company}-audit-workspace/02-tech-stack.md | head -10
```

Pass criteria:
- Search vendor field is populated (even if "None detected" is a valid answer — but it must be explicitly stated, not missing)
- E-commerce platform identified (Shopify, Salesforce, SAP, Magento, custom, etc.)
- If BuiltWith returned empty: SimilarWeb `get-website-content-technologies-agg` was used as fallback (required)

**If 02-tech-stack.md fails**: Re-call `mcp__builtwith__domain-lookup` for the domain. If still empty, call `get-website-content-technologies-agg` from SimilarWeb and note which source was used.

### Gate 1.4 — Citation Count

Count hyperlinks across all scratchpad files:

```bash
grep -c '](http' {company}-audit-workspace/*.md | awk -F: '{sum += $2} END {print "Total citations:", sum}'
```

Pass criteria: Total citations ≥ 15 across all scratchpad files.

If below 15: identify which files have the fewest citations and add missing source links before proceeding.

### Gate 1.5 — Core Metrics Not All N/A

Check that key financial and traffic figures are not universally missing:

```bash
grep -E "N/A|unavailable|not available|private company" {company}-audit-workspace/08-financial-profile.md | wc -l
```

If > 5 lines return N/A: confirm in `01-company-context.md` that the company is private. Private companies legitimately have fewer data points — this is acceptable. Public companies should not have >5 N/A fields; if they do, re-run Step 9 (financials).

### Gate 1 Summary — Pass/Fail Output

After running all checks, write a Gate 1 summary block to CHECKPOINT.md:

```markdown
## Gate 1 Results
Gate 1.1 File Completeness: PASS / FAIL ({N} files, all >500B)
Gate 1.2 SimilarWeb Quality: PASS / FAIL / WAIVED (private/low-traffic)
Gate 1.3 BuiltWith Quality: PASS / FAIL / FALLBACK-USED
Gate 1.4 Citation Count: PASS / FAIL ({N} citations found, required: 15+)
Gate 1.5 Core Metrics: PASS / ACCEPTABLE (private co)

Overall: PASS → Proceed to Phase 2
       OR FAIL → Fix steps: [list which steps need re-run]
```

**Blocking condition**: Gate 1.1, 1.3, and 1.4 must PASS. Gate 1.2 and 1.5 may be WAIVED for private companies with documented justification. Do NOT start Phase 2 until overall gate is PASS.

Write final CHECKPOINT.md with status "COMPLETE":

```markdown
# Research Checkpoint
Phase: 1 — Pre-Audit Research
Company: {company}
URL: {url}
Status: COMPLETE
Completed: {ISO datetime}

## Step Status
- [x] Step 1: Company Context — DONE
- [x] Step 2: Tech Stack — DONE
- [x] Step 3: Traffic & Engagement — DONE
- [x] Step 4: Competitor Identification — DONE
- [x] Step 5: Test Queries — DONE
- [x] Step 6: Competitor Search Analysis — DONE
- [x] Step 6b: Competitive Gap Analysis & Strategic Positioning — DONE
- [x] Step 7: Strategic Angle Mining — DONE
- [x] Step 8: Hiring Signal Detection — DONE
- [x] Step 9: Financial Context Synthesis — DONE
- [x] Step 10: Trigger Event Synthesis — DONE
- [x] Step 11: Vertical Matching + Case Studies — DONE
- [x] Step 12: Investor Intelligence — DONE
- [x] Step 13: Deep Hiring + Buying Committee — DONE
- [x] Step 14: ICP-to-Priority Mapping — DONE

## Recovery Command
N/A — Phase 1 complete.
```

Output a summary table to the user:

| File | Size | Status |
|------|------|--------|
| 01-company-context.md | X KB | Done |
| 02-tech-stack.md | X KB | Done |
| 03-traffic-data.md | X KB | Done |
| 04-competitors.md | X KB | Done |
| 05-test-queries.md | X KB | Done |
| 06-strategic-context.md | X KB | Done |
| 07-hiring-signals.md | X KB | Done |
| 08-financial-profile.md | X KB | Done |
| 11-investor-intelligence.md | X KB | Done |
| 12-icp-priority-mapping.md | X KB | Done |

Then inform the user:

> Phase 1 research complete for {company}. All 12 scratchpad files written to `./{company}-audit-workspace/`.
>
> Next step: Run `/algolia-audit-browser {company}` (or `/algolia-search-audit {company} --phase searchaudit`) to begin Phase 2 browser testing.
>
> To regenerate deliverables from this research data: `/algolia-search-audit {company} --phase deliverables`
