# Sketch Explainer Style Guide

Use this reference to keep outputs consistent across models and hosts.

## Purpose

Create clear hand-drawn explainer images that help a person understand or teach a concept quickly. The output should feel like a smart teacher's sketch or an architect's field notebook: approachable, structured, and memorable.

This skill is best for:
- Concept explanations
- Educational visuals
- High-level process diagrams
- CEO-friendly summaries
- Visual metaphors
- Non-technical explainers

This skill is not the right tool for:
- Editable technical architecture diagrams
- Codebase-derived dependency maps
- Cloud infrastructure diagrams for engineering teams
- Precise system topology
- Documentation that must be maintained in draw.io, Mermaid, or diagrams.net

For those cases, propose an editable architecture-diagram workflow instead.

## Taste Rules

- Prioritize clarity over decoration.
- Use simple words a reader can scan in a few seconds.
- Keep labels short: 1-4 words where possible.
- Use one small icon per element, not icon clutter.
- Use arrows only when direction matters.
- Leave generous whitespace between elements.
- Avoid dense paragraphs inside the diagram.
- Make the title concrete and readable.
- Keep the visual logic obvious without requiring the user to read an explanation.
- For executive, team, governance, and architecture work, use the executive hand-drawn register from `executive-hand-drawn.md`: editorial restraint, functional objects, sparse figures, and no mascot-heavy composition.
- Treat characters as evidence of agency, not decoration. If removing a character leaves the meaning unchanged, prefer the simpler icon or object.

## Business And Technical Language

For mixed business and technical audiences, use a two-level hierarchy in every major stage:

- **Heading:** plain-language business meaning, outcome, or reader benefit.
- **Subheading:** precise technical implementation, component, contract, or execution environment.

The business heading answers "what is happening and why does it matter?" The technical subheading answers "what performs it?" This order makes the visual immediately legible while preserving engineering accuracy. Reverse the hierarchy only for an explicitly engineering-only audience.

Use plain-language relationships in visible headings and captions. Internal terms such as `edge`, `node`, `envelope`, schema suffixes, and version identifiers belong in secondary technical annotations, not in the main business story.

## Semantic Color System

- Color is a grouping language, not decoration.
- Define one color per stage, category, owner, or conceptual group.
- Reuse the same color wherever that group appears horizontally or vertically.
- Related business labels, technical components, data objects, and callouts share the same color family.
- Do not use one color for unrelated concepts or change a group's color between layers.
- Keep neutral connectors charcoal; use colored connectors only when they belong unambiguously to one group.
- Add a compact legend for any diagram where colors recur in multiple regions.

## Progressive Data Rules

If a store or memory layer receives information from several stages, show it as shared infrastructure rather than placing its final contents at the beginning. Color each stored record by the stage that creates it, and make the accumulation order visible. Clearly mark fields that are operational, reserved, or currently unused so the diagram does not overstate their role.

## Prompt Rules

Every prompt should specify:
- White (or warm off-white) background
- Hand-drawn sketch aesthetic
- Slightly imperfect lines
- Hand-lettered labels
- Pastel palette from the skill (or a brand palette override, see below)
- Clear layout format
- Element labels, icons, and captions
- No gradients
- No drop shadows
- No corporate polish

For a professional audience, also specify:

- Editorial strategy-sketch register
- Sparse, restrained figures
- Functional hand-inked objects and symbols
- No mascot styling, comic expressions, toy-like robots, or children’s-book illustration

## Brand Palette Override (v2 uplift)

When a diagram must match a specific brand/site, override the default pastels with that brand's palette and name each element's fill color EXPLICITLY in the prompt (per-box), rather than saying "pastel palette." Explicit per-box colors are what produce a clean, on-brand result.

Proven recipe (verified 2026-07: the "One Audit, Two Fixes" diagram regenerated for scratchpad.chowmes.com's fresh palette):
- Warm off-white paper background (not stark white) reads more premium and matches paper-toned sites.
- Assign one soft pastel fill per box, named directly (e.g. "soft blush-coral fill", "sunshine-yellow fill", "fresh pastel-green fill", "sky-blue fill", "soft lilac fill", "white fill").
- One small icon per box, named (magnifying-glass, shield-check, broom, gear-and-check).
- End with: "clean and cheerful, neat legible hand-lettered labels, generous whitespace, no gradients, no drop shadows, no corporate polish."
- Keep bullet text to 1-4 words so the image model renders it legibly (image models garble long text). ALWAYS view the generated image and check every label is legible + correct before shipping — regenerate if any text is garbled.

Model: `generate_image.py` uses `gemini-3.1-flash-image-preview` (falls back to `gemini-2.5-flash-image`). Needs `GEMINI_API_KEY`.

## Variant Rules

When the user asks for options, create two versions:
- Variant A: the clearest teaching version
- Variant B: the more memorable or metaphorical version

Do not create multiple variants by default. Multiple generated images increase cost and review noise.

## Non-Technical Topic Rules

For human, emotional, personal, coaching, business, or advisory topics:
- Prefer Linear Steps for a sequence of actions.
- Prefer Wheel for equal principles or habits.
- Prefer Concept Map for a broad mental model.
- Avoid technical words like pipeline, architecture, output, branch, and path unless they naturally fit.
- Do not force binary outcomes where the topic is actually a single journey.

## Quality Check

Before finalizing, ask internally:
- Would this be understandable if someone saw only the image?
- Is the chosen format natural for the topic?
- Are the labels short enough to render well?
- Is the diagram trying to be too precise for an image?
- Would an editable diagram be a better artifact?
