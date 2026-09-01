# Algolia landing page section library

**Source:** Algolia Figma file `5DkPHASwX5HwFgG0WFEDhS` — "Landing Page options"
`https://www.figma.com/design/5DkPHASwX5HwFgG0WFEDhS/Landing-Page-options`

`verified: 2026-07-15` — **derived from archived page renders, not re-pulled live.** See
*Re-verifying* at the bottom. Treat structure as reliable and exact pixel values as approximate.

Palette: the single 2026 Xenon palette. See `tokens.md` / `colors_and_type.css`. Use token names, never inline hexes, when building.

This is Algolia's own modular section library: named, swappable hero / body / footer blocks that
assemble into a landing page per campaign or per prospect. **Build from this catalog. Do not invent
section structures.** A page is a stack of these, not a bespoke layout.

---

## The background rule

Every section sits on exactly one of four backgrounds:

**dark-blue** (`--bg-dark-blue` `#000033`) · **Xenon Blue band** (`--xenon-blue` `#0067F7`) · **white** (`--bg-white`) · **light-gray** (`--bg-light-gray` `#F6F6F6`)

Alternate for rhythm. Two adjacent sections should not share a background unless they read as one
block. Dark sections take on-dark type (`--fg-on-dark`); light sections take ink headlines (`--ink` `#000033`) and body text (`--fg1`).

---

## Hero variants

| Variant | Structure | Use when |
|---|---|---|
| **Hero + image, two CTAs** | Navy background. Eyebrow label in blue, H1, one-line subhead, primary + secondary CTA. Product UI screenshot to the right. | Default. The workhorse hero. |
| **Title and subtitle only** | Navy, centered. Algolia wordmark above, H1, single line of detail beneath. CTAs optional. | Events, dinners, announcements — anything where the title *is* the message. |
| **Form in hero, single column** | Navy. Headline, supporting paragraph, source attribution on the left. Form stacked in one column on the right. | Gated content with 4+ fields. |
| **Form in hero, two column** | Navy. Headline and longer body left. Form in a **white card** with paired fields, two across. | Gated content where the form should feel light. The white card is what makes a long form approachable. |
| **Xenon Blue full-bleed** | Entire hero `--xenon-blue` (`#0067F7`). Centered wordmark, small uppercase eyebrow, very large H1 (often the prospect's name), one line of body, single white CTA. Full site nav retained above. | Named-account and ABM pages. The highest-impact variant. |

**Nav is optional on every hero.** The Figma notes call this out explicitly — remove it for
campaign pages where the only valid action is the CTA.

CTA pattern: primary is a filled button, secondary is a white or outlined button beside it.
"Request demo" + "Get started" is the canonical pair.

---

## Body variants

| Variant | Structure | Use when |
|---|---|---|
| **Form with image or text beside it** | Asset thumbnail or descriptive copy on one side, form on the other. | Report and whitepaper downloads below the fold. |
| **Left / right split** | Image one side, copy the other. Alternate sides down the page. Valid on navy, kelly blue, white, or gray. | The default body block. |
| **2, 3, or 4 column** | Equal-width cards or copy blocks. | Feature grids, benefit sets, agenda items. |
| **Single column with bullets** | Centered heading, bulleted list beneath, each bullet with a check or icon marker. | Agendas, "what you'll learn", requirements. |
| **People cards** | Photo, name, title per card, in a row. | Speakers, executives, hosts. |
| **Accordions** | Stacked collapsible rows. First row open by default, heading bold, body inside. | "Key benefits", FAQs, capability lists that would otherwise run long. |
| **Accordions with images** | Same, plus a paired image that swaps as each row opens. | Feature deep-dives where each point has a visual. |
| **Video or interactive demo** | Full-width embed on a light gray band, captioned above. | "See it in action". |

---

## Footer variants

| Variant | Structure |
|---|---|
| **Plain CTA footer** | Xenon Blue `--xenon-blue` (`#0067F7`) band: headline left, "Request demo" + "Get started" right as white buttons. Dark-blue nav block beneath in five columns — Solutions, Developers, Integrations, Industries, Company. |
| **Alt footer** | Same layout, but the CTA band carries the blue→cyan→teal gradient blob treatment instead of flat blue. |

**Footers, including the navigation block, can be removed entirely** — same note as the hero nav.
Campaign pages often ship with the CTA band and nothing below it.

Footer nav column contents, as shown: Solutions (Overview, AI Search, AI Browse) · Developers
(Developer Hub, Documentation, Integrations) · Integrations (Salesforce Commerce Cloud B2C, Shopify,
Adobe Commerce) · Industries (Overview, B2C ecommerce, B2B ecommerce) · Company (About Algolia,
Careers, Newsroom).

---

## Assembling a page

1. Pick one hero.
2. Stack 3–6 body variants, alternating background per the four-background rule.
3. Close with a footer variant, or just the CTA band.

Keep one primary action for the whole page. Every CTA on it should point at the same next step.

---

## Re-verifying

The catalog above was read from renders archived 2026-07-15, not from a live Figma pull. To refresh:

1. Ensure the Figma MCP server is enabled for your working directory
   (`{"figma": {"type": "http", "url": "https://mcp.figma.com/mcp"}}` in `.mcp.json`) and restart
   Claude Code — project-scoped MCP servers load only at startup.
2. Read file `5DkPHASwX5HwFgG0WFEDhS` and diff the section inventory against this file.
3. If the library has moved, **the live file wins.** Update this file and the `verified:` date.
