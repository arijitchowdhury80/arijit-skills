---
name: algolia-one-pager
description: Create Algolia-branded one-page executive summaries, product overviews, or leave-behinds.
---

# Algolia Branded One-Pager

Create a single-page document with structured content blocks, data callouts, and visual hierarchy guidance. Designed for executive audiences who need key information at a glance.

## Input

- Topic or initiative to summarize
- Target audience (executive, technical lead, partner, prospect)
- Key message or value proposition (one sentence)
- Three to five supporting points or data metrics
- Desired CTA or next step

## Process

1. **Header Block** -- Algolia logo top-left. Document title in Sora SemiBold 24pt, `#23263B`. Optional subtitle in 14pt regular. Thin Nebula Blue #003DFF accent line below header.
2. **Key Message** -- One to two sentences that capture the core value proposition. Position directly below the header. Use 16pt Sora Regular in `#23263B`. This is the single most important takeaway.
3. **Content Blocks (3-4)** -- Each block contains an icon placeholder description, a bold heading (14pt), and two to three sentences of supporting text (11pt). Arrange in a two-column grid for visual balance. Each block should stand alone as a scannable unit.
4. **Metrics/Stats Callout** -- Highlight two to four quantified data points in a horizontal strip. Use `#003DFF` for the metric numbers (24pt bold) with `deliverable` body-colour labels below (10pt), per `../algolia-shared-reference/brand-core/tokens.md`. Only use approved Algolia stats or clearly attributed third-party data.
5. **Supporting Detail** -- Optional section for a brief customer quote, technical specification, or timeline. Keep to three lines maximum. Use the `deliverable` page background (`--color-bg`) to visually separate from content blocks.
6. **CTA Strip** -- Clear next step in the `deliverable` accent (`--color-accent`). Include contact name, email, and one relevant URL. Keep to a single line if possible.
7. **Footer** -- Algolia URL (algolia.com), document date, confidentiality notice if needed. 9pt Sora Regular in `#6B7280`.
8. **Word Budget** -- Total word count must not exceed 350 words. Edit ruthlessly. Every sentence must earn its place.
9. **Visual Balance Check** -- Verify the page has adequate white space (at least 30% of the page). No section should dominate more than 25% of the vertical space.
10. **Run `/algolia-brand-check`** on the final content before delivery.

## Output Sections

### Document Metadata
- Title, subtitle, date, audience, confidentiality level

### Header
- Logo placement, title, subtitle, accent line

### Key Message
- One to two sentence value proposition

### Content Blocks (repeat 3-4 times)
- Icon description, heading, body text (2-3 sentences)

### Metrics Strip
- Two to four data points with number + label

### CTA
- Action statement, contact info, URL

### Footer
- URL, date, legal notice

### Layout Guidance
- Margin, column, and spacing specifications for print or PDF export

## Brand requirements

**Theme: `deliverable`.** Read `../algolia-shared-reference/brand-core/` before generating —
`tokens.md`, `approved-stats.md`, `product-names.md`, and `messaging-framework.md`. Those files are
the source of truth for color, typography, statistics, product naming, voice, and editorial standards.
Do not rely on brand values remembered from anywhere else; Algolia's brand moved in 2026.

**Skill-specific**
- **350 words maximum.** One printed page. Edit ruthlessly.
- At least 30% white space. No section takes more than 25% of vertical height.
- Logo top-left, minimum 120px wide, clear space equal to the height of the "a".
- Metric numbers in `#003DFF`; CTA strip in the `deliverable` accent.
- Executive-grade voice: concise, confident, data-driven, every claim substantiated.

Run `/algolia-brand-check --theme deliverable` on the output before finalizing.
