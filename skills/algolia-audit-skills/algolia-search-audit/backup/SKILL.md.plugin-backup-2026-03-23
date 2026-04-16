---
name: algolia-search-audit
description: Run a comprehensive Algolia Search Audit on a prospect website with browser tests and report.
---

# Algolia Search Audit

Run a full search experience audit on a prospect's e-commerce or content website, producing a detailed findings report with screenshots, industry benchmarks, Algolia solution recommendations, an Algolia-branded presentation deck, an AE pre-call brief, and a strategic signal brief. Includes investor intelligence from SEC filings and earnings calls, deep hiring analysis from actual careers pages, and buying committee mapping with named stakeholders. Every deliverable uses full Algolia brand standards and hyperlinked source citations for instant credibility.

## Universal Mandate — Screenshots & Source Citations

These rules apply to ALL phases and ALL 6 deliverables, with NO exceptions.

**Screenshots**: Every finding MUST reference the actual screenshot file from `screenshots/`. Report = file path reference. Landing page = `<img>` tag. Deck = markdown image embed `![](screenshots/...)`. Chrome MCP screenshot imageIds are session-bound and USELESS after session ends — files MUST exist on disk. Without screenshots, findings are unverifiable claims.

**Source Citations**: Every data point MUST have a clickable hyperlink to its source:
- Financial figures → Yahoo Finance or SEC EDGAR URL
- Traffic stats → SimilarWeb URL
- Technology claims → BuiltWith URL
- Industry benchmarks → Baymard, Forrester, or source study URL
- Competitor data → BuiltWith per competitor + SimilarWeb
- Hiring signals → Careers page URL
- Investor quotes → Earnings transcript, 10-K, 10-Q, or investor presentation URL
- Case studies → Algolia customer page URL

**Citation format by deliverable**:
- **Report** (`search-audit.md`): Inline markdown hyperlinks `[Source](URL)`
- **Landing page** (`landing-page.html`): Source badges `<a href="URL">` per section + full bibliography
- **Deck** (`search-audit-deck.md`): Footnotes `[[N] Source](URL)` per slide + Appendix A1 bibliography
- **Content spec** (`landing-page.md`): Inline references
- **AE brief** (`ae-precall-brief.md`): Inline hyperlinks on every data point
- **Signal brief** (`strategic-signal-brief.md`): `SOURCE: {url}` on every line

**A deliverable without sources is INCOMPLETE. A finding without a screenshot is UNVERIFIABLE. Neither is acceptable.**

**MCP-First Data Collection**: Always prefer MCP server data over WebSearch. Use WebSearch only for narrative context, executive bios, hiring signals, and earnings call transcripts where no structured MCP endpoint exists.

## Input

Accept a website URL as `$ARGUMENTS` (e.g., `autozone.com`, `lacoste.com`). If no URL is provided, ask the user for the prospect's website.

Optionally the user may also provide:
- Company name (if different from domain)
- Industry vertical
- `--phase {phase}` flag to run only a specific part of the audit (see below)
- Multiple phases can be combined: `--phase financials,hiring,intel`

### Phase Flags (Modular Invocation)

By default (no `--phase` flag), the full audit runs end-to-end. Use `--phase` to run individual modules independently.

| Flag | What It Runs | Steps | Output | Tools Used |
|------|-------------|-------|--------|------------|
| `--phase company` | Company context, executives, vertical classification | Step 1 | `01-company-context.md` | WebSearch, Yahoo Finance MCP, BuiltWith MCP (`keywords-api`) |
| `--phase techstack` | BuiltWith technology deep dive (current + removed + added) | Step 2 | `02-tech-stack.md` | BuiltWith MCP (`domain-lookup`, `relationships-api`, `recommendations-api`, `financial-api`, `social-api`, `trust-api`) |
| `--phase traffic` | SimilarWeb traffic, demographics, audience, keywords, ranking, referrals, popular pages | Step 3 | `03-traffic-data.md` | SimilarWeb MCP (11 endpoints) |
| `--phase competitors` | Competitor identification + search provider analysis | Steps 4, 6 | `04-competitors.md` | SimilarWeb MCP (`similar-sites`, `keywords-competitors`), BuiltWith per competitor |
| `--phase financials` | 3-year financial trends, margin zone, ROI estimate | Steps 1 (financial), 9 | `01-company-context.md`, `08-financial-profile.md` | Yahoo Finance MCP (all financial tools), WebSearch |
| `--phase hiring` | Hiring signals + deep careers page analysis (Chrome MCP) | Steps 8, 13 | `07-hiring-signals.md` | WebSearch, Chrome MCP (careers page visit) |
| `--phase intel` | Investor intelligence: 10-K, 10-Q, earnings calls, investor presentations | Step 12 | `11-investor-intelligence.md` | SEC EDGAR MCP, Yahoo Finance MCP, WebSearch, WebFetch |
| `--phase strategic` | Strategic angles, trigger events, negative signals | Steps 7, 10 | `06-strategic-context.md` | WebSearch |
| `--phase queries` | Generate vertical-calibrated test queries | Steps 5, 11 | `05-test-queries.md` | Reads `01-company-context.md` for vertical |
| `--phase research` | **ALL of Phase 1** (steps 1-14) — no browser testing | Steps 1-14 | All scratchpad files (01-12) | All research tools |
| `--phase searchaudit` | **Browser-based search testing + scoring** (Phase 2 + 3) | Steps 2a-2t, Phase 3 | `09-browser-findings.md`, `10-scoring-matrix.md`, `screenshots/` | Chrome MCP |
| `--phase deliverables` | **Generate all 6 output files** from existing scratchpad data | Phases 4-5 | All 6 deliverables | Reads scratchpad files |
| `--phase report` | Generate only the audit report | Phase 4 | `{company}-search-audit.md` | Reads scratchpad files |
| `--phase deck` | Generate only the presentation deck | Phase 5b | `{company}-search-audit-deck.md` | Reads scratchpad files |
| `--phase landingpage` | Generate only the landing page HTML | Phase 5a | `{company}-landing-page.html` | Reads scratchpad files |
| `--phase aebrief` | Generate only the AE pre-call brief | Phase 5e | `{company}-ae-precall-brief.md` | Reads scratchpad files |
| *(no flag)* | **Full audit** — all phases end-to-end | Everything | All scratchpad + all 6 deliverables + screenshots | All tools |

**Combining phases**: Use comma-separated values: `/algolia-search-audit costco.com --phase financials,hiring,intel`

**Common workflows**:
- **Quick financial check**: `--phase financials`
- **Research only (no browser)**: `--phase research`
- **Browser testing only (already have research)**: `--phase searchaudit`
- **Regenerate deliverables (data already collected)**: `--phase deliverables`
- **Deep intel package**: `--phase financials,intel,hiring,strategic`

### Argument Parsing Rules

1. **Parse `$ARGUMENTS`**: Extract the URL (first non-flag argument) and any `--phase` flag value
2. **If `--phase` is present**: Run ONLY the specified phase(s). Skip all other phases. Still create workspace if it doesn't exist.
3. **If no `--phase`**: Run the full audit (default behavior)
4. **Dependency handling**: If a required scratchpad file is missing, warn the user — do NOT silently skip.
5. **Workspace reuse**: All phases write to the same `{company}-audit-workspace/` directory.
6. **Gate checks**: Only run gates relevant to the phase(s) being executed.

### Phase Dependencies

```
company ──────────┐
techstack ────────┤
traffic ──────────┤
competitors ──────┤── queries (needs vertical from company)
financials ───────┤
hiring ───────────┤── strategic (needs signals from all above)
intel ────────────┘
                   ↓
            searchaudit (needs queries from 'queries' phase)
                   ↓
              scoring (part of searchaudit)
                   ↓
            deliverables (needs scratchpad files + screenshots)
               ├── report
               ├── deck
               ├── landingpage
               ├── aebrief
               └── signalbrief
```

## Execution Mode: Agent Teams

When running the full audit (no `--phase` flag) or `--phase research`, use agent teams for parallel execution. The orchestrator spawns specialized agents per wave. This requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in settings.

### Wave 1 — Independent Research (parallel, no dependencies)

| Agent | Steps | Tools | Output |
|-------|-------|-------|--------|
| Agent A | Step 1: Company context + financials | Yahoo Finance MCP, BuiltWith `keywords-api`, WebSearch | `01-company-context.md` |
| Agent B | Step 2: Tech stack deep dive | BuiltWith MCP (6 endpoints) | `02-tech-stack.md` |
| Agent C | Step 3: Traffic & engagement | SimilarWeb MCP (11 endpoints) | `03-traffic-data.md` |
| Agent D | Step 4: Competitor identification | SimilarWeb MCP (2 endpoints) | `04-competitors.md` |

### Wave 2 — Dependent Research (parallel, after Wave 1 completes)

| Agent | Steps | Reads | Output |
|-------|-------|-------|--------|
| Agent E | Steps 5+11: Test queries + vertical matching | `01-company-context.md` | `05-test-queries.md` |
| Agent F | Step 6: Competitor search analysis | `04-competitors.md` | Appends to `04-competitors.md` |
| Agent G | Steps 7+10: Strategic angles + trigger events | All Wave 1 files | `06-strategic-context.md` |
| Agent H | Step 8: Hiring signals | `01-company-context.md` | `07-hiring-signals.md` |
| Agent I | Step 9: Financial synthesis + ROI | `01-company-context.md`, `03-traffic-data.md` | `08-financial-profile.md` |

### Wave 3 — Deep Intelligence (parallel, after Wave 1+2)

| Agent | Steps | Reads | Output |
|-------|-------|-------|--------|
| Agent J | Step 12: Investor intelligence | `01-company-context.md` (for ticker) | `11-investor-intelligence.md` |
| Agent K | Step 13: Deep hiring + buying committee | `07-hiring-signals.md` | Appends to `07-hiring-signals.md` |

### Wave 4 — Synthesis (sequential)

Step 14: ICP-to-Priority Mapping. Reads `11-investor-intelligence.md` + `08-financial-profile.md`. Writes to `12-icp-priority-mapping.md`.

### Phase 2: Sequential

Browser interaction cannot be parallelized — run all 20 steps sequentially in Chrome MCP.

### Phase 5: Deliverable Generation (parallel where possible)

| Agent | Deliverable | Depends On |
|-------|------------|------------|
| Agent L | Report (Phase 4) | All scratchpad files |
| Agent M | Deck (Phase 5b) | Report exists |
| Agent N | Landing page (Phase 5a) | Report exists |
| Agent O | AE brief + Signal brief (Phase 5e+5f) | Report exists |

## Process

### Phase 0: Workspace Setup

Before starting, create the scratchpad workspace:
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
├── 09-browser-findings.md
├── 10-scoring-matrix.md
├── 11-investor-intelligence.md
├── 12-icp-priority-mapping.md
├── screenshots/
└── _workspace-manifest.md
```
Create `_workspace-manifest.md` with all steps listed as `[ ] pending`. Update each to `[x] done` as completed. This enables resume if context resets.

### Phase 1: Pre-Audit Research (14 steps — no browser needed except Step 13)

> **Pattern per step**: Run MCP/API call → Write structured results to scratchpad file → Continue to next step. This prevents context overflow from ~35K tokens of raw Phase 1 data.
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

1. **Company Context** — Gather comprehensive company intelligence:
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
   - → Write to `01-company-context.md`

2. **Technology Stack Deep Dive** — Use BuiltWith MCP comprehensively:
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
   - → Write to `02-tech-stack.md`

3. **Traffic & Engagement Deep Dive** — Use SimilarWeb MCP with ALL of these endpoints:
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
   - → Write to `03-traffic-data.md`

4. **Competitor Identification** — Use SimilarWeb to find top 3-5 competitors:
   - `get-websites-similar-sites-agg` — top similar sites by audience overlap
   - `get-websites-keywords-competitors-agg` — keyword competitors (organic)
   - Cross-reference both lists to select the top 3-5 most relevant competitors
   - → Write to `04-competitors.md`

5. **Generate Test Queries** — Based on the company's vertical from Step 1:
   - Look up the prospect's vertical in `vertical-query-library.md`
   - Pull 10-12 queries from the matching vertical row (broad, specific, NLP, typo, non-product, brand)
   - Add 4-6 company-specific queries (flagship products, house brands, specific product names found on site)
   - Total: 14-18 queries (vertically calibrated)
   - → Write to `05-test-queries.md`

6. **Competitor Search Analysis** — For each of the top 3-5 competitors:
   a. Use BuiltWith `domain-lookup` to detect their search provider
   b. Use SimilarWeb `get-websites-traffic-and-engagement` for each competitor (quick check — monthly visits and bounce rate)
   c. **Quick search spot-check** (optional, time permitting): Use Chrome MCP to visit 1-2 competitor sites and run a single typo query. Screenshot if competitor handles it better.
   d. **GOLDEN ANGLE**: If ANY competitor uses Algolia, flag prominently. This is the strongest sales angle.
   e. Create competitor matrix:
      | Competitor | Search Provider | Monthly Traffic | Bounce Rate | Uses Algolia? |
   - → Append to `04-competitors.md`

7. **Strategic Angle Mining** — Use WebSearch to find business context:
   a. **Expansion signals**: New stores, new markets, new product lines?
   b. **Digital transformation**: E-commerce investment, mobile app, headless commerce migration?
   c. **Competitive pressure**: Competitors gaining share?
   d. **Industry trends**: Macro trends affecting this vertical
   e. **Negative signal check**: WebSearch for `"{company} layoffs 2025 2026"` + `"{company} earnings miss"` + `"{company} hiring freeze"`
   f. Output: 2-3 strategic angles (1-sentence insight + 1-sentence search connection each)
   - → Write to `06-strategic-context.md`

8. **Hiring Signal Detection** — Detect active buying signals via job postings:
   - WebSearch: `"{company} careers search engineer"` + `"{company} jobs site search OR relevance OR algolia OR elasticsearch"`
   - Match found titles against `buyer-persona-reference.md` Section 1 (Tier 1/2/3 taxonomy)
   - **Signal interpretation**:
     - 🔥 Strong: Tier 1 titles (VP eComm, Director Digital) = budget likely allocated
     - 🟡 Moderate: Tier 2 titles (Engineering Manager, Product Manager) = team building
     - ⚡ Technical: Tier 3 titles (Senior Engineer, Architect) = may be building in-house
     - ⚠️ Caution: "Search Engineer" or "Relevance Engineer" = possible build-vs-buy
   - → Write to `07-hiring-signals.md`

9. **Financial Context Synthesis + ROI Estimate** — Synthesize financial data with trend visualization:

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
   - Cite benchmarks: Lacoste +37% search revenue, Decathlon +50% search conversion
   - **Guardrails**: Always show formula + inputs + sources. Label as "directional estimate." Never present as guarantee.
   - → Write to `08-financial-profile.md`

10. **Trigger Event Synthesis** — Cross-reference all signals from Steps 1-9:
    - Top 3 **positive trigger events** (e.g., "Search vendor removed + hiring search engineers + digital sales +20%")
    - Any **⚠️ caution signals** (e.g., "Coveo added 4 months ago", "layoffs announced")
    - → Append to `06-strategic-context.md`

11. **Vertical Matching** — Select best case studies for this prospect:
    - Match prospect vertical to `buyer-persona-reference.md` Section 2
    - Select primary + secondary case study
    - If BuiltWith detected a specific competitor vendor, select matching displacement quote from Section 3
    - → Append to `01-company-context.md`

12. **Investor Intelligence** — Extract the company's stated strategic priorities using their OWN words from SEC filings, earnings calls, investor presentations, and investor day transcripts. This is the most powerful sales intelligence because it is unimpeachable — they said it themselves, on the record, to investors.

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

    **For private companies** (fallback):
    - WebSearch: CEO interviews, funding rounds, press releases, conference talks

    **Extraction targets**:
    - 5-8 direct quotes from **any executive** speaking (CEO, CFO, CTO, COO, SVP, VP, or any named speaker) about digital/technology/e-commerce priorities — across MULTIPLE earnings calls and investor presentations
    - Stated e-commerce revenue target or growth goal (forward guidance to Wall Street)
    - Capex allocation: what % goes to digital vs. physical expansion (3-year trend)
    - Risk factors mentioning technology, digital capability, or customer experience gaps
    - Analyst consensus sentiment on digital transformation
    - Any stated timelines for technology modernization or platform migrations
    - Any mention of search, discovery, recommendations, personalization, AI in filings
    - Stated priorities that map to Algolia products (even if not directly about search)

    **Output** → Write to `11-investor-intelligence.md`:
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

13. **Deep Hiring Analysis + Buying Committee Mapping** — Go beyond web search to actually visit the company's careers page.

    **Phase A: Web Search** (from Step 8 data):
    - Additional: `"{company} LinkedIn jobs e-commerce OR digital OR search"`

    **Phase B: Browser Visit** (Chrome MCP):
    - Navigate to company careers page
    - Search for keywords: "search", "relevance", "AI", "machine learning", "e-commerce", "digital", "discovery"
    - Take screenshot of search results
    - Count total roles by category (Engineering, Product, Data, eCommerce, Merchandising)
    - Click into 2-3 most relevant JDs and extract: skills, team, responsibilities, technologies, source URL

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

    **Output** → Append to `07-hiring-signals.md` (includes hiring analysis AND buying committee map with stakeholder table and recommended outreach sequence)

    **Fallback**: If careers page is behind auth, fall back to LinkedIn Jobs + Indeed web searches.

14. **ICP-to-Priority Mapping** (synthesis step, no new API calls) — Cross-reference investor intelligence + financial profile + audit scoring for the most powerful framing: "You said X → We found Y → Algolia does Z"

    **Input files**: `11-investor-intelligence.md`, `08-financial-profile.md`, `10-scoring-matrix.md` (after Phase 3), `01-company-context.md`

    **Process**:
    1. For each stated priority from investor intelligence: find matching Algolia product
    2. For each major audit gap: find supporting investor quote (if available)
    3. Create discovery questions using the company's OWN language

    **Note**: Preliminary mapping after Phase 1. Refined after Phase 3 with specific audit findings.

    **Output** → Write to `12-icp-priority-mapping.md`:
    ```
    ## ICP-to-Priority Mapping — "Speaking Their Language"

    ### Priority-to-Product Map
    | Their Stated Priority | Source | Algolia Solution | Discovery Question |
    |---|---|---|---|
    | "{exact quote from executive}" | Q4 2025 Earnings | NeuralSearch | "You told investors X — we can help with Y" |

    ### Anchor Points for AE
    1. "{Company} told investors {X} — we can accelerate that with {product}"
    ```

### Phase 2: Browser-Based Search Audit (20 steps)

> **SCREENSHOT PERSISTENCE**: Before starting Phase 2, run `mkdir -p screenshots/`. Every screenshot instruction means: (1) Chrome MCP `computer` action `screenshot`, (2) IMMEDIATELY persist to disk in `screenshots/`, (3) VERIFY with `ls -la screenshots/{filename}`.

> **Scratchpad**: Append all observations to `09-browser-findings.md` after each step.

#### Browser Audit Resilience — Anti-Detection Best Practices

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

Open the website in the browser and systematically test:

> **CORE AUDIT (Steps 2a-2l)** — Foundation of every search audit. Execute in full.

#### Step 2a: Initial Observations
- Navigate to the homepage
- Take a screenshot of the homepage with search bar visible
- Note: Is search prominent? Icon or full bar? Position?

#### Step 2b: Empty State Test
- Click on the search bar WITHOUT typing
- Take a screenshot
- Note: Popular searches, trending, recent searches, or nothing?

#### Step 2c: Search-As-You-Type (SAYT) Test
- Type a broad category query letter by letter
- Take a screenshot mid-typing (after 3-4 characters)
- Note: Autocomplete speed, content (products, categories, suggestions), latency

#### Step 2d: Full Search Results Test
- Submit the full query and land on results page
- Take a screenshot
- Note: Result quality, layout, filters/facets, sort options, result count
- Check: At least 4 sort options? Relevant facets with count badges?

#### Step 2e: Typo Tolerance Test
- Search each misspelled query from test list
- Take a screenshot per typo search
- Note: Returns results? "Did you mean..."? Or zero results?

#### Step 2f: Synonym / Colloquial Test
- Search synonym queries
- Note: Does "couch" = "sofa"? Site understands colloquial terms?

#### Step 2g: No Results Test
- Search nonsense query ("asdfghjk")
- Take a screenshot
- Note: Suggestions? Popular products? Just "no results found"?

#### Step 2h: Non-Product Content Test
- Search "return policy", "customer service", "store hours"
- Take a screenshot
- Note: Content/help pages returned? Or only products (or nothing)?

#### Step 2i: Intent Detection Test
- Brand name → redirect to brand page or filter?
- Category name → suggest category?
- Attribute + product ("black chest", "red shoes") → apply filters?

#### Step 2j: Merchandising Consistency Test
- Search a category term, then navigate to same category via menu
- Take screenshots of both views
- Note: Same products? Same order? Different merchandising?

#### Step 2k: Federated Search Check
- During SAYT, note: Products, categories, content pages, brand pages? Or products-only?

#### Step 2l: Mobile Experience
- Resize browser to mobile viewport
- Quick search test
- Note: Mobile search experience quality, responsiveness

> **ALGOLIA VALUE-PROP TESTS (Steps 2m-2t)** — Map to Algolia products for strategic differentiation.

#### Step 2m: Semantic / Natural Language Search (→ Algolia NeuralSearch)
- Test 2-3 NLP queries: conversational, multi-attribute, question-format
- Compare with keyword-equivalent queries
- Take screenshots. Note: Intent understanding or just keyword-match?

#### Step 2n: Dynamic Facets & Filtering (→ Algolia Dynamic Faceting)
- Search 2-3 different categories, observe filter panels
- Take screenshots. Note: Filters change by category context? Or static/generic?

#### Step 2o: Popular & Recent Searches (→ Algolia Query Suggestions)
- Click search bar → popular/trending suggestions?
- Search, navigate away, return → recent searches shown?
- Take screenshots.

#### Step 2p: Dynamic Search Categories (→ Algolia Federated Search + Rules)
- While typing, observe dynamic category suggestions (e.g., "nike" → "Nike Running Shoes")
- Take screenshot if present.

#### Step 2q: Personalization Signals (→ Algolia Personalization)
- Browse a specific category (click 3-4 products), then search a broad term
- Look for: "Recommended for you", personalized carousels, re-ranked results

#### Step 2r: Recommendations / FBT (→ Algolia Recommend)
- Navigate to 2-3 product detail pages
- Take screenshots of recommendation sections
- Note: "Frequently bought together", "Similar items" — relevant or generic?

#### Step 2s: Banners & Merchandising Rules (→ Algolia Rules Engine)
- Search seasonal/campaign terms ("sale", "clearance")
- Search brand name → curated brand experience?
- Take screenshots of promotional content.

#### Step 2t: Analytics Visibility (→ Algolia Analytics)
- Look for: "trending" badges, "bestseller" tags, "most searched" labels
- Note: Visible analytics signals = strength; none = gap

### Screenshot Handling & Persistence

Screenshots are the #1 audit artifact — PROOF that testing was done.

> **FAILURE MODE TO AVOID**: Taking a Chrome MCP screenshot (getting imageId) but never writing to disk.

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

4. **VERIFY file exists**: `ls -la screenshots/{nn}-{slug}.png`
5. **Log to scratchpad** in `09-browser-findings.md`:
   ```
   ### Step 2x: {Test Name}
   - Query: "{query}"
   - Screenshot: screenshots/{nn}-{slug}.png (VERIFIED ON DISK)
   - Result count: {n}
   - Observation: {what happened}
   ```

**Naming Convention**:
```
screenshots/
├── 01-homepage.png
├── 02-empty-state.png
├── 03-sayt-mid-type.png
├── 04-full-results-{query}.png
├── 05-typo-{query}.png
├── 06-synonym-{query}.png
├── 07-no-results.png
├── 08-non-product-{query}.png
├── 09-intent-{query}.png
├── 10-merchandising.png
├── 11-federated.png
├── 12-mobile-{query}.png
├── 13-nlp-{query}.png
├── 14-dynamic-facets.png
├── 15-popular-searches.png
├── 16-dynamic-categories.png
├── 17-personalization.png
├── 18-recommendations.png
├── 19-banners.png
├── 20-analytics.png
```

### Phase 3: Analyze & Score Findings

> Write the complete scoring matrix to `10-scoring-matrix.md`.

For each of the 10 challenge areas, assign severity:

**Core Challenge Areas (1-6)**:

| Area | Severity Criteria |
|------|------------------|
| **Latency** | HIGH: >500ms or full page reload. MEDIUM: 300-500ms. LOW: <300ms |
| **Typo Tolerance** | HIGH: No typo handling. MEDIUM: Partial. LOW: Good tolerance |
| **Query Suggestions / Empty State** | HIGH: Blank empty state + poor no-results. MEDIUM: One lacking. LOW: Both good |
| **Intent Detection** | HIGH: No category/brand/attribute detection. MEDIUM: Partial. LOW: Good |
| **Merchandising Consistency** | HIGH: Major search/browse differences. MEDIUM: Minor. LOW: Consistent |
| **Content Commerce / Front-End UX** | HIGH: No federated search + poor UX. MEDIUM: Some issues. LOW: Good |

**Algolia Value-Prop Areas (7-10)**:

| Area | Severity Criteria |
|------|------------------|
| **Semantic / NLP Search** | HIGH: Pure keyword match. MEDIUM: Partial NLP. LOW: Good semantic understanding |
| **Dynamic Facets & Personalization** | HIGH: Static filters + no personalization. MEDIUM: Some. LOW: Dynamic + visible |
| **Recommendations & Merchandising** | HIGH: No recs + no banners. MEDIUM: Some. LOW: Relevant recs + active rules |
| **Search Intelligence** | HIGH: No trending/popular/analytics signals. MEDIUM: 1-2 present. LOW: 3+ present |

**Overall Score Calculation Formula**:

Use a weighted average where HIGH-severity areas receive 2x weight, penalizing critical gaps:

```
For each of the 10 areas:
  weight = 2.0 if severity == HIGH
  weight = 1.0 if severity == MEDIUM
  weight = 0.5 if severity == LOW

overall_score = sum(score_i × weight_i) / sum(weight_i)
```

**Example**: Scores [8, 8, 4, 4, 9, 2, 2, 5, 2, 4] with severity [LOW, LOW, HIGH, MEDIUM, LOW, HIGH, HIGH, MEDIUM, HIGH, MEDIUM]:
- Numerator: 8(0.5) + 8(0.5) + 4(2) + 4(1) + 9(0.5) + 2(2) + 2(2) + 5(1) + 2(2) + 4(1) = 45.5
- Denominator: 0.5 + 0.5 + 2 + 1 + 0.5 + 2 + 2 + 1 + 2 + 1 = 12.5
- Score: 45.5 / 12.5 = 3.64 → round to 3.6/10

**Always show the formula, inputs, and calculation in `10-scoring-matrix.md`.** This makes the overall score reproducible and verifiable by the fact-check skill.

### Phase 4: Generate Report

Create `{company-name}-search-audit.md` with the following structure:

```markdown
# {Company Name} — Algolia Search Audit
**Date**: {today's date}
**Website**: {url}
**Prepared by**: Algolia

---

## Executive Summary
{2-3 sentence overview of key findings and biggest opportunities}

## Strategic Intelligence

> **Why Now**: {1-sentence timing thesis}

### Timing Signals
| Signal | Evidence | Source | Implication |
|--------|----------|--------|-------------|

### Trigger Events
| Trigger | Opening Line for AE | Source |

### ⚠️ Caution Signals (shown only when detected)

## In Their Own Words (Investor Intelligence)

> {Quote #1}
> — {Speaker Name}, {Title}, {Source + Date}

**What we found**: {matching audit finding}
**Algolia solution**: {product + expected impact}

> {Quote #2}
> — {Speaker Name}, {Title}, {Source + Date}

**What we found**: {matching audit finding}
**Algolia solution**: {product + expected impact}

### Forward Guidance
### Risk Factors Mentioning Digital/Technology

## Company Context
## Technology Stack Deep Dive
## Competitor Landscape
## Financial Profile
## Strategic Leadership
## Buying Committee (Deal Stakeholders)
## Hiring Signal Analysis
## Revenue Impact Estimate
## ICP-to-Priority Mapping

## Search Audit Findings
### Audit Recap (10-row scoring table)
### Detailed Findings (per gap: tested, happened, screenshot, why it matters + SAIM stat, Algolia solution)

## Opportunities
## Algolia Value-Prop Assessment (7-row product table)
## How Algolia Can Help
## Next Steps
```

### Pre-Deliverable Data Refresh (MANDATORY — Prevents Post-Compaction Hallucination)

Before generating EACH deliverable file (Phase 4 and 5a through 5f), you MUST re-read the 5 critical scratchpad files to ensure exact data fidelity. This is NOT optional — context compaction corrupts numerical data in memory. The model will regenerate plausible-looking numbers that are internally consistent (e.g., traffic sources summing to 100%) but factually WRONG.

**Refresh procedure (run before EACH deliverable)**:
1. `Read 03-traffic-data.md` — Capture exact traffic source percentages, demographics (all 6 age brackets)
2. `Read 04-competitors.md` — Capture exact competitor names, bounce rates, traffic volumes, search providers
3. `Read 08-financial-profile.md` — Capture exact revenue, EBITDA, margin zone, ROI figures
4. `Read 10-scoring-matrix.md` — Capture exact scores per area, severity distribution, overall score
5. `Read 11-investor-intelligence.md` — Capture exact quotes with speaker names, titles, and source URLs

**Spot-check verification after writing each deliverable**: After writing each file, grep for 3 values to confirm data fidelity:
- Traffic: grep for the exact Paid Search % from scratchpad 03
- Competitors: grep for the exact first-competitor bounce rate from scratchpad 04
- Financials: grep for the exact revenue figure from scratchpad 08
If ANY spot-check fails, re-read the scratchpad file and correct the deliverable before proceeding.

**Data Table Freeze Rule**: For ANY table containing competitor data (names, traffic, bounce rates, search providers), traffic source breakdowns, demographic distributions, or financial figures — COPY the exact table from the corresponding scratchpad file. Do NOT regenerate tables from memory. Tabular data with parallel columns is especially vulnerable to column-scrambling (values assigned to wrong rows) during context compaction.

**Why this exists**: In the TheRealReal audit (2026-02-23), the content spec was generated after context compaction and contained 12 data errors — traffic sources, demographics, and competitor bounce rates were all regenerated from lossy memory. Competitor bounce rates were scrambled (Fashionphile got 28.8% when it was actually 50.6%). The other 5 deliverables, generated earlier while scratchpad data was in active context, had ZERO errors.

### Phase 5: Generate Deliverables (Brand-Validated)

#### 5a: Landing Page — Dual-View HTML

Read `/algolia-landing` skill before generating. Generate `{company-name}-landing-page.html` with Algolia branding (Sora font, Xenon Blue #003DFF, heading text #23263B, body text #5A5E9A, Algolia Purple #5468FF).

**Tab 1: Executive Summary** (default active): Hero, metrics bar, findings summary cards, before/after, industry stats, strengths, solutions, customer proof, CTA.

**Tab 2: Deep Dive**: Company context (traffic sources, tech stack pills), strategic context cards, competitor search landscape table, Algolia value-prop assessment, audit methodology, detailed gap analysis with ACTUAL SCREENSHOT IMAGES (`<img src="screenshots/{nn}.png">`), scoring table, opportunities, technical fit, next steps timeline.

**Screenshot requirement**: Every gap card MUST embed the actual screenshot with `onerror` fallback. Goal = ZERO missing images.

**Source requirement**: Every data section has source badge. Full Sources & Bibliography at bottom grouped by: Financial, Traffic, Technology, Industry, Competitors, Hiring, Investor, Case Studies.

**Tab UI**: Sticky tabs, URL hash support (#executive, #deep-dive), shared hero/metrics/CTA/footer, responsive.

#### 5b: Presentation Deck (Markdown for Google Slides)

Read `/algolia-deck` skill before generating. Generate `{company-name}-search-audit-deck.md` using **McKinsey Pyramid + Hollywood Cold Open** structure (~30-33 slides).

**Scratchpad Mining Rule**: Every scratchpad file (01-12) MUST produce at least one dedicated slide. Rich data tables, demographics, keyword analysis warrant 2-3 slides. Never compress intelligence into thin summaries. Each finding is a chapter.

**Deck Structure**:

| # | Slide | Content | Scratchpad Source |
|---|-------|---------|-------------------|
| 1 | **Title** | Company store/HQ photo + dark gradient + logo + status badge | — |
| 2 | **The Bottom Line** | 4 bullets: gaps costing $Y, executive quote, competitor angle, pilot impact | All files |
| | **ACT 1: THE COMPANY** | | |
| 3 | **Company snapshot** | Full financial table + enriched executive table with backgrounds | `01-company-context.md` |
| 3a | **Digital traffic deep dive** | Complete traffic analysis, source breakdown, geographic concentration | `03-traffic-data.md` |
| 3b | **Audience DNA** | Demographics, audience overlap, keyword intent patterns | `03-traffic-data.md` |
| 4 | **Tech stack upheaval** | Two-column: REMOVED vs ADDED, "gap in the middle" | `02-tech-stack.md` |
| 5 | **Competitive landscape** | BuiltWith-verified matrix, bounce rate comparisons, golden angle | `04-competitors.md` |
| | **ACT 2: THE EVIDENCE** | | |
| 6 | **Audit overview** | 10-area scoring matrix with color-coded severity | `10-scoring-matrix.md` |
| 7–N | **Gap slides** (1 per gap) | Screenshot embed + test + result + SAIM stat + case study + strategic connection | `09-browser-findings.md` |
| N+1 | **What's working well** | 3-4 strengths with ✅ checkmarks | `10-scoring-matrix.md` |
| | **ACT 3: THE URGENCY** | | |
| N+2 | **In their own words** | Executive quotes from earnings calls/10-K/10-Q → mapped to gaps. Show Speaker + Title. | `11-investor-intelligence.md` |
| N+2a | **SEC risk factors** | Each risk factor mapped to specific audit finding | `11-investor-intelligence.md` |
| N+3 | **Hiring & investment signals** | Role table, salary ranges, JD evidence, build-vs-buy table | `07-hiring-signals.md` |
| N+4 | **Strategic intelligence** | Timing signals, trigger events, timing window | `06-strategic-context.md` |
| | **ACT 4: THE RESOLUTION** | | |
| N+5 | **Connecting the dots** | ICP mapping: "You said X → We found Y → Algolia does Z" | `12-icp-priority-mapping.md` |
| N+6 | **Executive profiles** | Full profile tables per executive with frames | `01-company-context.md` |
| N+7 | **The business case** | ROI with shown math, margin-zone framing | `08-financial-profile.md` |
| N+8 | **Pilot strategy** | 30-day A/B pilot, KPIs, budget by margin zone | `08-financial-profile.md` |
| N+9 | **Next steps + CTA** | Timeline, contact info | — |
| | **APPENDIX** | | |
| A1 | **Sources & Bibliography** | All URLs hyperlinked by category | All files |
| A2 | **Full tech stack** | Complete BuiltWith analysis | `02-tech-stack.md` |
| A3 | **Algolia value-prop assessment** | 7-row product mapping | `10-scoring-matrix.md` |
| A4 | **Full test query matrix** | All queries with results and scores | `05-test-queries.md` |
| A5 | **Full traffic source data** | Keywords, channels, audience overlap | `03-traffic-data.md` |

**Slide Format**: Nebula Blue #003DFF backgrounds for title/dividers/CTA; White for content. Source Sans Pro throughout. Max 4 bullets per slide. Speaker notes (60-90 sec) with key point, strategic connection, transition hook. Source footnotes as `[[N] Source](URL)`.

**Emotional Continuity**: Slide 2 = "wait, what?". Act 2 = mounting concern. Act 2→3 pivot = urgency. "In Their Own Words" = emotional climax. Act 4 = relief through resolution.

#### 5c: Landing Page Content Spec
Generate `{company-name}-landing-page.md` — content specification with all copy, sections, CTAs, A/B test recommendations.

#### 5d: Brand Compliance Validation
Run `/algolia-brand-check` on landing page and deck. Auto-fix below 8/10.

#### 5e: AE Pre-Call Brief
Generate `{company}-ae-precall-brief.md` — AE-facing (NOT for prospect). Every data point hyperlinked.

**Structure**:
1. **Executive Cheat Sheet** (5 bullets): Revenue + margin zone, business model, digital focus, top gap, opportunity + ROI
2. **Financial Profile** with hyperlinked figures
3. **Key Executives** with source links
4. **Recent News & Trigger Events** with source links
5. **Audit Highlights** — top 3 findings with evidence
6. **Discovery Questions** — 6-8 questions from audit findings + margin zone
7. **Stakeholder Targets** — buyer persona mapping
8. **Pilot Strategy** — margin-zone-aware scope, KPIs, budget
9. **Competitive Context** — golden angle if applicable
10. **Speaking Their Language** — discovery questions using company's OWN language from SEC filings/earnings calls, anchored to ICP-to-Priority mapping from Step 14

#### 5f: Strategic Signal Brief
Generate `{company}-strategic-signal-brief.md` — 1-page brief for downstream LLM consumption. Every line is standalone with full context. Sections: 60-Second Story, Timing Signals, In Their Own Words (with Speaker + Title), People, Money, Gaps, Hiring Intelligence, Competitive Landscape, ICP Mapping, The Angle, Sources.

## Output

The audit produces SIX deliverables, all brand-validated:
1. **`{company}-search-audit.md`** — Full audit report with Strategic Intelligence after exec summary
2. **`{company}-landing-page.html`** — Dual-view landing page
3. **`{company}-search-audit-deck.md`** — ~30-33 slide McKinsey Pyramid + Cold Open deck
4. **`{company}-landing-page.md`** — Landing page content spec
5. **`{company}-ae-precall-brief.md`** — AE pre-call brief (internal only)
6. **`{company}-strategic-signal-brief.md`** — Strategic signal brief for downstream LLMs

## Key Reference Data (SAIM - Search Audit Impact Map)

| Issue | Statistic | Algolia Case Study |
|-------|-----------|-------------------|
| No typo tolerance | 1 in 6 queries have typos | Lacoste: 37% increase in search revenue |
| Slow search | 39% leave if too slow; 100ms delay = 1% revenue loss | Under Armour: <20ms latency |
| No federated search | 68% would return to site with good search | Staples: improved content discoverability |
| No personalization | 80% prefer personalized experiences; 10-15% revenue lift | Gymshark: increased conversion |
| Poor relevance | 72% of sites have mediocre/broken relevance | Decathlon: 50% search conversion boost |
| No/bad filters | 43% lack sufficient filtering; filter users convert 2x | Birkenstock: dynamic faceting |
| Missing sort options | 46% missing at least one key sort option | Algolia Sort By Replicas |
| Browse/search inconsistency | Erodes user trust | Algolia unified index |
| No results pages | 12% of searches → no results; 75% leave | Herschel: 80% no-results reduction |
| Out of stock at top | Wastes real estate, frustrates users | Algolia custom ranking |
| Irrelevant recommendations | Recommendations drive 31% of e-commerce revenue | Algolia Recommend ML models |
| Not factoring reviews | 93% say reviews influence purchase | Algolia custom ranking with ratings |

## Execution Checklist Gates (MANDATORY)

### Gate 1: After Phase 1 — Verify before opening browser

**Data Collection (Steps 1-6)**:
- [ ] BuiltWith `domain-lookup` called for prospect → tech categories logged
- [ ] BuiltWith `relationships-api` called → sister sites logged
- [ ] BuiltWith `recommendations-api` called → tech gaps logged
- [ ] BuiltWith `financial-api` called → revenue estimates logged
- [ ] BuiltWith `trust-api` called → trust score logged
- [ ] SimilarWeb traffic called (11 endpoints): traffic-and-engagement, traffic-sources, geography, demographics, keywords, audience-interests, website-rank, referrals, popular-pages, leading-folders, landing-pages
- [ ] SimilarWeb competitors called (2 endpoints): similar-sites, keywords-competitors → top 3-5 identified
- [ ] BuiltWith `domain-lookup` called for EACH competitor → search providers detected
- [ ] SimilarWeb `traffic-and-engagement` called for each competitor

**Enrichment (Steps 7-14)**:
- [ ] Ticker resolved via WebSearch (or noted as private company)
- [ ] Financial data via Yahoo Finance MCP (8+ tools) → 3-year trends, margin zone classified
- [ ] Key executives identified (Tier 1 + Tier 2 + Tier 3 where findable) with backgrounds
- [ ] Vertical classified, test queries generated (14-18 vertically calibrated)
- [ ] Hiring signals checked, strategic angles documented, trigger events synthesized
- [ ] ROI estimate calculated with formula + sources
- [ ] Vertical case studies selected
- [ ] Competitor matrix populated with search providers
- [ ] Investor intelligence collected: SEC EDGAR for 10-K + 10-Q (MD&A, Risk Factors), last 3 quarters of earnings calls, investor presentations → 5-8 executive quotes with speaker names + titles
- [ ] Deep hiring via Chrome MCP: careers page visited, role counts, JD evidence with URLs
- [ ] Buying committee mapped: stakeholder table with names, titles, roles, priorities
- [ ] ICP-to-Priority mapping created (preliminary)
- [ ] Source URLs captured in ALL scratchpad files (01-12)

### Gate 2: After Phase 2 — Verify before scoring

- [ ] All 12 core steps executed (2a-2l)
- [ ] All 8 Algolia value-prop steps executed (2m-2t)
- [ ] **HARD GATE — BLOCKING**: Run `ls screenshots/ | wc -l`.
  - If result < 10: **STOP THE AUDIT. Do NOT proceed to Phase 3.**
  - Print: "⛔ SCREENSHOT GATE FAILED: Only {N} screenshots on disk. Required: 10+."
  - Re-attempt screenshot capture for any missing files.
  - Re-run the count. If STILL < 10, ask the user for guidance before proceeding.
  - This gate exists because Chrome MCP imageIds are SESSION-BOUND and become USELESS after session ends. If screenshots are not on disk NOW, they will NEVER be on disk.
- [ ] **Zero-byte check**: `find screenshots/ -empty | wc -l` must return 0. Delete and re-capture any empty files.
- [ ] **Disk path verification**: Each entry in `09-browser-findings.md` must include `Screenshot: screenshots/{nn}-{slug}.png (VERIFIED ON DISK)`. Entries with Chrome MCP imageIds like `ss_XXXXXXX` instead of file paths indicate persistence failure — fix immediately.

### Gate 3: After Phase 3 — Verify before writing report

- [ ] All 10 areas scored with evidence and screenshot references
- [ ] Overall score calculated with severity counts

### Gate 4: After Phase 4 — Verify before generating deliverables

Report MUST contain ALL sections: Executive Summary, Strategic Intelligence, In Their Own Words (with speaker names + titles), Company Context, Technology Stack, Competitor Landscape, Financial Profile, Strategic Leadership, Buying Committee, Hiring Analysis, Revenue Impact, ICP Mapping, Audit Recap, Detailed Findings, Opportunities, Value-Prop Assessment, How Algolia Helps, Next Steps. Source URLs throughout.

### Gate 5: After Phase 5 — Verify before completion

**File existence**: All 6 files exist.

**Screenshot validation**:
- [ ] `ls screenshots/ | wc -l` → minimum 10
- [ ] Report references screenshots in gap findings
- [ ] Landing page has `<img src="screenshots/"` tags
- [ ] Deck has `![](screenshots/` embeds

**Source citation validation**:
- [ ] Report: `grep -c '](http' {company}-search-audit.md` → minimum 20 hyperlinks
- [ ] Landing page: `grep -c 'source-badge' {company}-landing-page.html` → minimum 8
- [ ] Deck: `grep -c '\[\[' {company}-search-audit-deck.md` → footnoted sources + appendix

**Final validation commands**:
```bash
echo "Screenshots:" && ls screenshots/ | wc -l
echo "Report links:" && grep -c '](http' {company}-search-audit.md
echo "LP source badges:" && grep -c 'source-badge' {company}-landing-page.html
echo "Deck footnotes:" && grep -c '\[\[' {company}-search-audit-deck.md
echo "Zero-byte files:" && find screenshots/ -empty | wc -l
```

## Notes

- Be objective — note both strengths and weaknesses
- Focus on issues Algolia can solve
- Use the prospect's actual product names and categories in examples
- If the site already uses Algolia, focus on optimization opportunities
- Always generate all six deliverables — they are a complete package
- The landing page MUST include dual-view tabbed interface (Executive Summary + Deep Dive)
- The 12 scratchpad files are a BOOK of research intelligence. Each file is a chapter. Never compress multi-dimensional data into thin one-line summaries. Each file deserves dedicated slide(s) with full data tables and strategic insights.
- Title slide MUST have company store/HQ photo + logo + status badge
- Scratchpad → Slide depth: Traffic data → 2 slides. Tech stack → 1 slide. Hiring → 1 enriched slide. Investor intelligence → 2 slides. Executives → 1 enriched slide.
- Every standalone insight in the signal brief must survive context dropping by downstream LLMs
- Deck designed for Google Slides — Visual Notes describe layout, Speaker Notes provide 60-90 sec talking points
- Never compress Phase 1 data into single lines — tech stack, traffic, and competitor landscape deserve full sections with tables
- **Post-compaction data integrity**: After any context compaction mid-audit, treat ALL numerical data in memory as UNVERIFIED. Always re-read scratchpad files before using any data point. The most dangerous hallucination pattern is plausible regeneration — where the model creates internally consistent but factually wrong numbers (e.g., traffic sources that sum to 100% but with wrong individual values).
- **Competitor table scrambling**: LLMs are especially bad at preserving column-row associations in competitor tables after context compaction. The model remembers "4 competitors had bounce rates in the 28-51% range" but assigns values to the wrong company names. ALWAYS copy competitor tables from scratchpad 04, never regenerate.
- **Browser observations are exact**: When the browser shows "10,000+ New Items", record exactly "10,000+" — do not round up, generalize, or inflate to "30,000+". [OBSERVED] values are verbatim.

## MCP Server Integration (Required Tools)

The audit MUST use these MCP servers. Always prefer MCP data over WebSearch.

### 1. BuiltWith MCP (Phase 1 steps 1, 2, 6)
| Endpoint | Usage |
|----------|-------|
| `domain-lookup` | Prospect + each competitor: search provider, e-commerce platform, analytics, personalization, removed/added tech |
| `relationships-api` | Sister/related sites |
| `recommendations-api` | Technology gap analysis |
| `financial-api` | Revenue estimates, employee count, funding (cross-reference Yahoo Finance) |
| `social-api` | Social profile URLs (LinkedIn, Twitter, Facebook) |
| `trust-api` | Domain trust score, domain age |
| `keywords-api` | Meta keywords, page titles (SEO focus) |
| Fallback: SimilarWeb `get-website-content-technologies-agg` | If BuiltWith credits exhausted |

### 2. SimilarWeb MCP (Phase 1 steps 3, 4, 6)
| Endpoint | Usage |
|----------|-------|
| `get-websites-traffic-and-engagement` | Visits, bounce, engagement (prospect + each competitor) |
| `get-websites-traffic-sources` | Channel breakdown |
| `get-websites-geography-agg` | Top countries |
| `get-websites-demographics-agg` | Age/gender |
| `get-website-analysis-keywords-agg` | Top keywords (branded vs non-branded) |
| `get-websites-audience-interests-agg` | Audience interests |
| `get-websites-website-rank` | Global rank + category rank |
| `get-websites-referrals-agg` | Incoming referral sites |
| `get-pages-popular-pages-agg` | Top pages by traffic share |
| `get-pages-leading-folders-agg` | Top URL folders (site architecture) |
| `get-websites-landing-pages-agg` | Top organic/paid landing pages |
| `get-websites-similar-sites-agg` | Competitor identification |
| `get-websites-keywords-competitors-agg` | Keyword competitors |
| `get-website-content-technologies-agg` | Fallback for BuiltWith |
| Use `country: "ww"` if `"us"` errors | |

### 3. Yahoo Finance MCP (Phase 1 steps 1, 9, 12)
| Tool | Usage |
|------|-------|
| `get_stock_info(ticker)` | Company overview, market cap, employee count |
| `get_financial_statement(ticker, "income_stmt")` | 3-year revenue, net income, EBITDA |
| `get_financial_statement(ticker, "quarterly_income_stmt")` | Most recent quarterly trajectory |
| `get_financial_statement(ticker, "balance_sheet")` | Cash, debt, total assets |
| `get_financial_statement(ticker, "cashflow")` | Free cash flow, capex allocation |
| `get_recommendations(ticker, "recommendations")` | Analyst consensus |
| `get_recommendations(ticker, "upgrades_downgrades")` | Recent rating changes |
| `get_yahoo_finance_news(ticker)` | Latest news, earnings reactions |
| `get_historical_stock_prices(ticker, period="2y")` | 2-year price trajectory |
| `get_holder_info(ticker, "institutional_holders")` | Top institutional investors |
| **Ticker resolution**: WebSearch first — Yahoo Finance MCP has no search tool | |
| **Fallback**: Private company → WebSearch for all financial data | |

### 4. SEC EDGAR MCP (Phase 1 step 12)
| Tool | Usage |
|------|-------|
| `search_filings(ticker, '10-K')` | Find annual filing accession number |
| `search_filings(ticker, '10-Q')` | Find quarterly filing accession number |
| `get_section_text(accession, 'MD&A')` | Item 7 (10-K) / Item 2 (10-Q): digital strategy, e-commerce priorities |
| `get_section_text(accession, 'Risk Factors')` | Item 1A: technology gaps, competition, cybersecurity |
| `get_section_text(accession, 'Business Description')` | Item 1: business overview |
| **Source URLs**: Point to `sec.gov` filing URLs | |
| **Fallback**: Private company or MCP unavailable → WebSearch + WebFetch | |

### 5. Chrome MCP (Phase 1 step 13 + Phase 2)
All browser-based testing. Use real Chrome browser profile — NOT headless.
- Phase 1 Step 13: Visit careers page for deep hiring analysis
- Phase 2: All 20 audit test steps
- Every screenshot persisted to disk immediately
- Follow Browser Audit Resilience guidelines for anti-detection

### 6. WebSearch + WebFetch (Phase 1 various steps)
Used ONLY where no structured MCP endpoint exists:
- Company overview narrative (founding story, business model)
- Executive research (names, titles, backgrounds)
- Hiring signals (job postings, careers page URL discovery)
- Strategic angles (news, expansion, competitive pressure)
- Earnings call transcripts (Seeking Alpha, Motley Fool, IR pages)
- Investor presentations and investor day transcripts
- Ticker resolution
- Industry context and vertical trends
- Negative signal checks

**Ticker Resolution Rule**: At audit start, resolve ticker via WebSearch. Use for ALL Yahoo Finance + SEC EDGAR calls. If no ticker found (private), note in manifest and fall back to WebSearch.

All tools used automatically — no user prompting needed. If any tool is unavailable, note the gap and proceed.

## Default Output Workflow

After completing Phase 3 (Analyze & Score):
1. **Refine Step 14**: Re-read `10-scoring-matrix.md` and update ICP-to-Priority Mapping with audit findings mapped to investor quotes.
2. **Phase 4**: Write report. Hyperlink every data point. (Run Pre-Deliverable Data Refresh before writing.)
3. **Phase 5c**: Write content spec IMMEDIATELY after report — both share the same data tables and the scratchpad data is still in active context. (Run Pre-Deliverable Data Refresh before writing.)
4. **Phase 5a**: Write landing page HTML with evidence cards, screenshots, source badges. (Run Pre-Deliverable Data Refresh before writing.)
5. **Phase 5b**: Write deck (~30-33 slides). Read ALL scratchpad files first. Each file = at least one slide. Title slide with company photo + logo + status badge. Source footnotes + appendix. (Run Pre-Deliverable Data Refresh before writing.)
6. **Phase 5d**: Run `/algolia-brand-check` — auto-fix below 8/10.
7. **Phase 5e**: Write AE brief with "Speaking Their Language" section. (Run Pre-Deliverable Data Refresh before writing.)
8. **Phase 5f**: Write signal brief with all standalone insights and source URLs. (Run Pre-Deliverable Data Refresh before writing.)

**Ordering rationale**: The content spec (5c) MUST be generated right after the report (Phase 4) while scratchpad data is still in the active context window. Generating it last — after deck, HTML, and briefs — risks context compaction corrupting numerical data. The TheRealReal audit proved this: the content spec was the last file generated and contained 12 data errors while all other files had zero.

All files written to same working directory. Every deliverable uses the same data, findings, screenshots, and SAIM stats. The Pre-Deliverable Data Refresh MUST run before each file regardless of order.
