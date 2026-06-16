# Format: Flowchart

## When to use
Use this format for topics that describe a **decision process, branching logic, or conditional flow** — anything where the answer to "what happens next?" depends on a condition. Great for: debugging steps, approval workflows, algorithms, troubleshooting guides, how a request gets routed, how a compiler decides what to do.

**Keywords that suggest flowchart:** "how does X decide", "what happens if", "process for", "steps to approve", "how to diagnose", "decision tree"

## Layout description

A vertical or slightly diagonal flow of connected shapes on a white background, hand-drawn in whiteboard sketch style.

**Shapes used:**
- Rounded rectangles (pill shapes) for start/end nodes — drawn in salmon/peach `#F4A896`
- Diamond shapes for decision points — drawn in soft yellow `#F7E08A`
- Regular rectangles for action steps — drawn in sage green `#A8D5A2`, slate blue `#A8C5DA`, or lavender `#C5B8E8`
- Arrows connecting shapes: slightly wobbly hand-drawn lines with arrowheads
- "Yes" / "No" labels (or equivalent) in small italic handwritten text beside the arrows leaving each diamond

**Structure:**
- Title: large sketchy handwritten lettering at the top
- Flow starts at top, progresses downward (or in a Z/S shape if many branches)
- Decision diamonds branch left (one path) and right (another path) or down/side
- Paths reconverge where they logically merge, or end in distinct terminal nodes
- Each shape has a short bold label inside (2–6 words max)
- Small italic captions can appear beside key steps to add context

**Visual feel:** Slightly imperfect lines, arrows that look drawn by hand, diamonds that aren't perfectly symmetrical. Approachable, not sterile.

## Prompt structure

```
[Title] — hand-drawn whiteboard flowchart titled "[Topic]" in large sketchy lettering at the top.

White background. Flowchart layout with hand-drawn shapes and wobbly connecting arrows. Pastel color scheme.

Start node: rounded pill shape in salmon/peach at the top labeled "[start label]".

Decision node 1: yellow diamond labeled "[condition?]" — arrow labeled "Yes" leads to [action], arrow labeled "No" leads to [action].

[Continue describing each node and connection in sequence...]

End node(s): rounded pill in [color] labeled "[end label]".

Sketch aesthetic: slightly imperfect lines, hand-lettered labels, educational whiteboard style. No gradients, no drop shadows, no corporate polish.
```

## Color assignment guidance

- Start / End nodes: salmon `#F4A896`
- Decision diamonds: soft yellow `#F7E08A`
- Action steps: rotate through sage green `#A8D5A2`, slate blue `#A8C5DA`, lavender `#C5B8E8`
- Arrow lines: dark charcoal/near-black, hand-drawn weight
