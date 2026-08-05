---
name: algolia-landing
description: Create Algolia-branded landing page content and HTML/CSS with conversion optimization.
---

# Algolia Branded Landing Page

Create complete landing page content with HTML/CSS output following Algolia brand guidelines and conversion optimization best practices. Includes hero section, value proposition, feature blocks, social proof, and conversion-focused CTAs.

## Input

- Page purpose (product feature, campaign, event registration, free trial, content download)
- Target audience (developers, product managers, executives, mixed)
- Primary CTA (what action should the visitor take)
- Key value proposition (one sentence)
- Features or benefits to highlight (3-6 items)
- Social proof available (customer logos, testimonials, stats)
- Form fields needed (if lead capture)

## Process

1. **Hero Section** -- Full-width hero with a headline (8-12 words, benefit-driven), subheadline (15-25 words, supporting detail), primary CTA button, and optional secondary link. Background: one of the four approved section backgrounds — navy, kelly blue `#003DFF`, white, or gray. Headline in white on dark, `#021046` on light.
2. **Social Proof Bar** -- Horizontal strip of five to eight customer logos in grayscale. Include one supporting stat taken from `../algolia-shared-reference/brand-core/approved-stats.md` — for example "Trusted by more than 18,000 businesses" or "1.75 trillion searches powered annually." Position directly below hero.
3. **Value Proposition Section** -- Three to four feature blocks in a grid layout. Each block: icon placeholder, bold heading (4-6 words), description (2-3 sentences), optional link to learn more. Alternate section backgrounds for visual rhythm, drawing only from the four approved options: navy, kelly blue, white, gray (`#f7f8fb`).
4. **Product Demo/Visual Section** -- Placeholder for interactive demo, video embed, or product screenshot. Include descriptive caption. This section should show the product in action.
5. **Benefits Section** -- Two-column layout with image on one side and three to four benefit bullet points on the other. Each bullet: bold lead-in phrase followed by one explanatory sentence. Alternate image side between sections.
6. **Testimonial Section** -- One to two customer quotes with attribution (name, title, company, optional headshot). Pull quotes in `#003DFF`. Sora has no italic — use weight and size for emphasis. Company logo beside each quote.
7. **Metrics Section** -- Three to four data callouts in a horizontal strip. Large numbers in Nebula Blue #003DFF, labels in Space Gray. Use approved stats or customer-specific results.
8. **CTA Section** -- Repeated primary CTA with a slightly different framing than the hero. If lead capture: minimal form (name, email, company maximum). Form button matches hero CTA color.
9. **Footer** -- Standard Algolia footer: navigation links, social icons, legal links, copyright notice. Space Gray background with white text.
10. **HTML/CSS Output** -- Generate clean, semantic HTML5 with inline CSS or a style block. Mobile-responsive using flexbox/grid. Accessible: proper heading hierarchy, alt text placeholders, sufficient color contrast, focus states on interactive elements.
11. **Run `/algolia-brand-check`** on the complete page content and code before finalizing.

## Output Sections

### Page Content (structured markdown)
- Hero: headline, subheadline, CTA text
- Social proof: logos list, supporting stat
- Feature blocks (3-4): heading, description, icon description
- Testimonials: quote, attribution
- Metrics: number + label pairs
- Final CTA: heading, CTA text, form fields (if applicable)

### HTML/CSS Code
- Complete HTML5 document
- Responsive CSS (mobile-first)
- Color variables using Algolia brand palette
- Font stack: Sora (300/400/600) via Google Fonts, with a sans-serif fallback. Never substitute another named webfont.

### Conversion Notes
- Recommended A/B test elements
- Heatmap focus areas
- Page load optimization tips

## Brand requirements

**Theme: `marketing`.** Read `../algolia-shared-reference/brand-core/` before generating —
`tokens.md`, `approved-stats.md`, `product-names.md`, and `messaging-framework.md`. Those files are
the source of truth for color, typography, statistics, product naming, voice, and editorial standards.
Do not rely on brand values remembered from anywhere else; Algolia's brand moved in 2026.

**Skill-specific**
- **Build from the section library.** Read `../algolia-shared-reference/brand-core/layout-patterns.md`
  and assemble from Algolia's real hero, body, and footer variants. Do not invent section structures.
- Every section sits on one of the four approved backgrounds: navy, kelly blue, white, gray.
- CTA buttons: `#003DFF`, white text, 18px bold, 52px height, 8px radius, 10% darker on hover.
- Logo top-left in the nav, minimum 32px height.
- Mobile-first, single column below 768px, 44px minimum tap targets.
- One primary action for the whole page; every CTA points at the same next step.

Run `/algolia-brand-check --theme marketing` on the output before finalizing.
