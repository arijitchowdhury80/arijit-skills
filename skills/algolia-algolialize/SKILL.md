---
name: algolia-algolialize
description: Transform any content into Algolia-branded output with proper voice, tone, terminology, and visual identity.
---

# Algolialize -- Brand Transformation Engine

Take any content artifact and transform it into fully Algolia-branded output. This skill rewrites voice and tone, corrects terminology, applies visual specifications, and ensures messaging alignment -- producing a complete branded version alongside a detailed change log.

## Input

- Source content (any format: text, markdown, HTML, slide content, email copy, social posts)
- Original content type and context (who wrote it, what it was for)
- Target content type (may differ from source -- e.g., transform a competitor blog into an Algolia response blog)
- Target audience (developers, business buyers, partners, internal)
- Transformation intensity: Light (terminology and tone only), Medium (full rewrite preserving structure), Heavy (complete restructure and rewrite)

## Process

1. **Content Analysis** -- Identify the source content type, structure, word count, reading level, and existing brand signals. Detect any competitor terminology, off-brand tone, or problematic claims.
2. **Voice Transformation** -- Rewrite all content in Algolia voice: confident without arrogance, clear without oversimplifying, technically credible without jargon overload, approachable without being casual. Remove hedge words ("might", "possibly", "we think") and replace with direct, assertive language.
3. **Terminology Correction** -- Replace all incorrect or generic product references with official Algolia product names (Algolia Search, Algolia Recommend, Algolia AI Search, Algolia Crawler, Algolia Analytics). Remove any competitor names and replace with category terms. Fix deprecated terminology.
4. **Messaging Alignment** -- Verify all claims against approved Algolia stats and positioning. Remove unsubstantiated superlatives. Ensure value propositions align with current messaging framework: speed, relevance, developer experience, business impact.
5. **Editorial Cleanup** -- Apply AP Style, enforce Oxford comma, convert headings to sentence case, spell out numbers under 10, standardize date formats, fix punctuation inconsistencies.
6. **Visual Specification** -- If content includes HTML/CSS or design references: apply Nebula Blue #003DFF as primary color, Space Gray #21243D for text, Algolia Purple #5468FF for accents. Specify Source Sans Pro font family. Add logo placement guidance.
7. **Structure Optimization** -- Improve content hierarchy: ensure clear H1/H2/H3 progression, add transition sentences between sections, verify CTA placement and clarity, check scannability (bullet points, bold key phrases, adequate white space).
8. **Anthropomorphism Scrub** -- Remove any language attributing human qualities to Algolia. Replace "Algolia thinks/believes/feels" with "Algolia enables/delivers/powers/provides".
9. **Competitor Sanitization** -- Remove all direct competitor mentions from marketing content. Replace with category descriptors: "legacy search solutions", "traditional keyword-based search", "alternative providers".
10. **Change Log Generation** -- Document every modification with: original text, modified text, reason for change, brand dimension affected.
11. **Run `/algolia-brand-check`** on the transformed output to verify compliance score of 8 or above.

## Output Sections

### Transformed Content
- Complete branded version of the input content
- Formatted appropriately for the target content type

### Change Log
For each modification:
- Section/line reference
- Original text
- Transformed text
- Reason for change
- Brand dimension (voice, terminology, editorial, messaging, visual, anthropomorphism, competitor)

### Transformation Summary
- Total changes made by category
- Reading level before and after
- Word count before and after
- Brand compliance score (from `/algolia-brand-check`)

### Remaining Issues
- Any items that require human judgment (ambiguous claims, missing data, visual assets needed)

## Brand Requirements

- **Voice**: Confident, clear, technically credible, approachable -- the Algolia voice is expert but never condescending
- **Colors**: Nebula Blue #003DFF, Space Gray #21243D, Algolia Purple #5468FF, White #FFFFFF
- **Font**: Source Sans Pro for all text elements
- **Product Names**: Algolia Search, Algolia Recommend, Algolia AI Search, Algolia Crawler, Algolia Analytics -- always capitalized, never abbreviated
- **Approved Stats**: 17,000+ customers, 1.7 trillion searches/year, 30 billion records indexed
- **Anthropomorphism**: Algolia "enables", "powers", "delivers" -- never "thinks", "believes", "feels"
- **Competitors**: Never named in marketing content; use category terms instead
- **Editorial**: AP Style, Oxford comma, sentence case headings, numbers under 10 spelled out
