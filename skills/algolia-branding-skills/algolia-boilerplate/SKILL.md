---
name: algolia-boilerplate
description: Return the correct pre-approved Algolia company description for any context — press releases, case studies, event bios, partner pages, or proposals.
user-invocable: true
allowed-tools: Read, Grep
argument-hint: "[context: press-release|case-study|event|partner|proposal|social] [length: short|medium|long]"
---

# Algolia boilerplate selector

Return the right pre-approved Algolia company description for any use case.

## Reference files

- [Approved descriptions](../algolia-shared-reference/examples/approved-descriptions.md)
- [Messaging framework](../algolia-shared-reference/brand-core/messaging-framework.md)
- [Case study template](../algolia-shared-reference/content-templates/case-study.md)

## Available descriptions

| Context | Length | Source |
|---------|--------|--------|
| Standard company description | Long (~80 words) | Messaging framework |
| Short description | Short (~30 words) | Approved descriptions |
| Social/bio description | 1-2 sentences | Approved descriptions |
| Case study insert (standard) | Long paragraph | Case study template |
| Case study insert (security-focused) | 2 paragraphs | Case study template |
| Event/speaker bio | Medium (~50 words) | Approved descriptions |

## Rules
- **Never rewrite** the approved descriptions — use them verbatim
- Select the version that best fits the requested context and length
- For case studies, include the standard or security-focused insert as specified
- If the context requires adaptation, note: "Contact the Content Marketing Team for help adapting for specific vendors"
- All approved stats (1.75 trillion searches, 18,000+ businesses, etc.) must be used exactly as written
- If no exact match exists, return the closest approved description and note any adaptation needed

## Output format

```
**Context:** [where this will be used]
**Version:** [which approved description]

---

[The verbatim approved description]

---

**Notes:** [Any adaptation guidance if needed]
```

Get boilerplate: $ARGUMENTS
