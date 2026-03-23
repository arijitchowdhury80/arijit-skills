---
name: algolia-email
description: Create Algolia-branded email templates for campaigns, product updates, and nurture sequences.
---

# Algolia Branded Email Templates

Create email content optimized for deliverability, engagement, and conversion while maintaining full Algolia brand compliance. Supports marketing campaigns, product updates, event invitations, nurture sequences, and customer success communications.

## Input

- Email type (marketing campaign, product update, event invitation, nurture sequence, customer success check-in)
- Target audience segment (developers, product managers, executives, existing customers, prospects, trial users)
- Key message or offer
- CTA destination (landing page, documentation, signup, event registration, meeting booking)
- Position in sequence (if part of a nurture flow: email 1 of 5, etc.)
- Personalization tokens available (first name, company, product usage, etc.)

## Process

1. **Subject Line** -- Write three subject line options (40-60 chars each). Lead with value or curiosity, not brand name. A/B test variants: one data-driven, one benefit-driven, one question-based. Avoid spam trigger words (free, guarantee, act now).
2. **Preview Text** -- Write preview text (80-100 chars) that complements the subject line. This appears after the subject in inbox view and must add context, not repeat the subject.
3. **Header** -- Algolia logo centered or left-aligned. Keep header minimal -- no large hero images that delay rendering. Optional thin Nebula Blue #003DFF accent bar.
4. **Opening Line** -- Personalized greeting using first name token. First sentence must hook the reader with relevance to their role or situation. No generic "Hope this finds you well."
5. **Body Content** -- Two to three short paragraphs (max four sentences each). Single-column layout for mobile compatibility. Bold key phrases for scannability. If including a list, use three to five bullet points maximum.
6. **CTA Button** -- Single primary CTA per email. Button text is action-oriented (2-5 words): "Try AI Search Free", "Reserve Your Spot", "See the Results". Button color: Nebula Blue #003DFF with white text. Minimum 44px height for mobile tap targets.
7. **Secondary Link** -- Optional text link below CTA for a softer ask: "Or learn more about [feature]." Never compete with the primary CTA.
8. **Footer** -- Algolia logo (small), physical address (CAN-SPAM), unsubscribe link, preference center link, social icons (LinkedIn, Twitter/X, GitHub). All in Space Gray on white background.
9. **Nurture Sequence Logic** -- If part of a sequence: define the email's role (awareness, consideration, decision), reference previous email context, escalate CTA commitment level across the sequence.
10. **Deliverability Check** -- Verify: text-to-image ratio above 60:40, no all-caps words, no excessive punctuation, alt text for all images, plain-text fallback notes.
11. **Run `/algolia-brand-check`** on the complete email content before finalizing.

## Output Sections

### Email Metadata
- Email type, audience segment, sequence position, send timing recommendation

### Subject Lines (3 variants)
- Subject line text, preview text, A/B test rationale

### Email Body
- Header specification
- Opening line (with personalization tokens)
- Body paragraphs
- CTA button (text, color, destination)
- Secondary link (optional)
- Footer specification

### Sequence Context (if applicable)
- Previous email summary
- This email's role in the journey
- Next email teaser

### Technical Notes
- Personalization tokens used
- Conditional content blocks (if any)
- Plain-text fallback guidance

## Brand Requirements

- **Voice**: Helpful and direct -- emails should feel like a smart colleague sharing something useful, not a marketing blast. Developers get technical precision; executives get business impact.
- **Colors**: Nebula Blue #003DFF (CTA buttons, accent bars), Space Gray #21243D (body text), White #FFFFFF (background), Algolia Purple #5468FF (secondary accents only)
- **Font**: Source Sans Pro or system fallback stack (Arial, Helvetica, sans-serif) for email client compatibility
- **Logo**: Algolia logo in header (centered or left-aligned) and footer (small, left-aligned)
- **CTA Buttons**: Nebula Blue #003DFF background, white text, 16px font, 44px minimum height, 8px border-radius
- **Subject Lines**: No ALL CAPS, no excessive punctuation, no spam trigger words, 40-60 characters
- **Personalization**: Use first name minimum; company name and role when available
- **Competitors**: Never mention competitors in any email communication
- **Unsubscribe**: Always include clear unsubscribe link (legal requirement and brand trust)
