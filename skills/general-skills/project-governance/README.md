# Project Governance for Claude Code (v2)

> **One command. Any project. Claude never forgets — and never deploys without your say-so.**

A [Claude Code](https://claude.ai/code) skill that solves the two most painful problems with AI-assisted development: **context loss between sessions** and **agents shipping untested code**.

---

## The Problem

Claude Code is extremely capable — but it has no memory between sessions.

Every time you open a new conversation, Claude starts from zero. It re-reads the same files, re-discovers the same architecture, re-makes the same mistakes. In long sessions, context compaction silently drops earlier work. After a multi-day gap, the agent has no idea what changed.

**And if you use Vercel, GitHub Actions, or any CI/CD pipeline**: governance systems that auto-commit to git will trigger paid builds for zero user-facing changes. Every 13-minute heartbeat = one deployment. That's real money for bookkeeping.

This skill fixes all of it.

---

## The v2 Design Principle

> **Claude's working memory is not your version control.**

State files live on disk only. They are gitignored. They never trigger CI/CD pipelines, Vercel builds, or deployment credits. You commit your code when you decide it's ready — Claude never commits for you.

---

## What It Does

Running `/project-governance` once bootstraps a complete governance system:

### 1. Two Bounded State Files (~35 lines at session start)

Both files live in `.claude/state/` — gitignored, local-only.

| File | Size | Lives at | Purpose |
|------|------|----------|---------|
| `STATUS.md` | ≤ 20 lines | `.claude/state/` | Project snapshot: components, priorities, blockers. Full overwrite. |
| `TASK.md` | ≤ 15 lines | `.claude/state/` | Active task: steps, files, test plan link. Deleted when task completes. |

`TASK.md` only exists while a task is active. File presence = task running. File absence = idle. No "Status: IDLE" field to maintain.

Session start total: STATUS.md (20) + TASK.md (15 if active) + `git log -5` = **~35 lines**.

### 2. Two-Tier Persistence (No git, no deploys)

```
Tier 1: 13-minute cron (in-session)
         → calls /checkpoint every 13 minutes
         → /checkpoint writes .claude/state/ files to disk
         → zero git operations, zero Vercel triggers

Tier 2: Disk persistence (always-on, free)
         → files in .claude/state/ survive between sessions on the same machine
         → git log --oneline -5 at session start shows what changed since last session
         → no hook, no stale flag, no self-referencing commit loops
```

### 3. Three Commands (Not Five)

| Command | When | What it does |
|---------|------|-------------|
| `/wake-up` | Start of every session | Reads `.claude/state/` + git log → 5-line briefing → registers 13-min cron |
| `/checkpoint` | Every 13 min (automatic) + every 3 task steps (manual) | Overwrites state files on disk. **No git. No commit.** |
| `/task start "name"` | Before any coding | Checks test plan exists — **blocks if missing**. Writes TASK.md. |
| `/task done` | After finishing | Runs all tests — **blocks if any failing**. Deletes TASK.md. Confirms ready — **won't commit without your instruction**. |

### 4. Canonical Project Directory Structure

```
project-root/
├── .claude/
│   ├── commands/          ← /wake-up, /checkpoint, /task
│   ├── state/             ← STATUS.md, TASK.md (gitignored)
│   └── archive/sessions/  ← optional session archives (gitignored)
├── frontend/src/
│   ├── components/        ← with co-located __tests__/
│   ├── pages/             ← or app/ for Next.js App Router
│   ├── hooks/             ← custom React hooks
│   ├── services/          ← API clients
│   ├── lib/               ← shared utils/constants
│   └── types/
├── backend/src/
│   ├── routes/            ← URL mapping only
│   ├── controllers/       ← request handling logic
│   ├── services/          ← business logic
│   ├── models/            ← data shapes, DB wrappers
│   ├── middleware/
│   ├── workers/           ← background jobs
│   └── utils/
├── data/migrations/
├── docs/
│   ├── get-up-to-speed.md ← agent onboarding (on-demand)
│   ├── prd/               ← PRDs (required before feature work)
│   ├── adr/               ← Architecture Decision Records
│   ├── api/
│   └── ux/
├── tests/
│   ├── e2e/               ← cross-stack Playwright tests
│   └── fixtures/          ← real captured data (no mocks)
├── scripts/
├── scratchpad/            ← gitignored
├── .env.example
├── README.md
└── CLAUDE.md              ← agent constitution + mandates
```

**Key decisions:**
- State files in `.claude/state/` (not root) — they're Claude's files, not project files
- `adr/` not `decisions/` — industry standard name every developer recognizes
- Co-located `__tests__/` not root `tests/unit/` — avoids painful cross-package imports; modern standard
- `controllers/` separate from `routes/` — MVC: routes = URL mapping only
- `hooks/` in frontend — first-class React concern that needs a home
- `utils/` in backend, `lib/` in frontend — matches each ecosystem's conventions

### 5. Development Mandates (written into CLAUDE.md)

- Try/catch on every async operation
- No `console.log` in production code — structured logging only
- `/task start` required before any coding — blocks without a test plan
- `/checkpoint` every 3 task steps — protects against context compaction loss
- **No commits or deploys without explicit user instruction — ever**

---

## Why No Git Hook?

v1 of this skill used a git post-commit hook. It caused three problems:

1. **Self-referencing loop**: The hook fired on every commit including auto-persist commits, which triggered another persist, which committed, which fired the hook again.
2. **Paid deployments**: Every governance commit triggered Vercel/GitHub Actions builds.
3. **Polluted git history**: `chore: auto-persist 14:23` commits mixed in with real work.

v2 replaces the hook with `git log --oneline -5` at session start. Same information, zero side effects.

---

## Requirements

- [Claude Code](https://claude.ai/code) (any version)
- Git (initialized repo)
- macOS, Linux, or WSL

No API keys. No external services. No CI/CD configuration.

---

## Installation

### Option A — GitHub (Recommended)

```bash
git clone https://github.com/arijitchowdhury80/algolia-claude-skills.git
cd algolia-claude-skills/
chmod +x install-governance.sh
./install-governance.sh
```

### Option B — curl (No git required)

```bash
mkdir -p ~/.claude/skills/project-governance
curl -s https://raw.githubusercontent.com/arijitchowdhury80/algolia-claude-skills/main/skills/project-governance/SKILL.md \
  -o ~/.claude/skills/project-governance/SKILL.md
```

### Option C — Zip

Download the zip from GitHub → extract → `chmod +x install-governance.sh && ./install-governance.sh`

### Verify

```bash
claude
# Type / — you should see "project-governance" in the autocomplete
```

---

## Quick Start

```bash
# 1. Install (once, globally)
chmod +x install-governance.sh && ./install-governance.sh

# 2. Open any project
cd my-project/
claude

# 3. Bootstrap governance (once per project)
/project-governance

# 4. Every future session:
/wake-up
```

After `/wake-up`, the 13-minute cron is registered. It calls `/checkpoint` automatically, writing state to disk. You just work.

---

## Typical Session Flow

```
You: /wake-up
Claude reads: .claude/state/STATUS.md + TASK.md (if exists) + git log -5
Claude says: "Here's where we are: [5-line briefing]"
Claude registers: cron → /checkpoint every 13 min (disk only)

You: /task start "add search pagination"
Claude checks: docs/prd/test-plans/search-pagination.md — exists ✓
Claude writes: .claude/state/TASK.md
Claude begins: Step 1

[Every 13 minutes, automatic]
Cron fires → /checkpoint
→ Overwrites .claude/state/STATUS.md (20 lines)
→ Updates .claude/state/TASK.md (step progress)
→ No git. No Vercel trigger.

[After finishing]
You: /task done
Claude runs: all tests in search-pagination test plan
All passing ✓
Claude says: "Ready when you are. NOT committing without your instruction."

You: git add -p && git commit -m "feat: add search pagination"
→ You decide what to commit and when. Always.
```

---

## Retrofitting an Existing Project

Works on existing projects — won't touch your code.

```bash
cd my-existing-project/
claude
/project-governance
```

Creates `.claude/` directory and adds governance files to `.gitignore` alongside your existing code. Writes `CLAUDE.md` if none exists, or appends the governance section if one does.

---

## File Reference

| File | Location | Gitignored | Purpose |
|------|----------|------------|---------|
| `STATUS.md` | `.claude/state/` | Yes | 20-line project snapshot |
| `TASK.md` | `.claude/state/` | Yes | Active task state (deleted when done) |
| `wake-up.md` | `.claude/commands/` | No | Session start command |
| `checkpoint.md` | `.claude/commands/` | No | Disk-write state command |
| `task.md` | `.claude/commands/` | No | Task gate command |
| `CLAUDE.md` | project root | No | Agent constitution |
| `docs/get-up-to-speed.md` | `docs/` | No | Agent onboarding (on-demand) |

---

## FAQ

**Does this work on Vercel/Netlify/GitHub Actions projects?**
Yes — that's specifically what v2 is designed for. State files are gitignored. The cron never commits. You control all git operations.

**Does it work on an existing project?**
Yes. Creates governance files alongside your code without touching it.

**What happens after context compaction?**
Tell Claude: "Read `.claude/state/STATUS.md` and `TASK.md` before continuing." Those two files (~35 lines) fully restore context.

**Do I need to re-run `/project-governance` each session?**
No — run it once. Each session, run `/wake-up` instead.

**Can I use this with other Claude Code skills?**
Yes. Fully independent. Project commands in `.claude/commands/` don't conflict with global `~/.claude/skills/`.

**What if I work across multiple machines?**
State files are local-only by design. On a new machine, run `/wake-up` and Claude will re-read git log to understand what changed. You can optionally commit `.claude/state/` if you want cross-machine sync — just remove it from `.gitignore`.

---

## Uninstall

```bash
# Remove skill globally:
rm -rf ~/.claude/skills/project-governance

# Remove from a specific project:
rm -rf .claude/state/ .claude/archive/ .claude/commands/
# Remove the gitignore entries (3 lines)
# Optionally remove CLAUDE.md if it was created by this skill
```

---

## Updating

```bash
cd algolia-claude-skills/
git pull
./install-governance.sh
```

---

*Part of the [Algolia Claude Code Skills](https://github.com/arijitchowdhury80/algolia-claude-skills) collection — usable by any developer, no Algolia account needed.*
