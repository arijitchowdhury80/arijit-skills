---
name: algolia-intel-investor
description: Layer 1G investor and executive intelligence module. Captures verbatim executive quotes from earnings calls, SEC 10-K MD&A and risk factors, and Yahoo Finance news feed. Produces 11-investor-intelligence.md and 11-investor-intelligence.json. Run in Wave 1 for public companies. For private companies, uses CEO/founder interview transcripts via WebFetch.
layer: 1-intelligence
module_id: 1G
script: collect-investor.py
reads_from:
  - 01-company-context.json
writes_to:
  - 11-investor-intelligence.md
  - 11-investor-intelligence.json
mcp_required:
  - yahoo_finance: "get_yahoo_finance_news for news feed"
  - gemini_search: "grounded Google-Search via scripts/gemini_search.py — earnings call transcripts"
skill_enrichment: true
version: 2.0.0
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Module Identity
- **Layer:** 1-Intelligence (Wave 1)
- **Module ID:** 1G
- **Model tier:** data_enrichment (claude-haiku-4-5)

---

## Step 1: Run Script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-investor.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  [--ticker TICKER] \
  [--private]
```

---

## Step 2: Skill Enrichment — ALL Sources (not fallback chain)

### For public companies:
1. **Earnings call transcripts** — Use `gemini_search.py` to locate transcripts:
   ```bash
   python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
     --system "Find verbatim executive quotes from earnings call transcripts. Cite exact sources." \
     '"{Company}" Q4 2025 earnings call transcript'
   ```
   Then WebFetch the cited transcript URLs (Motley Fool / Seeking Alpha) — last 3 quarters, ANY named speaker.
   Label: `[FACT — {source} transcript WebFetch, {date}]`

2. **SEC EDGAR 10-K** — WebFetch sec.gov directly (SEC EDGAR MCP does NOT exist — use direct HTTP WebFetch)
   URL: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K&count=1`
   Extract: MD&A section + Risk Factors (digital/technology items)
   Label: `[FACT — SEC EDGAR 10-K WebFetch, {date}, {URL}]`

3. **Yahoo Finance news** — get_yahoo_finance_news(ticker)
   Label: `[FACT — Yahoo Finance MCP news, {date}]`

### For private companies:
- No SEC EDGAR, no Yahoo Finance
- Replace with: CEO/founder podcast interviews, conference talks, company blog, press releases
- Label: `[WEBFETCH — {source}, {date}]`

### Quote rules:
- VERBATIM only if WebFetch confirms exact text. Use quotation marks.
- If not WebFetched: use *said that* notation. NO quotation marks.
- Named speaker + title + source URL + date — every quote.
- NO anonymous sources.

### MANDATORY grounding gate — verify every verbatim quote against the fetched source

Injecting the source and asking for an exact quote is NOT sufficient — paraphrases dressed
as verbatim are the classic hallucination (proven in the report-QA spike: a post-gen
verifier is mandatory). Before any quote ships with quotation marks, run it through the
deterministic grounding gate. It checks TWO things: (1) the quote is an EXACT substring of
the fetched source text, and (2) the source date is **>= January 2025**.

```bash
# /tmp/quotes.json = [{"quote":"<verbatim candidate>","source_date":"2025-03-14","speaker":"..."}]
# /tmp/source.txt  = the plaintext you WebFetched (transcript / 10-K / article)
python3 ~/.claude/skills/algolia-search-audit/scripts/ground_quotes.py \
  /tmp/quotes.json /tmp/source.txt
```

The script returns `{accepted, rejected, ...}` and exits non-zero if anything was rejected:
- `accepted[]` → quote is verbatim-present AND >= Jan 2025. Ship with quotation marks + `[FACT]`.
- `rejected[]` → each carries `_grounding.reasons`:
  - `not_grounded` → the candidate is NOT an exact substring (paraphrase / fabrication).
    **Do NOT ship it as a verbatim quote.** Either re-extract the exact text or drop it.
  - `too_old` / `recency_unverified` → fails the Jan-2025 floor. **Drop it** (SKILL rule below).

Never include a quote that the gate rejected. An undated "verbatim" quote fails closed.

---

---

## Step 3: Media Quote Extraction (Gemini-grounded Signals)

### 3a. Run the script

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/collect-exec-media.py \
  {domain} \
  "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/" \
  [--company-name "{CompanyName}"]
```

### 3b. Capture stdout and check status

Parse the JSON printed to stdout:
- `status: "success"` with `media_quotes_collected > 0` → proceed to Step 3c
- `status: "partial"` with `"media_quotes"` in `skill_enrichment_required` → Gemini-grounded search unavailable or no results → go to Step 3e (gemini_search.py fallback)
- `media_quotes_collected: 0` → go to Step 3e (gemini_search.py fallback)

### 3c. LLM enrichment — context and algolia_relevance

For each entry in `media_quotes[]` where `context` is null:
- Write a one-sentence Algolia pitch context explaining why this quote matters in a sales context
  (e.g., "Signals that {exec_name} is actively investing in digital CX, opening the door for a search conversation.")
- Format: plain sentence, present tense, no quotes around it

For each entry where `algolia_relevance` is null:
- Write pipe-separated relevance tags from this set:
  `personalization | search | digital | technology | cx | commerce | platform | ai | data | performance`
- Include 1-3 most applicable tags only

### 3d. Write enriched fields back to JSON and MD

Update `11-investor-intelligence.json`:
- For each entry in `media_quotes[]`, set `context` and `algolia_relevance` to the enriched values
- Do NOT modify any other keys (executive_quotes, _meta, etc.)
- Write the file (overwrite)

Update `11-investor-intelligence.md`:
- In the `## Media Quotes (Trade Press)` section, replace each `[COLLECT_VIA_SKILL]` placeholder:
  - Under **Context (Algolia pitch):** → insert the enriched context sentence
  - Under **Algolia Relevance:** → insert the pipe-separated tags

### 3e. gemini_search.py fallback (when script collection unavailable or zero results)

Run `gemini_search.py` for each top executive (max 3, prioritize CEO/CMO/CTO):

```bash
python3 ~/.claude/skills/algolia-search-audit/scripts/gemini_search.py \
  --system "Find verbatim executive quotes from trade press interviews. Cite exact sources." \
  '"{exec_name}" "{company_name}" 2024 OR 2025 interview digital commerce personalization'
```

**Grounding rule (no fabrication):** use `citations[]` from the JSON output as URLs to WebFetch for verbatim text. If `"grounded": false`, leave the entry null — do not synthesize a quote from ungrounded model knowledge.

For each result:
- Confirm the URL is trade press (NOT sec.gov, fool.com, seekingalpha.com)
- **HARD RULE: Reject any quote dated before January 2025. No exceptions.** Quotes older than 12 months are stale — executives change roles, strategies change, the quote becomes a liability not an asset. If no quotes ≥ Jan 2025 exist, leave the section empty rather than use old quotes. **Enforce this with `ground_quotes.py` (see the grounding gate in Step 2) — its recency floor is Jan 2025 and it rejects undated quotes fail-closed.**
- Extract the most relevant verbatim sentence containing the exec's name
  - If verbatim not possible: use *said that* notation, set `confidence: "ESTIMATE"`
- Build a `media_quote` entry with all fields populated (including `context` and `algolia_relevance` — LLM fills these directly, not deferred)
- Append to `media_quotes[]` in `11-investor-intelligence.json`
- Append formatted quote block to `## Media Quotes (Trade Press)` section in `11-investor-intelligence.md`

**Label format for gemini_search.py fallback:**
`[ESTIMATE — {Publication} via Gemini search, {date}, {URL}]`

---

## Verification Gate

Ensure `11-investor-intelligence.json` has `_meta` block (use `_meta` with underscore):
```json
{"_meta": {"skill_enrichment_completed": true}, "executive_quotes": [...], "media_quotes": [...]}
```

Pass conditions — ALL must be true:
- `[ ]` Both files exist: `11-investor-intelligence.md` and `11-investor-intelligence.json`
- `[ ]` `11-investor-intelligence.md` ≥ 3000 bytes
- `[ ]` At least 3 executive quotes each with `speaker`, `title`, `source_url` fields
- `[ ]` No anonymous sources
- `[ ]` `_meta.skill_enrichment_completed = true`
- `[ ]` `11-investor-intelligence.json` contains `media_quotes` key (array, may be empty)
- `[ ]` Any entries in `media_quotes[]` have non-null `source_url`
