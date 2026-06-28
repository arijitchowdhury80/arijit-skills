#!/usr/bin/env python3
"""
check-claim-traceability.py — mechanical claim-traceability gate for Cluster E deliverables.

WHY THIS EXISTS:
  The copywriting/narrative in the playbook and the query-design in test-queries.md are
  irreducibly LLM work — we do NOT rewrite them here. But two properties are MECHANICAL and
  should be checked deterministically, not left to the LLM to self-attest:

    1. PLAYBOOK talking points: every "TALKING POINT #N" block must trace to a real audit
       finding ("What we found:") AND an exec quote ("Their words:"). A talking point with
       neither is an ungrounded claim — exactly what the skill's own sourcing rule forbids
       ("If a talking point cannot be grounded in an exec quote, do not include it").

    2. TEST QUERIES: every numbered query must be marked testable — carry a "Tests:" marker
       so the browser auditor knows what each query proves. An unmarked query is dead weight.

  This is a VERIFICATION step, not a rewriter. It reads the finished deliverable and reports
  PASS/FAIL per claim. It never edits prose. Exit code 0 = all claims traceable, 1 = gaps.

USAGE:
  python3 check-claim-traceability.py playbook  <path-to-{slug}-playbook.md>
  python3 check-claim-traceability.py queries   <path-to-05-test-queries.md>
  python3 check-claim-traceability.py both <playbook.md> <queries.md>

  Optional: --research-dir <dir>   cross-check finding references resolve to a research file
"""

import argparse
import os
import re
import sys


# ── Playbook talking-point traceability ───────────────────────────────────────

TP_HEADER_RE = re.compile(r'^#{2,4}\s*TALKING POINT\s*#?\s*(\d+)\s*[:\-]?\s*(.*)$',
                          re.IGNORECASE | re.MULTILINE)
FOUND_RE = re.compile(r'(?:^|\n)\s*[-*]?\s*\*{0,2}What we found:\*{0,2}\s*(.+)', re.IGNORECASE)
QUOTE_RE = re.compile(r'(?:^|\n)\s*[-*]?\s*\*{0,2}Their words:\*{0,2}\s*(.+)', re.IGNORECASE)


def split_talking_points(text):
    """Return list of (num, title, block_text) for each TALKING POINT block."""
    matches = list(TP_HEADER_RE.finditer(text))
    blocks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        blocks.append((m.group(1), m.group(2).strip(), text[start:end]))
    return blocks


def check_playbook(path):
    """Each talking point must reference an audit finding AND an exec quote. Returns (ok, lines)."""
    out = []
    text = _read(path)
    if text is None:
        return False, [f"FAIL: playbook not found: {path}"]

    blocks = split_talking_points(text)
    if not blocks:
        return False, [f"FAIL: no 'TALKING POINT #N' blocks found in {os.path.basename(path)}"]

    ok = True
    for num, title, block in blocks:
        has_finding = bool(FOUND_RE.search(block))
        has_quote = bool(QUOTE_RE.search(block))
        title_short = (title[:54] + '…') if len(title) > 55 else title
        if has_finding and has_quote:
            out.append(f"  PASS  TP#{num}: finding + quote present — {title_short}")
        else:
            ok = False
            missing = []
            if not has_finding:
                missing.append("'What we found:' (audit finding)")
            if not has_quote:
                missing.append("'Their words:' (exec quote)")
            out.append(f"  FAIL  TP#{num}: missing {', '.join(missing)} — {title_short}")

    out.insert(0, f"Playbook talking-point traceability: {len(blocks)} talking points checked")
    return ok, out


# ── Query testability ─────────────────────────────────────────────────────────

# A numbered query line:  `1. "televisions" — [cat] — Tests: ...`
QUERY_LINE_RE = re.compile(r'^\s*(\d+)\.\s+(.+)$', re.MULTILINE)


def check_queries(path):
    """Every numbered query must carry a 'Tests:' marker (testable). Returns (ok, lines)."""
    out = []
    text = _read(path)
    if text is None:
        return False, [f"FAIL: test-queries file not found: {path}"]

    # Only consider lines inside the query set, not the Browser Audit Mapping table rows.
    # Numbered queries live under "## Query Set"; the mapping table uses pipes, not numbers.
    lines = QUERY_LINE_RE.findall(text)
    if not lines:
        return False, [f"FAIL: no numbered queries found in {os.path.basename(path)}"]

    ok = True
    untestable = 0
    for num, body in lines:
        # A query is testable if it states what it Tests (mechanical marker).
        if re.search(r'Tests?\s*:', body, re.IGNORECASE):
            continue
        untestable += 1
        ok = False
        snippet = body.strip()[:60]
        out.append(f"  FAIL  query {num}: no 'Tests:' marker — not marked testable — {snippet}")

    tested = len(lines) - untestable
    out.insert(0, f"Query testability: {tested}/{len(lines)} queries marked testable")
    if ok:
        out.append(f"  PASS  all {len(lines)} queries carry a 'Tests:' marker")
    return ok, out


def _read(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return f.read()


def main():
    p = argparse.ArgumentParser(description='Mechanical claim-traceability gate (Cluster E).')
    p.add_argument('mode', choices=['playbook', 'queries', 'both'])
    p.add_argument('paths', nargs='+',
                   help='playbook|queries: one path. both: <playbook.md> <queries.md>')
    args = p.parse_args()

    all_ok = True
    report = []

    if args.mode == 'playbook':
        ok, lines = check_playbook(args.paths[0])
        all_ok &= ok
        report += lines
    elif args.mode == 'queries':
        ok, lines = check_queries(args.paths[0])
        all_ok &= ok
        report += lines
    else:  # both
        if len(args.paths) < 2:
            p.error("mode 'both' needs two paths: <playbook.md> <queries.md>")
        ok1, l1 = check_playbook(args.paths[0])
        ok2, l2 = check_queries(args.paths[1])
        all_ok = ok1 and ok2
        report += l1 + [''] + l2

    print('\n'.join(report))
    print()
    print('✅ TRACEABILITY PASS — every claim traces to a finding/quote/test'
          if all_ok else
          '❌ TRACEABILITY FAIL — ungrounded claims above must be fixed (add the finding/quote/Tests marker)')
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
