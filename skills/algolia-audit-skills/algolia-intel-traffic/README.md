# algolia-intel-traffic

> Collect the full traffic and engagement profile for an audit prospect via a live, logged-in SimilarWeb PRO browser session — NOT the API. The API path is permanently dead.

**Version:** 2.0.0 · **Layer/Phase:** Layer 1C / Wave 1 · **Suite:** Algolia Search Audit

## ⛔ PERMANENT HITL — NO SIMILARWEB API

SimilarWeb API access is gone and is not coming back. No key exists or can be generated — `SIMILARWEB_API_KEY` is permanently dead (HTTP 401). `collect-traffic.py` **cannot run** and must never be invoked as a primary path — it rides the dead key and is retained for reference only. Do not fall back to it, and do not silently degrade to a Gemini-search estimate as a substitute for real data.

**FAIL-LOUD RULE:** when live capture hasn't happened yet for a company, HARD-STOP the module and flag it as blocked/pending-capture. Never produce a silent partial or an [ESTIMATE]-labeled substitute and mark the module complete. (This module previously did exactly that for lululemon.com on 2026-07-01 — dead-API fallback to Gemini-search estimate, silently marked `skill_enrichment_completed: true`, and shipped as a 9.4/10 PROCEED. Root-caused and fixed 2026-07-09.)

## What it does

Arijit logs into `pro.similarweb.com` (PRO) in a real browser. The agent drives that logged-in session and extracts data directly from the page's own data objects — `window.Highcharts.charts[].series[].data` (exact values) plus structured DOM tables. Never eyeball/vision-guess values. Full profile: visits, engagement, device split, 10-way marketing channels, geography, organic/paid keywords (branded + non-branded), referrals (in + out), referring industries, outgoing traffic/ads, display networks, social referral mix, demographics (age + gender), competitor traffic, category, rankings.

**Mandatory guards:** confirm the loaded page's analyzed domain matches the target; require value stability across 2 reads; sum-validate (channels ≈100%, device ≈100%, social ≈100%, age ≈100%, gender ≈100%); run the completeness gate against the full schema before any write. Abort on any gap rather than writing a partial record.

## When to use

- Any Algolia Search Audit, Wave 1 — no upstream module dependencies; can run immediately alongside `algolia-intel-company`.
- Needed before scoring search traffic patterns, keyword intent, and channel mix in the final report.

## Inputs (upstream)

This module has no upstream file dependencies. Inputs are:
- `domain` — the prospect's primary web domain
- `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/` — output directory
- A live, logged-in SimilarWeb PRO browser session (Arijit's login)

## Outputs

Two files written to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`:

| File | Key fields |
|---|---|
| `03-traffic-data.md` | Narrative traffic summary with `[FACT — SimilarWeb PRO HITL capture, ...]` labeled data points |
| `03-traffic-data.json` | `monthly_visits_raw`, `bounce_rate_pct`, `device_split`, `rankings`, `traffic_channels`, `organic_search`, `paid_search`, `geography`, `referrals`, `outgoing_traffic`, `demographics`, `competitor_traffic`, `meta` (including `data_quality` and `degraded_mode` — MUST propagate to `deliverables/{slug}-audit-data.json` via `generate-audit-data.py`'s `lift_traffic_json`, which is the only place downstream checks can see it) |

Verification gate: both files exist; `03-traffic-data.md` ≥1000 bytes; every data point carries a `[FACT — SimilarWeb PRO HITL capture, ...]` label; `meta.degraded_mode` is `false` and `meta.data_quality` is NOT `"DEGRADED_MODE"` or `"ESTIMATE"`-flavored. If live capture has not happened for this company, the module is **BLOCKED**, not degraded-pass — do not write an estimate-based file and mark it complete.

## Data sources

| Source | Provides | Method |
|---|---|---|
| SimilarWeb PRO (logged-in HITL browser capture) | All traffic metrics | Arijit logs in; agent drives the session and extracts Highcharts data + DOM tables, sum-validated. No API, no key, no MCP. |

No-fabrication gate: there is no fallback estimate path for this module. If live capture isn't available, the module is blocked — it does not ship a substitute value.

## How PRISM runs it

PRISM invokes this skill via the claude-cli executor as part of Wave 1, running it in parallel with other independent modules (`algolia-intel-company`, `algolia-intel-techstack`). No module must complete before this one starts. The output feeds the traffic and keyword analysis sections of the audit report, and the outgoing traffic data provides search-abandonment signals used in scoring.

## Dependencies

| Item | Detail |
|---|---|
| Capture method | Live, logged-in SimilarWeb PRO browser session (HITL) — see SKILL.md for the canonical capture procedure and reference implementation |
| Env | `ALGOLIA_AUDIT_DIR` |

## Notes

- `collect-traffic.py` and the SimilarWeb REST API/MCP are permanently dead (401). Retained in the scripts directory for reference only — do not invoke, do not re-attempt, do not ask for a new key.
- Referring industries (category groupings) are captured directly from the SimilarWeb PRO dashboard as part of the standard HITL capture — no longer an API limitation to work around.
- `03-traffic-data.json`'s `meta.data_quality` / `meta.degraded_mode` must survive into `deliverables/{slug}-audit-data.json` as `traffic.data_quality` / `traffic.degraded_mode`. `factcheck_mechanical.py` BLOCKS the audit if either flag indicates degraded/estimate data — this is enforced, not advisory.
