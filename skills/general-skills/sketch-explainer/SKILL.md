---
name: sketch-explainer
description: Generates hand-drawn explainer diagram prompts and images for technical or non-technical topics, including restrained executive strategy sketches. Use when the user asks to explain something visually, make a diagram, sketch or whiteboard how something works, create an explainer, or produce an executive-friendly hand-drawn system visual.
---

# Sketch Explainer

Your job is to take a topic and produce two things:
1. A **structured breakdown** of the topic into its key components
2. A **detailed image-generation prompt** describing a whiteboard-sketch explainer diagram in the exact style described below

This is an image explainer skill, not a technical architecture documentation skill. Use it for CEO-friendly explanation, learning, teaching, visual summaries, and conceptual diagrams. If the user asks for a technical architecture diagram from code, cloud services, repositories, deployment topology, or something they need to edit later, recommend an editable Mermaid/draw.io/diagrams.net output or a separate architecture-diagram skill instead of producing only a raster image prompt.

For a system, operating model, AI workflow, or architecture that must serve business and technical audiences together, read `references/business-technical-system.md` before decomposing the topic. That reference governs the content contract, narrative hierarchy, stage layout, ownership marks, shared inputs, and approval-safe revision process.

For an executive, leadership, team-facing, governance, or architecture explainer, also read `references/executive-hand-drawn.md`. Its restrained editorial treatment is the default for professional audiences; do not default to mascot-heavy or cartoon storytelling.

## The Target Visual Style

The output should look like a smart teacher drew it on a whiteboard — clean, informal, educational, and visually clear. Hand-drawn but intentional. Not a corporate slide. Not a technical architecture doc. A beautiful diagram you'd want to photograph and share.

**Core style rules (apply to all formats):**
- White background
- Hand-drawn / sketch aesthetic throughout — slightly imperfect lines, wobbly edges, hand-lettered labels
- Pastel color palette (see Palette Reference below) — these exact colors, always
- Title: large, slightly imperfect handwritten-style lettering at the top
- Minimal sketch icons inside elements: gear, arrow, magnifying glass, clock, microchip, dumbbell, waveform, stacked layers, checkmark, etc.
- No glossy digital gradients, synthetic bevels, or corporate presentation polish. Natural watercolor tonal transitions are allowed inside a semantic color family. Subtle hand-painted grounding shadows may be used beneath functional objects when they improve depth without becoming decorative.
- Overall feel: clear, warm, intelligent, and hand-made. For professional audiences, favor editorial restraint over whimsy.

### Choose the illustration register

Use one register deliberately:

- **Executive hand-drawn (default for professional work):** disciplined ink linework, restrained hand lettering, functional objects, pale watercolor grouping, sparse people or agent silhouettes, and generous white space. It should feel like a strategist or architect drew it in a field notebook.
- **Teaching sketch:** warmer and more playful, with a few expressive figures or visual metaphors. Use for learning, onboarding, or broad public education.
- **Character-led explainer:** recurring characters carry the story. Use only when the user explicitly asks for character storytelling or the human interaction itself is the subject.

Do not let “hand-drawn” silently become “cartoon.” A professional diagram may contain characters, but they are supporting notation, not mascots or the dominant visual language.

## Step 1: Choose the right format

Read the topic, then consult `references/style-guide.md` and `references/format-selection.md` to pick the best layout. There are six options:

| Format | File | Best For |
|--------|------|----------|
| **Layered Stack** | `references/layered-stack.md` | Abstraction layers, tech stacks, "built on top of" |
| **Flowchart** | `references/flowchart.md` | Decision logic, branching, "what happens if" |
| **Linear Steps** | `references/linear-steps.md` | Ordered sequences, tutorials, step-by-step guides |
| **Wheel** | `references/wheel.md` | Equal components around a center concept |
| **Grid / Matrix** | `references/grid.md` | Comparisons, parallel items, 2×2 quadrants |
| **Concept Map** | `references/concept-map.md` | Rich associations, landscape of a topic |

Read the selected format's reference file to understand the exact layout, shape anatomy, and prompt structure before writing anything.

For non-technical, human, emotional, or advisory topics, do not force technical labels like "path A/path B", "output A/output B", "system", "pipeline", or "architecture" unless the user explicitly asks for that framing. Prefer linear steps, wheel, or concept map layouts with plain-language labels.

For a dense ordered system with four to six stages, do not default to one narrow column per stage. Use the business-technical system reference to choose a 2x2 or 2x3 narrative matrix that preserves readable type and a clear sequence.

## Step 2: Decompose the topic

Break the topic into its meaningful parts using the structure appropriate to the chosen format:
- **Layered Stack**: 3–6 layers from visible to hidden
- **Flowchart**: nodes, decision points, and the paths between them
- **Linear Steps**: 3–8 ordered steps with clear names and what happens in each
- **Wheel**: the central concept + 4–8 surrounding components
- **Grid**: the items being compared and the attributes they share
- **Concept Map**: the central topic + 3–6 primary branches + sub-branches

Name each element clearly. For each element, identify a simple sketch-able icon.

### Dual-audience label hierarchy

For architecture, workflow, data, and operating-model explainers, make every major stage understandable at two levels:

1. **Primary heading: business meaning** — what this stage accomplishes for the visitor, operator, or business.
2. **Secondary subheading: technical mechanism** — the code, service, agent, storage layer, protocol, or contract that performs it.

Example:

- **Remember the journey**
- `Browser JavaScript: tracker + local/session storage`

Use technical-first hierarchy only when the intended audience is explicitly engineering-only or the user asks for it. Do not make the reader decode implementation names before understanding why a stage exists.

Prefer plain-language relationship labels over internal graph or implementation jargon. For example, use **"Last page move: Grocery -> H-E-B"** as the visible label and place `navigation edge` only in a small technical sublabel when that term is genuinely useful.

### Semantic color grouping

Color must encode meaning, not decorate individual boxes:

- Assign one color to each business stage, category, or conceptual group.
- Reuse that exact color for every related item across rows, columns, rails, overlays, legends, and data-flow callouts.
- Use a different color only when the meaning or ownership changes.
- Never rotate colors merely to make adjacent boxes look different.
- Include a compact legend whenever a color appears in more than one part of the diagram.
- Keep neutral arrows, boundaries, and cross-stage connectors charcoal unless a connector clearly belongs to one stage.

For a 2x2 process matrix, each quadrant is one semantic stage. Any business label, technical component, data object, and supporting icon owned by that stage uses the quadrant's color family consistently.

### Semantic emphasis invariants

Visual hierarchy is part of the diagram's meaning and must survive every style, layout, or character edit:

- Preserve established distinctions such as primary vs optional, active vs inactive, current vs historical, and deterministic code vs AI agent.
- Render primary inputs with stronger contrast and saturation. Render optional or supporting inputs with visibly lower contrast, lighter ink, or a neutral/faded treatment while keeping labels legible.
- Never equalize two elements merely because a new watercolor, sketch, or branding treatment is being applied.
- Before replacing an approved diagram, compare every visible label, connector, actor, and emphasis cue against the approved baseline. Treat any unexplained change as a regression.
- When an image edit is intentionally narrow, state the invariants explicitly and verify the final image before making it canonical.

### Watercolor presentation treatment

When the user selects a watercolor treatment for an explainer:

- Use subtle cold-pressed watercolor paper rather than a flat gray or digitally tinted background.
- Define major semantic stages with broad translucent watercolor washes and naturally imperfect brush edges. Do not put rigid dark rectangular borders around the large stage areas.
- Keep fine charcoal ink outlines around small functional diagrams, controls, books, packets, and other elements when they improve legibility.
- Preserve semantic color ownership across the watercolor washes, summary rails, callouts, and supporting artifacts.
- For a process explainer, place the concise journey summary directly below the title and subtitle, then place the detailed stage explanations underneath it. The reader should understand the whole journey before entering the implementation detail.
- Remove captions that merely repeat what the title, subtitle, summary rail, or stage labels already communicate. Reclaim that space for the explanation.

The watercolor treatment should feel hand-painted and executive-ready, not whimsical: restrained paper texture, strong contrast, generous white space, natural pigment blooms, and no glossy digital gradients, hard drop shadows, gray corporate panels, or decorative clutter. A restrained tonal transition within one watercolor wash and a soft grounding shadow beneath a functional object are acceptable.

### Semantic actor identity

People, software, and AI agents must remain visually distinct:

- Use human figures for visitors, customers, operators, and other real people.
- Make AI ownership legible without making AI the visual subject by default. A small Agent Studio mark, headset badge, role icon, or subtle mechanical cue is often enough.
- Use one consistent robot character only when agent embodiment is central to the explanation. Do not fill a diagram with large robots merely because several stages use agents.
- Distinguish Agent Studio roles through their task and surrounding artifacts, not through different robot identities. For example, a Greetings Agent may use conversation bubbles and choices, while an Orchestrator may hold a context bundle containing the journey, greeting, choices, and response.
- When the named persona is aRRIe, depict a warm professional robot concierge with a small cap, over-ear headphones, and a bow tie. Keep the design approachable and clearly mechanical, never childish or science-fictional.
- Use non-character symbols for deterministic code and transport: rulebooks or control signals for controllers, envelopes or packets for handoff, and storage vessels for browser memory.

For executive hand-drawn diagrams:

- Prefer objects, symbols, role cards, and small head-and-shoulder figures over full-body characters.
- Keep faces minimal and emotionally restrained. Use a brow, mouth line, posture, or surrounding artifact to show a role; avoid exaggerated yelling mouths, oversized eyes, costumes, comic gestures, and mascot poses.
- Budget characters deliberately: normally zero to two prominent figures in a full diagram. Parallel roles may use small consistent portrait marks when comparison requires them.
- Keep any character visually secondary to the system, evidence, decision, or business outcome being explained.
- Reject a candidate that feels like a children’s book, comic strip, game, or mascot campaign when shown without its text.

Once an actor identity is established within a diagram, reuse it everywhere that actor or platform reappears. This lets the reader identify ownership before reading the technical label.

### Cross-asset visual canon

When several diagrams belong to the same product, program, platform, or story:

- Treat recurring actors, platforms, storage, packets, interfaces, and other reusable artifacts as a shared visual system, not as new illustrations in every image.
- Load the approved prior asset or actor reference before generating the next diagram.
- Preserve the same base silhouette, proportions, face language, line weight, mechanical design, brand mark placement, and semantic color ownership across every asset.
- Apply role differences only as an additive layer: expression, posture, label, task artifact, or one restrained accessory. Never redesign the underlying actor because its job changed.
- All Agent Studio agents use one canonical Agent Studio agent design. Greetings Agent, Orchestrator, Skeptic, Referee, and Advocate are roles performed by that same visual family.
- Every depicted Agent Studio agent must carry the exact official Algolia symbol in the same approved location and scale family. Composite the repository-owned logo deterministically; never rely on the image model to draw it.
- Record reusable actor and artifact specifications in the companion Markdown contract so future diagrams can reproduce them.
- Reject a new asset if a recurring actor or artifact would not be recognized as the same one when the diagrams are viewed side by side.

### Progressive state and shared storage

When a shared store accumulates data across multiple stages:

- Do not draw the completed store inside the first stage; that falsely implies all records exist from the beginning.
- Show the store as a shared rail, shelf, or working-memory area spanning the stages.
- Color each record or folder using the stage that creates or owns it.
- Show the creation order explicitly: observed journey first, decision state later, conversation state after engagement, and handoff state only after the visitor responds.
- Distinguish data that actively drives the experience from operational, reserved, or currently unused metadata.

### Platform ownership marks

When platform ownership helps explain the system:

- Place a small brand mark directly beside each component owned by that platform.
- Do not place the mark beside generic JavaScript, browser APIs, neutral transport, or third-party components.
- Keep the main brand mark separate from component ownership marks: the main mark identifies the artifact; the small marks identify responsibility inside the flow.
- Verify every ownership mark against the implementation before generation.
- Official logos are immutable assets, not illustration prompts. Use the supplied or repository-owned logo file itself for every official brand mark. Never ask the image model to redraw, approximate, stylize, or infer a logo. If the surrounding diagram is generated, leave a clean placement area and composite the exact asset afterward.

### Baseline and revision discipline

When the user approves a diagram as canonical:

- Preserve the full-resolution image under a stable, descriptive filename.
- Record exact labels, stage order, semantic colors, actor types, ownership, inputs, outputs, dimensions, checksum, and publication locations in a companion Markdown file.
- Generate future variants from a copy. Never overwrite the approved baseline during experimentation.
- Treat a change to any fact, connector, actor, ownership mark, or emphasis cue as a semantic change requiring explicit review, even when the request sounds purely visual.
- Proofread the generated image at original resolution. Misspellings, changed numbers, substituted brand assets, and omitted connectors block canonical promotion.

## Step 3: Write the image prompt

Produce a detailed, specific image-generation prompt (150–300 words) following the style guide and the structure from the chosen format's reference file.

The prompt must:
- Open with the format type and title
- Declare the white background and hand-drawn sketch aesthetic
- Describe each element (layers/nodes/steps/spokes/cells/branches) specifically, including color, label, icon, and any caption
- State the semantic meaning of every color and require the same color wherever that group reappears
- For dual-audience explainers, specify the business heading first and the technical subheading second in every major stage
- Close with the mood/tone line: "sketch aesthetic: slightly imperfect lines, hand-lettered labels, educational whiteboard style. Natural watercolor tonal transitions and subtle grounding shadows only; no glossy digital gradients, hard drop shadows, or corporate polish."

If the user asks for options, variations, or multiple images, create two distinct prompt variants for each topic before generating images:
- **Variant A**: clearer, simpler, more instructional
- **Variant B**: more memorable, more metaphorical, or more visually interesting

If the user does not ask for variants, produce one prompt by default to avoid unnecessary image cost.

For executive hand-drawn prompts, explicitly include: “editorial strategy-sketch register; sparse, restrained figures; functional ink icons; no mascot styling, comic expressions, toy-like robots, or children’s-book illustration.”

## Output Format

Always output:

### Format Chosen
One line stating which format was selected and why (e.g., "Flowchart — because this topic involves decision branching based on conditions").

### Topic Breakdown
A short bulleted list of the elements and their components (for the user to verify before they use the prompt).

### Image Prompt
The full image generation prompt, formatted as a single block of plain text ready to copy-paste into an image generator (Midjourney, DALL-E, Stable Diffusion, Gemini) or hand to a human illustrator.

### Variant Prompt B (only if requested)
When the user asks for options, provide a second prompt with a clearly different layout, metaphor, or emphasis.

### Excalidraw Notes (optional)
If the user mentions Excalidraw specifically, add a brief note after the prompt explaining how to recreate it: use the hand-drawn stroke style, rounded corners, and the hex colors from the Palette Reference below.

## Step 4: Generate the image when requested

After producing the Image Prompt above, generate the image when the user asks for an actual image, not only a prompt.

Preferred paths:

- If the host environment provides a native image-generation tool, use that tool with the Image Prompt.
- Otherwise, run this skill's bundled script, passing the full Image Prompt as the first argument:

```bash
python /path/to/sketch-explainer/scripts/generate_image.py "<image prompt>"
```

The script saves the image to `sketch_explainer_output/sketch_<timestamp>.png` in the current working directory (creating the folder if needed). After running, tell the user where the image was saved.

**Requirements:**
- `GEMINI_API_KEY` environment variable must be set
- `google-genai` Python package must be installed (`pip install google-genai`)

Do not store API keys inside the skill folder. If the script fails due to a missing API key or package, show the error and display the Image Prompt so the user can still use it manually.

---

## Palette Reference

Use the Judge Explainer watercolor family as the default shared base. These are pale wash colors, not solid fills:

- Orange: `#F7E2C2` wash with restrained `#E5A45B` edge pigment.
- Blue: `#DCE6F2` wash with restrained `#7EA6D6` edge pigment.
- Green: `#E1E9D8` wash with restrained `#92AF7F` edge pigment.
- Yellow: `#F8E9B8` wash with restrained `#D8B85C` edge pigment.
- Purple: `#E8E1F0` wash with restrained `#A894C9` edge pigment.

Keep the paper visible through every wash. Never make a diagram feel more premium by darkening or saturating these colors. Premium means luminous paper, controlled pigment, semantic consistency, and quiet contrast.

For topics with fewer elements than colors, pick the most fitting subset. Do not force all five. When two approved diagrams belong to one story, reuse the same semantic family mapping so they look like one system.

---

## References

- `references/format-selection.md` — decision guide for picking the right format
- `references/style-guide.md` — durable visual taste, image-skill boundaries, and prompt-quality rules
- `references/executive-hand-drawn.md` — professional middle ground between sterile architecture and cartoon illustration
- `references/layered-stack.md` — horizontal bands, abstraction layers
- `references/flowchart.md` — decision diamonds, branching arrows
- `references/linear-steps.md` — numbered sequential steps
- `references/wheel.md` — central hub with radiating spokes
- `references/grid.md` — card grids and 2×2 quadrants
- `references/concept-map.md` — organic branching mind map
