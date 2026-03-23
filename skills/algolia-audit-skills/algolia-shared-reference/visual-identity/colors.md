# Algolia Color Palette

## Primary Colors

### Xenon Blue (Primary Brand Color)
- **HEX**: #003DFF
- **RGB**: 0, 61, 255
- **Usage**: Primary brand color, logo, CTAs, key interactive elements, links

### Neon Blue (Logo Color)
- **HEX**: #003DFF
- **RGB**: 0, 61, 255
- **Usage**: The Algolia logo is created using Neon Blue — a bold, vibrant color that evokes speed

### Dark Navy / Heading Color
- **HEX**: #23263B
- **RGB**: 35, 38, 59
- **Usage**: Primary text color for headings and body text on light backgrounds

## Text Colors

| Element | HEX | Usage |
|---------|-----|-------|
| Heading text | #23263B | H1, H2, H3, H4, H5, H6 headings |
| Body text | Gray scale shade | Body paragraphs — always a shade of gray, never pure black |
| Light background | #FFFFFF | Default page/section background |

## Background Colors

| Variant | HEX | Usage |
|---------|-----|-------|
| White | #FFFFFF | Default light background |
| Dark | #23263B (Navy) | Dark sections, footer, hero areas |

## Brand Gradient

The Algolia brand uses a **blue-to-purple gradient** in the header and hero areas:
- Gradient flows from deep blue (left) through mid-blue to purple (right)
- Used for: Page headers, hero sections, feature highlight backgrounds
- **Never use the gradient for body text backgrounds** — only decorative/hero areas

## Color Usage Rules

### Do
- Use Xenon Blue (#003DFF) as the primary accent color
- Use the dark navy (#23263B) for all text on light backgrounds
- Present body text in a shade of gray scale
- Use white (#FFFFFF) for text on dark/blue backgrounds
- Maintain high contrast ratios for accessibility

### Don't
- Don't colorize the logo outside of official color variations
- Don't use colored text in body copy (except in special cases like graphs)
- Don't place the logo on poorly contrasted backgrounds
- Don't create new color combinations not in the approved palette

## CSS Variables (for HTML/Web Output)

```css
:root {
  /* Primary */
  --algolia-blue: #003DFF;
  --algolia-navy: #23263B;
  --algolia-white: #FFFFFF;

  /* Text */
  --algolia-text-heading: #23263B;
  --algolia-text-body: #5A5E9A;

  /* Backgrounds */
  --algolia-bg-light: #FFFFFF;
  --algolia-bg-dark: #23263B;

  /* Interactive */
  --algolia-link: #003DFF;
  --algolia-cta: #003DFF;
  --algolia-cta-hover: #0032CC;
}
```
