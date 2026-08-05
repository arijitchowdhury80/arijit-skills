---
name: algolia-shared-reference
description: Internal reference library loaded by the Algolia branding skills. Do not invoke directly — invoke algolia-brand-check, algolia-blog, algolia-landing, or another algolia-* branding skill instead, and it reads these files itself.
---

# Algolia shared reference

**This is not a user-facing skill.** It is the single source of truth the 13 Algolia branding skills
read at runtime. Nothing here generates output.

Before this existed, every branding skill carried its own inlined copy of the brand rules. They
diverged and went stale together — by August 2026 all 13 were enforcing a pre-2023 Algolia brand
while certifying it as compliant. One source, read at runtime, is what prevents that recurring.

## What is here

| File | Holds |
|---|---|
| `brand-core/tokens.md` | The two themes (`marketing`, `deliverable`), typography, shape, motion, logo and icon rules |
| `brand-core/approved-stats.md` | **The only place Algolia numbers live.** Nothing may hardcode a statistic |
| `brand-core/product-names.md` | Current product line, and what is retired |
| `brand-core/messaging-framework.md` | Positioning, tagline, voice, editorial standards |
| `brand-core/layout-patterns.md` | Algolia's Figma landing-page section library |
| `brand-core/colors_and_type.css` | Importable CSS custom properties for the `marketing` theme |
| `content-templates/case-study.md` | Company inserts for customer case studies |
| `examples/approved-descriptions.md` | Verbatim company boilerplate, four lengths |

## How skills use it

Each branding skill declares a theme and reads what it needs:

```
Theme: marketing
Read ../algolia-shared-reference/brand-core/ before generating.
```

Path resolution works because skills install flat into `~/.claude/skills/`, making
`../algolia-shared-reference/` a sibling of every branding skill.

## Changing something

Edit the one file that owns it. A stat changes in `approved-stats.md` and all 13 skills pick it up
on the next run — never patch a number into a skill.

Every file carries a `verified:` date and its sources. Update the date whenever you check a value,
even if nothing changed — a stale date is the signal that a re-check is overdue.
