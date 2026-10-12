# General rules for every shaped prompt

Source: Anthropic "Prompting best practices" (platform.claude.com, read 2026-10-12), OpenAI "Using GPT-6" (developers.openai.com, read 2026-10-12), Google "Prompt design strategies" (ai.google.dev, read 2026-10-12). All three vendors agree on everything in this file. Model-specific deltas live in the sibling files.

## Shape

- Say what the output must be, not how to think. Reasoning models calibrate their own depth. A hand-written step plan degrades current Claude and Gemini output.
- Give the reason behind each constraint. "Never use ellipses, the text is read aloud by TTS" beats "NEVER use ellipses". The model generalizes from the reason.
- Positive instructions. "Write in flowing paragraphs" beats "no markdown".
- One consistent delimiter style per prompt. XML tags for Claude. Gemini accepts XML or Markdown headings, pick one.
- Large pasted material goes above everything else. Instructions and the question go last, with a bridge like "Based on the material above".
- Examples: few, relevant, varied, identical in format, wrapped in `<example>` tags. Present each as problem, method, expected answer. No `<thinking>` tags inside examples.
- Say the scope out loud. Current models follow literally and don't silently generalize ("apply to every section, not just the first").
- Imperatives trigger action. "Can you suggest changes" gets suggestions. "Change this function" gets changes.

## Two lint rules that apply to every Claude 5-series target

1. **No reasoning echo.** Never ask the executor to write out, show, transcribe or explain its reasoning, and never put `<thinking>` tags in the prompt. On Fable 5.1, Fable 5, Opus 5.5, Opus 5 and Sonnet 5.5 this can return `stop_reason: "refusal"` with category `reasoning_extraction`. Ask for a short explanation of the result, or a summary of actions taken, instead.
2. **No MUST-shouting for tool or skill triggers.** "CRITICAL: You MUST use X when..." overtriggers on every 4.5+ model. Write "Use X when...".

## Effort

Effort is the main lever for depth, cost and latency on every current Claude model. Level names don't mean the same amount of thinking across models. The shaped prompt recommends "start at the model's default, then measure", not a fixed level, unless the user asked for a tier.

## Audit before you add

Prompts and skills written for older models often carry anti-laziness scaffolding: "if in doubt use the tool", "hold all findings for the end", "after every 3 tool calls summarize", "think step by step". On 5-series models these cause overtriggering, silence, or over-planning. When shaping a prompt that will run alongside an existing system prompt or skill, flag such lines for removal rather than adding counter-instructions.

## Non-Claude executors

- **Codex / GPT:** load the `codex:gpt-5-4-prompting` skill for the full guide. GPT-6 deltas that matter for shaping are in `codex-gpt.md`.
- **Gemini:** direct and concise, consistent structure, defaults for temperature, context first and question last. Not a dispatch target in this setup; no dedicated file.
