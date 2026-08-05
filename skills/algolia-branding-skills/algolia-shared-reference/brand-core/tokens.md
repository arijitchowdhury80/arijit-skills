# Algolia design tokens

`verified: 2026-08-05` · Sources: live algolia.com, Algolia Figma landing-page library
(`5DkPHASwX5HwFgG0WFEDhS`), Frontify typography page

There are **two themes**. Both are correct. They serve different surfaces, and mixing them is the
most common way branded output goes wrong.

---

## Pick your theme first

| Theme | Use for | Skills that default to it |
|---|---|---|
| `marketing` | Public-facing web. Landing pages, blog, social cards, email, decks, case studies, partner pages | `algolia-landing`, `algolia-blog`, `algolia-social`, `algolia-email`, `algolia-deck`, `algolia-case-study`, `algolia-partner` |
| `deliverable` | Documents and app surfaces. Reports, one-pagers, leave-behinds, product UI | `algolia-one-pager`, `algolia-brief`, `algolia-ui-copy` |

If you are unsure: will a prospect see this on the open web? → `marketing`. Is it a document you
hand someone? → `deliverable`.

---

## Theme: `marketing`

Matches what algolia.com actually serves today. Full CSS custom properties in
`colors_and_type.css` in this directory — import that file rather than retyping these.

**Color**

| Token | Value | Role |
|---|---|---|
| `--algolia-blue` | `#003DFF` | Nebula Blue / "kelly blue". Primary CTA, links, accent |
| `--algolia-blue-700` | `#0031cc` | Hover, pressed |
| `--ink` | `#021046` | Headlines |
| `--gray-700` | `#2f3447` | Body text |
| `--bg-hero-dark` | `#0e1224` | Dark hero and CTA bands, footer |
| `--bg-canvas` | `#f7f8fb` | Section wash |
| `--gray-200` | `#e1e4ec` | Card and section borders |

**Four approved section backgrounds**, per the Figma library: **navy, kelly blue, white, gray.**
Nothing else. A section sits on one of those four.

**Gradient accents** — cyan `#00B6FF`, teal `#00C29A`, blue. Used as soft color-blur decoration
behind hero and footer bands. Never as flat fills, never behind body text.

**No purple in `marketing`.** `#5468FF` is Algolia's pre-2023 accent. It does not appear on
algolia.com or anywhere in the Figma library. `algolia-brand-check --theme marketing` fails on it.

**Surfaces** — mostly flat white. No full-bleed photographic backgrounds, no textures, no grain,
no protection gradients behind type.

---

## Theme: `deliverable`

The established report and dashboard system. Existing reports and internal tooling are built on these
exact values — do not "modernize" them, or previously shipped output stops matching.

| Token | Value | Role |
|---|---|---|
| `--color-primary` | `#003DFF` | Primary CTA, links |
| `--color-accent` | `#5468FF` | Accent — valid in this theme only |
| `--color-text` | `#23263B` | **Space Gray** — headings and body |
| `--color-muted` | `#6B7280` | Secondary text |
| `--color-bg` | `#F5F5F7` | Page background |
| `--color-border` | `#E5E7EB` | Card and section borders |
| `--topbar-bg` | `#23263B` | Dark topbar |

Severity system: critical `#DC2626`, moderate `#D97706`, positive `#059669`, each with tint and
border variants.

Hero gradient: `linear-gradient(135deg, #0D1240 0%, #21243D 45%, #001A8A 100%)`.

> **Naming note.** "Space Gray" is the current, valid name for `#23263B` in this theme — it is not
> retired, and it is **not** `#21243D`. `#21243D` survives only as a midpoint of the hero gradient
> above; it is not a text or surface colour in either theme. Do not treat the name and that hex as
> interchangeable. The `marketing` theme has no Space Gray: its body colour is `#2f3447` and its
> headline ink is `#021046`, so the name should not appear in marketing guidance at all.

---

## Typography — both themes

**Sora.** Weights 300 (Light), 400 (Regular), 600 (SemiBold). Nothing heavier, no italics — the
brand spec ships only these three styles.

```
https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600&display=swap
```

**Never use: Inter, Roboto, DM Sans, Arial, system fonts, serif fonts.**

> **On Inter.** algolia.com does load Inter alongside Sora, and applies it to site chrome —
> figcaptions, the mobile-menu toggle, the OneTrust cookie banner. That is site plumbing, not brand
> typography. Every piece of Algolia content in the Figma library is Sora. Do not read Inter's
> presence on the site as permission to emit it. `algolia-brand-check` fails on Inter.

Mono: `JetBrains Mono` for `marketing` code samples, `SF Mono`/`Fira Code` for `deliverable`.

**Scale** — `marketing` uses the fluid clamp scale in `colors_and_type.css`. `deliverable` uses the
fixed scale: H1 56px/300/-2px, H2 36px/300/-2px, H3 28px/400/-1px, H4 22px/600, H5 18px/600,
body 16px/400/1.6, label 14px/600/0.12em.

Display type is tight: `-0.02em` letter-spacing, `1.05` line-height. Body is 16px / 1.5.

---

## Shape and motion — both themes

- **Radii:** 4 / 6 / 8 / 12 / 16 / 20 / 999. Cards 12–16px, inputs 8px, buttons 8–10px.
- **Pills (`999px`) are for tags, status badges, and category chips only.** Never a primary CTA.
- **Cards:** white, 1px `#e1e4ec` border, `--shadow-sm` at rest, lifting to `--shadow-lg` with
  `translateY(-2px)` on hover. No left-border accent stripe, no gradient interior.
- **Spacing:** 4px grid. Marketing sections breathe — 80–96px vertical rhythm. Cards 24–32px padding.
- **Motion:** `cubic-bezier(.2,.7,.2,1)`, 120–320ms. Buttons darken ~10% on hover. No bounces,
  no springs, no scroll theatrics.
- **Focus rings:** 2–3px `#003DFF`, 2px offset. Always visible.

## Logos

**Not redistributed with these skills.** Pull the current logo pack from Frontify
(`algolia.frontify.com`) — every Algolia employee has access.

- Wordmark on light backgrounds; white variant on dark or photographic backgrounds.
- Mark only when space is constrained: favicons, app icons, avatars.
- Minimum clear space around the wordmark: the height of the "a".
- **Never redraw, recolor, stretch, or combine the mark with another logo into a single lockup.**

## Iconography

Single-color SVG line icons, ~24px, brand blue or dark ink, ~1.5px stroke. Algolia's own set lives
behind their CDN. **Lucide** is the approved substitute — it matches stroke weight and corner
treatment. Never use emoji as icons. A Unicode arrow in a CTA link ("Learn more →") is fine.
