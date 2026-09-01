# recipe: brief — Algolia campaign brief

output: campaign planning document aligning Marketing, ABX, and Sales
mode: create or rebrand
note: this is an orchestrating type — its content plan references other types as
`algolia-create --type <x>` (blog, email, landing, social, one-pager, deck), never as separate skills.

## inputs
campaign name + type (launch | ABX | demand-gen | content series | event | brand) ·
business objective · target audience / account criteria · budget range · timeline constraints ·
products to promote · existing assets to leverage

## structure (in order)
1. executive summary — one paragraph (what, why, who, when, expected outcome); readable in 30s by a VP
2. business objective — primary KPI + 1–2 supporting metrics tied to quarterly/annual goals; be specific
3. target audience — ICP (industry, size, titles, technographics, triggers); for ABX, account-list criteria + expected size; primary + secondary personas
4. key messages — three tiers: campaign headline (one benefit-driven sentence), 3–4 supporting value props with proof points, persona-specific angles
5. channel strategy — map messages to paid / owned / earned; budget allocation % per channel
6. content requirements — list every asset with format, owner, due date, status; reference creation via `algolia-create --type blog|email|landing|social|one-pager|deck`
7. ABX integration (if applicable) — account tiers (1:1, 1:few, 1:many), personalization depth per tier, sales-marketing handoff triggers, SDR talk-track bullets
8. timeline — week-by-week plan from approval to wrap; content deadlines, review cycles, launch, reporting
9. budget breakdown — paid media, content production, tools, events, contingency; cost-per-lead targets
10. success metrics — primary KPI, secondary metrics, reporting cadence, ROI framework
11. approval workflow — stakeholders + review deadlines (messaging=Brand, audience=Demand Gen, budget=Marketing Ops, timeline=PM)

## format-specific checks
every stat sourced (approved-stats.md) · messaging aligns with messaging-framework.md · content refs use algolia-create types

## then
engine runs algolia-brand-check on all campaign messaging; fix to ≥8.
