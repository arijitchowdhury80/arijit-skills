# Algolia Design System

`canonical: 2026-08-19` · SSOT = this directory (`brand-core/`) · Truth source: Algolia
Brand & Style Guide on Frontify (https://algolia.frontify.com/document/1, public).
This is the **2026 Xenon rebrand**.

This is the single authoritative document for every Algolia-branded artifact: web and
campaign pages, apps, branded emails, HTML decks, LinkedIn carousels, press releases,
one-pagers, and product docs. It is the brand-control layer of the Algolia Workspace
plugin. **Nothing downstream invents a value.** Every generator reads from here.

---

## 1. The model

- **TRUTH** - `brand-core/` holds every token, asset pointer, stat, product name, and
  messaging rule. The only place they live.
  - `colors_and_type.css` - importable CSS custom properties (the runtime tokens).
  - `tokens.json` - machine-readable tokens with per-value provenance.
  - `tokens.md` - human-readable token reference.
  - `assets/` - real logo vectors, photography, icons, and the illustration catalog.
  - `approved-stats.md`, `product-names.md`, `messaging-framework.md`, `layout-patterns.md`.
- **GATE** - `algolia-brand-check` reads brand-core and is required on big-ticket collateral.
- **CONSUMERS** - the `algolia-*` generators + `frontend-design` / `artifact-design-arijit`.
  They produce artifacts and hold NO tokens; they read from here.

Provenance discipline: `[FRONTIFY]` = read on Frontify. `[DERIVED]` = implementation
default a working UI needs but Frontify does not publish. Never present derived as brand spec.

---

## 2. Color - [FRONTIFY]

| Role | Token | Hex |
|---|---|---|
| Primary brand | `--xenon-blue` | `#0067F7` |
| Dark / ink | `--xenon-900` | `#000033` |
| Primary | `--algolia-purple` | `#8572F6` |
| Primary | `--algolia-teal` | `#21C9C4` |
| Accent | `--algolia-lime` | `#CEFF00` |
| Accent | `--algolia-cyan` | `#5FFBFB` |
| Background | white / light-gray / dark-blue | `#FFFFFF` / `#F6F6F6` / `#000033` |

Range scale: Xenon 900 → Blue → Purple → Teal → Lime. Neutral ramp, states, hover blues
are `[DERIVED]` (see `colors_and_type.css`).

**Never use:** retired Nebula `#003DFF`, old ink `#021046`/`#0e1224`, old purple
`#5468FF`/`#8A4FFF`, old teal `#00C29A`, old cyan `#00B6FF`; fabricated accents
`#FF4F81`/`#FF7A59`/`#FFD64D`; Frontify template placeholders `#00FF11`/`#123123`/`#BADA55`.

---

## 3. Typography - [FRONTIFY]

**Sora only**, weights **300 / 400 / 600**, style normal. No italics, no 700+. Delivered
via Google Fonts. Never Inter/Roboto/Arial/serif (Inter on algolia.com is site chrome, not
brand type). Size scale is `[DERIVED]`.

---

## 4. Logo - [FRONTIFY]

Real files: `assets/logo/` (SVG + PNG + EPS + AI). Variants: Full Xenon (light bg) /
White text (dark bg) / Full white (blue or photo bg). Containers: none (preferred) /
rounded / circle / square. Never redraw, recolour, distort, or add effects.
**Vintage caveat:** the official pack is 2022 in `#003DFF`; ship the file as-is (never
recolour), the color token is Xenon. Re-issued pack pending from Brand.

---

## 5. Iconography

Algolia's ~33 product feature icons (partial local set in `assets/icons/`; full set is a
Frontify lazy gallery, follow-up harvest). Approved substitute `[DERIVED]`: **Lucide**,
single-colour line, ~24px, brand blue or Xenon 900, ~1.5px stroke. No emoji as icons.

---

## 6. Photography & digital assets - [FRONTIFY]

- **Photography** (`assets/photography/`): customer-industry shots, used under a palette
  colour overlay. Dunelm, Gymshark, Mercari, Swedol, TeachersPayTeachers, The Times,
  Ubisoft, Viacom18.
- **Digital assets**: 230 Algolia-owned illustrations / product-UI examples (light + dark).
  **Not bundled** - fetched on demand from the public CDN
  (`media.ffycdn.net/eu/algolia-brand/{hash}.png`).

### Asset selection (how a generator picks the right illustration)

Asset NAMES are unreliable (e.g. "B2B Buyers" is a cereal product-search analytics UI), so
selection runs over VISION descriptions, not names:

1. **Enriched catalog** - each asset carries a vision `description`, `content_type`,
   `depicts_tags`, corrected `surface` (light/dark), `text_on_image`. Built once, cached.
   (`harvest/frontify/DIGITAL-ASSETS-CATALOG.enriched.json`; plugin ships a slim copy.)
2. **Match** - content topic → semantic search over descriptions + tags. Recommended
   backend: an Algolia index of the enriched records (we dogfood); fallback embeddings.
3. **Filter** - surface must fit the layout (dark asset on navy, light on white).
4. **Justify** - carry the match score + description as the "why this one" rationale.
5. **Confidence floor** - below threshold, emit NO illustration (wrong is worse than none).
   High-stakes: propose top 3, human picks.
6. **Fetch** - pull only the chosen CDN URL; inline as data-URI only when the target is a
   claude.ai Artifact (its CSP blocks external hosts), else hot-link.

---

## 7. Shape, layout, motion - [DERIVED]

Radii 4/6/8/12/16/20/999 (pills for tags/badges only). 4px spacing grid. Low-spread
shadows tinted with Xenon 900. Motion `cubic-bezier(.2,.7,.2,1)`, 120–320ms. Focus rings
2–3px Xenon Blue. Full layout guidance in `layout-patterns.md`.

---

## 8. Voice, stats, names

- Voice: `tone-of-voice` skill. No em dashes in user-facing copy.
- Numbers: only from `approved-stats.md` (Frontify Welcome: 1.75 trillion searches,
  18,000+ businesses, ~800 people).
- Product names: only from `product-names.md`.

---

## 9. How the plugin loads this

Ships as: this doc + `tokens.json` + `colors_and_type.css` + the slim asset catalog + the
small logo vectors + the `algolia-brand-check` gate. Assets stream from the public CDN on
demand. Consumers import `colors_and_type.css` (runtime) or read `tokens.json` (data);
they never hardcode a value.

---

## 10. Keep-current re-verify routine (P6 seed)

Frontify is live and changing (color spec has already outrun the 2022 logo pack). To stay
true:
1. Re-run the Scout harvest against all 11 Frontify routes (config in PHASE1-FINDINGS.md:
   `use_js`, `stealth`, `respect_robots_txt:false`, `networkidle`, `delay 3.5s`).
2. Diff new values against `tokens.json`; any change = a drift entry + a brand-core update.
3. Re-enrich only NEW/changed illustration hashes (vision pass), merge into the catalog.
4. Re-render one artifact per generator and eyeball it (Done-Means-Live).
5. Cadence: quarterly, or on any Brand announcement. Owner: Brand@Algolia.com is the human
   source of record for finalized changes.
