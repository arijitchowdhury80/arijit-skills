---
name: algolia-intel-industry
description: Use for any Algolia Search Audit task involving industry-level research: collecting vertical benchmarks (Baymard, Forrester, NRF), ecommerce search conversion stats, vertical trend analysis, expert analyst quotes, and competitive search landscape for a prospect's industry. Invoke when the user explicitly runs 'algolia-intel-industry', asks for 'industry intelligence' or 'industry benchmarks' for an audit company, wants bigger-picture vertical context for a sales narrative, or needs to produce industry-intel.md. Distinct from competitor intel (specific companies) and financial profile (company financials) — this skill covers the broader vertical and what's happening across the industry.
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Input
$ARGUMENTS — company slug. Reads: $ALGOLIA_AUDIT_DIR/{CompanyName}/research/01-company-context.md (for vertical classification)

## Output
$ALGOLIA_AUDIT_DIR/{CompanyName}/research/industry-intel.md

## Path
$AUDIT_DIR = $ALGOLIA_AUDIT_DIR

## What to Collect (ALL sources — not fallback)

### 1. Vertical Benchmarks
WebSearch: "[vertical] ecommerce search conversion benchmark 2024 2025"
WebSearch: "[vertical] site search statistics 2025"
Sources: Baymard Institute (baymard.com/blog), Forrester (free summaries), NRF (nrf.com), Retail Dive, trade publications
Label: [WEBFETCH — Baymard Institute, {date}] if page WebFetched and stat confirmed on page
Label: [WEBSEARCH — {source}] if search result only (not WebFetched)
RULE: If stat cannot be WebFetched at source URL → label WEBSEARCH, never FACT

**Baymard Institute fallback:** Baymard pages often block WebFetch (JS-rendered). If WebFetch fails:
1. Try WebFetch on the specific blog post URL first
2. If blocked (empty or JS redirect): use the stat from WebSearch snippet, label [WEBSEARCH — Baymard Institute, {date}]
3. Never label a Baymard stat [FACT] unless you confirm the exact figure on the fetched page
4. Alternative benchmark sources when Baymard is blocked: Nielsen Norman Group (nngroup.com), Econsultancy, Search Engine Land, Think with Google

### 2. Industry Trends (2025-2026)
WebSearch: "[vertical] AI search personalization trends 2025 2026"
WebSearch: "[vertical] ecommerce technology investment 2025"
WebSearch: "[vertical] search discovery trends retail"
Focus: What technologies is this vertical adopting? What's driving investment? What's changing?

### 3. Expert Quotes
WebSearch: "[vertical] search personalization expert quote 2025"
WebSearch: "Baymard [vertical] search findings"
WebSearch: "Forrester [vertical] digital commerce 2025"
For any quote found: WebFetch the source URL and confirm the exact quote appears on that page.
Label: [WEBFETCH — {source}, {date}] if confirmed on page
Label: [WEBSEARCH — {source}] if not WebFetched

### 4. Competitor Behavior in the Vertical
From 04-competitors.md: what search/discovery investments are competitors making?
WebSearch: "[top competitor] search personalization AI 2025"
Focus: What is the "table stakes" level for this vertical now?

## Output Format

```markdown
# Industry Intelligence — {Company} / {Vertical}
*Generated: {date} | Vertical: {classification}*

## Vertical Overview
[2-3 sentences: what defines this vertical's search/discovery challenges]
[FACT — 01-company-context.md classification]

## Key Benchmarks for {Vertical}
| Metric | Benchmark | Source | Verified |
| Site search usage rate | X% of sessions | [source URL] | [WEBFETCH/WEBSEARCH] |
| Search-initiated conversion uplift | X% | [source URL] | [WEBFETCH/WEBSEARCH] |
[Add 3-5 relevant benchmarks with source verification status]

## 2025-2026 Trends
1. **[Trend name]**: [Description + why it matters for Algolia]
   Source: [URL] [WEBFETCH/WEBSEARCH label]
2. [etc.]

## Expert Quotes on Search in {Vertical}
| Quote | Speaker/Org | Source | Verified |
[Verbatim if WebFetch confirmed. Paraphrase with attribution if WEBSEARCH only. Never quote marks on WEBSEARCH.]

## Competitive Landscape in {Vertical}
[What are top competitors doing with search/discovery? What's become table stakes?]
[From 04-competitors.md + WebSearch]

## Algolia Vertical Positioning
[How does Algolia's capability map to this vertical's specific needs?]
[Reference: algolia.com/industries/{vertical} if applicable]

## Sources
[All URLs, labeled WEBFETCH or WEBSEARCH]
```

## Expert Quote Rules (MANDATORY)
- **Named sources only**: Every quote in the Expert Quotes table MUST have a named speaker with their title and organization. Anonymous quotes ("an analyst said...") are NOT permitted — omit them entirely.
- **Verbatim if WebFetched**: If the quote page was WebFetched and the exact text confirmed, use quotation marks and label [WEBFETCH].
- **No quotation marks on WEBSEARCH**: If only a search snippet, use *said that* notation (e.g., *Smith said that conversion rates improve 30% with site search*) and label [WEBSEARCH].
- **Maximum age**: If the quoted speaker made this statement more than 18 months ago, place it in a "Historical Context" subsection, not the main Expert Quotes table.

## Article Date Verification (MANDATORY)
For EVERY trend or benchmark: extract the article publication date from the page content.
If article is >18 months old → classify as "Historical Context" NOT "Current Trend".
Never use 2020-2022 articles as "2025 trends".
**Enforcement**: Before including any trend or benchmark, state the article date explicitly in your reasoning. If date cannot be confirmed → label as WEBSEARCH and note "date unverified".

## Verification Gate
After writing: verify industry-intel.md exists and ≥3000 bytes.
Must contain: benchmarks table, at minimum 2 trends, source labels.
