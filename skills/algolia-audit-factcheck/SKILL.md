---
name: algolia-audit-factcheck
description: Fact-check and validate Algolia Search Audit outputs across 7 dimensions. Run after /algolia-search-audit.
---

## CANONICAL PATH DEFINITIONS

```
AUDIT_DIR  = ~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit
ARIAN_DIR  = ~/algolia-arian-v2
```

**Factcheck reads from:** `$AUDIT_DIR/{CompanyName}/research/` (scratchpads)
**Factcheck writes to:** `$AUDIT_DIR/{CompanyName}/deliverables/` (3 output files)
**Factcheck workspace:** `$AUDIT_DIR/{CompanyName}/factcheck/` (6 dimension files)



# Algolia Audit Fact-Check (v1.1)

Validate every factual claim across all deliverables produced by `/algolia-search-audit`. Catches cross-file inconsistencies, math errors, stale API data, broken citations, unverifiable quotes, and scratchpad-to-deliverable drift. Produces 3 output files: a human-readable confidence report, a machine-readable correction manifest, and a methodology feedback file for continuous skill improvement.

---

## EVIDENCE TIER SYSTEM (MANDATORY — applies to every claim in every deliverable)

Every fact, stat, quote, and data point must be classified into one of three evidence tiers. The tier determines how it is labeled in deliverables and what action to take.

### Tier 1 — Data Source Verified ✅
**Definition**: Confirmed via a structured data source (MCP API, SEC filing, official company IR page, official press release at original URL).

**Accepted sources**: SimilarWeb MCP, BuiltWith MCP, Yahoo Finance MCP, SEC EDGAR, official company press release (press.{company}.com), Crunchbase API data, Bloomberg Terminal.

**Action**: Cite normally. No warning label needed.

**Example**: Traffic data from SimilarWeb MCP → cite as `[FACT — SimilarWeb MCP]`

---

### Tier 2 — Web Search / WebFetch Only ⚠️
**Definition**: Found via WebSearch or WebFetch of a third-party article/blog/database, but NOT independently confirmed through a structured data source.

**This includes**: Trade press articles (WWD, Retail Dive), analyst reports (CBInsights, Crunchbase web pages), company LinkedIn posts, third-party databases (Zippia, LeadIQ, Tracxn web pages), non-official interview transcripts.

**Action**: Keep the claim BUT display the following warning label in RED wherever it appears in deliverables:

```
🔴 ⚠️ Web search only — verify before using
```

And in the factcheck report and correction manifest, tag as:
```
[WEB-ONLY] Found in web search — not verified through a structured data source. Use at your own risk.
```

**Example**: Revenue estimate from Zippia → `🔴 ⚠️ Web search only — verify before using | $17M est. (Zippia)`

---

### Tier 3 — Cannot Be Verified ❌ → DROP
**Definition**: Cannot be confirmed via WebFetch of source URL, cannot be found via WebSearch, AND no structured data source exists for this claim. This includes: URLs that return 404/403, paywalled pages where the stat doesn't appear in the preview, quotes not found at the attributed source, stats where the source URL doesn't contain the number cited.

**Action**: **REMOVE ENTIRELY** from all deliverables. Do not replace with a weaker claim. Do not hedge. Delete it.

In the correction manifest, mark as:
```
[DROPPED] Cannot be verified by any means — removed from all deliverables.
```

**Example**: "77% of consumers prefer brands with ESG commitments" cited on a page where that number doesn't appear → DROP.

---

### Evidence Tier Summary

| Tier | Label | Action | Display |
|------|-------|--------|---------|
| **1 — Data Source** | `[FACT]` | Keep, cite source | Normal |
| **2 — Web Search Only** | `[WEB-ONLY]` | Keep with prominent red warning | `🔴 ⚠️ Web search only — verify before using` |
| **3 — Unverifiable** | `[DROPPED]` | Remove from all deliverables | Nothing (deleted) |

**The 10/10 standard**: A score of 10/10 is only achievable when ZERO Tier 3 claims remain in any deliverable, and all Tier 2 claims are explicitly flagged. An unflagged Tier 2 claim is treated as a Tier 3 violation (score penalty same as `[FAIL]`).

---

## CRITICAL: Validation Priority Order (MANDATORY)

> **External verification is 90% of this job. Cross-file consistency is 10%.**

The fact-check MUST follow this priority order — no exceptions:

1. **Validate the information itself (90% of the job)**:
   - **Follow every bibliography link** in the book, report, scratchpad, and all deliverables. WebFetch each URL. Verify the specific claim attributed to that source actually exists on that page.
   - **Re-call MCP APIs** (SimilarWeb, BuiltWith, Yahoo Finance) to independently verify traffic, tech stack, and financial data. Compare fresh API values to audit claims.
   - **Verify every quote** by fetching the source URL and confirming the exact quote text appears there.
   - **Verify every case study** link opens (not 404/hallucinated) AND is relevant to the prospect's business (e.g., a retailer audit should cite retail case studies, not media companies).
   - **Verify financials** are correct (revenue, margins, ROI math).
   - **Verify hiring claims** (job postings still exist, role titles match).
   - **Verify competitor data** independently via SimilarWeb API calls for each competitor.
   - **Check business relevance** of examples: case studies, industry stats, and benchmarks must match the prospect's vertical.

2. **Validate what made it to the deliverables (10% of the job)**:
   - Cross-file consistency: scratchpad values match deliverable values.
   - No hallucinated data that bypassed scratchpad ground truth.
   - No context compaction drift (values changed during long sessions).
   - Math/scoring arithmetic is correct.

**The default tier is now `full`**, not `quick`. Quick tier is only for rapid pre-share sanity checks — it does NOT constitute a real fact-check. A fact-check without external verification is not a fact-check.

## Input

Accept a path to an audit directory as `$ARGUMENTS` (e.g., `costco-v2/`, `therealreal-v2/`).

If no path is provided, look for `$AUDIT_DIR/{CompanyName}/research/` matching the company. Ask the user for CompanyName if ambiguous.

`$AUDIT_DIR = ~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit` If none found, ask the user.

Optionally the user may specify:
- **Tier**: `full` (default), `standard`, or `quick` — controls depth of external verification. Full is the default because external validation is the primary job.
- **Focus**: Specific dimension number(s) to run (e.g., `--dim 1,4` to run only cross-file consistency and API accuracy)

## Prerequisites

For parallel agent execution (Team Mode):
- Install `claude-sneakpeek` to unlock Agent Teams tools: `npx @realmikekelly/claude-sneakpeek quick --name claudesp`
- Run via `claudesp` (not `claude` or VS Code extension)
- Teammates inherit the lead's permissions at spawn time

## Execution Tiers

| Tier | Time | External Calls | What Runs |
|------|------|----------------|-----------|
| **Quick** | ~3-5 min | 0 | All dimensions, read-only. Catches consistency, math, reference errors. Best for fast pre-share checks. |
| **Standard** | ~10-15 min | ~15-20 | + SimilarWeb/BuiltWith re-calls for prospect + WebFetch sample source URLs + transcript verification |
| **Full** | ~25-40 min | ~30-40 + browser | + Competitor API re-calls + all source URLs verified + Chrome MCP re-tests of top 5 queries |

## Process

### Phase 0: Discovery & Workspace Setup

1. **Locate audit files** — Scan the provided directory for:
   - **Deliverables** (6 files): `{company}-search-audit.md`, `{company}-landing-page.html`, `{company}-search-audit-deck.md`, `{company}-landing-page.md`, `{company}-ae-precall-brief.md`, `{company}-strategic-signal-brief.md`
   - **Workspace** (11+ files): `$AUDIT_DIR/{CompanyName}/research/` containing `01-company-context.md` through `11-investor-intelligence.md` plus `_workspace-manifest.md`
   - **Screenshots**: `screenshots/` directory — count files present

2. **Extract company slug** — Derive from filenames (e.g., `costco` from `costco-search-audit.md`)

3. **Read workspace manifest** — `_workspace-manifest.md` shows which Phase 1 steps were completed

4. **Create factcheck workspace**:
   ```
   $AUDIT_DIR/{CompanyName}/factcheck/
   ├── claim-registry.md          ← Phase 1 output (Agent 1)
   ├── dim-1-2-3-results.md       ← Phase 1 output (Agent 1)
   ├── dim-4-api-results.md       ← Phase 2 output (Agent 2)
   ├── dim-5-6-citation-results.md ← Phase 2 output (Agent 3)
   ├── dim-7-browser-results.md   ← Phase 2 output (Agent 4)
   ├── pattern-analysis.md        ← Phase 2 output (Agent 5)
   └── _factcheck-manifest.md     ← Progress tracking
   ```

5. **File inventory** — Count and list all files found. If fewer than 6 deliverables exist, note which are missing. If workspace files are absent, flag that Quick tier can only verify deliverable-internal consistency.

### Phase 1: Claim Registry + Read-Only Dimensions (Sequential — Agent 1)

> **This phase MUST complete before Phase 2 starts.** Agent 1 builds the master claim registry that all subsequent agents reference.

Spawn **Agent 1: Claim Registry Builder** (subagent_type: `general-purpose`) with the following task:

#### Agent 1 Task: Build Claim Registry + Run Dimensions 1-3

**Step 1: Build the Master Claim Registry**

Read ALL files (deliverables + workspace) and extract every verifiable data point into a structured registry. Track each data point across every file where it appears.

**Data Points to Extract** (organized by source):

| Category | Data Points | Primary Source (scratchpad) | Check In (deliverables) |
|----------|-------------|---------------------------|------------------------|
| **Traffic** | monthly_visits, bounce_rate, pages_per_visit, avg_duration, unique_visitors | 03-traffic-data.md | report, landing page, deck, signal brief |
| **Traffic Sources** | direct_share, organic_share, paid_share, social_share, referral_share, mail_share | 03-traffic-data.md | report, landing page, deck, signal brief |
| **Demographics** | male_share, female_share, age_18_24, age_25_34, age_35_44, age_45_54, age_55_64, age_65_plus | 03-traffic-data.md | report, landing page |
| **Geography** | top_country_1 (name + share), top_country_2, top_country_3 | 03-traffic-data.md | report |
| **Company** | revenue, net_income, operating_margin, ebitda_margin, margin_zone, employee_count, store_count, founding_year, public_private | 01-company-context.md, 08-financial-profile.md | report, landing page, deck, AE brief, signal brief |
| **Executives** | exec_name, exec_title, exec_since (for each) | 01-company-context.md | report, AE brief, deck, signal brief |
| **Tech Stack** | search_provider, ecommerce_platform, cdn, analytics, personalization, recommendations, cms, payments, bot_detection | 02-tech-stack.md | report, landing page, deck |
| **Competitors** | competitor_name, competitor_search_provider, competitor_traffic, competitor_bounce, uses_algolia (for each) | 04-competitors.md | report, landing page, deck, signal brief |
| **Scoring** | overall_score, area_scores (10), severity_counts (HIGH/MEDIUM/LOW), gap_count, strength_count | 10-scoring-matrix.md | report, landing page, deck, signal brief |
| **ROI** | total_revenue, digital_share_pct, search_share_pct, improvement_pct, conservative_estimate, moderate_estimate | 08-financial-profile.md | report, AE brief, deck, signal brief |
| **Investor Quotes** | quote_text, quote_source, quote_date, quote_speaker, maps_to_product (for each) | 11-investor-intelligence.md | report, deck, signal brief |
| **Hiring** | total_relevant_roles, roles_by_category, signal_strength, build_vs_buy_risk | 07-hiring-signals.md | report, AE brief, deck, signal brief |
| **Browser Observations** | query_tested, result_count, behavior_observed, screenshot_ref (for each test step) | 09-browser-findings.md | report, landing page, deck |
| **SAIM Stats** | stat_text, stat_source (for each cited industry stat) | (reference: memory/search-audit-impact-map.md) | report, landing page, deck |
| **Trigger Events** | event_description, evidence, source_url, implication (for each) | 06-strategic-context.md | report, AE brief, deck, signal brief |

**Registry Format** — Write to `claim-registry.md`:
```markdown
# Claim Registry — {Company}

## Data Point: {name} (e.g., "monthly_visits")
| File | Value | Line/Location |
|------|-------|--------------|
| 03-traffic-data.md | 100.9M | L12 |
| costco-search-audit.md | 100.9M | L45 |
| costco-landing-page.html | 100.9M | L234 |
| costco-search-audit-deck.md | 100.9M | Slide 3 |
| costco-strategic-signal-brief.md | 100.9M | Money section |
| MEMORY.md (project) | 100.9M | Costco section |
STATUS: [CONS] — All files agree

## Data Point: {name} (e.g., "bounce_rate")
| File | Value | Line/Location |
|------|-------|--------------|
| 03-traffic-data.md | 37.2% | L14 |
| costco-search-audit.md | 31.3% | L169 |
| MEMORY.md (project) | 31.3% | Costco section |
STATUS: [DISC] — Scratchpad says 37.2%, deliverables say 31.3%
SOURCE OF TRUTH: 03-traffic-data.md (direct SimilarWeb API output)
```

**Step 2: Run Dimension 1 — Cross-File Consistency (Weight: 15%)**

For each data point in the registry:
- If ALL files agree → `[CONS]`
- If files disagree → `[DISC]` + identify the source of truth (scratchpad file = ground truth)
- If data point exists in scratchpad but is MISSING from a deliverable that should include it → `[MISS]`

**Consistency Rules**:
- Numbers must match exactly (100.9M everywhere, not 100.9M in one file and 101M in another)
- Percentages must match to 1 decimal (37.2% everywhere, not 37.2% and 37%)
- Executive names and titles must match exactly
- Competitor names and their search providers must match
- Score counts must add up (e.g., "3 HIGH, 5 MEDIUM, 2 LOW" = 10 total areas)
- Margin zone must match classification rules (Red ≤10%, Yellow 10-20%, Green >20%)

**Step 3: Run Dimension 2 — Math & Logic (Weight: 10%)**

Verify all arithmetic and logical claims:

1. **ROI Calculation**: Re-derive from components:
   ```
   Revenue Addressable = Total Revenue × Digital Share % × Search Share (15%)
   Conservative = Revenue Addressable × 5%
   Moderate = Revenue Addressable × 10%
   ```
   Compare calculated values to reported values. Flag if difference > 1%.

2. **Scoring Arithmetic**:
   - Count HIGH/MEDIUM/LOW severities in the scoring matrix → must match stated counts
   - Overall score must be consistent with individual area scores
   - Gap count + strength count should = 10 (total areas)

3. **Percentage Sums**:
   - Traffic source shares should sum to ~100% (allow ±2% for rounding)
   - Demographics age groups should sum to ~100% (allow ±2%)
   - Gender shares should sum to ~100% (allow ±1%)

4. **Margin Zone Classification**:
   - Verify EBITDA margin maps to correct zone: ≤10% = Red, 10-20% = Yellow, >20% = Green
   - Check that sales motion advice matches the zone

5. **Date Consistency**: Audit date, filing dates, data periods should be internally consistent

**Step 4: Run Dimension 3 — Reference Data (Weight: 10%)**

Read `memory/search-audit-impact-map.md` (the SAIM reference) and verify every cited industry stat:

1. **SAIM Stats**: For each "Why it matters" section in the report, verify the stat matches SAIM:
   - "39% of shoppers leave if search is slow" → must match SAIM
   - "1 in 6 queries have typos" → must match SAIM
   - "75% leave after no results" → must match SAIM
   - etc.

2. **Algolia Approved Stats**: Verify:
   - "17,000+ customers" (not 17,500 or 18,000)
   - "1.75T searches" or "1.7 trillion searches/year"
   - "30 billion records indexed"

3. **Case Study Metrics**: Cross-check any customer case study citations:
   - "Lacoste: 37% increase in search revenue" → must match reference
   - "Decathlon: 50% search conversion boost" → must match reference
   - "Herschel: 80% no-results reduction" → must match reference

4. **Product Names**: Verify Algolia product names are correct:
   - "Algolia Search", "Algolia Recommend", "Algolia NeuralSearch", "Algolia AI Search"
   - NOT: "Algolia search" (lowercase), "Algolia's Search" (possessive)

**Output**: Write combined results to `dim-1-2-3-results.md` with per-claim status tables.

---

### Phase 2: External Verification (Parallel — Agents 2-5)

> **All 4 agents run in parallel.** Each reads the claim registry from Phase 1 and performs dimension-specific verification. Agent 5 waits for Agents 2-4 to complete before generating pattern analysis.

#### Agent 2: API Data Accuracy (Dimension 4, Weight: 20%)

Spawn with `subagent_type: general-purpose`, `name: "api-verifier"`.

##### CRITICAL: Parameter Matching (MANDATORY)

**Before making ANY API re-call, you MUST first read the audit's scratchpad file (`03-traffic-data.md`) to determine:**
1. **Which data sources were used** — SimilarWeb, Semrush, Grips Intelligence, or a mix. If the scratchpad cites Semrush for a metric, you verify against Semrush (or flag as "different source" if you can only call SimilarWeb). You do NOT compare a Semrush value against a SimilarWeb re-call and call it a discrepancy.
2. **Which `web_source` parameter was used** — Look for `WEB_SOURCE:` at the top of the scratchpad. If not recorded, check the actual values: desktop-only numbers are typically higher for session duration and pages/visit. If ambiguous, re-call BOTH `web_source: "desktop"` and `web_source: "total"` and report which one matches the audit values.
3. **Which `country` parameter was used** — Look for `"us"` vs `"ww"`. Re-call with the SAME country parameter.
4. **Which time period was used** — Match the exact `start_date` and `end_date` from the scratchpad.

**The principle is absolute: you must replicate the audit's exact query before you can call something a discrepancy.** If you use different parameters, you're comparing apples to oranges, and the "discrepancy" is YOUR error, not the audit's.

**If the scratchpad mixed sources** (e.g., bounce rate from SimilarWeb but session duration from Semrush), flag that as a **methodology finding** — the audit skill mixed data sources — but do NOT mark each individual value as `[DISC]` just because it doesn't match a different source's number.

**If the scratchpad doesn't record its parameters** (no `WEB_SOURCE:` line, no explicit API parameters), flag that as a **methodology finding** — the audit skill failed to record its query parameters — and note that re-verification is ambiguous. Then re-call with BOTH `"desktop"` and `"total"` and report which one matches.

##### Verification Steps

**Quick tier**: Read-only. Cross-reference scratchpad values against claim registry. Check that API endpoint names match expected sources (e.g., traffic data should cite SimilarWeb, tech stack should cite BuiltWith). Flag any data point with no clear API source attribution. **Flag if scratchpad mixes multiple data sources for the same category** (e.g., SimilarWeb for bounce rate but Semrush for session duration).

**Standard tier** (in addition to Quick):
- Read `03-traffic-data.md` to identify exact sources and parameters used
- Re-call SimilarWeb `get-websites-traffic-and-engagement` with the SAME `web_source`, `country`, and date range as the audit
- Re-call SimilarWeb `get-websites-demographics-agg` for the prospect domain
- Re-call BuiltWith `domain-lookup` for the prospect domain
- Compare fresh values to audit values:
  - If within ±15% → `[PASS]` (normal monthly drift)
  - If drift 15-30% → `[STALE]` with drift %
  - If drift >30% → `[DISC]` — data may be wrong or significantly outdated
  - If key technology removed/added since audit → `[STALE]` with note
- **If a value came from a non-MCP source** (Semrush, Grips, etc.), WebFetch that source URL and compare. If the source is paywalled/inaccessible, mark as `[UNVF]` with note "source not accessible for re-verification", NOT as `[DISC]`.

**Full tier** (in addition to Standard):
- Re-call SimilarWeb for each competitor (traffic-and-engagement) — use the SAME `web_source` as the audit
- Re-call BuiltWith `domain-lookup` for each competitor
- Verify competitor search provider assignments still match

**Tolerance Band**: 15% for all SimilarWeb metrics. SimilarWeb data is estimated and shifts monthly — this is normal, not an error. BuiltWith tech presence is binary (present/absent) — changes here ARE significant.

**Output**: Write to `dim-4-api-results.md`.

#### Agent 3: Source Citations + Investor Quotes (Dimensions 5-6, Weight: 30%)

Spawn with `subagent_type: general-purpose`, `name: "citation-verifier"`.

**Dimension 5: Source Citation Integrity (Weight: 15%)**

**Quick tier**: Read-only.
- Scan all deliverables for hyperlinks and source attributions
- Count total citations vs. total data points → calculate citation coverage %
- Check for common citation issues:
  - "Source: web search" without URL → `[UNVF]`
  - URL present but domain doesn't match attribution (e.g., source says "10-K" but URL is a blog) → `[DISC]`
  - Data point has NO source attribution at all → `[MISS]`
- Check scratchpad files for `Source:` lines after each data point

**Standard tier** (in addition to Quick):
- WebFetch 10-15 of the most important source URLs to verify they resolve (not 404/dead)
- For each resolved URL: check that the page topic matches the claimed source context
- Verify at least 1 earnings call transcript URL, 1 company IR URL, 1 careers page URL

**Full tier** (in addition to Standard):
- WebFetch ALL source URLs found in deliverables + scratchpad
- Report link rot rate (% of URLs that are dead or redirected)

### IMPACT STAT VERIFICATION (BLOCKING — runs for every finding, all tiers)

For every finding in `audit-data.json` (and the main report) with a non-empty `impact_stat`:
1. WebFetch the `impact_stat_source` URL
2. Search the page text for the exact number or percentage stated in the `impact_stat`
3. If the URL returns 404 or cannot be fetched: mark as `[FAIL]` — **CRITICAL ISSUE — BLOCKING**
4. If the URL exists but the stat (the specific number/percentage) does NOT appear on the page: mark as `[FAIL]` — **CRITICAL ISSUE — BLOCKING**
5. If the number/percentage is confirmed present on the page: mark as `[PASS]` — CONFIRMED

This check CANNOT be skipped regardless of tier. It runs even in Quick tier (it is the one external call Quick tier always makes, because the failure mode is invisible to read-only analysis).

**Why this is BLOCKING**: Impact stats with unverified sources are the #1 hallucination vector in the audit pipeline. An AE presenting fabricated stats to a prospect destroys credibility with no recovery.

**The failure mode that caused this rule**: Claude writes `"15-20% of search volume is NLP"` and links `baymard.com/research/ecommerce-search` — but that stat never appears on that page. The URL looks credible, the stat sounds plausible. Only WebFetch verification catches it. In the audit that triggered this rule, 7 of 10 impact_stat_source URLs were 404 and the remaining 3 existed but did not contain the claimed stat.

**Remediation**: For each `[FAIL]` stat, the correction manifest must specify:
- Either: a replacement URL where the stat is verified to appear (WebFetch confirmed)
- Or: clear both fields to `""` if no verifiable source exists

**Output**: Include impact stat results in `dim-5-6-citation-results.md` under a dedicated `## Impact Stat Verification` section with a table:
```
| Finding ID | impact_stat (first 60 chars) | Source URL | HTTP Status | Stat Found on Page? | Verdict |
```

**Dimension 6: Investor Quote Verification (Weight: 15%)**

**Quick tier**: Read-only.
- Extract every quote (text in quotation marks attributed to a person) from all deliverables
- For each quote: check if it appears in `11-investor-intelligence.md`
- Traceability matrix:
  | Quote Text | In Scratchpad? | In Report? | In Deck? | In Signal Brief? | Source URL? |
  - Quote in deliverable but NOT in scratchpad → `[UNVF]` (late-added, bypassed ground truth)
  - Quote in scratchpad AND deliverable with matching text → `[CONS]`
  - Quote in scratchpad with source URL → `[PASS]` (fully traceable)
  - Quote text differs between files (e.g., misquoted, paraphrased) → `[DISC]`

**Standard tier** (in addition to Quick):
- WebFetch the source URL for each quote → search the page text for the exact quote
- If quote text found on source page → `[PASS]` (externally verified)
- If quote NOT found on source page → `[UNVF]` (URL exists but quote not confirmed)
- If source URL is dead → `[UNVF]` (cannot verify)

**Full tier** (in addition to Standard):
- WebFetch ALL earnings call transcript URLs
- Search each transcript for related quotes (may find additional quotable material)

**Output**: Write to `dim-5-6-citation-results.md`.

#### Agent 4: Browser Observation Fidelity (Dimension 7, Weight: 15%)

Spawn with `subagent_type: general-purpose`, `name: "browser-verifier"`.

**Quick tier**: Read-only.
- Read `09-browser-findings.md` and extract all query → result observations
- Cross-reference with report gap descriptions: do the queries, result counts, and behaviors match?
- Check screenshot references: do referenced screenshot files exist in `screenshots/` directory?
- Count total screenshots expected vs. present
- For each gap in the report: verify the supporting observation exists in 09-browser-findings.md
  - Observation matches report → `[CONS]`
  - Report claims something not in scratchpad → `[UNVF]`
  - Report numbers differ from scratchpad → `[DISC]`

**Standard tier** (in addition to Quick):
- Verify screenshot files exist on disk (ls the screenshots/ directory)
- Check file sizes (>0 bytes = valid, 0 bytes = corrupted)
- Count screenshots vs. expected (20 steps = ~20 screenshots expected)

**Full tier** (in addition to Standard):
- Use Chrome MCP to re-test the top 5 most impactful queries on the prospect site
- Compare current results to audit observations
- If results changed significantly → `[STALE]` with current vs. audit values
- Take new screenshots for comparison

**Output**: Write to `dim-7-browser-results.md`.

#### Agent 5: Pattern Analysis (runs AFTER Agents 2-4 complete)

Spawn with `subagent_type: general-purpose`, `name: "pattern-analyzer"`.

> **Timing**: Agent 5 starts in Phase 2 but only produces output after reading all dim results. For Quick tier, it can start immediately since Agents 2-4 are also read-only. For Standard/Full tiers, it should wait for Agents 2-4 dimension result files to be written.

**Task**: Read all dimension results (dim-1-2-3, dim-4, dim-5-6, dim-7) and the claim registry. Analyze patterns across ALL issues found to produce the skill feedback file.

**Pattern Detection Rules**:

1. **Scratchpad-to-Deliverable Drift**: If >2 data points in claim registry show `[DISC]` between scratchpad and deliverable → pattern detected. Root cause: Phase 4 report generation reads from context memory rather than re-reading scratchpad files.

2. **Source URL Coverage Gaps**: Calculate % of scratchpad data points that have `Source:` lines. If <70% → pattern detected. Identify which scratchpad files have the worst coverage.

3. **Investor Quotes Without Scratchpad Trace**: If any `[UNVF]` quotes appear in deliverables but not in `11-investor-intelligence.md` → pattern detected. Root cause: quotes added during Phase 4 from context, bypassing scratchpad.

4. **Math Errors in ROI/Scoring**: If Dimension 2 found any `[FAIL]` in arithmetic → pattern detected. Identify whether error is in formula application or in input values.

5. **SAIM Stat Misquotes**: If Dimension 3 found any `[FAIL]` in reference data → pattern detected. Track which stats are most commonly misquoted.

6. **Stale Data Prevalence**: If Dimension 4 found >3 `[STALE]` items → pattern detected. Track average drift % and stalest data category.

7. **Screenshot Coverage**: If Dimension 7 found <50% expected screenshots present → pattern detected. Root cause: session-bound IDs not persisted.

8. **Citation Asymmetry**: If source URL coverage differs significantly between scratchpad files (e.g., 02-tech-stack has 90% coverage but 01-company-context has 30%) → pattern detected. Root cause: different Phase 1 steps have different enforcement levels.

**Output**: Write to `pattern-analysis.md` using the skill feedback template (see Output 3 below).

---

### Phase 3: Score Aggregation + Output Generation

After all agents complete, the team lead (main conversation) collects all dimension results and generates the 3 output files.

#### Scoring Methodology

**Per-Dimension Score** (0-10 scale):

```
Base Score = 10 × (PASS_count + CONS_count) / total_claims

Penalties:
  FAIL  → -1.5 per occurrence
  DISC  → -1.0 per occurrence
  UNVF  → -0.5 per occurrence
  STALE → -0.25 per occurrence
  MISS  → -0.25 per occurrence

Dimension Score = max(0, Base Score + Penalties)
```

**Overall Score** = Weighted average:

| Dimension | Weight |
|-----------|--------|
| 1. Cross-File Consistency | 15% |
| 2. Math & Logic | 10% |
| 3. Reference Data | 10% |
| 4. API Data Accuracy | 20% |
| 5. Source Citation Integrity | 15% |
| 6. Investor Quote Verification | 15% |
| 7. Browser Observation Fidelity | 15% |

**Verdict**:
- **9.0+ = HIGH CONFIDENCE** — Acceptable to share with AE. Target for all audits.
- **7.5–8.9 = MODERATE** — Acceptable only if all unverified items are flagged red in the SPA (`verified: false`).
- **Below 7.5 = NOT ACCEPTABLE** — Must re-run factcheck, fix all issues, and re-score before sharing.

**Target score: 10/10 on every audit.** The factcheck skill does not stop at "good enough."

### Three-Tier Data Standard (mandatory outcome of every factcheck)

Every claim must be classified and handled as follows:

**TIER 1 — VERIFIED:** WebFetched at specific URL, exact claim confirmed on that page. OR live MCP API call with timestamp. OR public 10-K/earnings confirmed at IR URL. → Keep, display normally.

**TIER 2 — WEB SEARCH ONLY:** Found via search but cannot be WebFetched, or source URL exists but exact claim not on that page (paywalled Forrester/Gartner/Baymard counts here). → Keep in JSON with `"verified": false`. Template renders red source link + amber ⚠ "Web search only — verify before using" badge automatically.

**TIER 3 — NO SOURCE:** No URL exists at all. E-commerce folklore. Completely unverifiable. → **DELETE from JSON entirely.** Not kept with caveat, not kept with warning. Removed.

**How to apply in JSON:**
```json
// Verified — no flag needed
{"impact_stat": "37% increase in CVR", "impact_stat_source": "https://algolia.com/customers/lacoste"}

// Web search only — flag it
{"impact_stat": "15-20% conversion lift", "impact_stat_source": "https://forrester.com", "impact_stat_verified": false}

// No source — delete the field entirely, do not include
```

Same pattern applies to: `executives[].verified`, `gap_pairs[].verified`, `intelligence_signals[].verified`

#### Claim Verification Statuses

| Status | Symbol | Evidence Tier | Meaning | Severity | Action |
|--------|--------|--------------|---------|----------|--------|
| VERIFIED | `[PASS]` | Tier 1 | Confirmed correct against structured data source (MCP/API/SEC/official PR) | None | Cite normally |
| CONSISTENT | `[CONS]` | Tier 1 | Matches across all files (no external check needed — source is MCP data) | None | Cite normally |
| WEB-ONLY | `[WEB-ONLY]` | Tier 2 | Found via WebSearch/WebFetch of third-party page — NOT from structured data source | Medium | Keep with `🔴 ⚠️ Web search only — verify before using` label |
| STALE | `[STALE]` | Tier 1 | Was correct at time of audit but live data has drifted >15% | Low | Note staleness; re-verify if critical |
| DISCREPANT | `[DISC]` | — | Different values found across files (source of truth = scratchpad) | High | Correct to scratchpad value |
| DROPPED | `[DROPPED]` | Tier 3 | Cannot be verified by any means — source URL 404/paywalled/stat not on page, AND not findable via WebSearch | Critical | **REMOVE from all deliverables entirely** |
| INCORRECT | `[FAIL]` | Tier 3 | Demonstrably wrong (math error, fabricated stat, misattribution, URL doesn't contain cited stat) | Critical | **REMOVE or correct with verified replacement** |
| MISSING | `[MISS]` | — | Expected data point absent from deliverable that should include it | Medium | Add from scratchpad source of truth |

**Scoring impact (per occurrence)**:
- `[PASS]` / `[CONS]`: +0 (correct baseline)
- `[WEB-ONLY]` unflagged in deliverable: -1.5 (same as `[FAIL]` — unflagged Tier 2 = Tier 3 violation)
- `[WEB-ONLY]` properly labeled with ⚠️: -0.25 (minor, acceptable)
- `[STALE]`: -0.25
- `[DISC]`: -1.0
- `[DROPPED]` / `[FAIL]` still present in deliverable: -1.5
- `[MISS]`: -0.25

---

## Output

The fact-check produces **FOUR files** — three reports in the audit directory PLUS a structured verification data file in a `factcheck/` subdirectory.

### Output 0 (MANDATORY): `factcheck/verification-data.md`

**This file is created FIRST, before the three report files.** It persists all raw externally-verified data so the audit skill can consume it and self-correct.

**Location**: Always create a `factcheck/` subdirectory under the prospect's parent audit directory. This is the ONLY persistent artifact that crosses the boundary between fact-check skill and audit skill.

**Purpose**: When the user feeds this file to the audit skill (e.g., "here are the fact-check results, fix your deliverables"), the audit skill must:
1. Read this verification data
2. Find each discrepant claim in its own deliverables
3. Compare its value to the verified value
4. Self-correct using the verified data as ground truth

**Format**: Structured markdown with sections for each data category (traffic, tech stack, case studies, quotes, market data, dead URLs, scoring). Each section contains tables with columns: `Audit Value | Verified Value | Source`. Includes a ROOT CAUSE ANALYSIS section identifying systemic patterns (not just individual errors).

**Critical design principle**: This file provides the VERIFIED DATA, not the corrections. The audit skill must figure out WHERE in its own files the wrong data lives and HOW to fix it. We teach it to fish, not give it the fish.

The fact-check also produces THREE report files in the audit directory:

### Output 1: `{company}-factcheck-report.md`

**Write to:** `$AUDIT_DIR/{CompanyName}/deliverables/{company}-factcheck-report.md`

Human-readable scored verification report.

```markdown
# {Company} — Audit Fact-Check Report
*Generated by /algolia-audit-factcheck v1.1 on {date}*
*Tier: {Quick/Standard/Full} | Files scanned: {count} | Claims verified: {count}*

---

## 🔴 EVIDENCE TIER SUMMARY (read this first)

| Tier | Count | Status | Action |
|------|-------|--------|--------|
| ✅ Tier 1 — Data Source Verified | {N} | Confirmed via MCP/API/SEC/official PR | None — cite normally |
| 🔴 Tier 2 — Web Search Only (flagged ⚠️) | {N} | Found via WebSearch/third-party, not verified at structured source | Keep — labeled with `🔴 ⚠️ Web search only — verify before using` |
| 🔴 Tier 2 — Web Search Only (UNFLAGGED) | {N} | Same as above but WARNING LABEL MISSING in deliverable | **BLOCKING — add label before sharing** |
| ❌ Tier 3 — DROPPED (unverifiable) | {N} | Cannot be verified by any means | **REMOVED from all deliverables** |

> **10/10 requires**: Zero Tier 3 claims remaining. Zero unflagged Tier 2 claims. All Tier 2 claims labeled with `🔴 ⚠️ Web search only — verify before using`.

---

## Verification Summary

| # | Dimension | Claims | PASS | CONS | WEB-ONLY | STALE | DISC | FAIL | MISS | Score |
|---|-----------|--------|------|------|----------|-------|------|------|------|-------|
| 1 | Cross-File Consistency | {n} | {n} | {n} | — | — | {n} | — | {n} | {x}/10 |
| 2 | Math & Logic | {n} | {n} | {n} | — | — | {n} | {n} | — | {x}/10 |
| 3 | Reference Data | {n} | {n} | {n} | {n} | — | — | {n} | — | {x}/10 |
| 4 | API Data Accuracy | {n} | {n} | {n} | — | {n} | {n} | — | — | {x}/10 |
| 5 | Source Citation Integrity | {n} | {n} | {n} | {n} | — | {n} | — | {n} | {x}/10 |
| 6 | Investor Quote Verification | {n} | {n} | {n} | {n} | — | {n} | {n} | — | {x}/10 |
| 7 | Browser Observation Fidelity | {n} | {n} | {n} | — | {n} | {n} | — | — | {x}/10 |
| | **OVERALL** | **{N}** | | | | | | | | **{X}/10** |

## Verdict: {HIGH CONFIDENCE / MODERATE / LOW CONFIDENCE}

{1-2 sentence summary. E.g., "The Savage X Fenty audit scores 8.2/10 (HIGH CONFIDENCE). 3 Tier 2 web-search-only claims flagged with ⚠️ warning labels. All SAIM stats and ROI math verified. 1 unverifiable stat dropped."}

---

## Critical Issues (fix before sharing)

> These are `[FAIL]` and `[DISC]` items that represent material errors in the deliverables.

| # | Issue | Status | Data Point | Wrong Value | Correct Value | Affected Files |
|---|-------|--------|-----------|------------|---------------|---------------|
| 1 | {description} | [DISC] | bounce_rate | 31.3% | 37.2% | report L169, MEMORY.md |
| 2 | {description} | [FAIL] | roi_conservative | $150M | $148M | landing-page.html L456 |

## 🔴 Tier 3 DROPPED Claims (removed from deliverables)

> These claims were present in deliverables but could not be verified by any means. They have been removed.

| # | Claim | Was In | Reason Dropped |
|---|-------|--------|----------------|
| 1 | "{exact claim text}" | {file} L{n} | {URL 404 / stat not on cited page / not found in any search} |

## ⚠️ Tier 2 Web-Search-Only Claims (flagged — labeled in deliverables)

> These claims are kept but labeled with `🔴 ⚠️ Web search only — verify before using`. Use at your own risk.

| # | Claim | Found In | Label Applied? |
|---|-------|----------|----------------|
| 1 | "{claim text}" | {file} L{n} | ✅ Yes — `🔴 ⚠️ Web search only — verify before using` |

## Warnings (review before sharing)

> These are `[STALE]`, `[WEB-ONLY]` unflagged, and `[MISS]` items that may need action.

| # | Issue | Status | Details | Recommendation |
|---|-------|--------|---------|---------------|
| 1 | {description} | [WEB-ONLY] unflagged | Claim present without ⚠️ label | Add `🔴 ⚠️ Web search only — verify before using` label |
| 2 | {description} | [STALE] | Traffic drifted +12% | Note: normal monthly shift, low risk |
| 3 | {description} | [MISS] | investor_quote_3 not in deck | Add from scratchpad or remove from report |

---

## Dimension 1: Cross-File Consistency

{Per data-point table from claim registry showing values across all files, with status}

## Dimension 2: Math & Logic

### ROI Recalculation
| Component | Reported | Recalculated | Match? |
|-----------|----------|-------------|--------|
| Total Revenue | ${X} | — | (input) |
| Digital Share | {X}% | — | (input) |
| Search Share | 15% | — | (benchmark) |
| Revenue Addressable | ${X} | ${calc} | {yes/no} |
| Conservative (5%) | ${X} | ${calc} | {yes/no} |
| Moderate (10%) | ${X} | ${calc} | {yes/no} |

### Scoring Arithmetic
| Check | Expected | Actual | Match? |
|-------|----------|--------|--------|
| HIGH count | {n} | {n} | {yes/no} |
| MEDIUM count | {n} | {n} | {yes/no} |
| LOW count | {n} | {n} | {yes/no} |
| Total areas | 10 | {n} | {yes/no} |
| Overall score | {x}/10 | {recalc} | {yes/no} |

### Percentage Sums
| Category | Sum | Expected | Within tolerance? |
|----------|-----|----------|-------------------|
| Traffic sources | {x}% | ~100% | {yes/no} |
| Age demographics | {x}% | ~100% | {yes/no} |
| Gender split | {x}% | ~100% | {yes/no} |

## Dimension 3: Reference Data

### SAIM Stat Verification
| Cited Stat | In SAIM? | SAIM Value | Match? | Status |
|-----------|----------|-----------|--------|--------|
| "{stat text}" | Yes/No | {value} | Exact/Close/Wrong | [PASS]/[FAIL] |

### Algolia Approved Stats
| Stat | Used Value | Approved Value | Match? |
|------|-----------|---------------|--------|
| Customer count | {value} | 17,000+ | {yes/no} |
| Searches/year | {value} | 1.75T | {yes/no} |

### Case Study Citations
| Customer | Cited Metric | Reference Metric | Match? |
|----------|-------------|-----------------|--------|
| Lacoste | {value} | 37% search revenue increase | {yes/no} |

## Dimension 4: API Data Accuracy
*(Standard/Full tier only — shows current vs. audit values)*

| Data Point | Audit Value | Current Value | Drift % | Status |
|-----------|------------|---------------|---------|--------|
| monthly_visits | {audit} | {current} | {x}% | [PASS]/[STALE] |
| bounce_rate | {audit} | {current} | {x}% | [PASS]/[STALE] |

## Dimension 5: Source Citation Integrity

### Citation Coverage
| File | Data Points | With Source URL | Coverage % |
|------|------------|----------------|-----------|
| 01-company-context.md | {n} | {n} | {x}% |
| 02-tech-stack.md | {n} | {n} | {x}% |
| ... | | | |
| **Overall** | **{N}** | **{n}** | **{x}%** |

### URL Verification Results
*(Standard/Full tier only)*

| URL | Status | Expected Content | Actual | Match? |
|-----|--------|-----------------|--------|--------|
| {url} | 200 OK / 404 / redirect | {what it should be} | {what it is} | {yes/no} |

## Dimension 6: Investor Quote Verification

### Quote Traceability Matrix
| # | Quote (first 50 chars) | In Scratchpad? | In Report? | In Deck? | In Signal Brief? | Source URL? | Verified? | Status |
|---|----------------------|---------------|-----------|---------|-----------------|-----------|-----------|--------|
| 1 | "{quote start}..." | Yes/No | L{n} | Slide {n} | Yes/No | {url or "none"} | {tier-dependent} | [status] |

## Dimension 7: Browser Observation Fidelity

### Screenshot Coverage
- Expected screenshots: {n} (20 test steps)
- Found on disk: {n}
- Coverage: {x}%

### Observation Cross-Reference
| Test Step | Scratchpad Observation | Report Claim | Match? | Status |
|-----------|----------------------|-------------|--------|--------|
| 2e: Typo "{query}" | {result from 09-browser-findings} | {claim from report} | {yes/no} | [status] |

---

## Files Verified

### Deliverables
| File | Status | Size |
|------|--------|------|
| {company}-search-audit.md | Found | {size} |
| {company}-landing-page.html | Found | {size} |
| ... | | |

### Workspace
| File | Status | Size |
|------|--------|------|
| 01-company-context.md | Found | {size} |
| ... | | |

---
*Report generated by /algolia-audit-factcheck v1.1. Verification tier: {tier}.*
```

### Output 2: `{company}-correction-manifest.md`

**Write to:** `$AUDIT_DIR/{CompanyName}/deliverables/{company}-correction-manifest.md`

Machine-readable fix list for correcting deliverables.

```markdown
# {Company} — Correction Manifest
*Generated by /algolia-audit-factcheck v1.1 on {date}*
*Feed this file to the audit skill or use it as a manual fix checklist.*

## Evidence Tier Summary
| Tier | Count | Status |
|------|-------|--------|
| Tier 1 — Data Source Verified | {N} | ✅ Cite normally |
| Tier 2 — Web Search Only (flagged) | {N} | ⚠️ Labeled in deliverables |
| Tier 2 — Web Search Only (UNFLAGGED) | {N} | 🔴 MUST ADD WARNING LABEL |
| Tier 3 — Dropped (unverifiable) | {N} | ❌ Removed from deliverables |

## Corrections Required: {N total}

### 🔴 TIER 3 DROPS — REMOVE FROM ALL DELIVERABLES (blocking)
These claims cannot be verified by any method. They must be deleted from every deliverable file.

| # | Claim | File(s) | Reason | Action |
|---|-------|---------|--------|--------|
| 1 | "{claim text}" | {file1}, {file2} | {URL 404 / stat not on page / not found in WebSearch} | **DELETE** |

### 🔴 TIER 2 UNFLAGGED — ADD WARNING LABEL (blocking)
These claims were found only via WebSearch/WebFetch of third-party pages but appear in deliverables WITHOUT the required ⚠️ warning. This is treated as a Tier 3 violation until labeled.

| # | Claim | File(s) | Current State | Required Label |
|---|-------|---------|---------------|----------------|
| 1 | "{claim text}" | {file} (L{n}) | No warning | Add: `🔴 ⚠️ Web search only — verify before using` |

### ⚠️ TIER 2 FLAGGED — Web Search Only (properly labeled, for AE awareness)
These claims are already labeled with ⚠️. Listing here for AE transparency.

| # | Claim | Source | Label Present? |
|---|-------|--------|----------------|
| 1 | "{claim text}" | {WebSearch/third-party URL} | ✅ Labeled |

### DISCREPANCY FIXES (propagate single source of truth)
| # | Data Point | Correct Value | Source of Truth | Files to Fix | Current Wrong Value |
|---|-----------|---------------|-----------------|-------------|-------------------|
| 1 | {data_point} | {correct} | {scratchpad file} (L{n}) | {file1 L{n}, file2 L{n}} | {wrong value} |

### INCORRECT FIXES (replace wrong values)
| # | Data Point | Wrong Value | Correct Value | Affected Files | How Verified |
|---|-----------|------------|---------------|---------------|-------------|
| 1 | {data_point} | {wrong} | {correct} | {files} | {verification method} |

### MISSING DATA FIXES (add to deliverables)
| # | Data Point | Value | Source | Missing From |
|---|-----------|-------|--------|-------------|
| 1 | {data_point} | {value} | {source file} (L{n}) | {deliverable} |

### STALE DATA (consider refreshing)
| # | Data Point | Audit Value | Current Value | Drift % | Source |
|---|-----------|------------|---------------|---------|--------|
| 1 | {data_point} | {old} | {new} | {drift}% | {API + date} |

### SOURCE CITATION FIXES (add/fix URLs)
| # | Claim | Current Source | Issue | Fix |
|---|-------|---------------|-------|-----|
| 1 | {claim text} | {current or "None"} | {issue} | {recommended fix} |
```

### Output 3: `{company}-skill-feedback.md`

**Write to:** `$AUDIT_DIR/{CompanyName}/deliverables/{company}-skill-feedback.md`

Methodology improvement analysis for the audit skill.

```markdown
# Skill Methodology Feedback — {Company} Audit
*Generated by /algolia-audit-factcheck v1.0 on {date}*
*Use this to improve ~/.claude/skills/algolia-search-audit/SKILL.md*

## Patterns Detected: {count}

## Pattern: {pattern name}
**Frequency**: Found in {N} claims in this audit
**Root Cause**: {why this keeps happening — traced to specific SKILL.md instruction or process gap}
**SKILL.md Fix**: {specific change to the skill methodology — exact wording to add/change}
**Affected Phase/Step**: Phase {N}, Step {M}
**Evidence**: {specific examples from this audit}

{Repeat for each pattern detected}

---

## Audit Health Summary
- Overall confidence: {X}/10
- Most common issue type: {DISC/FAIL/UNVF/MISS/STALE}
- Highest-risk dimension: {dimension name + score}
- Lowest-risk dimension: {dimension name + score}
- Citation coverage: {X}%
- Screenshot coverage: {X}%

## Recommended SKILL.md Changes (Priority Order)
1. {highest impact change — with exact instruction text to add}
2. {second highest}
3. {third}
```

---

## Team Mode Architecture

The fact-checker uses Claude Code's team mode to run verification dimensions in parallel.

### Agent Topology

```
TEAM LEAD (Coordinator — this conversation)
  │
  │ Phase 1 (sequential)
  ├─→ Agent 1: Claim Registry + Dims 1-3 (MUST complete first)
  │
  │ Phase 2 (parallel fan-out)
  ├─→ Agent 2: API Data Accuracy (Dim 4)      ─┐
  ├─→ Agent 3: Citations + Quotes (Dims 5-6)   ├─ all run in parallel
  ├─→ Agent 4: Browser Fidelity (Dim 7)        ─┘
  │
  │ Phase 2b (after Agents 2-4 complete)
  ├─→ Agent 5: Pattern Analysis (reads all dim results)
  │
  │ Phase 3 (team lead)
  └─→ Score aggregation + 3 output files
```

### Spawning Instructions

**Phase 1 — Sequential**:
```
Task tool:
  subagent_type: general-purpose
  name: "claim-registry-builder"
  prompt: [Phase 1 instructions above, with paths to all files]
```
Wait for Agent 1 to complete and return claim-registry.md + dim-1-2-3-results.md.

**Phase 2 — Parallel**:
Spawn Agents 2, 3, and 4 simultaneously in a single message with 3 Task tool calls:
```
Agent 2: subagent_type: general-purpose, name: "api-verifier"
Agent 3: subagent_type: general-purpose, name: "citation-verifier"
Agent 4: subagent_type: general-purpose, name: "browser-verifier"
```
Each agent receives: the claim registry path, the tier, and dimension-specific instructions.

**Phase 2b — After Agents 2-4**:
```
Agent 5: subagent_type: general-purpose, name: "pattern-analyzer"
```
Receives paths to all dim result files.

**Phase 3 — Team Lead**:
Read all 5 dimension result files. Aggregate scores. Generate 3 output files.

### Tier Impact on Agents

| Agent | Quick | Standard | Full |
|-------|-------|----------|------|
| 1 (Registry + Dims 1-3) | Read all files, full analysis | Same | Same |
| 2 (API Data) | Read-only cross-ref | + SimilarWeb + BuiltWith re-calls | + competitor APIs |
| 3 (Citations + Quotes) | Read-only URL scan | + WebFetch 10-15 URLs + transcripts | + all URLs + all transcripts |
| 4 (Browser) | Read-only scratchpad check | + screenshot file verification | + Chrome MCP re-tests |
| 5 (Patterns) | Full analysis of dim results | Same | Same |

---

## Key Design Decisions

1. **Scratchpad = ground truth for Quick tier** — deliverables are compared against raw collected data in workspace files
2. **15% tolerance band for SimilarWeb data** — monthly estimates shift naturally; this is not an error
3. **Cross-file consistency is highest ROI** — zero API calls, catches the most real issues
4. **Quote verification = trace to scratchpad + WebFetch** — URL resolution alone is insufficient; must find actual quote text
5. **Screenshots almost always UNVERIFIABLE** — session-bound Chrome MCP IDs can't be re-checked; report count as warning, don't penalize heavily
6. **No brand-check overlap** — factcheck = factual accuracy only; brand compliance stays with `/algolia-brand-check`
7. **Team mode is built-in from day 1** — parallel agents cut execution time ~60%
8. **3 output files** — human report + machine-readable corrections + methodology feedback creates a full improvement loop
9. **Correction manifest is atomic** — each row is one specific fix with correct value, source, and affected files
10. **Skill feedback identifies patterns, not just issues** — root cause analysis enables SKILL.md methodology improvements

## Feedback Loop

```
/algolia-search-audit  ──→  6 deliverables + workspace
         │
         ▼
/algolia-audit-factcheck  ──→  3 files:
         │                      ├── factcheck-report.md (human review)
         │                      ├── correction-manifest.md (fix deliverables)
         │                      └── skill-feedback.md (fix methodology)
         │
         ▼
Fix deliverables (using manifest) + Fix SKILL.md (using feedback)
         │
         ▼
Next audit is more accurate → factcheck scores improve over time
```

## Important Notes

- **Always verify before claiming** — Read actual files. Never assume data from compaction summaries is correct.
- **Never fabricate verification results** — If a data point can't be checked at the selected tier, mark it `[UNVF]`, not `[PASS]`.
- **Full tier is the default** — External verification (MCP API re-calls, WebFetch of every source URL, quote verification) is the PRIMARY job of a fact-check. A fact-check without external verification is not a fact-check.
- **Standard tier is for time-constrained checks** — Verifies prospect APIs + samples source URLs, but skips competitor re-verification and browser re-tests.
- **Quick tier is ONLY for rapid pre-share sanity checks** — Read-only, zero external calls. Catches consistency and math errors but does NOT validate the information itself. This is 10% of the job at best.
- **The correction manifest is the most actionable output** — It tells you exactly what to fix, where, and what the correct value is.
- **The skill feedback file accumulates value over multiple audits** — Run fact-checks on 2-3 audits and patterns emerge that reveal systemic SKILL.md weaknesses.

---

## FACTCHECK_GATE.md — Machine-Readable Publish Gate (MANDATORY)

**This file is written LAST, after all 7 dimensions are scored.** It is the structured verdict consumed by the `/algolia-search-audit` orchestrator to decide whether to proceed to local review, warn the user, or block publishing entirely.

**Location**: `{company}-audit-workspace/FACTCHECK_GATE.md`

**Write this file immediately after calculating the overall score. No exceptions.**

### Format (copy exactly):

```markdown
# FACTCHECK GATE
SCORE: {x.x}
CONFIDENCE: {HIGH | MODERATE | LOW}
ACTION: {PROCEED | WARN | BLOCKED}
BLOCKING_COUNT: {n}
WARNING_COUNT: {n}
DATE: {YYYY-MM-DD}

## BLOCKING ISSUES (must fix before publish — ACTION = BLOCKED if any exist)
{List each [DISC] and [FAIL] item as: "- [TYPE] {field}: audited '{wrong}' vs verified '{correct}' — Source: {url}"}
{If none: "- none"}

## WARNINGS (should review — shown to user at review gate)
{List each [UNVF] and [STALE] item as: "- [TYPE] {field}: {description} — {recommendation}"}
{If none: "- none"}

## TOP 3 FINDINGS FOR USER
1. {Most important positive or negative finding in one sentence}
2. {Second most important}
3. {Third most important}
```

### Gate Rules (enforced by orchestrator):

| Score | Confidence | ACTION | Orchestrator Behavior |
|-------|-----------|--------|----------------------|
| ≥ 8.0 | HIGH | PROCEED | Stage to hub automatically, present for review |
| 6.0–7.9 | MODERATE | WARN | Stage to hub, show all warnings at review gate, require explicit user acknowledgment before publish |
| < 6.0 | LOW | BLOCKED | Do NOT stage. Show blocking issues. Require fixes before re-running factcheck. Do not proceed until score ≥ 6.0 |

### ACTION = BLOCKED rule:
If **any** `[DISC]` or `[FAIL]` items are found regardless of score, set `ACTION: BLOCKED` and `BLOCKING_COUNT: {n}`. The orchestrator will not stage or publish until these are corrected and the factcheck re-run.

### Example FACTCHECK_GATE.md (passing):
```markdown
# FACTCHECK GATE
SCORE: 9.2
CONFIDENCE: HIGH
ACTION: PROCEED
BLOCKING_COUNT: 0
WARNING_COUNT: 2
DATE: 2026-03-18

## BLOCKING ISSUES
- none

## WARNINGS
- [UNVF] Under Armour case study: metric "35% conversion" not confirmed on live page — recommend WebFetch to verify
- [STALE] Traffic estimate: SimilarWeb shows 3.2M/mo vs audited 3.5M — within 10% tolerance, acceptable

## TOP 3 FINDINGS FOR USER
1. All 10 scoring area values verified against browser findings — no discrepancies
2. ROI math verified: $97M × 5% = $4.85M confirmed correct
3. Nike and Asics BuiltWith verification confirmed — golden angle data is solid
```

### Example FACTCHECK_GATE.md (blocked):
```markdown
# FACTCHECK GATE
SCORE: 5.8
CONFIDENCE: LOW
ACTION: BLOCKED
BLOCKING_COUNT: 2
WARNING_COUNT: 4
DATE: 2026-03-18

## BLOCKING ISSUES
- [DISC] revenue: audited '~$2.8B' vs verified '~$1.6B (FY2024)' — Source: https://ir.llbean.com/...
- [FAIL] case_study_metric: "Under Armour 35% conversion" NOT found on https://algolia.com/customers/under-armour/ — fabricated or wrong URL

## WARNINGS
- [UNVF] CEO quote: not found in 11-investor-intelligence.md, cannot verify source
- [STALE] Monthly visits: 26.7M audited vs 24.1M SimilarWeb current
- [UNVF] Competitor bounce rate: Nordstrom 42% — no source URL
- [MISS] score.breakdown_severity missing for 3 areas

## TOP 3 FINDINGS FOR USER
1. Revenue figure is 75% too high — must correct before sharing with prospect
2. Under Armour case study metric is unverifiable at the cited URL — remove or find correct source
3. CEO quote needs scratchpad source trace — currently floating without evidence
```
