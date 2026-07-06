---
name: algolia-intel-traffic
description: Layer 1C traffic and engagement module. ⛔ PERMANENT HITL STEP — SimilarWeb API is GONE (no service, no key, ever). Data is captured HUMAN-IN-THE-LOOP from a logged-in SimilarWeb PRO browser session (Arijit logs in; agent extracts from Highcharts chart-data + structured DOM, sum-validated). Full profile: visits, engagement, device, channels, geography, organic/paid keywords, referrals (in+out), demographics (age+gender), competitor traffic, category. `collect-traffic.py` is DEAD (API 401) and retained for reference only. Run in Wave 1.
layer: 1-intelligence
module_id: 1C
script: collect-traffic.py
reads_from:
  - none
writes_to:
  - 03-traffic-data.md
  - 03-traffic-data.json
data_sources:
  - similarweb_api: "SimilarWeb REST API v1/v4 via collect-traffic.py — SIMILARWEB_API_KEY env var required; direct HTTPS requests (Python requests library); not an MCP; ~15 endpoints (visits, channels, v4 keywords, referrals, geo, demographics_v2, rank)"
skill_enrichment: false
version: 2.0.0
---

> # ⛔ PERMANENT HITL — NO SIMILARWEB API (read before anything)
> **SimilarWeb API access is GONE and is NOT coming back.** Algolia no longer has the service. **No API key exists or can be generated** — the old `SIMILARWEB_API_KEY` (`483b77…`) is dead (HTTP 401), permanently. Do **NOT** ask for or wait on a key. Do **NOT** silently fall back and improvise.
> - `collect-traffic.py` (deterministic API script) and the SimilarWeb MCP **CANNOT RUN** — both ride the dead key. Retained for reference only.
> - **This module is Human-In-The-Loop (HITL), by design and permanently:** Arijit logs into SimilarWeb PRO in a real browser; the agent captures the data from that logged-in session.
> - **FAIL-LOUD RULE:** when the API path is unavailable (always, now), HARD-STOP and switch to the HITL browser capture below — **never** produce a silent partial or an estimate. (Recorded 2026-07-06 after this exact failure: the module silently degraded to ad-hoc scraping and shipped an incomplete subset.)

## HITL CAPTURE METHOD (canonical — deterministic browser extraction)
Arijit logs into `pro.similarweb.com` (PRO). Then, **per domain**, drive the browser and extract from the page's own data objects — **read Highcharts `window.Highcharts.charts[].series[].data` (exact values) + structured DOM tables; never eyeball/vision-guess.** Capture the **full schema**, validate, then upsert to Postgres `audits.audit_data.traffic`.
- **Overview route:** `#/sales/account-review/overview/website-performance/{domain}/*/999/3m?webSource=Total` → visits (use **"Monthly visits"**, NOT the 3-mo "Total visits"), engagement (bounce/pages/duration/unique), device split, 10-way marketing channels, geography (top countries table), organic branded/non-branded + top keywords, paid keywords, referrers, referring industries, outgoing traffic/ads, display networks, social, competitor traffic (multi-series trend chart), category, ranks.
- **Demographics route:** `#/sales/account-review/audience-demographics/{domain}/*/999/3m?webSource=Total` → age groups + gender.
- **Guards (mandatory):** confirm the loaded page's analyzed domain == target (avoid stale reads during SPA transitions); require value stability across 2 reads; **sum-validate** (channels ≈100%, device ≈100%, social ≈100%, age ≈100%, gender ≈100%).
- **Completeness gate:** validate the assembled record against the traffic schema (every dimension present or explicitly N/A) BEFORE any DB write. Abort on any gap.
- **N/A that is real (not a miss):** `popular_pages` is not exposed in the account-review overview (separate Digital Suite view) — mark explicit N/A.
- **Reference implementation (2026-07-06 run, 18 companies):** `PIP/docs/temp/sw-capture/*` + `PIP/docs/temp/sw_upsert3.py` (assembler + completeness gate + upsert). This is the pattern to codify/reuse — not re-improvise each run.

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1 — no dependencies)
- **Module ID:** 1C
- **Model tier:** programmatic (script handles all SimilarWeb calls)
- **Writes to:** `03-traffic-data.md` + `03-traffic-data.json`

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-traffic.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/"
```

The script calls all SimilarWeb endpoints listed below. No skipping. If an endpoint returns 403 (plan limitation), it is logged as an error — do not treat as a data point. Demographics endpoints may return 403 on non-Business plans — gracefully skip and record as unavailable.

All data labeled: `[FACT — SimilarWeb API, https://www.similarweb.com/website/{domain}/, {date}]`

### Required Endpoints

**Traffic & Engagement**
- `GET /v1/website/{domain}/total-traffic-and-engagement/visits` — monthly visits (desktop + mobile combined)
- `GET /v1/website/{domain}/total-traffic-and-engagement/bounce-rate` — bounce rate
- Batch vtable `traffic_and_engagement` — visits, unique_visitors, bounce_rate, avg_visit_duration, desktop_share, mobile_share, global_rank, category_rank

**Marketing Channels**
- `GET /v1/website/{domain}/traffic-sources/overview-share` — 7-channel breakdown (Organic, Paid, Direct, Display, Email, Referrals, Social) — desktop
- `GET /v5/website/{domain}/mobile-traffic-sources/mobile-overview-share` — mobile channel breakdown
- Batch vtable `marketing_channels` — combined desktop + mobile channel visits and share

**Keywords (Search 3.0 — current)**
> Note: Search 1.0 endpoints (`/v1/website/{domain}/traffic-sources/organic-search`, `/v1/.../paid-search`, `/v1/.../branded`, `/v1/.../non-branded`) were deprecated Feb 28 2025 and MUST NOT be used. Use the unified v4 keywords endpoint below.
- `GET /v4/website-analysis/keywords?domain={domain}&traffic_source=organic&branded_type=non_branded&limit=100` — top organic non-branded keywords
- `GET /v4/website-analysis/keywords?domain={domain}&traffic_source=organic&branded_type=branded&limit=100` — branded organic keywords
- `GET /v4/website-analysis/keywords?domain={domain}&traffic_source=paid&branded_type=non_branded&limit=100` — top paid non-branded keywords
- Use `branded_type=all` for combined. Default limit=100, paginate via `offset`.

**Referrals**
- `GET /v4/website/{domain}/traffic-sources/referrals` — incoming desktop referrers (domain, traffic share, change, visits)
- `GET /v4/website/{domain}/traffic-sources/mobileweb-referrals` — incoming mobile referrers + MoM change
- `GET /v4/website/{domain}/traffic-sources/outgoing-referrals` — outgoing desktop (sites receiving traffic from domain — search abandonment signal)
- `GET /v4/website/{domain}/traffic-sources/mobileweb-outgoing-referrals` — outgoing mobile
- Batch vtable `referrals` — desktop_referral_visits, desktop_referral_share, desktop_outgoing_referral_visits, referral_change (MoM)

**Geography**
- `GET /v4/website/{domain}/geo/total-traffic-by-country` — top countries, desktop + mobile combined

**Demographics (optional — Business plan required)**
> Attempt both endpoints. If either returns 403, log as `demographics: unavailable (plan limitation)` and continue — do not abort the run.
- `GET /v4/website/{domain}/demographics_v2/age` — age group breakdown (18-24, 25-34, 35-44, 45-54, 55-64, 65+)
- `GET /v4/website/{domain}/demographics_v2/groups` — gender + age cohort with engagement metrics

**Popular Pages**
- `GET /v4/website/{domain}/popular-pages` — top pages by traffic share

### Referring Industries — NOT available via API
Referring industries (category groupings of referral sources) are NOT available via SimilarWeb API — UI only. Do not attempt to collect via API. Collect via screenshot of the SimilarWeb dashboard if available and attach to the research folder.

---

## Step 2: Gemini-Grounded Search Fallback (when sources_succeeded < 3)

If the script produces `sources_succeeded < 3` or `monthly_visits_raw = null`:

1. Check the script output for errors (403 = API plan limitation, 404 = domain not indexed)
2. Run `gemini_search.py` (WebSearch is retired here — use the grounded helper):
```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
  --system "Find traffic statistics for this website from SimilarWeb or similar sources. Return only grounded results with citation URLs." \
  'site:similarweb.com "{domain}" monthly traffic visits 2025 2026'

python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
  --system "Find monthly website visitor estimates from reputable analytics sources. Return only grounded results with citation URLs." \
  '"{CompanyName}" monthly website traffic visitors 2025 SimilarWeb Semrush'
```
3. If estimates found (and `grounded: true`): add to 03-traffic-data.md with `[ESTIMATE — <citation url from gemini_search.py>, {date}]` label; if `grounded: false`, leave field null — never use ungrounded model knowledge
4. Update `03-traffic-data.json` to include:
   - `meta.skill_enrichment_completed = true`
   - `meta.degraded_mode = true` (if SimilarWeb MCP failed)
   - `monthly_visits_raw` with estimate if found (as string like "~500K/month [ESTIMATE]")
   - `monthly_visits_source` = "gemini_search.py fallback — SimilarWeb MCP returned 0 endpoints"

**MANDATORY — Write `03-traffic-data.json` after every run (full OR degraded):**

```json
{
  "meta": {
    "skill_enrichment_completed": true,
    "domain": "{domain}",
    "collection_date": "YYYY-MM-DD",
    "sources_succeeded": 0,
    "degraded_mode": true,
    "degraded_reason": "SimilarWeb MCP: 0/14 endpoints succeeded (403/404)"
  },
  "monthly_visits_raw": "~500K/month [ESTIMATE — <citation url from gemini_search.py>, {date}]",
  "monthly_visits_source": "gemini_search.py fallback",
  "bounce_rate": null,
  "device_split": {"mobile": null, "desktop": null},
  "top_channels": []
}
```

Even if SimilarWeb returns zero data, always write this file. Never leave `03-traffic-data.json` absent. Use `meta` (not `_meta`).

---

## Verification Gate

Pass criteria:
- Both files exist and `03-traffic-data.md` ≥ 1000 bytes (lowered to allow degraded-mode output)
- `meta.skill_enrichment_completed = true` in JSON
- `source_label` or `[ESTIMATE` label present in MD
- If `sources_succeeded >= 3`: FULL PASS. If `sources_succeeded < 3`: DEGRADED PASS (acceptable — document why)

---

## Output Schema

The `03-traffic-data.json` file MUST include the following fields (null where unavailable):

```json
{
  "meta": {
    "skill_enrichment_completed": true,
    "domain": "{domain}",
    "collection_date": "YYYY-MM-DD",
    "sources_succeeded": 0,
    "degraded_mode": false,
    "degraded_reason": null
  },
  "monthly_visits_raw": null,
  "monthly_visits_source": null,
  "bounce_rate": null,
  "avg_visit_duration_seconds": null,
  "device_split": {
    "desktop": null,
    "mobile": null
  },
  "global_rank": null,
  "category_rank": null,
  "top_channels": [],
  "organic_search": {
    "share": null,
    "branded_pct": null,
    "non_branded_pct": null,
    "top_non_branded_keywords": [],
    "top_branded_keywords": []
  },
  "paid_search": {
    "share": null,
    "top_non_branded_keywords": []
  },
  "referrals": {
    "share": null,
    "top_referring_sites": [],
    "top_referring_industries": "NOT AVAILABLE VIA API — UI only. Collect via screenshot if available."
  },
  "outgoing_traffic": {
    "top_destinations": []
  },
  "geography": {
    "top_countries": []
  },
  "demographics": {
    "available": null,
    "age_groups": [],
    "gender_cohorts": []
  },
  "popular_pages": []
}
```

Note on `referrals.top_referring_industries`: Referring industries (category groupings) are NOT available via SimilarWeb API — UI only. Do not attempt to collect via API. Set this field to the string `"NOT AVAILABLE VIA API — UI only. Collect via screenshot if available."` in all cases.
