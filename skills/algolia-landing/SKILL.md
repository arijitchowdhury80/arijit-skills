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

1. **Hero Section** -- Full-width hero with a headline (8-12 words, benefit-driven), subheadline (15-25 words, supporting detail), primary CTA button, and optional secondary link. Background: Nebula Blue #003DFF gradient or white with blue accent. Headline in white (on dark) or Space Gray #21243D (on light).
2. **Social Proof Bar** -- Horizontal strip of five to eight customer logos in grayscale. Include a supporting stat: "Trusted by 17,000+ companies" or "1.7 trillion searches powered annually." Position directly below hero.
3. **Value Proposition Section** -- Three to four feature blocks in a grid layout. Each block: icon placeholder, bold heading (4-6 words), description (2-3 sentences), optional link to learn more. Use alternating background colors (white and light gray #F5F5F7) for visual rhythm.
4. **Product Demo/Visual Section** -- Placeholder for interactive demo, video embed, or product screenshot. Include descriptive caption. This section should show the product in action.
5. **Benefits Section** -- Two-column layout with image on one side and three to four benefit bullet points on the other. Each bullet: bold lead-in phrase followed by one explanatory sentence. Alternate image side between sections.
6. **Testimonial Section** -- One to two customer quotes with attribution (name, title, company, optional headshot). Pull quotes in Algolia Purple #5468FF italics. Company logo beside each quote.
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
- Font stack with Source Sans Pro and fallbacks

### Conversion Notes
- Recommended A/B test elements
- Heatmap focus areas
- Page load optimization tips

## Brand Requirements

- **Voice**: Benefit-driven and action-oriented -- landing pages sell outcomes, not features. Confident without hype.
- **Colors**: Nebula Blue #003DFF (hero background, CTAs, metric numbers), Space Gray #21243D (body text, headings on white), Algolia Purple #5468FF (accents, testimonial quotes), White #FFFFFF (content backgrounds), Light Gray #F5F5F7 (alternating section backgrounds)
- **Font**: Source Sans Pro -- headlines 36-48px bold, subheads 20-24px regular, body 16-18px regular. Fallback: Arial, Helvetica, sans-serif.
- **CTA Buttons**: Nebula Blue #003DFF background, white text, 18px bold, 52px height, 8px border-radius, hover state 10% darker
- **Logo**: Algolia logo in top-left navigation bar, minimum height 32px
- **Responsive**: Mobile-first design, single column below 768px, touch-friendly tap targets (44px minimum)
- **Stats**: Only approved Algolia metrics or customer-attributed results with permission
- **Competitors**: Never reference competitors; position against "traditional" or "legacy" approaches
