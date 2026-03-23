---
name: algolia-intel-competitors
description: Layer 1D competitor intelligence module. Identifies who competes with the prospect, what search technology each uses (BuiltWith + network verification), whether any use Algolia (Golden Angle), and which Algolia case studies apply. Run in Wave 1 — depends only on company context. Produces 04-competitors.md and 04-competitors.json.
layer: 1-intelligence
module_id: 1D
script: collect-competitors.py
reads_from:
  - 01-company-context.json
  - 02-tech-stack.json
writes_to:
  - 04-competitors.md
  - 04-competitors.json
mcp_required:
  - similarweb: "similar-sites-agg, keywords-competitors-agg"
  - builtwith: "domain-lookup per competitor"
  - websearch: "competitor profiles, case studies"
skill_enrichment: true
version: 1.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1D
- **Model tier:** data_enrichment (claude-haiku-4-5)

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-competitors.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/"
```

---

## Step 2: Skill Enrichment

### For each competitor identified by script:
1. BuiltWith MCP: `domain-lookup` → detect search vendor (Layer 1 detection)
2. WebSearch: `"{competitor}" search OR "search experience" OR Algolia OR Elasticsearch 2025`
3. If any competitor uses Algolia → **GOLDEN ANGLE**: WebFetch algolia.com/customers/{slug} for exact metrics

### Case study verification:
- WebFetch: `https://www.algolia.com/customers/` — find same-vertical case studies
- Extract verbatim metric (never paraphrase): "search conversion increased 6.2% to 10%+"
- Verify URL is live: `[FACT — algolia.com/customers/{slug} WebFetch, {date}]`

### Competitive scenario classification:
- GOLDEN: ≥1 competitor uses Algolia with public proof
- DEFENSIVE: prospect uses Algolia, audit is expansion
- OFFENSIVE: competitors use inferior search, Algolia creates moat
- MIXED: combination

Update `04-competitors.json` with findings. Set `meta.skill_enrichment_completed = true` (use `meta` key, NOT `meta`).

---

## Verification Gate

Pass: Both files exist, `competitive_scenario` not null, at least 2 competitors identified.
