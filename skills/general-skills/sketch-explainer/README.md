# Sketch Explainer

Create professional, hand-drawn visual explainers that make a system understandable to both business and technical audiences.

Sketch Explainer is not a generic cartoon generator. It turns an approved body of facts into a clear visual story, selects an appropriate diagram structure, writes a production-ready image prompt, and can generate the final raster image when an image tool is available.

## What it creates

- Executive-friendly system and operating-model explainers
- Technical concepts expressed in business-readable language
- Process flows, decision trees, layered systems, comparison grids, wheels, and concept maps
- Consistent diagram families for a product, program, or presentation
- Image prompts that can be handed to an image model or human illustrator
- Final images when the runtime provides image generation or `GEMINI_API_KEY`

## Core design contract

Every professional explainer follows the same rules:

1. **Meaning before styling.** Lock the facts, stage order, ownership, inputs, outputs, and connectors before changing the visual treatment.
2. **Business meaning first.** Use a plain-language stage heading, followed by a smaller technical subheading naming the mechanism.
3. **Color carries meaning.** One semantic group owns one watercolor family everywhere it appears. Color is not rotated merely for decoration.
4. **Hand-drawn does not mean cartoon.** The default professional register uses disciplined ink, restrained figures, functional objects, pale watercolor washes, and generous white space.
5. **Characters are supporting notation.** Use people or agents only when they explain ownership, interaction, or role. Avoid mascot-heavy storytelling.
6. **Brand assets are exact.** Never ask an image model to redraw a company logo. Composite the official asset deterministically after generation.
7. **Recurring actors stay consistent.** The same platform, agent family, storage object, packet, or interface must remain recognizable across related diagrams.
8. **Approved baselines are protected.** Make variants from a copy, preserve semantic invariants, and verify the final image at original resolution before promotion.

## Illustration registers

| Register | Use it for | Visual treatment |
|---|---|---|
| **Executive hand-drawn** | Leadership, architecture, governance, strategy, team communication | Restrained editorial sketch, sparse figures, functional icons, quiet watercolor grouping |
| **Teaching sketch** | Onboarding, learning, public explanation | Warmer and slightly more expressive, with a few visual metaphors |
| **Character-led explainer** | Stories where human or agent interaction is the subject | Recurring characters carry the narrative; use only when explicitly justified |

The executive hand-drawn register is the default for professional work.

## Supported structures

| Structure | Best for |
|---|---|
| **Linear steps** | Ordered sequences and tutorials |
| **Flowchart** | Decisions, branching, and conditional paths |
| **Layered stack** | Architecture layers and dependency relationships |
| **Grid / matrix** | Parallel stages, comparisons, and 2x2 or 2x3 systems |
| **Wheel** | Equal components surrounding one central concept |
| **Concept map** | Rich associations and topic landscapes |

Dense four-to-six-stage systems should usually use a 2x2 or 2x3 narrative matrix instead of narrow vertical columns. The reader should understand the whole journey before entering the implementation details.

## Example output

These two approved diagrams demonstrate the current visual system and its cross-asset consistency rules:

### Personalized concierge engagement

![How personalized concierge engagement works](examples/how-personalized-concierge-engagement-works.png)

### Three-judge quality framework

![How judges work](examples/how-judges-work.png)

The examples are reference outputs, not hard-coded templates. Their subject matter is project-specific; the reusable method is encoded in `SKILL.md` and the reference files.

## How to use it

Ask naturally, for example:

- `Draw how this architecture works for executives and engineers.`
- `Explain this six-stage process as a professional hand-drawn diagram.`
- `Turn this workflow into a 2x2 visual with business headings and technical subheadings.`
- `Create a second diagram that uses the same agents, colors, and visual language as the approved first diagram.`

The skill returns:

1. The selected diagram format and why it fits
2. A structured topic breakdown for factual review
3. A detailed image-generation prompt
4. A second variant only when requested
5. The generated image when requested and supported

## File map

| Path | Purpose |
|---|---|
| [`SKILL.md`](SKILL.md) | Runtime instructions and the complete visual-generation workflow |
| [`references/business-technical-system.md`](references/business-technical-system.md) | Content contract for business and technical system explainers |
| [`references/executive-hand-drawn.md`](references/executive-hand-drawn.md) | Professional middle ground between sterile architecture and cartoon illustration |
| [`references/style-guide.md`](references/style-guide.md) | Durable visual language, semantic color, and quality rules |
| [`references/format-selection.md`](references/format-selection.md) | Decision guide for selecting a diagram structure |
| [`references/grid.md`](references/grid.md) | Grid, 2x2, and 2x3 layout guidance |
| [`references/flowchart.md`](references/flowchart.md) | Decision and branching layouts |
| [`references/linear-steps.md`](references/linear-steps.md) | Sequential process layouts |
| [`references/layered-stack.md`](references/layered-stack.md) | Layer and dependency layouts |
| [`references/wheel.md`](references/wheel.md) | Hub-and-spoke layouts |
| [`references/concept-map.md`](references/concept-map.md) | Association and landscape layouts |
| [`scripts/generate_image.py`](scripts/generate_image.py) | Optional Gemini image-generation helper |
| [`examples/`](examples/) | Approved reference outputs demonstrating the current visual system |

## Generate an image locally

The agent should use the host runtime's native image tool when available. The bundled fallback requires Python, `google-genai`, and `GEMINI_API_KEY`:

```bash
pip install google-genai
export GEMINI_API_KEY="..."
python3 scripts/generate_image.py "<full image prompt>"
```

Generated files are written to `sketch_explainer_output/` in the current working directory. Never place API keys inside the skill folder.

## Validation

Validate the skill structure after changing instructions or references:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/general-skills/sketch-explainer
```

For a final diagram, validation is visual as well as structural: inspect the original-resolution image, compare every label and connector with the approved factual baseline, verify official logos, and reject unexplained changes in emphasis or ownership.
