---
name: algolia-search-audit
description: Run a comprehensive Algolia Search Audit on a prospect website with browser tests and report.
---

## CANONICAL PATH DEFINITIONS

```
AUDIT_DIR  = ~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit
ARIAN_DIR  = ~/algolia-arian-v2
SKILLS_DIR = ~/.claude/skills/algolia-search-audit
```

**Every audit MUST use this structure:**
```
$AUDIT_DIR/{CompanyName}/
├── research/          ← scratchpads 01-12, CHECKPOINT.md, FACTCHECK_GATE.md
├── factcheck/         ← factcheck dimension files (never published)
├── scripts/           ← company-specific scripts only
└── deliverables/
    ├── index.html                ← SPA
    ├── screenshots/              ← browser audit screenshots
    ├── ae-report.html
    ├── battle-card.html
    ├── leave-behind.html
    └── {slug}-*.md               ← markdown reports
```

**Published to GitHub/Vercel:**
```
$ARIAN_DIR/{slug}/                ← mirrors $AUDIT_DIR/{CompanyName}/deliverables/
├── index.html
├── screenshots/
├── ae-report.html
├── battle-card.html
└── leave-behind.html
$ARIAN_DIR/{slug}-audit-data.json ← JSON stays at root
```



# Algolia Search Audit — Orchestrator

Full-stack search experience audit pipeline with mandatory factcheck gate and human review before publishing.

| Sub-skill | Phase | Time | SKILL.md |
|-----------|-------|------|----------|
| `/algolia-audit-research` | Phase 1: Research (14 steps) | ~15 min | `~/.claude/skills/algolia-audit-research/SKILL.md` |
| `/algolia-live-signals` | Phase 1b: Live Intel — Hiring, Social, News (Apify) | ~3 min | `~/.claude/skills/algolia-live-signals/SKILL.md` |
| `/algolia-audit-browser` | Phase 2: Browser Testing (20 steps) | ~25 min | `~/.claude/skills/algolia-audit-browser/SKILL.md` |
| `/algolia-audit-report` | Phase 3-5: Scoring + Deliverables | ~20 min | `~/.claude/skills/algolia-audit-report/SKILL.md` |
| `/algolia-audit-factcheck` | Phase 6: Fact Verification (**MANDATORY**) | ~25 min | `~/.claude/skills/algolia-audit-factcheck/SKILL.md` |

**Full execution order (non-negotiable):**
```
Phase 1  → /algolia-audit-research       (14 research steps)
Phase 1b → /algolia-live-signals         (Apify: hiring + social + news)
Phase 2  → /algolia-audit-browser        (20 browser tests + screenshots)
Phase 3-5→ /algolia-audit-report         (score + render SPA + deliverables)
Phase 6  → /algolia-audit-factcheck      ← MANDATORY BEFORE ANY PUBLISH
           ↓
         Read FACTCHECK_GATE.md
           ↓
         ACTION = BLOCKED  → Stop. Show issues. Fix required.
         ACTION = WARN     → Stage + show warnings. Explicit approval needed.
         ACTION = PROCEED  → Stage to hub. Present for local review.
           ↓
         USER REVIEWS locally at http://127.0.0.1:8766/{slug}/
           ↓
         User says "publish" → git push → Vercel auto-deploys
```

**Why factcheck is mandatory:** Claude fabricates data. Stats are wrong. Links break. ROI math errors occur. Case study metrics get paraphrased. The factcheck is the only thing standing between an AE presenting wrong data to a prospect and an accurate audit. Every single audit must pass factcheck before it can be staged or published. No exceptions.

**Each sub-skill is fully self-contained** — it can be run independently. `/algolia-live-signals` can be re-run standalone to refresh data. `/algolia-audit-factcheck` can be re-run after fixes without re-running the full audit.

---

## THE PUBLISH PIPELINE (Full Detail)

### Step 1–5: Run Full Audit Pipeline
```
/algolia-audit-research {slug}
/algolia-live-signals {slug}
/algolia-audit-browser {slug}
/algolia-audit-report {slug}
```

### Step 6: Run Factcheck (MANDATORY — never skip)
```
/algolia-audit-factcheck $AUDIT_DIR/{CompanyName}/research/
```

The factcheck writes `FACTCHECK_GATE.md` to `$AUDIT_DIR/{CompanyName}/research/`. Read it immediately after.

### Step 7: Evaluate the Gate

Read `$AUDIT_DIR/{CompanyName}/research/FACTCHECK_GATE.md` and parse:

**If `ACTION: BLOCKED`:**
```
⛔ PUBLISH BLOCKED — {BLOCKING_COUNT} critical issue(s) must be fixed.

Blocking issues:
{list from BLOCKING ISSUES section}

These must be corrected before this audit can be staged or published.
Reply with what you'd like to fix, or run:
  /algolia-audit-factcheck $AUDIT_DIR/{CompanyName}/research/
again after corrections.
```
DO NOT stage. DO NOT push. Wait for user direction.

**If `ACTION: WARN`:**
```
⚠️  FACTCHECK WARNINGS — Score: {SCORE}/10 ({CONFIDENCE})
{WARNING_COUNT} items need your review before publishing:

{list warnings}

The audit has been staged for local review. You must explicitly acknowledge
these warnings before I will push to GitHub.

Review at: http://127.0.0.1:8766/{slug}/
Type 'publish' to deploy (acknowledging the warnings above), or describe what to fix.
```
Proceed to staging (Step 8), but require explicit "publish" before Step 10.

**If `ACTION: PROCEED`:**
```
✓ FACTCHECK PASSED — Score: {SCORE}/10 (HIGH CONFIDENCE)
Staging for local review...
```
Proceed automatically to staging (Step 8).

### Step 8: Start Local Server + Stage to Hub

```bash
# Start/restart server from hub root
lsof -ti tcp:8766 | xargs kill -9 2>/dev/null; sleep 0.3
cd ~/algolia-arian-v2 && python3 -m http.server 8766 &>/dev/null &
sleep 1

# Stage to hub (LOCAL commit, not pushed yet)
cd $AUDIT_DIR/{CompanyName}/research
bash ~/.claude/skills/algolia-search-audit/scripts/publish-audit.sh {slug} ~/algolia-arian-v2 --stage-only
```

### Step 9: Present Review to User

Show this exact block:

```
═══════════════════════════════════════════════════════
  {COMPANY} AUDIT — READY FOR LOCAL REVIEW
═══════════════════════════════════════════════════════

  Factcheck: {SCORE}/10 — {CONFIDENCE}
  {If WARN: show warning list}

  Score:     {AUDIT_SCORE}/10 — {VERDICT}
  ROI est:   {CONSERVATIVE} (conservative) · {MODERATE} (moderate)
  Top gaps:  G1: {GAP1} · G2: {GAP2} · G3: {GAP3}

  Review at: http://127.0.0.1:8766/{slug}/
  Hub index: http://127.0.0.1:8766/

  When you're satisfied, reply:
    "publish"      → push to GitHub, Vercel auto-deploys in ~60 sec
    "fix {issue}"  → describe what to change, I'll fix and re-stage
    "factcheck"    → re-run factcheck if you made manual edits
═══════════════════════════════════════════════════════
```

Wait. Do not push until the user explicitly says "publish".

### Step 10: On "publish" Approval

```bash
cd ~/algolia-arian-v2
bash ~/.claude/skills/algolia-search-audit/scripts/publish-audit.sh {slug} ~/algolia-arian-v2 --push-only
```

Then confirm:
```
✓ {COMPANY} published to GitHub.
  Vercel is auto-deploying (ready in ~60 seconds).

  Live URL: https://algolia-arian-v2.vercel.app/{slug}/
  Hub:      https://algolia-arian-v2.vercel.app/
```

### Step 11: On "fix {issue}" (iterative fixes)

1. Make the requested fix (edit JSON, re-render SPA, update scratchpad as needed)
2. Re-run factcheck if the fix touches a factual claim: `/algolia-audit-factcheck $AUDIT_DIR/{CompanyName}/research/`
3. Re-stage: `bash publish-audit.sh {slug} ~/algolia-arian-v2 --stage-only`
4. Return to Step 9 (show updated review prompt)

---

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
   - Workspace: `$AUDIT_DIR/{CompanyName}/research/` — always reuse/append (never recreate from scratch)
   - Deliverables: check for `{company}-audit-v1/`, `{company}-audit-v2/`, etc.
3. Write deliverables to `$AUDIT_DIR/{CompanyName}/deliverables/` (canonical — no versioning)
   - Never overwrite previous audit deliverable directories
   - Note in CHECKPOINT.md: `Deliverables written to: $AUDIT_DIR/{CompanyName}/deliverables/`

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

## Key Architecture Principles

### Style Token Enforcement (2 layers — added 2026-03-19)

- **Layer 1 — PostToolUse hook**: Project settings at `.claude/settings.local.json` in the audit working directory. Runs `check-style-tokens.py` after every Edit/Write to `index-template.html`. Immediately flags violations in the session.
- **Layer 2 — Renderer gate**: `render-audit.ts` runs `check-style-tokens.py` before rendering. If violations exist, render is BLOCKED with `Deno.exit(1)`. Cannot produce output with T token violations.
- **T token system**: All inline `font-size`, `font-weight`, `color`, `text-transform`, `letter-spacing` must use `T.*` tokens defined at top of `index-template.html`. Never write these freehand.
- **Extended T tokens added**: `T.h3` (28px), `T.h4` (20px), `T.label15` / `T.label15Col()`, `T.eyebrowMd` / `T.eyebrowMdCol()`, `T.microCol()`, `T.scoreNum()`.

### Visual Patterns Established (2026-03-19)

- **dp-tile grouping**: Wrap related sections in `<div class="dp-tile">` to group them visually with light blue gradient card. Used for: Tech Stack + Traffic (Company Intel), Competitive Synthesis (Business Case). The competitive synthesis dp-tile uses `overflow:visible; margin-left:-16px; margin-right:-16px` to allow the capability matrix table to fit.
- **Capability matrix**: Must use `table-layout:fixed` with `<colgroup>` percentage widths. Never use `overflow-x:auto` wrapper — the table must fit without scrollbar.
- **Competitor tiers table**: Render ONE row per tier (not one row per competitor). Multiple competitors in a tier are joined with `, ` in the first cell. The old `comps.map()` pattern that iterated each competitor as a separate row is REMOVED — it created ghost empty rows.
- **Why Act Now section**: Uses Aceternity `.feature-grid` / `.feature-card` with `grid-template-columns:repeat(2,1fr)` — same template as Timing Signals and Hiring sections.
- **Vertical Case Studies**: Cards use `.card.card-3d` (white shadow card, no border). Links use `proofPill(url, company, result, 'green')` — NOT `'var(--blue)'` (invalid variant). Grid uses `min-width:0; box-sizing:border-box` on each card to prevent overflow.
- **Berkshire/Investor note**: Rendered via `renderBerkshire(f)` helper function (NOT inline IIFE — inline IIFEs in template literals corrupt the script). Parses `(1)...(2)...(3)...` pattern into `<ol>`. Shows source link from `f.berkshire_source`.
- **Scrolling disclaimer**: Topbar ticker uses `position:absolute` inner span inside `overflow:hidden` wrapper div. Uses `left:100%` → `left:calc(-100% - 8px)` animation (NOT translateX — translateX escapes overflow:hidden). 120s cycle: 60s scroll, 60s wait.
- **Case study section header**: Must have `color:white` on each `<th>` inline — do NOT rely on inheritance from `<tr>` as browsers don't reliably inherit into `<th>`.

---

## audit-data.json Fields Reference

### `financials` object — required fields

| Field | Type | Description |
|-------|------|-------------|
| `total_digital_revenue` | string | E-commerce/digital revenue (e.g. `"$1.105B"`). **Required** — if missing, template falls back to generic `~$540M` default |
| `berkshire_source` | string (URL) | Only for Berkshire-owned companies. Source URL confirming ownership |
| `berkshire_note` | string | Only for Berkshire-owned companies. Text with `(1)...(2)...(3)...` pattern |
| `berkshire_label` | string | Only for Berkshire-owned companies. Display label |

### `competitive_synthesis.competitor_tiers[]` structure

| Field | Type | Description |
|-------|------|-------------|
| `tier` | string | Tier key: `"AHEAD"`, `"GOLDEN"`, `"DISRUPTOR"`, or `"PARITY"` |
| `competitors` | string[] | Array of competitor names — multiple allowed, rendered as ONE row joined with `, ` |
| `search_stack` | string | Search technology string (from BuiltWith live scan) |
| `strategic_implication` | string | Strategic angle text |
| `source_url` | string (URL) | BuiltWith or verification URL |

### `competitive_synthesis.matrix_col_labels` — capability matrix competitor column names

**Critical for non-Brooks companies.** Maps generic row keys to display competitor names:

```json
"matrix_col_labels": {
  "nike_has": "REI",
  "asics_has": "Patagonia",
  "on_running_has": "The North Face",
  "new_balance_has": "Eddie Bauer"
}
```

The capability matrix template always uses `nike_has`, `asics_has`, `on_running_has`, `new_balance_has` as row keys. Use `matrix_col_labels` to display any competitor names. Brooks Running omits this (uses defaults: Nike, Asics, On Running, New Balance). Every other company MUST set this.

### `gap_pairs[]` structure — "Said vs. Found" section

**Critical** — must use these exact keys or the section renders blank:

| Key | Description |
|-----|-------------|
| `said_quote` | Verbatim executive quote |
| `said_attr` | Attribution: `"— Name, Title"` |
| `said_source_url` | Source URL |
| `said_source_label` | Source display name |
| `found_title` | What the audit found (short title) |
| `found_evidence` | Evidence text with query tested and observed result |
| `finding_id` | Links to a `findings[]` entry (e.g. `"F01"`) |
| `algolia_angle` | Algolia solution description |

### `abx_sequence.contacts[]` — who to target in outreach

**ABX contacts must NEVER include CEO.** CEOs do not evaluate or buy SaaS tools. Correct targets:
- **Tier 1 Champion** — Director/VP of Digital Commerce, eCommerce, or Digital Products. Feels the pain daily. Initiates evaluation.
- **Tier 2 Technical Buyer** — CIO or VP Engineering. Engaged *after* champion is already in conversation. Budget authority.
- **Tier 3 Co-champion** — Director of Analytics/Personalization/CX. Personalization angle.

Each contact requires: `id`, `name`, `title`, `tier`, `role`, `linkedin_url`, `angle`.

---

## Notes

- Be objective — note both strengths and weaknesses
- Focus on issues Algolia can solve
- Use the prospect's actual product names and categories in examples
- If the site already uses Algolia, focus on optimization opportunities
- Never compress Phase 1 data into single lines — each scratchpad file is a chapter of research intelligence
- Post-compaction data integrity: after any context compaction mid-audit, re-read scratchpad files before using any data point. Never regenerate from memory.

---

## MANDATORY FINAL STEP: Factcheck (Non-Negotiable)

**Every audit MUST end with `/algolia-audit-factcheck` at FULL tier before any output is shown to the user or published. No exceptions.**

This was established as a hard requirement on 2026-03-19 after multiple audits were delivered with unverified data, wrong math, and fabricated statistics. The factcheck is not optional — it is the last gate before an audit is considered complete.

### The Three-Tier Data Standard (mandatory)

Every data point in every audit must be classified by one of three tiers:

#### Tier 1 — Verified (green, normal display)
- WebFetched at a specific URL and the exact claim appears on that page
- Live MCP API call (SimilarWeb, BuiltWith, Yahoo Finance) with timestamp
- Public company filing (10-K, earnings press release) confirmed at IR URL
- Algolia customer page metric confirmed verbatim via WebFetch
- Earnings call quote confirmed verbatim via Motley Fool/Seeking Alpha transcript

#### Tier 2 — Web Search Only (red warning, keep but flag)
- Found via WebSearch but could not be WebFetched at specific URL
- Source URL exists but the exact number/quote does not appear on that page
- Paywalled source (Forrester, Gartner, Baymard) where the stat cannot be confirmed

**Implementation:** Set `"verified": false` on the JSON field. The template automatically renders:
- Source link in **red**
- ⚠ amber badge: *"Web search only — verify before using"*

#### Tier 3 — No Source (delete entirely)
- No verifiable source exists at all
- Completely unverifiable claim with no URL even to flag
- Statistics that are "e-commerce folklore" with no traceable origin

**Implementation:** Remove the data point from the JSON entirely. Do not keep it with a caveat.

### Factcheck Scoring Requirement

The `/algolia-audit-factcheck` skill produces a score out of 10. Target is 10/10 on every audit. In practice:
- **9.0+ / HIGH CONFIDENCE** — acceptable to share with AE
- **7.5–8.9 / MODERATE** — acceptable with all unverified items flagged red
- **Below 7.5** — not acceptable, must re-run factcheck and fix issues

### What Gets Flagged vs Deleted — Decision Rules

| Situation | Action |
|---|---|
| Stat confirmed verbatim at live URL | Keep — display normally |
| Stat from Forrester/Gartner/Baymard (paywalled) | Keep with `verified: false` — shows red warning |
| Exec quote confirmed verbatim at transcript URL | Keep — display normally |
| Exec quote from dead/404 URL | Keep with `verified: false` — shows red warning |
| Exec quote is a paraphrase not verbatim | Convert to paraphrase notation, not in quote marks |
| Traffic figures from SimilarWeb MCP | Keep — display normally with MCP date stamp |
| Revenue figure from public 10-K | Keep — display normally with filing URL |
| Revenue figure from private company (no filing) | Keep — label as `[ESTIMATE]` with source note |
| Statistic with no source URL at all | Delete entirely |
| Case study metric not found on Algolia customer page | Replace with what IS on the page, or remove |

### Output Files Required

The `/algolia-audit-factcheck` skill produces 3 mandatory output files:
1. `{slug}-factcheck-report.md` — 7-dimension scored report with verdict
2. `{slug}-correction-manifest.md` — every correction with file and field reference
3. `{slug}-skill-feedback.md` — methodology patterns for SKILL.md improvement

These files must be committed to GitHub alongside the corrected `{slug}-audit-data.json` and re-rendered `{slug}/index.html`.
