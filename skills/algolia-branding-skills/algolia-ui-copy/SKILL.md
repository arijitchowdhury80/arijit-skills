---
name: algolia-ui-copy
description: Write Algolia-branded UI microcopy: buttons, tooltips, errors, empty states, success messages.
---

# Algolia Branded UI Microcopy

Write interface text that is concise, helpful, and brand-consistent. Covers every category of UI copy: actions, feedback, navigation, forms, empty states, loading states, tooltips, and onboarding flows. Each piece of microcopy must guide the user while maintaining the Algolia voice.

## Input

- UI component or screen being written for (dashboard, search interface, settings, onboarding, error page)
- Copy category (action labels, feedback messages, form fields, empty states, loading states, tooltips, navigation, onboarding)
- User context (what the user is trying to do, where they are in the flow)
- Technical constraints (character limits, single-line vs. multi-line, responsive breakpoints)
- Tone calibration (standard, celebratory, cautionary, instructional)

## Process

1. **Action Labels (Buttons, CTAs)** -- Write verb-first labels: "Search records", "Create index", "Save configuration", "Export results". Two to four words maximum. Use sentence case. Primary actions in Nebula Blue #003DFF, secondary in outline style, destructive in red. Avoid generic labels ("Submit", "Click here", "OK").
2. **Feedback Messages -- Success** -- Confirm what happened in past tense: "Index created successfully", "Configuration saved", "Records imported (2,450 of 2,450)". Include the result when quantifiable. Dismiss automatically after five seconds or provide a dismiss action.
3. **Feedback Messages -- Error** -- State what went wrong and what to do: "Could not connect to index. Check your API key and try again." Never blame the user. Never use technical jargon without explanation. Provide a clear recovery action. Include error codes for support reference where applicable.
4. **Feedback Messages -- Warning** -- Alert without alarming: "This will remove all records from the index. This action cannot be undone." State the consequence, then the permanence. Use for destructive or irreversible actions only.
5. **Feedback Messages -- Info** -- Provide helpful context: "Changes may take up to 60 seconds to appear in search results." Informational, not urgent. Positioned near the relevant UI element.
6. **Form Fields** -- Labels are nouns or noun phrases: "API key", "Index name", "Records per page". Placeholder text shows format examples: "sk_1234abcd...", "my-ecommerce-index", "10". Validation messages are specific: "Index name must be 1-64 characters, alphanumeric and hyphens only."
7. **Empty States** -- Explain what will appear here and how to populate it: "No records yet. Import your first dataset to start searching." Include a primary action button. Empty states are an opportunity to guide, not a dead end.
8. **Loading States** -- Brief and informative: "Indexing records...", "Analyzing search patterns...", "Building recommendations...". Use present participle (-ing). For long operations, include progress indication: "Importing records (1,200 of 5,000)."
9. **Tooltips** -- One to two sentences maximum. Answer "what is this?" or "why should I care?". Example: "Distinct: Groups results by a specific attribute to avoid showing duplicate items." No period needed for single sentences.
10. **Navigation and Menus** -- Labels are one to two words: "Dashboard", "Search", "Analytics", "Settings", "API Keys". Sentence case. Match mental models: group related items, use familiar category names.
11. **Onboarding** -- Step-by-step with clear progress: "Step 2 of 4: Connect your data source." Each step has a heading, one-sentence instruction, and a primary action. Celebrate completion: "You are all set. Your first index is live."
12. **Run `/algolia-brand-check`** on all UI copy sets before finalizing.

## Output Sections

### Action Labels
- Primary button labels (verb + noun, 2-4 words)
- Secondary action labels
- Destructive action labels (with confirmation copy)

### Feedback Messages
- Success messages (with auto-dismiss timing)
- Error messages (with recovery action)
- Warning messages (with consequence + permanence)
- Info messages (with contextual placement)

### Form Copy
- Field labels, placeholder text, help text, validation messages

### Empty States
- Heading, description, primary action button text

### Loading States
- Loading message, progress format (if applicable)

### Tooltips
- Tooltip text (1-2 sentences each)

### Navigation Labels
- Menu items, breadcrumb format, tab labels

### Onboarding Copy
- Step headings, instructions, completion message

## Brand Requirements

- **Voice**: Helpful, clear, and concise. UI copy is the most utilitarian expression of the Algolia voice. Every word must earn its place. Be direct without being curt. Be helpful without being verbose.
- **Colors**: Nebula Blue #003DFF (primary actions, links), Space Gray #21243D (body text, labels), Algolia Purple #5468FF (accents, highlights), Green #00C853 (success states), Red #FF3D00 (error/destructive states), Amber #FFC107 (warning states)
- **Font**: Source Sans Pro -- UI labels 14px medium, body text 14px regular, small text 12px regular
- **Capitalization**: Sentence case for all UI text. Never use ALL CAPS except for abbreviations (API, SDK, URL).
- **Punctuation**: No periods on single-sentence tooltips, button labels, or headings. Use periods on multi-sentence descriptions and error messages. No exclamation marks except in celebratory completion messages (use sparingly).
- **Length**: Button labels 2-4 words. Tooltips 1-2 sentences. Error messages 1-2 sentences. Empty states 2-3 sentences maximum.
- **Anthropomorphism**: The product "helps you", "lets you", "shows you" -- it never "thinks", "believes", or "knows"
- **Technical Terms**: Use developer-friendly language but explain Algolia-specific concepts. "Index" is acceptable; "inverted index data structure" needs simplification for UI context.
