# algolia-intel-queries

> Generate a vertically-calibrated set of 14–18 search queries for browser-based audit testing, covering all query types needed to evaluate a site's search behavior.

**Version:** 2.0.0 · **Layer/Phase:** Phase 1 Query Preparation · **Suite:** Algolia Search Audit

## What it does

Produces the search query test set that the browser auditor (`algolia-audit-browser`) uses when manually testing a prospect's site search. The skill reads the company's vertical, product categories, house brands, and top traffic keywords from upstream research files, then generates a balanced mix of 14–18 queries spanning 8 types: broad category, specific product, NLP/conversational, typo variants, synonym/colloquial, non-product content, brand, and gibberish/no-results. Every query carries a `Tests:` annotation explaining what it proves so the browser auditor knows exactly what to observe. No browser interaction is required — this is pure analysis and writing over upstream research outputs.

## When to use

- Generate or regenerate the query test set for a company's audit workspace.
- Create the `05-test-queries.md` file before running `algolia-audit-browser`.
- Build a query mix (NLP, typo, synonym, brand, zero-results) tailored to a specific company and retail vertical.
- Invoked automatically by `algolia-audit-research` at Step 5 in the full research pipeline (after `04-competitors.md` is written).
- Can also be run standalone when only the query file needs refreshing — input is the company slug, prerequisite is `01-company-context.md`.

## Inputs (upstream)

- `$ARGUMENTS` — company slug; resolves to `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`
- `01-company-context.md` — required; reads vertical, key product categories, house brands/private labels, brand name and common spelling variants
- `03-traffic-data.md` — optional but preferred; top organic/direct keywords are used to derive typo variants from the company's most-searched terms rather than generic ones

## Outputs

Single file: `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/05-test-queries.md`

Content:
- 14–18 numbered queries grouped into 8 typed sections (Broad Category, Specific Product, NLP/Conversational, Typo Variants, Synonym/Colloquial, Non-Product Content, Brand, No-Results Recovery)
- Each query carries a `Tests:` marker explaining what it proves
- Browser Audit Mapping table linking each `algolia-audit-browser` step to a specific query number and test objective
- Query Source Notes section documenting how each query was derived (top keyword, house brand, product category, etc.)

## Data sources

| Source | Provides | Method |
|--------|----------|--------|
| `01-company-context.md` | Vertical, product categories, house brands, brand name variants | Read upstream output |
| `03-traffic-data.md` | Top organic/direct keywords for typo variant derivation | Read upstream output (optional) |

No external API calls or live data sources — this skill is pure LLM reasoning over upstream research outputs.

## How PRISM runs it

PRISM invokes this skill via the claude-cli executor as part of the `algolia-audit-research` pipeline at Step 5, after `algolia-intel-competitors` writes `04-competitors.md`. It requires `01-company-context.md` to be present (from `algolia-intel-company`); `03-traffic-data.md` is optional but improves typo query quality. The output `05-test-queries.md` is a hard prerequisite for `algolia-audit-browser` — browser testing cannot start until this file exists. The skill is idempotent: re-running for the same company safely overwrites the previous query file.

## Dependencies

- `01-company-context.md` — required upstream input (from `algolia-intel-company`)
- `03-traffic-data.md` — optional upstream input (from `algolia-intel-traffic`); improves typo variant quality
- `check-claim-traceability.py` — verification script that checks every numbered query has a `Tests:` marker (`~/.claude/skills/algolia-search-audit/scripts/`); exit 0 = all queries testable, exit 1 = untestable queries listed
- No API keys required; no MCP servers required

## Notes

- Queries must use the company's ACTUAL products, categories, and brands — not generic placeholders. Generic queries (e.g., "running shoes" for a warehouse club) are explicitly prohibited. Good: "Kirkland running shoes", "treadmill for home gym".
- NLP queries must use realistic shopping language for the specific vertical (e.g., warehouse club: "bulk coffee for office"; luxury resale: "pre-owned Chanel bag under 2000").
- Typo variants should be derived from `03-traffic-data.md` top keywords if available; otherwise take the top 2 product categories and introduce common typos (double letters, transposition, missing letter).
- Verification gate (4 checks): file ≥ 2000 bytes; all 8 query type sections present; Browser Audit Mapping table present; every numbered query has a `Tests:` marker (Gate 4, enforced by `check-claim-traceability.py`). Any gate failure must be fixed before reporting done.
