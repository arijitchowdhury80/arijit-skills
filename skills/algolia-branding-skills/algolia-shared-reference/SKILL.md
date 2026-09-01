---
name: algolia-shared-reference
description: Internal reference library (brand-core SSOT + content recipes) loaded by the Algolia branding skills. Do not invoke directly — invoke algolia-create (the content generator) or algolia-brand-check (the compliance gate) instead, and they read these files themselves.
---

# Algolia shared reference

**This is not a user-facing skill.** It is the single source of truth the Algolia branding skills —
`algolia-create` (the generator) and `algolia-brand-check` (the gate) — read at runtime. Nothing here
generates output.

Before this existed, every branding skill carried its own inlined copy of the brand rules. They
diverged and went stale together — by August 2026 the whole set was enforcing a pre-2023 Algolia
brand while certifying it as compliant. One source, read at runtime, is what prevents that recurring.
The format generators were later collapsed into a single engine (`algolia-create`) that reads the
recipes below, so a format can no longer hold — or drift — a brand value.

## What is here

| File | Holds |
|---|---|
| `brand-core/design-system.md` | The canonical 2026 Xenon design system overview |
| `brand-core/tokens.md` / `tokens.json` | Color, typography, shape, motion tokens (single Xenon palette; provenance + retired list) |
| `brand-core/colors_and_type.css` | Importable CSS custom properties (the runtime tokens) |
| `brand-core/approved-stats.md` | **The only place Algolia numbers live.** Nothing may hardcode a statistic |
| `brand-core/product-names.md` | Current product line, and what is retired |
| `brand-core/messaging-framework.md` | Positioning, tagline, voice, editorial standards |
| `brand-core/layout-patterns.md` | Algolia's Figma landing-page section library |
| `brand-core/recipes/` | The 11 content formats, as data (structure only — no colors/fonts) |
| `content-templates/case-study.md` | Company inserts for customer case studies |
| `examples/approved-descriptions.md` | Verbatim company boilerplate, four lengths |

## How the skills use it

`algolia-create` reads `brand-core/` + the recipe for the requested type, then produces output using
only these values. `algolia-brand-check` reads `brand-core/` and audits an artifact against it. There
is one Xenon palette — no theme argument.

```
Read ../algolia-shared-reference/brand-core/ before generating.
```

Path resolution works because skills install flat into `~/.claude/skills/`, making
`../algolia-shared-reference/` a sibling of every branding skill.

## Changing something

Edit the one file that owns it — a value in `approved-stats.md`, or the structure of a format in its
`recipes/<type>.md`. Every output picks it up on the next run; never patch a value into a skill.

Every file carries a `verified:` date and its sources. Update the date whenever you check a value,
even if nothing changed — a stale date is the signal that a re-check is overdue.
