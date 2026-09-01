---
name: algolia-create
description: Create or rebrand any Algolia-branded content — blog post, email, landing page, social post, slide deck, one-pager, case study, UI microcopy, campaign brief, partner co-marketing material, or approved company boilerplate. One generator for all of them; reads brand-core (the single source of truth) plus a per-type recipe, then runs the algolia-brand-check gate. Use for any "write / make / draft an Algolia <thing>" request, or "rebrand this <draft> for Algolia". Replaces the retired per-format skills (algolia-blog, -email, -landing, -social, -deck, -one-pager, -case-study, -ui-copy, -brief, -partner, -boilerplate, -algolialize).
user-invocable: true
---

# Algolia Create — the single branded-content engine

You produce OR rebrand Algolia content. You hold **no brand values and no format rules of
your own** — both are read at runtime. This is deliberate: it is why brand values cannot
drift out of sync again.

## Types

`blog` · `email` · `landing` · `social` · `deck` · `one-pager` · `case-study` ·
`ui-copy` · `brief` · `partner` · `boilerplate`

## Process — every run

1. **Type.** Take it from the request or a `--type` argument. If genuinely unclear, ask
   once, then proceed. `brief` and `partner` may fan out to other types (they reference
   them as `algolia-create --type <x>`, never as separate skills).

2. **Read the warehouse — always, every run.** Algolia's brand moved in 2026 (Nebula →
   Xenon); never trust remembered values. Read from
   `../algolia-shared-reference/brand-core/`:
   - `design-system.md` — the canonical 2026 Xenon system
   - `tokens.json` / `colors_and_type.css` — the runtime values (import the CSS into any HTML)
   - `tokens.md` — human token reference (names below)
   - `approved-stats.md` — the ONLY valid numbers
   - `product-names.md` — current + retired product names
   - `messaging-framework.md` — voice, positioning, editorial

3. **Read the recipe** — `../algolia-shared-reference/brand-core/recipes/<type>.md`. It
   carries the format's structure only (inputs, section order, length limits, format
   checks). It contains no colors or fonts by design.

4. **Mode.**
   - *Create* — build from the brief per the recipe.
   - *Rebrand* — the user's draft is the source. Restructure to the recipe, rewrite in
     Algolia voice, correct terminology against product-names.md, verify every figure
     against approved-stats.md, and emit a change log (original → new → reason → dimension).
     Intensity: Light (terms + tone), Medium (full rewrite, keep structure), Heavy
     (restructure). This is the old algolialize behaviour.

5. **Produce.** Follow the recipe's structure exactly. Use ONLY brand-core values —
   **never hardcode a hex or a font name.** Hard rules:
   - Type: **Sora only** (`--font-display` / `--font-body`, weights 300/400/600, no
     italics, no 700+). Code uses `--font-mono` (JetBrains, `[DERIVED]`).
   - Color: primary `--xenon-blue`; ink/dark `--xenon-900` / `--ink`; primaries
     `--algolia-purple` / `--algolia-teal`; accents `--algolia-lime` / `--algolia-cyan`;
     backgrounds `--bg-white` / `--bg-light-gray` / `--bg-dark-blue`; body text `--fg1`,
     muted `--fg2` / `--fg3`. Neutrals/states are `[DERIVED]` in the CSS.
   - **Never** any retired value: `#003DFF`, `#021046`, `#0e1224`, `#5468FF`, `#8A4FFF`,
     `#00C29A`, `#00B6FF`, fabricated accents, or Frontify placeholders.
   - Stats only from approved-stats.md, each with its source. Product names only from
     product-names.md. No em dashes in user-facing copy. **No left-border accent stripes**
     on any card/callout/quote (Arijit hard rule) — use tint, bold lead-in, or full border.
   - Logo: use the real files in `brand-core/assets/logo/`; never redraw or recolour.

6. **Gate.** Run `algolia-brand-check` on the output. If it scores below 8, fix and
   re-run. Never ship content that fails its own gate.

## Output

The finished artifact in the recipe's format, then the brand-check score. In rebrand mode,
also the change log.

## Adding a new format

Drop a new `recipes/<type>.md` and add the type to the list above. No engine change, no new
skill. That is the whole point of this design.
