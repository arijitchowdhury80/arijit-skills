---
description: Close the session — runs the full /persist pipeline (including its verify gate), then confirms. SESSION.md IS the bootstrap; new session starts with "read SESSION.md and proceed".
argument-hint: [optional note about the handoff]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
---

The user is closing this Claude Code session. Persist everything, verified, then confirm. No compaction (the session is ending), no on-screen bootstrap prompt (SESSION.md is the resume artifact).

**Sibling commands:**
- `/persist` — save + verify, mid-flow safe
- `/compact` (built-in) — save + compact, continue same session
- `/handoff` (this command) — save + verify + close

## Execute

### Step 1 — Run /persist, completely
Execute `~/.claude/commands/persist.md` — **every stage, as written there. This file deliberately does NOT restate the stage list** (a restated copy silently forked from persist once before — the stage list lives in ONE place: persist.md + `~/.claude/scripts/persist-stages.yaml`).

That includes persist's own Step 8 verify gate (`persist-verify.sh`). The gate's pass/fail table is the evidence.

### Step 2 — Gate the close on the verify result
- Verify exit 0 → proceed to Step 3.
- Verify exit 1 → **STOP.** Surface the FAIL rows to the user. Do not emit the closing confirmation. Fix and re-run, or the user closes knowingly.

### Step 3 — Closing confirmation (nothing else)
```
✅ Handoff complete (persist verified — table above).
Resume: open new session → read SESSION.md and proceed.
```

## Quality bar
- The verify table is the only accepted proof of persistence — no self-reported success.
- SESSION.md must be self-contained: the next session's only required read.

$ARGUMENTS
