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

The output should look like a **hand-painted watercolor explainer** — soft, luminous, and educational, as if a smart teacher painted it in a watercolor sketchbook. Hand-painted and hand-lettered, intentional but organic. Not a corporate slide. Not a flat marker diagram. Not a technical architecture doc. A beautiful painting you'd want to photograph and share.

**Core style rules (apply to all formats):**
- **Textured watercolor-paper background** — visible cold-press paper grain/tooth, warm off-white, faint deckle feel. Never flat pure white, never a screen-flat fill.
- **Everything is watercolor** — each shape is a soft, translucent watercolor **wash**, never a flat solid fill. Real watercolor behavior: a gentle gradient inside every wash (pigment pooling a touch deeper at the edges, lighter and paper-bright in the center), soft feathered edges, slight blooms and uneven pigment.
- **Keep washes LIGHT and airy** — pale, diluted tints (think 20–40% pigment, lots of water) with the paper glowing through. Never dull, heavy, or over-saturated.
- **Hand-lettered labels** — natural handwriting in dark charcoal/sepia ink, as if penned over the dry wash. Legible.
- **Loose hand-painted icons** with visible brush strokes: gear, arrow, magnifying glass, clock, stacked layers, checkmark, etc. One per element.
- Connectors/arrows: hand-inked, slightly wobbly.
- **Full composition inside the frame** — the entire diagram sits within the canvas with generous margins on all four sides. Nothing cropped, nothing running off the edge.
- No drop shadows, no vector flatness, no digital gloss. It must read as physical watercolor on paper.
- Overall feel: friendly, luminous, hand-made, educational.

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
- State the framing explicitly: "entire composition fits within the canvas with generous margins on all sides, nothing cropped or running off the edge."
- Close with the mood/tone line: "hand-painted watercolor on textured cold-press paper: light translucent washes with soft gradients and feathered edges, gentle blooms, hand-lettered ink labels, luminous and airy. No flat fills, no drop shadows, no digital gloss."

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

**Backends:** the script uses **OpenAI GPT Image** (`gpt-image-2`, falling back to `gpt-image-1`) as the primary generator, and **Google Gemini** ("Nano-banana") only as a fallback if OpenAI is unavailable or errors.

**Requirements:**
- `OPENAI_API_KEY` (primary). Optional `GEMINI_API_KEY` enables the fallback.
- No extra package for OpenAI — the script calls the REST API via `curl`.
- `google-genai` Python package (`pip install google-genai`) is needed only for the Gemini fallback.

**Secure key setup (key never lives in the skill folder, git, argv, or chat):**
The script reads keys from `~/.claude/skills/sketch-explainer/.config/.env.local` first, then the process environment. This `.config/` folder is gitignored so the key never gets committed. Create it once:
```bash
mkdir -p ~/.claude/skills/sketch-explainer/.config && chmod 700 ~/.claude/skills/sketch-explainer/.config
printf 'OPENAI_API_KEY=%s\n' "YOUR_KEY" > ~/.claude/skills/sketch-explainer/.config/.env.local
chmod 600 ~/.claude/skills/sketch-explainer/.config/.env.local
```
The key is passed to `curl` through a temporary chmod-600 config file, so it never appears in the process argument list.

**Optional overrides** (env or the `.env` file): `SKETCH_IMAGE_SIZE` (default `1536x1024`; W & H divisible by 16), `SKETCH_IMAGE_QUALITY` (default `high`; `low`|`medium`|`high`|`auto` — higher costs more).

Do not store API keys inside the skill folder. If the script fails due to a missing API key or package, show the error and display the Image Prompt so the user can still use it manually.

---

## Palette Reference

These are the base hues. **Always render them as light, translucent watercolor washes with a soft gradient — never as flat solid colors.** Dilute heavily (roughly 20–40% pigment, lots of water) so the paper glows through; each wash sits a touch deeper where the brush pooled and lighter/paper-bright toward the center.
- `#F4A896` — salmon/peach → paint as a **pale peach-coral wash** (warm, prominent: top layer / center / start nodes)
- `#F7E08A` — soft yellow → **pale butter-yellow wash**
- `#A8D5A2` — sage green → **pale mint-sage wash**
- `#A8C5DA` — slate blue → **pale sky-blue wash**
- `#C5B8E8` — lavender/purple → **pale lilac wash** (cool, receding: bottom layer / hidden / end nodes)

Treat these hex values as the *target tint*, not a fill color — the finished wash should read lighter than the hex chip. For topics with fewer elements than colors, pick the most fitting subset — don't force all five.

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
