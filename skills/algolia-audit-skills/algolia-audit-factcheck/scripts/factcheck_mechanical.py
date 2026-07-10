#!/usr/bin/env python3
"""
factcheck_mechanical.py — deterministic mechanical gate for the Algolia audit factcheck.

WHY THIS EXISTS (root cause it fixes):
    A prior factcheck run on lululemon returned a 9.4/10 PROCEED verdict on a report that
    contained blank sourced fields, an impossible "276.44% of traffic" channel share, and a
    self-contradictory tech-stack block. That happened because the deterministic completeness
    gate referenced by the factcheck SKILL.md ("scripts/factcheck_mechanical.py") was NOT
    deployed to the skill-discovery path, so factcheck silently degraded to LLM narrative
    judgment only. An LLM spot-checking prose cannot reliably catch "this field is blank",
    "this array is empty", or "this percentage is > 100%" — deterministic code can.

    This script makes the STRUCTURAL truths of an audit-data.json actually mechanical. The
    JUDGMENT dimensions (quote-vs-transcript authenticity, "does this claim match the
    evidence", search-UX quality) stay on the LLM and are intentionally NOT implemented here.

TWO CHECK FAMILIES (both run when inputs are present):
  A. STRUCTURAL (operate directly on audit-data.json) — the 8 bug-class gates:
       financials    — most-recent-year revenue/gross_profit/ebitda/operating_income/net_income
                        non-null OR an explicit source-unavailable marker (never blank-with-citation)
       tech_stack    — search provider non-empty & not a leaked markdown fragment; summary does
                        not contradict populated vendor fields; greenfield scenario consistent
                        with algolia_detected / search_vendor
       traffic       — every "% of traffic / share" field is within [0, 100]
       hiring        — >= 1 role OR an explicit "no ICP roles found, verified via <source>" note
       partner_intel — if prose invokes Crossbeam, there must be an honest availability marker /
                        fallback note (not an unexplained skip)
       screenshots   — each finding.screenshot_file exists on disk, > 50KB, AND (when a rendered
                        index.html is available) is actually embedded in the rendered HTML
       next_steps    — next_steps and ae_fields action items are populated, not placeholder-only
       dash_citation — no bare "—" / "-" / "" data value sitting in the same object as a live
                        citation that implies the value was sourced (the signature of this bug)
  B. CORPUS (operate on research/ + deliverables/ .md, when a company_dir exists) — the original
     dimensions: completeness, source_density, cross_file_stats, no_fabrication, data_accuracy,
     optional url_liveness.

Usage:
  # direct — the primary form the gate should use
  python3 factcheck_mechanical.py --audit-data /path/to/{company}-audit-data.json [--check-urls]
  # legacy / pipeline form (matches SKILL.md); resolves deliverables/*audit-data.json
  python3 factcheck_mechanical.py --audit-dir "$ALGOLIA_AUDIT_DIR" --company "Lululemon"
  # optional explicit rendered HTML for the screenshot-embed sub-check
  python3 factcheck_mechanical.py --audit-data ... --rendered-html /path/to/index.html
  python3 factcheck_mechanical.py --self-test          # no filesystem/network — unit checks

Output: JSON to stdout (machine-readable, for the orchestrator gate) + a human summary to stderr.
Exit code: 0 if no BLOCKING mechanical issue, 2 if any blocking issue is found.
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
MONEY_RE = re.compile(r"\$\s?([0-9][0-9,]*(?:\.[0-9]+)?)\s?([BMK])?", re.IGNORECASE)
PCT_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s?%")
PLACEHOLDER_PATTERNS = ["TBD", "TODO", "lorem ipsum", "XXX", "{{", "FILL IN", "FILLIN", "PLACEHOLDER"]
PENDING_RE = re.compile(r'"\s*[Pp]ending\s*"|:\s*"[Pp]ending"')
# markers that legitimately explain a missing value (so a blank is honest, not a hidden gap)
UNAVAILABLE_RE = re.compile(
    r"(not\s+disclosed|unavailable|not\s+available|no\s+source|n/?a\b|not\s+reported|"
    r"not\s+broken\s+out|withheld|undisclosed|no\s+data)", re.IGNORECASE)
# a value that is "blank" for the purposes of the dash-vs-citation signature
BARE_BLANK = {"", "—", "-", "–", "n/a", "N/A", "tbd", "TBD", "...", "—%", "undefined", "undefined%"}
# an AFFIRMATIVE blank placeholder (a slot that should carry a value but got a dash) — always suspect
DASH_MARKERS = {"—", "–", "-", "n/a", "tbd", "...", "undefined", "undefined%", "—%", "$—", "—/yr"}
# keys whose value is a citation/provenance claim
CITATION_KEY_RE = re.compile(r"(source|citation|proof_url|proof_company|_url|evidence|cite)$", re.IGNORECASE)
# keys that denote a SOURCED DATA VALUE (empty-string here next to a citation = a real gap; an empty
# cosmetic label/badge/note is NOT this bug class, so it is excluded to avoid false positives)
VALUE_KEY_RE = re.compile(
    r"(value|amount|revenue|ebitda|income|profit|margin|stat|figure|number|price|share|rate|"
    r"pct|percent|count|total|score|visits|cap|roi|multiple|estimate|revenue_fy|fy20)", re.IGNORECASE)


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


def is_blank(v):
    if v is None:
        return False  # explicit null = an intentional "no value", NOT the blank-next-to-citation bug
    if isinstance(v, str):
        return v.strip().lower() in {b.lower() for b in BARE_BLANK}
    return False


def nonempty_str(v, minlen=1):
    return isinstance(v, str) and len(v.strip()) >= minlen


def all_pcts(v):
    """Every numeric percentage inside a string (handles ranges like '70.9–74.43%' and
    plain numeric shares). Only numbers that are a percentage (before a '%' or a range
    that ends in '%') are returned — bare years/counts are ignored to avoid false positives."""
    if v is None:
        return []
    if isinstance(v, (int, float)):
        return [float(v)]
    s = str(v)
    out = []
    for a, b in re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*[–—-]\s*([0-9]+(?:\.[0-9]+)?)\s*%", s):
        out += [float(a), float(b)]
    for m in re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*%", s):
        out.append(float(m))
    if not out:
        m = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*", s)
        if m:
            out.append(float(m.group(1)))
    seen = []
    for x in out:
        if x not in seen:
            seen.append(x)
    return seen


def find_audit_data(company_dir):
    cands = sorted(glob.glob(os.path.join(company_dir, "deliverables", "*audit-data.json")))
    cands = [c for c in cands if "workspace" not in os.path.basename(c).lower() and ".bak" not in c] or cands
    return cands[0] if cands else None


def deliverable_md_files(company_dir):
    return sorted(glob.glob(os.path.join(company_dir, "deliverables", "*.md")))


def research_md_files(company_dir):
    return sorted(glob.glob(os.path.join(company_dir, "research", "*.md")))


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


# ── STRUCTURAL dimensions (operate on audit-data.json) ───────────────────────────

def struct_financials(data):
    """Most-recent-year core metrics are non-null OR carry an explicit unavailable marker.
    A blank/empty metric that sits next to a sourcing citation is the failure signature."""
    fin = data.get("financials") or {}
    fails = []
    if not isinstance(fin, dict) or not fin:
        return {"pass": True, "skipped": "no financials block", "fails": []}

    years = sorted({int(m.group(1)) for k in fin for m in [re.search(r"_fy(\d{4})$", k)] if m}, reverse=True)
    year = years[0] if years else None
    has_citation = any(nonempty_str(fin.get(k)) and (str(fin.get(k)).startswith("http") or "sec" in str(fin.get(k)).lower() or k.endswith("source"))
                       for k in ("revenue_source", "source_url", "source", "revenue_source_label"))

    metrics = ["revenue", "gross_profit", "ebitda", "net_income", "operating_income"]
    for metric in metrics:
        val = fin.get(f"{metric}_fy{year}") if year else None
        # operating_income may legitimately be expressed only as a margin
        if metric == "operating_income" and not nonempty_str(str(val) if val is not None else ""):
            if nonempty_str(str(fin.get("operating_margin_pct") or "")) or nonempty_str(str(fin.get(f"operating_margin_fy{year}") or "")):
                continue
        # explicit per-metric unavailable marker
        marker = fin.get(f"{metric}_unavailable") or fin.get(f"{metric}_status") or ""
        if val is None and not year:
            continue  # cannot locate a fiscal year suffix; don't fabricate a failure
        if nonempty_str(str(val) if val is not None else "") and not is_blank(val):
            continue
        if UNAVAILABLE_RE.search(str(marker)) or (isinstance(val, str) and UNAVAILABLE_RE.search(val)):
            continue
        # missing / blank
        if is_blank(val) and has_citation:
            fails.append(f"financials.{metric}_fy{year} is blank ('{val}') but a sourcing citation is present (implies it was sourced)")
        else:
            fails.append(f"financials.{metric}_fy{year} missing/blank with no explicit unavailable marker")
    return {"pass": not fails, "year": year, "fails": fails}


def struct_techstack(data):
    ts = data.get("tech_stack") or {}
    fails = []
    if not isinstance(ts, dict) or not ts:
        return {"pass": True, "skipped": "no tech_stack block", "fails": []}

    # current_vendor is the canonical field when the report/render pipeline overrides the
    # client-side detect-search finding with partner/investor intel (e.g. Belk: detect-search
    # found nothing but partner intel confirmed Constructor.io). search_provider/search_vendor
    # are the raw detect-search output and may be empty even when current_vendor is correctly
    # set — checking only the raw fields produced a false "search provider field is empty"
    # BLOCKED on Belk's 2026-07-03 run even after the vendor was correctly resolved.
    provider = ts.get("current_vendor") or ts.get("search_provider") or ts.get("search_vendor") or ""
    if not nonempty_str(str(provider)):
        fails.append("tech_stack: search provider field is empty (checked current_vendor, search_provider, search_vendor)")
    else:
        p = str(provider).strip()
        # leaked markdown-fragment signature: a bullet / label / bold marker instead of a vendor name
        if p.startswith(("-", "*", "•", "#")) or "**" in p or re.match(r"^\s*[A-Z][a-z ]+:\s*$", p):
            fails.append(f"tech_stack.search_provider looks like a leaked markdown/label fragment, not a vendor: '{p[:70]}'")

    # summary contradicts populated vendor fields
    summary = str(ts.get("tech_stack_summary") or "")
    negation = re.search(r"(no\s+platform|no\s+analytics|no\s+.*detections|blocked\s+by\s+waf|"
                         r"yielded\s+no|no\s+vendor\s+detected|detection\s+failed)", summary, re.IGNORECASE)
    populated_fields = [k for k in ("search_vendor", "ecommerce_platform", "analytics", "cms", "frontend", "cdn_waf")
                        if nonempty_str(str(ts.get(k) or "")) and not str(ts.get(k)).strip().startswith("-")]
    if negation and len(populated_fields) >= 2:
        fails.append(f"tech_stack_summary claims no detection ('{negation.group(0)}') but these fields are populated: {populated_fields}")

    # current_vendor self-consistency: when current_vendor is set from an override (partner/
    # investor intel), tech_stack_summary must name that SAME vendor — never a different one
    # left over from an earlier detect-search pass. Root cause of Belk's original C1 bug
    # (summary said "proprietary search" while current_vendor said "Constructor.io"); this is
    # the structural check that would have caught it instead of requiring a manual re-render.
    cv_raw = str(ts.get("current_vendor") or "").strip()
    # strip a trailing parenthetical qualifier (e.g. "Constructor.io (displacement target)")
    # before the substring check — the vendor name itself is what must appear in the summary,
    # not the deal-context annotation tacked onto it. Belk 2026-07-09: a real vendor match was
    # false-flagged because "Constructor.io" and "(displacement target)" aren't one contiguous
    # substring in the summary even though the vendor name is clearly present.
    cv = re.sub(r"\s*\([^)]*\)\s*$", "", cv_raw).strip()
    if cv and summary and cv.lower() not in summary.lower():
        fails.append(
            f"tech_stack_summary does not name current_vendor ('{cv_raw}') — summary may describe a "
            f"stale/different vendor from an earlier detect-search pass. Regenerate the summary "
            f"from current_vendor before shipping."
        )

    # garbage full_list: a list of bare label fragments (ends with ':') is a parse failure
    fl = ts.get("full_list")
    if isinstance(fl, list) and fl:
        frag = sum(1 for x in fl if isinstance(x, str) and x.strip().endswith(":"))
        if frag >= max(3, len(fl) // 2):
            fails.append(f"tech_stack.full_list is {frag} bare label fragments (parse failure, not real detections)")

    # greenfield consistency: greenfield/displacement means the TARGET has no incumbent SaaS search;
    # if algolia_detected True or the vendor names Algolia, that contradicts a greenfield scenario.
    scenario = " ".join(str(data.get(k, "")) for k in ("golden_angle",)) + " " + str(ts.get("deal_type") or "") + " " + str(ts.get("architecture_notes") or "")
    ga = data.get("golden_angle") or {}
    scenario += " " + str(ga.get("headline", "")) + " " + str(ga.get("detail", ""))
    is_greenfield = re.search(r"greenfield|displacement", str(ts.get("deal_type") or "") + " " + str(data.get("ae_fields", {}).get("competitive_scenario", "")), re.IGNORECASE)
    if is_greenfield:
        if ts.get("algolia_detected") is True or re.search(r"\balgolia\b", str(ts.get("search_vendor") or ""), re.IGNORECASE):
            fails.append("tech_stack: scenario is GREENFIELD/DISPLACEMENT but target's own search_vendor/algolia_detected indicates Algolia already in use (contradiction)")
    return {"pass": not fails, "fails": fails}


def struct_traffic(data):
    tr = data.get("traffic") or {}
    fails = []
    if not isinstance(tr, dict) or not tr:
        return {"pass": True, "skipped": "no traffic block", "fails": []}

    # data_quality gate — SimilarWeb is PERMANENT HITL, no API exists or ever will.
    # degraded_mode=true means the API path was attempted, failed, and the module fell
    # back to a Gemini-search ESTIMATE instead of a real HITL capture. That is a policy
    # violation, not a warning: it must BLOCK, not PROCEED. (Root cause of the 2026-07-01
    # lululemon false 9.4/10 PROCEED — this flag existed in research JSON but was dropped
    # before reaching audit-data.json, so nothing could ever check it. Fixed upstream in
    # generate-audit-data.py's lift_traffic_json; this is the enforcement side.)
    dq = str(tr.get("data_quality") or "").upper()
    if tr.get("degraded_mode") is True or "DEGRADED" in dq or "ESTIMATE" in dq:
        fails.append(
            f"traffic.data_quality={tr.get('data_quality')!r} / degraded_mode={tr.get('degraded_mode')!r} "
            "— SimilarWeb traffic data is API-fallback/estimate, not a verified HITL capture. "
            "BLOCKED per permanent HITL policy: no API-derived or estimate traffic data may ship. "
            "Run the SimilarWeb PRO live-capture method (see algolia-intel-traffic SKILL.md) and re-run this module."
        )

    def check_share(label, v):
        for p in all_pcts(v):
            if p < 0 or p > 100:
                fails.append(f"traffic.{label} = {p}% is outside [0,100] (a traffic share cannot exceed 100%)")

    for i, ch in enumerate(tr.get("top_channels") or []):
        if isinstance(ch, dict):
            check_share(f"top_channels[{i}]({ch.get('channel')}).share", ch.get("share"))
    dev = tr.get("device_share") or {}
    if isinstance(dev, dict):
        for k, v in dev.items():
            check_share(f"device_share.{k}", v)
    for i, d in enumerate(tr.get("demographics") or []):
        if isinstance(d, dict):
            check_share(f"demographics[{i}].pct", d.get("pct"))
    for i, g in enumerate(tr.get("geo_distribution") or []):
        if isinstance(g, dict):
            check_share(f"geo_distribution[{i}]({g.get('country')}).traffic_share_pct", g.get("traffic_share_pct"))
    for i, r in enumerate(tr.get("referring_industries") or []):
        if isinstance(r, dict):
            check_share(f"referring_industries[{i}].share_pct", r.get("share_pct"))
    refs = (tr.get("referrals") or {}).get("top_referring_sites") or []
    for i, r in enumerate(refs):
        if isinstance(r, dict):
            check_share(f"referrals.top_referring_sites[{i}].share_pct", r.get("share_pct"))
    # any key literally named as a share-of-total (skip change/mom/yoy semantics)
    ps = tr.get("paid_search") or {}
    if isinstance(ps, dict):
        for k, v in ps.items():
            if "share_of_total" in k and "change" not in k and "mom" not in k and "yoy" not in k:
                check_share(f"paid_search.{k}", v)
    return {"pass": not fails, "fails": fails}


def struct_hiring(data):
    h = data.get("hiring") or {}
    fails = []
    if not isinstance(h, dict) or not h:
        return {"pass": True, "skipped": "no hiring block", "fails": []}
    count = 0
    for k in ("total_open_roles", "icp_roles_count"):
        try:
            count = max(count, int(h.get(k) or 0))
        except (TypeError, ValueError):
            pass
    count = max(count, len(h.get("top_signals") or []))
    if count < 1:
        note = str(h.get("null_signal_note") or "")
        if not (nonempty_str(note, 20) and (URL_RE.search(note) or re.search(r"verified|checked|scraped|via\s+\w", note, re.IGNORECASE))):
            fails.append("hiring: 0 roles found AND null_signal_note does not explain a verified no-result (bare empty array)")
    return {"pass": not fails, "roles": count, "fails": fails}


def struct_partner(data):
    pi = data.get("partner_intel") or {}
    fails = []
    if not isinstance(pi, dict) or not pi:
        return {"pass": True, "skipped": "no partner_intel block", "fails": []}
    blob = json.dumps(pi).lower()
    mentions_crossbeam = "crossbeam" in blob
    has_marker = "crossbeam_data_available" in pi
    has_fallback_note = bool(re.search(r"(gemini_search|websearch|web search|fallback|no overlap|not queried|unavailable)", blob))
    if mentions_crossbeam and not has_marker and not has_fallback_note:
        fails.append("partner_intel mentions Crossbeam but shows no crossbeam_data_available marker and no fallback/skip explanation (looks like an unexplained skip)")
    return {"pass": not fails, "fails": fails}


def struct_screenshots(data, screenshots_roots, rendered_html, browser_findings_path=None):
    fails = []
    findings = data.get("findings") or []
    if not isinstance(findings, list) or not findings:
        return {"pass": True, "skipped": "no findings", "fails": []}
    html = read(rendered_html) if rendered_html and os.path.isfile(rendered_html) else ""

    # WAF-degraded exception: a genuine WAF/bot-challenge interstitial (e.g. Belk's PerimeterX
    # "Press & Hold" block) is a real, small screenshot by construction — flagging it as
    # "blank/broken" on size alone produced a false BLOCKED on Belk's 2026-07-03 run even though
    # the screenshot was verified real. Read the browser-findings doc's own status line rather
    # than guess from size.
    waf_degraded = False
    if browser_findings_path and os.path.isfile(browser_findings_path):
        bf_text = read(browser_findings_path)
        if re.search(r"STATUS:\s*WAF[- ]BLOCKED|blocked\s+by\s+waf|waf[- ]block", bf_text, re.IGNORECASE):
            waf_degraded = True

    checked = 0
    for f in findings:
        if not isinstance(f, dict):
            continue
        sf = f.get("screenshot_file") or f.get("screenshot") or f.get("image")
        if not nonempty_str(str(sf or "")):
            continue
        checked += 1
        base = os.path.basename(str(sf))
        # resolve against candidate roots
        found_path = None
        for root in screenshots_roots:
            for cand in (os.path.join(root, str(sf)), os.path.join(root, base),
                         os.path.join(root, "screenshots", base)):
                if os.path.isfile(cand):
                    found_path = cand
                    break
            if found_path:
                break
        fid = f.get("id") or f.get("title", "?")
        if not found_path:
            fails.append(f"screenshots: finding {fid} references '{sf}' but the file is not present on disk")
            continue
        size = os.path.getsize(found_path)
        finding_text = f"{f.get('title', '')} {f.get('detail', '')} {f.get('description', '')}".lower()
        is_waf_finding = waf_degraded and re.search(r"waf|blocked|interstitial|perimeterx|press\s*&?\s*hold", finding_text)
        if size < 50 * 1024:
            if is_waf_finding:
                pass  # PASS-with-note: legitimately small because it's a bot-challenge page, not blank/broken
            else:
                fails.append(f"screenshots: finding {fid} file '{base}' is only {size} bytes (< 50KB — likely blank/broken)")
        if html and base not in html and os.path.splitext(base)[0] not in html:
            fails.append(f"screenshots: finding {fid} file '{base}' is NOT embedded in the rendered index.html")
    return {"pass": not fails, "checked": checked, "embed_checked": bool(html), "waf_degraded": waf_degraded, "fails": fails}


def struct_next_steps(data):
    fails = []
    ns = data.get("next_steps") or []
    if isinstance(ns, list):
        for i, s in enumerate(ns):
            if isinstance(s, dict):
                action = s.get("action") or s.get("title") or ""
                detail = s.get("detail") or s.get("description") or ""
                if not nonempty_str(str(action), 4) or is_blank(action):
                    fails.append(f"next_steps[{i}].action is blank/placeholder")
                if not nonempty_str(str(detail), 10) or is_blank(detail):
                    fails.append(f"next_steps[{i}].detail is blank/placeholder")
            elif not nonempty_str(str(s), 10):
                fails.append(f"next_steps[{i}] is blank/placeholder")
    ae = data.get("ae_fields") or {}
    if isinstance(ae, dict) and ae:
        for k in ("next_step", "opportunity_headline"):
            if k in ae and (not nonempty_str(str(ae.get(k) or ""), 10) or is_blank(ae.get(k))):
                fails.append(f"ae_fields.{k} is blank/placeholder")
        dq = ae.get("discovery_questions")
        if dq is not None and isinstance(dq, list) and len([q for q in dq if nonempty_str(str(q), 10)]) == 0:
            fails.append("ae_fields.discovery_questions is empty / all-blank")
    return {"pass": not fails, "fails": fails}


def struct_dash_citation(data):
    """Bare '—' / '-' / '' data value sitting in the same object as a live citation
    (the value LOOKS sourced but is actually blank). Recursive."""
    fails = []

    def walk(obj, path):
        if isinstance(obj, dict):
            # does this object carry a live citation?
            cite_keys = [k for k, v in obj.items()
                         if CITATION_KEY_RE.search(k) and nonempty_str(str(v or ""))
                         and (str(v).startswith("http") or "sec" in str(v).lower() or "http" in str(v).lower())]
            if cite_keys:
                for k, v in obj.items():
                    if CITATION_KEY_RE.search(k):
                        continue
                    if not isinstance(v, str):
                        continue
                    sv = v.strip().lower()
                    # affirmative dash placeholder → always suspect regardless of key
                    if sv in DASH_MARKERS:
                        fails.append(f"{path}.{k} is a bare blank placeholder ('{v}') next to citation(s) {cite_keys} implying it was sourced")
                    # empty string → only a bug when the key denotes a sourced data VALUE (not a cosmetic label/badge/note)
                    elif sv == "" and VALUE_KEY_RE.search(k):
                        fails.append(f"{path}.{k} is an empty sourced-value field next to citation(s) {cite_keys} implying it was sourced")
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")

    walk(data, "$")
    return {"pass": not fails, "fails": fails[:25]}


# ── CORPUS dimensions (original — operate on research/ + deliverables/ .md) ───────

def dim_completeness(company_dir):
    required = ["01", "02", "03", "04", "08", "10"]
    threshold = 2000
    results, passing = [], 0
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
    urls = labels = 0
    for f in research_md_files(company_dir):
        txt = read(f)
        urls += len(URL_RE.findall(txt))
        labels += len(LABEL_RE.findall(txt))
    return {"source_urls": urls, "labeled_claims": labels, "url_threshold": 15, "pass": urls >= 15}


def dim_no_fabrication(company_dir):
    issues, placeholder_hits = [], 0
    ad_path = find_audit_data(company_dir)
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
        data = load_json(ad_path)
        unsourced_impact = 0
        if isinstance(data, dict):
            for fnd in (data.get("findings") or []):
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


def dim_url_liveness(company_dir, sample):
    import urllib.request
    import urllib.error
    urls = []
    for f in research_md_files(company_dir):
        urls.extend(URL_RE.findall(read(f)))
    seen = []
    for u in urls:
        u = u.rstrip(".,);")
        if u not in seen:
            seen.append(u)
    sample_urls = seen[:sample]
    results, dead = [], 0
    for u in sample_urls:
        status = None
        try:
            req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "Mozilla/5.0 (audit-factcheck)"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception as e:  # noqa: BLE001
            status = f"ERR:{type(e).__name__}"
        ok = isinstance(status, int) and 200 <= status < 400
        if not ok:
            dead += 1
        results.append({"url": u, "status": status, "ok": ok})
    return {"sampled": len(sample_urls), "dead": dead, "results": results}


# ── orchestration ────────────────────────────────────────────────────────────────

STRUCT_BLOCKING = ["financials", "tech_stack", "traffic", "hiring", "screenshots", "next_steps", "dash_citation"]
STRUCT_WARN = ["partner_intel"]


def run_structural(audit_data_path, rendered_html=None):
    data = load_json(audit_data_path)
    if not isinstance(data, dict):
        return {"error": f"could not parse audit-data json: {audit_data_path}"}, 2
    deliv_dir = os.path.dirname(os.path.abspath(audit_data_path))
    company_dir = os.path.dirname(deliv_dir)
    screenshots_roots = [deliv_dir, company_dir]
    if rendered_html is None:
        for cand in (os.path.join(deliv_dir, "index.html"),
                     os.path.join(deliv_dir, os.path.splitext(os.path.basename(audit_data_path))[0].replace("-audit-data", ""), "index.html")):
            if os.path.isfile(cand):
                rendered_html = cand
                break
    # the rendered-html directory is also a screenshots root (published-site layout keeps
    # {company}/index.html next to {company}/screenshots/, with audit-data.json one level up)
    if rendered_html and os.path.isfile(rendered_html):
        screenshots_roots.insert(0, os.path.dirname(os.path.abspath(rendered_html)))
    browser_findings_path = os.path.join(company_dir, "research", "09-browser-findings.md")

    dims = {
        "financials": struct_financials(data),
        "tech_stack": struct_techstack(data),
        "traffic": struct_traffic(data),
        "hiring": struct_hiring(data),
        "partner_intel": struct_partner(data),
        "screenshots": struct_screenshots(data, screenshots_roots, rendered_html, browser_findings_path),
        "next_steps": struct_next_steps(data),
        "dash_citation": struct_dash_citation(data),
    }
    blocking = []
    for name in STRUCT_BLOCKING:
        if not dims[name].get("pass", True):
            for msg in dims[name].get("fails", []):
                blocking.append(f"{name}: {msg}")
    warnings = []
    for name in STRUCT_WARN:
        if not dims[name].get("pass", True):
            for msg in dims[name].get("fails", []):
                warnings.append(f"{name}: {msg}")
    return {
        "audit_data": audit_data_path,
        "rendered_html": rendered_html,
        "structural": dims,
        "blocking_reasons": blocking,
        "warnings": warnings,
        "mechanical_action": "BLOCKED" if blocking else "PROCEED",
    }, (2 if blocking else 0)


def run_corpus(company_dir, check_urls=False, url_sample=8):
    dims = {
        "completeness": dim_completeness(company_dir),
        "source_density": dim_source_density(company_dir),
        "no_fabrication": dim_no_fabrication(company_dir),
    }
    if check_urls:
        dims["url_liveness"] = dim_url_liveness(company_dir, url_sample)
    blocking = []
    if dims["no_fabrication"]["blocking"]:
        blocking.append("no_fabrication: placeholder/unsourced impact_stat present")
    if dims["completeness"]["passing"] != dims["completeness"]["total"]:
        blocking.append("completeness: missing/undersized required research files")
    if check_urls and dims.get("url_liveness", {}).get("dead", 0) > 0:
        blocking.append("url_liveness: one or more sampled source URLs not reachable")
    return dims, blocking


def run_all(audit_dir=None, company=None, audit_data=None, check_urls=False, url_sample=8, rendered_html=None):
    # resolve audit-data path + company_dir
    company_dir = None
    if audit_data:
        audit_data_path = audit_data
        deliv = os.path.dirname(os.path.abspath(audit_data_path))
        company_dir = os.path.dirname(deliv)
    else:
        company_dir = os.path.join(audit_dir, company)
        if not os.path.isdir(company_dir):
            return {"error": f"company dir not found: {company_dir}"}, 2
        audit_data_path = find_audit_data(company_dir)
        if not audit_data_path:
            return {"error": f"no audit-data.json under {company_dir}/deliverables"}, 2

    struct_out, struct_code = run_structural(audit_data_path, rendered_html)
    out = dict(struct_out)
    out["company"] = company
    out["company_dir"] = company_dir

    # corpus dims only when a research/ tree exists
    corpus_blocking = []
    if company_dir and os.path.isdir(os.path.join(company_dir, "research")):
        corpus_dims, corpus_blocking = run_corpus(company_dir, check_urls, url_sample)
        out["corpus"] = corpus_dims

    all_blocking = list(out.get("blocking_reasons", [])) + corpus_blocking
    out["blocking_reasons"] = all_blocking
    out["mechanical_action"] = "BLOCKED" if all_blocking else "PROCEED"
    return out, (2 if all_blocking else 0)


# ── self-test (no fs/network) ─────────────────────────────────────────────────────

def self_test():
    fails = []

    def check(label, cond):
        if not cond:
            fails.append(label)
            print(f"  FAIL: {label}", file=sys.stderr)
        else:
            print(f"  ok: {label}")

    check("$1.2B == $1,200M", norm_money("1.2", "B") == norm_money("1,200", "M"))
    check("$900K == 900000", norm_money("900", "K") == 900000.0)
    check("garbage returns None", norm_money("abc", None) is None)
    check("is_blank em-dash", is_blank("—") is True)
    check("is_blank empty", is_blank("") is True)
    check("is_blank null is False", is_blank(None) is False)
    check("is_blank real value False", is_blank("Algolia") is False)
    check("all_pcts range", all_pcts("70.9–74.43%") == [70.9, 74.43])

    # traffic > 100%
    d = struct_traffic({"traffic": {"top_channels": [{"channel": "Paid", "share": "276.44%"}]}})
    check("traffic 276% flagged", d["pass"] is False and any("276.44" in f for f in d["fails"]))
    d = struct_traffic({"traffic": {"top_channels": [{"channel": "Direct", "share": "41%"}], "paid_search": {"mom_change_pct": "276.44%"}}})
    check("traffic mom_change 276% NOT flagged (it's a change, not a share)", d["pass"] is True)

    # tech stack markdown fragment + contradiction
    d = struct_techstack({"tech_stack": {"search_provider": "- **Status:** ACTIVE", "search_vendor": "Proprietary",
                                          "ecommerce_platform": "SFCC", "analytics": "GA4",
                                          "tech_stack_summary": "detection blocked by WAF; yielded no platform or analytics detections"}})
    check("tech_stack markdown-fragment provider flagged", any("markdown" in f for f in d["fails"]))
    check("tech_stack summary-contradiction flagged", any("claims no detection" in f for f in d["fails"]))

    # financials blank next to citation
    d = struct_financials({"financials": {"revenue_fy2026": "$11B", "gross_profit_fy2026": "—",
                                          "ebitda_fy2026": "$2B", "net_income_fy2026": "$1B",
                                          "operating_margin_pct": "11%", "revenue_source": "https://sec.gov/x"}})
    check("financials blank-next-to-citation flagged", d["pass"] is False and any("gross_profit" in f for f in d["fails"]))
    d = struct_financials({"financials": {"revenue_fy2026": "$11B", "gross_profit_fy2026": "$6B",
                                          "ebitda_fy2026": "$2B", "net_income_fy2026": "$1B",
                                          "operating_margin_pct": "11%", "revenue_source": "https://sec.gov/x"}})
    check("financials complete passes", d["pass"] is True)

    # hiring
    check("hiring 0 roles no note flagged",
          struct_hiring({"hiring": {"total_open_roles": 0, "null_signal_note": ""}})["pass"] is False)
    check("hiring 0 roles WITH verified note passes",
          struct_hiring({"hiring": {"total_open_roles": 0, "null_signal_note": "No ICP-relevant roles found, verified via careers page scrape 2026-07-01"}})["pass"] is True)
    check("hiring with roles passes", struct_hiring({"hiring": {"total_open_roles": 5}})["pass"] is True)

    # dash-next-to-citation
    d = struct_dash_citation({"x": {"value": "—", "source_url": "https://sec.gov/a"}})
    check("dash next to citation flagged", d["pass"] is False)
    d = struct_dash_citation({"x": {"value": "real", "source_url": "https://sec.gov/a"}})
    check("real value next to citation passes", d["pass"] is True)
    d = struct_dash_citation({"x": {"note": "", "source": "09d-hiring.md"}})
    check("empty next to non-http source NOT flagged", d["pass"] is True)

    # next_steps
    check("blank next_step action flagged",
          struct_next_steps({"next_steps": [{"action": "", "detail": "x" * 30}]})["pass"] is False)
    check("good next_step passes",
          struct_next_steps({"next_steps": [{"action": "Warm intro", "detail": "x" * 30}]})["pass"] is True)

    # partner
    check("crossbeam unexplained skip flagged",
          struct_partner({"partner_intel": {"co_sell": "query Crossbeam for overlap"}})["pass"] is False)
    check("crossbeam with marker passes",
          struct_partner({"partner_intel": {"co_sell": "Crossbeam", "crossbeam_data_available": False, "source_label": "gemini_search fallback"}})["pass"] is True)

    print(("\n✗ self-test FAILED" if fails else "\n✓ self-test passed"), file=sys.stderr)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="Deterministic mechanical factcheck gate for Algolia audits")
    ap.add_argument("--audit-data", help="direct path to {company}-audit-data.json")
    ap.add_argument("--audit-dir", default=os.environ.get("ALGOLIA_AUDIT_DIR", ""))
    ap.add_argument("--company")
    ap.add_argument("--rendered-html", help="path to rendered index.html for the screenshot-embed check")
    ap.add_argument("--check-urls", action="store_true", help="HTTP HEAD a sample of source URLs (network)")
    ap.add_argument("--url-sample", type=int, default=8)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())

    if not args.audit_data and not (args.audit_dir and args.company):
        ap.error("provide --audit-data PATH, or --audit-dir and --company (or set ALGOLIA_AUDIT_DIR)")

    result, code = run_all(audit_dir=args.audit_dir or None, company=args.company,
                           audit_data=args.audit_data, check_urls=args.check_urls,
                           url_sample=args.url_sample, rendered_html=args.rendered_html)
    print(json.dumps(result, indent=2))

    if "error" not in result:
        print(f"\n— Mechanical factcheck: {result['mechanical_action']} —", file=sys.stderr)
        s = result.get("structural", {})
        for name, d in s.items():
            status = "skip" if d.get("skipped") else ("PASS" if d.get("pass") else "FAIL")
            print(f"  [{status}] {name}" + (f" — {d['skipped']}" if d.get("skipped") else ""), file=sys.stderr)
        if result.get("warnings"):
            for w in result["warnings"]:
                print(f"  WARN: {w}", file=sys.stderr)
        for r in result["blocking_reasons"]:
            print(f"  BLOCK: {r}", file=sys.stderr)
    else:
        print(f"ERROR: {result['error']}", file=sys.stderr)
    sys.exit(code)


if __name__ == "__main__":
    main()
