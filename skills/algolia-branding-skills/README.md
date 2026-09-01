# Algolia Branding Skills

Three Claude Code skills for producing on-brand Algolia content — one generator, one compliance
gate, and the shared brand library they both read.

Everything is driven from **one source of truth** (`algolia-shared-reference/brand-core/`), so a
color, stat, or product name is corrected in a single place and every output picks it up. This is the
2026 **Xenon** brand (primary `#0067F7`, not the retired Nebula `#003DFF`).

---

## Install

```bash
git clone https://github.com/arijitchowdhury80/arijit-skills.git
cd arijit-skills/skills/algolia-branding-skills
chmod +x install.sh && ./install.sh
```

Installs to `~/.claude/skills/`. Restart Claude Code, then type `/` to see the commands. No MCP
servers, no API keys, no configuration.

---

## The three skills

| Skill | What it does |
|---|---|
| `/algolia-create` | The one content generator. Creates OR rebrands any content type — blog, email, landing page, social post, deck, one-pager, case study, UI copy, brief, partner material, boilerplate. Reads brand-core + the per-type recipe, then runs the gate. |
| `/algolia-brand-check` | The compliance gate. Audits any artifact across 7 dimensions, returns a 1–10 score with line-level violations and fixes. Auto-fails on any retired value. |
| `algolia-shared-reference` | Not invoked directly. The brand-core source of truth + the content recipes that `algolia-create` reads at runtime. |

### Why one generator instead of eleven

The old bundle had a separate skill per format (blog, email, deck…). They were the same engine copied
eleven times, which is exactly how brand values drifted out of sync. Now there is one engine and the
format knowledge lives as **data recipes** under `brand-core/recipes/`. A recipe carries structure
only — inputs, section order, length limits — and **no colors or fonts**, so a value physically
cannot be hardcoded into a format again.

Use it by intent (“write an Algolia blog post on X”, “rebrand this draft as a landing page”) or with
`--type <blog|email|landing|social|deck|one-pager|case-study|ui-copy|brief|partner|boilerplate>`.

---

## How the shared reference works

```
algolia-shared-reference/
  brand-core/
    design-system.md        the canonical 2026 Xenon design system
    tokens.json             machine tokens with per-value provenance + the retired list
    tokens.md               human token reference (color, type, shape, motion)
    colors_and_type.css     importable CSS custom properties (the runtime tokens)
    approved-stats.md       the ONLY place Algolia numbers live
    product-names.md        current product line, and what is retired
    messaging-framework.md  positioning, tagline, voice, editorial standards
    layout-patterns.md      section/layout guidance
    recipes/                the 11 content formats, as data (no colors inside)
    assets/                 logo/icon/illustration manifests (binaries stream from the public CDN)
  content-templates/case-study.md
  examples/approved-descriptions.md
```

**To change a brand value, edit the one file that owns it.** Update a figure in `approved-stats.md`
and every output uses it on the next run. Never patch a value into a skill — that is how these
drifted before.

---

## One palette, no themes

The 2026 Xenon rebrand collapsed the old `marketing` / `deliverable` theme split into a single
palette. There is no `--theme` argument any more; audit and generate against the one Xenon palette.

| Role | Token | Hex |
|---|---|---|
| Primary brand | `--xenon-blue` | `#0067F7` |
| Ink / dark | `--xenon-900` / `--ink` | `#000033` |
| Purple | `--algolia-purple` | `#8572F6` |
| Teal | `--algolia-teal` | `#21C9C4` |
| Lime | `--algolia-lime` | `#CEFF00` |
| Cyan | `--algolia-cyan` | `#5FFBFB` |
| Backgrounds | white / light-gray / dark-blue | `#FFFFFF` / `#F6F6F6` / `#000033` |

**Typography is Sora**, weights 300 / 400 / 600, no italics, from Google Fonts. Never Inter, Roboto,
DM Sans, Arial, system fonts, or serif. Retired values (`#003DFF`, `#021046`, `#0e1224`, `#5468FF`,
`#8A4FFF`, `#00C29A`, `#00B6FF`) auto-fail `/algolia-brand-check`.

---

## Logos & assets

Logo and photography binaries are **not bundled** — pull the current pack from Frontify,
[algolia.frontify.com](https://algolia.frontify.com). Illustrations stream from the public CDN
(`media.ffycdn.net`) via the manifest in `brand-core/assets/`. Never redraw, recolor, or distort the
mark.

---

## Keeping this current

Every reference file carries a `verified:` date and names its sources. Truth source is the Algolia
Brand & Style Guide on Frontify. Re-harvest quarterly or on any brand announcement; diff against
`tokens.json` and log any change. As of the current brand: 1.75 trillion searches a year, 18,000+
businesses. `17,000+ customers`, `1.7 trillion`, or `30 billion records` are out of date and fail the
gate.

## Contributing

Found a value that is wrong or has moved? Fix it in `algolia-shared-reference/brand-core/` (or the
relevant recipe for a format change), update the `verified:` date, and open a PR. Never fix it inside
a skill.
