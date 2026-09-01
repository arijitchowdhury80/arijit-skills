# recipe: landing — Algolia landing page

output: page content (structured) + responsive HTML/CSS (imports brand-core colors_and_type.css)
mode: create or rebrand

## inputs
page purpose (feature | campaign | event | trial | download) · audience · primary CTA ·
value proposition (one sentence) · features/benefits (3–6) · social proof available · form fields (if lead capture)

## structure (in order)
1. hero — full-width; headline 8–12 words benefit-driven; subhead 15–25 words; primary CTA button; optional secondary link. Background drawn ONLY from the brand-core background set (`--bg-white`, `--bg-light-gray`, `--bg-dark-blue`) or a primary-color band; headline is on-dark text on dark grounds, `--ink` on light
2. social-proof bar — 5–8 customer logos in grayscale + one stat from approved-stats.md; directly below hero
3. value-prop section — 3–4 feature blocks in a grid; each: icon placeholder, bold heading 4–6 words, 2–3 sentence description, optional learn-more link. Alternate section backgrounds for rhythm, only from the brand-core background set
4. product-demo/visual section — placeholder for demo, video, or product screenshot + caption
5. benefits section — two-column, image one side, 3–4 benefit bullets the other; each bullet = bold lead-in + one sentence; alternate image side
6. testimonials — 1–2 customer quotes with attribution (name, title, company, optional headshot); pull quotes in primary color; Sora has no italic — use weight/size for emphasis; logo beside each
7. metrics section — 3–4 data callouts in a strip; large numbers in primary color, labels in muted body color; approved stats or customer-specific results
8. CTA section — repeat primary CTA, reframed vs hero; if lead capture, minimal form (name, email, company max); form button matches hero CTA
9. footer — nav links, social icons, legal, copyright; dark-blue background, on-dark text (use `--bg-dark-blue` / `--fg-on-dark`)

## format-specific checks (HTML)
semantic HTML5 · mobile-first flexbox/grid · proper heading hierarchy · alt-text placeholders ·
sufficient contrast · focus states on interactive elements · import brand-core CSS, never inline hexes ·
Sora (300/400/600) via Google Fonts with sans-serif fallback; never substitute another webfont

## then
engine runs algolia-brand-check on content AND code; fix to ≥8.
