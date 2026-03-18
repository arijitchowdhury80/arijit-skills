---
name: algolia-search-audit
description: Run a comprehensive Algolia Search Audit on a prospect website with browser tests and report.
---

# Algolia Search Audit — Orchestrator

Full-stack search experience audit pipeline. This skill orchestrates four dedicated sub-skills:

| Sub-skill | Phase | Time | SKILL.md |
|-----------|-------|------|----------|
| `/algolia-audit-research` | Phase 1: Research (14 steps) | ~15 min | `~/.claude/skills/algolia-audit-research/SKILL.md` |
| `/algolia-live-signals` | Phase 1b: Live Intel — Hiring, Social, News (Apify) | ~3 min | `~/.claude/skills/algolia-live-signals/SKILL.md` |
| `/algolia-audit-browser` | Phase 2: Browser Testing (20 steps) | ~25 min | `~/.claude/skills/algolia-audit-browser/SKILL.md` |
| `/algolia-audit-report` | Phase 3-5: Scoring + Deliverables | ~20 min | `~/.claude/skills/algolia-audit-report/SKILL.md` |

**Execution order:** Phase 1 → Phase 1b (Apify live signals, runs after Step 2 of research) → Phase 2 → Phase 3-5

**Each sub-skill is fully self-contained** — it can be run independently without the orchestrator. `/algolia-live-signals` can also be re-run standalone to refresh hiring/social/news data without re-running the full audit.

---

## Input

`$ARGUMENTS` — prospect website URL (e.g., `autozone.com`, `costco.com`).

Optional flags:
- `--company {name}` — override company name if different from domain
- `--phase {phase}` — run only specific phases (see Phase Flags below)
- `--skip-pdf` — skip PDF generation (faster iteration)
- `--no-browser` — skip Phase 2; useful for research-only runs
- Comma-separated phases: `--phase financials,hiring,intel`

---

## Phase Flags

By default (no `--phase` flag), the full audit runs end-to-end. Use `--phase` to run individual modules.

| Flag | Sub-skill | Description |
|------|-----------|-------------|
| `--phase company` | algolia-audit-research | Company context + executives |
| `--phase techstack` | algolia-audit-research | BuiltWith tech analysis |
| `--phase traffic` | algolia-audit-research | SimilarWeb traffic deep dive |
| `--phase competitors` | algolia-audit-research | Competitor ID + search providers |
| `--phase financials` | algolia-audit-research | 3-year Yahoo Finance + ROI |
| `--phase hiring` | algolia-audit-research | Hiring signals + careers page |
| `--phase intel` | algolia-audit-research | Investor intelligence (10-K, earnings) |
| `--phase strategic` | algolia-audit-research | Strategic angles + trigger events |
| `--phase research` | algolia-audit-research | **All of Phase 1** (no browser) |
| `--phase searchaudit` | algolia-audit-browser | Browser testing (requires Phase 1 workspace) |
| `--phase deliverables` | algolia-audit-report | All deliverables from existing scratchpad data |
| `--phase site` | algolia-audit-report | SPA `{company}/index.html` only |
| `--phase aebrief` | algolia-audit-report | AE pre-call brief only |
| *(no flag)* | All three | Full audit end-to-end |

### Phase Dependencies

```
research (Phase 1)
    ↓
searchaudit (Phase 2) — requires: 01-company-context.md, 02-tech-stack.md, 05-test-queries.md
    ↓
deliverables (Phase 3-5) — requires: all 12 scratchpad files + screenshots/
```

If a required scratchpad file is missing, stop and show the recovery command — do NOT silently skip.

---

## Versioning

Before starting any audit run:

1. Determine company slug: lowercase, hyphens, no spaces (e.g., `costco`, `the-realreal`)
2. Check for existing audit directories:
   - Workspace: `{company}-audit-workspace/` — always reuse/append (never recreate from scratch)
   - Deliverables: check for `{company}-audit-v1/`, `{company}-audit-v2/`, etc.
3. Write deliverables to `{company}-audit-v{N}/` where N = next unused integer
   - Never overwrite previous audit deliverable directories
   - Note in CHECKPOINT.md: `Deliverables version: v{N}`

---

## Execution

### Full Audit (no --phase flag)

**Phase 1 — Research:**
Read `~/.claude/skills/algolia-audit-research/SKILL.md` and execute all Phase 0 + Phase 1 instructions for the provided URL.

After Phase 1 completes, output recovery command:
```
✅ Phase 1 complete — {N} scratchpad files written to {company}-audit-workspace/
Recovery if needed: /algolia-audit-research {url} --refresh {step}
Proceeding to Phase 2 browser testing...
```

**Phase 2 — Browser Testing:**
Read `~/.claude/skills/algolia-audit-browser/SKILL.md` and execute all Phase 2 instructions using the workspace from Phase 1.

After Phase 2 completes, output recovery command:
```
✅ Phase 2 complete — {N} screenshots in screenshots/
Recovery if needed: /algolia-audit-browser {company-slug} --resume-from {step}
Proceeding to Phase 3-5 scoring and deliverables...
```

**Phase 3-5 — Scoring + Deliverables:**
Read `~/.claude/skills/algolia-audit-report/SKILL.md` and execute all Phase 3, 4, and 5 instructions.

After all phases complete, output the Completion Summary (see Output section).

### Phase-Specific Execution (--phase flag)

Map the `--phase` value to the sub-skill using the Phase Flags table above. Read that sub-skill's SKILL.md and follow its instructions for the specified phase(s).

For research sub-phases (company, techstack, traffic, etc.): pass `--phase {value}` through to `algolia-audit-research`. It handles individual step execution natively.

### Agent Teams (parallel research, Wave architecture)

When running `--phase research` or the full audit, Phase 1 runs in 4 parallel waves for speed. The detailed wave structure is defined in `algolia-audit-research/SKILL.md`. Summary:

| Wave | Agents | Steps |
|------|--------|-------|
| Wave 1 (parallel) | A: company+financials, B: tech stack, C: traffic, D: competitors | Steps 1-4 |
| Wave 2 (parallel, after Wave 1) | E: queries, F: competitor search, G: strategic, H: hiring, I: financial synthesis | Steps 5-11 |
| Wave 3 (parallel, after Wave 2) | J: investor intel, K: deep hiring | Steps 12-13 |
| Wave 4 (sequential) | Synthesis | Step 14: ICP mapping |

Phase 2 (browser): always sequential — browser interaction cannot be parallelized.

**Prerequisites for Agent Teams:**
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` environment variable
- Run via `claudesp` (not `claude` or VS Code extension)
- Teammates inherit the lead's permissions at spawn time

---

## Crash Recovery

If any phase fails mid-execution, all progress is saved to scratchpad files in the workspace. Restart from the failed phase:

| Phase that crashed | Recovery command |
|-------------------|-----------------|
| Phase 1 (research) | `/algolia-audit-research {url} --refresh {step}` |
| Phase 2 (browser) | `/algolia-audit-browser {company-slug} --resume-from {step}` |
| Phase 3-5 (deliverables) | `/algolia-audit-report {company-slug}` |

Check `{company}-audit-workspace/CHECKPOINT.md` to see exactly which step was last completed before the crash.

---

## Universal Mandates (apply to all phases and all deliverables)

### Screenshots
Every finding MUST reference the actual screenshot file from `screenshots/`. Chrome MCP imageIds are session-bound — files MUST be saved to disk immediately. Without screenshots on disk, findings are unverifiable.

### Source Citations
Every data point MUST have a clickable hyperlink:
- Financial figures → Yahoo Finance or SEC EDGAR URL
- Traffic stats → SimilarWeb URL
- Technology claims → BuiltWith URL
- Industry benchmarks → Baymard, Forrester, or source study URL
- Hiring signals → Careers page URL
- Investor quotes → Earnings transcript, 10-K, 10-Q, or investor presentation URL
- Case studies → Algolia customer page URL

**A deliverable without sources is INCOMPLETE. A finding without a screenshot is UNVERIFIABLE.**

### MCP-First Data Collection
Always prefer MCP server data over WebSearch. Use WebSearch only for narrative context, executive bios, and earnings transcripts where no structured MCP endpoint exists.

### Legal Disclaimer
Add to ALL deliverables (book PDF cover, deck title slide, AE brief header, landing page footer):

> *Data sourced from public APIs (SimilarWeb, BuiltWith, SEC EDGAR, Yahoo Finance) as of [audit date]. For internal Algolia sales use only. Does not constitute investment advice. All trademarks belong to their respective owners.*

---

## Output

Eight deliverables written to `{company}-audit-v{N}/`:

| File | Format | Audience |
|------|--------|----------|
| `{company}-audit-data.json` | JSON | Internal (source of truth) |
| `{company}/index.html` | HTML SPA | AE, SE, BD (primary internal) |
| `{company}-ae-report.html` | HTML | AE action card |
| `{company}-battle-card.html` | HTML | AE/SE deal room |
| `{company}-leave-behind.html` | HTML | Prospect-facing |
| `{company}-leave-behind.pdf` | PDF | Prospect-facing |
| `{company}-ae-precall-brief.md` | Markdown | AE |
| `{company}-strategic-signal-brief.md` | Markdown | LLMs, downstream AI |

Also kept in workspace: `{company}-search-audit.md` (Phase 4 research report).

Renderer scripts: `~/.claude/skills/algolia-search-audit/scripts/`

### Completion Summary

Output after all phases pass their gates:

```
✅ Audit Complete — {Company Name}
Score: {X.X}/10 — {Critical Gaps Found | Moderate Issues | Strong Baseline}
Top 3 Gaps: {gap1}, {gap2}, {gap3}

Deliverables written to {company}-audit-v{N}/:
  {company}-audit-data.json       ({size})
  {company}/index.html            ({size})
  {company}-ae-report.html        ({size})
  {company}-battle-card.html      ({size})
  {company}-leave-behind.html     ({size})
  {company}-leave-behind.pdf      ({size})
  {company}-ae-precall-brief.md   ({size})
  {company}-strategic-signal-brief.md ({size})

Screenshots: {N} files in screenshots/
Next: /algolia-audit-factcheck {company-slug}
```

---

## Notes

- Be objective — note both strengths and weaknesses
- Focus on issues Algolia can solve
- Use the prospect's actual product names and categories in examples
- If the site already uses Algolia, focus on optimization opportunities
- Never compress Phase 1 data into single lines — each scratchpad file is a chapter of research intelligence
- Post-compaction data integrity: after any context compaction mid-audit, re-read scratchpad files before using any data point. Never regenerate from memory.
