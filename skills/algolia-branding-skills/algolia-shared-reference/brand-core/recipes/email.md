# recipe: email — Algolia branded email

output: email content (subject variants + body spec)
mode: create or rebrand
covers: marketing campaign · product update · event invite · nurture sequence · customer-success

## inputs
email type · audience segment (dev | PM | exec | customer | prospect | trial) · key message / offer ·
CTA destination · sequence position (e.g. 1 of 5) · personalization tokens available

## structure (in order)
1. subject lines — 3 options, 40–60 chars each; lead with value/curiosity, not brand name; A/B: one data-driven, one benefit-driven, one question. Avoid spam triggers in the SUBJECT specifically (free, guarantee, act now) — filters weight subject far above body
2. preview text — 80–100 chars; complements the subject, adds context, never repeats it
3. header — Algolia logo (centered or left). Keep minimal; no large hero image that delays render. Optional thin primary-color accent bar across the TOP (a top rule, never a left-edge stripe)
4. opening line — personalized greeting; first sentence hooks on the reader's role/situation; no "Hope this finds you well"
5. body — 2–3 short paragraphs (≤4 sentences); single-column for mobile; bold key phrases; lists ≤5 bullets
6. CTA button — single primary CTA; action text 2–5 words ("Start your free trial"); sentence case; "free" is fine HERE (subject-line rule only); primary color fill, on-blue text; ≥44px tap target
7. secondary link — optional softer ask below CTA; never competes with primary
8. footer — small logo; physical address (CAN-SPAM); unsubscribe + preference-center links; social icons (LinkedIn, X, GitHub); footer text in muted body color on white
9. nurture logic (if sequence) — state this email's role (awareness/consideration/decision), reference prior context, escalate CTA commitment across the sequence

## format-specific checks
text-to-image ratio > 60:40 · no all-caps words · no excessive punctuation · alt text on all images · plain-text fallback noted

## then
engine runs algolia-brand-check on the email; fix to ≥8.
