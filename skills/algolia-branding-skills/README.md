# Algolia Branding Skills

Thirteen Claude Code skills for producing on-brand Algolia content: blog posts, landing pages,
emails, decks, case studies, one-pagers, social posts, partner collateral, and UI microcopy — plus a
compliance gate that scores any artifact against the current brand.

All thirteen read their brand data from **one shared reference library**, so a stat or a product name
is corrected in a single file and every skill picks it up.

---

## Install

```bash
git clone https://github.com/arijitchowdhury80/arijit-skills.git
cd arijit-skills/skills/algolia-branding-skills
chmod +x install.sh && ./install.sh
```

Installs to `~/.claude/skills/`. Restart Claude Code, then type `/` to see the commands.

No MCP servers, no API keys, no configuration. If you only want these skills, you only need this
folder — nothing else in the repo is required.

---

## The skills

| Skill | What it does |
|---|---|
| `/algolia-brand-check` | Audits any content across 7 dimensions, returns a 1–10 score with line-level violations and fixes. The gate every other skill calls |
| `/algolia-algolialize` | Transforms existing content into Algolia brand — voice, terminology, stats, visual spec — with a full change log |
| `/algolia-boilerplate` | Returns the correct approved company description for a given context and length |
| `/algolia-blog` | Blog posts with SEO metadata, structure, code examples, CTA, and social snippets |
| `/algolia-landing` | Landing page content and HTML/CSS, assembled from Algolia's real section library |
| `/algolia-email` | Campaign, product-update, and nurture emails with subject-line variants and deliverability checks |
| `/algolia-social` | LinkedIn and X posts with platform-specific variants for A/B testing |
| `/algolia-deck` | Presentation decks with per-slide layout, visual notes, and speaker notes |
| `/algolia-case-study` | Customer stories in challenge–solution–results form |
| `/algolia-one-pager` | Single-page executive summaries and leave-behinds, 350-word cap |
| `/algolia-brief` | Campaign briefs for Marketing and ABX — audience, messaging, channels, budget, metrics |
| `/algolia-partner` | Co-branded partner collateral with dual-brand compliance rules |
| `/algolia-ui-copy` | Product UI microcopy: buttons, errors, empty states, tooltips, onboarding |

---

## How the shared reference works

`algolia-shared-reference/` is not a skill you invoke. It is the source of truth the others read at
runtime.

```
algolia-shared-reference/
  brand-core/
    tokens.md               themes, typography, shape, motion, logo and icon rules
    approved-stats.md       the ONLY place Algolia numbers live
    product-names.md        current product line, and what is retired
    messaging-framework.md  positioning, tagline, voice, editorial standards
    layout-patterns.md      Algolia's Figma landing-page section library
    colors_and_type.css     importable CSS custom properties
  content-templates/
    case-study.md           company inserts for customer stories
  examples/
    approved-descriptions.md  verbatim company boilerplate, four lengths
```

**To change a brand value, edit the one file that owns it.** Update a figure in
`approved-stats.md` and all thirteen skills use the new figure on their next run. Never patch a
number into an individual skill — that is exactly how these drifted out of date before.

---

## The two themes

Every skill declares which theme it emits. Picking the wrong one is the most common way branded
output goes wrong.

| Theme | Surfaces | Palette |
|---|---|---|
| **`marketing`** | Public-facing web: landing pages, blog, social, email, decks, case studies, partner pages | `#003DFF` primary · `#021046` headlines · `#2f3447` body · `#0e1224` dark bands · `#f7f8fb` wash. Sections sit on navy, kelly blue, white, or gray. **No purple** |
| **`deliverable`** | Documents you hand someone: reports, one-pagers, leave-behinds, product UI | `#003DFF` primary · `#5468FF` accent · `#23263B` text · `#F5F5F7` background · full severity system |

Rule of thumb: will a prospect see this on the open web? `marketing`. Is it a document or an app
screen? `deliverable`.

`/algolia-brand-check` takes `--theme marketing` or `--theme deliverable` and validates against that
theme only.

**Typography is Sora in both themes**, weights 300 / 400 / 600, from Google Fonts. Never Inter,
Roboto, DM Sans, Arial, system fonts, or serif faces. algolia.com does load Inter for site chrome —
cookie banner, mobile menu, figcaptions — but that is plumbing, not brand typography.

---

## Logos

**Not bundled with these skills.** Pull the current pack from Frontify —
[algolia.frontify.com](https://algolia.frontify.com) — which every Algolia employee can access.

Never redraw, recolor, stretch, or merge the mark into a combined lockup. Minimum clear space around
the wordmark is the height of the "a".

---

## Keeping this current

Brand data goes stale quietly, which is the failure mode this library exists to prevent. Every
reference file carries a `verified:` date and names its sources.

| What | Where to re-check |
|---|---|
| Stats | The "About Algolia" boilerplate on any release at `algolia.com/about/news/` — canonical, and it changes when the numbers do |
| Product names | Products and Solutions navigation on algolia.com. This shifts faster than anything else |
| Tokens, type | algolia.com plus the Frontify brand portal |
| Section library | Figma file `5DkPHASwX5HwFgG0WFEDhS`, "Landing Page options" |

When you check something, update the `verified:` date even if nothing changed. A stale date is the
signal that a re-check is overdue.

As of `2026-08-05` the approved figures are 1.75 trillion searches a year, 18,000+ businesses, 150+
countries, and 70+ data centers across 17 regions. If you see 17,000+ customers, 1.7 trillion
searches, or 30 billion records anywhere, it is out of date — `/algolia-brand-check` fails on all
three.

---

## Contributing

Found a value that is wrong or has moved? Fix it in `algolia-shared-reference/brand-core/`, update
the `verified:` date, and open a PR. Do not fix it inside an individual skill.
