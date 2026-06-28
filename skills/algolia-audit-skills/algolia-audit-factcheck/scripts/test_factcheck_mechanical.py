#!/usr/bin/env python3
"""Offline tests for factcheck_mechanical.py — builds a tiny temp audit dir (no network).

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
    """Create research/ + deliverables/ for a fake company. clean=True → no fabrication issues."""
    company = "Acme"
    cdir = os.path.join(root, company)
    research = os.path.join(cdir, "research")
    deliv = os.path.join(cdir, "deliverables")
    # 6 required research files, all above 2000 bytes, with URLs + labels
    body = "x" * 2200 + "\n[FACT] revenue is $1.2B per https://example.com/ir\n"
    for pre, name in [("01", "company-context"), ("02", "tech-stack"), ("03", "traffic-data"),
                      ("04", "competitors"), ("08", "financial-profile"), ("10", "scoring-matrix")]:
        extra = "Revenue: $1.2B [FACT] https://sec.gov/x\n" if pre == "08" else ""
        _write(os.path.join(research, f"{pre}-{name}.md"), body + extra + ("https://a.com/%d " % 1) * 20)
    # a deliverable quoting $1.2B (should match financial profile in data_accuracy)
    _write(os.path.join(deliv, "acme-search-audit-report.md"),
           "The company makes $1.2B in revenue. Search gap costs them $40M.\n")
    # audit-data.json
    findings = [
        {"impact_stat": "72% use NLP", "impact_stat_source": "https://baymard.com/x"},
        {"impact_stat": "", "impact_stat_source": ""},  # empty stat = OK (rule followed)
    ]
    if not clean:
        findings.append({"impact_stat": "made up number", "impact_stat_source": ""})  # unsourced → fabrication
    data = {"score": {"overall": 4.3}, "findings": findings,
            "abx_sequence": [{"channel": "email", "body": "real body " * 30}]}
    if not clean:
        data["notes"] = "TBD finish this"  # placeholder
    _write(os.path.join(deliv, "acme-audit-data.json"), json.dumps(data, indent=2))
    return company


def main():
    fails = []

    def check(label, cond):
        if not cond:
            fails.append(label)
            print(f"  FAIL: {label}")
        else:
            print(f"  ok: {label}")

    with tempfile.TemporaryDirectory() as root:
        # clean audit → PROCEED
        company = build_fixture(root, clean=True)
        res, code = fm.run_all(root, company)
        d = res["dimensions"]
        check("clean audit → mechanical_action PROCEED", res["mechanical_action"] == "PROCEED")
        check("clean audit → exit 0", code == 0)
        check("completeness 6/6", d["completeness"]["passing"] == 6)
        check("source_density passes (>=15 urls)", d["source_density"]["pass"] is True)
        check("no_fabrication not blocking on clean", d["no_fabrication"]["blocking"] is False)
        check("empty impact_stat is NOT flagged", d["no_fabrication"]["unsourced_impact_stats"] == 0)
        check("data_accuracy matches $1.2B in financial profile",
              d["data_accuracy"]["passed"] >= 1)

    with tempfile.TemporaryDirectory() as root:
        # dirty audit → BLOCKED
        company = build_fixture(root, clean=False)
        res, code = fm.run_all(root, company)
        d = res["dimensions"]
        check("dirty audit → mechanical_action BLOCKED", res["mechanical_action"] == "BLOCKED")
        check("dirty audit → exit 2", code == 2)
        check("placeholder TBD detected", d["no_fabrication"]["placeholder_hits"] >= 1)
        check("unsourced impact_stat detected", d["no_fabrication"]["unsourced_impact_stats"] >= 1)

    with tempfile.TemporaryDirectory() as root:
        # missing company dir → error + exit 2
        res, code = fm.run_all(root, "DoesNotExist")
        check("missing company → error", "error" in res and code == 2)

    print("\n" + ("✗ FAILED: " + ", ".join(fails) if fails else "✓ all factcheck_mechanical tests passed"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
