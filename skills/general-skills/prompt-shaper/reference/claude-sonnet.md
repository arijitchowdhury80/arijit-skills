# Target: Claude Sonnet 5.5

Source: "Prompting Claude Sonnet 5.5", platform.claude.com, read 2026-10-12. Model id `claude-sonnet-5-5`. T2 in the routing table: most coding, grounded synthesis, structured edits, bugfix with clear repro, tests, doc drafting.

## What's different about this executor

- Thinking on by default (adaptive). Lowest setting is `between_tools`, accepted at `high` or below. Effort default `high` on the API; for agentic coding start at `medium` for well-specified tasks.
- Effort levels recalibrated vs Sonnet 5; re-sweep rather than carry a setting over.
- At `low`/`medium` on long agentic tasks it checks in before finishing (confirms a plan, asks a question it could answer, stops after one part). At `low` it can skip verifying a change.
- At every effort level it adds tests, docs and small supporting files that fit the repo's conventions. More at higher effort.
- At `xhigh`/`max` it starts its own review rounds, sometimes with reviewer subagents, and makes related fixes it noticed. Run routine work at `high` or below.
- On open-ended requests ("show me what you can do") it starts building when you wanted ideas.
- On chat and knowledge work it sometimes answers from training when a search would catch changed details.
- Reasoning tasks with JSON output: at `low`/`medium` it often answers without thinking first.
- Occasionally calls a tool by the wrong letter case (`bash` for `Bash`). Harness concern, not prompt.
- Resists prompt injection; can misread harness text placed right after tool results as an injection.

## Shaping rules

1. **Effort: "default `high`; `medium` for well-specified agentic coding; measure".** Asking it to think less doesn't work; lower effort does.
2. **No reasoning echo.** See general.md lint rule 1. `reasoning_extraction` refusals apply here.
3. **Carry work through (low/medium agentic).** "Keep working until everything the user asked for is done, and only stop to ask when you can't go on without the user or before a risky step."
4. **Limit additions.** "When the work the user asked for is done and checked, stop and report. Don't add features, tests, files, docs or refactors that weren't asked for. If you think one would help, mention it at the end." Use only this paragraph if you welcome the carry-through but not the extras.
5. **Cap self-started review at xhigh/max.** "Don't start extra rounds of review or hardening on your own, and don't launch reviewer sub-agents unless the user asked for a review." Cut session cost by about a third in testing.
6. **Ideas vs build.** "When the user asks for ideas, options or a plan, give them that and stop. Don't start building until they say go."
7. **Verification at low effort.** "When you change code that can be run, built or type-checked, run a real check that exercises the change before reporting it done. A syntax-only check does not count. If no real check can run, say which one you did not run and why."
8. **Search for changed facts.** Remove "minimize tool calls" lines. Add: "Use the search tool to check specifics that may have changed since your training, such as what is allowed, required or charged, even when you feel confident."
9. **JSON + reasoning.** Prefer structured outputs. Add "Think the problem through before you answer." at the end of the system prompt, or use `xhigh`. Treat `stop_reason: "max_tokens"` as failed even if the JSON parses.
10. **Mark pasted third-party text** the same way as for Opus 5.5 (see claude-opus.md rule 8).

## Effort recommendation wording

"Start at `high` (default), or `medium` for well-specified agentic coding. Reserve `xhigh`/`max` for a measured gain; at those levels add the review cap."
