# /project-governance — Project Governance Bootstrap (v2)

**Invocation**: `/project-governance`
**Purpose**: Bootstrap complete project governance for any new or existing project.
**Run once** at project start, or to retrofit an existing project.

---

## Core Design Principles

**1. Claude's working memory is not your version control.**
State files live on disk only. They are gitignored. They never trigger CI/CD pipelines, Vercel builds, or deployment costs. You commit code when you decide it's ready — never automatically.

**2. Files stay small enough to read without burning context budget.**

| File | Size Limit | Lives at | Written when |
|------|-----------|----------|--------------|
| `STATUS.md` | 20 lines max | `.claude/state/` | Every checkpoint (full overwrite) |
| `TASK.md` | 15 lines max | `.claude/state/` | While task active (deleted when done) |
| `docs/get-up-to-speed.md` | ~300 lines | `docs/` | When developer commits real changes |

Session start reads: `.claude/state/STATUS.md` + `.claude/state/TASK.md` (if exists) + `git log -5` = ~35 lines total.

**3. Three commands, not five.**
`/wake-up` (session start), `/checkpoint` (save state to disk), `/task` (task gates). That's all.

**4. The cron saves to disk only — no commits, ever.**
The 13-min cron calls `/checkpoint`. Checkpoint writes files. Nothing touches git.

---

## Canonical Project Directory Structure

```
project-root/
│
├── .claude/
│   ├── commands/              ← 3 governance commands
│   ├── state/                 ← STATUS.md, TASK.md (gitignored — Claude's memory)
│   └── archive/sessions/      ← session archives (gitignored)
│
├── .github/
│   └── workflows/
│
├── frontend/
│   └── src/
│       ├── components/
│       │   └── ComponentName/
│       │       ├── index.tsx
│       │       └── __tests__/ ← co-located unit tests (NOT root-level tests/unit/)
│       ├── pages/             ← or app/ for Next.js App Router
│       ├── hooks/             ← custom React hooks
│       ├── services/          ← API clients
│       ├── lib/               ← shared utils/constants (lib inside src/, not at root)
│       └── types/
│
├── backend/
│   └── src/
│       ├── routes/            ← URL mapping only
│       ├── controllers/       ← request handling logic (separate from routes)
│       ├── services/          ← business logic
│       ├── models/            ← data shapes, DB query wrappers
│       ├── middleware/
│       ├── workers/           ← background jobs
│       └── utils/             ← small helpers (utils in backend, lib in frontend)
│           └── __tests__/     ← co-located integration tests
│
├── data/
│   ├── migrations/            ← numbered SQL changes (001-, 002-, ...)
│   └── seeds/
│
├── docs/
│   ├── get-up-to-speed.md     ← agent onboarding (on-demand, not every session)
│   ├── prd/                   ← PRD per feature (required before feature work)
│   ├── adr/                   ← Architecture Decision Records (industry standard name)
│   ├── api/                   ← API reference
│   └── ux/                    ← UI/UX specs, wireframes
│
├── tests/
│   ├── e2e/                   ← cross-stack browser tests (Playwright)
│   └── fixtures/              ← real captured data (NOT generated mocks)
│
├── scripts/
│   ├── setup.sh
│   ├── migrate.sh
│   └── reset-dev.sh
│
├── scratchpad/                ← agent working files (gitignored)
│
├── .env.example
├── .gitignore
├── docker-compose.yml         ← local services if needed
├── README.md
└── CLAUDE.md                  ← agent constitution + coding mandates
```

**Key structural decisions:**
- `STATUS.md`, `CHECKPOINT.md`, `SESSION.md` do NOT live at root — they are Claude's files, not project files. They live in `.claude/state/` and are gitignored.
- `adr/` not `decisions/` — ADR is the universally recognized abbreviation
- Co-located `__tests__/` not root `tests/unit/` — avoids painful cross-package import paths; modern standard (Vitest/Jest)
- `controllers/` separate from `routes/` — MVC: routes = URL mapping, controllers = logic
- `hooks/` in frontend — first-class React concern, needs a home
- `utils/` in backend, `lib/` in frontend — convention matches each ecosystem

---

## What Gets Created

### .claude/commands/wake-up.md

```markdown
# /wake-up — Session Start

## Step 1: Read state
Read .claude/state/STATUS.md (≤20 lines).
If .claude/state/TASK.md exists, read it (≤15 lines).

## Step 2: Check git
git log --oneline -5

## Step 3: Give 5-line briefing
1. Project + overall completion %
2. What shipped recently (from git log)
3. Active task and step, or IDLE
4. Top blocker if any
5. Recommended next action

## Step 4: Register cron (disk-only, no commits)
CronCreate cron="*/13 * * * *" recurring=true
prompt="Run /checkpoint — write .claude/state/STATUS.md to disk. Do NOT git add, commit, or push."

Confirm: "Cron registered (13-min). Disk-only — zero Vercel triggers."
```

### .claude/commands/checkpoint.md

```markdown
# /checkpoint — Save State to Disk

Called every 13 min by cron. Also call manually every 3 task steps.
NEVER runs git add, git commit, or git push.

## Step 1: Overwrite .claude/state/STATUS.md (≤20 lines strict)
# Status — [Project]
**Updated**: [timestamp] | **Overall**: [X]% complete
## Active Task
[name + step, or "IDLE"]
## Component Status
| Component | Status | % |
[5-8 rows max]
## Top 3 Priorities
1. [specific action]
2-3. ...
## Blockers
[1-2 lines or "None"]
## Key Paths
[2 lines]

## Step 2: Overwrite .claude/state/TASK.md if task active (≤15 lines)
# Task: [name]
Started: [date] | Goal: [one sentence]
## Steps
- [x] Done
- [ ] Current ← CURRENT
- [ ] Next
## Files: path/to/file.ts
## Test Plan: docs/prd/test-plans/[name].md
## Last checkpoint: [HH:MM]
If task complete: delete .claude/state/TASK.md

## Step 3: Nothing else. No git. No deploy.
```

### .claude/commands/task.md

```markdown
# /task — Task Management

## /task start "name"
Gate 1: docs/prd/test-plans/[name].md must exist — BLOCK if missing
Gate 2: Write .claude/state/TASK.md to disk
Gate 3: Confirm and begin

## /task done
Gate 1: Run all tests in test plan — BLOCK if any failing
Gate 2: try/catch coverage, no console.log, tsc --noEmit — BLOCK if failing
Gate 3: Delete TASK.md, update STATUS.md
Gate 4: "Ready when you are. Will NOT commit or push without your instruction."
```

### .claude/state/STATUS.md (initial, gitignored)

Write a 20-line snapshot of the project's current state based on what the developer tells you. Ask if needed.

### CLAUDE.md

```markdown
# [Project] — Agent Guidelines

## Context Recovery (after compaction or session gap)
1. Read .claude/state/STATUS.md
2. If .claude/state/TASK.md exists, read it
3. Run git log --oneline -5
Do NOT proceed from compaction summaries alone.

## Mandates
- Try/catch on every async operation
- No console.log in production code
- /task start before any coding task (blocks without test plan)
- /checkpoint every 3 task steps
- NEVER commit or deploy without explicit user instruction

## Key Locations
[fill in]
```

### .gitignore additions

```
# Claude governance — disk-only, never triggers deploys
.claude/state/
.claude/archive/
scratchpad/
```

### No git hook

v2 has no post-commit hook. The hook:
1. Fired on every commit including auto-persist commits → self-referencing loop
2. Triggered unnecessary CI/CD builds
3. Added noise to git history
4. Created tracked artifact files that needed their own commits

`git log --oneline -5` at session start replaces everything the hook was doing.

---

## Bootstrap Steps

### Step 1: Create directories

```bash
mkdir -p .claude/commands .claude/state .claude/archive/sessions
mkdir -p frontend/src/{components,pages,hooks,services,lib,types}
mkdir -p backend/src/{routes,controllers,services,models,middleware,workers,utils}
mkdir -p data/{migrations,seeds}
mkdir -p docs/{prd,adr,api,ux}
mkdir -p tests/{e2e,fixtures}
mkdir -p scripts scratchpad
```

### Step 2: Write 3 command files to .claude/commands/

Write `wake-up.md`, `checkpoint.md`, `task.md` as shown above.

### Step 3: Write initial .claude/state/STATUS.md

Ask the developer: project name, tech stack, what's complete (if retrofitting), top priorities.
Write 20-line STATUS.md.

### Step 4: Update .gitignore

Append:
```
.claude/state/
.claude/archive/
scratchpad/
```

### Step 5: Write CLAUDE.md (if none exists, or append governance section)

### Step 6: Write .env.example stub (if none exists)

```
# Required
DATABASE_URL=
# Optional
REDIS_URL=redis://localhost:6379
```

### Step 7: Write docs/get-up-to-speed.md stub

10-line stub: "Read this on your first session or after a 3+ day gap. For daily sessions, .claude/state/STATUS.md is sufficient." Leave sections blank for developer to fill in.

### Step 8: Write docs/adr/000-template.md

```markdown
# ADR-000: [Title]
**Status**: [Proposed | Accepted | Deprecated]
**Date**: [YYYY-MM-DD]

## Context
[What problem were we solving? What constraints existed?]

## Decision
[What did we decide?]

## Consequences
[What becomes easier? What becomes harder?]
```

### Step 9: Confirm and summarize

```
✓ .claude/commands/  — /wake-up, /checkpoint, /task
✓ .claude/state/     — STATUS.md written (gitignored)
✓ .gitignore         — governance files excluded from git
✓ CLAUDE.md          — agent constitution written
✓ Directory structure created

Next: Run /wake-up to start your session.
Before coding: /task start "task name"
Your commits, your timing — governance never commits for you.
```

---

## Rationale

| Decision | Why |
|----------|-----|
| State files gitignored | Git commits trigger CI/CD. Claude's memory should never cause a Vercel build or burn deployment credits. |
| No git hook | Creates self-referencing commit loops. `git log` at session start replaces it entirely. |
| 3 commands not 5 | Fewer commands = higher adoption. Everything fits in wake-up + checkpoint + task. |
| `adr/` not `decisions/` | Universal abbreviation. Any developer who's worked on a mature codebase knows ADRs. |
| Co-located `__tests__/` | Root `tests/unit/` creates painful cross-package imports. Co-location is the modern standard. |
| `controllers/` separate | Routes = URL mapping only. Controllers = logic. Mixing creates 500-line files. |
| TASK.md deleted when done | File existence = task active. File absence = IDLE. No "Status: IDLE" field to maintain. |
| 20-line STATUS (not 30) | Forces prioritization. Everything essential fits. Tighter = faster to read. |
