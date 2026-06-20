---
name: agent-knowledge-capture
description: Capture important work from any coding-agent session into durable project or vault knowledge. Use when the user says record, persist, capture knowledge, update the vault/wiki/docs, save decisions, create a session log, distill a conversation, or build a reusable knowledge trail across Codex, Claude, Hermes, MyOS, or other agent workflows.
---

# Agent Knowledge Capture

Turn the current work into durable knowledge without dumping the whole chat.

## Core Rule

Preserve raw evidence when useful, but promote distilled knowledge into the places future agents will actually read.

## Workflow

1. Identify the target project or workspace.
2. Capture a concise raw/session log with evidence.
3. Extract durable items:
   - decisions
   - process changes
   - architecture or product facts
   - project state
   - reusable lessons
   - open questions
4. Route each item to the right layer.
5. Update indexes or backlinks when the destination has them.
6. Return a compact receipt listing created and updated files.

Ask at most one clarifying question when the destination is genuinely ambiguous or a wrong destination could cause damage.

## Knowledge Layers

- **Raw evidence**: session logs, transcript summaries, command evidence, source links, artifact paths.
- **Project knowledge**: project wiki, specs, ADRs/decisions, status files, handoff docs.
- **Shared knowledge**: standards, reusable methods, cross-project concepts, organization decisions.
- **Agent memory proposals**: durable behavior/preferences for future agents, written only when explicitly approved or the local workflow supports review.

## Do Not

- Do not treat chat history as the source of truth.
- Do not paste a full transcript into canonical docs.
- Do not record secrets, tokens, private keys, passwords, identity documents, or private material outside the approved scope.
- Do not create a decision record unless a real decision was made.
- Do not create a new project/workspace just because an idea was mentioned.
- Do not overwrite canonical notes broadly; make targeted patches.

## Destination Resolvers

Use the same method across agents. Only resolve destinations differently:

- **Codex**: use repo docs, local vault folders, and reusable skills. Prefer file-backed artifacts over chat-only summaries.
- **Claude**: use project `.claude/` state only for working memory; promote durable knowledge into `docs/`, `adr/`, specs, or the vault.
- **Hermes/MyOS**: use Obsidian/MyOS as the destination resolver, with `Chowmes-Inbox` only as a staging area.

Read `references/methodology.md` for the full routing model.
Read `references/adapters.md` for runtime-specific destination rules.
