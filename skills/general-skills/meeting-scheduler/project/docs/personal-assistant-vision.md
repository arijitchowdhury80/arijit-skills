# Personal AI Assistant Platform — Vision Document
**Captured:** 2026-04-15  
**Source:** Arijit Chowdhury (recorded during Scheduler v1 build session)  
**Status:** Raw vision — not yet refined into a spec

---

## The Vision in One Sentence

A personal AI assistant platform built as a collection of independent agents, each owning a domain of Arijit's work life, all orchestrated through a Mission Control dashboard — where clicking any item launches the right Claude instance to do the work.

---

## The Architecture: Agent-Based Personal OS

Each capability is a standalone **agent** (not a feature, not a function — an agent with its own:
- **Playbook** — the instructions, context, and workflow for that domain
- **Protocol** — how the agent communicates, what inputs it accepts, what outputs it produces
- **Thin Execution Layer** — the Claude Code skill + Python helpers that power it
- **Harness** — the scaffolding that wires it into Claude Code and the platform

This mirrors the PRISM architecture: each module = an agent with a clean contract. The personal assistant IS a PRISM-style platform, but for Arijit's personal work.

---

## Known Agents (Modules)

### Module 1: Scheduler (Built — v1 complete)
- **Purpose:** Schedule meetings across time zones
- **Trigger:** "Schedule a meeting with X for next week"
- **Output:** Ranked availability options → calendar event created
- **Status:** MVP working. Gaps: People API scope, freebusy for non-subscribed calendars.

### Module 2: Morning Briefing Agent (Concept)
- **Purpose:** Every morning, check Arijit's calendar for the day, review memory for in-progress work, surface what needs attention
- **Trigger:** Daily morning (cron) or "what's my day look like?"
- **Output:** Structured briefing: meetings today (with prep notes), open tasks, what's overdue
- **Builds on:** Scheduler (calendar access) + Memory system

### Module 3: Memory Agent (Concept)
- **Purpose:** Manage and surface cross-session memory. "What am I working on? What did I leave unfinished?"
- **Trigger:** "What's on my plate?" / start of any Claude session
- **Output:** Prioritized context dump — current projects, pending decisions, open threads
- **Note:** This is essentially the CLAUDE.md + memory system made interactive

### Module 4: Mission Control Dashboard (Concept)
- **Purpose:** Web-based (or local HTML) overview of everything — active projects, today's meetings, open tasks, agent statuses
- **UX:** Click on any item → launches the relevant Claude instance with correct context
- **Design:** Like PRISM but personal. Modular panels, each owned by an agent.
- **Tech:** Could be a local web server (FastAPI + HTML) or a simple HTML file Claude regenerates

### Future Modules (Named, Not Scoped):
- **Email triage agent** — summarize inbox, draft replies
- **Weekly review agent** — generate week-in-review, plan next week
- **Research agent** — "go deep on X topic and brief me"
- **Context agent** — "before this meeting, prepare me" (pull relevant context from calendar, email, memory)

---

## The UX Principle

**Zero friction.** No mode switching, no "open the scheduler app." Just talk to Claude:
> "Hey Claude, schedule a meeting with David next week"
> "What's my day look like?"
> "What am I working on?"

The skill layer makes this work — each skill is globally available in every Claude Code thread. The user just talks; Claude routes to the right agent.

For the dashboard: one URL, always current, shows the whole picture. Clicking any item drops the user into a pre-loaded Claude session with full context.

---

## The Build Order

1. ✅ **Scheduler** — foundation skill, gws integration, multi-TZ logic
2. **Morning Briefing** — extends Scheduler + reads memory, runs on cron
3. **Memory Agent** — formalizes the existing memory system into an interactive skill
4. **Mission Control** — dashboard that ties all agents together with a UI
5. **Email/Context Agents** — depends on Gmail MCP or gws gmail integration

---

## Architectural Principles (From the Brief)

- Each module is an **agent**, not a script
- Agents communicate through well-defined **protocols** (JSON contracts)
- A **thin execution layer** (skill + helpers) is all that's needed per agent
- The **playbook** (skill `.md` file) is the agent's brain — change the playbook, change the behavior
- The **harness** is Claude Code itself — already built, already running
- Distribution is not a concern in v1 — personal use only. Future: share with the team if useful.

---

## What This Is Really About

This is Arijit building his own cognitive operating system — a layer on top of Claude that knows his context, his team, his work patterns, and his tools. Each agent is a specialist. The platform is the orchestrator. The human stays in the loop for decisions; agents handle the grunt work.

The Scheduler is the proof of concept. If it works, the model scales to every other domain.

---

## Open Questions (Not Answered Yet)

1. How do agents hand off context to each other? (Morning Briefing needs Scheduler's calendar data)
2. What does the Mission Control dashboard actually look like? (Needs design work)
3. How do we handle agent persistence — do they run on cron or on demand?
4. Is there a central "agent registry" that knows which agents exist and what they do?
5. When agents conflict (e.g. memory says X but calendar says Y), who wins?
