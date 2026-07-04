#!/usr/bin/env python3
"""Offline tests for factcheck_mechanical.py — no network.

Covers:
  - the in-script structural self-test (unit-level, the 8 bug-class gates)
  - end-to-end run_all() on a temp fixture (clean → PROCEED, dirty → BLOCKED)
  - backward-compat legacy interface (--audit-dir/--company via run_all positional)

Run: python3 test_factcheck_mechanical.py
"""
import json
import os
import sys
import tempfile

import factcheck_mechanical as fm


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def build_fixture(root, *, clean=True):
    """Create {company}/deliverables/{company}-audit-data.json (+ a rendered index.html and a
    screenshot) for a fake company. clean=True → passes every structural gate."""
    company = "Acme"
    cdir = os.path.join(root, company)
    deliv = os.path.join(cdir, "deliverables")
    shots = os.path.join(deliv, "screenshots")
    os.makedirs(shots, exist_ok=True)
    # a >50KB screenshot
    with open(os.path.join(shots, "01-home.png"), "wb") as fh:
        fh.write(b"\x89PNG\r\n" + b"0" * (60 * 1024))
    # rendered html that embeds it
    _write(os.path.join(deliv, "index.html"),
           "<html><img src='screenshots/01-home.png'></html>")

    data = {
        "financials": {
            "revenue_fy2026": "$11B", "gross_profit_fy2026": "$6B", "ebitda_fy2026": "$2B",
            "net_income_fy2026": "$1B", "operating_margin_pct": "11%",
            "revenue_source": "https://sec.gov/x",
        },
        "tech_stack": {
            "search_provider": "Bloomreach", "search_vendor": "Bloomreach",
            "ecommerce_platform": "SFCC", "analytics": "GA4",
            "tech_stack_summary": "Bloomreach detected via network inspection.",
            "deal_type": "DISPLACEMENT", "algolia_detected": False,
        },
        "traffic": {"top_channels": [{"channel": "Direct", "share": "41%"}],
                    "device_share": {"mobile": "60%", "desktop": "40%"}},
        "hiring": {"total_open_roles": 5, "top_signals": ["PM Search"]},
        "partner_intel": {"co_sell": "Crossbeam overlap", "crossbeam_data_available": False,
                          "source_label": "gemini_search fallback"},
        "findings": [{"id": "F1", "title": "x", "screenshot_file": "screenshots/01-home.png"}],
        "next_steps": [{"action": "Warm intro via partner", "detail": "x" * 40, "priority": "HIGH"}],
        "ae_fields": {"next_step": "Request warm intro to CTO", "opportunity_headline": "1% lift = $27M",
                      "discovery_questions": ["Where does search sit in the roadmap today?"]},
    }
    if not clean:
        # inject exactly the lululemon bug class:
        data["traffic"]["top_channels"].append({"channel": "Paid", "share": "276.44%"})   # >100%
        data["tech_stack"]["search_provider"] = "- **Bloomreach** (confirmed)"             # markdown fragment
        data["financials"]["gross_profit_fy2026"] = "—"                                    # blank next to citation
        data["next_steps"].append({"action": "", "detail": "TBD"})                         # placeholder action
    _write(os.path.join(deliv, f"{company.lower()}-audit-data.json"), json.dumps(data, indent=2))
    return company, os.path.join(deliv, f"{company.lower()}-audit-data.json")


def main():
    fails = []

    def check(label, cond):
        if not cond:
            fails.append(label)
            print(f"  FAIL: {label}")
        else:
            print(f"  ok: {label}")

    print("— in-script structural self-test —")
    check("self_test() passes", fm.self_test() == 0)

    print("— clean fixture → PROCEED —")
    with tempfile.TemporaryDirectory() as root:
        company, ad = build_fixture(root, clean=True)
        res, code = fm.run_all(audit_data=ad)
        check("clean → PROCEED", res["mechanical_action"] == "PROCEED")
        check("clean → exit 0", code == 0)
        s = res["structural"]
        for dim in ("financials", "tech_stack", "traffic", "hiring", "screenshots", "next_steps", "dash_citation"):
            check(f"clean {dim} passes", s[dim]["pass"] is True)

    print("— dirty fixture → BLOCKED with the right dims —")
    with tempfile.TemporaryDirectory() as root:
        company, ad = build_fixture(root, clean=False)
        res, code = fm.run_all(audit_data=ad)
        s = res["structural"]
        check("dirty → BLOCKED", res["mechanical_action"] == "BLOCKED")
        check("dirty → exit 2", code == 2)
        check("dirty traffic FAILS (>100%)", s["traffic"]["pass"] is False)
        check("dirty tech_stack FAILS (markdown fragment)", s["tech_stack"]["pass"] is False)
        check("dirty financials FAILS (blank next to citation)", s["financials"]["pass"] is False)
        check("dirty next_steps FAILS (placeholder action)", s["next_steps"]["pass"] is False)
        check("blocking_reasons non-empty", len(res["blocking_reasons"]) >= 4)

    print("— legacy interface (--audit-dir/--company) still resolves —")
    with tempfile.TemporaryDirectory() as root:
        company, ad = build_fixture(root, clean=True)
        res, code = fm.run_all(audit_dir=root, company=company)
        check("legacy resolves audit-data + PROCEED", res["mechanical_action"] == "PROCEED" and code == 0)

    print("— missing company dir → error —")
    res, code = fm.run_all(audit_dir="/nonexistent", company="Nope")
    check("missing company → error + exit 2", "error" in res and code == 2)

    print("\n" + ("✗ FAILED: " + ", ".join(fails) if fails else "✓ all factcheck_mechanical tests passed"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
