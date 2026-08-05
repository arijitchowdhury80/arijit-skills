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
3. **Terminology Correction** -- Replace all incorrect or generic product references with the current official names from `../algolia-shared-reference/brand-core/product-names.md`. That file also lists retired names to strip. Remove competitor names and replace with category terms.
4. **Messaging Alignment** -- Verify every quantified claim against `../algolia-shared-reference/brand-core/approved-stats.md`. Strip any figure not on that list, and attach the source to any figure that survives. Remove unsubstantiated superlatives. Align positioning with `../algolia-shared-reference/brand-core/messaging-framework.md`.
5. **Editorial Cleanup** -- Apply AP Style, enforce Oxford comma, convert headings to sentence case, spell out numbers under 10, standardize date formats, fix punctuation inconsistencies.
6. **Visual Specification** -- If the content includes HTML/CSS or design references: apply the token set for the declared theme from `../algolia-shared-reference/brand-core/tokens.md`. Do not hardcode hex values or a font name here — read them. Sora is the only typeface in either theme. Add logo placement guidance per the logo rules in that file.
7. **Structure Optimization** -- Improve content hierarchy: ensure clear H1/H2/H3 progression, add transition sentences between sections, verify CTA placement and clarity, check scannability (bullet points, bold key phrases, adequate white space).
8. **Anthropomorphism Scrub** -- Remove any language attributing human qualities to Algolia. Replace "Algolia thinks/believes/feels" with "Algolia enables/delivers/powers/provides".
9. **Competitor Sanitization** -- Remove all direct competitor mentions from marketing content. Replace with category descriptors: "legacy search solutions", "traditional keyword-based search", "alternative providers".
10. **Change Log Generation** -- Document every modification with: original text, modified text, reason for change, brand dimension affected.
11. **Run `/algolia-brand-check --theme <declared theme>`** on the transformed output to verify a compliance score of 8 or above. If it fails, fix and re-run; do not ship a transformation that fails its own gate.

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

## Brand requirements

**Theme: declared per transformation.** Ask for it, or infer from the target content type using the
table in `../algolia-shared-reference/brand-core/tokens.md`, and state which you inferred. A landing
page is `marketing`; a report or one-pager is `deliverable`.

Read `../algolia-shared-reference/brand-core/` before transforming — `tokens.md`, `approved-stats.md`,
`product-names.md`, and `messaging-framework.md`. Those files are the source of truth for color,
typography, statistics, product naming, voice, and editorial standards. Do not rely on brand values
remembered from anywhere else; Algolia's brand moved in 2026.

**Skill-specific**
- This skill rewrites content into the Algolia brand. If it works from stale values it does active
  harm, converting correct material into incorrect material. Read the reference files every run.
- Transformation intensity (Light / Medium / Heavy) governs structure, never brand accuracy. Even a
  Light pass corrects retired stats, retired product names, and banned fonts.
- The change log must record the brand dimension for every edit so a reviewer can audit the reasoning.
- Flag for human judgment rather than guessing: ambiguous claims, missing data, and any statistic
  that is not in `approved-stats.md`.

Run `/algolia-brand-check --theme <declared theme>` on the output before finalizing.
