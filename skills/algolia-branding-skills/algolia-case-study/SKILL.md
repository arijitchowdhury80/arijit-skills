---
name: algolia-case-study
description: Create Algolia-branded customer case studies using challenge-solution-results framework.
---

# Algolia Branded Customer Case Study

Create a structured customer success story using the challenge-solution-results framework. Designed for both sales enablement (leave-behind) and marketing (web publication) with proper brand formatting and compelling narrative.

## Input

- Customer company name and industry
- Customer contact (name, title) for attribution
- The business challenge they faced before Algolia
- Algolia products/features implemented
- Quantified results (metrics, percentages, timeframes)
- Direct quotes from the customer (if available)
- Technical details of the implementation (optional)
- Timeline from evaluation to go-live

## Process

1. **Customer Overview** -- One paragraph (3-4 sentences) introducing the customer: company name, industry, size, what they do, and why search/discovery matters to their business. Include company logo placement guidance.
2. **Challenge Section** -- Two to three paragraphs describing the problem before Algolia. Lead with the business impact (lost revenue, poor UX, developer frustration), then detail the technical limitations. Use the customer's words where possible. Heading: "The Challenge" in H2.
3. **Solution Section** -- Two to three paragraphs on how Algolia addressed the challenge. Name the specific Algolia products used, taking the current names from `../algolia-shared-reference/brand-core/product-names.md`. Describe the implementation approach without excessive technical jargon. Heading: "The Solution" in H2.
4. **Technical Sidebar** -- Optional boxed section with implementation specifics: products used, integration method, data volume, index configuration, custom features. Use bullet points. Background: the section wash `#f7f8fb`.
5. **Results Section** -- Lead with the headline metric (the most impressive number). Follow with two to four supporting metrics. Each metric: large number in Nebula Blue #003DFF with a descriptive label. Provide context for each number (before vs. after, timeframe). Heading: "The Results" in H2.
6. **Pull Quotes** -- Extract two to three compelling quotes from the customer. Format: large text in `#003DFF` with attribution (name, title, company) below. Sora has no italic — use weight and size for emphasis, never a faux-italic transform. Place one in the challenge section, one in the results section.
7. **Key Metrics Callout Strip** -- Horizontal bar with three to four quantified results: percentage improvements, time savings, revenue impact. Large numbers in Nebula Blue, labels in Space Gray.
8. **CTA Section** -- "Ready to see similar results?" followed by a CTA button linking to demo request or free trial. Include a secondary link to related case studies.
9. **Metadata** -- Industry tag, company size, Algolia products used, region, use case type (ecommerce search, content discovery, mobile search, etc.).
10. **Run `/algolia-brand-check`** on the complete case study before finalizing.

## Output Sections

### Metadata
- Customer name, industry, company size, region, products used, use case

### Customer Overview
- Company introduction paragraph, logo placement

### The Challenge
- Problem description (2-3 paragraphs)
- Pull quote from customer

### The Solution
- Algolia implementation description (2-3 paragraphs)
- Technical sidebar (optional)

### The Results
- Headline metric (the hero number)
- Supporting metrics (2-4 additional data points)
- Pull quote from customer
- Key metrics callout strip

### CTA
- Closing statement, CTA button, secondary link

### Sales Enablement Notes
- One-paragraph summary for CRM notes
- Key objection this case study addresses
- Ideal prospect profile for this story

## Brand requirements

**Theme: `marketing`.** Read `../algolia-shared-reference/brand-core/` before generating —
`tokens.md`, `approved-stats.md`, `product-names.md`, and `messaging-framework.md`. Those files are
the source of truth for color, typography, statistics, product naming, voice, and editorial standards.
Do not rely on brand values remembered from anywhere else; Algolia's brand moved in 2026.

**Skill-specific**
- **The customer is the hero.** Algolia is the enabler, never the protagonist.
- All metrics must be customer-approved and accurately attributed. No rounding that inflates results.
- Quotes must be real, with name, title, and company. Never fabricate; never paraphrase without
  marking it as such.
- Customer logo requires written permission.
- If the customer replaced a competitor, call it "their previous solution" — never by name.
- Use the company insert from `../algolia-shared-reference/content-templates/case-study.md` verbatim.

Run `/algolia-brand-check --theme marketing` on the output before finalizing.
