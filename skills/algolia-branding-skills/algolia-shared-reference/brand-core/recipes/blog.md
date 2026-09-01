# recipe: blog — Algolia blog post

output: markdown body + SEO meta block
mode: create (from topic) or rebrand (from a draft / competitor post)

## inputs
topic / working title · target keyword(s) · audience (dev | PM | business | practitioner) ·
category (tutorial | thought-leadership | product-update | customer-story | industry) ·
word count (1,200–2,000 standard; 2,500–4,000 pillar) · outline (optional) · products to reference

## structure (in order)
1. meta block — SEO title 50–60 chars incl. primary keyword; meta description 150–160 chars incl. keyword + CTA verb; primary + secondary keywords; category; estimated reading time
2. hero hook — establish relevance in the first two sentences; no generic intro
3. introduction 150–200 words; primary keyword within first 100 words; preview the structure
4. body: 3–5 sections — H2 sentence case, keyword-rich where natural; H3 subsections; paragraphs ≤4 sentences; bullets for lists of 3+; transition sentences between sections
5. code examples (if technical) — language-tagged, one-sentence explainer before and after; Algolia API client syntax
6. proof — every quantified claim carries a source (approved-stats.md or linked third-party)
7. internal links — 2–3, placed naturally in body
8. CTA — matched to audience sophistication (trial | docs | feature | contact sales)
9. author bio — 3 sentences (name, role, expertise)
10. social snippets — 1 LinkedIn (100–150 words) + 1 X (<260 chars)

## format-specific checks
keyword in title · keyword in first 100 words · keyword in ≥1 H2 · meta description has keyword ·
image alt-text suggested · internal links present

## then
engine runs algolia-brand-check on the full post; fix to ≥8.
