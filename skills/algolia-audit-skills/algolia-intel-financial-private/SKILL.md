---
name: algolia-intel-financial-private
description: Layer 1F financial intelligence for PRIVATE companies. Estimates revenue using 6-source waterfall — ecdb.com, PitchBook/Crunchbase, LinkedIn headcount, trade press, Inc 5000/Deloitte Fast 500, job posting volume. All figures labeled [ESTIMATE]. Produces 08-financial-profile.md and 08-financial-profile.json. Only for private companies with no SEC filings.
layer: 1-intelligence
module_id: 1F
script: collect-financials.py
reads_from:
  - 01-company-context.json
writes_to:
  - 08-financial-profile.md
  - 08-financial-profile.json
mcp_required:
  - gemini_search: "grounded Google-Search via scripts/gemini_search.py — ecdb.com, trade press, ranking lists"
skill_enrichment: true
version: 1.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1F
- **Model tier:** data_enrichment (claude-haiku-4-5)
- **Use only for:** Private companies. For public companies (with ticker), use `algolia-intel-financial-public`.

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-financials.py \
  {TICKER_OR_PLACEHOLDER} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  --private
```

`--private` is an alias for `--company-type private` and stamps a
`<!-- company_type: private -->` marker into `08-financial-profile.md`.

**BUG-5 overwrite guard:** if `08-financial-profile.md` already exists and was written
by the PUBLIC path (1E), the script REFUSES to overwrite it and exits 2 — this stops a
public/private routing misclassification (or a stray re-run) from silently clobbering
the other path's profile. To intentionally replace a public profile, re-run with
`--force`; the script backs up the existing file to `08-financial-profile.public.bak`
first. A same-type refresh (private over private) is allowed without `--force`.

---

## Step 2: Skill Enrichment — 6-Source Waterfall (ALL sources, not fallback)

Run all 6 sources simultaneously:

1. **ecdb.com/PitchBook/Crunchbase** — WebFetch for revenue estimate
   Label: `[ESTIMATE — ecdb.com WebFetch, {date}]`

2. **LinkedIn headcount** — WebFetch linkedin.com/company/{slug}
   Label: `[ESTIMATE — LinkedIn, {date}]`

3. **CEO/founder interviews** — grounded search + WebFetch transcripts (NOT WebSearch — retired)
   ```bash
   python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
     --system "Return only facts supported by Google Search results. Cite each fact." \
     "{CompanyName} CEO founder interview transcript OR podcast"
   ```
   Use the cited URLs to WebFetch the transcripts.
   Label: `[WEBFETCH — {source}, {date}]`

4. **Trade press** — grounded search (NOT WebSearch — retired)
   ```bash
   python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
     --system "Return only facts supported by Google Search results. Cite each fact." \
     "{CompanyName} revenue OR funding site:retaildive.com OR site:wwd.com OR site:techcrunch.com"
   ```
   **Grounding rule:** only use results when `"grounded": true`. Revenue figures from this source still use `[ESTIMATE — <citation url>, <date>]` — the `[ESTIMATE]` label for all private company revenue always takes precedence. If `"grounded": false`, leave the field null.

5. **Inc 5000/Deloitte Fast 500** — grounded search (NOT WebSearch — retired)
   ```bash
   python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
     --system "Return only facts supported by Google Search results. Cite each fact." \
     "{CompanyName} Inc 5000 OR Deloitte Fast 500 ranking"
   ```
   Label: `[ESTIMATE — ranking list, {date}]`

6. **Job posting volume** — count from hiring signals as proxy
   Label: `[OBSERVED — hiring signals, {date}]`

### Deterministic reconciliation — do NOT judge the confidence tier in prose

Once you have collected the revenue figure from each of the 6 sources, **do NOT eyeball
whether "3+ sources agree within 20%."** Compute it deterministically. Build a JSON array
of the candidate estimates (one entry per source that returned a number) and run the
reconciler:

```bash
# /tmp/candidates.json = [{"source":"ecdb","value":"$1.2B"},
#                         {"source":"linkedin","value":1100000000},
#                         {"source":"trade_press","value":"$1.15 billion"}, ...]
python3 ~/.claude/skills/algolia-search-audit/scripts/reconcile_financials.py \
  /tmp/candidates.json
```

The script parses each value (unit-aware — `$1.2B`, `1.2 billion`, `$1,150,000,000` all
normalize correctly), finds the cluster of sources within ±20% of the median, and returns:
- `revenue_confidence` — **HIGH** (3+ agree within 20%), **MEDIUM** (exactly 2), **LOW** (0-1).
  Use this value verbatim; do not override it.
- `revenue_estimate_range` — `{min, median, max}`. **Report the RANGE, not a single point.**
  Never collapse the spread to one number — show min–max and use the median as the headline.
- `revenue_sources`, `sources_failed`, `agreeing_sources` — carry these into the JSON.

Confidence: HIGH = 3+ sources agree within 20% | MEDIUM = 2 sources | LOW = single mention
(now computed by `reconcile_financials.py`, not judged in prose).

All figures must use `[ESTIMATE]` label. Never use `[FACT]` for private company revenue.

### BUG-5 overwrite guard — before writing 08-financial-profile.json

Both 1E (public) and 1F (private) write `08-financial-profile.json`. They are mutually
exclusive ONLY by the orchestrator's public/private routing. If routing misclassified, or
both ran on a re-run, a private write can silently clobber a public profile. **Guard the
write:**

```bash
python3 -c "
import sys; sys.path.insert(0, '$HOME/.claude/skills/algolia-search-audit/scripts')
from reconcile_financials import assert_no_overwrite, OverwriteError
try:
    assert_no_overwrite('$OUTPUT_DIR/08-financial-profile.json', 'private')
    print('OK to write (private)')
except OverwriteError as e:
    print('BLOCKED:', e); sys.exit(1)
"
```

If this BLOCKS, the existing file is a *public* profile — re-check the orchestrator's
public/private decision before proceeding. Do not pass `force=True` unless you have
confirmed the company really is private and the existing file is the misclassification.

Write `08-financial-profile.json` with this EXACT top-level structure. **No deviations — do not nest these fields inside `meta`.**

```json
{
  "meta": {
    "skill_enrichment_completed": true,
    "company_type": "private",
    "yahoo_finance_used": false
  },
  "revenue_confidence": "HIGH|MEDIUM|LOW",
  "revenue_sources": ["ecdb", "trade_press", "linkedin_headcount"],
  "sources_succeeded": ["ecdb", "trade_press"],
  "sources_failed": [],
  "company_overview": { "...all company fields here..." },
  "financials": { "...revenue trend, margins, etc..." }
}
```

**CRITICAL:** `revenue_confidence`, `revenue_sources`, `sources_succeeded`, and `sources_failed` are **TOP-LEVEL** keys — NOT inside `meta` or any other nested object. Use `meta` (not `_meta`).

---

## Verification Gate

Pass: Both files ≥3000 bytes, revenue estimate present with [ESTIMATE] label, `revenue_confidence` at top level in JSON, `revenue_sources` array at top level (≥2 entries), `meta.skill_enrichment_completed = true`, `sources_succeeded` does NOT include `yahoo_finance`.
