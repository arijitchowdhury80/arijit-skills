# PRISM Audit Pipeline — Unification & Reliability Plan

*Drafted 2026-07-09, end of the Lululemon full-re-validation session. Revised same night after
Arijit corrected 3 factual errors in the first draft — those corrections are folded in below,
not left as open questions. For execution in a fresh context per Arijit's instruction.*

## Why this plan exists

Tonight's session started as "fix Lululemon's SimilarWeb module" and became a 6+ hour forensic
audit because the underlying pipeline has no single source of truth for code, data, or output
shape. Nine-plus real bugs were found and fixed one at a time, each rediscovered by Arijit
finding the *next* broken thing live rather than by the pipeline catching it itself. That
pattern — "5 days and a hundred iterations to fix one audit" — is the actual problem this plan
solves. Individual bug fixes are not the deliverable; the deliverable is a pipeline that cannot
silently ship broken data again.

## Non-negotiable outcomes (Arijit's own words, verbatim requirements)

1. VPS code, local code, GitHub code — identical, always, no drift possible.
2. **Zero filesystem storage for audit data.** Everything in Postgres. Fetches read the DB, not `.md`/`.json` files on disk.
3. One schema shape (Pydantic) enforced across every skill's output, so the SPA always receives a consistent structure.
4. No deprecated methods anywhere: SimilarWeb API, BuiltWith, or any other retired tool — deleted from code and docs, not just flagged.
5. Tech stack = live network-packet inspection only (`detect-search`). Never an external lookup tool.
6. SimilarWeb = permanent human-in-the-loop (Arijit logs in, screenshots/live-extraction) — already policy, needs enforcement to hold under all future edits.
7. No `WebFetch` anywhere in the pipeline. Scout only.
8. Partner data = Crossbeam MCP actually connected and called every run, not silently degraded.
9. Hiring = Scout, not a Gemini-search substitute, and not silently "unavailable."
10. Solution map and business-case (dollar impact) sections fully populated on every run — no placeholders shipped.
11. Every skill runs its own factcheck/quality gate immediately after producing output — not one gate at the very end of the whole pipeline.
12. The SPA (rendered live page) itself gets a completeness check — an audit isn't "done" until the actual served page is verified, not just the data file.

## Corrections from the first draft (read this before the rest — these were wrong the first time)

- **Postgres is a real relational database, not a design decision still open.** 13 tables exist: `accounts`, `audits`, `deliverables`, `module_executions`, `algolia_case_studies`, `algolia_gaps`, `algolia_knowledge`, `algolia_proofpoints`, `algolia_quotes`, `algolia_advocates`, `algolia_customers`, `vertical_benchmarks`, `alembic_version`. The open item is not "should we build a schema" — it's "the `audits.audit_data` jsonb blob is where all module content still lands, and it should migrate to the already-existing normalized tables + typed columns instead."
- **Crossbeam MCP is authenticated and works.** Tested live tonight (`get_account_context`, `find_overlap_partners` for lululemon.com) — real data returned: an assigned Algolia owner (Erik Metke) and 60 real partner overlaps, including a CRM-confirmed commercetools customer relationship. The problem was never "needs OAuth again" — it's that **no skill run has ever actually called it**; `algolia-intel-partner` runs Gemini-grounded search and never touches the Crossbeam MCP tools at all, despite them being available. This is a wiring bug in the skill, not an auth problem.
- **Scout's local scrape endpoint is now enabled** (`SCOUT_PUBLIC_HOSTED_ONLY` flipped false, container recreated, still `127.0.0.1`-only — confirmed still internal, never public). Verified working for static/JS-rendered page loads. Not yet verified for interactive site-search (typing into a search box + submit) — lululemon's careers site search needs that, and Scout's basic `/scrape` doesn't simulate form interaction. This is the one remaining real gap on hiring, not "Scout is unavailable."

## Current state — verified facts, not guesses

| Area | Verified state |
|---|---|
| Code drift | `algolia-audit-factcheck`, `algolia-intel-traffic` — symlinked repo↔live (done tonight; also caught and fixed a live `algolia-intel-traffic/SKILL.md` stuck on v1.1, the old dead-API instructions, while doing this). `algolia-search-audit` — this is BOTH the top-level orchestrator skill (entry point for a full audit run) AND a shared script/template library every intel-* skill calls into (e.g. `algolia-intel-hiring` calls `collect-hiring.py` from its `scripts/` dir). It has genuine divergence in **both directions**: repo has 9 scripts + a `tests/` dir the live path lacks; live path has ~25 company-specific one-off `.js` scratch scripts the repo never had. Every other skill (~40) unreviewed. |
| Data storage | `research/*.md/.json` + `deliverables/*.json/.html` on VPS filesystem is the pipeline's actual working source of truth today. Postgres's normalized tables (`algolia_case_studies` etc.) and the `audits.audit_data` jsonb column are populated by one-off manual scripts (`sw_upsert3.py`) and ad-hoc edits (tonight's fixes), not by the pipeline itself on a normal run. The live SPA (`/opt/PRISM/v1/{company}/index.html`) bakes a third copy in as a static JS blob — `sync-live-page.py` (built and deployed tonight) makes this syncable on command, but is not yet wired as an automatic step. |
| Pydantic | 3 scripts total reference Pydantic anywhere in the skill suite. Effectively no schema enforcement exists. |
| `algolia_case_studies` table | Real, curated, 10 rows with structured fields (`url`, `key_results`, `features_used`, `competitor_takeout`). Gymshark is in it, pointed at `gymshark-recommend` (accurate to that page's actual content — 150% order-rate stat — but missing the 6.2%→10% conversion stat, which lives on a *different* Gymshark case study, `gymshark-headless`). **Arc'teryx is not in this table at all** — it was never a real canonical case study, which is why its citation was wrong in Lululemon's audit. A corrected INSERT for the second Gymshark row is drafted (see Action Items) but was correctly blocked from being run ad hoc via SSH — needs a real migration path. |
| Crossbeam | MCP works, tested live tonight, returns real account + partner-overlap data. `algolia-intel-partner`'s SKILL.md does not currently call any Crossbeam MCP tool — it's Gemini-search-only. This is the actual bug. |
| Scout for hiring | Skill design is correct (`algolia-intel-hiring` SKILL.md documents Scout as Layer 1). Scout's local scrape now works (fixed tonight) for standard page loads. Interactive site-search (needed to verify specific role postings on lululemon's careers site) is not yet proven to work through Scout's `/scrape` endpoint — needs investigation into whether Scout supports simulated form interaction, or whether hiring verification needs a different Scout capability. |
| Scout local API | Was disabled via `SCOUT_PUBLIC_HOSTED_ONLY=true` in `/opt/prism/scout/.env`. Flipped to `false` tonight, container recreated (plain `docker restart` does NOT reload `.env` — must be `docker compose up -d --force-recreate`), confirmed still bound to `127.0.0.1:8421` only. Working, authenticated via `X-API-Key`. |
| `module_executions` table | Has `validation_json` and `output_json` columns, currently unused/null for Lululemon's audit. This is the ready-made hook for Phase 5's per-skill factcheck gate — it doesn't need to be built from scratch, it needs to be populated. |
| WebFetch | Referenced in 14 `SKILL.md` files: `algolia-audit-factcheck`, `algolia-audit-report`, `algolia-audit-research`, `algolia-campaign-abx`, `algolia-intel-company`, `algolia-intel-competitors`, `algolia-intel-financial-private`, `algolia-intel-financial-public`, `algolia-intel-hiring`, `algolia-intel-industry`, `algolia-intel-investor`, `algolia-intel-partner`, `algolia-synth-business-case`, `scout`. |
| Deprecated APIs | SimilarWeb API and BuiltWith already removed from the live pipeline per `.mcp.json`'s own comment ("BuiltWith/Algolia/Yahoo removed from pipeline 2026-06-29"). `collect-traffic.py` (dead SimilarWeb API script) is still present in the repo "for reference" — Arijit's instruction is explicit: delete, don't retain. |
| Per-skill factcheck | Does not exist today as a running gate, but the storage hook (`module_executions.validation_json`) already exists. |
| SPA completeness check | Does not exist as a formal automated gate. Tonight's fixes were verified by manually diffing the live page's embedded JSON against canonical data, using the newly-built `sync-live-page.py` — a real tool now, not yet a required/automatic pipeline step. |

## Plan — phased, each phase independently shippable

### Phase 0 — Decisions Arijit needs to make before building (down from 4 to 2)
0.1. **Rendering model**: does the SPA fetch data live from an API-backed-by-Postgres at page-load time (true "no filesystem, no static copy"), or does a deploy step still bake a snapshot into static HTML (faster to serve, but needs the sync step automated)? `sync-live-page.py` is the answer either way it's just a question of whether it runs once at deploy-time or is replaced by a live API.
0.2. **`algolia-search-audit` script reconciliation**: for the ~25 live-only company-specific `.js` files, and each of the 8 differing scripts (`collect-financials.py`, `collect-hiring.py`, `collect-news.py`, `collect-social.py`, `collect-traffic.py`, `scout_company.py`, `audit-browser.js`, `algolia-brand.css`) — someone needs to look at each pair and decide which side is correct before any merge. Manual review, not automatable safely (confirmed tonight: repo and live each have real content the other lacks).

*(Postgres schema and Scout hosted-mode are no longer open decisions — both resolved and verified tonight, see Corrections section above.)*

### Phase 1 — Single source of truth for CODE
1.1. Resolve Phase 0.2 (manual diff review) for `algolia-search-audit`.
1.2. For every other skill not yet reviewed (~40), run the same diff-and-decide process used tonight: confirm byte-identical or reconcile, then symlink live path → repo.
1.3. Once every skill is symlinked, the repo IS the live execution path — "two copies" stops being possible by construction, not by discipline.
1.4. Add a CI check (GitHub Action on push to `main`) that fails if `~/.claude/skills` on the VPS doesn't match the repo — catches any future accidental copy-not-symlink regression.

### Phase 2 — Single source of truth for DATA (Postgres-only, no filesystem)
2.1. Migrate module content out of `audits.audit_data` jsonb into the already-existing normalized tables (`algolia_case_studies`, `algolia_quotes`, `algolia_gaps`, `algolia_proofpoints`, etc.) plus typed columns where a normalized table doesn't yet exist for a given module (traffic, tech_stack, hiring, financials).
2.2. Rewrite each intel module (`algolia-intel-traffic`, `algolia-intel-techstack`, `algolia-intel-hiring`, `algolia-intel-partner`, etc.) to write directly to Postgres instead of `research/*.md/.json`.
2.3. Rewrite `algolia-audit-report`'s deliverable generation to read from Postgres, not `research/` files.
2.4. Delete `/opt/prism-executor/audits/{company}/research/` and `deliverables/` directories once their Postgres equivalents are verified — do not leave them "for reference."
2.5. Decision 0.1 determines whether `sync-live-page.py` becomes the permanent deploy-time step or is retired in favor of a live-fetch SPA.
2.6. Fix the `algolia_case_studies` Gymshark/Arc'teryx gap via a real migration (see Action Items) as part of this phase, not as a one-off patch.

### Phase 3 — Consistent Pydantic schemas
3.1. Define one Pydantic model per module's output shape (traffic, tech_stack, hiring, partner_intel, financials, etc.) — these become the Postgres write contract from Phase 2.
3.2. Every module's script validates its own output against its model before writing to Postgres — a shape mismatch fails loudly at write time.
3.3. `algolia-audit-report` and the SPA renderer both import the same models.

### Phase 4 — Delete deprecated methods, enforce canonical methods
4.1. Delete `collect-traffic.py` entirely — not "retained for reference." Same for any other dead-API script found during Phase 1's reconciliation.
4.2. Audit and fix all 14 `SKILL.md` files referencing `WebFetch` — replace with Scout calls. Confirm Scout supports arbitrary third-party URL fetch-and-verify (SEC EDGAR, Algolia case studies, news sites) for factcheck's citation checks — if not, that's a Scout capability gap to raise separately.
4.3. **Wire Crossbeam MCP tool calls into `algolia-intel-partner`'s actual instructions** — the auth already works; the skill just needs to call `get_account_context` + `find_overlap_partners` and use the real results instead of Gemini-grounded search. This is now a scoped, concrete fix, not an infra investigation.
4.4. Investigate whether Scout can do interactive site-search (form fill + submit) for hiring verification; if not, document the real limitation rather than silently falling back to Gemini search.
4.5. Enforce (already-documented) tech-stack-is-network-only and SimilarWeb-is-HITL-only policies with the same propagation+block mechanism built tonight for the traffic module — generalize into a reusable pattern for every module with a "canonical method" policy.

### Phase 5 — Per-skill factcheck/quality gate
5.1. Populate `module_executions.validation_json` after every module run — the column already exists, just needs to be written to. Validation = the module's own Pydantic model check (Phase 3) + a no-fabrication/citation-liveness spot-check.
5.2. A module that fails its own gate blocks the pipeline right there — the orchestrator does not proceed to the next wave with a broken upstream module.
5.3. The end-of-pipeline `algolia-audit-factcheck` becomes a cross-module consistency + citation-liveness check (its proper job) rather than the only thing catching module-level bugs.

### Phase 6 — SPA completeness gate
6.1. Formalize tonight's ad hoc "diff canonical data vs. live page" check into a real, runnable gate using `sync-live-page.py` as the sync mechanism and a new completeness-check script as the gate: given a company slug, verify every section the SPA template can render has non-empty, non-placeholder data, and matches Postgres exactly.
6.2. Wire this gate to run automatically after Phase 2's rendering/sync step — an audit is not marked complete until this gate passes.
6.3. Extend to check solution-map (`icp_mapping.priority_to_product`) and business-case (`calculate-roi.py` output) completeness specifically — the two sections Arijit caught as incomplete tonight after the pipeline had already claimed "done."

### Phase 7 — Full re-validation of existing companies
7.1. Once Phases 1–6 are live, re-run every existing audited company through the new pipeline.
7.2. Any company whose old file-based data doesn't cleanly migrate to the new Postgres schema gets flagged for a fresh audit run, not a forced/lossy migration.

## Action Items (concrete, ready to execute, don't need Phase 0 decisions first)

- [ ] Run this migration to fix the case-study gap found tonight (needs a real migration path, not an ad-hoc SSH INSERT):
  ```sql
  INSERT INTO algolia_case_studies (customer_name, url, industry, sub_vertical, use_case, features_used, key_results, status)
  VALUES ('Gymshark', 'https://www.algolia.com/customers/gymshark-headless', 'Retail', 'Athletic Apparel',
  'Headless commerce migration; AI-based merchandising replacing manual process',
  '["AI Synonyms", "AI-based Merchandising", "Dynamic Re-Ranking"]',
  'Search conversion 6.2% to over 10% · revenue from search users up 400%+ YoY · search usage +20%', 'customer');
  ```
- [ ] Wire `algolia-intel-partner` to actually call Crossbeam MCP tools (Phase 4.3) — highest-leverage single fix, auth already works.
- [ ] Confirm `sync-live-page.py` (already deployed to both repo and live path tonight) gets run as part of every future audit's completion step, not just manually.

## What NOT to do (guardrails for whoever executes this)
- Do not symlink or delete anything in `algolia-search-audit`'s live-only company scripts without a human confirming they're genuinely disposable scratch work.
- Do not build Phase 3's Pydantic models by copying the CURRENT (unvalidated, sometimes-wrong) field shapes verbatim — design each model from what the data SHOULD contain, not from what happens to already exist in a given company's JSON.
- Do not run ad-hoc production database writes (INSERT/UPDATE) via direct SSH+psql outside a reviewed migration — confirmed tonight this gets (correctly) blocked, and for good reason: it's a shared table other companies' audits also read.
- Do not mark any phase "done" without the same discipline used tonight: read the actual output, run the actual gate, don't trust a skim of an exit code, and don't assume infrastructure is broken without testing it live first (Crossbeam and Scout were both wrongly assumed broken in the first draft of this plan — 10 minutes of live testing proved otherwise).
