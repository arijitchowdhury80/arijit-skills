---
name: algolia-intel-competitors
description: Layer 1D competitor intelligence module. Identifies who competes with the prospect, what search technology each uses (detect-search + network verification), whether any use Algolia (Golden Angle), and which Algolia case studies apply. Run in Wave 1 — depends only on company context. Produces 04-competitors.md and 04-competitors.json.
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
  - gemini_search: "grounded Google-Search via scripts/gemini_search.py — competitor profiles, case studies"
depends_on_skill:
  - detect-search: "canonical search-vendor oracle — per-competitor vendor verdict (primary)"
skill_enrichment: true
version: 2.0.0
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

The script attempts SimilarWeb Competitors tab via browser session. The SW Competitors tab
has CloudFront anti-bot protection — it will often return 0 results. This is expected.
The script creates the output file structure regardless.

**If script returns 0 competitors → proceed directly to Step 2. Grounded search (gemini_search.py) is the primary identification path.**

---

## Step 2: Skill Enrichment — Competitor Identification (PRIMARY PATH)

### For each competitor identified by script:
1. **Search-vendor detection — use the `detect-search` oracle, NOT LLM pattern-matching.**
   The canonical, deterministic verdict for which search vendor a competitor runs comes from
   the `detect-search` skill (Playwright packet inspection, catches proxied first-party setups),
   the same oracle techstack Layer 3 uses. Run it per competitor and map the verdict:

   ```bash
   node ~/.claude/skills/detect-search/detect-search.js "https://{competitor_domain}" \
     --type-query "shoes" > /tmp/ds_comp_{competitor_slug}.json
   python3 ~/.claude/skills/algolia-search-audit/scripts/map-detect-search.py \
     --detect /tmp/ds_comp_{competitor_slug}.json
   ```

   Record `search_vendor` + `search_vendor_status` + `search_vendor_details` (app_id/indexes) per
   competitor into `04-competitors.json`.
   If `detect-search` reports `UNCONFIRMED_WAF_BLOCK` (WAF, common on e-commerce — see Scout A/B F4),
   record the block as the finding; do NOT fall back to LLM guessing.
2. Use **grounded search** for enrichment (case studies, public statements) — NOT the vendor source of truth. Run the helper (WebSearch is retired):
   ```bash
   python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
     --system "Return only facts supported by Google Search results. Cite each fact." \
     "{competitor} search OR 'search experience' OR Algolia OR Elasticsearch 2025"
   ```
   **Grounding rule:** only label a field `[FACT — <citation url>, <date>]` when `"grounded": true` and a cited source supports it. If `"grounded": false`, leave the field null — never fall back to ungrounded model knowledge.
3. If `detect-search` confirms a competitor on Algolia → **GOLDEN ANGLE**: WebFetch algolia.com/customers/{slug} for exact metrics

### Step 2b: Algolia customer portfolio — vertical-wide lookup (MANDATORY)

This is separate from competitor scanning. Even if NO direct competitor uses Algolia, search the full Algolia customer base for companies in the same vertical.

Run the grounded search helper (NOT WebSearch — retired) for each query:
```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
  --system "Return only facts from Google Search. Cite sources." \
  "<query>"
```
- Query 1: `"algolia.com/customers {vertical}"` — e.g. `"algolia.com/customers footwear"`
- Query 2: `"algolia.com/customers {adjacent_vertical}"` — e.g. `"algolia.com/customers retail apparel"`

WebFetch: https://www.algolia.com/customers/ — scan full list for same-industry companies

For each Algolia customer in the same vertical:
- WebFetch their customer page: `https://www.algolia.com/customers/{slug}/`
- Extract verbatim metric: exact number, exact quote, exact outcome
- Note: are they a direct competitor, a non-competing peer, or an adjacent vertical?
- Label: `[FACT — algolia.com/customers/{slug} WebFetch, {date}]`

Add ALL verified Algolia customers in the vertical to `golden_angle.competitors_using_algolia[]` — not just direct competitors. The AE needs the full Algolia proof set for their vertical, not one example.

**This list must have at least 3 entries when Algolia has customers in this vertical.** If only 1 direct competitor uses Algolia, look wider: adjacent verticals, similar business models, same audience.

### Case study verification:
- Extract verbatim metric (never paraphrase): "search conversion increased 6.2% to 10%+"
- Verify URL is live: `[FACT — algolia.com/customers/{slug} WebFetch, {date}]`
- Match case study to finding type: NLP gap → find NLP case study; personalization gap → find personalization case study; federated search gap → find federated search case study

### Competitive scenario classification:
- GOLDEN: ≥1 competitor uses Algolia with public proof
- DEFENSIVE: prospect uses Algolia, audit is expansion
- OFFENSIVE: competitors use inferior search, Algolia creates moat
- MIXED: combination

Update `04-competitors.json` with findings. Set `meta.skill_enrichment_completed = true` (use `meta` key, NOT `meta`).

---

## Verification Gate

Pass: Both files exist, `competitive_scenario` not null, at least 2 competitors identified.
