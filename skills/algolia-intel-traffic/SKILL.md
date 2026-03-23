---
name: algolia-intel-traffic
description: Layer 1C traffic and engagement module. Collects full traffic profile via SimilarWeb MCP — all 11 endpoints covering visits, bounce rate, device split, traffic sources, geography, keywords, audience interests, rank, referrals, popular pages. Run in Wave 1 alongside other independent modules. Produces 03-traffic-data.md and 03-traffic-data.json.
layer: 1-intelligence
module_id: 1C
script: collect-traffic.py
reads_from:
  - none
writes_to:
  - 03-traffic-data.md
  - 03-traffic-data.json
mcp_required:
  - similarweb: "ALL 11 endpoints — no skipping"
skill_enrichment: false
version: 1.0
---

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

The script calls ALL 11 SimilarWeb endpoints. No skipping. If an endpoint returns 403 (plan limitation), it is logged as an error — do not treat as a data point.

All data labeled: `[FACT — SimilarWeb API, https://www.similarweb.com/website/{domain}/, {date}]`

---

## Step 2: WebSearch Fallback (when sources_succeeded < 3)

If the script produces `sources_succeeded < 3` or `monthly_visits_raw = null`:

1. Check the script output for errors (403 = API plan limitation, 404 = domain not indexed)
2. Run WebSearch: `site:similarweb.com "{domain}" monthly traffic visits 2025 2026`
3. Run WebSearch: `"{CompanyName}" monthly website traffic visitors 2025 SimilarWeb Semrush`
4. If estimates found: add to 03-traffic-data.md with `[ESTIMATE — WebSearch, {url}, {date}]` label
5. Update `03-traffic-data.json` to include:
   - `meta.skill_enrichment_completed = true`
   - `meta.degraded_mode = true` (if SimilarWeb MCP failed)
   - `monthly_visits_raw` with estimate if found (as string like "~500K/month [ESTIMATE]")
   - `monthly_visits_source` = "WebSearch fallback — SimilarWeb MCP returned 0 endpoints"

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
  "monthly_visits_raw": "~500K/month [ESTIMATE — WebSearch, {url}, {date}]",
  "monthly_visits_source": "WebSearch fallback",
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
