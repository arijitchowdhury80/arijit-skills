# Algolia Typography

## Primary Typeface: Sora

Algolia uses only the **Sora** font, in three different weights. Adapt the font size depending on the size and resolution of the collateral you are producing. Text should always be legible.

### Font Import

**HTML:**
```html
<link href="https://fonts.googleapis.com/css?family=Sora" rel="stylesheet" type="text/css">
```

**CSS:**
```css
font-family: "Sora", sans-serif;
```

### Available Weights

| Weight | CSS Value | Usage |
|--------|-----------|-------|
| Light | `font-weight: 300` | Large display headings, hero text |
| Regular | `font-weight: 400` | Body text, paragraphs, descriptions |
| Semi-Bold | `font-weight: 600` | Emphasis, subheadings, bold text, CTAs |

## Typeface Scale

### Heading 1
- **Font**: Sora
- **Size**: 56px
- **Line height**: 110%
- **Weight**: 300 (Light)
- **Letter spacing**: -2px
- **Text color**: #23263B (dark backgrounds: #FFFFFF)

### Heading 2
- **Font**: Sora
- **Size**: 36px
- **Line height**: 140%
- **Weight**: 300 (Light)
- **Letter spacing**: -2px
- **Text color**: #23263B (dark backgrounds: #FFFFFF)

### Heading 3
- **Font**: Sora
- **Size**: 28px
- **Line height**: 140%
- **Weight**: 400 (Regular)
- **Letter spacing**: -1px
- **Text color**: #23263B (dark backgrounds: #FFFFFF)

### Heading 4
- **Font**: Sora
- **Size**: 22px
- **Line height**: 140%
- **Weight**: 400 (Regular)
- **Letter spacing**: -0.5px
- **Text color**: #23263B

### Heading 5
- **Font**: Sora
- **Size**: 18px
- **Line height**: 150%
- **Weight**: 600 (Semi-Bold)
- **Letter spacing**: 0
- **Text color**: #23263B

### Body Text
- **Font**: Sora
- **Size**: 16px
- **Line height**: 160%
- **Weight**: 400 (Regular)
- **Letter spacing**: 0
- **Text color**: Gray scale (never pure black)

### Small / Caption
- **Font**: Sora
- **Size**: 14px
- **Line height**: 160%
- **Weight**: 400 (Regular)

## Typography Rules

### Spacing
- Be mindful of white space around paragraphs
- A good practice is to have white space equal to 50% the size of your font line

### Text Presentation
- Every text should always be presented in a shade of gray scale
- Except in rare cases: highlighting a word in a paragraph, hyperlinks, or CTAs

### Sentence Case
- Use **sentence-case** for all headings and titles
- Only capitalize the first word (and proper nouns)

## CSS Implementation

```css
/* Algolia Typography System */
h1 {
  font-family: "Sora", sans-serif;
  font-size: 56px;
  line-height: 110%;
  font-weight: 300;
  letter-spacing: -2px;
  color: #23263B;
}

h2 {
  font-family: "Sora", sans-serif;
  font-size: 36px;
  line-height: 140%;
  font-weight: 300;
  letter-spacing: -2px;
  color: #23263B;
}

h3 {
  font-family: "Sora", sans-serif;
  font-size: 28px;
  line-height: 140%;
  font-weight: 400;
  letter-spacing: -1px;
  color: #23263B;
}

h4 {
  font-family: "Sora", sans-serif;
  font-size: 22px;
  line-height: 140%;
  font-weight: 400;
  letter-spacing: -0.5px;
  color: #23263B;
}

h5 {
  font-family: "Sora", sans-serif;
  font-size: 18px;
  line-height: 150%;
  font-weight: 600;
  color: #23263B;
}

body, p {
  font-family: "Sora", sans-serif;
  font-size: 16px;
  line-height: 160%;
  font-weight: 400;
  color: #5A5E9A;
}

small, .caption {
  font-family: "Sora", sans-serif;
  font-size: 14px;
  line-height: 160%;
  font-weight: 400;
}
```
