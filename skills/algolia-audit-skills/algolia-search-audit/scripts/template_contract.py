"""
template_contract.py — Machine-readable mapping of audit-data.json fields
to the JavaScript field names the SPA template actually reads.

WHY THIS EXISTS:
  The SPA template (index-template.html) is written in JavaScript and reads
  specific field names from the embedded AUDIT_DATA JSON. When a Python script
  writes the wrong field name (e.g. 'their_priority' instead of 'pain'), the
  template silently renders blank — there is no JS error, just empty output.

  This file is the authoritative contract between the Python data layer and
  the JavaScript rendering layer. Every field the template reads must appear here.
  The Pydantic schema (audit_data_schema.py) uses this contract to enforce aliases.

USAGE:
  from template_contract import TEMPLATE_FIELDS, verify_contract
  issues = verify_contract(audit_data_dict)

FORMAT:
  Each entry: { "json_path": "...", "template_reads": "...", "template_section": "...", "required": bool }
  json_path    = dot-separated path in audit-data.json
  template_reads = exact JS expression the template uses (e.g. `p.pain || p.their_priority`)
  template_section = which SPA section renders it
  required     = whether a blank value causes a visibly broken section
"""
from __future__ import annotations
from typing import Any


TEMPLATE_FIELDS: list[dict[str, Any]] = [

    # ── ABX Sequence ────────────────────────────────────────────────────────
    {
        "json_path":        "abx_sequence.touches[N].body",
        "template_reads":   "t.body",
        "template_section": "Sales Actions → Outreach Plan",
        "required":         True,
        "notes":            "For email/linkedin: clean sendable copy. For video: short delivery email. "
                            "Source notes must NOT appear here.",
    },
    {
        "json_path":        "abx_sequence.touches[N].video_script",
        "template_reads":   "t.video_script",
        "template_section": "Sales Actions → Outreach Plan → Loom Script panel",
        "required":         True,
        "channel":          "video",
        "notes":            "ONLY read for channel='video'. t.body is NOT used for the script. "
                            "If this field is missing, the Loom script panel is blank.",
    },
    {
        "json_path":        "abx_sequence.touches[N].subject",
        "template_reads":   "t.subject",
        "template_section": "Sales Actions → Outreach Plan",
        "required":         False,
    },
    {
        "json_path":        "abx_sequence.contacts[N].id",
        "template_reads":   "c.id  (used in contactMap lookup)",
        "template_section": "Sales Actions → Buying Committee + Outreach Plan",
        "required":         True,
        "notes":            "Without id, the contact cannot be looked up in the contactMap — "
                            "touch target labels render as 'All contacts' regardless of target field.",
    },

    # ── ICP Mapping / Discovery Q Cards ──────────────────────────────────────
    {
        "json_path":        "icp_mapping.priority_to_product[N].their_priority",
        "template_reads":   "p.their_priority",
        "template_section": "Sales Actions → Discovery Q card label (Q1·, Q2·...)",
        "required":         True,
        "notes":            "Also accepted: p.pain (Solution Map). Both must be set. "
                            "Pydantic auto-populates their_priority from pain if missing.",
    },
    {
        "json_path":        "icp_mapping.priority_to_product[N].pain",
        "template_reads":   "p.pain",
        "template_section": "Business Case → Solution Map (Pain column)",
        "required":         True,
        "notes":            "Different template path from their_priority. Both needed.",
    },
    {
        "json_path":        "icp_mapping.priority_to_product[N].discovery_question",
        "template_reads":   "p.discovery_question",
        "template_section": "Sales Actions → Discovery Q card body",
        "required":         True,
        "notes":            "The actual question text shown to the BDR.",
    },
    {
        "json_path":        "icp_mapping.priority_to_product[N].algolia_solution",
        "template_reads":   "p.algolia_solution  (split on '—', takes first part)",
        "template_section": "Sales Actions → Discovery Q card → Algolia arrow",
        "required":         True,
        "notes":            "Also accepted: p.product (Solution Map). Both must be set.",
    },
    {
        "json_path":        "icp_mapping.priority_to_product[N].product",
        "template_reads":   "p.product",
        "template_section": "Business Case → Solution Map (Algolia Product column)",
        "required":         True,
    },
    {
        "json_path":        "icp_mapping.priority_to_product[N].evidence",
        "template_reads":   "p.evidence || p.exact_quote",
        "template_section": "Sales Actions → Discovery Q card → Citation block (italic quote)",
        "required":         False,
        "notes":            "Renders inline citation. Without this, BDR has no proof behind the question.",
    },
    {
        "json_path":        "icp_mapping.priority_to_product[N].proof_url",
        "template_reads":   "p.proof_url",
        "template_section": "Sales Actions → Discovery Q card citation link + Solution Map Proof column",
        "required":         False,
        "notes":            "Required when proof_company is set — renders clickable link.",
    },
    {
        "json_path":        "icp_mapping.priority_to_product[N].proof_company",
        "template_reads":   "p.proof_company",
        "template_section": "Business Case → Solution Map (Proof column company name)",
        "required":         False,
    },
    {
        "json_path":        "icp_mapping.priority_to_product[N].proof_result",
        "template_reads":   "p.proof_result",
        "template_section": "Business Case → Solution Map (Proof column result metric)",
        "required":         False,
    },

    # ── Executives ────────────────────────────────────────────────────────────
    {
        "json_path":        "executives[N].quote",
        "template_reads":   "e.quote",
        "template_section": "Research → Executive Quotes section",
        "required":         True,
    },
    {
        "json_path":        "executives[N].quote_source",
        "template_reads":   "e.quote_source",
        "template_section": "Research → Executive Quotes → citation link",
        "required":         True,
        "notes":            "Also accepted: e.source_url. Without this, no citation link renders.",
    },

    # ── Intelligence Signals ──────────────────────────────────────────────────
    {
        "json_path":        "intelligence_signals[N].title",
        "template_reads":   "s.title || s.badge_label || s.signal",
        "template_section": "Research → Signals section + Overview → Why Now",
        "required":         True,
        "notes":            "Accepts any of: title, badge_label, signal. "
                            "generate-audit-data.py writes 'signal', manual writes use 'title'.",
    },
    {
        "json_path":        "intelligence_signals[N].source_url",
        "template_reads":   "s.source_url",
        "template_section": "Research → Signals → source link",
        "required":         False,
        "notes":            "Required when detail/signal content > 50 chars per citation rule.",
    },

    # ── Findings (Browser Audit) ──────────────────────────────────────────────
    {
        "json_path":        "findings[N].algolia_case_study_company",
        "template_reads":   "f.algolia_case_study_company",
        "template_section": "Search Audit → Finding cards + Business Case → Solution Map table",
        "required":         False,
        "notes":            "Required alongside algolia_case_study_url when citing proof.",
    },
    {
        "json_path":        "findings[N].algolia_case_study_url",
        "template_reads":   "f.algolia_case_study_url",
        "template_section": "Search Audit + Solution Map → Proof column link",
        "required":         False,
        "notes":            "Required when algolia_case_study_company is set.",
    },

    # ── AE Fields (Overview → WHAT DO I DO NEXT?) ─────────────────────────────
    {
        "json_path":        "ae_fields.urgency / ae_fields.urgency_level / ae_fields.urgency_label",
        "template_reads":   "ae.urgency_label || ae.urgency || ae.urgency_level.split('—')[0]",
        "template_section": "Overview → WHAT DO I DO NEXT? urgency dot label",
        "required":         False,
        "notes":            "BA writes 'urgency' (e.g. 'CRITICAL'). LBP writes 'urgency_level' (e.g. 'HIGH — 3 signals...'). "
                            "Template extracts first word before '—'. urgency_label is the canonical field name.",
    },
    {
        "json_path":        "ae_fields.next_step_action / ae_fields.cta / ae_fields.urgency_reason",
        "template_reads":   "ae.next_step_action || ae.cta || ae.urgency_reason",
        "template_section": "Overview → WHAT DO I DO NEXT? action text",
        "required":         False,
        "notes":            "next_step_action is canonical. Falls back to cta (recommended for 'what to do') or urgency_reason.",
    },

    # ── Score ─────────────────────────────────────────────────────────────────
    {
        "json_path":        "score.breakdown",
        "template_reads":   "score.breakdown.{canonical_key}",
        "template_section": "Overview → Score + Search Audit → Heatmap",
        "required":         True,
        "notes":            "Only 10 canonical keys accepted. Wrong keys = blank sections. "
                            "Keys: latency, typo_tolerance, query_suggestions_empty_state, "
                            "intent_detection, merchandising_consistency, content_commerce_ux, "
                            "semantic_nlp_search, dynamic_facets_personalization, "
                            "recommendations_merchandising, search_intelligence",
    },
]


def verify_contract(data: dict[str, Any]) -> list[str]:
    """
    Spot-check audit-data.json against the template contract.
    Returns a list of violation strings (empty = all good).

    Not a full structural check (use audit_data_schema.py for that).
    Focuses on the template-specific field name requirements that Pydantic
    can't catch because the Pydantic model uses Python aliases.
    """
    issues: list[str] = []

    # Check ICP cards have both aliases set
    ptp = (data.get("icp_mapping") or {}).get("priority_to_product") or []
    for i, p in enumerate(ptp):
        if not p.get("their_priority") and not p.get("pain"):
            issues.append(
                f"icp[{i}]: neither 'their_priority' nor 'pain' set — "
                f"Discovery Q label will be blank (template reads p.their_priority)"
            )
        if not p.get("algolia_solution") and not p.get("product"):
            issues.append(
                f"icp[{i}]: neither 'algolia_solution' nor 'product' set — "
                f"Discovery Q product arrow will be blank"
            )

    # Check video touches have video_script
    touches = (data.get("abx_sequence") or {}).get("touches") or []
    for t in touches:
        if t.get("channel") == "video" and not t.get("video_script"):
            issues.append(
                f"abx touch {t.get('touch')}: channel=video but video_script is missing — "
                f"Loom script panel will be blank (template reads t.video_script, NOT t.body)"
            )

    # Check score breakdown keys
    breakdown = (data.get("score") or {}).get("breakdown") or {}
    valid_keys = {
        "latency", "typo_tolerance", "query_suggestions_empty_state",
        "intent_detection", "merchandising_consistency", "content_commerce_ux",
        "semantic_nlp_search", "dynamic_facets_personalization",
        "recommendations_merchandising", "search_intelligence",
    }
    bad_keys = set(breakdown.keys()) - valid_keys
    if bad_keys:
        issues.append(
            f"score.breakdown has invalid keys: {bad_keys} — "
            f"template hardcodes only the 10 canonical keys, wrong keys render as blank"
        )

    return issues


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 2:
        print("Usage: python3 template_contract.py <path-to-audit-data.json>")
        print("\nKnown template field contracts:")
        for f in TEMPLATE_FIELDS:
            req = "REQUIRED" if f.get("required") else "optional"
            print(f"  [{req}] {f['json_path']} → {f['template_reads']}  ({f['template_section']})")
        sys.exit(0)

    with open(sys.argv[1]) as fh:
        data = json.load(fh)
    issues = verify_contract(data)
    if issues:
        print(f"❌ {len(issues)} template contract violation(s):")
        for issue in issues:
            print(f"  {issue}")
        sys.exit(1)
    else:
        print("✅ Template contract verified — all field names correct")
