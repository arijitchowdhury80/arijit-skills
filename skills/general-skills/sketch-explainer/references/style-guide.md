# Sketch Explainer Style Guide

Use this reference to keep outputs consistent across models and hosts.

## Purpose

Create clear whiteboard-style explainer images that help a person understand or teach a concept quickly. The output should feel like a smart teacher's sketch: approachable, structured, and memorable.

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

## Prompt Rules

Every prompt should specify:
- Textured cold-press **watercolor-paper** background, warm off-white (never flat pure white)
- **Hand-painted watercolor aesthetic** — translucent washes, soft feathered edges, gentle blooms
- **Light, airy, diluted tints** with a soft gradient inside each wash (paper glowing through); never dull or over-saturated flat fills
- Hand-lettered ink labels (charcoal/sepia), legible
- Loose hand-painted icons with visible brush strokes
- Clear layout format
- Element labels, icons, and captions
- **Full composition inside the frame — generous margins on all sides, nothing cropped or running off the edge**
- No flat solid fills, no drop shadows, no digital gloss/corporate polish

**Framing note (prevents the #1 failure — content cut off):** the image model will crop a busy layout if not told otherwise. Always state that the whole diagram must fit within the canvas with padding around every edge, and match orientation to the layout — **portrait for tall vertical stacks (5–8 steps), landscape for horizontal ribbons/wheels/grids.**

## Brand Palette Override (v2 uplift)

When a diagram must match a specific brand/site, override the default pastels with that brand's palette and name each element's fill color EXPLICITLY in the prompt (per-box), rather than saying "pastel palette." Explicit per-box colors are what produce a clean, on-brand result.

Proven recipe (verified 2026-07: the "One Audit, Two Fixes" diagram regenerated for scratchpad.chowmes.com's fresh palette):
- Warm off-white paper background (not stark white) reads more premium and matches paper-toned sites.
- Assign one soft pastel fill per box, named directly (e.g. "soft blush-coral fill", "sunshine-yellow fill", "fresh pastel-green fill", "sky-blue fill", "soft lilac fill", "white fill").
- One small icon per box, named (magnifying-glass, shield-check, broom, gear-and-check).
- End with: "clean and cheerful, neat legible hand-lettered labels, generous whitespace, no gradients, no drop shadows, no corporate polish."
- Keep bullet text to 1-4 words so the image model renders it legibly (image models garble long text). ALWAYS view the generated image and check every label is legible + correct before shipping — regenerate if any text is garbled.

Model: `generate_image.py` uses OpenAI `gpt-image-2` (falls back to `gpt-image-1`, then Gemini `gemini-3.1-flash-image-preview` if configured). Needs `OPENAI_API_KEY` in `~/.claude/skills/sketch-explainer/.config/.env.local`. Overrides: `SKETCH_IMAGE_SIZE` (portrait `1024x1536` for tall stacks; landscape `1536x1024` otherwise), `SKETCH_IMAGE_QUALITY`.

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
