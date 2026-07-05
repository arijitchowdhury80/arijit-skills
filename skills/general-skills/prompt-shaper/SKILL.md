---
name: prompt-shaper
description: Use when the user sends a large unstructured stream-of-consciousness message — multi-paragraph rambling, dictation-style text, mixed topics and asides in one blob — or when a hook flags LARGE UNSTRUCTURED INPUT, or when composing a prompt to dispatch to another Claude model or agent. Not for short direct requests, pasted code/logs, or the user's answers to clarifying questions already in flight.
---

# Prompt Shaper

Convert raw stream-of-consciousness into a verified, structured prompt before any work starts. The user speaks their mind in blobs; your job is to guarantee nothing is lost, gaps are surfaced, and the prompt matches Claude best practices for the model that will execute it.

**Contract: interview → shape → verify → save → execute. Never start the task before the user approves the shaped prompt.**

## Step 1 — Inventory the blob

List every distinct point: tasks, constraints, context facts, motivations, questions, opinions. Number them. Honor self-corrections ("no wait, X is the CTO" → X is the CTO; the earlier statement is dead). Treat "maybe there's a simpler way, you tell me" as a requirement to propose alternatives, not filler.

## Step 2 — Interview on gaps FIRST

Before showing any prompt, check the blob for missing critical info:

- Success criteria / definition of done
- Scope boundary (what's explicitly out)
- Priority order when multiple asks compete
- Execution target (this session, subagent, other model/agent?)
- Genuine ambiguities (two readings that lead to different work)

Ask ONLY questions whose answers change the prompt — batch them in one AskUserQuestion call (max 4). If nothing critical is missing, skip the interview; record assumptions in Step 4 instead. Never ask about things the blob, memory, or the repo already answer.

## Step 3 — Pick target model + apply its rules

Read [reference.md](reference.md) for model-conditional best practices. Determine who executes: this session's model, or a dispatched tier (haiku/sonnet/opus/fable per the user's routing table in CLAUDE.md). Apply that model's rules — effort recommendation, structure depth (haiku needs explicit steps; fable needs one-line steering and NO show-your-thinking language), subagent guidance direction, thinking config notes.

## Step 4 — Compose the shaped prompt

Canonical shape (omit empty sections; any large pasted documents go at the TOP above everything):

```
<context>Why this matters, who it's for, relevant system facts</context>
<task>The objective, one paragraph</task>
<requirements>Prioritized, numbered</requirements>
<constraints>Hard boundaries: cost, infra, secrets, style</constraints>
<deliverables>Including how completion will be verified</deliverables>
<out_of_scope>Explicit exclusions</out_of_scope>
<assumptions>Defaults chosen where the user didn't specify</assumptions>
<original_input>The user's blob, verbatim and complete</original_input>
```

`<original_input>` is mandatory — the executor reads both, so no nuance is ever silently lost.

## Step 5 — Show for verification

Present to the user, in order:

1. The shaped prompt (full text)
2. Coverage map: every inventory item from Step 1 → the section it landed in (or "dropped because…")
3. Recommended routing: model tier, effort, and skill (e.g. development-loop) with one-line reason

Then STOP and wait for approval. Corrections → edit and re-show only the diff.

## Step 6 — Save, then execute

On approval: save the shaped prompt to `~/.claude/prompt-library/YYYY-MM-DD-<slug>.md` (create dir if missing), then execute or dispatch per the approved routing.

## Common mistakes

| Mistake | Fix |
|---|---|
| Showing the prompt with "notes/open questions" attached instead of asking first | Gaps that change the work are Step 2 questions, not footnotes |
| Rewriting cleanly but dropping the original | `<original_input>` is a required section, always |
| Asking about priorities the blob already states | Interview only on genuine gaps |
| Starting work "since the prompt is obvious" | Verification stop is the point of the skill — always wait |
| Same prompt shape for every model | Step 3: haiku ≠ fable; check reference.md |
