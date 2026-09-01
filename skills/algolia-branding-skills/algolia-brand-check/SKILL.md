---
name: algolia-brand-check
description: Scan content for Algolia brand compliance across 7 dimensions. Returns 1-10 score with fixes.
argument-hint: "[content or file path]"
---

# Algolia Brand Compliance Check

Audit any content artifact against current Algolia brand guidelines across seven dimensions. Produces
a scored report with line-level violations, suggested fixes, and a pass/fail verdict.

## Before you start: read the source of truth

**This skill holds no brand data of its own.** Read these first, every run:

- `../algolia-shared-reference/brand-core/design-system.md` — the canonical 2026 Xenon design system
- `../algolia-shared-reference/brand-core/tokens.json` — machine tokens with provenance + the retired list
- `../algolia-shared-reference/brand-core/tokens.md` — human token reference, type, shape
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
- (Theme is retired.) The 2026 Xenon rebrand collapsed the old marketing/deliverable split into ONE
  palette. Audit every artifact against the single Xenon palette in brand-core. A `--theme` argument
  is deprecated; note it and ignore it.

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
   Validate against the single 2026 Xenon palette (brand-core `tokens.json` / `colors_and_type.css`):
   - Primary brand `#0067F7` (Xenon Blue). Ink / dark surfaces `#000033` (Xenon 900).
   - Primaries: Purple `#8572F6`, Teal `#21C9C4`. Accents: Lime `#CEFF00`, Cyan `#5FFBFB`.
   - Backgrounds: White `#FFFFFF`, Light Gray `#F6F6F6`, Dark Blue `#000033`.
   - Neutral / hover / shadow ramp are `[DERIVED]` (see `colors_and_type.css`); do not flag a derived
     neutral as off-brand, but DO flag any retired value (see Automatic failures).
   - Sora only (300 / 400 / 600). Check logo clear space and minimum size; a recoloured logo is a
     violation (ship the official file; the token is Xenon but the 2022 logo file is #003DFF by design).
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
| `#003DFF` (Nebula Blue) | Retired 2026 primary. The primary is now Xenon `#0067F7` |
| `#5468FF`, `#8A4FFF` | Retired / fabricated purple. The real Xenon purple is `#8572F6` |
| `#021046`, `#0e1224` | Retired ink / dark. Use Xenon 900 `#000033` |
| `#00C29A`, `#00B6FF` | Retired teal / cyan. Use `#21C9C4` / `#5FFBFB` |
| `#00FF11`, `#123123`, `#BADA55` | Frontify template placeholders, never Algolia colours |
| Any product name on `product-names.md`'s retired list | Built from a stale source. Defer to that file — do NOT hardcode product names here (current names like Recommend, Crawler, NeuralSearch are valid) |

An artifact containing any of these cannot score above 5, and the verdict is FAIL.

## Output Sections

### Overall Score
Numeric 1–10 (10 = fully compliant). Pass threshold 8. Verdict: PASS, NEEDS REVISION, or FAIL.
Audited against the single 2026 Xenon palette (there is no longer a theme split).

### Dimension Breakdown
Per dimension: name, score 1–10, violation count, severity classification (critical, major, minor).

### Violation Details
Per violation: line or section reference, quoted original text, violation type and dimension,
severity, suggested fix with corrected text.

### Summary
Total violations by severity, top 3 issues to fix first, estimated effort to reach compliance.

## Notes

- There is one Xenon palette; the old marketing/deliverable theme split is retired. A `--theme` argument
  is deprecated — note it and ignore it, never branch behaviour on it.
- This skill reports; it does not rewrite. For transformation use `algolia-create` in rebrand mode, which calls
  this skill to verify its own output.
