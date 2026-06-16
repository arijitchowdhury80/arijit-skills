# Format: Concept Map / Mind Map

## When to use
Use this format for topics that are **rich, interconnected, and don't have a strict order or hierarchy** — where the goal is to show relationships, associations, and the full landscape of a concept. Great for: brainstorming outputs, subject overviews, "everything about X", mental models, fields of study, how ideas relate to each other, when the user wants to understand the breadth of something.

**Keywords that suggest concept map:** "everything about", "overview of", "all the parts of", "what is X really", "map of", "mindmap", "brain dump", "what connects to what", "how does X relate to Y"

## Layout description

A central node with branches radiating outward, each branch spawning sub-branches, on a white background, hand-drawn in whiteboard sketch style.

**Unlike the wheel** (which has equal, flat spokes), a concept map has **hierarchical branching** — branches have sub-branches, and the depth reflects importance and specificity.

**Core anatomy:**
- **Central node**: a slightly imperfect hand-drawn oval or rectangle in salmon `#F4A896` containing the main topic (bold, 1–3 words)
- **Primary branches**: 3–6 main themes or categories radiating from the center, each in a distinct pastel color
  - Each primary branch ends in a rounded rectangle or oval with a bold label
  - The connecting line is a curved or slightly wobbly line, labeled with a relationship phrase (e.g., "includes", "depends on", "leads to") in tiny italic text along the line
- **Secondary branches**: 2–3 sub-concepts hanging off each primary branch
  - Smaller, lighter nodes in the same hue family as the parent but slightly lighter
  - Short 1–3 word labels
- **Connecting lines**: curved, hand-drawn, with optional arrow tips where direction matters

**Optional icons:** small sketch icons inside or beside key nodes to make them more memorable.

**Structure:**
- Title: large sketchy handwritten lettering at the top or in a corner (not the center — that's the main node)
- Layout is organic, not perfectly symmetrical — this is intentional, mirrors how ideas actually spread
- Avoid crossing lines where possible; if unavoidable, one line hops over the other

**Visual feel:** Sprawling but readable. The hand-drawn style is especially important here — perfect geometry would make this feel like software output; the wobbly lines make it feel like thinking.

## Prompt structure

```
[Title] — hand-drawn whiteboard concept map titled "[Topic]" in large sketchy lettering in the top corner.

White background. Organic mind-map / concept-map layout centered on a main node. Pastel color scheme. Curved, slightly wobbly connecting lines.

Central node: hand-drawn oval in salmon `#F4A896`, bold label "[main topic]".

Primary branch 1 (soft yellow `#F7E08A`): curved line from center labeled "[relationship]", ends in rounded rectangle labeled "[branch name]". Sub-branches: "[sub 1]", "[sub 2]", "[sub 3]".

Primary branch 2 (sage green `#A8D5A2`): curved line from center labeled "[relationship]", ends in rounded rectangle labeled "[branch name]". Sub-branches: "[sub 1]", "[sub 2]".

Primary branch 3 (slate blue `#A8C5DA`): [same structure...]

Primary branch 4 (lavender `#C5B8E8`): [same structure...]

[... up to 6 primary branches]

Connecting lines are curved and hand-drawn. Sub-branch nodes are smaller than primary nodes. Relationship labels along lines are in tiny italic text.

Sketch aesthetic: organic layout, slightly imperfect shapes, hand-lettered labels, educational whiteboard style. No gradients, no drop shadows, no corporate polish.
```

## Color assignment guidance

- Central node: salmon `#F4A896`
- Primary branches: soft yellow → sage green → slate blue → lavender (cycle if >4)
- Sub-branch nodes: same color family as parent, slightly desaturated or lighter in prompt description
- Connecting lines: dark charcoal, hand-drawn, curved
