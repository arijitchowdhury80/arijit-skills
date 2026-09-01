# recipe: deck — Algolia slide deck

output: per-slide content (title, body, layout, background, speaker notes) ready for Google Slides / Keynote
mode: create or rebrand

## inputs
topic + objective · audience (customer | prospect | internal | partner | exec | dev) ·
slide count (10–15 external, 5–10 internal) · key messages · data/metrics/customer examples

## structure
1. outline — narrative arc: hook → problem → solution → proof → CTA; map sections to slide budget
2. title slide — logo top-left; title centered; subtitle (date, presenter); background = primary color, on-blue (white) text
3. agenda — 3–5 numbered items, sentence case; white background, `--ink` headings, `--fg1` body
4. problem/challenge slides — frame the pain; data callouts; ≤4 bullets; one idea per slide
5. solution slides — position Algolia capability against the framed problem; two-column for before/after or feature/benefit; product screenshots / architecture as callouts
6. proof slides — customer logos, quantified results (approved stats), pull quotes from case studies; chart/graph guidance
7. technical slides (if dev audience) — code snippets in `--font-mono` on white; architecture diagrams; API examples
8. CTA / next-steps — single clear CTA, contact, links; background = primary color, on-blue text
9. speaker notes — conversational, 60–90s talk time per slide; expand on bullets, don't repeat them

## per-slide output fields
layout (Title | Content | Two-Column | Image-Left | Image-Right | Data/Chart | Quote | Divider | CTA) ·
background (brand-core token, not a hex) · title (sentence case) · body · visual notes · speaker notes
+ deck summary: slide count, est. duration, key-message reinforcement checklist

## format-specific rules
≤4 bullets per slide, sentence case, no periods on single-line bullets ·
title + divider slides = primary background / on-blue text; content slides = white

## then
engine runs algolia-brand-check on the deck content; fix to ≥8.
