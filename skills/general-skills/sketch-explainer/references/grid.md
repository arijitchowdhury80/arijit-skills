# Format: Grid / Matrix

## When to use
Use this format for topics that have **multiple parallel items that each share the same structure**, or when comparing things across two dimensions. Great for: comparing options/tools/frameworks, feature breakdowns, pros/cons tables, quadrant analyses (2×2), category overviews, glossaries of related concepts, cheat sheets.

**Keywords that suggest grid:** "compare", "vs", "differences between", "options for", "types of", "categories", "which should I use", "overview of", "cheat sheet"

## Layout description

A structured grid of cells on a white background, hand-drawn in whiteboard sketch style. Can be a simple N-column layout or a 2×2 quadrant.

**Two sub-variants:**

### Variant A: Card Grid (N columns × M rows)
- Each "card" is a rounded rectangle with consistent sizing
- Cards arranged in rows and columns (e.g., 2×3, 3×2, 2×4)
- Each card contains: a bold title at top, a small sketch icon, and 2–4 bullet points or short phrases
- Each column or row can share a pastel color to group related items
- Column headers (if used): bold labels above each column, underlined or circled in charcoal

### Variant B: 2×2 Quadrant
- Four equal quadrants divided by two perpendicular hand-drawn axes
- Axis labels at the ends of each line (e.g., "Simple ←→ Complex", "Low ↑ High")
- Each quadrant has a distinct pastel background fill and a bold label in the corner
- Items or concepts are placed as small labeled dots or chips within the appropriate quadrant
- Title in the center where axes cross, or at the very top

**Structure (Card Grid):**
- Title: large sketchy handwritten lettering at the top
- Grid of rounded-rectangle cards, each in a pastel color
- Bold item name at top of each card
- Small sketch icon (relevant to the item)
- 2–4 short bullet traits or keywords inside the card

**Visual feel:** Organized and scannable, but still hand-drawn. Cards have slightly irregular borders. Not a spreadsheet — a thoughtful sketch.

## Prompt structure (Card Grid)

```
[Title] — hand-drawn whiteboard grid diagram titled "[Topic]" in large sketchy lettering at the top.

White background. [N]-column card grid layout. Pastel color scheme. Each card is a rounded rectangle with hand-drawn borders.

Row 1:
  Card 1 ([color]): Title "[name]", icon [icon], bullets: [trait 1], [trait 2], [trait 3]
  Card 2 ([color]): Title "[name]", icon [icon], bullets: [trait 1], [trait 2], [trait 3]
  [...]

Row 2:
  [...]

Sketch aesthetic: slightly imperfect card borders, hand-lettered labels, educational whiteboard style. No gradients, no drop shadows, no corporate polish.
```

## Prompt structure (2×2 Quadrant)

```
[Title] — hand-drawn whiteboard 2×2 quadrant diagram titled "[Topic]" in large sketchy lettering at the top.

White background. Two perpendicular hand-drawn axes dividing the space into four quadrants.

X-axis label: "[left label] ←——→ [right label]"
Y-axis label: "[bottom label] ↕ [top label]"

Top-left quadrant (salmon `#F4A896`): labeled "[quadrant name]", contains: [items]
Top-right quadrant (soft yellow `#F7E08A`): labeled "[quadrant name]", contains: [items]
Bottom-left quadrant (sage green `#A8D5A2`): labeled "[quadrant name]", contains: [items]
Bottom-right quadrant (slate blue `#A8C5DA`): labeled "[quadrant name]", contains: [items]

Sketch aesthetic: slightly imperfect lines, hand-lettered labels, educational whiteboard style.
```

## Color assignment guidance

- Card Grid: assign one pastel per column or per row to create grouping. Rotate: salmon → yellow → green → blue → lavender.
- 2×2 Quadrant: one pastel per quadrant (salmon, yellow, green, blue).
- Card borders and axis lines: dark charcoal, hand-drawn weight.
