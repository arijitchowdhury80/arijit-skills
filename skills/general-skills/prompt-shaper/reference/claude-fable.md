# Target: Claude Fable 5.1 (and Fable 5 / Mythos)

Source: "Prompting Claude Fable 5.1" and "Prompting Claude Fable 5", platform.claude.com, read 2026-10-12. Model id `claude-fable-5-1`. T4 in the routing table: only when explicitly chosen.

## What's different about this executor

- Thinking always on, adaptive only. No `budget_tokens`. Effort default `high`; `medium` roughly matches Fable 5 at lower cost; `low` is often competitive with Opus and Sonnet on cost per task.
- One brief sentence steers a whole behavior class. Enumerated cases and prescriptive step plans degrade output. Skills written for older models are usually too prescriptive.
- Fights overshoot, not laziness: surveys options it won't pursue, over-plans, fixes nearby code, commits extra tests. Quality modifiers ("go beyond the basics") make this worse.
- Writes fewer user-facing updates during long tool chains. Ask for them if a human is watching.
- Prose can run dense. "Please remove all mannered prose" works.
- Formats less than older models. Remove anti-markdown blocks; they suppress structure the content needs.
- At `low` effort, answers from memory instead of searching. Say that recognizing a name is not knowing its current state.
- May rewrite whole files for small edits. One line fixes it.
- Early stopping is rare but real: ends a turn on "Next, I'll..." or asks permission for work already requested.

## Shaping rules

1. **Brevity.** One clear sentence per behavior you want. Delete anything that enumerates cases the sentence already covers.
2. **No quality modifiers.** Instead: "When you have enough information to act, act. Do not re-derive facts already established. Give a recommendation, not an exhaustive survey."
3. **No reasoning echo.** See general.md lint rule 1. Hard constraint on this model.
4. **Scope the deliverable.** "The user's request sets the scope and the scope is the deliverable: don't narrow, widen or swap it." Add: "If you find a pre-existing bug or unrelated improvement, report it as a follow-up, don't fix it."
5. **Autonomy clause when unattended.** "You are operating autonomously. The user is not watching and cannot answer mid-task. For reversible actions that follow from the request, proceed. Stop only for destructive actions or genuine scope changes. Before ending your turn, check your last paragraph: if it is a plan, a question or a promise, do that work now." The first sentence carries most of the effect.
6. **Assessment vs fix.** "When the user is describing a problem or thinking out loud, the deliverable is your assessment. Don't apply a fix until asked."
7. **Grounded progress claims.** "Before reporting progress, audit each claim against a tool result from this session. Report only work you can point to evidence for; say what is not yet verified."
8. **Subagents: use them, keep working.** "Delegate independent subtasks to subagents and keep working while they run." Fresh-context verifier subagents beat self-critique.
9. **Progress text if a human watches.** "Say in a line what you're about to do, give brief updates while you work, and close with a recap that stands on its own."
10. **Targeted edits.** "When it will not affect the result, surgically edit a file rather than rewrite it."
11. **Long deliverables at xhigh/max.** Recommend `high` instead. If xhigh/max is required, add the "everything in one reply counts toward one limit, don't draft the deliverable twice" note from the docs.

## Effort recommendation wording

"Start at `high` (default). Step down to `medium` or `low` if evals hold; step up to `xhigh` only for a measured gain."
