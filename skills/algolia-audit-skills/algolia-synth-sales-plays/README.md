# algolia-synth-sales-plays

> Generate a fully personalized AE/BDR sales playbook for a specific Algolia prospect, grounded in the prospect's own executive language from earnings calls.

**Version:** 2.0.0 · **Layer/Phase:** Phase 4 — Sales Activation · **Suite:** Algolia Search Audit

## What it does

Produces a 6-section sales playbook that uses the prospect's own words — verbatim quotes from earnings calls, 10-K filings, and investor statements — to build talking points, discovery questions, objection responses, and a power map. Every section draws from completed audit research files rather than generic templates. A `check-claim-traceability.py` script mechanically verifies that each talking point traces to a real browser audit finding and a real executive quote before the skill declares completion.

## When to use

- "Build the AE playbook for [company]"
- "Run synth-sales-plays"
- "Create pre-call talking points grounded in [company]'s exec language"
- "Map MEDDPICC gaps for [company]"
- "Write SPIN-structured discovery questions"
- "Draft objection handling scripts for [company]"
- "Prepare personalized cold outreach angles for [company]"

## Inputs (upstream)

| File | Purpose |
|------|---------|
| `research/11-investor-intelligence.md` | Executive quotes to mirror — required for talking point sourcing |
| `research/10-scoring-matrix.md` | Which gaps exist — determines what to pitch |
| `research/04-competitors.md` | Golden Angle evidence + current vendor relationship |
| `research/09d-hiring-signals.md` | Buying committee (Economic Buyer, Technical Buyer, Champion) |
| `research/08-financial-profile.md` | Financial context for objection handling and MEDDPICC |
| `deliverables/{slug}-business-case.md` | ROI inputs for MEDDPICC Metrics row (read if exists) |

If a file is missing the skill notes "NOT FOUND" and proceeds with available data — sections that cannot be grounded are omitted rather than fabricated.

## Outputs

`deliverables/{slug}-playbook.md` — a single Markdown file containing:

- **BLUF header** — signal tier (HOT/WARM/COLD), top angle, key exec, partner play, most urgent trigger signal
- **Section 1: Top 5 Talking Points** — each with a browser audit finding, verbatim exec quote (Speaker + Title + Source + Date), competitor proof, and exact opening line for the AE
- **Section 2: Discovery Questions** — SPIN-structured (minimum 6: 3 Implication, 2 Need-Payoff, 1 Problem confirmation), with branching follow-ups and qualification signals
- **Section 3: MEDDPICC Gap Map** — 8-row table mapping each component to status, evidence, and AE action
- **Section 4: Objection Handling** — minimum 4 objections, each with Response + Pivot + Fallback
- **Section 5: Power Map** — name, title, deal role, relationship tier, approach strategy
- **Section 6: Partner Angles** — priority-ordered (warm intro via SI partner first, then co-sell, then cold outbound)

## Data sources

| Source | Provides | Method |
|--------|----------|--------|
| `11-investor-intelligence.md` | Verbatim executive quotes | Read upstream audit file (produced by `algolia-intel-investor` via WebFetch of earnings transcripts) |
| `10-scoring-matrix.md` | Confirmed gap areas | Read upstream audit file |
| `04-competitors.md` | Golden Angle / current vendor | Read upstream audit file (produced by detect-search + Gemini-grounded search) |
| `09d-hiring-signals.md` | Buying committee + vacancy signals | Read upstream audit file |
| `08-financial-profile.md` | Financial constraints for objections | Read upstream audit file |
| `{slug}-business-case.md` | ROI figures for MEDDPICC | Read Phase 4 Step 3A output |
| `partner-intel.md` | SI partner warm-intro routes | Read if present; falls back to `03-tech-stack.md` |

All content is grounded in existing audit files. The skill performs no external lookups of its own.

## How PRISM runs it

PRISM invokes this skill as Layer 3 / Step 3B of the orchestrated pipeline. The orchestrator (`algolia-search-audit`) spawns an Opus-class agent (creative synthesis from unstructured executive prose requires full reasoning) that reads `AGENT-CONTEXT.md` first, then calls this skill via the Skill tool with the company slug as argument. It runs after Step 3A (business case) completes. Its output (`{slug}-playbook.md`) is then consumed by `algolia-campaign-abx` (Layer 3D) for signal tier classification and talking point sourcing.

## Dependencies

| Item | Detail |
|------|--------|
| `check-claim-traceability.py` | `~/.claude/skills/algolia-search-audit/scripts/` — mechanically verifies every talking point traces to an audit finding + exec quote. Exit 0 = pass; exit 1 = lists ungrounded talking points. |
| `$ALGOLIA_AUDIT_DIR` | Must be set; fallback is `$(pwd)` with a warning |
| `AGENT-CONTEXT.md` | Read before any other step — governs platform rules and path convention |

## Notes

- A talking point without a `What we found:` (browser finding) AND a `Their words:` (verbatim exec quote) is a structural violation. The traceability checker catches this mechanically — it does not rewrite prose.
- The BLUF partner play prioritizes a warm intro via a HIGH-confidence SI partner over any cold outbound approach. If `partner-intel.md` is absent, the skill infers from `03-tech-stack.md`.
- Verification gate requires: file ≥ 6000 bytes, all 6 sections present, ≥ 3 cited exec quotes with Speaker + Title + Source + Date, complete MEDDPICC table, ≥ 4 fully handled objections, no generic placeholder language.
