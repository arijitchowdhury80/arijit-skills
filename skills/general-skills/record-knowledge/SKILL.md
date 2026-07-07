---
name: record-knowledge
description: "ALWAYS invoke when the user says 'record this', 'record-knowledge new', 'ingest', 'create a wiki', 'initialize a project wiki', 'log a build step', or 'capture this decision'. Also invoke proactively — without being asked — when an architectural decision is made, when research is read, when a build step completes, or when an open question is resolved. Use for all vault and knowledge operations: initializing project wikis, recording ADRs, ingesting research sources, and logging development history. Do NOT use spec-expander, wiki-update, or knowledge-base — this skill replaces all three."
user-invocable: true
---

# record-knowledge

One skill. Three operations. One wiki structure. Everything goes to the vault.

**Vault bases:**
- Projects: `~/Dropbox/AI-Development/Obsidian/Arijit-Second-Brain/Projects/{slug}/`
- Research domains: `~/Dropbox/AI-Development/Obsidian/Arijit-Second-Brain/Knowledge/{slug}/`

---

## Proactive Behavior

Offer to invoke record-knowledge without being asked when:
- A significant architectural decision is made → offer ADR write
- Research is completed (URLs read, documents analyzed) → offer ingest
- A build step completes → offer dev-log entry
- An open question resolves in conversation → offer open-questions update
- A natural session breakpoint is reached with unrecorded work

Keep the offer short: "That's a significant decision. Want me to record it?" or "I just ingested that source — want me to file it to the wiki?"

---

## Cross-project tracker sync (My OS) — do this on every project write

record-knowledge is the **vault-update layer** of My OS: it writes DEEP per-project knowledge (this skill) AND keeps the SHALLOW cross-project rollup current so the dashboard reflects reality. These are two layers, not two skills — do not create a separate "Vault-Update" skill.

**Rule:** whenever you record something significant to a *project* wiki (a decision/ADR, a dev-log step, a pivot, a resolved/new open question, a new idea or exploratory direction, a status change), ALSO update the cross-project tracker for that project:

- Invoke the **`project-tracker`** skill (it owns the rollup format), or do the equivalent inline:
  - In vault `Projects/ArijitOS/My-Projects.md`: bump that project's `stage` / `health` / one-line description, and append a dated line to the progress log: `- YYYY-MM-DD: <Project> — <what changed> (<source: ADR / commit / dev-log>)`.
  - Mirror the status into memory `project-tracker-status.md`.
- Keep `stage`/`health` as the fixed enums the dashboard expects (stage: idea|in-build|shipping|paused|idle|reference; health: on-track|at-risk|stalled|blocked|unknown).

So one "record this" both files the deep knowledge in the wiki AND updates the rollup + (later) the dashboard and the Etna notification. Deep record and rollup stay in lockstep. Research domains (Knowledge/) skip the tracker sync — it is project-only.

---

## Unified Wiki Structure

Same structure for both project wikis and research domains:

```
{vault-base}/{slug}/
  index.md            ← LLM reads FIRST. Navigation catalog. Always current.
  log.md              ← Append-only operation chronicle
  CLAUDE.md           ← Schema governing this wiki
  raw/                ← Immutable source documents (never modified after write)
    assets/
  wiki/
    overview.md       ← What this is, personas, value props
    requirements.md   ← Spec, functional requirements, acceptance criteria
    decisions/        ← ADRs (one file per decision: YYYY-MM-DD-name.md)
    dev-log.md        ← Append-only build log
    open-questions.md ← Living checklist (check off when resolved)
    sources/          ← One page per ingested research source
    concepts/         ← Domain concept pages
    entities/         ← People, orgs, tools
    syntheses/        ← Cross-cutting analysis and comparisons
```

**Project wikis** use heavily: overview, requirements, decisions, dev-log, open-questions
**Research domains** use heavily: sources, concepts, entities, syntheses
**Both always have**: index.md + log.md updated after every operation

---

## Operation 1: `record-knowledge new [name]`

**Triggers:** "record-knowledge new [name]", "start a wiki for X", "initialize a knowledge base for X"

### Step 1A: Classify and interview

Determine type from context: **project** (building something) or **research domain** (accumulating knowledge on a topic).

Run a focused interview — **one question per turn, max 8 questions**. Stop when gaps are filled. Cover:

| # | What to learn |
|---|---------------|
| 1 | What is this? One-sentence description. |
| 2 | What problem does it solve? (project) or What question is this exploring? (research domain) |
| 3 | Who uses it / who benefits? Personas for projects. |
| 4 | What does success look like? Key capabilities or key questions to answer. |
| 5 | What sources or docs are available to ingest now? |
| 6 | Any hard constraints, deadlines, or dependencies? |

Confirm after gathering: "Does this capture it?" — wait for yes before writing.

### Step 1B: Initialize vault wiki

Create `{vault-base}/{slug}/` with these files:

**`index.md`** — The LLM entry point. Read first in every session.
```markdown
# {Name} — Wiki Index
Type: {project | research domain}
Created: {date}
Last Updated: {date}

Read this file first. It maps the entire wiki.

## Files

| File | Purpose | Last Updated |
|------|---------|-------------|
| wiki/overview.md | What this is, personas, value props | {date} |
| wiki/requirements.md | Spec and acceptance criteria | — |
| wiki/decisions/ | Architectural decisions (ADRs) | — |
| wiki/dev-log.md | Build chronicle | — |
| wiki/open-questions.md | Open questions | — |
| wiki/sources/ | Research source summaries | — |
| wiki/concepts/ | Domain concept pages | — |
| wiki/entities/ | People, orgs, tools | — |
| wiki/syntheses/ | Cross-cutting analysis | — |

## Decision Records

| ADR | Summary | Date | Status |
|-----|---------|------|--------|
| _(none yet)_ | | | |

## Sources

| Title | Slug | Date |
|-------|------|------|
| _(none yet)_ | | |

## Recent Activity

| Date | Event |
|------|-------|
| {date} | Wiki initialized |
```

**`log.md`**
```markdown
# {Name} — Operation Log

## [{date}] new | {Name}
Files touched: index.md, log.md, CLAUDE.md, wiki/overview.md, wiki/open-questions.md
Notes: Wiki initialized
```

**`CLAUDE.md`**
```markdown
# {Name} — Wiki Schema
Type: {project | research domain}
Created: {date}

## Entry Point
Read `index.md` first. It maps all files and tracks recent activity.

## File Roles
- index.md: Navigation catalog — always current
- log.md: Append-only operation chronicle
- raw/: Immutable source documents
- wiki/overview.md: What this is and why
- wiki/requirements.md: Spec and acceptance criteria
- wiki/decisions/: ADRs — one file per decision (YYYY-MM-DD-name.md)
- wiki/dev-log.md: Append-only build log
- wiki/open-questions.md: Living checklist
- wiki/sources/: One summary page per ingested source
- wiki/concepts/: Domain knowledge pages
- wiki/entities/: People, orgs, tools
- wiki/syntheses/: Cross-source analysis

## Iron Rules
- index.md is updated after EVERY operation
- log.md is append-only — never delete entries
- raw/ is immutable — never modify after write
- ADRs: one file per decision in decisions/ — never write to decisions/README.md
```

**`raw/assets/`** — placeholder directory

**`wiki/overview.md`** — populated from interview answers

**`wiki/open-questions.md`** — populate with any unresolved items from interview; otherwise empty with a comment placeholder

Confirm to user:
> "Wiki initialized at `{dir}/{slug}/`. Entry point: `index.md` — LLMs should read this first every session. Use 'record this' to capture decisions/steps/questions, or 'ingest [URL]' to add sources."

---

## Operation 2: `record this`

**Triggers:** "record this", "log this decision", "write this to the wiki", proactive offer accepted, any signal to capture current conversation context to the vault

### Step 2A: Identify the target wiki

1. Check SESSION.md — slug is usually recorded there
2. Infer from the current working directory name
3. Ask: "Which wiki? Give the slug."

### Step 2B: Detect content type and write

Read current conversation context. Detect all applicable types. Write **all** of them in one pass:

**Architectural decision** → `wiki/decisions/YYYY-MM-DD-kebab-name.md` — NEW FILE per decision

```markdown
# ADR: {Decision Name}

**Date:** YYYY-MM-DD
**Status:** Accepted

## Context
{Why this decision was needed}

## Decision
{What was decided — one clear sentence}

## Rationale
{Why this was chosen — specific technical reasons}

## Alternatives Considered
| Option | Why rejected |
|--------|-------------|

## Consequences
{What changes — new dependencies, env vars, test setup}
```

Rationale rule: if none was given → write `[Rationale not captured — add if known]`. Surface it: "Want to add rationale before closing the ADR?"

**Build step complete / discovery / pivot** → append to `wiki/dev-log.md`

```markdown
### YYYY-MM-DD — {Step or event name}

**Status:** Done | Blocked | Pivoted
**What happened:** {1–3 factual sentences}
**Key decisions:** {Pointer to ADR if written, otherwise "none"}
**Tests written:** {If applicable}
**Next:** {Next step}
```

**Open question resolved** → update `wiki/open-questions.md` in-place

```markdown
- [x] {original question text}
  **Resolution (YYYY-MM-DD):** {what was decided}
```

**New unknown emerged** → append to `wiki/open-questions.md`

```markdown
- [ ] {question} [Added YYYY-MM-DD]
```

**Requirements or spec content** → update `wiki/requirements.md`

**Research insight or cross-source analysis** → `wiki/syntheses/{slug}.md`

### Step 2C: Update index.md (mandatory after every write)

- `Last Updated` at top
- `Last Updated` column for each file written
- If ADR written: add row to Decision Records table
- Always add a Recent Activity row: `| YYYY-MM-DD | {type}: {name} |`
- Keep Recent Activity ≤ 10 rows — remove oldest if needed

Append to `log.md`:
```markdown
## [{date}] record | {content description}
Files touched: {list}
Notes: {anything worth flagging}
```

---

## Operation 3: `ingest [URL or file]`

**Triggers:** "ingest [URL or file]", "read this and file it", "add this paper/article/doc to the wiki"

### Step 3A: Identify the target wiki

Same as Operation 2 Step 2A.

### Step 3B: Read and ingest

1. Read the source fully (WebFetch for URL, Read for file path).

2. Write source summary to `wiki/sources/{slug}.md`:

```yaml
---
type: source
title: "{Full title}"
author: "{Author(s)}"
date: YYYY-MM-DD
url: "{URL if applicable}"
raw: "raw/{slug}.md"
tags: []
---
```
Sections: **Summary** (3–5 sentences, core argument), **Key Claims** (specific citable bullets), **Key Concepts** (wikilinks to concept pages), **Notable Quotes** (verbatim, max 5), **Connections** (wikilinks to related pages)

3. For every significant concept introduced or enriched: update or create `wiki/concepts/{slug}.md`:

```yaml
---
type: concept
title: "{Concept name}"
aliases: []
tags: []
---
```
Sections: Definition (1–2 sentences), Extended Explanation, Sources, Related Concepts, Open Questions

4. For every significant person, org, tool, or product: update or create `wiki/entities/{slug}.md`:

```yaml
---
type: entity
entity-type: person | org | tool | product
title: "{Name}"
tags: []
---
```
Sections: Overview, Key Contributions (person) / Key Capabilities (tool), Appearances, Related Entities

5. Save verbatim source to `raw/{slug}.md` (immutable — never edit after write).

6. Scan existing wiki pages for contradictions — flag: `> ⚠️ CONFLICT: {description} — see: [[link]]`

7. Update `index.md`: add rows to Sources table + Concepts and Entities tables, update Last Updated, add Recent Activity row.

8. Append to `log.md`:
```markdown
## [{date}] ingest | {Source Title}
Files touched: {comma-separated list}
Notes: {anything worth flagging}
```

**Iron rules for ingest:**
- A single source typically touches 5–15 pages. Do NOT just write the source summary and stop. Update every relevant concept and entity page.
- Good synthesis insights: file as `wiki/syntheses/{slug}.md` — don't let them disappear into chat.
- Contradictions must be flagged at ingest time, not discovered later.
- index.md and log.md must be updated on every ingest, no exceptions.

---

## Context Compaction Survival

If context compacts mid-operation:
1. Read `{slug}/index.md` — tells you what exists
2. Read `{slug}/log.md` — tells you what's been processed
3. Resume at the next unfinished step

The wiki files are the state. The context window is temporary.
