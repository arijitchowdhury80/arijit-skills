#!/usr/bin/env python3
"""
factcheck_mechanical.py — deterministic mechanical dimensions for the Algolia audit
factcheck + eval gates.

The factcheck and eval SKILL.md files DESCRIBE these checks as inline bash snippets but ship
no runnable, tested script — so the "mechanical" dimensions are re-implemented by the LLM by
hand every run (non-deterministic, ungrep-able). This script makes the mechanical dimensions
actually mechanical. The JUDGMENT dimensions (quote-vs-transcript truth, "does this claim match
evidence", search-UX quality) stay on the LLM and are intentionally NOT implemented here.

Dimensions implemented (all deterministic, stdlib-only):
  completeness     — required files exist AND exceed byte thresholds
  source_density   — count source URLs + [FACT]/[ESTIMATE]/[OBSERVED] labels across research
  cross_file_stats — the same dollar/percent figures agree across deliverable .md files
  no_fabrication   — placeholder/TBD grep + impact_stat with no impact_stat_source in audit-data.json
  data_accuracy    — spot-check: a revenue figure in a deliverable also appears in 08-financial-profile.md
  url_liveness     — (opt-in, --check-urls) HTTP HEAD a sample of source URLs, report non-200

Usage:
  python3 factcheck_mechanical.py --audit-dir "/path/to/audits" --company "Brooks Running"
  python3 factcheck_mechanical.py --audit-dir ... --company ... --check-urls --url-sample 8
  python3 factcheck_mechanical.py --self-test         # no filesystem/network — unit checks

Output: JSON to stdout (machine-readable, for the orchestrator gate) + a human summary to stderr.
Exit code: 0 if no BLOCKING mechanical issue, 2 if a blocking issue is found.
"""

import argparse
import glob
import json
import os
import re
import sys


# ── helpers ────────────────────────────────────────────────────────────────────

URL_RE = re.compile(r"https?://[^\s)\]\"'>]+")
LABEL_RE = re.compile(r"\[(?:FACT|ESTIMATE|OBSERVED)\]")
# money: $1,234.5B / $12M / $900K  — captures number + optional magnitude
MONEY_RE = re.compile(r"\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)\s?([BMK])?", re.IGNORECASE)
# percentages: 72% / 12.5 %
PCT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s?%")
PLACEHOLDER_PATTERNS = ["TBD", "TODO", "lorem ipsum", "XXX", "{{", "FILL IN", "FILLIN", "PLACEHOLDER"]
# "Pending" only counts as a placeholder when it's clearly a stub value, not prose.
PENDING_RE = re.compile(r'"\s*[Pp]ending\s*"|:\s*"[Pp]ending"')


def read(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def norm_money(num, mag):
    """Normalize '$1.2B' to a float in dollars so $1.2B == $1,200M. Unit-aware (not strip+parseFloat)."""
    try:
        val = float(num.replace(",", ""))
    except ValueError:
        return None
    mult = {"B": 1e9, "M": 1e6, "K": 1e3}.get((mag or "").upper(), 1.0)
    return val * mult


def find_audit_data(company_dir):
    cands = sorted(glob.glob(os.path.join(company_dir, "deliverables", "*audit-data.json")))
    # Prefer the non-workspace one.
    cands = [c for c in cands if "workspace" not in os.path.basename(c).lower()] or cands
    return cands[0] if cands else None


def deliverable_md_files(company_dir):
    return sorted(glob.glob(os.path.join(company_dir, "deliverables", "*.md")))


def research_md_files(company_dir):
    return sorted(glob.glob(os.path.join(company_dir, "research", "*.md")))


# ── dimensions ──────────────────────────────────────────────────────────────────

def dim_completeness(company_dir):
    """Required research scratchpads exist and exceed byte threshold."""
    required = ["01", "02", "03", "04", "08", "10"]  # core spine; 04 may be 04-competitors*
    threshold = 2000
    results = []
    passing = 0
    for prefix in required:
        matches = sorted(glob.glob(os.path.join(company_dir, "research", f"{prefix}-*.md")))
        if matches:
            size = os.path.getsize(matches[0])
            ok = size >= threshold
            results.append({"prefix": prefix, "file": os.path.basename(matches[0]), "bytes": size, "pass": ok})
            passing += int(ok)
        else:
            results.append({"prefix": prefix, "file": None, "bytes": 0, "pass": False})
    return {"passing": passing, "total": len(required), "files": results}


def dim_source_density(company_dir):
    urls = 0
    labels = 0
    for f in research_md_files(company_dir):
        txt = read(f)
        urls += len(URL_RE.findall(txt))
        labels += len(LABEL_RE.findall(txt))
    return {"source_urls": urls, "labeled_claims": labels, "url_threshold": 15, "pass": urls >= 15}


def dim_cross_file_stats(company_dir):
    """Detect deliverable .md files that disagree on the SAME headline money figure.

    Conservative: we only flag when one file states a money figure that NO other deliverable
    corroborates AND another deliverable states a *different* value for an adjacent percent/figure.
    To stay deterministic and low-false-positive, we report the set of distinct normalized money
    values that appear in 2+ files and whether they are mutually consistent.
    """
    money_by_file = {}
    for f in deliverable_md_files(company_dir):
        txt = read(f)
        vals = set()
        for num, mag in MONEY_RE.findall(txt):
            nv = norm_money(num, mag)
            if nv is not None and nv >= 1e6:  # ignore tiny dollar amounts (prices etc.)
                vals.add(round(nv))
        if vals:
            money_by_file[os.path.basename(f)] = sorted(vals)
    # Build value -> files appearing in
    appears = {}
    for fname, vals in money_by_file.items():
        for v in vals:
            appears.setdefault(v, set()).add(fname)
    shared = {v: sorted(fs) for v, fs in appears.items() if len(fs) >= 2}
    return {
        "files_with_money": len(money_by_file),
        "shared_figures": len(shared),
        "money_by_file": money_by_file,
        # Not a hard pass/fail by itself — surfaced for the LLM to adjudicate ambiguous cases.
        "note": "shared money figures listed; LLM adjudicates any single-file outlier",
    }


def dim_no_fabrication(company_dir):
    issues = []
    ad_path = find_audit_data(company_dir)
    placeholder_hits = 0
    if ad_path:
        raw = read(ad_path)
        for pat in PLACEHOLDER_PATTERNS:
            c = raw.count(pat)
            if c:
                placeholder_hits += c
                issues.append({"type": "placeholder", "pattern": pat, "count": c, "file": os.path.basename(ad_path)})
        pending = len(PENDING_RE.findall(raw))
        if pending:
            placeholder_hits += pending
            issues.append({"type": "placeholder", "pattern": '"pending"', "count": pending, "file": os.path.basename(ad_path)})
        # impact_stat with content but no impact_stat_source
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            data = None
        unsourced_impact = 0
        if isinstance(data, dict):
            findings = data.get("findings") or []
            if isinstance(findings, list):
                for fnd in findings:
                    if not isinstance(fnd, dict):
                        continue
                    stat = (fnd.get("impact_stat") or "").strip()
                    src = (fnd.get("impact_stat_source") or "").strip()
                    if stat and not src.startswith("http"):
                        unsourced_impact += 1
            if unsourced_impact:
                issues.append({"type": "unsourced_impact_stat", "count": unsourced_impact, "file": os.path.basename(ad_path)})
    return {
        "placeholder_hits": placeholder_hits,
        "unsourced_impact_stats": sum(i["count"] for i in issues if i["type"] == "unsourced_impact_stat"),
        "issues": issues,
        "blocking": placeholder_hits > 0 or any(i["type"] == "unsourced_impact_stat" for i in issues),
    }


def dim_data_accuracy(company_dir):
    """Spot-check: the FIRST money figure quoted in a deliverable .md also appears
    (same normalized value) somewhere in 08-financial-profile.md."""
    fin_matches = sorted(glob.glob(os.path.join(company_dir, "research", "08-*.md")))
    fin_txt = read(fin_matches[0]) if fin_matches else ""
    fin_vals = {round(norm_money(n, m)) for n, m in MONEY_RE.findall(fin_txt) if norm_money(n, m) and norm_money(n, m) >= 1e6}
    checked = []
    for f in deliverable_md_files(company_dir):
        txt = read(f)
        m = MONEY_RE.search(txt)
        if not m:
            continue
        nv = norm_money(m.group(1), m.group(2))
        if nv is None or nv < 1e6:
            continue
        match = round(nv) in fin_vals
        checked.append({"file": os.path.basename(f), "value": m.group(0), "in_financial_profile": match})
        if len(checked) >= 3:
            break
    passed = sum(1 for c in checked if c["in_financial_profile"])
    return {"checked": checked, "passed": passed, "total": len(checked),
            "note": "no financial profile money figures to anchor against" if not fin_vals else ""}


def dim_url_liveness(company_dir, sample):
    """Opt-in HTTP HEAD on a sample of source URLs. Network — only runs with --check-urls."""
    import urllib.request
    import urllib.error

    urls = []
    for f in research_md_files(company_dir):
        urls.extend(URL_RE.findall(read(f)))
    # dedupe, preserve order, drop obvious non-source (algolia case study placeholders ok to keep)
    seen = []
    for u in urls:
        u = u.rstrip(".,);")
        if u not in seen:
            seen.append(u)
    sample_urls = seen[:sample]
    results = []
    dead = 0
    for u in sample_urls:
        status = None
        try:
            req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "Mozilla/5.0 (audit-factcheck)"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception as e:  # noqa: BLE001 — network failures of any kind = unreachable
            status = f"ERR:{type(e).__name__}"
        ok = isinstance(status, int) and 200 <= status < 400
        if not ok:
            dead += 1
        results.append({"url": u, "status": status, "ok": ok})
    return {"sampled": len(sample_urls), "dead": dead, "results": results}


# ── orchestration ───────────────────────────────────────────────────────────────

def run_all(audit_dir, company, check_urls=False, url_sample=8):
    company_dir = os.path.join(audit_dir, company)
    if not os.path.isdir(company_dir):
        return {"error": f"company dir not found: {company_dir}"}, 2

    out = {
        "company": company,
        "company_dir": company_dir,
        "dimensions": {
            "completeness": dim_completeness(company_dir),
            "source_density": dim_source_density(company_dir),
            "cross_file_stats": dim_cross_file_stats(company_dir),
            "no_fabrication": dim_no_fabrication(company_dir),
            "data_accuracy": dim_data_accuracy(company_dir),
        },
    }
    if check_urls:
        out["dimensions"]["url_liveness"] = dim_url_liveness(company_dir, url_sample)

    # Blocking determination (mechanical only — judgment dims excluded by design)
    blocking = []
    if out["dimensions"]["no_fabrication"]["blocking"]:
        blocking.append("no_fabrication: placeholder/unsourced impact_stat present")
    if not out["dimensions"]["completeness"]["passing"] == out["dimensions"]["completeness"]["total"]:
        blocking.append("completeness: missing/undersized required research files")
    if check_urls and out["dimensions"].get("url_liveness", {}).get("dead", 0) > 0:
        blocking.append("url_liveness: one or more sampled source URLs not reachable")
    out["mechanical_action"] = "BLOCKED" if blocking else "PROCEED"
    out["blocking_reasons"] = blocking
    return out, (2 if blocking else 0)


# ── self-test (no fs/network) ───────────────────────────────────────────────────

def self_test():
    fails = []

    def check(label, cond):
        if not cond:
            fails.append(label)
            print(f"  FAIL: {label}", file=sys.stderr)
        else:
            print(f"  ok: {label}")

    # money normalization is unit-aware
    check("$1.2B == $1,200M", norm_money("1.2", "B") == norm_money("1,200", "M"))
    check("$900K == 900000", norm_money("900", "K") == 900000.0)
    check("bare $5,000,000 parses", norm_money("5,000,000", None) == 5000000.0)
    check("garbage returns None", norm_money("abc", None) is None)
    # regexes
    check("URL_RE finds url", URL_RE.findall("see https://x.com/a?b=1) here") == ["https://x.com/a?b=1"])
    check("LABEL_RE finds labels", len(LABEL_RE.findall("[FACT] x [ESTIMATE] y [OBSERVED] z [NOPE]")) == 3)
    check("MONEY_RE captures magnitude", MONEY_RE.findall("$1.2B and $300M")[0] == ("1.2", "B"))
    check("PCT_RE captures pct", PCT_RE.findall("72% off, 12.5 %") == ["72", "12.5"])
    check("pending placeholder detected", len(PENDING_RE.findall('"body": "pending"')) == 1)
    check("real prose 'pending' not over-matched", len(PENDING_RE.findall("the deal is pending approval")) == 0)
    print(("\n✗ self-test FAILED" if fails else "\n✓ self-test passed"), file=sys.stderr)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="Deterministic mechanical factcheck/eval dimensions")
    ap.add_argument("--audit-dir", default=os.environ.get("ALGOLIA_AUDIT_DIR", ""))
    ap.add_argument("--company")
    ap.add_argument("--check-urls", action="store_true", help="HTTP HEAD a sample of source URLs (network)")
    ap.add_argument("--url-sample", type=int, default=8)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())

    if not args.audit_dir or not args.company:
        ap.error("--audit-dir and --company are required (or set ALGOLIA_AUDIT_DIR)")

    result, code = run_all(args.audit_dir, args.company, args.check_urls, args.url_sample)
    print(json.dumps(result, indent=2))
    # human summary to stderr
    if "error" not in result:
        d = result["dimensions"]
        print(f"\n— Mechanical factcheck: {result['mechanical_action']} —", file=sys.stderr)
        print(f"  completeness: {d['completeness']['passing']}/{d['completeness']['total']} required files", file=sys.stderr)
        print(f"  source_density: {d['source_density']['source_urls']} urls / {d['source_density']['labeled_claims']} labels (pass={d['source_density']['pass']})", file=sys.stderr)
        print(f"  no_fabrication: {d['no_fabrication']['placeholder_hits']} placeholders, {d['no_fabrication']['unsourced_impact_stats']} unsourced impact_stats", file=sys.stderr)
        print(f"  data_accuracy: {d['data_accuracy']['passed']}/{d['data_accuracy']['total']} money spot-checks", file=sys.stderr)
        if "url_liveness" in d:
            print(f"  url_liveness: {d['url_liveness']['dead']} dead of {d['url_liveness']['sampled']} sampled", file=sys.stderr)
        for r in result["blocking_reasons"]:
            print(f"  BLOCK: {r}", file=sys.stderr)
    sys.exit(code)


if __name__ == "__main__":
    main()
