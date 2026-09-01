# Algolia design tokens — SSOT

`verified: 2026-08-19` · Source of truth: **Algolia Brand & Style Guide on Frontify**
(https://algolia.frontify.com/document/1, public). Harvested with Scout. Sourced
inventory: `algolia-design-system-harvest-a6ff9b/harvest/frontify/PHASE1-FINDINGS.md`.

> **This is the 2026 Xenon rebrand.** Primary blue is **Xenon Blue `#0067F7`**, not the
> retired Nebula Blue `#003DFF`. Import `colors_and_type.css` in this directory rather
> than retyping values. `[FRONTIFY]` = read on Frontify. `[DERIVED]` = implementation
> default not published on Frontify.

---

## Brand palette — [FRONTIFY], verified 2026-08-19

**Primary**

| Token | Value | Frontify name | Role |
|---|---|---|---|
| `--xenon-blue` / `--algolia-blue` | `#0067F7` | Blue (Xenon Blue) | Primary brand, logo, CTA, links |
| `--xenon-900` / `--ink` | `#000033` | Dark Blue / Xenon 900 | Headlines, dark surfaces |
| `--algolia-purple` | `#8572F6` | Purple | Real primary — **not retired** |
| `--algolia-teal` | `#21C9C4` | Teal | |

**Accent**

| Token | Value | Frontify name |
|---|---|---|
| `--algolia-lime` | `#CEFF00` | Lime (electric-lime) |
| `--algolia-cyan` | `#5FFBFB` | Cyan |

**Backgrounds** (the brand's named set, for light AND dark modes)

| Token | Value | Frontify name |
|---|---|---|
| `--bg-white` | `#FFFFFF` | White |
| `--bg-light-gray` | `#F6F6F6` | Light Gray |
| `--bg-dark-blue` | `#000033` | Dark Blue |

Color-range scale (named on Frontify): **Xenon 900 → Blue → Purple → Teal → Lime.**

### Do NOT use — excluded

- **Frontify template placeholders** (their stock example swatches, never Algolia):
  `Green #00FF11`, `Everglade #123123`, `Conifer #BADA55`.
- **Retired Nebula palette**: `#003DFF` (old primary), `#021046`, `#0e1224`,
  teal `#00C29A`, cyan `#00B6FF`.
- **Previously fabricated accents** (were self-labeled "from algolia.com hero blobs",
  never on Frontify): `#8A4FFF`, `#FF4F81`, `#FF7A59`, `#FFD64D`.

---

## Typography — [FRONTIFY]

- **Sora**, three weights only: **300 (Light) / 400 (Regular) / 600 (SemiBold)**, style
  **normal**. No italics, no 700+.
- Delivery: Google Fonts. `font-family: "Sora", sans-serif;`
- **Never**: Inter, Roboto, DM Sans, Arial, system, serif. (algolia.com loads Inter for
  site chrome only — that is plumbing, not brand type. `algolia-brand-check` fails on it.)
- Mono (implementation, [DERIVED]): JetBrains Mono.
- Scale, line-height, letter-spacing: **[DERIVED]** — Frontify publishes no size scale.
  See `colors_and_type.css`. Display type tight (`-0.02em`, `1.05`); body 16px / 1.5.

---

## Logo — [FRONTIFY]

Real files: `brand-core/assets/logo/` (SVG + EPS + PNG + AI source; from the official
"Algolia Logo Pack 2022").

- Built in **Xenon Blue**. Variants: **Full Xenon** (preferred, light bg) · **White
  text** (dark bg) · **Full white** (blue/photographic bg).
- Containers: **without (preferred)** · rounded · circle · square.
- **Never** redraw, recolour, distort, rotate, stretch, skew, or add effects. Use the
  latest file. Check contrast.
- Co-branding: Algolia + partner divided by an "&", same safe-zone rules.
- **Vintage caveat**: the only official logo files are the 2022 pack in `#003DFF`; the
  colour spec has moved to Xenon `#0067F7`. Ship the official file as-is (never recolour);
  the colour TOKEN is Xenon. Flag to Brand for a re-issued logo pack.

---

## Iconography — [FRONTIFY] + [DERIVED substitute]

- Algolia's own product feature icons (~33: A/B Testing, AI Search, Crawler,
  InstantSearch, Personalization, Recommend, Rules…). Partial set in
  `assets/icons/` (Frontify serves them as a lazy-load gallery; full pull is a follow-up).
- Approved substitute [DERIVED]: **Lucide** — single-colour line icons, ~24px, brand blue
  or Xenon 900, ~1.5px stroke. Never emoji as icons.

---

## Photography & digital assets — [FRONTIFY]

- **Photography**: customer-industry shots, used with a colour overlay from the palette.
  Real files `assets/photography/` (Dunelm, Gymshark, Mercari, Swedol,
  TeachersPayTeachers, The Times, Ubisoft, Viacom18).
- **Digital assets**: 232 Algolia-owned illustrations / product-UI examples (light + dark
  background sets) in `assets/illustrations/`. "All images belong to Algolia."

---

## Slide template — [FRONTIFY]

"Slide Template 2026". Google Slides master + PowerPoint version (links in
PHASE1-FINDINGS). Contact Brand@Algolia.com. The P4 HTML slide master derives its visual
language from this template.

---

## Shape & motion — [DERIVED]

Frontify publishes no radius/shadow/spacing/motion spec. Defaults in `colors_and_type.css`:
radii 4/6/8/12/16/20/999 (pills for tags/badges only, never CTA); 4px spacing grid;
low-spread shadows tinted with Xenon 900; motion `cubic-bezier(.2,.7,.2,1)`, 120–320ms;
focus rings 2–3px Xenon Blue.
