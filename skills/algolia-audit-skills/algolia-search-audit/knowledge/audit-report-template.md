# Audit Report Template Structure (v2.6)

> **SOURCE CITATION RULE**: Every data point in the report MUST include an inline hyperlink to its source. Format: `**$269.9B** ([FY2025 10-K](https://...))`  or `**100.9M visits/mo** ([SimilarWeb](https://similarweb.com/website/costco.com))`. No unsourced claims. This applies to financials, traffic data, tech stack data, industry stats, case studies, and executive information.

## Report Sections (in order)

### 1. Cover
- Company name + "Search Audit"
- Date
- Algolia branding

### 1b. Executive Summary
- 4-6 bullet overview: who they are, what we found, biggest gaps, opportunity size
- **"Why Now" callout**: All timing signals in bold — leadership transitions, tech removals, expansion signals, earnings guidance
- Overall score (X/10) with one-line interpretation
- Source: Links to detailed sections below

### 2. Strategic Intelligence (ELEVATED — immediately after Executive Summary)

> **PLACEMENT RATIONALE**: This section comes first because it frames EVERYTHING that follows. When downstream LLMs (NotebookLM, Gamma) process this report, they summarize from the top — strategic intelligence must be at the top to survive.

#### 2a. Timing Signals
| Signal | Evidence | Source | Implication |
|--------|----------|--------|-------------|
| {e.g., "RichRelevance removed"} | {BuiltWith shows removal date} | [BuiltWith](url) | {Vacuum for Algolia Recommend} |
| {e.g., "Digital sales +20.5% YoY"} | {10-K or earnings data} | [FY2025 10-K](url) | {Search quality increasingly critical} |

**Opening lines for AE**: For each timing signal, provide a conversation opener:
- "We noticed {signal} — how is the team approaching {capability}?"

#### 2b. Key Executives
| Name | Title | Since | Background | Entry Angle | Source |
|------|-------|-------|------------|-------------|--------|
| {name} | {title} | {date} | {e.g., "Ex-Kroger digital"} | {e.g., "Knows digital retail pain"} | [source](url) |

#### 2c. Financial Profile
| Metric | Value | Source |
|--------|-------|--------|
| Revenue | {e.g., $269.9B FY2025} | [10-K](url) |
| Net Income | {e.g., $7.4B} | [10-K](url) |
| EBITDA Margin | {e.g., ~4-5%} | {derived} |
| Public/Private | {e.g., Public (NASDAQ: COST)} | — |

**Margin Zone**: {🔴 Red (≤10% EBITDA) / 🟡 Yellow (10-20%) / 🟢 Green (>20%)}
**Sales motion implication**: {e.g., "Red zone = thin margins. Prioritize fast ROI, tight pilot scope (<$100K), clear KPIs tied to revenue lift or conversion improvement."}

Confidence: Unmarked = 2+ sources agree. ⚠️ = single source or sources disagree.

#### 2d. Trigger Events & Caution Signals

**Positive Triggers** (conversation openers for AE):
1. {e.g., "RichRelevance recommendation engine removed — vacuum for Algolia Recommend"} ([BuiltWith](url))
2. {e.g., "Digital sales surging +20.5% YoY — search quality increasingly critical"} ([10-K](url))
3. {e.g., "28 new warehouses in FY2026 — catalog expansion makes search harder"} ([earnings call](url))

**⚠️ Caution Signals** (shown only when detected):
- {e.g., "Coveo detected as ADDED 4 months ago — prospect may have recently committed to a competitor"} ([BuiltWith](url))

#### 2e. Revenue Impact Estimate
```
Revenue Addressable by Search = Total Revenue × Digital Share × Search-Driven Share
Estimated Impact = Revenue Addressable × Improvement Benchmark

{Company}:
  Total Revenue: ${X}B (from Financial Profile) [source](url)
  Digital Share: ~{X}% [source](url)
  Search-Driven Share: ~15% (industry benchmark: 15-30% of e-commerce revenue)
  Revenue Addressable: ${calc}

  Conservative (5% improvement): ~${X}/year
  Moderate (10% improvement): ~${X}/year

  Benchmarks: Lacoste +37% search revenue, Decathlon +50% search conversion
```
*Estimate based on public data and published Algolia benchmarks. Individual results vary. Directional estimates for conversation purposes only.*

### 3. In Their Own Words — Investor Intelligence (v2.6)

> **PURPOSE**: Direct quotes from CEO/CFO earnings calls and 10-K filings, each mapped to a specific audit finding. This is the most powerful sales material because it uses the prospect's OWN stated priorities.

> "{CEO quote about digital priority}"
> — {Name}, {Title}, {Source + Date}
> Source: [{filing name}](url)

**What we found**: {matching audit finding from Phase 2/3}
**Algolia solution**: {product + expected impact}

> "{CFO quote about e-commerce investment}"
> — {Name}, {Title}, {Source + Date}
> Source: [{filing name}](url)

**What we found**: {matching audit finding}
**Algolia solution**: {product + expected impact}

*Repeat for 2-4 quotes. Each quote must have: exact text, attribution, source URL, mapped finding, Algolia solution.*

**If private company**: Use press releases, CEO interviews, or conference talks instead. Same format. Note "Source: {publication}" instead of SEC filing.

**If no investor data found**: Skip this section gracefully. Note "Limited public investor data available" and proceed.

### 4. Company Context
- Industry, business model, key differentiators
- Traffic data ([SimilarWeb](url)): monthly visits, bounce rate, pages/visit, avg duration, top geos, demographics, traffic sources
- Recent news and business developments (with source links)

### 4b. Competitor Landscape
| Competitor | Search Provider | Monthly Traffic | Uses Algolia? | Source |
|-----------|----------------|-----------------|---------------|--------|
| {competitor1} | {provider} | {visits} | Yes/No | [BuiltWith](url) |

**Key Insight**: If competitor uses Algolia → "Competitor X already uses Algolia, demonstrating that modern AI-powered search is a competitive requirement in this vertical." If none use Algolia → "None of the top competitors have invested in modern search — {company} has an opportunity to leapfrog."

### 4c. Technology Stack Deep Dive
Full BuiltWith output organized by category:
| Category | Technology | Status | Source |
|----------|-----------|--------|--------|
| Search | {provider or "None detected"} | {Active/Removed} | [BuiltWith](url) |
| E-commerce | {platform} | Active | [BuiltWith](url) |
| CDN | {provider} | Active | [BuiltWith](url) |
| Analytics | {provider} | Active | [BuiltWith](url) |
| Personalization | {provider} | Active/Removed | [BuiltWith](url) |
| Recommendations | {provider} | Active/Removed | [BuiltWith](url) |
| CMS | {provider} | Active | [BuiltWith](url) |

**Search Provider Analysis**: {detailed analysis of current search state — what's detected, what's been removed, what the gap is}

**Relationships** (sister sites from BuiltWith relationships-api): {related domains}

### 5. Hiring Signal Analysis (v2.6 — Deep)

> **NOTE**: This section replaces the shallow v2.4 "Hiring Signals" (which was just "detected/not detected"). v2.6 visits the actual careers page and analyzes job descriptions.

#### Role Count by Category
| Category | Open Roles | Notable Titles | Source |
|----------|-----------|----------------|--------|
| Engineering | {count} | {titles} | [{careers page}](url) |
| Product | {count} | {titles} | [{careers page}](url) |
| Data/ML | {count} | {titles} | [{careers page}](url) |
| eCommerce | {count} | {titles} | [{careers page}](url) |
| Merchandising | {count} | {titles} | [{careers page}](url) |
| **Total relevant** | **{count}** | | |

#### Job Description Evidence
**Role: {title}** (posted {date}) — [Link](url)
- Required: {skills mentioning search/AI/relevance}
- Team: {team name}
- Key quote from JD: "{relevant excerpt}"

#### Signal Interpretation
- **Signal strength**: {🔥 Strong / 🟡 Moderate / ⚡ Technical / ⚠️ Caution / ❄️ No Signal}
- **Build-vs-buy risk**: {Low/Medium/High} — based on: {JD language, team structure, tech mentions}
- **Timing signal**: {e.g., "3 new search roles posted in last 30 days = active buying cycle"}

**If careers page inaccessible**: Fall back to LinkedIn Jobs + Indeed web searches. Note limitation.

### 6. ICP-to-Priority Mapping — "Speaking Their Language" (v2.6)

> **PURPOSE**: Cross-references investor intelligence + financial profile + audit findings to create the ultimate sales framing.

| Their Stated Priority | What We Found | Algolia Solution | Discovery Question |
|---|---|---|---|
| "{quote from 10-K/earnings}" ([source](url)) | {specific audit finding} | {Algolia product} | "{discovery question using their language}" |

**Anchor Points for AE**:
1. "{Company} told investors {X} — we can help accelerate that with {Algolia product}"
2. "{Company}'s 10-K identifies {risk} — our audit confirms this: {finding}"
3. "{CFO} said {quote about efficiency} — Algolia delivers {metric} improvement at {pilot cost}"

### 7. Search Audit Recap
Summary table of findings across the 10 challenge areas:
| Area | Finding | Severity | Source |
|------|---------|----------|--------|
| Latency | [description] | High/Medium/Low | Screenshot + test |
| Typo Tolerance | [description] | High/Medium/Low | Screenshot + test |
| Query Suggestions / Empty State | [description] | High/Medium/Low | Screenshot + test |
| Intent Detection | [description] | High/Medium/Low | Screenshot + test |
| Merchandising Consistency | [description] | High/Medium/Low | Screenshot + test |
| Content Commerce / Front-End UX | [description] | High/Medium/Low | Screenshot + test |
| Semantic / NLP Search | [description] | High/Medium/Low | Screenshot + test |
| Dynamic Facets & Personalization | [description] | High/Medium/Low | Screenshot + test |
| Recommendations & Merchandising | [description] | High/Medium/Low | Screenshot + test |
| Search Intelligence | [description] | High/Medium/Low | Screenshot + test |

### 8. Detailed Findings (one section per gap found)
Each finding section includes:
- **Gap Title**: e.g., "Gap #1: No Typo Tolerance"
- **Description**: What was tested, what happened, what should happen
- **Screenshots**: Side-by-side or annotated screenshots showing the issue
- **Why It Matters**: Industry stat from SAIM ([source]) + business impact. **Algolia proof point**: {vertically-matched case study with named customer and specific metric from buyer-persona-reference.md} ([source])
- **Algolia Solution**: How Algolia addresses this specific gap
- **Strategic Connection**: How this gap relates to the company's stated priorities (from Section 3)

### 9. Opportunity Slides
For each opportunity area where the prospect can improve:

#### Speed
- Current latency measurement vs Algolia's <20ms
- Why it matters: 39% of shoppers leave if search is slow ([Baymard Institute](url))

#### Typo Tolerance
- Examples of failed typo queries
- Why it matters: 1 in 6 queries contain typos ([Baymard Institute](url))

#### Facets + Filters
- Current filter state vs dynamic faceting
- Why it matters: Filter users convert 2x higher ([Algolia research](url))

#### Product & Content (Federated Search)
- Current search showing only products vs federated approach
- Why it matters: 68% of shoppers value good search experience

#### No Results Page
- Current no-results experience vs best practice
- Why it matters: 75% of users leave after hitting no results

#### Smart Relevance
- Examples of poor relevance vs Algolia custom ranking
- Why it matters: 72% of sites have mediocre/broken relevance ([Baymard Institute](url))

#### Dynamic UX
- Current static experience vs Algolia's dynamic re-ranking, banners, merchandising
- Why it matters: Merchandising drives incremental revenue

#### Omnichannel & BOPIS (if applicable)
- Store availability in search, buy online pick up in store
- Why it matters: Omnichannel shoppers have 30% higher lifetime value

### 9b. Algolia Value-Prop Assessment
Summary of findings from Phase 2 steps 13-20 mapped to Algolia products:
| Algolia Product | Current State | Opportunity | Source |
|----------------|---------------|-------------|--------|
| NeuralSearch | [NLP test results] | [gap or strength] | Screenshot |
| Dynamic Faceting | [filter test results] | [gap or strength] | Screenshot |
| Query Suggestions | [popular/recent test results] | [gap or strength] | Screenshot |
| Personalization | [observable signals] | [gap or strength] | Screenshot |
| Recommend | [FBT/recs test results] | [gap or strength] | Screenshot |
| Rules Engine | [banners/merchandising test results] | [gap or strength] | Screenshot |
| Analytics | [trending/bestseller signals] | [gap or strength] | Screenshot |

### 10. How Algolia Can Help
- Algolia At A Glance: API-first, composable, AI-powered
- The Algolia Way: Crawl → Walk → Run → Fly implementation roadmap
- Key differentiators relevant to this prospect

### 11. Next Steps
- Recommended evaluation plan
- POC scope suggestion (margin-zone-aware)
- Timeline expectations
- Pilot strategy: 30-day A/B test focused on highest-impact gap

## Formatting Guidelines
- Use markdown with clear headers
- Include screenshots inline with descriptions
- Use tables for comparison data
- Bold key statistics and findings
- Use severity indicators: HIGH (red), MEDIUM (yellow), LOW (green)
- Reference SAIM data for every finding
- **Source every data point** — inline hyperlinks on financials, traffic, tech stack, industry stats, case studies
- Never compress Phase 1 data into single lines — give full detail

## Example Finding Format
```
### Gap #1: No Typo Tolerance

**What we tested**: We searched for common misspellings of top product categories.

**What happened**:
- "iphne" → 0 results (should show iPhones)
- "samsnug" → 0 results (should show Samsung products)
- Screenshot: [inline screenshot]

**Why it matters**: 1 in 6 search queries contain a typo ([Baymard Institute, 2023](url)). Without typo tolerance,
these high-intent users see zero results and are likely to leave. Lacoste saw a 37%
increase in search revenue after implementing Algolia's typo tolerance ([Algolia case study](url)).

**Algolia solution**: Algolia's built-in typo tolerance automatically handles
misspellings, returning relevant results even with 1-2 character errors.

**Strategic connection**: With {company}'s e-commerce growing {X}% YoY ([10-K](url)), every failed
search is a missed conversion at growing scale.
```
