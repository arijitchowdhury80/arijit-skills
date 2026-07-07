---
description: Persist full session context to disk — vault project wiki, tracker, memory, SESSION.md, wiki log/hot, graph + dashboard data — then VERIFY every write with substance checks. Does NOT compact. For save+compact use /compact (PreCompact hook auto-runs persist). For session close use /handoff.
argument-hint: [optional note about why you're persisting]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
---

The user wants the session state saved so they can exit now and resume later with zero context loss. Write everything down; then PROVE it landed. A persist that is not verified is not a persist.

**Pipeline contract:** the stage list lives in ONE manifest — `~/.claude/scripts/persist-stages.yaml` — and the gate is `~/.claude/scripts/persist-verify.sh`. This file describes the stages; the manifest defines them; the verify script enforces them. Never add/remove a stage in one place without the others (that drift class is what rotted the old pipeline). Design of record: `AI-OS/research/GATE1-SECOND-BRAIN-DESIGN.md` (Gate 1 approved 2026-07-07).

**Sibling commands (DO NOT confuse):**
- `/persist` (this command) — save + verify. No compaction. Mid-flow crash insurance.
- `/compact` (built-in, gated) — the guard hook BLOCKS it unless persist succeeded in the last 15 min (`~/.claude/.persisted_recently` — dropped ONLY by the verify script on full pass).
- `/handoff` — runs THIS command, then emits the one-line close confirmation. It has no step list of its own.

## Execute in this exact order

### 0. Stamp the start
```bash
PERSIST_START=$(date +%s)
```
Every verify check compares against this stamp. Also identify: CWD + project slug (memory dir name), the ACTIVE vault project name under `Projects/` (you'll pass both to the verify script), git status if repo.

### 1. CORE (cheap, deterministic — never skip, no prose required)
- **vault event log:** if `wiki/log.md` exists in the vault, APPEND one dated line: `## [YYYY-MM-DD HH:MM] <session slug> — <files/areas touched>`. Append-only — never rewrite this file. (Pre-migration: skip, verify reports SKIP.)
- **graph + dashboard:** if the graph builder / dashboard refresh scripts exist (`AI-OS/cockpit/`), run them. If absent, skip — verify reports it honestly.
- **VPS sync:** if the sync queue is configured, queue (never run inline, never --delete). Network ships are async — a dead tailnet must not fail a persist.

### 2. SYNTHESIS — vault project wiki (THE compiled truth)
For the active project(s) this session touched, update `Projects/<name>/` in the vault using the record-knowledge convention — **this is the ONLY vault convention; the old Modules/<name>/Spec.md pattern is retired**:
- `index.md` — two-zone shape: **compiled truth ABOVE the `---` divider** (rewrite freely, current-state synthesis), **append-only cited timeline BELOW it**. Update the `updated:` frontmatter stamp. Every claim in the compiled zone must trace to a timeline entry or a linked note — no unsourced assertions.
- `log.md` — append today's dated entry (what happened, files, decisions).
- If the project folder doesn't exist yet, invoke the `record-knowledge` skill to initialize it — do NOT hand-roll a different structure. **There is no "inline equivalent" — that escape hatch is closed.**

### 3. SYNTHESIS — hot cache
If `wiki/hot.md` exists in the vault: rewrite it (≤500 words) — what the last sessions did, what's live, what's blocked, where the next session should look first. This is the first thing every fresh session reads. (Pre-migration: skip.)

### 4. SYNTHESIS — project tracker
**Invoke the `project-tracker` skill** to sync `Projects/ArijitOS/My-Projects.md` (stage / health / next / dated log line). Inline updates forbidden — the bypass is why the tracker went dormant historically.

### 5. SYNTHESIS — memory (cross-session state)
At `~/.claude/projects/<slug>/memory/`:
- One focused file per significant item (feedback / project / user / reference types per global CLAUDE.md).
- Update `MEMORY.md` index (one line per memory) and `session_pointer.md` (where the next session picks up).
- Pointers + behavior, not content — never duplicate what the vault or SESSION.md holds.

### 6. SYNTHESIS — ./SESSION.md (this-session continuity)
All sections, no truncation: **Status** (one line) · **Resume action** (numbered, concrete) · **Where we stopped (exact)** · **Decisions locked** · **Remaining work** · **Reference files** · **What has NOT been done** (prevents false completion claims) · **Files written this session**.

### 7. ./CLAUDE.md only if missing or stale
Thin pointer, ≤50 lines: SESSION.md, memory dir, vault project folder, hard constraints. Accurate → leave it.

### 8. VERIFY — the gate (mandatory, replaces trust)
```bash
~/.claude/scripts/persist-verify.sh --start $PERSIST_START --project "<VaultProjectName>" --slug "<memory-slug>" --cwd "$PWD"
```
The script checks SUBSTANCE per stage (dated entries, content changes, word caps, index consistency — mtimes alone prove nothing) and prints the pass/fail table. **It drops the /compact marker itself, only on full pass.**
- Exit 0 → report "persisted and verified" with the table.
- Exit 1 → **the persist FAILED.** Show the FAIL rows, fix what's fixable, re-run verify. Never summarize a failed persist as done, and never touch the marker manually.

### 9. Report
Tight summary in chat: the verify table · files written (paths) · whether /compact is unblocked · what's captured vs still missing · pending approvals for next session · offer git commit if repo (ask, never auto-commit) · **the project-status board** (one row per project: stage + 🟢/🟡/🔴/⚪ + one-line next action; when the AI-OS dashboard graph exists, render/link it here instead).

## Quality bar
- Zero context loss; every decision, question, and file captured.
- No duplication — each surface has one distinct role; Projects/<name>/index.md is the ONLY compiled project truth.
- No false green. The verify table is the completion claim — nothing else is.
- Plain language everywhere — the reader is a future Claude with no conversation history.

$ARGUMENTS
