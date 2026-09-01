# recipe: one-pager — Algolia executive one-pager

output: single-page document spec + layout guidance (print/PDF)
mode: create or rebrand
note: this recipe was the most stale under the old skill (a retired theme, graphite hex values, and
dead theme-scoped variables). All of that is removed — colors come only from brand-core tokens below.

## inputs
topic/initiative · audience (exec | tech lead | partner | prospect) · value proposition (one sentence) ·
3–5 supporting points or metrics · desired CTA / next step

## structure (in order)
1. header — logo top-left; document title in Sora SemiBold, `--ink`; optional subtitle regular; thin primary-color rule below header (a top/under-header rule, never a left-edge stripe)
2. key message — 1–2 sentences, the single most important takeaway; directly below header; Sora Regular, `--ink`
3. content blocks (3–4) — each: icon placeholder, bold heading, 2–3 sentences; two-column grid; each block stands alone as a scannable unit
4. metrics/stats callout — 2–4 quantified points in a strip; numbers in primary color (bold), labels in muted body color (`--fg2`/`--fg3`); only approved stats or clearly attributed third-party data
5. supporting detail — optional short customer quote / spec / timeline, ≤3 lines; separate visually with the light-gray background (`--bg-light-gray`)
6. CTA strip — clear next step in a primary-color band; contact name, email, one URL; single line if possible
7. footer — algolia.com, document date, confidentiality notice if needed; small muted text (`--fg3`)

## format-specific rules
total word count ≤ 350 — edit ruthlessly · ≥30% white space · no section > 25% of vertical space

## layout guidance
provide margin, column, and spacing specs for print/PDF export (use the brand-core spacing scale `--s-*`)

## then
engine runs algolia-brand-check on the final content; fix to ≥8.
