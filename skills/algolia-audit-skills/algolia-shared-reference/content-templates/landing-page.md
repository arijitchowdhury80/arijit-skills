# Landing Page Template

## Structure

### 1. Hero Section
- **Headline (H1)**: Clear value proposition in sentence case, 6-12 words
- **Subheadline**: 1-2 sentences expanding on the headline
- **CTA Button**: Action-oriented text (e.g., "Start free trial," "Get a demo," "Try it now")
- **Visual**: Algolia digital asset or product screenshot with brand overlay

### 2. Social Proof Bar
- Customer logos (recognizable brands)
- Key stat: "Powering 1.75 trillion searches for 18,000+ businesses"
- Analyst recognition: "Named a Leader in the Gartner Magic Quadrant"

### 3. Value Props Section (3-4 cards)
- Each card: Icon + Headline (H3) + 2-3 sentence description
- Focus on outcomes/benefits, not features
- Use specific numbers where possible

### 4. Feature Deep-Dive (2-3 sections)
- H2 heading for each feature area
- Screenshot or illustration
- 1-2 paragraph description
- Bullet list of capabilities

### 5. Customer Quote / Testimonial
- Named customer with title and company
- Specific result mentioned in the quote
- Customer logo

### 6. CTA Section
- Repeat or evolve the primary CTA
- Address remaining objections ("Free trial, no credit card required")

## HTML/CSS Guidelines

When generating landing page HTML, always use:

```html
<!-- Font -->
<link href="https://fonts.googleapis.com/css?family=Sora:300,400,600" rel="stylesheet">

<!-- Base styles -->
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: "Sora", sans-serif; color: #23263B; }

  /* Headings */
  h1 { font-size: 56px; font-weight: 300; line-height: 110%; letter-spacing: -2px; }
  h2 { font-size: 36px; font-weight: 300; line-height: 140%; letter-spacing: -2px; }
  h3 { font-size: 28px; font-weight: 400; line-height: 140%; letter-spacing: -1px; }

  /* Body */
  p { font-size: 16px; font-weight: 400; line-height: 160%; color: #5A5E9A; }

  /* CTA Button */
  .cta-btn {
    background: #003DFF;
    color: #FFFFFF;
    font-family: "Sora", sans-serif;
    font-weight: 600;
    font-size: 16px;
    padding: 14px 32px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
  }
  .cta-btn:hover { background: #0032CC; }

  /* Hero gradient */
  .hero {
    background: linear-gradient(135deg, #003DFF 0%, #5468FF 50%, #8B5CF6 100%);
    color: #FFFFFF;
    padding: 80px 40px;
  }
  .hero h1 { color: #FFFFFF; }
  .hero p { color: rgba(255,255,255,0.85); }
</style>
```

## Style Rules for Landing Pages
- **Tone**: Compelling, clear, action-oriented
- **Headings**: Sentence case, no periods
- **CTA text**: Action verbs, 2-5 words
- **Above the fold**: Headline + subheadline + CTA must be visible without scrolling
- **Mobile-first**: All layouts must work on mobile
- **Accessibility**: Maintain proper contrast ratios, use semantic HTML
