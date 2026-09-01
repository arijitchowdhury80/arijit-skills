# recipe: partner — Algolia co-marketing material

output: co-branded material for technology / SI / agency / marketplace partners
mode: create or rebrand
note: orchestrating type — the one-pager and landing forms are produced via
`algolia-create --type one-pager` / `--type landing` with dual branding, never as separate skills.

## inputs
partner name + type · material type (joint solution brief | integration overview | co-branded one-pager | partner landing page | co-sell battle card) ·
joint value proposition · integration details · shared customer examples · partner brand guidelines (if provided) · target audience

## structure (in order)
1. co-brand framework — logo hierarchy: Algolia-led = Algolia logo first/left/top; joint = both logos equal size side by side. Color usage: primary sections use Algolia brand colors; partner sections may use partner colors in designated zones; neutral sections use body color on white
2. joint value proposition — combined headline naming both companies + the joint outcome ("[Partner] + Algolia: [benefit]"); explain the integration multiplier
3. material content — by type:
   - joint solution brief (2–3 pages): cover (both logos + joint headline) · challenge · solution architecture · 3–4 joint benefits · customer proof · dual CTA
   - integration overview (1 page): architecture description · integration method (API/webhook/plugin/native) · data-flow summary · setup complexity · supported platforms/versions
   - co-branded one-pager: `algolia-create --type one-pager` with dual logos, joint key message, split content blocks, combined metrics, dual CTA
   - partner landing page: `algolia-create --type landing` with joint hero (both logos), combined value prop, integration feature blocks, shared proof, dual CTA
   - co-sell battle card (internal): joint ICP · discovery questions · competitive positioning · objection handling · pricing guidance notes · deal-registration process
4. messaging hierarchy — lead with the joint customer outcome, then each company's contribution; neither brand dominates; use "together" / "combined"
5. legal review notes — flag claims needing partner legal approval; note co-marketing agreement requirements; mark sections needing partner review

## output extras
co-brand specs (logo placement, color zones, font hierarchy) · partner review checklist · distribution plan (where hosted, enablement delivery)

## format-specific checks
Algolia-branded sections use only brand-core values · partner logo used per their guidelines · both brands compliant

## then
engine runs algolia-brand-check on the Algolia-branded sections; fix to ≥8.
