---
name: algolia-live-signals
description: Apify-powered live intelligence for Algolia Search Audits. Scrapes hiring signals (LinkedIn Jobs), social signals (LinkedIn + Twitter/X posts), and news signals (Google News). Replaces Chrome MCP for hiring data. Adds social + news as net-new capabilities. Called by algolia-audit-research after company context is established.
---

# Algolia Live Signals — Apify Intelligence Layer

Sub-skill of the Algolia Search Audit system. Runs 3 phases of live data collection using Apify actors.

**Invoke:** `/algolia-live-signals {company-slug}`

**Called from:** `algolia-audit-research` after Step 2 (tech stack), before Step 6 (strategic context).

**Requires:**
- `01-company-context.md` must exist (for company name, domain, LinkedIn URL, Twitter handle)
- Apify MCP must be active (`mcp__apify__call-actor`, `mcp__apify__get-actor-output`)
- Internet access

**Produces:**
- `07-hiring-signals.md` — enriched from LinkedIn Jobs (replaces Chrome MCP version)
- `09b-social-signals.md` — LinkedIn + Twitter/X posts with relevance scoring
- `09c-news-signals.md` — Google News articles with signal tagging

---

## Parameters (hardcoded defaults)

```
HIRING_LOOKBACK_DAYS    = 90      # jobs older than 90 days excluded
SOCIAL_LOOKBACK_DAYS    = 30      # posts older than 30 days excluded
NEWS_LOOKBACK_DAYS      = 60      # news older than 60 days excluded
MAX_JOBS                = 50      # LinkedIn job results cap
MAX_LI_POSTS            = 30      # LinkedIn company posts cap
MAX_TWEETS              = 30      # Twitter/X posts cap
MAX_NEWS                = 20      # Google News articles cap
SIGNAL_MIN_RELEVANCE    = 6       # 1-10 score; below 6 = excluded from output
SOCIAL_MIN_ENGAGEMENT   = 20      # minimum reactions OR 5+ comments to qualify
```

---

## ICP Role Taxonomy

Use these to classify and score job postings. Roles are tiered by Algolia sales importance.

### Tier 1 — Economic Buyers 🔴 HIGH SIGNAL
```
VP / Director / Head of: Digital Commerce, eCommerce, Digital Products, Digital Transformation
Chief Digital Officer (CDO)
Chief Technology Officer (CTO) — if at a digital-first company
VP / Director of Product (eCommerce / Digital)
SVP Digital Experience
```

### Tier 2 — Technical Buyers 🔴 HIGH SIGNAL
```
Senior / Staff / Principal Engineer: eCommerce, Platform, Search, Backend
Solutions Architect: eCommerce / Digital / Salesforce Commerce Cloud / Shopify / Magento
Technical Lead: SFCC / Headless Commerce / Composable Commerce
Search Engineer / Search Relevance Engineer
Platform Engineer (eCommerce-focused)
Full Stack Engineer with eCommerce keywords in JD
```

### Tier 3 — Champions 🟡 MEDIUM SIGNAL
```
Head / Director / Manager: Performance Marketing, Paid Media, Growth Marketing
Head / Director / Manager: Digital Merchandising, eCommerce Merchandising, Visual Merchandising
Conversion Rate Optimization (CRO) Manager / Analyst
Digital Analytics Manager / Director
SEO / SEM Manager (if JD mentions "on-site search" or "product discovery")
Customer Experience Manager / Director
UX/CX Designer (if JD mentions "search UX" or "product discovery")
Head of Personalization / Customer Data
```

### Tier 4 — Weak Signal 🟢 CONTEXT ONLY
```
General Software Engineer (no eCommerce context)
Data Scientist (no search/personalization context)
Product Manager (no digital commerce context)
```

### JD Keyword Boosters (upgrade tier by 1 if found in job description)
```
HIGH BOOST: "search", "search relevance", "NLP", "natural language", "personalization",
            "recommendation engine", "product discovery", "Algolia", "Elasticsearch",
            "composable commerce", "headless commerce", "AI-powered search"

MEDIUM BOOST: "conversion rate", "A/B testing", "experimentation platform",
              "catalog management", "merchandising rules", "faceted search",
              "typeahead", "autocomplete", "customer experience optimization"
```

---

## Phase 1: Hiring Intelligence

**Actor:** `curious_coder/linkedin-jobs-scraper`
**Cost:** ~$0.05 for 50 jobs
**Purpose:** Find what ICP roles the company is actively hiring — reveals buying committee gaps, technical investment signals, and urgency indicators.

### Step 1a: Extract company info from 01-company-context.md
Read the file to get:
- `COMPANY_NAME` — exact legal name
- `DOMAIN` — e.g. brooksrunning.com
- `LINKEDIN_URL` — company LinkedIn page (if available)

### Step 1b: Run LinkedIn Jobs scraper
```
Actor: curious_coder/linkedin-jobs-scraper
Input:
  keywords: "{COMPANY_NAME}"
  location: ""          # empty = worldwide
  limit: 50
  datePosted: "past-3-months"
```

If LinkedIn URL is known, also run with:
```
  companyName: "{COMPANY_NAME}"
  limit: 50
```

### Step 1c: Score and classify each job

For each job returned:
1. Assign tier (1-4) based on ICP Role Taxonomy above
2. Check JD text for keyword boosters → upgrade tier if found
3. Calculate `signal_score`:
   - Tier 1 = base 9
   - Tier 2 = base 7
   - Tier 3 = base 5
   - Tier 4 = base 2
   - +1 if HIGH BOOST keyword in JD
   - +0.5 if MEDIUM BOOST keyword in JD
   - Cap at 10

4. Flag as `VACANCY_SIGNAL` if:
   - Role is Tier 1 or 2 AND score ≥ 7
   - These are the most actionable — Technical/Economic buyer roles are OPEN

### Step 1d: Write 07-hiring-signals.md

```markdown
# {Company} — Hiring Signals (Apify/LinkedIn)
**Source**: LinkedIn Jobs via Apify (curious_coder/linkedin-jobs-scraper)
**Scraped**: {today}
**Lookback**: 90 days
**Total jobs found**: {N}
**ICP roles (Tier 1-3)**: {N}

## 🔴 Critical Vacancy Signals
{List Tier 1 + 2 roles with signal_score ≥ 7}
For each:
- **{Role Title}** — {Department}
- Posted: {date} | URL: {job_url}
- Signal: {why this matters for Algolia}
- JD Keywords Found: {list of ICP keywords}
- Salary: {if available}

## 🟡 Champion Signals (Tier 3)
{List Tier 3 roles}

## 🟢 Context Roles (Tier 4)
{Brief count only, no detail}

## Buying Committee Assessment
{Based on what's open/closed, assess:}
- Economic Buyer: {name if found, or "Not identified — private company"}
- Technical Buyer: {VACANT / identified}
- Champion roles: {what exists}
- Build vs Buy signal: {inferred from JD language}

## ICP Role Count Summary
| Tier | Count | Signal |
|------|-------|--------|
| 1 — Economic Buyer | N | 🔴/🟡/⚫ |
| 2 — Technical Buyer | N | 🔴/🟡/⚫ |
| 3 — Champion | N | 🟡/🟢/⚫ |

## Sources
All job URLs are direct LinkedIn links — fully referenceable.
```

---

## Phase 2: Social Signals

**Actors:**
- `harvestapi/linkedin-company-posts` — LinkedIn posts
- `apidojo/tweet-scraper` — Twitter/X posts

**Cost:** ~$0.06 for 30 LinkedIn posts + 30 tweets
**Purpose:** Find what the company is publicly talking about — reveals strategic priorities, pain points, and executive messaging that creates Algolia entry points.

### Step 2a: Extract social handles
From `01-company-context.md` get:
- `LINKEDIN_COMPANY_URL` — e.g. linkedin.com/company/brooks-running
- `TWITTER_HANDLE` — e.g. @brooksrunning

If not in scratchpad, derive from domain: try `linkedin.com/company/{company-slug}` and `@{company-slug}` on Twitter.

### Step 2b: Scrape LinkedIn company posts
```
Actor: harvestapi/linkedin-company-posts
Input:
  url: "{LINKEDIN_COMPANY_URL}"
  maxPosts: 30
  includeComments: false
  includeReactions: false
```

### Step 2c: Scrape Twitter/X posts
```
Actor: apidojo/tweet-scraper
Input:
  searchTerms: ["from:{TWITTER_HANDLE}"]
  maxTweets: 30
  since: "{90_DAYS_AGO_DATE}"
```

### Step 2d: Score each post for Algolia relevance

For each post, assign `relevance_score` (1-10) and `signal_category`:

| Score | Meaning | Criteria |
|-------|---------|----------|
| 9-10 | DIRECT | Mentions search, discovery, personalization, conversion, NLP, product findability |
| 7-8 | STRONG | International expansion, tech investment, AI initiative, customer experience, new platform |
| 5-6 | MODERATE | New product launch, major partnership, CX initiative, digital transformation |
| 3-4 | WEAK | Brand marketing, event announcements, culture posts |
| 1-2 | NOISE | Contests, sports results, unrelated content |

Signal categories:
- `SEARCH_PAIN` — directly mentions search/discovery problems
- `TECH_INVESTMENT` — AI, machine learning, platform modernization
- `INTERNATIONAL_EXPANSION` — new markets, multi-language, global growth
- `CONVERSION_FOCUS` — conversion rate, AOV, revenue per visitor
- `CX_INITIATIVE` — customer experience, UX improvement
- `EXEC_PRIORITY` — CEO/C-suite post about digital strategy
- `PRODUCT_LAUNCH` — new catalog items, product lines (merchandising signal)
- `COMPETITOR_SIGNAL` — mentions competitive pressure

Apply `SOCIAL_MIN_ENGAGEMENT` filter: exclude posts with < 20 reactions AND < 5 comments.

Only include posts with `relevance_score ≥ SIGNAL_MIN_RELEVANCE (6)`.

### Step 2e: Write 09b-social-signals.md

```markdown
# {Company} — Social Signals (Apify)
**Sources**: LinkedIn Company Posts + Twitter/X
**Scraped**: {today}
**Lookback**: 30 days (posts) / 90 days (pattern analysis)
**Total posts scraped**: {N LinkedIn} + {N Twitter}
**Qualifying signals (score ≥ 6)**: {N}

## Top Signals by Relevance

### 🔴 Direct Algolia Signals (Score 9-10)
{List highest-relevance posts}
For each:
- **Platform**: LinkedIn / Twitter
- **Date**: {date}
- **Author**: {name + title if exec post}
- **Post**: "{text truncated to 200 chars}"
- **Engagement**: {reactions} reactions · {comments} comments
- **Signal**: {signal_category} — {1 line why this matters for Algolia}
- **Source**: {direct URL — ALWAYS include}

### 🟡 Strong Signals (Score 7-8)
{Same format}

### 🟢 Context Signals (Score 5-6)
{Brief list only}

## Pattern Analysis (90-day themes)
{3-5 bullet points on what topics the company keeps returning to}
- Theme 1: ...
- Theme 2: ...

## Exec Posts (prioritized)
{Any posts from C-suite / VP level — flag separately}

## Platform Notes
- LinkedIn: {N qualifying posts from {N} scraped}
- Twitter/X: {N qualifying posts from {N} scraped}
- Handle used: {handles confirmed or not found}
```

---

## Phase 3: News Signals

**Actor:** `data_xplorer/google-news-scraper-fast`
**Cost:** ~$0.02 for 20 articles
**Purpose:** Catch leadership changes, funding events, product launches, tech announcements, competitive moves in the press.

### Step 3a: Run Google News scraper — multiple queries
Run 3 separate queries, max 7 results each (= ~20 total):

```
Query 1: "{COMPANY_NAME} digital OR ecommerce OR technology OR search"
Query 2: "{COMPANY_NAME} executive OR leadership OR hire OR appoint"
Query 3: "{COMPANY_NAME} launch OR expansion OR international OR AI"

Actor: data_xplorer/google-news-scraper-fast
Input per query:
  query: "{query}"
  maxItems: 7
  language: "en"
```

### Step 3b: Classify each article

| Category | Keywords | Algolia Signal |
|----------|----------|---------------|
| LEADERSHIP_CHANGE | hired, appointed, named, joins as, new CEO/CTO/CDO | New exec = tech review window |
| FUNDING_EVENT | raised, funding, investment, Series, IPO, M&A | Budget signal |
| TECH_INVESTMENT | AI, machine learning, platform, modernization, migration | Tech spend appetite |
| PRODUCT_LAUNCH | launches, introduces, new product, new category | Catalog growth = search complexity |
| INTERNATIONAL | expansion, global, enters market, international | Multi-language search need |
| DIGITAL_INITIATIVE | digital, ecommerce, online, D2C, omnichannel | Digital investment signal |
| COMPETITIVE_PRESSURE | loses to, faces competition, market share | Urgency signal |

Exclude: articles older than `NEWS_LOOKBACK_DAYS` (60 days).

### Step 3c: Write 09c-news-signals.md

```markdown
# {Company} — News Signals (Apify/Google News)
**Source**: Google News via Apify (data_xplorer/google-news-scraper-fast)
**Scraped**: {today}
**Lookback**: 60 days
**Queries run**: 3
**Articles found**: {N}

## Signal Articles (by category)

### 🔴 Immediate Action Signals
{LEADERSHIP_CHANGE + FUNDING_EVENT articles}
For each:
- **{Headline}**
- Source: {publication} | Date: {date}
- Category: {signal_category}
- Algolia angle: {1 line why this creates an opening}
- URL: {direct article URL — ALWAYS include}

### 🟡 Strategic Signals
{TECH_INVESTMENT + DIGITAL_INITIATIVE + INTERNATIONAL articles}

### 🟢 Context Signals
{PRODUCT_LAUNCH + COMPETITIVE_PRESSURE}

## Summary
{3 bullet points: what happened in the last 60 days that matters for Algolia}
```

---

## Error Handling

- If actor returns 0 results: log "No results from {actor} for {company}" and continue to next phase
- If LinkedIn URL not found: skip LinkedIn jobs, note in output
- If Twitter handle not found: try searching `"{COMPANY_NAME}" Twitter` to find handle, note if still not found
- If any phase fails entirely: write the scratchpad file with the error logged, don't block other phases

---

## Output Summary

After all 3 phases complete, print:

```
✓ Phase 1 Hiring: {N} ICP roles found, {N} vacancy signals flagged
  → 07-hiring-signals.md updated
✓ Phase 2 Social: {N} qualifying posts ({N} LinkedIn + {N} Twitter)
  → 09b-social-signals.md written
✓ Phase 3 News: {N} signal articles found
  → 09c-news-signals.md written

Top 3 signals for this audit:
1. {most important signal found}
2. {second signal}
3. {third signal}
```

---

## Integration with algolia-audit-research

In `algolia-audit-research` SKILL.md, replace Step 8 (Chrome MCP hiring) with:

```
Step 8: Run /algolia-live-signals {slug}
  - Produces 07-hiring-signals.md (replaces Chrome MCP version)
  - Produces 09b-social-signals.md (new)
  - Produces 09c-news-signals.md (new)
  - These feed directly into JSON generation at Step 5a
```

New JSON fields populated by this sub-skill:
- `hiring.buying_committee[]` — from Phase 1
- `hiring.total_open_roles` — from Phase 1
- `intelligence_signals[]` — enriched with Phase 2 + 3 data
  - social posts → type: "media" or "exec"
  - news articles → type: "funding", "media", or "industry-opp"

---

## Cost Estimate per Audit

| Phase | Actor | Max Results | Cost |
|-------|-------|-------------|------|
| Hiring | curious_coder/linkedin-jobs-scraper | 50 jobs | ~$0.05 |
| LinkedIn Posts | harvestapi/linkedin-company-posts | 30 posts | ~$0.06 |
| Twitter/X | apidojo/tweet-scraper | 30 tweets | ~$0.01 |
| News | data_xplorer/google-news-scraper-fast | 20 articles | ~$0.02 |
| **Total** | | | **~$0.14/audit** |

Well within Apify free tier for low-volume usage. ~$14 per 100 audits at scale.
