---
name: algolia-blog
description: Write Algolia-branded blog posts with SEO, meta descriptions, CTAs, and social snippets.
---

# Algolia Branded Blog Post

Write a complete blog post for the Algolia blog with proper SEO structure, editorial standards, and brand-compliant content. Includes metadata, body content, code examples, and social media promotion snippets.

## Input

- Topic or working title
- Target keyword(s) for SEO
- Target audience (developers, product managers, business leaders, search practitioners)
- Content category (technical tutorial, thought leadership, product update, customer story, industry analysis)
- Desired word count (recommended: 1,200-2,000 for standard, 2,500-4,000 for pillar content)
- Key points or outline to cover (optional)
- Related Algolia products or features to reference

## Process

1. **Meta Block** -- Write an SEO title (50-60 chars, includes primary keyword), meta description (150-160 chars, includes keyword and CTA verb), select primary and secondary keywords, assign content category.
2. **Hero Section** -- Opening hook that establishes relevance in the first two sentences. Address the reader's problem or curiosity directly. No generic introductions.
3. **Introduction (150-200 words)** -- Expand on the hook, establish what the reader will learn, preview the structure. Include the primary keyword naturally within the first 100 words.
4. **Body Sections (3-5 sections)** -- Each section gets an H2 heading (sentence case, keyword-rich where natural). Subsections use H3. Paragraphs max four sentences. Use bullet points for lists of three or more items. Include transition sentences between sections.
5. **Code Examples** -- If technical: provide working code snippets with language tags, brief inline comments, and a one-sentence explanation before and after each block. Use Algolia API client syntax where applicable.
6. **Data and Proof Points** -- Support claims with approved Algolia stats, linked third-party research, or customer results. Every quantified claim must have a source.
7. **Internal Linking** -- Suggest two to three internal links to relevant Algolia blog posts, documentation pages, or product pages. Place links naturally within body text.
8. **CTA Section** -- Clear next step: try Algolia free, read documentation, explore a feature, contact sales. Match CTA to audience sophistication level.
9. **Author Bio** -- Three-sentence author bio template with name, role, expertise area, and a personal or professional detail.
10. **Social Snippets** -- Write one LinkedIn post (100-150 words, professional tone, includes key takeaway and link placeholder) and one Twitter/X post (under 260 chars to leave room for link, punchy and direct).
11. **SEO Checklist** -- Verify: keyword in title, keyword in first 100 words, keyword in at least one H2, meta description includes keyword, image alt text suggestions, internal links present.
12. **Run `/algolia-brand-check`** on the full post before finalizing.

## Output Sections

### Meta
- SEO title, meta description, primary keyword, secondary keywords, category, estimated reading time

### Blog Post Content
- Hero/hook paragraph
- Introduction
- Body sections with H2/H3 hierarchy
- Code examples (if applicable)
- CTA section

### Author Bio
- Three-sentence bio template

### Social Promotion
- LinkedIn post (100-150 words)
- Twitter/X post (under 260 chars)

### SEO Notes
- Keyword placement verification
- Internal link suggestions
- Image alt text recommendations

## Brand requirements

**Theme: `marketing`.** Read `../algolia-shared-reference/brand-core/` before generating —
`tokens.md`, `approved-stats.md`, `product-names.md`, and `messaging-framework.md`. Those files are
the source of truth for color, typography, statistics, product naming, voice, and editorial standards.
Do not rely on brand values remembered from anywhere else; Algolia's brand moved in 2026.

**Skill-specific**
- Blog voice is authoritative yet accessible — a trusted resource, not a sales pitch. Technical posts
  educate; thought leadership provokes thinking.
- Product references use the full name on first mention, shortened form afterwards.
- No exclamation marks in headings.
- Every post ends with one clear, relevant call to action.
- Third-party research must be linked and attributed, not paraphrased as an Algolia claim.

Run `/algolia-brand-check --theme marketing` on the output before finalizing.
