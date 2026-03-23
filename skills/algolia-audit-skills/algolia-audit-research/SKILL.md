---
name: algolia-audit-research
description: Use when kicking off an Algolia Search Audit and need to gather pre-audit intelligence on a prospect company before any browser testing. Covers company profile, tech stack, web traffic, competitor landscape, hiring signals, financial data, investor/executive quotes from earnings calls, and strategic angles. Triggers for: 'start research phase for [company]', 'prep pre-audit dossier on [company]', 'gather background intel before discovery call', 'run phase 1 on [domain]', 'build all context files before browser tests', 'kick off audit research on [site]'. Produces all research scratchpad files required before Phase 2 browser testing begins.
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

This file defines platform rules: JSON field names, CSS classes, T.* tokens, function names, naming conventions, sub-skill invocation pattern, path convention ($ALGOLIA_AUDIT_DIR). These rules apply to every action this skill takes. No exceptions.

---

## Input
$ARGUMENTS — prospect URL (e.g., `costco.com`). Optional: `--company {name}`, `--refresh {step}`, `--no-browser`

## Output
13 scratchpad files in `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

```
01-company-context.md | 02-tech-stack.md | 03-traffic-data.md | 04-competitors.md | 05-test-queries.md
06-strategic-context.md | 07-hiring-signals.md | 08-financial-profile.md | 09-browser-findings.md (placeholder)
09b-social-signals.md | 09c-news-signals.md | 10-scoring-matrix.md (placeholder)
11-investor-intelligence.md | 12-icp-priority-mapping.md | _workspace-manifest.md | CHECKPOINT.md
```

## Path
`$ALGOLIA_AUDIT_DIR` = user-configured base directory.
If not set: use current working directory. Run: `export ALGOLIA_AUDIT_DIR="$(pwd)"`

**Required folder structure:**
```
$ALGOLIA_AUDIT_DIR/{CompanyName}/
├── research/          ← scratchpads 01-12, CHECKPOINT.md
├── factcheck/
├── scripts/
└── deliverables/
    ├── index.html
    ├── screenshots/
    ├── ae-report.html
    ├── battle-card.html
    └── leave-behind.html
```

## Execution Mode
**Sequential (default — VS Code):** Execute Wave 1 steps 1-5, then Wave 2 steps 6-14 in order.
**Parallel (claudesp only):** Wave architecture in REFERENCE.md.

## MCP Servers Required
| MCP | Used in | Required? |
|-----|---------|-----------|
| BuiltWith MCP | Steps 1, 2, 6 | Yes |
| SimilarWeb MCP | Steps 2, 3, 4, 6 | Yes |
| Yahoo Finance MCP | Steps 1, 9, 12 | Public companies |
| Apify MCP | Step 8 | Yes (live signals) |
| WebSearch/WebFetch | Steps 5-8, 10-14 | Yes |

## Python Scripts (deterministic data collection)
These scripts replace manual MCP API iteration for high-volume endpoints.
The skill calls them explicitly — they always execute all required API calls.

| Script | Step | What it does |
|--------|------|-------------|
| `collect-traffic.py` | Step 3 | All 11 SimilarWeb endpoints → 03-traffic-data.md |
| `collect-techstack.py` | Step 2 | BuiltWith 660KB filtered → 02-tech-stack.md |
| `collect-competitors.py` | Step 4 | SimilarWeb similar-sites → 04-competitors.md |
| `collect-financials.py` | Step 9 | All Yahoo Finance endpoints → 08-financial-profile.md |
| `calculate-roi.py` | Step 9 | ROI formula → appended to 08-financial-profile.md |
| `calculate-score.py` | (Phase 3) | Scoring formula → verified score in 10-scoring-matrix.md |

Run scripts from: `cd "$ALGOLIA_AUDIT_DIR/{CompanyName}/research" && python3 ~/.claude/skills/algolia-search-audit/scripts/{script}.py ...`

## Step Reference (see REFERENCE.md for full detail)
| Step | Output file | Key sources |
|------|------------|-------------|
| 1: Company Context | 01-company-context.md | Yahoo Finance MCP, BuiltWith keywords, WebSearch |
| 2: Tech Stack | 02-tech-stack.md | BuiltWith MCP (all 7 endpoints), SimilarWeb tech, parse-builtwith.js |
  → Run: `python3 ~/.claude/skills/algolia-search-audit/scripts/collect-techstack.py {domain} "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/"`
  → Verify: output ≥2000 bytes. If algolia_detected=true in JSON output: STOP — existing customer, abort audit.
| 3: Traffic | 03-traffic-data.md | SimilarWeb MCP (all 11 endpoints) |
  → Run: `python3 ~/.claude/skills/algolia-search-audit/scripts/collect-traffic.py {domain} "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/"`
  → Verify: `ls -la "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/03-traffic-data.md"` — must exist and be ≥3000 bytes
| 4: Competitors | 04-competitors.md | SimilarWeb similar-sites + keywords |
  → Run: `python3 ~/.claude/skills/algolia-search-audit/scripts/collect-competitors.py {domain} "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/"`
  → Verify: output ≥1000 bytes, ≥3 competitors found
| 5: Test Queries | 05-test-queries.md | vertical-query-library + company context |
| 6: Competitor Search | 04-competitors.md (append) | BuiltWith + network inspection |
| 6b: Competitive Gap | 04-competitors.md (append) | All Wave 1 data |
| 7: Strategic Angles | 06-strategic-context.md | WebSearch |
| 8: Live Signals | 07-hiring/09b-social/09c-news | Apify (LinkedIn + Twitter + Google News) |
| 9: Financials + ROI | 08-financial-profile.md | Yahoo Finance MCP + calculations |
  → If public company: Run `python3 ~/.claude/skills/algolia-search-audit/scripts/collect-financials.py {TICKER} "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/"`
  → Then run: `python3 ~/.claude/skills/algolia-search-audit/scripts/calculate-roi.py "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/"`
  → Verify: 08-financial-profile.md ≥3000 bytes
| 10: Trigger Events | 06-strategic-context.md (append) | WebSearch |
| 11: Case Studies | 01-company-context.md (append) | WebFetch algolia.com/customers/ |
| 12: Investor Intel | 11-investor-intelligence.md | Yahoo Finance + SEC EDGAR WebFetch + transcripts |
| 13: Deep Hiring | 07-hiring-signals.md (append) | Apify + careers page WebFetch |
| 14: ICP Mapping | 12-icp-priority-mapping.md | All prior files |

## Source Recording Gate (every step)
Before marking any step DONE in CHECKPOINT.md: count source URLs in output file.
`grep -c 'https://' {file}.md` — minimum counts in REFERENCE.md.

## Full Methodology
See `~/.claude/skills/algolia-audit-research/REFERENCE.md` for:
- Complete step-by-step instructions for all 14 steps
- Wave architecture (parallel execution)
- Data collection hierarchy and source validation
- Completion gates (Gate 1.1 through Gate 1.5)
- Universal mandates (source citations, tier labels, MCP-first)
- `--refresh` step reference table
- Checkpoint file format
