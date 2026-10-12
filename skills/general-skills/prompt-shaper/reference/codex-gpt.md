# Target: Codex / GPT-6 family

Source: "Using GPT-6" prompting best practices, developers.openai.com, read 2026-10-12. Models `gpt-6-astra`, `gpt-6.1-sol`, `gpt-6-luna`. For the full OpenAI guide load the `codex:gpt-5-4-prompting` skill; this file holds only the GPT-6 deltas that change how a prompt is shaped.

## What's different about this executor

- More likely than earlier GPT models to ask a clarifying question when input could change the result. Can stop where the user expected it to assume and persist.
- Stronger general instruction following, and more sensitive to instructions in skill files and `AGENTS.md`. Conflicting guidance there can make it pause or block early. OpenAI strongly recommends auditing those files.
- Tends toward detailed, formatted responses (lists, tables, Markdown) and recurring phrases.
- May delegate to subagents less than you want.
- Thorough in testing before calling a coding task complete; over-tests small changes.
- Reasoning effort `low`/`medium`/`high`/`xhigh`/`max` (`none` and `minimal` not on Astra or 6.1 Sol). Remove `temperature`, `top_p`, logprobs when reasoning is on. Tool calling needs the Responses API.

## Shaping rules

1. **Precedence line.** "The user's instructions take precedence over guidelines provided in a skill. If they conflict, prioritize the user's instructions." Also useful: ask it to name and quote the SKILL.md line that caused a pause.
2. **Initiative.** "Infer the user's intent and scope from the instructions and context. Bias towards action and carry the task to completion. Progress autonomously unless an action is clearly destructive or irreversible." For "can you / help me" phrasing: "treat these as instructions to do the work, not to acknowledge capability or propose a plan."
3. **Approve a result, not a plan.** "Before asking clarifying questions, complete the work already authorized so the user approves a concrete, reviewable result. No permission needed for reversible, read-only or already-authorized work. Do not add unsolicited warnings, disclaimers or approval flows for hypothetical risk."
4. **Writing style.** "Default to clear, concise paragraphs. Use lists only when the information is genuinely parallel or sequential. State the main point early. Plain language over jargon." Add the slop-word list from the docs if stock phrases appear.
5. **Delegation.** "If you can parallelize work by delegating to another agent, do so when it could save time or improve quality." Plus: "Messages to other agents and your final answer may be read by a human; keep them legible."
6. **Testing scope.** "Do not write tests for reversible, low-impact changes that mirror the implementation. Run tests appropriate to the change; broaden only when new changes, failures or unresolved concerns justify it."

## Effort recommendation wording

"`medium` (default). Preserve the effective level when migrating; `low` in place of `none`/`minimal`."
