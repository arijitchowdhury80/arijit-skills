# Prompting Reference: Classic Best Practices vs Claude Fable 5

> Source material for a future prompt-generation skill. Compiled 2026-07-03 from three official docs pages:
> 1. https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices (all current models)
> 2. https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-4-8 (Opus 4.8 specifics — the baseline Fable 5 is compared against)
> 3. https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5 (Fable 5 / Mythos 5 specifics)

---

# PART 1 — CLASSIC / GENERAL BEST PRACTICES (apply to ALL current models, including Fable 5)

## 1A. Core prompt construction

### 1. Be clear and direct
- Claude = brilliant new employee with no context on your norms. Precision in = quality out.
- **Golden rule:** show the prompt to a colleague with minimal context; if they'd be confused, Claude will be.
- Be specific about output format and constraints.
- Numbered lists / bullets when step order or completeness matters.
- Quality modifiers push effort. Example: instead of "Create an analytics dashboard" →
  > "Create an analytics dashboard. Include as many relevant features and interactions as possible. Go beyond the basics to create a fully-featured implementation."
- ⚠️ Fable 5 caveat: quality modifiers now risk OVERSHOOT (see Part 3, row 2).

### 2. Add context / motivation
- Explain WHY a behavior matters; model generalizes from the explanation.
- Example: "NEVER use ellipses" → "Your response will be read aloud by a text-to-speech engine, so never use ellipses since the engine will not know how to pronounce them."

### 3. Use examples (few-shot / multishot)
- 3–5 examples, best-in-class steering for format/tone/structure.
- Make them: **relevant** (mirror real use case), **diverse** (cover edge cases, avoid unintended patterns), **structured** (wrap in `<example>` / `<examples>` tags).
- Can ask Claude to critique or extend your example set.

### 4. Structure prompts with XML tags
- Separate instructions / context / input / examples with dedicated tags.
- Consistent, descriptive tag names; nest for hierarchy (`<documents>` → `<document index="n">`).

### 5. Give Claude a role (system prompt)
- Even one sentence focuses behavior and tone: "You are a helpful coding assistant specializing in Python."

### 6. Long-context prompting (20k+ token inputs)
- **Longform data at TOP, query/instructions at BOTTOM** — up to 30% response-quality improvement on multi-doc tasks.
- Wrap each doc in `<document>` with `<source>` + `<document_content>` metadata subtags.
- **Ground in quotes:** ask Claude to first extract relevant quotes into `<quotes>` tags, then answer based on them.

### 7. Model self-knowledge
- If app needs correct self-identification or model strings, state them in the system prompt:
  > "The assistant is Claude, created by Anthropic. The current model is Claude Opus 4.8."
  > "When an LLM is needed, default to Claude Opus 4.8 unless the user requests otherwise. The exact model string is claude-opus-4-8."

## 1B. Output and formatting control

### 8. Tell Claude what TO do, not what NOT to do
- "Do not use markdown" → "Your response should be composed of smoothly flowing prose paragraphs."

### 9. XML format indicators
- "Write the prose sections of your response in `<smoothly_flowing_prose_paragraphs>` tags."

### 10. Match prompt style to desired output style
- Markdown-heavy prompt → markdown-heavy output. Strip markdown from prompt to reduce it in output.

### 11. Detailed formatting prompt for markdown control (canonical snippet)
```
<avoid_excessive_markdown_and_bullet_points>
When writing reports, documents, technical explanations, analyses, or any long-form
content, write in clear, flowing prose using complete paragraphs and sentences. Use
standard paragraph breaks for organization and reserve markdown primarily for `inline
code`, code blocks, and simple headings (## and ###). Avoid using **bold** and *italics*.

DO NOT use ordered lists (1. ...) or unordered lists (*) unless: a) you're presenting
truly discrete items where a list format is the best option, or b) the user explicitly
requests a list or ranking

Instead of listing items with bullets or numbers, incorporate them naturally into
sentences. This guidance applies especially to technical writing. Using prose instead of
excessive formatting will improve user satisfaction. NEVER output a series of overly
short bullet points.

Your goal is readable, flowing text that guides the reader naturally through ideas
rather than fragmenting information into isolated points.
</avoid_excessive_markdown_and_bullet_points>
```

### 12. LaTeX off-switch
```
Format your response in plain text only. Do not use LaTeX, MathJax, or any markup
notation such as \( \), $, or \frac{}{}. Write all math expressions using standard text
characters (e.g., "/" for division, "*" for multiplication, and "^" for exponents).
```

### 13. Communication style baseline (latest models)
- More direct/grounded, more conversational, less verbose; may skip post-tool-call summaries.
- To restore visibility: "After completing a task that involves tool use, provide a quick summary of the work you've done."

### 14. Prefilled responses — DEAD on Claude ≥4.6 and Fable/Mythos
- Prefill on last assistant turn returns 400 error. Migrations:
  - Format control → **Structured Outputs** feature, or direct schema instruction + retries; classification → tool with enum field.
  - Preamble elimination → "Respond directly without preamble. Do not start with phrases like 'Here is...'"
  - Continuation → move into user message: "Your previous response was interrupted and ended with `[previous_response]`. Continue from where you left off."
  - Context hydration → inject reminders into user turns, hydrate via tools, or during compaction.

## 1C. Thinking and reasoning

### 15. Adaptive thinking (current standard)
- Opus 4.6–4.8 / Sonnet 4.6: `thinking: {type: "adaptive"}`, model decides when/how much to think. Thinking OFF when parameter omitted.
- **Fable 5 / Mythos 5: thinking ALWAYS ON, adaptive is the only mode.** `budget_tokens` returns 400 error on Opus 4.7+ and Fable.
- Depth controlled by `effort` parameter + query complexity.
- Adaptive thinking outperforms extended thinking in internal evals.
- Steer trigger frequency: "Extended thinking adds latency and should only be used when it will meaningfully improve answer quality — typically for problems that require multi-step reasoning. When in doubt, respond directly."

### 16. Reasoning guidance principles
- **Prefer general instructions over prescriptive steps** ("think thoroughly" beats a hand-written step plan).
- Multishot examples with `<thinking>` tags inside examples teach the reasoning pattern.
- Manual chain-of-thought with `<thinking>`/`<answer>` tags as fallback when thinking is off. ⚠️ **DANGEROUS ON FABLE 5** — see Part 3, row 5.
- Self-check: "Before you finish, verify your answer against [test criteria]."
- Anti-rumination: "Choose an approach and commit to it. Avoid revisiting decisions unless you encounter new information that directly contradicts your reasoning."
- Opus 4.5 quirk: sensitive to the word "think" when thinking disabled — use "consider," "evaluate," "reason through."

## 1D. Tool use and agentic systems

### 17. Explicit action language
- "Can you suggest some changes?" → model only suggests. "Change this function to improve its performance." → model acts.
- Proactive toggle:
```
<default_to_action>
By default, implement changes rather than only suggesting them. If the user's intent is
unclear, infer the most useful likely action and proceed, using tools to discover any
missing details instead of guessing.
</default_to_action>
```
- Conservative toggle:
```
<do_not_act_before_instructions>
Do not jump into implementation or change files unless clearly instructed to make
changes. When the user's intent is ambiguous, default to providing information, doing
research, and providing recommendations rather than taking action.
</do_not_act_before_instructions>
```
- Dial back aggressive triggers on newer models: "CRITICAL: You MUST use this tool when..." → "Use this tool when..."

### 18. Parallel tool calls (canonical snippet)
```
<use_parallel_tool_calls>
If you intend to call multiple tools and there are no dependencies between the tool
calls, make all of the independent tool calls in parallel... [full snippet in docs]
Never use placeholders or guess missing parameters in tool calls.
</use_parallel_tool_calls>
```
- Reduce: "Execute operations sequentially with brief pauses between each step to ensure stability."

### 19. Long-horizon state management
- First context window sets up framework (tests, setup scripts); later windows iterate on todo list.
- Structured state in JSON (`tests.json`); freeform progress notes (`progress.txt`); git as state log/checkpoints.
- "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality."
- Quality-of-life scripts (`init.sh`) to avoid repeated setup.
- Fresh window often beats compaction — models discover state from filesystem. Be prescriptive on restart: "Review progress.txt, tests.json, and the git logs."
- Context-awareness reassurance (Sonnet-class models that see token budget):
```
Your context window will be automatically compacted as it approaches its limit... do not
stop tasks early due to token budget concerns... Never artificially stop any task early
regardless of the context remaining.
```
- Encourage full use of window: "It's encouraged to spend your entire output context working on the task — just make sure you don't run out of context with significant uncommitted work."

### 20. Balancing autonomy and safety (canonical snippet)
```
Consider the reversibility and potential impact of your actions... for actions that
are hard to reverse, affect shared systems, or could be destructive, ask the user before
proceeding.

Examples: deleting files or branches, dropping database tables, rm -rf, git push
--force, git reset --hard, pushing code, commenting on PRs/issues, sending messages,
modifying shared infrastructure.

When encountering obstacles, do not use destructive actions as a shortcut (e.g. don't
bypass safety checks with --no-verify or discard unfamiliar files).
```

### 21. Research prompting
- Define success criteria; ask for multi-source verification.
- Structured approach: "develop several competing hypotheses. Track your confidence levels in your progress notes... Update a hypothesis tree or research notes file."

### 22. Subagent orchestration (pre-Fable stance)
- Models orchestrate natively; define subagent tools well; let it delegate.
- Opus 4.6: OVERUSES subagents → restrain: "Use subagents when tasks can run in parallel, require isolated context, or involve independent workstreams... For simple tasks... work directly rather than delegating."
- Opus 4.8: spawns FEWER by default → prompt to spawn: "Spawn multiple subagents in the same turn when fanning out across items or reading multiple files."

### 23. Prompt chaining
- Mostly internalized by adaptive thinking + subagents. Still useful for inspectable pipelines.
- Canonical pattern: draft → review against criteria → refine (separate API calls).

### 24. Anti-overengineering (canonical snippet)
```
Avoid over-engineering. Only make changes that are directly requested or clearly
necessary...
- Scope: Don't add features, refactor code, or make "improvements" beyond what was asked.
- Documentation: Don't add docstrings/comments/type annotations to code you didn't change.
- Defensive coding: Don't add error handling/fallbacks/validation for scenarios that
  can't happen. Trust internal code. Only validate at system boundaries.
- Abstractions: Don't create helpers for one-time operations. Don't design for
  hypothetical future requirements.
```

### 25. Anti-test-gaming (canonical snippet)
```
Please write a high-quality, general-purpose solution using the standard tools
available. Do not create helper scripts or workarounds... Implement a solution that
works correctly for all valid inputs, not just the test cases... Tests are there to
verify correctness, not to define the solution... If the task is unreasonable or
infeasible, or if any of the tests are incorrect, please inform me rather than working
around them.
```

### 26. Anti-hallucination (canonical snippet)
```
<investigate_before_answering>
Never speculate about code you have not opened. If the user references a specific file,
you MUST read the file before answering... Never make any claims about code before
investigating unless you are certain of the correct answer.
</investigate_before_answering>
```

### 27. Temp file hygiene
- "If you create any temporary new files, scripts, or helper files for iteration, clean up these files by removing them at the end of the task."

### 28. Vision
- Crop tool / zoom skill gives consistent uplift on image tasks (cookbook available).
- Break videos into frames.

### 29. Frontend aesthetics (canonical `<frontend_aesthetics>` snippet)
- Avoid "AI slop": generic fonts (Inter/Roboto/Arial), purple-gradient-on-white, predictable layouts.
- Typography / color+theme / motion / backgrounds guidance. Full snippet in docs + frontend-design skill.
- Opus 4.8 needs a much shorter version of this snippet.

---

# PART 2 — OPUS 4.8-ERA REFINEMENTS (the baseline Fable 5 diverges from)

1. **Verbosity calibrated to task complexity**, not fixed. Positive style examples beat negative instructions.
2. **Effort ladder:** `xhigh` best for coding/agentic; `max` can overthink; minimum `high` for intelligence-sensitive; `low`/`medium` scope strictly to what was asked (risk of under-thinking on complex work at low). Raise effort rather than prompting around shallow reasoning. Set 64k+ max output tokens at max/xhigh.
3. **Thinking OFF by default** — must set `thinking: {type: "adaptive"}`.
4. **Favors reasoning over tool calls** — raise effort or explicitly describe when/why to use tools.
5. **Native user-facing progress updates** — REMOVE forced interim-status scaffolding ("after every 3 tool calls, summarize").
6. **More literal instruction following** — doesn't silently generalize; state scope explicitly ("Apply this formatting to every section, not just the first").
7. **Direct, opinionated prose style** — re-evaluate voice prompts; add warmth explicitly if needed.
8. **Fewer subagents by default** — steer with explicit spawn guidance.
9. **Design house style:** cream/serif/terracotta default; generic negations just shift to another fixed palette. Fixes: (a) specify concrete alternative spec, (b) "propose 4 distinct visual directions, ask user to pick, then implement." Shorter frontend_aesthetics snippet suffices.
10. **Interactive vs autonomous:** more tokens in interactive multi-turn; front-load full task spec in first turn, add auto modes, reduce required human interactions.
11. **Code review harnesses:** better recall+precision, but follows "only report high-severity" literally → measured recall drops. Fix: separate finding (coverage) from filtering (verification stage): "Report every issue you find, including ones you are uncertain about... include confidence level and estimated severity so a downstream filter can rank them." Or define the bar concretely, not qualitatively.
12. **Computer use:** up to 2576px/3.75MP; 1080p sweet spot; 720p for cost-sensitive.

---

# PART 3 — FABLE 5: WHAT CHANGES, SIDE BY SIDE

Change types: **KEEP** (unchanged) · **AUGMENT** (same idea, stronger/extended) · **RECALIBRATE** (same lever, new settings) · **REVERSE** (opposite advice) · **NEW** (no prior equivalent) · **FORBIDDEN** (previously recommended, now harmful)

| # | Dimension | Classic / Opus 4.8 guidance | Fable 5 guidance | Δ |
|---|---|---|---|---|
| 1 | Instruction volume | Enumerate desired behaviors; add modifiers; aggressive triggers for undertriggering | One brief instruction steers whole behavior class. Old prescriptive prompts/skills DEGRADE output — audit and remove. "Skills developed for prior models are often too prescriptive." | **REVERSE** |
| 2 | Quality modifiers | "Go beyond the basics. Include as many features as possible." to fight laziness | Model overshoots instead: surveys options it won't pursue, over-plans, over-structures. Counter-prompt: "When you have enough information to act, act. Do not re-derive facts... give a recommendation, not an exhaustive survey." | **REVERSE** |
| 3 | Task selection | (not a prompting topic) | Start at the TOP of your difficulty range. Testing only on simpler workloads undersells capability. Have it scope, ask clarifying questions, execute. | **NEW** |
| 4 | Thinking config | Opus 4.8: off unless `adaptive` set; older: `budget_tokens` | Always on, adaptive-only. No budgets (400 error). Thinking output is summarized-only. | **RECALIBRATE** |
| 5 | Reasoning echo / manual CoT | "Use `<thinking>`/`<answer>` tags"; "show your reasoning" as fallback technique | **FORBIDDEN.** Echo/transcribe/explain-your-reasoning instructions trigger `reasoning_extraction` refusal → elevated fallbacks to Opus 4.8. Audit skills/system prompts for show-your-thinking language. Read structured `thinking` blocks from API instead. | **FORBIDDEN** |
| 6 | Effort calibration | Opus 4.8: xhigh for coding, min high for intelligence-sensitive | `high` is default for most tasks; `xhigh` only for most capability-sensitive; `low`/`medium` for routine — and low-effort Fable still often exceeds xhigh on prior models. Reduce effort if tasks complete but take too long. | **RECALIBRATE** |
| 7 | Turn length / harness timeouts | (not addressed) | Single requests run many minutes; autonomous runs extend hours. Adjust client timeouts, streaming, progress indicators BEFORE migrating. Check on runs asynchronously (scheduled jobs), don't block. | **NEW** (scaffolding) |
| 8 | Progress truthfulness | Opus 4.8 gives good updates natively | Ground claims: "Before reporting progress, audit each claim against a tool result from this session. Only report work you can point to evidence for; if something is not yet verified, say so explicitly." Nearly eliminated fabricated status reports in testing. | **NEW** |
| 9 | Unrequested actions | 4.6-era destructive-ops confirmation list | Broader boundary-setting: can draft emails nobody asked for, create defensive git-branch backups. "When the user is describing a problem... the deliverable is your assessment. Don't apply a fix until they ask. Before running a state-changing command, check the evidence actually supports that specific action." | **AUGMENT** |
| 10 | Early stopping | (not addressed) | Rare: deep in long session, ends turn with text-only intent ("I'll now run X") without the tool call, or asks permission when it has enough to proceed. Fix: autonomous-mode reminder — "Before ending your turn, check your last paragraph. If it is a plan, a question, or a promise about work you have not done, do that work now with tool calls." | **NEW** |
| 11 | Context-budget anxiety | Sonnet context-awareness reassurance prompt | Avoid surfacing remaining-token countdowns at all. If harness must show them: "You have ample context remaining. Do not stop, summarize, or suggest a new session on account of context limits." | **AUGMENT** |
| 12 | Subagents | 4.6: restrain overuse. 4.8: spawns few, prompt to spawn | Use subagents FREQUENTLY. Explicit delegation guidance + async communication (don't block on each return). Long-lived subagents keeping context across subtasks save cost via cache reads. "Delegate independent subtasks to subagents and keep working while they run." | **REVERSE** (vs 4.6) / **AUGMENT** (vs 4.8) |
| 13 | Memory | Memory tool + state files existed | First-class practice: markdown memory system, one lesson per file with one-line summary; record corrections AND confirmed approaches with why; no duplicates; delete wrong notes. Bootstrap: "Reflect on previous sessions... use subagents to identify core themes and lessons, store them in [X]." | **AUGMENT** |
| 14 | Verification | "Before you finish, verify your answer against [criteria]" (self-check) | Fresh-context VERIFIER SUBAGENTS outperform self-critique. "Establish a method for checking your own work at an interval of [X]... verifying your work with subagents against the specification." | **AUGMENT** |
| 15 | Mid-run communication | Remove forced interim summaries (4.8) | `send_to_user` client-side tool: delivers verbatim content mid-turn (deliverables, numbers, direct answers). Tool inputs never summarized. Must PAIR with elicitation prompt or model rarely calls it. Don't route narration through it. | **NEW** (scaffolding) |
| 16 | Context/motivation | "Add context to improve performance" | Same principle, higher payoff — template: "I'm working on [larger task] for [who]. They need [what output enables]. With that in mind: [request]." Especially for agents drawing on multiple workstreams. | **KEEP/AUGMENT** |
| 17 | Final-message readability | Verbosity/markdown control | Long agentic runs produce arrow-chain shorthand, invented labels, references to unseen thinking. Addendum: final summary is a RE-GROUNDING for a reader who saw none of the work — outcome first, complete sentences, drop working vocabulary, no arrow chains. | **AUGMENT** |
| 18 | Overengineering | Canonical snippet (Part 1 §24) | Same snippet, near-verbatim — now targeted at high-effort side effects (unrequested tidying/refactoring). | **KEEP** |
| 19 | Prefill | Dead ≥4.6 | Still dead. | **KEEP** |
| 20 | Safety / refusals | (not a prompting topic) | Safety classifiers: offensive cyber, bio/life-sciences, reasoning extraction. `stop_reason: "refusal"` + configure server/client-side fallback to Opus 4.8. Benign work in those domains may trigger too. | **NEW** |
| 21 | Checkpoint behavior | Enumerate pause cases | One instruction suffices: "Pause for the user only when the work genuinely requires them: a destructive or irreversible action, a real scope change, or input only they can provide. Ask and end the turn, rather than ending on a promise." | **REVERSE** (brevity replaces enumeration) |

## Unchanged classics (carry straight into any Fable 5 prompt-generation logic)
XML structure · few-shot examples · roles · long-doc-top/query-bottom layout · quote grounding · positive-instruction formatting · LaTeX switch · parallel-tool-call snippet · anti-hallucination snippet · anti-test-gaming snippet · state files + git + init.sh · autonomy/safety confirmation list · research hypothesis-tree prompting · temp-file cleanup · crop tool for vision · frontend aesthetics (short form).

## Fable 5 capability deltas that motivate the changes (vs Opus 4.8)
Long-horizon autonomy (multi-day runs) · first-shot correctness on complex well-specified problems · vision (dense screenshots; bash/crop tools for bad images) · enterprise workflows (finance/spreadsheets/slides) · code review + debugging recall · navigating ambiguity · delegation/parallel-subagent management. NOT intended for offensive cyber or bio work.

## Meta-observations for skill design
1. **Direction of correction flipped:** pre-Fable prompting fights UNDERSHOOT (laziness, undertriggering, shallow reasoning). Fable prompting fights OVERSHOOT (overplanning, scope creep, unrequested actions) and adds TRUST calibration (grounded claims, boundaries).
2. **Prompt generation for Fable is partly prompt DELETION** — a generator skill needs a prune/audit mode, not just compose mode.
3. **One-line steering:** each behavior class needs one clear sentence, not enumerated cases — snippet library becomes small and composable.
4. **Scaffolding is inseparable from prompting** on Fable: timeouts, async check-ins, send_to_user, memory files, verifier subagents. A prompt-generation skill that emits only prompt text is incomplete for Fable targets.
5. **Model-conditional output:** the same request should generate different prompts per target model (haiku/sonnet/opus/fable) — e.g. subagent guidance is opposite for Opus 4.6 vs Fable; thinking config differs; effort ladders differ; hard constraint (no reasoning echo) applies only to Fable/Mythos.
6. **Two structural conflicts to encode as lint rules:** (a) manual CoT / show-your-thinking → forbidden on Fable; (b) aggressive MUST-triggers → overtriggering on all 4.5+ models.
