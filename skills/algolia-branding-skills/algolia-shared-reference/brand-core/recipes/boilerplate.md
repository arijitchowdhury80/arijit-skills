# recipe: boilerplate — approved Algolia company description

output: the correct pre-approved company description, verbatim (a lookup, not a rewrite)
mode: lookup only — NEVER rewrite an approved description

## source files (read these; do not invent copy)
- approved descriptions: `../examples/approved-descriptions.md`
- messaging framework: `messaging-framework.md`
- case-study insert template: `../content-templates/case-study.md`

## available descriptions
| context | length | source |
|---|---|---|
| standard company description | long (~80 words) | messaging framework |
| short description | short (~30 words) | approved descriptions |
| social / bio description | 1–2 sentences | approved descriptions |
| case-study insert (standard) | long paragraph | case-study template |
| case-study insert (security-focused) | 2 paragraphs | case-study template |
| event / speaker bio | medium (~50 words) | approved descriptions |

## rules
- use the approved text VERBATIM; select the version that fits the requested context + length
- all approved stats (1.75 trillion searches, 18,000+ businesses, etc.) exactly as written (approved-stats.md)
- if adaptation for a specific vendor is needed, note: "Contact the Content Marketing Team for help adapting"
- if no exact match, return the closest approved description and note the adaptation needed

## output format
**Context:** [where this will be used]
**Version:** [which approved description]
[the verbatim approved description]
**Notes:** [adaptation guidance if any]

## then
no brand-check needed for a verbatim approved description (it is pre-approved source).
