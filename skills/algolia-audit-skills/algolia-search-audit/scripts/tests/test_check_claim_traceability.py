#!/usr/bin/env python3
"""Tests for check-claim-traceability.py — Cluster E mechanical claim gate."""
import importlib.util
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

spec = importlib.util.spec_from_file_location(
    "check_claim_traceability", os.path.join(parent_dir, "check-claim-traceability.py"))
cct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cct)


def _write(tmp_path, name, text):
    p = os.path.join(str(tmp_path), name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


# ── Playbook: every talking point needs finding + quote ───────────────────────

GOOD_TP = (
    "### TALKING POINT #1: \"Catalog is activity-based\"\n\n"
    "WHY IT LANDS:\n"
    "- What we found: Tested \"warm jacket\" — returned 3758 items, intent ignored.\n"
    "- Their words: \"digital is our point of difference\" — CEO, earnings call, 2026.\n\n"
)


def test_playbook_passes_when_grounded(tmp_path):
    p = _write(tmp_path, "pb.md", GOOD_TP)
    ok, lines = cct.check_playbook(p)
    assert ok is True
    assert any("PASS" in l for l in lines)


def test_playbook_fails_missing_quote(tmp_path):
    bad = (
        "### TALKING POINT #1: \"Ungrounded claim\"\n\n"
        "- What we found: some audit finding here.\n\n"  # no 'Their words:'
    )
    p = _write(tmp_path, "pb.md", bad)
    ok, lines = cct.check_playbook(p)
    assert ok is False
    assert any("Their words" in l for l in lines)


def test_playbook_fails_missing_finding(tmp_path):
    bad = (
        "### TALKING POINT #1: \"No finding\"\n\n"
        "- Their words: \"a quote\" — CEO, 2026.\n\n"  # no 'What we found:'
    )
    p = _write(tmp_path, "pb.md", bad)
    ok, lines = cct.check_playbook(p)
    assert ok is False
    assert any("What we found" in l for l in lines)


def test_playbook_fails_when_no_talking_points(tmp_path):
    p = _write(tmp_path, "pb.md", "# Playbook\n\nNo talking points here.\n")
    ok, lines = cct.check_playbook(p)
    assert ok is False


# ── Queries: every numbered query must be marked testable ─────────────────────

def test_queries_pass_when_all_marked_testable(tmp_path):
    text = (
        "## Query Set\n\n"
        "1. \"jackets\" — [Outerwear] — Tests: SAYT response\n"
        "2. \"backpacks\" — Tests: facet availability\n"
    )
    p = _write(tmp_path, "q.md", text)
    ok, lines = cct.check_queries(p)
    assert ok is True


def test_queries_fail_when_unmarked(tmp_path):
    text = (
        "## Query Set\n\n"
        "1. \"jackets\" — Tests: SAYT\n"
        "2. \"backpacks\"\n"  # no Tests: marker — untestable
    )
    p = _write(tmp_path, "q.md", text)
    ok, lines = cct.check_queries(p)
    assert ok is False
    assert any("query 2" in l for l in lines)


def test_queries_fail_when_none_found(tmp_path):
    p = _write(tmp_path, "q.md", "# Test Queries\n\nNo numbered queries.\n")
    ok, lines = cct.check_queries(p)
    assert ok is False


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([__file__, "-v"]))
