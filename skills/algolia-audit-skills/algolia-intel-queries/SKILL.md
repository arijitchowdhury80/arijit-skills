---
name: algolia-intel-queries
version: 2.0.0
description: Use this skill to create the search query test set for an Algolia browser audit. Invoke when someone asks to: generate the queries to run on a company's website, create or regenerate the test-queries.md file for an audit workspace, decide what to search for during site search testing, or build a query mix (NLP/conversational, typo tolerance, synonym handling, brand, zero-results) tailored to a specific company and retail vertical. This is the query-preparation step that happens before browser test execution — not during active browser testing and not for broader research phases.
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Input
$ARGUMENTS — company slug. Reads: $ALGOLIA_AUDIT_DIR/{CompanyName}/research/01-company-context.md

## Output
$ALGOLIA_AUDIT_DIR/{CompanyName}/research/05-test-queries.md

## Path
```bash
# At start of skill execution:
if [ -z "$ALGOLIA_AUDIT_DIR" ]; then
  AUDIT_DIR="$(pwd)"
  echo "WARNING: ALGOLIA_AUDIT_DIR not set — using current directory: $AUDIT_DIR"
else
  AUDIT_DIR="$ALGOLIA_AUDIT_DIR"
fi
```

---

## Query Types Required (14-18 total)

Generate queries across ALL of these types:

| Type | Count | Purpose | Example |
|------|-------|---------|---------|
| Broad category | 2 | SAYT + results quality | "televisions", "running shoes" |
| Specific product | 2 | Precision + relevance | "noise cancelling headphones", "Kirkland protein bar" |
| NLP / Conversational | 2-3 | Semantic search test | "best TV for gaming under $500", "gift for dad who likes golf" |
| Typo variants | 2 | Typo tolerance | "samung tv", "nikee shoes", "runnnig shoes" |
| Synonym / colloquial | 2 | Synonym handling | "couch" vs "sofa", "sneakers" vs "tennis shoes" |
| Non-product content | 2 | Federated search | "return policy", "store hours", "customer service" |
| Brand / sub-brand | 2 | Brand intent detection | "Kirkland", "Nike", house brand names |
| Gibberish / no-results | 1 | No-results handling | "asdfghjk" or similar |

---

## How to Generate

### Step 1 — Read company context
Read `$AUDIT_DIR/{CompanyName}/research/01-company-context.md` to identify:
- Company vertical (e.g., warehouse retail, athletic footwear, luxury resale)
- Key product categories
- House brands / private labels
- Brand name and common spelling variants

### Step 2 — Use traffic keywords if available
If `$AUDIT_DIR/{CompanyName}/research/03-traffic-data.md` exists, read the top organic/direct keywords. Use these as the basis for typo variants (misspell the company's most-searched terms, not generic ones).

### Step 3 — Generate vertically-calibrated queries
Use the company's ACTUAL products and categories. Do not use generic placeholder queries.

**BAD:** "running shoes" for a warehouse club
**GOOD:** "Kirkland running shoes", "treadmill for home gym", "Costco tire installation"

For NLP queries: use realistic shopping language for this vertical.
- Warehouse club: "bulk coffee for office", "best protein powder family size"
- Athletic footwear: "trail running shoes for wide feet"
- Luxury resale: "pre-owned Chanel bag under 2000"

For typo variants: misspell the company's most common search terms.
- Derive from 03-traffic-data.md top keywords if available.
- Otherwise, take the top 2 product categories and introduce common typos (double letters, transposition, missing letter).

For brand queries: use the company's actual house brands, private labels, or sub-brands. If none exist, use the company name itself and a key vendor brand.

---

## Output Format

Write the following to `$AUDIT_DIR/{CompanyName}/research/05-test-queries.md`:

```markdown
# Test Queries — {Company}
*Generated: {date} | Vertical: {vertical}*

## Query Set (14-18 queries)

### Broad Category Queries
1. "{query}" — [{category}] — Tests: SAYT response, result quality
2. "{query}" — [{category}] — Tests: filter/facet availability

### Specific Product Queries
3. "{query}" — [{product type}] — Tests: precision search
4. "{query}" — [{product type}] — Tests: SKU-level relevance

### NLP / Conversational
5. "{query}" — Tests: semantic intent understanding
6. "{query}" — Tests: multi-attribute NLP
7. "{query}" — Tests: price + attribute combination

### Typo Variants
8. "{typo query}" → correct: "{correct}" — Tests: typo tolerance
9. "{typo query}" → correct: "{correct}" — Tests: correction prompt

### Synonym / Colloquial
10. "{synonym1}" vs "{synonym2}" — Tests: synonym handling
11. "{colloquial}" vs "{formal}" — Tests: language normalization

### Non-Product Content
12. "return policy" — Tests: federated search
13. "store hours" OR "customer service" — Tests: content integration

### Brand Queries
14. "{house brand}" — Tests: brand intent detection
15. "{sub-brand or vendor brand}" — Tests: brand filtering

### No-Results Recovery
16. "asdfghjk" OR "{gibberish}" — Tests: zero-results handling

---

## Browser Audit Mapping

| Step | Query to use | What to test |
|------|-------------|--------------|
| 2c SAYT | Query 1 (broad) | Autocomplete speed + content |
| 2d Results | Query 2 (broad) | Result quality + facets |
| 2e Typo | Query 8 (typo) | Tolerance + correction prompt |
| 2f Synonym | Query 10 | Synonym recognition |
| 2g No-results | Query 16 | Zero-results handling |
| 2h Non-product | Query 12 | Content federation |
| 2m NLP | Query 5 (NLP) | Semantic understanding |

---

## Query Source Notes
*Document how each query was derived (top keyword, house brand, product category, etc.) so the browser auditor has context when testing.*
```

---

## Verification Gate

After writing `05-test-queries.md`, verify ALL of the following before reporting success:

```bash
FILE="$AUDIT_DIR/{CompanyName}/research/05-test-queries.md"

# Gate 1: File exists and is large enough
SIZE=$(wc -c < "$FILE")
[ "$SIZE" -ge 2000 ] || echo "FAIL: File too small ($SIZE bytes, need ≥2000)"

# Gate 2: All 8 query types present
grep -q "Broad Category" "$FILE" || echo "FAIL: Missing Broad Category section"
grep -q "Specific Product" "$FILE" || echo "FAIL: Missing Specific Product section"
grep -q "NLP" "$FILE" || echo "FAIL: Missing NLP section"
grep -q "Typo" "$FILE" || echo "FAIL: Missing Typo section"
grep -q "Synonym" "$FILE" || echo "FAIL: Missing Synonym section"
grep -q "Non-Product" "$FILE" || echo "FAIL: Missing Non-Product section"
grep -q "Brand" "$FILE" || echo "FAIL: Missing Brand section"
grep -q "No-Results" "$FILE" || echo "FAIL: Missing No-Results section"

# Gate 3: Browser audit mapping table present
grep -q "Browser Audit Mapping" "$FILE" || echo "FAIL: Missing browser audit mapping table"

echo "Verification complete. File: $FILE | Size: $SIZE bytes"
```

```bash
# Gate 4 (mechanical testability — every numbered query must be marked testable):
# each query line must carry a "Tests:" marker so the browser auditor knows what it proves.
SCRIPTS="$HOME/.claude/skills/algolia-search-audit/scripts"   # adjust if running from repo
python3 "$SCRIPTS/check-claim-traceability.py" queries "$FILE"
# Exit 0 = every numbered query has a "Tests:" marker. Exit 1 = untestable queries listed.
```

If any gate fails: fix and re-verify before reporting done. For Gate 4, add a `— Tests: <what it
proves>` clause to any query the checker flags — do not ship a query that states no test target.

---

## Integration with algolia-audit-research

This skill extracts Step 5 from `algolia-audit-research`. When running the full research pipeline, `algolia-audit-research` calls this skill at Step 5 after `04-competitors.md` is written.

When invoked standalone:
- Input: company slug as $ARGUMENTS
- Prerequisite: `01-company-context.md` must exist
- Optional but preferred: `03-traffic-data.md` for keyword-derived typos
- Output: `05-test-queries.md`
- No browser required — pure analysis and writing

---

## Workspace Declaration
This skill writes to PRODUCTION: `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/05-test-queries.md`
It is safe to overwrite if re-running query generation for the same company (idempotent).
