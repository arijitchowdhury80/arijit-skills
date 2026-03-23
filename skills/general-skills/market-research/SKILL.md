---
name: market-research
description: Produce competitive intelligence briefs using SimilarWeb, BuiltWith, and web search.
allowed-tools: mcp__similarweb-mcp__*, mcp__builtwith__*, WebSearch, WebFetch, Read, Write
---

# Market Research -- Competitive Intelligence Brief

Produce a comprehensive competitive intelligence brief using available MCP servers and web search.

## Input

Accept domain or company name as `$ARGUMENTS`.

## Process

1. **Traffic & Engagement** (SimilarWeb MCP):
   - Pull visits, bounce rate, pages per visit, average duration
   - Pull traffic sources breakdown (direct, search, social, referral, display, mail)
   - Pull top geographies and demographics

2. **Technology Stack** (BuiltWith MCP):
   - Pull current technology stack (frameworks, analytics, CDN, hosting, etc.)
   - Identify search/discovery technology (Algolia, Elasticsearch, Coveo, etc.)
   - Note recent technology changes (added/removed)

3. **Market Context** (Web Search):
   - Recent funding or M&A news
   - Leadership changes
   - Product announcements
   - Industry positioning

4. **Competitive Position** (SimilarWeb MCP):
   - Similar sites and overlap
   - Website ranking (global and category)
   - Keyword competitors

## Output

Structured markdown brief with sections:
1. **Company Overview** -- what they do, size indicators
2. **Traffic Profile** -- visits, sources, geography, trends
3. **Technology Stack** -- current tech with search/discovery highlighted
4. **Market Position** -- ranking, competitors, audience overlap
5. **Key Insights** -- 3-5 actionable observations
6. **Algolia Fit Assessment** -- where Algolia could add value

Write output to `docs/research/MARKET-<company>.md`.
