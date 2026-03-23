---
name: algolia-search-audit
description: Full-pipeline Algolia Sales Audit orchestrator. Use when given a prospect domain and asked to produce everything: company research, browser testing, scoring, factcheck, and all 6 sales deliverables (SPA, AE brief, battle card, leave-behind, PDF, signal brief) in a single end-to-end run. The entry point for requests like 'run an audit on X.com', 'all phases all deliverables', 'enterprise pitch prep', 'complete search intelligence before AE call', or any full audit. If only one phase is requested (research, browser, report), invoke the specific sub-skill directly instead.
---

## MANDATORY FIRST ACTION

Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

This file defines all platform rules: JSON field names, CSS classes, T.* tokens, function names, naming conventions, sub-skill invocation pattern, path convention ($ALGOLIA_AUDIT_DIR). No exceptions.

---

## What This Skill Does

Pure routing orchestrator. It spawns agents — one per module — in the correct wave order. It does NO data collection, NO analysis, NO writing. Every module runs in its own isolated Agent (separate context window) using the Skill tool internally.

This skill replaced the old monolithic `algolia-audit-research` approach. Each intelligence module is now independent, testable, and parallelizable.

---

## Path Setup

```bash
export ALGOLIA_AUDIT_DIR="/path/to/your/audit/directory"
# Example: export ALGOLIA_AUDIT_DIR="$HOME/Library/CloudStorage/.../Algolia Search Audit"
```

Workspace structure:
```
$ALGOLIA_AUDIT_DIR/{CompanyName}/
├── research/       ← all module outputs (.md + .json files)
├── deliverables/
│   ├── screenshots/
│   ├── {slug}-audit-data.json
│   └── {slug}/index.html (+ ae-report, battle-card, leave-behind, PDF)
└── audit-progress.jsonl
```

---

## Determine Public vs Private

Before spawning agents, determine if the company is publicly traded (has a stock ticker + SEC filings). This routes to `algolia-intel-financial-public` (Yahoo Finance MCP) vs `algolia-intel-financial-private` (6-source waterfall).

```bash
# Quick check: WebSearch "{CompanyName} stock ticker NYSE NASDAQ"
# Public: routes to algolia-intel-financial-public --ticker {TICKER}
# Private: routes to algolia-intel-financial-private
```

---

## WAVE 1 — Intelligence Collection (11 modules, run ALL in parallel)

Spawn all 11 agents simultaneously. Do NOT wait for one to finish before starting the next. All Wave 1 modules are independent.

**Agent template for each Wave 1 module:**
```
MANDATORY FIRST: Read ~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md

You are running [{module-name}] for {CompanyName} ({domain}).
Workspace (PRODUCTION): $ALGOLIA_AUDIT_DIR/{CompanyName}/research/

Use the Skill tool: skill="{module-name}", args="{domain}"

Progress log (run when starting and completing):
  echo '{"wave":1,"skill":"{module-name}","status":"running","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' >> "$ALGOLIA_AUDIT_DIR/{CompanyName}/audit-progress.jsonl"
  echo '{"wave":1,"skill":"{module-name}","status":"complete","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' >> "$ALGOLIA_AUDIT_DIR/{CompanyName}/audit-progress.jsonl"
```

### Wave 1 Modules (spawn all simultaneously):

| # | Skill | Args | Output file |
|---|-------|------|-------------|
| 1 | `algolia-intel-company` | `{domain}` | `01-company-context.md` + `.json` |
| 2 | `algolia-intel-techstack` | `{domain}` | `02-tech-stack.md` + `.json` |
| 3 | `algolia-intel-traffic` | `{domain}` | `03-traffic-data.md` + `.json` |
| 4 | `algolia-intel-competitors` | `{domain}` | `04-competitors.md` + `.json` |
| 5a | `algolia-intel-financial-public` | `{domain} --ticker {TICKER}` | `08-financial-profile.md` + `.json` |
| 5b | `algolia-intel-financial-private` | `{domain}` | `08-financial-profile.md` + `.json` |
| 6 | `algolia-intel-investor` | `{domain}` | `11-investor-intelligence.md` + `.json` |
| 7 | `algolia-intel-hiring` | `{domain}` | `09d-hiring-signals.md` + `.json` |
| 8 | `algolia-intel-social` | `{domain}` | `09b-social-signals.md` + `.json` |
| 9 | `algolia-intel-news` | `{domain}` | `09c-news-signals.md` + `.json` |
| 10 | `algolia-intel-partner` | `{domain}` | `07-partner-intel.md` + `.json` |
| 11 | `algolia-intel-industry` | `{domain}` | `06-industry-intel.md` + `.json` |

**Note:** Run 5a OR 5b based on public/private determination. Not both.

### Wave 1 Gate (wait for ALL 11 to complete, then verify):

```bash
ls "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/"*.md | wc -l
```

**PASS:** ≥ 11 files exist with non-trivial size (>500 bytes each)
**FAIL:** Stop. Show which files are missing. Do not proceed to Wave 2.

---

## WAVE 2 — Query Generation (1 module, runs after Wave 1)

Depends on `01-company-context.md` and `02-tech-stack.md` from Wave 1.

**Spawn agent:**
```
MANDATORY FIRST: Read ~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md

You are running [algolia-intel-queries] for {CompanyName} ({domain}).
Workspace (PRODUCTION): $ALGOLIA_AUDIT_DIR/{CompanyName}/research/

Prerequisite: 01-company-context.md and 02-tech-stack.md must exist.

Use the Skill tool: skill="algolia-intel-queries", args="{domain}"

Output: 05-test-queries.md
```

### Wave 2 Gate:

```bash
test -f "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/05-test-queries.md" && wc -c < "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/05-test-queries.md"
```

**PASS:** File exists, > 500 bytes
**FAIL:** Stop. Cannot proceed to browser audit without test queries.

---

## LAYER 2 — Browser Audit (sequential)

Runs after Wave 1 + Wave 2 complete. Reads `02-tech-stack.md` and `05-test-queries.md`.

**Spawn agent:**
```
MANDATORY FIRST: Read ~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md

You are running [algolia-audit-browser] for {CompanyName} ({domain}).
Workspace (PRODUCTION): $ALGOLIA_AUDIT_DIR/{CompanyName}/

Prerequisites:
- $ALGOLIA_AUDIT_DIR/{CompanyName}/research/05-test-queries.md (from Wave 2)
- $ALGOLIA_AUDIT_DIR/{CompanyName}/research/02-tech-stack.md (from Wave 1)

Use the Skill tool: skill="algolia-audit-browser", args="{slug}"

Screenshots go to: $ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/screenshots/
Findings go to: $ALGOLIA_AUDIT_DIR/{CompanyName}/research/09-browser-findings.md
```

### Layer 2 Gate:

```bash
ls "$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/screenshots/"*.png | wc -l
```

**PASS:** ≥ 10 screenshots
**FAIL:** Stop. Show screenshot count. Browser audit incomplete.

---

## LAYER 3 — Synthesis (sequential, each feeds the next)

### Step 3A: Business Case

**Spawn agent:**
```
MANDATORY FIRST: Read ~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md

You are running [algolia-synth-business-case] for {CompanyName} ({slug}).
Workspace (PRODUCTION): $ALGOLIA_AUDIT_DIR/{CompanyName}/

Reads from research/: 08-financial-profile.md, 04-competitors.md, 09-browser-findings.md
Output: {slug}-business-case.md in research/

Use the Skill tool: skill="algolia-synth-business-case", args="{slug}"
```

### Step 3B: Sales Plays

**Spawn agent:**
```
MANDATORY FIRST: Read ~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md

You are running [algolia-synth-sales-plays] for {CompanyName} ({slug}).
Workspace (PRODUCTION): $ALGOLIA_AUDIT_DIR/{CompanyName}/

Reads from research/: 11-investor-intelligence.md, 04-competitors.md, 09d-hiring-signals.md, 08-financial-profile.md
Reads from deliverables/: {slug}-business-case.md (if exists)
Output: deliverables/{slug}-playbook.md

Use the Skill tool: skill="algolia-synth-sales-plays", args="{slug}"
```

### Step 3C: Report + Deliverables

**Spawn agent:**
```
MANDATORY FIRST: Read ~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md

You are running [algolia-audit-report] for {CompanyName} ({slug}).
Workspace (PRODUCTION): $ALGOLIA_AUDIT_DIR/{CompanyName}/

Reads ALL research/*.md files + deliverables/screenshots/
Outputs: {slug}-audit-data.json + {slug}/index.html + ae-report + battle-card + leave-behind + PDF + ae-precall-brief.md + strategic-signal-brief.md

Use the Skill tool: skill="algolia-audit-report", args="{slug}"
```

### Layer 3 Gate:

```bash
ls "$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/{slug}-audit-data.json" \
   "$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/{slug}/index.html" 2>/dev/null | wc -l
```

**PASS:** Both files exist (count = 2)
**FAIL:** Stop.

---

## LAYER 3D — ABX Campaign (mandatory, runs after report)

**Spawn agent:**
```
MANDATORY FIRST: Read ~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md

You are running [algolia-campaign-abx] for {CompanyName} ({slug}).
Workspace (PRODUCTION): $ALGOLIA_AUDIT_DIR/{CompanyName}/

Reads: research/01-12 scratchpad files + deliverables/{slug}-audit-data.json
Outputs: deliverables/abx-campaign/ folder — 5-email sequence, LinkedIn messages, Loom script, collateral schedule.

Use the Skill tool: skill="algolia-campaign-abx", args="{slug}"
```

### Layer 3D Gate:

```bash
ls "$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables/abx-campaign/" 2>/dev/null | wc -l
```

**PASS:** ≥1 file in abx-campaign/ → proceed immediately to LAYER 4
**FAIL:** Stop and alert user: "ABX campaign failed — abx-campaign/ is empty."

---

## LAYER 4 — Factcheck (mandatory, blocks publish)

**Spawn agent:**
```
MANDATORY FIRST: Read ~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md

You are running [algolia-audit-factcheck] for {CompanyName} ({slug}).
Workspace (PRODUCTION): $ALGOLIA_AUDIT_DIR/{CompanyName}/

Use the Skill tool: skill="algolia-audit-factcheck", args="{slug}"

Output: $ALGOLIA_AUDIT_DIR/{CompanyName}/research/FACTCHECK_GATE.md
```

Read `FACTCHECK_GATE.md` and parse the ACTION field:
- **PROCEED** → stage for local review (Step 5)
- **WARN** → stage + require explicit user "publish" before pushing
- **BLOCKED** → stop, list blocking issues, wait for fixes

---

## Step 5: Local Review + Publish

```bash
# Start local server
lsof -ti tcp:8766 | xargs kill -9 2>/dev/null
cd ~/algolia-arian-v2 && python3 -m http.server 8766 &>/dev/null &

# Stage
cd "$ALGOLIA_AUDIT_DIR/{CompanyName}/deliverables"
bash ~/.claude/skills/algolia-search-audit/scripts/publish-audit.sh {slug} ~/algolia-arian-v2 --stage-only
```

Present to user:
```
═══════════════════════════════════════════════════════
  {COMPANY} AUDIT — READY FOR LOCAL REVIEW
═══════════════════════════════════════════════════════

  Factcheck:  {SCORE}/10 — {CONFIDENCE}
  Score:      {AUDIT_SCORE}/10 — {VERDICT}

  Review at: http://127.0.0.1:8766/{slug}/

  When satisfied, reply:
    "publish"   → push to GitHub (Vercel auto-deploys ~60s)
    "fix {X}"   → describe issue, I'll fix and re-stage
═══════════════════════════════════════════════════════
```

On "publish":
```bash
cd ~/algolia-arian-v2
bash ~/.claude/skills/algolia-search-audit/scripts/publish-audit.sh {slug} ~/algolia-arian-v2 --push-only
```

---

## Recovery Commands

| Phase failed | Recovery |
|---|---|
| Wave 1 module | Re-run that specific module: `Skill tool: skill="algolia-intel-{name}", args="{domain}"` |
| Wave 2 | `Skill tool: skill="algolia-intel-queries", args="{domain}"` |
| Browser | `Skill tool: skill="algolia-audit-browser", args="{slug}"` |
| Report | `Skill tool: skill="algolia-audit-report", args="{slug}"` |
| ABX Campaign | `Skill tool: skill="algolia-campaign-abx", args="{slug}"` |
| Factcheck | `Skill tool: skill="algolia-audit-factcheck", args="{slug}"` |

Check `audit-progress.jsonl` to see last completed step.

---

## Input

`{domain}` — prospect website (e.g. `dsw.com`, `costco.com`)

Optional:
- `--company {name}` — override company name
- `--ticker {TICKER}` — force public company financial route
- `--no-browser` — skip Layer 2 (research-only run)
- `--phase {layer}` — run specific layer only (research / browser / report / factcheck)
