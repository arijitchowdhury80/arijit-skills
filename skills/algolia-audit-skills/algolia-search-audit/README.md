# algolia-search-audit

> Full-pipeline Algolia Sales Audit orchestrator — runs the complete end-to-end pipeline from prospect domain to published audit deliverables.

**Version:** 2.0.0 · **Layer/Phase:** Orchestrator (all phases) · **Suite:** Algolia Search Audit

## What it does

This is the entry point for a complete Algolia Search Audit. It is a pure routing orchestrator: it spawns one isolated agent per module in the correct wave order, checks gates between waves, and coordinates data flow via the shared workspace on disk. It does no data collection, no analysis, and no writing itself — every module runs in its own context window, writes its output files, and exits. `AGENT-CONTEXT.md` (in this directory) governs all platform rules — JSON field names, CSS classes, path conventions, and naming — that every spawned agent must read before acting.

## When to use

- "Run an audit on [domain]"
- "All phases, all deliverables for [company]"
- "Enterprise pitch prep for [domain]"
- "Complete search intelligence before AE call"
- Any full end-to-end run

If only one phase is needed (research only, browser only, report only), invoke the specific sub-skill directly instead of this orchestrator.

## Inputs (upstream)

- A prospect domain (e.g. `dsw.com`, `costco.com`) passed as the argument
- Optional flags: `--company {name}`, `--ticker {TICKER}`, `--no-browser`, `--phase {layer}`
- `$ALGOLIA_AUDIT_DIR` must be set to the audit workspace root

No existing research files are required to start. This is the first step.

## Outputs

All outputs land under `$ALGOLIA_AUDIT_DIR/{CompanyName}/`:

```
research/              ← all module outputs (.md + .json pairs)
deliverables/
  screenshots/         ← browser audit evidence
  {slug}-audit-data.json
  {slug}/index.html    ← published SPA
  ae-report            ← AE pre-call brief
  battle-card
  leave-behind
  PDF
  {slug}-playbook.md
  {slug}-business-case.md
  abx-campaign/        ← 10-file campaign package
  FACTCHECK_GATE.md
audit-progress.jsonl   ← wave-level progress log
```

## Pipeline map

| Layer | Skills invoked | Run order | Gate |
|-------|---------------|-----------|------|
| **Wave 1** | `algolia-intel-company`, `-techstack`, `-traffic`, `-competitors`, `-financial-public` or `-financial-private`, `-investor`, `-hiring`, `-social`, `-news`, `-partner`, `-industry` | All 11 in parallel | ≥ 11 `.md` files > 500 bytes |
| **Wave 2** | `algolia-intel-queries` | After Wave 1 | `05-test-queries.md` > 500 bytes |
| **Layer 2** | `algolia-audit-browser` | After Wave 2 | ≥ 10 screenshots |
| **Layer 3A** | `algolia-synth-business-case` | Sequential | `{slug}-business-case.md` exists |
| **Layer 3B** | `algolia-synth-sales-plays` | After 3A | `{slug}-playbook.md` exists |
| **Layer 3C** | `algolia-audit-report` | After 3B | `{slug}-audit-data.json` + `{slug}/index.html` both exist |
| **Layer 3D** | `algolia-campaign-abx` | After 3C | ≥ 1 file in `abx-campaign/` |
| **Layer 4** | `algolia-audit-factcheck` | After 3D | `FACTCHECK_GATE.md` → PROCEED/WARN/BLOCKED |
| **Step 5** | Local review + `publish-audit.sh` | After Layer 4 PROCEED/WARN | User confirms "publish" |

## Data sources

This orchestrator collects no data directly. It routes to individual skills that own their own data sources. See each sub-skill's README for the sources they use.

The one direct action this orchestrator takes before spawning Wave 1 agents is running `classify-public-private.py` to determine whether to route to `algolia-intel-financial-public` (Yahoo Finance MCP) or `algolia-intel-financial-private` (6-source revenue waterfall).

## How PRISM runs it

PRISM (the Hermes instance on the VPS) invokes this skill as the top-level entry point. An operator passes a domain; PRISM calls this skill via the claude-cli executor on `/opt/prism-executor`. The orchestrator reads `AGENT-CONTEXT.md` first (platform rules), classifies the company as public or private, then fans out Wave 1 agents in parallel. All subsequent waves and layers follow in sequence. Progress is logged to `audit-progress.jsonl` so any failed module can be re-run individually using the recovery commands without restarting the full pipeline.

## Dependencies

| Item | Detail |
|------|--------|
| `AGENT-CONTEXT.md` | Must be read by every spawned agent — defines JSON field names, CSS classes, naming conventions, production write declarations |
| `classify-public-private.py` | `scripts/` — validates ticker via Yahoo Finance before routing financial module |
| `publish-audit.sh` | `scripts/` — stages and pushes audit to `algolia-arian-v2` (Vercel) |
| All `algolia-intel-*` skills | Wave 1 modules |
| All `algolia-synth-*`, `algolia-audit-*`, `algolia-campaign-abx` skills | Layers 2–4 |
| `$ALGOLIA_AUDIT_DIR` | Must be set; no fallback for the orchestrator (unlike sub-skills) |
| Yahoo Finance MCP | Used by `classify-public-private.py` for ticker validation |

## Notes

- The orchestrator uses the agent-teams architecture: workers write files, the orchestrator reads only file paths and sizes for gate checks — never the content of research files. This prevents context blowout across a full pipeline run.
- Model assignment is explicit: Haiku for pure data collection scripts (techstack, traffic, hiring, news, social), Sonnet for structured extraction and light synthesis, Opus for deep document reading and creative generation (investor intel, industry, browser audit, sales plays, ABX).
- A gate failure at any layer stops the pipeline. The `audit-progress.jsonl` log and recovery command table allow any single module to be re-run without re-running the whole audit.
- `--no-browser` skips Layer 2 and produces a research-only run. `--phase {layer}` runs a single layer.
