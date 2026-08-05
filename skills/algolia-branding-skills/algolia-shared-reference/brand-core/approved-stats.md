# Approved Algolia stats

`verified: 2026-08-05` · Sources: live algolia.com, Algolia press boilerplate (2026 releases)

**This file is the only place Algolia numbers live.** No skill may hardcode a statistic. If a number
is not on this list, it does not go in customer-facing output.

## The figures

| Figure | Use as | Source |
|---|---|---|
| 1.75 trillion searches per year | "powering 1.75 trillion searches a year" | Algolia press boilerplate, 2026 |
| 18,000+ businesses | "more than 18,000 businesses" | Algolia press boilerplate, 2026 |
| 150+ countries | "customers across 150+ countries" | algolia.com |
| 70+ data centers across 17 regions | infrastructure claims | algolia.com |

## Third-party proof points

| Claim | Detail | Source |
|---|---|---|
| Gartner Magic Quadrant Leader | Third consecutive year, June 2026 | Gartner MQ for Search and Product Discovery, 2026 |
| $3.1M NPV over three years | Economic impact of Algolia | Forrester Total Economic Impact study |
| 12 badges | Spring 2026 | G2 Spring 2026 Grid Reports |
| 12 medals across 12 categories | — | Paradigm B2B |

Gartner and Forrester claims carry attribution requirements. Name the analyst firm, the report, and
the year on every use. Never present an analyst finding as an Algolia claim.

## Retired — never emit

| Dead value | Replace with |
|---|---|
| 17,000+ customers | 18,000+ businesses |
| 1.7 trillion searches/year | 1.75 trillion searches per year |
| 30 billion records indexed | **nothing** — withdrawn, no current source found |

These three circulated in Algolia collateral through mid-2026 and are now wrong. `algolia-brand-check`
fails any artifact containing them.

## Rules

- Never round, never embellish, never combine two figures into a derived third.
- Every quantified claim carries its source within the same sentence or an adjacent citation.
- Customer results (conversion lift, revenue impact) are **not** on this list. Those require the
  customer's written approval and get attributed to that customer, never to Algolia generally.

## Keeping this current

Re-verify against the "About Algolia" boilerplate on any press release at
`algolia.com/about/news/` — that block is the canonical stat source and changes when the numbers do.
Update the `verified:` date above whenever you check, even if nothing changed.
