---
name: algolia-brand-check
description: Scan content for Algolia brand compliance across 7 dimensions. Returns 1-10 score with fixes.
---

# Algolia Brand Compliance Check

Audit any content artifact against the official Algolia brand guidelines across seven compliance dimensions. Produces a scored report with line-level violations, suggested fixes, and a pass/fail verdict.

## Input

- Content to audit (text, HTML, markdown, or structured slide content)
- Content type (blog, email, landing page, social post, deck, UI copy, one-pager, case study, brief, partner material)
- Target audience (developers, business decision-makers, partners, internal)

## Process

1. **Voice & Tone Audit** -- Verify content is confident, clear, technically credible, and approachable. Flag language that is arrogant, flippant, overly casual, or condescending. Check that developer content maintains precision while business content maintains accessibility.
2. **Terminology Audit** -- Confirm correct product names: Algolia Search, Algolia Recommend, Algolia AI Search, Algolia Crawler, Algolia Analytics, Algolia NeuralSearch. Flag deprecated terms (InstantSearch.js without version, Algolia Places, DocSearch when referring to current product). Verify branded phrases use correct capitalization.
3. **Editorial Standards Audit** -- Check AP Style compliance, Oxford comma usage, sentence case for headings, numbers spelled out below 10, correct date formats (Month Day, Year), no double spaces, consistent list formatting, proper em-dash usage.
4. **Messaging Accuracy Audit** -- Cross-check claims against approved stats: 17,000+ customers, 1.7 trillion searches/year, 30 billion records indexed. Flag unsubstantiated superlatives ("best", "fastest", "only"). Verify positioning aligns with current messaging framework.
5. **Visual Compliance Audit** -- If content includes HTML/CSS: verify Nebula Blue #003DFF as primary, Space Gray #21243D for body text, accent purple #5468FF, white #FFFFFF for backgrounds. Font family must reference Source Sans Pro. Check logo clear space and minimum size rules.
6. **Anthropomorphism Audit** -- Flag any instance where Algolia is described as thinking, believing, feeling, wanting, or having emotions. Algolia "enables", "provides", "powers", "delivers" -- it does not "think", "believe", "feel", "want", or "care".
7. **Competitor Mention Audit** -- Flag any direct competitor names in marketing materials (Elasticsearch, Typesense, Meilisearch, Coveo, Bloomreach, Lucidworks). Sales enablement and internal docs may reference competitors; marketing-facing content must not.

## Output Sections

### Overall Score
- Numeric score from 1-10 (10 = fully compliant)
- Pass threshold: 8 or above
- Verdict: PASS, NEEDS REVISION, or FAIL

### Dimension Breakdown
For each of the 7 dimensions:
- Dimension name and score (1-10)
- Number of violations found
- Severity classification (critical, major, minor)

### Violation Details
For each violation:
- Line or section reference
- Original text (quoted)
- Violation type and dimension
- Severity level
- Suggested fix with corrected text

### Summary
- Total violations by severity
- Top 3 issues to fix first
- Estimated effort to reach compliance

## Brand Requirements

- **Voice**: Confident, clear, technically credible, approachable -- never arrogant or dismissive
- **Colors**: Nebula Blue #003DFF (primary), Space Gray #21243D (body text), Accent Purple #5468FF, White #FFFFFF (backgrounds)
- **Font**: Source Sans Pro (headings and body)
- **Product Names**: Always capitalize: Algolia Search, Algolia Recommend, Algolia AI Search, Algolia Crawler, Algolia Analytics
- **Stats (approved)**: 17,000+ customers, 1.7 trillion searches/year, 30 billion records indexed
- **Anthropomorphism**: Never attribute human emotions or cognition to Algolia
- **Competitors**: Never name competitors in customer-facing marketing materials
- **Editorial**: AP Style, Oxford comma, sentence case headings, spell out numbers under 10
