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

## Brand Requirements

- **Voice**: Authoritative yet accessible -- the Algolia blog is a trusted resource, not a sales pitch. Technical content should educate; thought leadership should provoke thinking.
- **Colors**: If including HTML elements: Nebula Blue #003DFF for links and accents, Space Gray #21243D for body text
- **Font**: Source Sans Pro for any styled output
- **Headings**: Sentence case (capitalize first word and proper nouns only)
- **Editorial**: AP Style, Oxford comma, numbers under 10 spelled out, no exclamation marks in headings
- **Product References**: Use full product names on first mention (Algolia AI Search), shortened form acceptable on subsequent mentions (AI Search)
- **Stats**: Only approved metrics or properly attributed third-party data
- **Competitors**: Never name competitors; use "traditional search" or "legacy approaches"
- **CTAs**: Every post must end with a clear, relevant call to action
