# Format: Layered Stack (Horizontal Bands)

## When to use
Use this format for topics that have **distinct layers, levels, or strata where each layer sits on top of or depends on the one below it** — especially when there's a visible/invisible split or an abstraction hierarchy. Great for: technology stacks, OSI model, system architecture, software layers (OS → runtime → app), organizational levels, abstraction levels in any domain.

This is the original default format of the sketch-explainer skill. Use it when the topic is fundamentally about "what sits on top of what."

**Keywords that suggest layered stack:** "stack", "layers", "built on top of", "underneath", "how X is structured", "architecture", "what's inside", "levels of abstraction", "under the hood"

## Layout description

3–6 horizontal color bands stacked vertically on a white background, hand-drawn in whiteboard sketch style.

**Band anatomy:**
- Each band spans the full width of the diagram
- Bold left-aligned layer name at the start of the band
- 2–4 white rounded-rectangle "chips" inside the band, each with a small sketch icon and a short label
- Short italic caption below the band in smaller text describing what that layer does
- Bands are clearly separated, with slightly irregular top/bottom edges (hand-drawn feel)

**Optional left annotation:**
- A vertical bracket or arrow on the left edge labeled "You see this ↑" at the top and "Never see this ↓" at the bottom
- Only include this when the topic has a genuine visible/invisible split (e.g., tech stacks, network layers)
- Omit for topics where all layers are equally observable

**Structure:**
- Title: large sketchy handwritten lettering at the top
- Bands stack from top (user-facing / most visible) to bottom (infrastructure / most hidden)
- Colors flow from warm to cool top-to-bottom: salmon → yellow → green → blue → lavender

**Visual feel:** Like a cross-section diagram. Each band is a distinct world. The stack communicates dependency and abstraction depth.

## Prompt structure

```
[Title] — hand-drawn whiteboard layered stack diagram titled "[Topic]" in large sketchy lettering at the top.

White background. [N] horizontal color bands stacked vertically, each spanning the full width. Pastel color scheme.

[Optional: On the far left, a vertical bracket with "You see this ↑" near the top bands and "Never see this ↓" near the bottom bands.]

Band 1 (top, salmon `#F4A896`): bold label "[layer name]" on the left. Inside: [N] white rounded chips — chip 1: icon [icon] label "[label]", chip 2: icon [icon] label "[label]" [...]. Below band: italic caption "[what this layer does]".

Band 2 (soft yellow `#F7E08A`): [same structure...]

Band 3 (sage green `#A8D5A2`): [same structure...]

[... continue for each band]

Band borders are slightly irregular hand-drawn lines. Chips have rounded corners and hand-drawn outlines.

Sketch aesthetic: slightly imperfect lines, hand-lettered labels, educational whiteboard style. No gradients, no drop shadows, no corporate polish.
```

## Color assignment guidance

Top to bottom (most visible → most hidden / most abstract → most concrete):
1. Salmon `#F4A896`
2. Soft yellow `#F7E08A`
3. Sage green `#A8D5A2`
4. Slate blue `#A8C5DA`
5. Lavender `#C5B8E8`

For fewer than 5 layers, pick the most fitting colors (don't force all 5).
