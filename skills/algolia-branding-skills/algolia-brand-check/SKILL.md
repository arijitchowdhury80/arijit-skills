---
name: algolia-brand-check
description: Scan content for Algolia brand compliance across 7 dimensions. Returns 1-10 score with fixes.
argument-hint: "[--theme marketing|deliverable] [content or file path]"
---

# Algolia Brand Compliance Check

Audit any content artifact against current Algolia brand guidelines across seven dimensions. Produces
a scored report with line-level violations, suggested fixes, and a pass/fail verdict.

## Before you start: read the source of truth

**This skill holds no brand data of its own.** Read these first, every run:

- `../algolia-shared-reference/brand-core/tokens.md` — themes, type, shape
- `../algolia-shared-reference/brand-core/approved-stats.md` — the only valid numbers
- `../algolia-shared-reference/brand-core/product-names.md` — current and retired names
- `../algolia-shared-reference/brand-core/messaging-framework.md` — voice, positioning, editorial

If a value is not in those files, it is not a rule. Do not audit against remembered brand knowledge —
Algolia's brand moved in 2026, and stale memory is exactly what this skill exists to catch.

## Input

- Content to audit (text, HTML, markdown, or structured slide content)
- Content type (blog, email, landing page, social post, deck, UI copy, one-pager, case study, brief,
  partner material)
- Target audience (developers, business decision-makers, partners, internal)
- **Theme** — `marketing` or `deliverable`. If not supplied, infer from content type using the table
  in `tokens.md` and state which you inferred.

## Process

1. **Voice & Tone Audit** — Verify content is confident, clear, technically credible, approachable.
   Flag arrogant, flippant, overly casual, or condescending language. Developer content keeps
   precision; business content keeps accessibility. Flag hedging and unsubstantiated superlatives.
2. **Terminology Audit** — Check every product reference against `product-names.md`. Flag anything on
   that file's retired list. Verify capitalization of the brand and product names.
3. **Editorial Standards Audit** — AP Style, Oxford comma, sentence case headings, numbers under 10
   spelled out, Month Day, Year dates, no double spaces, consistent lists, correct em-dash usage.
4. **Messaging Accuracy Audit** — Cross-check every quantified claim against `approved-stats.md`.
   Flag any figure not on that list. Flag any figure used **without its source** — a correct number
   with no provenance is still a violation. Verify positioning matches `messaging-framework.md`.
5. **Visual Compliance Audit** — Applies when the artifact contains HTML, CSS, or design specs.
   Validate against **the declared theme only**, per `tokens.md`:
   - `marketing`: `#003DFF` primary, `#021046` headlines, `#2f3447` body, `#0e1224` dark bands,
     `#f7f8fb` wash. Sections sit on one of navy / kelly blue / white / gray. **`#5468FF` is a
     violation in this theme.**
   - `deliverable`: `#003DFF` primary, `#5468FF` accent, `#23263B` text, `#F5F5F7` background,
     `#E5E7EB` borders. **`#5468FF` is correct here — do not flag it.**
   - Both themes: Sora only. Check logo clear space and minimum size.
6. **Anthropomorphism Audit** — Flag any instance where Algolia thinks, believes, feels, wants, or
   has emotions. Algolia enables, provides, powers, delivers.
7. **Competitor Mention Audit** — Flag competitor names in marketing-facing content. Sales enablement
   and internal docs may reference them; marketing-facing content must not.

## Automatic failures

Any of these is a critical violation regardless of dimension score. They are values Algolia has
retired, and their presence means the artifact was built from a stale source:

| Value | Why it fails |
|---|---|
| `Source Sans Pro` | Never Algolia's typeface in the current brand. Sora is |
| `Inter`, `Roboto`, `DM Sans`, `Arial`, system fonts, serif | Explicitly banned faces |
| `17,000+` customers | Retired — 18,000+ businesses |
| `1.7 trillion` searches | Retired — 1.75 trillion |
| `30 billion records` | Withdrawn, no current source |
| `#5468FF` **in a `marketing` artifact** | Pre-2023 accent, absent from algolia.com and the Figma library |
| `#21243D`, `#F5F5F7` **in a `marketing` artifact** | Not in the marketing palette |
| `Algolia Places`, `Algolia Recommend`, `Algolia Crawler`, `Algolia AI Search`, `Algolia NeuralSearch` | Retired product names |

An artifact containing any of these cannot score above 5, and the verdict is FAIL.

## Output Sections

### Overall Score
Numeric 1–10 (10 = fully compliant). Pass threshold 8. Verdict: PASS, NEEDS REVISION, or FAIL.
State the theme audited against.

### Dimension Breakdown
Per dimension: name, score 1–10, violation count, severity classification (critical, major, minor).

### Violation Details
Per violation: line or section reference, quoted original text, violation type and dimension,
severity, suggested fix with corrected text.

### Summary
Total violations by severity, top 3 issues to fix first, estimated effort to reach compliance.

## Notes

- Auditing against the wrong theme produces confident nonsense. If the theme is ambiguous, say so and
  audit against both, reporting separately.
- This skill reports; it does not rewrite. For transformation use `algolia-algolialize`, which calls
  this skill to verify its own output.
