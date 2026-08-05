---
name: algolia-deck
description: Create Algolia-branded presentation decks with speaker notes and Google Slides-ready layout.
---

# Algolia Branded Slide Deck

Create structured presentation content following the official Algolia slide template. Each slide includes title, body, speaker notes, layout type, and color specifications ready for assembly in Google Slides or Keynote.

## Input

- Presentation topic and objective
- Target audience (customer, prospect, internal, partner, executive, developer)
- Desired slide count (recommended: 10-15 for external, 5-10 for internal)
- Key messages or talking points to incorporate
- Any specific data, metrics, or customer examples to include

## Process

1. **Outline Structure** -- Create a narrative arc: opening hook, problem framing, solution positioning, proof points, call to action. Map each section to slide count allocation.
2. **Title Slide** -- Company logo placement top-left, presentation title centered, subtitle with date and presenter name, Nebula Blue #003DFF background with white text.
3. **Agenda Slide** -- Three to five agenda items, numbered, sentence case. White background with `#021046` headings and `#2f3447` body text.
4. **Problem/Challenge Slides** -- Frame the audience pain point. Use data callouts, short bullet points (max four per slide), supporting visuals guidance. One idea per slide.
5. **Solution Slides** -- Position Algolia capabilities against the framed problem. Use two-column layouts for before/after or feature/benefit pairs. Include product screenshots or architecture diagrams as callouts.
6. **Proof Point Slides** -- Customer logos, quantified results (use approved stats), pull quotes from case studies. Data visualization guidance for charts and graphs.
7. **Technical Detail Slides** -- If audience is technical: code snippets, architecture diagrams, API examples. Use monospace font for code blocks on white background.
8. **CTA/Next Steps Slide** -- Clear single call to action, contact information, relevant links. Nebula Blue background with white text.
9. **Speaker Notes** -- Write conversational speaker notes for each slide (60-90 seconds of talk time per slide). Notes should expand on bullet points, not repeat them.
10. **Run `/algolia-brand-check`** on the complete deck content before finalizing.

## Output Sections

For each slide, provide:

### Slide [N]: [Title]
- **Layout**: Title Slide | Content | Two-Column | Image-Left | Image-Right | Data/Chart | Quote | Section Divider | CTA
- **Background**: Color hex code
- **Title**: Slide title text (sentence case)
- **Body**: Bullet points or paragraph content
- **Visual Notes**: Description of images, charts, or diagrams to include
- **Speaker Notes**: Talk track for this slide (2-4 sentences)

### Deck Summary
- Total slide count
- Estimated presentation duration
- Key message reinforcement checklist

## Brand requirements

**Theme: `marketing`.** Read `../algolia-shared-reference/brand-core/` before generating —
`tokens.md`, `approved-stats.md`, `product-names.md`, and `messaging-framework.md`. Those files are
the source of truth for color, typography, statistics, product naming, voice, and editorial standards.
Do not rely on brand values remembered from anywhere else; Algolia's brand moved in 2026.

**Skill-specific**
- Maximum four bullets per slide, sentence case, no periods on single-line bullets.
- Title and divider slides: `#003DFF` background, white text. Content slides: white background.
- Logo top-left on the title slide, bottom-right on content slides, clear space of 1x logo height.
- Titles 28–36pt, body 18–24pt, speaker notes 14pt.
- Speaker notes expand on the bullets; they never repeat them.

Run `/algolia-brand-check --theme marketing` on the output before finalizing.
