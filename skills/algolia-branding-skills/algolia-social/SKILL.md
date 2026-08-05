---
name: algolia-social
description: Create Algolia-branded social media posts for LinkedIn, Twitter/X, and other platforms.
---

# Algolia Branded Social Media Posts

Create platform-optimized social media content that maintains Algolia brand voice while adapting to each platform's format, audience expectations, and engagement patterns.

## Input

- Topic or content to promote (product launch, blog post, event, customer win, thought leadership, hiring)
- Target platforms (LinkedIn, Twitter/X, or both)
- Key message or takeaway
- Link to include (if applicable)
- Visual asset description (if applicable)
- Campaign or hashtag context (if part of a series)

## Process

1. **Message Extraction** -- Identify the single most compelling takeaway from the source material. Social posts must lead with value, not announcements.
2. **LinkedIn Post** -- Write a 100-200 word post optimized for LinkedIn's algorithm: strong opening line (hook visible before "see more"), line breaks for readability, one clear CTA, relevant hashtags (3-5 max). Tone is professional and insight-driven. Use first-person plural ("we") for company posts or first-person singular for executive thought leadership.
3. **Twitter/X Post** -- Write a post under 260 characters (leaving room for link). Lead with the sharpest insight or stat. Use direct, punchy language. Include one to two relevant hashtags. If the topic requires more space, create a thread outline (3-5 tweets).
4. **Thread Format (Twitter/X, if needed)** -- Tweet 1: hook with the key insight. Tweets 2-4: supporting points, one per tweet. Final tweet: CTA with link. Number threads (1/5, 2/5, etc.).
5. **Hashtag Strategy** -- Primary: #Algolia (always include on company posts). Secondary: topic-specific tags (#SearchExperience, #AISearch, #DevTools, #Ecommerce, #SiteSearch). Avoid trending but irrelevant hashtags.
6. **Visual Guidance** -- Describe the ideal accompanying visual: product screenshot, data visualization, quote card, or custom graphic. Specify Algolia brand colors for any designed assets.
7. **Engagement Optimization** -- LinkedIn: ask a question or include a poll suggestion to drive comments. Twitter/X: use a hook that invites retweets or replies.
8. **Variant Generation** -- Provide two to three variants per platform for A/B testing different angles (data-led, story-led, question-led).
9. **Run `/algolia-brand-check`** on all post variants before finalizing.

## Output Sections

### LinkedIn Posts
For each variant (2-3):
- Post text (100-200 words)
- Hashtags
- CTA type (link click, comment, poll)
- Visual recommendation

### Twitter/X Posts
For each variant (2-3):
- Tweet text (under 260 chars)
- Hashtags
- Thread outline (if applicable)

### Campaign Notes
- Suggested posting schedule (day of week, time)
- Cross-platform sequencing recommendation
- Engagement response templates (for common replies)

## Brand requirements

**Theme: `marketing`.** Read `../algolia-shared-reference/brand-core/` before generating —
`tokens.md`, `approved-stats.md`, `product-names.md`, and `messaging-framework.md`. Those files are
the source of truth for color, typography, statistics, product naming, voice, and editorial standards.
Do not rely on brand values remembered from anywhere else; Algolia's brand moved in 2026.

**Skill-specific**
- Always include `#Algolia` on company posts. Never more than five hashtags on LinkedIn, two on X.
- Use full product names even in short-form copy.
- LinkedIn: authoritative and insightful. X: sharp, direct, technically savvy, never flippant.
- Emoji sparingly on LinkedIn (max two per post); avoid on X unless part of a thread visual pattern.
- Quote cards and designed assets follow the `marketing` theme in `tokens.md`.

Run `/algolia-brand-check --theme marketing` on the output before finalizing.
