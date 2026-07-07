# Chronos

Composite plugin for Google Workspace operations and meeting scheduling. Two skills, one package, explicit dependency between them.

## Skills

- **`skills/gws`** — mechanics layer. Thin wrapper skill for the `gws` CLI: Gmail (search/read/triage/send/draft/reply/forward), Drive, Docs, Sheets, Slides, and raw Calendar CRUD. Auth via OAuth2; the client ID/secret are never hardcoded here — they live in `~/.config/gws/.env` (mode 600, local-only, gitignored everywhere, never committed).
- **`skills/meeting-scheduler`** — orchestration layer, built on top of `gws`. Resolves contacts, pulls freebusy across every attendee, ranks mutual slots across time zones, renders an ASCII picker, and books the event. Its `project/` subfolder is the actual backing implementation (contact resolution, slot-finding, rendering); `config/team.json` (real names/emails/timezones) is intentionally excluded from git — see `project/config/team.json.example` for the schema and keep the real file local-only.

## Why one plugin, not two

`gws` is single-purpose API mechanics; `meeting-scheduler` is a multi-step workflow that calls `gws`'s calendar commands as its plumbing. Bundling them means the dependency is explicit and versioned together, without merging orchestration logic into the mechanics layer (which would violate `gws`'s single responsibility).

## Local paths (this machine)

- `gws` skill mirror: `~/.claude/skills/gws/skill.md`
- `meeting-scheduler` skill mirror: `~/.claude/skills/meeting-scheduler/skill.md`
- `meeting-scheduler` full project (source of truth, includes real `team.json`): `~/AI-Development-OLD/Scheduler/`

This repo copy is the versioned/shareable reference; the live skill directories under `~/.claude/skills/` are what Claude Code actually loads.
