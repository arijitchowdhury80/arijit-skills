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
- White background
- Hand-drawn sketch aesthetic
- Slightly imperfect lines
- Hand-lettered labels
- Pastel palette from the skill
- Clear layout format
- Element labels, icons, and captions
- No gradients
- No drop shadows
- No corporate polish

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
