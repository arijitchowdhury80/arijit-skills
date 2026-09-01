# recipe: ui-copy — Algolia UI microcopy

output: interface text sets (concise, helpful, brand-consistent)
mode: create or rebrand

## inputs
component/screen (dashboard | search | settings | onboarding | error page) ·
copy category (action labels | feedback | forms | empty states | loading | tooltips | navigation | onboarding) ·
user context · technical constraints (char limits, single vs multi-line) · tone calibration (standard | celebratory | cautionary | instructional)

## structure (by category)
1. action labels — verb-first ("Search records", "Create index"); 2–4 words; sentence case; primary actions in primary color, secondary outline, destructive red (`--color-danger`); avoid generic ("Submit", "Click here", "OK")
2. feedback / success — past tense, confirm what happened + result ("Records imported (2,450 of 2,450)"); auto-dismiss ~5s or provide dismiss
3. feedback / error — what went wrong + what to do; never blame the user; no unexplained jargon; include error code where useful
4. feedback / warning — for destructive/irreversible only; state consequence then permanence ("This will remove all records. This cannot be undone.")
5. feedback / info — helpful context, not urgent ("Changes may take up to 60 seconds to appear"); near the relevant element
6. form fields — labels are nouns ("API key", "Index name"); placeholders show format ("my-ecommerce-index"); validation is specific ("1–64 characters, alphanumeric and hyphens")
7. empty states — what appears here + how to fill it + a primary action button; guide, don't dead-end
8. loading states — present participle ("Indexing records…"); progress for long ops ("Importing (1,200 of 5,000)")
9. tooltips — 1–2 sentences; answer "what is this / why care"; no period on a single sentence
10. navigation — 1–2 word labels, sentence case; match mental models
11. onboarding — stepped with progress ("Step 2 of 4: Connect your data source"); heading + one-sentence instruction + primary action; celebrate completion

## format-specific checks
respect char limits · voice = clear, helpful, never condescending · destructive copy states permanence

## then
engine runs algolia-brand-check on all copy sets; fix to ≥8.
