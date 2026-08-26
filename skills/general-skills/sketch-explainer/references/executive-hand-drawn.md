# Executive Hand-Drawn Explainer

Use this reference for leadership, team, governance, product strategy, operating-model, and architecture explainers. The goal is a professional middle ground between a sterile technical diagram and a cartoon illustration.

## Visual Thesis

The artifact should feel like an excellent strategist or architect explained the system by hand in a field notebook, then a careful editorial designer refined the composition without removing the human quality.

The hand-drawn quality comes from:

- slightly imperfect charcoal or ink lines;
- disciplined handwritten headings and short annotations;
- functional objects drawn from observation;
- pale watercolor washes that group meaning;
- visible paper texture and generous negative space.

It does **not** come from mascot characters, comic expressions, toy-like robots, speech-bubble clutter, or exaggerated poses.

## Information Before Illustration

Lock a content contract before choosing icons or characters. Preserve exact:

- title and subtitle;
- stage names and order;
- inputs, actions, outputs, and connectors;
- business and technical labels;
- actor types and ownership;
- semantic color mapping;
- primary, optional, active, and inactive emphasis.

Illustration may clarify this contract. It may not rewrite it.

## Preferred Visual Vocabulary

Use, in order of preference:

1. **Functional objects:** folder, rulebook, checklist, packet, browser window, evidence sheet, storage drawer, dial, timeline, or conversation panel.
2. **Abstract role marks:** small bust, profile silhouette, badge, headset, role card, or hand interacting with an object.
3. **Restrained characters:** only when a person or agent taking action is essential to understanding the flow.

Icons should use charcoal linework with one semantic-color accent. They should look hand-inked, not like clip art, emoji, stickers, or polished 3D assets.

## Character Restraint

- Normally use zero to two prominent figures across the whole diagram.
- Use small, repeated portrait marks for parallel roles instead of multiple large bodies.
- Keep proportions natural and editorial, not chibi, toy-like, or mascot-like.
- Convey role through brows, a simple mouth line, posture, label, and working artifact.
- Avoid oversized heads or eyes, theatrical gestures, costumes, zigzag mouths, and decorative personality details.
- Robots are optional notation for AI ownership, not the default depiction of every agent.
- When several AI agents appear, keep one consistent mechanical design and vary the task artifact or role label.

## Shared Actor Canon Across Assets

For a family of diagrams, define one reusable actor specification before generation:

- base silhouette and proportions;
- head and faceplate construction;
- default expression language;
- line weight and watercolor treatment;
- official brand-mark source, position, and relative scale;
- allowed role-specific expressions, postures, labels, and artifacts.

Reuse that specification in every artifact. “Different role” means the same actor working differently, not a newly invented character. Keep the chassis and ownership mark fixed; vary only the role layer.

When an approved prior diagram exists, include it as a visual reference. A text description alone is not enough to preserve character identity reliably across image-generation runs.

## Composition

- Begin with a literal title and one-line subtitle.
- Use a concise lifecycle rail when sequence matters.
- Use a 2x2 or 2x3 stage matrix for dense systems.
- Let functional objects anchor each stage; do not make character scenes the anchor.
- Keep at least one clear band of negative space between major groups.
- Use short labels in the image and move nuance into a companion document when necessary.

## Color And Material

- Use luminous cold-pressed paper, never flat gray.
- Use pale watercolor washes with restrained edge pigment.
- Color encodes stage or ownership; it does not decorate every object.
- Keep connectors and text in charcoal.
- Premium means quiet contrast, precise spacing, and controlled pigment, not darker fills, glossy gradients, shadows, or gold decoration.

## Brand And Ownership

- Composite official logos from exact source assets after generation.
- Never ask the image model to draw, reconstruct, stylize, or approximate a logo.
- Use one quiet artifact-level brand mark and only the necessary small ownership marks beside branded components.
- Do not add a white tile, badge, or background behind a transparent logo unless the approved brand treatment requires it.

## Revision Discipline

Image models are unreliable at narrow edits. A request to change one face, logo, or color can alter layout, text, and facts elsewhere. Therefore:

1. Preserve the approved baseline before every revision.
2. State the exact edit and the invariants that must not change.
3. Prefer deterministic compositing for logos and small overlays.
4. Compare the full image at original resolution, not only the edited region.
5. Reject variants with changed wording, alignment, ownership, stage order, numbers, or connectors.

## Visual Object Accountability

Every object must carry one named concept in the content contract. During review, point to each
folder, book, packet, checklist, character, badge, and connector and state what it represents.
If an object repeats an existing metaphor, has no distinct owner, or cannot be explained in one
sentence, remove it. A prior-generation leftover is a semantic defect, not harmless decoration.

Review both the isolated edited crop and the complete diagram. A locally improved object does not
pass if it creates a duplicate metaphor, crowds another stage, or breaks the visual family.

## Acceptance Test

Reject the image if any answer is “yes”:

- Would an executive describe it as cartoonish, cute, or mascot-heavy?
- Do characters attract more attention than the concept or system?
- Does it resemble a children’s book, comic, game, or AI marketing poster?
- Did decorative illustration reduce the space available for explanation?
- Did a visual-only change alter any fact, label, connector, or emphasis?
- Is any official logo synthesized or visually modified?
- Would a recurring actor or artifact look unrelated when this image is placed beside the rest of its approved family?
- Is there any unexplained, redundant, or orphaned visual object?

Accept when the image feels human and memorable, while still credible in an executive briefing or technical review.
