# Format Selection Guide

Use this reference to choose the right layout for any topic. Read the topic, ask yourself the key question, then pick the format.

## The Decision Tree

First ask whether the user needs a conceptual image or an editable technical artifact. If they need an engineering architecture diagram, repository map, cloud topology, or code-derived system view, do not force this image skill. Recommend Mermaid, draw.io, or diagrams.net instead.

**Does the topic have layers or strata where one thing sits on top of another?**
→ Use **Layered Stack** (`layered-stack.md`)
→ Examples: tech stacks, OSI model, app architecture, abstraction levels

**Does the topic involve a decision or branching — "what happens if X?"**
→ Use **Flowchart** (`flowchart.md`)
→ Examples: debugging steps, request routing, approval workflows, compiler logic

Avoid Flowchart for emotional, coaching, or relationship topics unless there are true decision points. A single journey with advice is usually Linear Steps, Wheel, or Concept Map.

**Is it a sequence of ordered steps that must happen in a fixed order?**
→ Use **Linear Steps** (`linear-steps.md`)
→ Examples: tutorials, setup guides, lifecycle stages, recipe steps, deployment pipelines

**Is it a central concept with several equal, surrounding components?**
→ Use **Wheel** (`wheel.md`)
→ Examples: pillars of a framework, skills in a discipline, ecosystem components, values of a system

**Is it a comparison across items, or a set of parallel things with the same structure?**
→ Use **Grid / Matrix** (`grid.md`)
→ Examples: tool comparisons, feature tables, pros/cons, 2×2 quadrants, cheat sheets

**Is it a rich, interconnected topic where ideas relate to each other in many ways?**
→ Use **Concept Map** (`concept-map.md`)
→ Examples: subject overviews, mental models, brainstorm maps, "everything about X"

---

## Quick Reference Table

| Format | Best For | Key Signal |
|--------|----------|------------|
| Layered Stack | Abstraction hierarchy, "built on top of" | Layers, stacks, infrastructure |
| Flowchart | Conditional logic, branching decisions | "If", "decide", "what happens when" |
| Linear Steps | Ordered sequence, step-by-step | Numbers, order matters, tutorials |
| Wheel | Equal components around a center | Pillars, ecosystem, "all aspects of" |
| Grid / Matrix | Comparison, parallel items | "vs", "compare", "types of" |
| Concept Map | Rich associations, landscape of a topic | "Everything about", "overview", no clear order |

---

## Tiebreaker rules

- If the topic could be **Layered Stack OR Linear Steps**: ask whether the layers are independent strata (stack) or must be followed in order (linear steps). A tech stack is not a tutorial; a deployment pipeline is not an architecture diagram.
- If the topic could be **Wheel OR Concept Map**: ask whether the surrounding elements are flat and equal (wheel) or have sub-structure and relationships between them (concept map).
- If the topic could be **Grid OR Concept Map**: ask whether there's a clear comparison dimension (grid) or whether it's more exploratory (concept map).
- When genuinely ambiguous, prefer whichever format makes the **relationships between elements** most obvious to a reader seeing it cold.
- For non-technical topics, prefer the format that feels natural to the audience, not the format that resembles a software diagram.
