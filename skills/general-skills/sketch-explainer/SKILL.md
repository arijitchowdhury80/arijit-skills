---
name: sketch-explainer
description: Generates sketch-style whiteboard explainer diagram prompts for any topic — technical or non-technical. Use this skill whenever the user asks to "explain X visually", "make a diagram of X", "sketch out how X works", "whiteboard X", "create an explainer for X", or mentions Excalidraw, sketch diagrams, or visual explainers. Also trigger when the user provides a topic and wants a prompt for an AI image generator in a hand-drawn or whiteboard style.
---

# Sketch Explainer

Your job is to take a topic and produce two things:
1. A **structured breakdown** of the topic into its key components
2. A **detailed image-generation prompt** describing a whiteboard-sketch explainer diagram in the exact style described below

This is an image explainer skill, not a technical architecture documentation skill. Use it for CEO-friendly explanation, learning, teaching, visual summaries, and conceptual diagrams. If the user asks for a technical architecture diagram from code, cloud services, repositories, deployment topology, or something they need to edit later, recommend an editable Mermaid/draw.io/diagrams.net output or a separate architecture-diagram skill instead of producing only a raster image prompt.

## The Target Visual Style

The output should look like a smart teacher drew it on a whiteboard — clean, informal, educational, and visually clear. Hand-drawn but intentional. Not a corporate slide. Not a technical architecture doc. A beautiful diagram you'd want to photograph and share.

**Core style rules (apply to all formats):**
- White background
- Hand-drawn / sketch aesthetic throughout — slightly imperfect lines, wobbly edges, hand-lettered labels
- Pastel color palette (see Palette Reference below) — these exact colors, always
- Title: large, slightly imperfect handwritten-style lettering at the top
- Minimal sketch icons inside elements: gear, arrow, magnifying glass, clock, microchip, dumbbell, waveform, stacked layers, checkmark, etc.
- No gradients, no drop shadows, no corporate polish
- Overall feel: friendly, approachable, educational

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

## Step 2: Decompose the topic

Break the topic into its meaningful parts using the structure appropriate to the chosen format:
- **Layered Stack**: 3–6 layers from visible to hidden
- **Flowchart**: nodes, decision points, and the paths between them
- **Linear Steps**: 3–8 ordered steps with clear names and what happens in each
- **Wheel**: the central concept + 4–8 surrounding components
- **Grid**: the items being compared and the attributes they share
- **Concept Map**: the central topic + 3–6 primary branches + sub-branches

Name each element clearly. For each element, identify a simple sketch-able icon.

## Step 3: Write the image prompt

Produce a detailed, specific image-generation prompt (150–300 words) following the style guide and the structure from the chosen format's reference file.

The prompt must:
- Open with the format type and title
- Declare the white background and hand-drawn sketch aesthetic
- Describe each element (layers/nodes/steps/spokes/cells/branches) specifically, including color, label, icon, and any caption
- Close with the mood/tone line: "sketch aesthetic: slightly imperfect lines, hand-lettered labels, educational whiteboard style. No gradients, no drop shadows, no corporate polish."

If the user asks for options, variations, or multiple images, create two distinct prompt variants for each topic before generating images:
- **Variant A**: clearer, simpler, more instructional
- **Variant B**: more memorable, more metaphorical, or more visually interesting

If the user does not ask for variants, produce one prompt by default to avoid unnecessary image cost.

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

These colors are fixed — always use these for the whiteboard aesthetic:
- `#F4A896` — salmon/peach (warm, prominent, use for top layer / center / start nodes)
- `#F7E08A` — soft yellow
- `#A8D5A2` — sage green
- `#A8C5DA` — slate blue
- `#C5B8E8` — lavender/purple (cool, receding, use for bottom layer / hidden / end nodes)

For topics with fewer elements than colors, pick the most fitting subset — don't force all five.

---

## References

- `references/format-selection.md` — decision guide for picking the right format
- `references/style-guide.md` — durable visual taste, image-skill boundaries, and prompt-quality rules
- `references/layered-stack.md` — horizontal bands, abstraction layers
- `references/flowchart.md` — decision diamonds, branching arrows
- `references/linear-steps.md` — numbered sequential steps
- `references/wheel.md` — central hub with radiating spokes
- `references/grid.md` — card grids and 2×2 quadrants
- `references/concept-map.md` — organic branching mind map
