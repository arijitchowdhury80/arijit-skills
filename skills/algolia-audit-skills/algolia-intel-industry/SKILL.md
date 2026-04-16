---
name: algolia-intel-industry
description: Use for any Algolia Search Audit task involving industry-level research: collecting vertical benchmarks (Baymard, Forrester, NRF), ecommerce search conversion stats, vertical trend analysis, expert analyst quotes, and competitive search landscape for a prospect's industry. Invoke when the user explicitly runs 'algolia-intel-industry', asks for 'industry intelligence' or 'industry benchmarks' for an audit company, wants bigger-picture vertical context for a sales narrative, or needs to produce industry-intel.md. Distinct from competitor intel (specific companies) and financial profile (company financials) — this skill covers the broader vertical and what's happening across the industry.
data_contract: v1.1
schema_additions: 1L (industry-intel.json)
script: collect-industry.py
updated: 2026-03-23
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Input
`$ARGUMENTS` — company slug. Resolves to: `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`

Upstream reads (graceful if missing):
- `01-company-context.json` → `vertical`, `primary_market`, `company_name`

---

## Step 1: Run `collect-industry.py`

### Invocation

```bash
cd ~/.claude/skills/algolia-search-audit/scripts

python3 collect-industry.py \
  "<domain>" \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research" \
  --company-name "{CompanyName}" \
  [--vertical "footwear-retail"]
```

Use `--vertical` flag ONLY if you want to override the value from `01-company-context.json`.
If `01-company-context.json` exists with a `vertical` field, the script reads it automatically.

### Capture stdout and route on status

```bash
RESULT=$(python3 collect-industry.py "$DOMAIN" "$OUTPUT_DIR" --company-name "$COMPANY_NAME")
STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
METHOD=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['collection_method'])")
```

**Routing:**
- `status: "success"` → proceed to Step 2 (LLM enrichment)
- `status: "partial"` → proceed to Step 2; check `skill_enrichment_required[]` for missing fields
- `status: "failed"` → `TAVILY_API_KEY` not set; go directly to Step 2b (WebSearch fallback)
- `collection_method: "websearch_fallback"` → go directly to Step 2b

### What the script writes

| Field | Source | LLM fills? |
|-------|--------|------------|
| `vertical` | upstream `01-company-context.json` or `--vertical` flag | No |
| `primary_market` | upstream `01-company-context.json` | No |
| `collection_method` | `tavily_advanced` or `websearch_fallback` | No |
| `benchmarks[]` | Tavily Query 1 (benchmark stats) | Partial — `context` if null |
| `trends_2025_2026[]` | Tavily Query 2 (trend data) | No |
| `expert_quotes[]` | Tavily Query 3 (analyst quotes) | Partial — `speaker` if null |
| `trend_headline` | Derived from top trend with stat | No |
| `trend_source_url` | First trend entry | No |
| `trend_source_label` | First trend entry | No |
| `algolia_angle` | `null` with `[COLLECT_VIA_SKILL]` | **YES — Step 2** |
| `competitor_search_landscape` | `null` with `[COLLECT_VIA_SKILL]` | **YES — Step 2** |

**Staleness rule (enforced by script):** Results where `age_months > 24` are excluded at collection time.
**Confidence rule:** `"FACT"` when Tavily returned `raw_content` (full page text); `"ESTIMATE"` when snippet-only.

---

## Step 2: SKILL LLM Enrichment

After the script runs, read both output files and perform LLM enrichment.
Do this regardless of `collection_method` — even Tavily results need contextualizing.

### 2a. Read script outputs

```
Read: $ALGOLIA_AUDIT_DIR/{CompanyName}/research/industry-intel.json
Read: $ALGOLIA_AUDIT_DIR/{CompanyName}/research/industry-intel.md
Read: $ALGOLIA_AUDIT_DIR/{CompanyName}/research/01-company-context.json  (for company context)
Read: $ALGOLIA_AUDIT_DIR/{CompanyName}/research/04-competitors.md  (for competitor search landscape, if exists)
```

### 2b. WebSearch fallback — when Tavily unavailable

When `collection_method == "websearch_fallback"` or `skill_enrichment_required` contains `"benchmarks"`:

Run these WebSearch queries (use locale from `primary_market`):

**Locale → query mapping:**

| Market | Benchmark query |
|--------|----------------|
| US | `"{vertical} ecommerce search conversion benchmark 2025" site:baymard.com OR site:nrf.com OR site:forrester.com` |
| UK | `"UK {vertical} ecommerce search benchmark 2025" site:econsultancy.com OR site:imrg.org` |
| EU | `"Europe {vertical} ecommerce search personalization benchmark 2025" site:econsultancy.com` |
| CA/AU/null | Use US queries as fallback |

**Trend queries (all locales):**
- `"{vertical} AI search personalization trends 2025 2026"`
- `"{vertical} ecommerce technology investment discovery 2025"`

**Expert quote queries (all locales):**
- `"{vertical} ecommerce search expert analyst quote 2025 site:baymard.com OR site:nrf.com"`
- `"Baymard {vertical} search user experience findings 2025"`

For any stat or quote found via WebSearch: attempt WebFetch of the source URL.
- If WebFetch succeeds and stat confirmed on page → label `[FACT — {Source} via WebFetch, {date}, {url}]`
- If WebFetch fails or stat not found on page → label `[ESTIMATE — {Source} via WebSearch, {url}]`

**Baymard fallback rule:** Baymard pages are often JS-rendered and block WebFetch.
If WebFetch returns empty or redirect: use the snippet stat, label `[ESTIMATE — Baymard Institute via WebSearch, {url}]`. Never label Baymard stats `[FACT]` unless the exact figure was confirmed on the fetched page.

### 2c. LLM enrichment tasks (always run, even after Tavily success)

**Task 1 — Fill null benchmark `context` fields:**
For each `benchmark` entry where `context` is null or generic:
Write one sentence explaining what this stat means for ecommerce search performance.
Example: `"43% of sessions that use site search convert at 3x the rate of non-searchers, making search the highest-ROI conversion lever in retail."`

**Task 2 — Write `algolia_angle`:**
Write exactly one sentence connecting the top industry trend (from `trend_headline`) to why *this specific company* needs Algolia now. Reference the company's vertical and at least one benchmark stat.

Format: `"[Company] operates in a [vertical] market where [trend/stat], making [specific Algolia capability] directly tied to [business outcome]."`

Example: `"AutoZone operates in an automotive parts market where 67% of automotive ecommerce customers abandon when search fails to match part numbers to vehicle fitment, making Algolia's AI-powered synonym and filtering capability directly tied to reducing a $340M annual cart abandonment problem."`

**Task 3 — Write `competitor_search_landscape`:**
Using `04-competitors.md` (if available) and your knowledge of the vertical:
Write 2-3 sentences on what search and discovery investments competitors in this vertical are making. What has become table stakes? What differentiates leaders?

**Task 4 — Fill null `expert_quotes[].speaker` fields:**
If a quote entry has `speaker: null`, check the source URL and content for a named analyst or author. Update if found. If still unknown, remove the entry — anonymous quotes are not permitted in deliverables.

### 2d. Update both output files with enriched content

After completing enrichment tasks 1-4, overwrite both files:

**Update `industry-intel.json`:**
- Set `algolia_angle` to the written sentence (replace null)
- Set `competitor_search_landscape` to the written paragraph
- Fill any null `context` fields in `benchmarks[]`
- Remove anonymous entries from `expert_quotes[]`
- Set `_meta.skill_enrichment_completed: true`
- Remove `"algolia_angle"` and `"competitor_search_landscape"` from `_meta.skill_enrichment_required[]`

**Update `industry-intel.md`:**
- Replace `[COLLECT_VIA_SKILL]` markers in the Algolia Vertical Positioning section
- Replace any empty/placeholder rows in tables
- Add a Vertical Overview section (2-3 sentences) above the benchmarks table

---

## Output Format

The complete `industry-intel.md` structure after Step 2 enrichment:

```markdown
# Industry Intelligence — {Company} / {Vertical}
*Generated: {date} via collect-industry.py | Vertical: {vertical} | Market: {primary_market}*
*Collection method: tavily_advanced | websearch_fallback*

## Vertical Overview
[2-3 sentences: what defines this vertical's search/discovery challenges and why they matter]
[FACT — 01-company-context.json vertical classification]

## Key Benchmarks for {Vertical}

| Metric | Value | Source | Age | Confidence | Verified |
|--------|-------|--------|-----|------------|----------|
| Site search usage rate | 43% of sessions | [Baymard Institute](https://baymard.com/blog/...) | 16mo | FACT | YES |
| Search-to-conversion lift | 3x | [Baymard Institute](https://baymard.com/blog/...) | 16mo | FACT | YES |
| Cart abandonment from failed search | 34% | [NRF](https://nrf.com/...) | 8mo | ESTIMATE | NO |

### Benchmark Source Labels
- [FACT — Baymard Institute via Tavily WebFetch, 2024-11-01, https://baymard.com/blog/...]
- [ESTIMATE — NRF via Tavily snippet, 2025-02-15, https://nrf.com/...]

## 2025-2026 Trends

1. **76% of US footwear retailers investing in personalization in 2026**
   [Description sentence from content]
   Source: [https://nrf.com/...](https://nrf.com/...) | Date: 2025-11-01 | FACT
   [FACT — NRF via Tavily WebFetch, 2025-11-01, https://nrf.com/...]

2. **AI-powered search adoption accelerating across mid-market retail**
   [Description...]
   ...

### Trend Headline (for use in deliverables)
**76% of US footwear retailers investing in personalization in 2026**
Source: https://nrf.com/...

## Expert Quotes on Search in {Vertical}

| Quote | Speaker | Organization | Source | Date | Confidence |
|-------|---------|--------------|--------|------|------------|
| "Shoppers who use site search convert at 3x the rate..." | Jamie Smith | Baymard Institute | [link](https://baymard.com/...) | 2024-11-01 | FACT |

### Expert Quote Labels
- [FACT — Baymard Institute via Tavily WebFetch, 2024-11-01, https://baymard.com/...]

## Algolia Vertical Positioning

**Algolia Angle:** {Company} operates in a {vertical} market where {trend/stat}, making
{specific Algolia capability} directly tied to {business outcome}.

**Competitor Search Landscape:** {2-3 sentences on what competitors are doing with search/discovery.
What is table stakes? What differentiates leaders?}

## Sources

- [Baymard Institute](https://baymard.com/blog/...) — Tavily advanced search
- [NRF](https://nrf.com/...) — Tavily advanced search
```

---

## Verification Gate

After Step 2 enrichment, verify all of the following before proceeding:

```bash
# 1. File existence and minimum size
test -f "$OUTPUT_DIR/industry-intel.md" && \
  test $(wc -c < "$OUTPUT_DIR/industry-intel.md") -ge 1000 && \
  echo "PASS: industry-intel.md exists >= 1000 bytes" || echo "FAIL: industry-intel.md missing or too small"

# 2. JSON validity and required fields
python3 -c "
import json, sys
with open('$OUTPUT_DIR/industry-intel.json') as f:
    d = json.load(f)
checks = {
    'benchmarks_non_empty': len(d.get('benchmarks', [])) > 0,
    'primary_market_present': d.get('primary_market') is not None,
    'algolia_angle_non_null': d.get('algolia_angle') is not None and d.get('algolia_angle') != '',
    'vertical_present': bool(d.get('vertical')),
    'meta_present': '_meta' in d,
}
for k, v in checks.items():
    print(f\"{'PASS' if v else 'FAIL'}: {k}\")
sys.exit(0 if all(checks.values()) else 1)
"
```

**Gate pass conditions:**
- `industry-intel.md` exists and >= 1000 bytes
- `benchmarks[]` non-empty (at least 1 entry)
- `primary_market` non-null
- `algolia_angle` non-null and not empty string
- `vertical` non-empty
- `_meta` present in JSON

**If gate fails:**
- Missing `benchmarks[]` → run Step 2b WebSearch fallback queries manually and populate
- `algolia_angle` still null → complete Step 2c Task 2 before proceeding
- File too small → check script errors in stdout JSON `errors[]` field

---

## Path Rules (AGENT-CONTEXT.md §7)

NEVER hardcode Google Drive paths.

```bash
# Correct
OUTPUT_DIR="$ALGOLIA_AUDIT_DIR/{CompanyName}/research"

# Fallback if ALGOLIA_AUDIT_DIR not set
if [ -z "$ALGOLIA_AUDIT_DIR" ]; then
  OUTPUT_DIR="$(pwd)/research"
  echo "WARNING: ALGOLIA_AUDIT_DIR not set — using $(pwd)/research"
fi
```

---

## Expert Quote Rules (unchanged from v1.0)

- **Named sources only**: Every quote MUST have a named speaker with title and organization. Anonymous quotes are NOT permitted — omit them entirely.
- **Verbatim if Tavily WebFetch / WebFetched**: Use quotation marks and label `[FACT]`.
- **No quotation marks on snippet-only**: Use *said that* notation and label `[ESTIMATE]`.
- **Maximum age enforced by script**: `age_months > 24` excluded at collection time.
- **Historical context exception**: Quotes 18-24 months old → place in a "Historical Context" subsection.

---

## Article Date Verification

The script enforces `age_months <= 24` at collection time. In Step 2 WebSearch fallback:

Before including any trend or benchmark, state the article date explicitly in your reasoning.
- If article date cannot be confirmed → label `[ESTIMATE]` and note "date unverified"
- Never use 2020-2022 articles as "2025 trends"
- If date confirmed and <= 24 months → include as current content
- If > 24 months → place in a "Historical Context" subsection with clear labeling
