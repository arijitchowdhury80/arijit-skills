# Runtime Destination Rules

There is one knowledge-capture method. These notes only explain where each runtime should write.

## Codex

Use this skill when the user asks to record knowledge, update docs, save decisions, or make work reusable.

Default behavior:

- Inspect the current repo or workspace structure.
- Prefer existing `docs/`, `adr/`, `decisions/`, `wiki/`, `specs/`, or `notes/` folders.
- If the user has an Obsidian vault path in context, write durable knowledge there.
- Use targeted edits.
- Mention tests or verification only if relevant to the recorded work.

Avoid:

- Creating root-level `SESSION.md` unless the project already uses it.
- Treating Codex memory as the only durable store.
- Committing or pushing unless the user explicitly asks.

## Claude

Claude may use `.claude/state/` for short working state, but durable knowledge belongs in project docs or the vault.

Use:

- `.claude/state/STATUS.md` for current working memory.
- `.claude/state/TASK.md` for active task state.
- `docs/`, `docs/adr/`, `docs/specs/`, `docs/wiki/`, or vault notes for durable knowledge.

Avoid:

- Making `.claude/state/` the long-term source of truth.
- Letting checkpoint commands replace actual documentation.

## Hermes / MyOS

For Hermes and MyOS, use the same `/record` contract. Obsidian is the preferred destination.

Default local vault pattern:

```text
MyOS/Projects/{Workspace}/
MyOS/Knowledge/wiki/
MyOS/Standards/
MyOS/Architecture/
MyOS/Chowmes-Inbox/
```

Use `Chowmes-Inbox` as staging only when the correct destination is unclear or the note needs review.

For live Hermes, sync the local vault mirror to:

```text
/opt/data/knowledge/obsidian/MyOS
```

Avoid:

- Storing reusable organization knowledge only in role memory.
- Letting Telegram transcript history become canonical state.
- Running live runtime changes just to record knowledge.

## Hermes `/record`

Hermes should expose the universal methodology as a `/record` skill command.

V1 should:

- infer workspace
- write a log
- create decisions when real decisions exist
- update canonical notes/indexes
- return a compact receipt

Later versions can add entity linking, contradiction checks, role-memory proposals, and scheduled audits. Those are extensions to the shared method, not a separate MyOS flavor.
