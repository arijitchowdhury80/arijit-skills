#!/usr/bin/env python3
"""
audit-health-check.py — DEEP field-level validation of all audit JSONs.

Checks every meaningful sub-field inside every section.
Reports actual values, empty strings, null, missing keys.
Does NOT assume a key existing means it has real data.

Usage:
  python3 audit-health-check.py [--slug <slug>] [--report <file.json>]
"""

import json, os, sys
from pathlib import Path
from datetime import datetime

VERCEL_REPO = Path.home() / "algolia-arian-v2"
SCRIPTS_DIR = Path(__file__).parent
AUDIT_DIR_ENV = os.environ.get("ALGOLIA_AUDIT_DIR", "")
AUDIT_DIR = Path(AUDIT_DIR_ENV) if AUDIT_DIR_ENV else None

SLUG_TO_FOLDER = {
    "autozone":       "Autozone",
    "brooks-running": "Brooks Running",
    "costco":         "Costco",
    "dsw":            "DSW",
    "llbean":         "LLBean",
    "sallybeauty":    "Sally Beauty",
    "savage-x-fenty": "Savage X Fenty",
    "tapestry":       "Tapestry",
    "therealreal":    "Therealreal",
}

# ── Value helper ────────────────────────────────────────────────────────────

def val_status(v, label=""):
    """Return (ok, display) for any value."""
    if v is None:
        return False, "NULL"
    if isinstance(v, str):
        stripped = v.strip()
        if stripped == "" or stripped == "—" or stripped == "null":
            return False, f"EMPTY STRING: '{v}'"
        return True, stripped[:80]
    if isinstance(v, list):
        if len(v) == 0:
            return False, "EMPTY LIST"
        return True, f"{len(v)} items"
    if isinstance(v, dict):
        if len(v) == 0:
            return False, "EMPTY DICT"
        return True, f"{len(v)} keys"
    if isinstance(v, (int, float)):
        if v == 0:
            return False, "ZERO (0)"
        return True, str(v)
    return True, str(v)[:80]


def field(data, *path, label=None):
    """Drill into nested path, return (ok, path_str, display_val)."""
    path_str = " → ".join(str(p) for p in path)
    obj = data
    for key in path:
        if isinstance(obj, dict):
            if key not in obj:
                return False, path_str, "KEY MISSING"
            obj = obj[key]
        elif isinstance(obj, list):
            if not isinstance(key, int) or key >= len(obj):
                return False, path_str, "INDEX OUT OF RANGE"
            obj = obj[key]
        else:
            return False, path_str, f"CANNOT DRILL (type={type(obj).__name__})"
    ok, display = val_status(obj)
    return ok, path_str, display


def check_list_items(lst, required_fields, section_name):
    """For a list of dicts, check each item has required fields with real values."""
    issues = []
    for i, item in enumerate(lst):
        if not isinstance(item, dict):
            issues.append(f"  item[{i}] is not a dict: {type(item).__name__}")
            continue
        for f in required_fields:
            ok, _, display = field(item, f)
            if not ok:
                issues.append(f"  [{i}].{f}: {display}")
    return issues


# ── Section validators ──────────────────────────────────────────────────────

def validate_meta(data):
    checks = []
    for path in [["meta", "company"], ["meta", "domain"], ["meta", "audit_date"]]:
        ok, p, v = field(data, *path)
        checks.append((ok, p, v))
    return checks


def validate_company_snapshot(data):
    checks = []
    snap = data.get("company_snapshot", {})
    if not isinstance(snap, dict) or len(snap) == 0:
        return [(False, "company_snapshot", "MISSING OR EMPTY")]

    for f in ["industry", "hq", "employees", "founded"]:
        ok, p, v = field(snap, f)
        checks.append((ok, f"company_snapshot.{f}", v))

    # Check revenue field (various schema versions)
    rev_found = False
    for rev_f in ["revenue", "revenue_est", "revenue_fy2025", "total_revenue"]:
        if snap.get(rev_f):
            checks.append((True, f"company_snapshot.{rev_f}", str(snap[rev_f])[:60]))
            rev_found = True
            break
    if not rev_found:
        checks.append((False, "company_snapshot.revenue (any)", "NO REVENUE FIELD FOUND"))

    return checks


def validate_executives(data):
    execs = data.get("executives", [])
    if not execs:
        return [(False, "executives", "EMPTY LIST — no executives")]
    checks = [(True, "executives", f"{len(execs)} executives")]
    issues = check_list_items(execs, ["name", "title"], "executives")
    for issue in issues:
        checks.append((False, issue, ""))
    # Check at least one has a quote
    with_quotes = [e for e in execs if e.get("quote")]
    if not with_quotes:
        checks.append((False, "executives[].quote", "NO EXECUTIVE HAS A QUOTE"))
    else:
        checks.append((True, "executives[].quote", f"{len(with_quotes)}/{len(execs)} have quotes"))
    return checks


def validate_tech_stack(data):
    ts = data.get("tech_stack", {})
    if not isinstance(ts, dict) or len(ts) == 0:
        return [(False, "tech_stack", "MISSING OR EMPTY")]

    checks = []
    # Search vendor — check multiple possible field names
    vendor_found = False
    for vf in ["current_search_vendor", "search_vendor", "search_platform"]:
        v = ts.get(vf)
        if v and str(v).strip() not in ["", "—", "null", "Unknown"]:
            checks.append((True, f"tech_stack.{vf}", str(v)[:60]))
            vendor_found = True
            break
    if not vendor_found:
        checks.append((False, "tech_stack.current_search_vendor", "MISSING — search vendor unknown"))

    for f in ["ecommerce_platform", "analytics"]:
        v = ts.get(f)
        if v:
            checks.append((True, f"tech_stack.{f}", str(v)[:60]))
        else:
            checks.append((False, f"tech_stack.{f}", "MISSING"))

    full_list = ts.get("full_list", [])
    checks.append((len(full_list) > 0, "tech_stack.full_list", f"{len(full_list)} technologies detected"))

    return checks


def validate_traffic(data):
    t = data.get("traffic", {})
    if not isinstance(t, dict) or len(t) == 0:
        return [(False, "traffic", "MISSING OR EMPTY")]

    checks = []

    # Core metrics
    for f in ["monthly_visits", "bounce_rate", "pages_per_visit", "visit_duration"]:
        ok, _, v = field(t, f)
        checks.append((ok, f"traffic.{f}", v))

    # Top channels (distribution)
    channels = t.get("top_channels", [])
    if not channels:
        checks.append((False, "traffic.top_channels", "MISSING — no channel distribution"))
    else:
        checks.append((True, "traffic.top_channels", f"{len(channels)} channels"))
        # Check channels have source and share
        for i, c in enumerate(channels[:3]):
            if not isinstance(c, dict) or not c.get("source") or not c.get("share"):
                checks.append((False, f"traffic.top_channels[{i}]", f"missing source/share: {c}"))

    # Device share
    device = t.get("device_share", {})
    if not device or not device.get("mobile"):
        checks.append((False, "traffic.device_share", "MISSING — no mobile/desktop split"))
    else:
        checks.append((True, "traffic.device_share", f"mobile={device.get('mobile')}, desktop={device.get('desktop')}"))

    # Demographics
    demo = t.get("demographics", {})
    if not demo or len(demo) == 0:
        checks.append((False, "traffic.demographics", "MISSING — no demographic data"))
    else:
        checks.append((True, "traffic.demographics", f"{len(demo)} demographic fields"))

    # Source citation
    src = t.get("source") or t.get("source_url")
    checks.append((bool(src), "traffic.source", str(src)[:60] if src else "MISSING"))

    return checks


def validate_financials(data):
    fin = data.get("financials", {})
    if not isinstance(fin, dict) or len(fin) == 0:
        return [(False, "financials", "MISSING OR EMPTY")]

    checks = []

    # Revenue data — 3yr array or individual year fields
    rev3y = fin.get("revenue_3y", [])
    if rev3y and len(rev3y) > 0:
        checks.append((True, "financials.revenue_3y", f"{len(rev3y)} years of data"))
    else:
        # Check individual year fields
        year_fields = {k: v for k, v in fin.items() if "revenue_fy" in k.lower() and v}
        if year_fields:
            checks.append((True, "financials.revenue (year fields)", str(year_fields)[:100]))
        else:
            checks.append((False, "financials.revenue", "NO REVENUE DATA (no revenue_3y or revenue_fyXXXX)"))

    # ROI data
    roi_found = False
    for roi_f in ["roi_conservative", "roi_moderate", "search_roi_est", "roi_scenarios"]:
        v = fin.get(roi_f)
        if v:
            checks.append((True, f"financials.{roi_f}", str(v)[:60]))
            roi_found = True
            break
    if not roi_found:
        checks.append((False, "financials.roi", "MISSING — no ROI estimate or scenarios"))

    # Ecommerce revenue
    ecom = fin.get("ecommerce_revenue") or fin.get("total_digital_revenue")
    checks.append((bool(ecom), "financials.ecommerce_revenue", str(ecom)[:60] if ecom else "MISSING"))

    return checks


def validate_intelligence_signals(data):
    sigs = data.get("intelligence_signals", [])
    if not sigs:
        return [(False, "intelligence_signals", "EMPTY — no signals at all")]

    checks = [(True, "intelligence_signals", f"{len(sigs)} signals total")]

    types = {}
    for s in sigs:
        t = s.get("type", "unknown")
        types[t] = types.get(t, 0) + 1
    checks.append((True, "intelligence_signals.types", str(types)))

    # Check signals have content
    no_content = [s.get("type","?") for s in sigs
                  if not (s.get("badge_label") or s.get("title") or s.get("text") or s.get("body") or s.get("quote"))]
    if no_content:
        checks.append((False, "intelligence_signals[].content", f"{len(no_content)} signals have no badge_label/title/text/body/quote"))
    else:
        checks.append((True, "intelligence_signals[].content", "all signals have display content"))

    return checks


def validate_competitors(data):
    comps = data.get("competitors", [])
    if not comps:
        return [(False, "competitors", "EMPTY LIST")]

    checks = [(True, "competitors", f"{len(comps)} competitors")]
    issues = check_list_items(comps, ["name", "search_stack"], "competitors")
    for issue in issues:
        checks.append((False, issue, ""))

    # Check at least one has search vendor confirmation
    confirmed = [c for c in comps if c.get("search_stack") and c.get("source_url")]
    checks.append((len(confirmed) > 0, "competitors[].source_url", f"{len(confirmed)}/{len(comps)} have source URLs"))

    return checks


def validate_partner_intel(data):
    pi = data.get("partner_intel", {})
    if not pi or len(pi) == 0:
        return [(False, "partner_intel", "MISSING OR EMPTY — partner intelligence not collected")]

    checks = []
    tech = pi.get("tech_partners", [])
    si = pi.get("si_partners", [])
    checks.append((len(tech) > 0, "partner_intel.tech_partners", f"{len(tech)} tech partners" if tech else "EMPTY"))
    checks.append((len(si) > 0 or pi.get("si_partners_note"), "partner_intel.si_partners",
                   f"{len(si)} SI partners" if si else (pi.get("si_partners_note", "EMPTY"))))

    rec = pi.get("co_sell_recommendation") or pi.get("immediate_action")
    checks.append((bool(rec), "partner_intel.co_sell_recommendation", str(rec)[:80] if rec else "MISSING"))

    return checks


def validate_hiring(data):
    hir = data.get("hiring", {})
    if not hir or len(hir) == 0:
        return [(False, "hiring", "MISSING OR EMPTY")]

    checks = []
    bc = hir.get("buying_committee")
    if bc is None:
        checks.append((False, "hiring.buying_committee", "MISSING"))
    elif isinstance(bc, list) and len(bc) > 0:
        checks.append((True, "hiring.buying_committee", f"{len(bc)} committee members (array)"))
    elif isinstance(bc, dict) and len(bc) > 0:
        checks.append((True, "hiring.buying_committee", f"object with keys: {list(bc.keys())[:4]}"))
    else:
        checks.append((False, "hiring.buying_committee", "EMPTY"))

    roles = hir.get("top_icp_roles", [])
    checks.append((len(roles) > 0, "hiring.top_icp_roles", f"{len(roles)} ICP roles" if roles else "EMPTY"))

    # Also check intelligence_signals for hiring_signal type
    sigs = data.get("intelligence_signals", [])
    hiring_sigs = [s for s in sigs if s.get("type") in ("hiring", "hiring_signal")]
    checks.append((len(hiring_sigs) > 0, "intelligence_signals[hiring]",
                   f"{len(hiring_sigs)} hiring signals" if hiring_sigs else "NO HIRING SIGNALS IN INTELLIGENCE"))

    return checks


def validate_score(data):
    sc = data.get("score", {})
    if not sc:
        return [(False, "score", "MISSING")]

    checks = []
    overall = sc.get("overall")
    checks.append((overall is not None and overall != 0, "score.overall", str(overall) if overall else "MISSING/ZERO"))

    bd = sc.get("breakdown", {})
    if not bd or len(bd) == 0:
        checks.append((False, "score.breakdown", "EMPTY — no per-area scores"))
    else:
        checks.append((True, "score.breakdown", f"{len(bd)} areas scored"))
        # Check 10 canonical areas
        canonical = ["latency", "typo_tolerance", "query_suggestions_empty_state", "intent_detection",
                     "merchandising_consistency", "content_commerce_ux", "semantic_nlp_search",
                     "dynamic_facets_personalization", "recommendations_merchandising", "search_intelligence"]
        missing_areas = [a for a in canonical if a not in bd]
        if missing_areas:
            checks.append((False, "score.breakdown.areas", f"MISSING {len(missing_areas)} canonical areas: {missing_areas}"))

    verdict = sc.get("verdict")
    checks.append((bool(verdict), "score.verdict", str(verdict)[:60] if verdict else "MISSING"))

    return checks


def validate_findings(data):
    findings = data.get("findings", [])
    if not findings:
        return [(False, "findings", "EMPTY — no findings at all")]

    checks = [(True, "findings", f"{len(findings)} findings")]

    # Required fields per finding
    required = ["id", "severity", "category", "tested_query", "expected_behavior",
                "actual_behavior", "algolia_solution"]

    for i, f in enumerate(findings):
        fid = f.get("id", f"[{i}]")
        for rf in required:
            ok, _, v = field(f, rf)
            if not ok:
                checks.append((False, f"findings[{fid}].{rf}", v))

        # Screenshot
        if not f.get("screenshot_file"):
            checks.append((False, f"findings[{fid}].screenshot_file", "MISSING"))

        # Case study
        if not f.get("algolia_case_study_url"):
            sev = (f.get("severity") or "").lower()
            if sev in ("critical", "high", "moderate", "medium"):
                checks.append((False, f"findings[{fid}].algolia_case_study_url", "MISSING on gap finding"))

        # Severity normalisation check
        sev = (f.get("severity") or "").strip()
        valid_sevs = {"critical", "high", "moderate", "medium", "positive", "low"}
        if sev.lower() not in valid_sevs:
            checks.append((False, f"findings[{fid}].severity", f"INVALID VALUE: '{sev}'"))

    # Summarise
    missing_screenshots = sum(1 for f in findings if not f.get("screenshot_file"))
    missing_cases = sum(1 for f in findings if not f.get("algolia_case_study_url")
                        and (f.get("severity") or "").lower() in ("critical","high","moderate","medium"))
    if missing_screenshots:
        checks.append((False, "findings[].screenshot_file SUMMARY",
                        f"{missing_screenshots}/{len(findings)} findings have no screenshot"))
    if missing_cases:
        checks.append((False, "findings[].algolia_case_study_url SUMMARY",
                        f"{missing_cases} gap findings have no case study URL"))

    return checks


def validate_competitive_synthesis(data):
    cs = data.get("competitive_synthesis", {})
    ga = data.get("golden_angle", {})

    checks = []

    if not cs or len(cs) == 0:
        checks.append((False, "competitive_synthesis", "MISSING OR EMPTY"))
    else:
        checks.append((True, "competitive_synthesis", f"{len(cs)} keys"))
        # Positioning matrix
        matrix = cs.get("positioning_matrix") or cs.get("matrix", [])
        checks.append((len(matrix) > 0 if isinstance(matrix, list) else bool(matrix),
                        "competitive_synthesis.positioning_matrix",
                        f"{len(matrix)} rows" if isinstance(matrix, list) else str(matrix)[:60]))
        # Tiers
        tiers = cs.get("competitor_tiers") or cs.get("tiers", [])
        checks.append((len(tiers) > 0 if isinstance(tiers, list) else bool(tiers),
                        "competitive_synthesis.competitor_tiers",
                        f"{len(tiers)} tiers" if isinstance(tiers, list) else str(tiers)[:60]))

    if not ga or len(ga) == 0:
        checks.append((False, "golden_angle", "MISSING — no golden angle analysis"))
    else:
        checks.append((True, "golden_angle", f"{len(ga)} keys"))
        tt = ga.get("talk_track")
        checks.append((bool(tt), "golden_angle.talk_track", str(tt)[:80] if tt else "MISSING"))

    return checks


def validate_strategic_angles(data):
    angles = data.get("strategic_angles", [])
    if not angles:
        return [(False, "strategic_angles", "EMPTY LIST")]
    checks = [(True, "strategic_angles", f"{len(angles)} angles")]
    issues = check_list_items(angles, ["angle", "hook"], "strategic_angles")
    for issue in issues:
        checks.append((False, issue, ""))
    return checks


def validate_abx_sequence(data):
    abx = data.get("abx_sequence")
    if not abx:
        return [(False, "abx_sequence", "MISSING")]

    checks = []
    if isinstance(abx, list):
        checks.append((len(abx) > 0, "abx_sequence", f"{len(abx)} sequence items"))
    elif isinstance(abx, dict):
        touches = abx.get("touches", [])
        checks.append((len(touches) > 0, "abx_sequence.touches", f"{len(touches)} touch points"))
        total = abx.get("total_touches")
        checks.append((bool(total), "abx_sequence.total_touches", str(total) if total else "MISSING"))
        seq_type = abx.get("sequence_type")
        checks.append((bool(seq_type), "abx_sequence.sequence_type", str(seq_type) if seq_type else "MISSING"))
    return checks


def validate_ae_fields(data):
    ae = data.get("ae_fields", {})
    if not ae or len(ae) == 0:
        return [(False, "ae_fields", "MISSING OR EMPTY")]

    checks = []
    for f in ["urgency_trigger", "recommended_approach", "icp_fit"]:
        ok, _, v = field(ae, f)
        checks.append((ok, f"ae_fields.{f}", v))
    return checks


def validate_icp_mapping(data):
    icp = data.get("icp_mapping")
    if icp is None or (hasattr(icp, '__len__') and len(icp) == 0):
        return [(False, "icp_mapping", "MISSING OR EMPTY")]
    if isinstance(icp, list):
        return [(True, "icp_mapping", f"list with {len(icp)} items")]
    if isinstance(icp, dict):
        checks = [(True, "icp_mapping", f"{len(icp)} keys")]
        anchor = icp.get("anchor_lines", [])
        checks.append((len(anchor) > 0, "icp_mapping.anchor_lines", f"{len(anchor)} anchor lines" if anchor else "EMPTY"))
        return checks
    return [(True, "icp_mapping", str(icp)[:60])]


def validate_bibliography(data):
    bib = data.get("bibliography", [])
    if not bib:
        return [(False, "bibliography", "EMPTY — no sources listed")]
    checks = [(True, "bibliography", f"{len(bib)} sources")]
    # Check sources have URL
    no_url = [b.get("id") or b.get("n") or "?" for b in bib if not b.get("url")]
    if no_url:
        checks.append((False, "bibliography[].url",
                        f"{len(no_url)} sources have no URL"))
    return checks


def validate_case_studies(data):
    cs = data.get("case_studies", [])
    # Also check per-finding case studies as fallback
    findings = data.get("findings", [])
    finding_cases = [f for f in findings if f.get("algolia_case_study_url")]

    if not cs and not finding_cases:
        return [(False, "case_studies", "EMPTY — no case studies in case_studies[] or findings[]")]

    checks = []
    if cs:
        checks.append((True, "case_studies", f"{len(cs)} top-level case studies"))
    else:
        checks.append((False, "case_studies (top-level)", "empty — using per-finding fallback"))
        checks.append((True, "case_studies (from findings)",
                        f"{len(finding_cases)} findings have case study URLs"))
    return checks


def validate_partner_and_contacts(data):
    """Combined check for partner intel and buying committee contacts."""
    checks = []

    # Buying committee — can be in hiring.buying_committee or icp_mapping
    hir = data.get("hiring", {})
    bc = hir.get("buying_committee") if isinstance(hir, dict) else None
    icp = data.get("icp_mapping", {})

    if bc is None:
        checks.append((False, "contacts/buying_committee", "NOT FOUND in hiring.buying_committee"))
    elif isinstance(bc, list) and len(bc) > 0:
        checks.append((True, "contacts/buying_committee", f"{len(bc)} identified contacts"))
        # Check each contact has name and title
        for i, c in enumerate(bc):
            if not isinstance(c, dict):
                continue
            name = c.get("name", "")
            title = c.get("title", "")
            if not name or "TBD" in name or "Unknown" in name:
                checks.append((False, f"contacts[{i}].name", f"Unidentified: '{name}'"))
    elif isinstance(bc, dict):
        # Old schema: {economic_buyer: "...", technical_buyer: "..."}
        filled = {k: v for k, v in bc.items() if v and "TBD" not in str(v) and "Unknown" not in str(v)}
        checks.append((len(filled) > 0, "contacts/buying_committee",
                        f"object with {len(filled)} identified roles" if filled else "ALL ROLES TBD/Unknown"))

    return checks


# ── Master validator ────────────────────────────────────────────────────────

VALIDATORS = [
    ("Meta",                    validate_meta),
    ("Company Snapshot",        validate_company_snapshot),
    ("Executives",              validate_executives),
    ("Tech Stack",              validate_tech_stack),
    ("Traffic (incl. demographics, channels, devices)", validate_traffic),
    ("Financials (revenue, ROI, ecommerce)", validate_financials),
    ("Intelligence Signals",    validate_intelligence_signals),
    ("Competitors",             validate_competitors),
    ("Partner Intelligence",    validate_partner_intel),
    ("Hiring + Buying Committee", validate_hiring),
    ("Contacts",                validate_partner_and_contacts),
    ("Score (10 areas)",        validate_score),
    ("Findings (with screenshots + case studies)", validate_findings),
    ("Competitive Synthesis + Golden Angle", validate_competitive_synthesis),
    ("Strategic Angles",        validate_strategic_angles),
    ("ABX Sequence",            validate_abx_sequence),
    ("AE Fields",               validate_ae_fields),
    ("ICP Mapping",             validate_icp_mapping),
    ("Bibliography",            validate_bibliography),
    ("Case Studies",            validate_case_studies),
]


def run_deep_check(slugs):
    results = {}
    for slug in slugs:
        json_path = VERCEL_REPO / f"{slug}-audit-data.json"
        if not json_path.exists():
            results[slug] = {"error": f"JSON not found: {json_path}"}
            continue
        with open(json_path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                results[slug] = {"error": f"JSON parse error: {e}"}
                continue

        company = data.get("meta", {}).get("company", slug)
        slug_result = {
            "company": company,
            "sections": {},
            "totals": {"ok": 0, "fail": 0},
        }

        for section_name, validator in VALIDATORS:
            checks = validator(data)
            ok_count = sum(1 for ok, _, _ in checks if ok)
            fail_count = sum(1 for ok, _, _ in checks if not ok)
            failures = [(path, val) for ok, path, val in checks if not ok]
            slug_result["sections"][section_name] = {
                "checks_ok": ok_count,
                "checks_fail": fail_count,
                "failures": failures,
            }
            slug_result["totals"]["ok"] += ok_count
            slug_result["totals"]["fail"] += fail_count

        results[slug] = slug_result

    return results


def print_deep_report(results):
    print("\n" + "="*90)
    print("  ALGOLIA AUDIT DEEP HEALTH CHECK")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*90)

    grand_ok = grand_fail = 0

    for slug, result in sorted(results.items()):
        if "error" in result:
            print(f"\n🔴 {slug}: {result['error']}")
            continue

        t = result["totals"]
        grand_ok += t["ok"]; grand_fail += t["fail"]
        pct = int(100 * t["ok"] / (t["ok"] + t["fail"])) if (t["ok"] + t["fail"]) > 0 else 0
        icon = "✅" if t["fail"] == 0 else "❌" if pct < 60 else "⚠️"

        print(f"\n{icon} {result['company'].upper()} ({slug})  — {t['ok']} OK, {t['fail']} PROBLEMS ({pct}%)")
        print("  " + "-"*85)

        for section_name, sec in result["sections"].items():
            if sec["checks_fail"] == 0:
                print(f"  ✅  {section_name}")
            else:
                print(f"  ❌  {section_name}  [{sec['checks_ok']} OK, {sec['checks_fail']} PROBLEMS]")
                for path, val in sec["failures"]:
                    print(f"       ▸ {path}: {val}")

    print("\n" + "="*90)
    total = grand_ok + grand_fail
    pct = int(100 * grand_ok / total) if total > 0 else 0
    print(f"  GRAND TOTAL: {grand_ok}/{total} checks passed ({pct}%)")
    print(f"  {grand_fail} issues need attention across all audits")
    print("="*90 + "\n")


def write_json_report(results, output_path):
    out = {}
    for slug, r in results.items():
        if "error" in r:
            out[slug] = r
            continue
        out[slug] = {
            "company": r["company"],
            "totals": r["totals"],
            "sections": {
                name: {
                    "ok": sec["checks_ok"],
                    "fail": sec["checks_fail"],
                    "failures": [{"field": p, "value": v} for p, v in sec["failures"]]
                }
                for name, sec in r["sections"].items()
            }
        }
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"JSON report: {output_path}")


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--slug",   help="Check one slug only")
    p.add_argument("--report", help="Write JSON report to file", default="/tmp/audit-deep-report.json")
    args = p.parse_args()

    all_slugs = sorted(SLUG_TO_FOLDER.keys())
    slugs = [args.slug] if args.slug else all_slugs

    print(f"Running DEEP check on {len(slugs)} audits…")
    results = run_deep_check(slugs)
    print_deep_report(results)
    if args.report:
        write_json_report(results, Path(args.report))
    return results


if __name__ == "__main__":
    main()
