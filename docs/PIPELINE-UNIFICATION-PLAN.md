# PRISM Audit Pipeline — Unification & Reliability Plan

*Drafted 2026-07-09, end of the Lululemon full-re-validation session. For execution in a fresh context per Arijit's instruction. Every item below is grounded in a fact checked this session or in the immediately-preceding fact-find — not assumption.*

## Why this plan exists

Tonight's session started as "fix Lululemon's SimilarWeb module" and became a 6+ hour forensic audit because the underlying pipeline has no single source of truth for code, data, or output shape. Nine real bugs were found and fixed one at a time, each rediscovered by Arijit finding the *next* broken thing live rather than by the pipeline catching it itself. That pattern — "5 days and a hundred iterations to fix one audit" — is the actual problem this plan solves. Individual bug fixes are not the deliverable; the deliverable is a pipeline that cannot silently ship broken data again.

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

## Current state — verified facts, not guesses

| Area | Verified state |
|---|---|
| Code drift | `algolia-audit-factcheck`, `algolia-intel-traffic` — now symlinked repo↔live (done tonight). `algolia-search-audit` (biggest skill) has genuine divergence in **both directions**: repo has 9 scripts + a `tests/` dir the live path lacks; live path has ~25 company-specific one-off `.js` scratch scripts the repo never had. Every other skill (~40) unreviewed — diff exists, direction unknown per-file. |
| Data storage | `research/*.md/.json` + `deliverables/*.json/.html` on VPS filesystem (`/opt/prism-executor/audits/{company}/`) is the working pipeline's actual source of truth today. Postgres (`prism` db, `audits.audit_data` jsonb column) is a **secondary, manually-upserted** copy — populated by one-off scripts like `sw_upsert3.py`, not by the pipeline itself. The live SPA (`/opt/PRISM/v1/{company}/index.html`) bakes a **third** copy in as a static JS blob, synced only by the new `sync-live-page.py` (built tonight, not yet run as a standing/automatic step). |
| Pydantic | 3 scripts total reference Pydantic anywhere in the skill suite. Effectively no schema enforcement exists. |
| Crossbeam | MCP **is** configured (`crossbeam: type=http, url=https://mcp.crossbeam.com` in `/opt/prism-executor/.mcp.json`, added 2026-07-01). It has never been authenticated — the auth-cache file has a timestamp but no working token. Per the MCP config's own comment: "this headless VPS invocation will still need a one-time interactive OAuth login... completed on this box before it actually authenticates." This is why `algolia-intel-partner` has run "Crossbeam unavailable" on every audit since the MCP was added — not a code bug, an un-completed setup step. |
| Scout for hiring | Skill design is already correct (`algolia-intel-hiring` SKILL.md documents Scout as Layer 1, Gemini-search as Layer 2 fallback). The failure is infrastructure: Scout's local `/scrape` API returns `403 Local Scout API is disabled in hosted-only mode` on this VPS deployment. Scout's own docs confirm `scout_public_hosted_only` is the toggle. This needs a Scout-side config decision, not a skill rewrite. |
| WebFetch | Referenced in 14 `SKILL.md` files: `algolia-audit-factcheck`, `algolia-audit-report`, `algolia-audit-research`, `algolia-campaign-abx`, `algolia-intel-company`, `algolia-intel-competitors`, `algolia-intel-financial-private`, `algolia-intel-financial-public`, `algolia-intel-hiring`, `algolia-intel-industry`, `algolia-intel-investor`, `algolia-intel-partner`, `algolia-synth-business-case`, `scout` (itself references WebFetch, needs checking why). |
| Deprecated APIs | SimilarWeb API and BuiltWith already removed from the live pipeline per `.mcp.json`'s own comment ("BuiltWith/Algolia/Yahoo removed from pipeline 2026-06-29"). `collect-traffic.py` (dead SimilarWeb API script) is still present in the repo "for reference" per SKILL.md — Arijit's instruction tonight was explicit: delete, don't retain "for reference." |
| Per-skill factcheck | Does not exist today. `algolia-audit-factcheck` runs once, at the end, against the fully-assembled `audit-data.json`. No individual module (`algolia-intel-traffic`, `algolia-intel-hiring`, etc.) validates its own output before handing off. |
| SPA completeness check | Does not exist as a formal gate. Tonight's fixes were verified by manually diffing the live page's embedded JSON against canonical data — ad hoc, not a repeatable check. |

## Plan — phased, each phase independently shippable

### Phase 0 — Decisions Arijit needs to make before building (blocking, needs his input)
0.1. **Postgres schema design**: is `audits.audit_data` (one big jsonb blob) the permanent shape, or should each module (traffic, tech_stack, hiring, etc.) get its own typed table/column? A single jsonb blob is easy to write but is exactly what let fields silently drift undetected all night — a normalized schema with real columns per verified field would make missing/null data visible in the schema itself, not just in application logic.
0.2. **Rendering model**: does the SPA fetch data live from an API-backed-by-Postgres at page-load time (true "no filesystem, no static copy"), or does a deploy step still bake a snapshot into static HTML (faster to serve, but reintroduces a sync step unless automated)? This determines whether `sync-live-page.py` becomes obsolete (live fetch) or becomes the permanent, automated glue (baked HTML, deploy-time sync).
0.3. **Scout hosted-only mode**: is it safe to disable `scout_public_hosted_only` on this VPS for internal pipeline use, or does that need a proper internal auth path instead of fully opening the local `/scrape` API?
0.4. **`algolia-search-audit` script reconciliation**: for the ~25 live-only company-specific `.js` files, and each of the 8 "differs" scripts (`collect-financials.py`, `collect-hiring.py`, `collect-news.py`, `collect-social.py`, `collect-traffic.py`, `scout_company.py`, `audit-browser.js`, `algolia-brand.css`) — someone needs to look at each pair and decide which side is correct before any merge. This is genuinely manual review, not automatable safely.

### Phase 1 — Single source of truth for CODE
1.1. Resolve Phase 0.4 (manual diff review) for `algolia-search-audit`.
1.2. For every other skill not yet reviewed (~40), run the same diff-and-decide process used tonight for the 2 already-fixed skills: confirm byte-identical or reconcile, then symlink live path → repo.
1.3. Once every skill is symlinked, the repo IS the live execution path — "two copies" stops being possible by construction, not by discipline.
1.4. Add a CI check (GitHub Action on push to `main`) that fails if `~/.claude/skills` on the VPS doesn't match the repo — catches any future accidental copy-not-symlink regression.

### Phase 2 — Single source of truth for DATA (Postgres-only, no filesystem)
2.1. Finalize Postgres schema per Decision 0.1.
2.2. Rewrite each intel module (`algolia-intel-traffic`, `algolia-intel-techstack`, `algolia-intel-hiring`, `algolia-intel-partner`, etc.) to write directly to Postgres instead of `research/*.md/.json`. This is the biggest engineering lift in this plan — 11+ modules to convert.
2.3. Rewrite `algolia-audit-report`'s deliverable generation to read from Postgres, not `research/` files, when assembling `audit-data.json`-equivalent output (or eliminate that intermediate JSON entirely if the SPA fetches live per Decision 0.2).
2.4. Delete `/opt/prism-executor/audits/{company}/research/` and `deliverables/` directories once their Postgres equivalents are verified — do not leave them "for reference."
2.5. If the SPA still needs a rendering step (Decision 0.2), that step reads Postgres and is the ONLY producer of the served page — `sync-live-page.py` either becomes this step or is retired.

### Phase 3 — Consistent Pydantic schemas
3.1. Define one Pydantic model per module's output shape (traffic, tech_stack, hiring, partner_intel, financials, etc.) — these become the Postgres write contract from Phase 2, not an afterthought bolted onto file output.
3.2. Every module's script validates its own output against its model before writing to Postgres — a shape mismatch fails loudly at write time, not silently three modules later.
3.3. `algolia-audit-report` and the SPA renderer both import the same models — "the SPA is picking up consistent data" becomes structurally true because there's one shape, enforced at write time, consumed by both readers.

### Phase 4 — Delete deprecated methods, enforce canonical methods
4.1. Delete `collect-traffic.py` (dead SimilarWeb API script) entirely — not "retained for reference." Same for any other dead-API script found during Phase 1's reconciliation.
4.2. Audit and fix all 14 `SKILL.md` files referencing `WebFetch` — replace with Scout calls. For citation-verification specifically (factcheck's Dim 22), confirm Scout supports arbitrary third-party URL fetch-and-verify (SEC EDGAR, Algolia case studies, news sites) — if Scout is built for company-intelligence only, this may need a Scout capability extension, not just a find-replace.
4.3. Complete the Crossbeam OAuth login (one-time human step, same pattern as SimilarWeb HITL) — then verify `algolia-intel-partner` actually returns real overlap data on a test run.
4.4. Resolve Scout hosted-only mode (Decision 0.3), then verify `algolia-intel-hiring` gets real Scout-scraped roles (not the Gemini-search fallback) on a test run.
4.5. Enforce (already-documented) tech-stack-is-network-only and SimilarWeb-is-HITL-only policies with the SAME propagation+block mechanism built tonight for the traffic module — i.e., generalize tonight's specific fix into a reusable pattern applied to every module with a "canonical method" policy.

### Phase 5 — Per-skill factcheck/quality gate
5.1. Design a lightweight per-module validation step (reuses the Pydantic models from Phase 3 — "did this module's output pass its own schema AND its own no-fabrication rules") that runs immediately after each module, not just at the end.
5.2. A module that fails its own gate blocks the pipeline right there — the orchestrator (`algolia-search-audit`) does not proceed to the next wave with a broken upstream module.
5.3. The end-of-pipeline `algolia-audit-factcheck` becomes a cross-module consistency + citation-liveness check (its proper job) rather than the only thing catching module-level bugs (its job tonight, badly).

### Phase 6 — SPA completeness gate
6.1. Formalize tonight's ad hoc "diff canonical data vs. live page" check into a real, runnable gate: given a company slug, verify every section the SPA template can render actually has non-empty, non-placeholder data for that company, and verify the live page's data matches Postgres exactly (post-Phase-2, "matches Postgres" replaces "matches the JSON file").
6.2. Wire this gate to run automatically after Phase 2's rendering step — an audit is not marked complete in the pipeline's own bookkeeping until this gate passes.
6.3. Extend to check solution-map (`icp_mapping.priority_to_product`) and business-case (`calculate-roi.py` output) completeness specifically, since those were the two sections Arijit caught as incomplete tonight after the pipeline had already claimed "done."

### Phase 7 — Full re-validation of existing companies
7.1. Once Phases 1–6 are live, re-run every existing audited company (belk, dell, jbl, nike, plus the Wave-2 batch) through the new pipeline.
7.2. Any company whose old file-based data doesn't cleanly migrate to the new Postgres schema gets flagged for a fresh audit run, not a forced/lossy migration.

## What NOT to do (guardrails for whoever executes this)
- Do not symlink or delete anything in `algolia-search-audit`'s live-only company scripts without a human confirming they're genuinely disposable scratch work.
- Do not disable Scout's `hosted_only` mode without confirming the security implication with Arijit first (Decision 0.3).
- Do not build Phase 3's Pydantic models by copying the CURRENT (unvalidated, sometimes-wrong) field shapes verbatim — design each model from what the data SHOULD contain, informed by tonight's factcheck-report.md findings, not from what happens to already exist in a given company's JSON.
- Do not mark any phase "done" without the same discipline used tonight: read the actual output, run the actual gate, don't trust a skim of an exit code.
