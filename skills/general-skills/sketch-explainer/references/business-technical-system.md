# Business + Technical System Explainer

Use this reference for a system, operating model, AI workflow, or architecture that must be understandable to business and technical audiences at the same time.

For executive, leadership, or team-facing presentation, also apply `executive-hand-drawn.md`. It controls the illustration register and prevents a factual system diagram from drifting into mascot-heavy storytelling.

## 1. Lock The Meaning Before Styling

Create a content contract before generating the image. For every stage, record:

| Field | Purpose |
|---|---|
| Business heading | What the stage accomplishes for a person or the business |
| Technical subtitle | The code, service, agent, storage, or protocol that performs it |
| Inputs | What this stage receives and where it comes from |
| Action | What the stage actually does |
| Outputs | What it hands to the next stage |
| Actor type | Human, deterministic code, AI agent, storage, or transport |
| Ownership | Which platform or company owns the component |
| Emphasis | Primary, optional, inactive, supporting, or future |
| Semantic color | The color family assigned to this stage |

Do not generate until the content contract is fact-checked against the implementation or approved source. An image generator may improve composition; it may not rewrite the system.

## 2. Build A Guided Story, Not A Wall Chart

The reader should understand the whole story before reading implementation detail:

1. Title: literal subject of the diagram.
2. Subtitle: what the visitor or business experiences and what the system does underneath.
3. Lifecycle strip: one short verb per stage, in order.
4. Detailed stage panels: business heading first, technical subtitle second.
5. One concluding value statement only when it adds meaning.

For four stages, prefer a 2x2 matrix. For five or six dense sequential stages, prefer a 2x3 matrix or two horizontal rows with unambiguous numbered connectors. Avoid six narrow columns when they force tiny text or make the diagram read like documentation pasted onto a poster.

Keep the stage number, lifecycle-strip position, panel position, and connector order consistent. Never rely on proximity alone to communicate sequence.

## 3. Use A Semantic Visual Grammar

Color is a category system:

- Give each stage one restrained watercolor family.
- Repeat that color in the lifecycle strip, stage wash, stage-owned artifacts, and relevant callouts.
- Keep cross-stage arrows and neutral structure in charcoal.
- Preserve primary versus optional differences. Optional context must remain visibly subdued.
- Do not recolor adjacent objects merely for variety.
- When an approved companion diagram exists, treat its watercolor families as the visual source of truth. Transfer the family and pigment behavior, not merely a verbal color name.
- Premium does not mean darker. Preserve luminous paper, pale centers, restrained edge pigment, and quiet contrast.

Use cold-pressed watercolor paper, broad translucent washes, imperfect brush edges, charcoal linework, and generous white space. Natural pigment transitions within a single semantic color family are welcome; glossy digital gradients are not. Small functional objects may use restrained hand-painted grounding shadows for depth. Large stage areas should not become rigid dark-bordered cards. Small controls, packets, books, and diagrams may retain fine outlines for legibility.

## 4. Make Actor And Ownership Legible

The reader should recognize who or what acts before reading a label:

- Human figure: visitor, customer, operator, or employee.
- Small Agent Studio mark, headset badge, role icon, or restrained mechanical cue: an AI agent when embodiment is not the central story.
- Consistent robot: an AI agent only when the agent itself needs to be a visible character.
- Rulebook, checklist, traffic signal, or gear: deterministic code.
- Envelope or parcel: transport or handoff.
- Cylinder, drawer, or folder: storage.
- Screen or conversation panel: user-facing interface.

Keep AI visualization proportional to the story. Do not let robots dominate a diagram about governance, evidence, business value, or process. When robots are appropriate, use the same design for every AI agent and differentiate roles through surrounding artifacts and task labels, not different characters.

Across a multi-diagram story, the same platform actor must retain the same visual identity. Establish one canonical Agent Studio agent design and reuse it for every Agent Studio role; vary only expression, posture, label, and working artifact. Place the exact official platform mark consistently on every depicted agent.

When ownership matters, add a small brand mark immediately beside each owned component name. Do not place that mark beside neutral JavaScript, browser APIs, or third-party components. A main brand mark may appear once in a quiet corner; ownership marks answer a different question and may repeat.

Lock the requested brand treatment precisely: symbol-only, wordmark-only, or symbol plus wordmark are different assets. An image generator may not substitute one for another. Official logos must come from the supplied or repository-owned source asset and be composited exactly; never accept a synthesized, hand-drawn, or approximate logo as canonical.

## 5. Show Inputs And Continuity Explicitly

If multiple stages consume the same packet, context, or evidence set, label that input at every consuming stage. Do not expect the reader to infer that an arrow crossing the page means shared input.

For each transition, make the handoff concrete:

`input -> actor/action -> checked output -> next consumer`

Show progressive state where it is created. Do not draw the final, fully populated memory or packet in the first stage. Distinguish:

- what is known now;
- what is added later;
- what actively drives the current decision;
- what is optional, operational, reserved, or currently unused.

## 6. Control Detail Without Losing Truth

Use business language for visible headings and concise technical language for subtitles. Keep internal keys, version suffixes, hashes, schema versions, and low-level field names out of the main diagram unless they are essential to the explanation.

Examples illustrate behavior; they do not define architecture. A generic system diagram must not display one journey, customer, industry, or route in a way that implies the code is hard-coded to it. Put scenario-specific examples in a separate journey diagram.

Every statement must be either:

- verified implementation fact;
- explicitly labeled optional or future behavior; or
- a clearly identified example.

## 7. Generate And Revise Safely

Before each generation or edit, state the invariants that may not change: exact labels, stage order, actors, ownership, inputs, outputs, colors, and emphasis.

For an approved baseline:

1. Save the full-resolution image under a canonical filename.
2. Save a companion Markdown record containing its content contract, dimensions, checksum, publication locations, and approval status.
3. Create stylistic variants from a copy, never by overwriting the baseline.
4. Make narrow edits one semantic object at a time.
5. Compare the result against the content contract and approved image before promotion.

Run a final visual proofreading pass at original resolution. Check every heading, technical term, score label, ownership mark, arrow, and numerical example. Image-generation spelling errors, accidental wordmarks, missing connectors, and altered numbers are blocking defects, not cosmetic imperfections.

Reject a candidate if it improves aesthetics but changes a fact, removes a connector, equalizes optional and primary inputs, changes ownership, substitutes a human for an AI agent, or makes text unreadable at the intended presentation size.

## Acceptance Checklist

- Can a business reader explain the stages from headings alone?
- Can a technical reader identify the implementation mechanism under each heading?
- Is the full sequence understandable from the lifecycle strip?
- Are inputs, outputs, and shared context explicit?
- Are humans, AI agents, code, storage, transport, and interfaces visually distinct?
- Are branded components marked accurately and only where appropriate?
- Does each semantic color retain one meaning everywhere?
- Are optional and primary elements still visually distinct?
- Did any example accidentally look hard-coded?
- Does every label remain legible at presentation size?
- Are all words, numbers, brand marks, and technical terms exact at original resolution?
- Does the candidate preserve every fact and invariant from the approved baseline?
- Are characters sparse and secondary to the mechanism, evidence, or business outcome?
- Would this still look credible in an executive briefing without its surrounding explanation?
- Do recurring actors and artifacts match the approved visual canon across companion diagrams?
