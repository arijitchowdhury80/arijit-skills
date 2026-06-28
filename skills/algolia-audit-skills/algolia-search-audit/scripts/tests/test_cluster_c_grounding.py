"""
Tests for Cluster C hardening — financial/investor grounding + industry staleness.

Covers:
  industry_fallback_filter.py  — BUG-2 age gate on fallback + F1 Scout-markdown guard
  reconcile_financials.py       — deterministic 6-source tier + range + BUG-5 guard
  ground_quotes.py              — exact-substring grounding + recency reject < Jan 2025

Pure-logic tests only — no network. Scout HTTP path is exercised via the pure
evaluate_scout_markdown() guard, which is the load-bearing F1 decision.
"""

import os
import sys
import json
import tempfile
import importlib.util
from datetime import date

import pytest

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import industry_fallback_filter as iff
import reconcile_financials as rf
import ground_quotes as gq

# collect-financials.py has a hyphen — load it via importlib (matches test_scout_company).
_spec = importlib.util.spec_from_file_location(
    "collect_financials", os.path.join(parent_dir, "collect-financials.py")
)
collect_financials = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(collect_financials)


# ── BUG-2: industry fallback age gate ─────────────────────────────────────────

FIXED_TODAY = date(2026, 6, 28)  # anchor so age math is deterministic


def test_fallback_drops_stale_gt_24mo():
    """A benchmark dated 2023-01 (>24mo before fixed today) is DROPPED on the
    fallback path — the gate that previously only existed on the Tavily path."""
    results = [{"url": "https://baymard.com/x", "title": "old", "source_date": "2023-01-01"}]
    kept, dropped = iff.filter_fallback_results(results, today=FIXED_TODAY)
    assert kept == []
    assert len(dropped) == 1
    assert dropped[0]["dropped_reason"] == "stale_gt_24mo"


def test_fallback_keeps_fresh_within_24mo():
    """A 2025 benchmark is kept and tagged websearch_fallback."""
    results = [{"url": "https://nrf.com/y", "title": "fresh", "source_date": "2025-06-01"}]
    kept, dropped = iff.filter_fallback_results(results, today=FIXED_TODAY)
    assert len(kept) == 1
    assert dropped == []
    assert kept[0]["collection_method"] == "websearch_fallback"
    assert kept[0]["stale_unknown"] is False


def test_fallback_unknown_date_kept_but_flagged():
    """Unknown/unparseable date is kept (matches Tavily path) but flagged so the LLM
    downgrades the label — not silently presented as fresh."""
    results = [{"url": "https://x.com/z", "title": "nodate", "source_date": None}]
    kept, dropped = iff.filter_fallback_results(results, today=FIXED_TODAY)
    assert len(kept) == 1
    assert kept[0]["stale_unknown"] is True
    assert kept[0]["age_months"] is None


def test_fallback_age_gate_matches_collect_industry_boundary():
    """Exactly 24 months old is KEPT; >24 is dropped — same boundary as
    collect-industry.is_stale (age_months > 24)."""
    # 24*30 = 720 days before today -> age_months == 24 -> kept
    from datetime import timedelta
    d24 = (FIXED_TODAY - timedelta(days=720)).isoformat()
    d25 = (FIXED_TODAY - timedelta(days=781)).isoformat()  # ~26 months -> dropped
    kept, dropped = iff.filter_fallback_results(
        [{"source_date": d24}, {"source_date": d25}], today=FIXED_TODAY
    )
    assert len(kept) == 1
    assert len(dropped) == 1


# ── F1: Scout empty-markdown guard ────────────────────────────────────────────

def test_scout_empty_markdown_flags_degraded():
    """Empty markdown (the Squarespace F1 failure) -> degraded + fallback_to_webfetch."""
    degraded, fallback, reason = iff.evaluate_scout_markdown("")
    assert degraded is True
    assert fallback is True
    assert reason == "scout_markdown_empty"


def test_scout_below_threshold_flags_degraded():
    """4-char markdown (the literal F1 measurement) is below threshold -> degraded."""
    degraded, fallback, reason = iff.evaluate_scout_markdown("hi\n\n")
    assert degraded is True
    assert fallback is True
    assert "below_threshold" in reason


def test_scout_good_markdown_accepted():
    """11.6K of clean markdown (the Baymard F3 win) -> not degraded, no fallback."""
    md = "search benchmark " * 1000  # ~17K chars
    degraded, fallback, reason = iff.evaluate_scout_markdown(md)
    assert degraded is False
    assert fallback is False
    assert reason == "ok"


def test_scout_never_silently_accepts_empty():
    """scout_benchmark_fetch returns a guarded dict even when Scout is unavailable —
    it does NOT return a falsely-clean result."""
    # Force scout_available -> False by pointing at an unreachable port.
    os.environ["SCOUT_URL"] = "http://127.0.0.1:1"
    try:
        out = iff.scout_benchmark_fetch("https://baymard.com/research")
    finally:
        os.environ.pop("SCOUT_URL", None)
    assert out["degraded"] is True
    assert out["fallback_to_webfetch"] is True


# ── reconcile_financials: money parsing ───────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("$1.2B", 1_200_000_000),
    ("1.2 billion", 1_200_000_000),
    ("$1,150,000,000", 1_150_000_000),
    ("900M", 900_000_000),
    ("$45.5 million", 45_500_000),
    (1_100_000_000, 1_100_000_000),
    ("250K", 250_000),
])
def test_parse_money_units(raw, expected):
    """Unit-aware parse — number+unit normalized together, not strip-then-parseFloat."""
    assert rf.parse_money(raw) == expected


def test_parse_money_unparseable_returns_none():
    assert rf.parse_money("undisclosed") is None
    assert rf.parse_money("") is None
    assert rf.parse_money(None) is None


# ── reconcile_financials: tier logic ──────────────────────────────────────────

def test_reconcile_high_3plus_within_20pct():
    """3 sources within ±20% of median -> HIGH."""
    res = rf.reconcile([
        {"source": "ecdb", "value": "$1.2B"},
        {"source": "linkedin", "value": 1_100_000_000},
        {"source": "trade_press", "value": "$1.15 billion"},
        {"source": "inc5000", "value": "$500M"},  # outlier, excluded from cluster
    ])
    assert res["revenue_confidence"] == "HIGH"
    assert res["agreeing_count"] >= 3
    assert res["revenue_estimate_range"]["min"] == 500_000_000
    assert res["revenue_estimate_range"]["max"] == 1_200_000_000


def test_reconcile_medium_exactly_2():
    """Exactly 2 sources agree within ±20% -> MEDIUM."""
    res = rf.reconcile([
        {"source": "ecdb", "value": "$1.0B"},
        {"source": "linkedin", "value": "$1.1B"},
        {"source": "trade_press", "value": "$300M"},
    ])
    assert res["revenue_confidence"] == "MEDIUM"
    assert res["agreeing_count"] == 2


def test_reconcile_low_single_source():
    """Single mention -> LOW."""
    res = rf.reconcile([{"source": "ecdb", "value": "$1.0B"}])
    assert res["revenue_confidence"] == "LOW"


def test_reconcile_emits_range_not_point():
    """A range (min/median/max) is always emitted — never a single collapsed number."""
    res = rf.reconcile([
        {"source": "a", "value": "$800M"},
        {"source": "b", "value": "$1.2B"},
    ])
    rng = res["revenue_estimate_range"]
    assert rng["min"] == 800_000_000
    assert rng["max"] == 1_200_000_000
    assert rng["min"] < rng["median"] < rng["max"] or rng["min"] <= rng["median"] <= rng["max"]


def test_reconcile_records_failed_sources():
    res = rf.reconcile([
        {"source": "ecdb", "value": "$1.0B"},
        {"source": "pitchbook", "value": "undisclosed"},
    ])
    assert "pitchbook" in res["sources_failed"]
    assert "ecdb" in res["revenue_sources"]


def test_reconcile_no_parseable_is_low():
    res = rf.reconcile([{"source": "x", "value": "n/a"}])
    assert res["revenue_confidence"] == "LOW"
    assert res["revenue_estimate_range"] is None


# ── BUG-5: overwrite guard ────────────────────────────────────────────────────

def _write_profile(path, company_type, key="meta"):
    with open(path, "w") as f:
        json.dump({key: {"company_type": company_type}}, f)


def test_bug5_blocks_private_clobbering_public():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.json")
        _write_profile(p, "public")
        with pytest.raises(rf.OverwriteError):
            rf.assert_no_overwrite(p, "private")


def test_bug5_blocks_public_clobbering_private_underscore_meta():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.json")
        _write_profile(p, "private", key="_meta")  # supports _meta too
        with pytest.raises(rf.OverwriteError):
            rf.assert_no_overwrite(p, "public")


def test_bug5_allows_same_type_rewrite():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.json")
        _write_profile(p, "private")
        assert rf.assert_no_overwrite(p, "private") == "private"


def test_bug5_force_bypasses():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.json")
        _write_profile(p, "public")
        assert rf.assert_no_overwrite(p, "private", force=True) == "public"


def test_bug5_no_file_allows():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.json")
        assert rf.assert_no_overwrite(p, "private") is None


# ── BUG-5: collect-financials.py script-level .md guard ───────────────────────

def test_md_marker_detects_public():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.md")
        with open(p, "w") as f:
            f.write("<!-- company_type: public -->\n# Acme — Financial Profile\n")
        assert collect_financials.detect_existing_company_type(p) == "public"


def test_md_marker_detects_private():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.md")
        with open(p, "w") as f:
            f.write("<!-- company_type: private -->\n# Acme — Financial Profile\n")
        assert collect_financials.detect_existing_company_type(p) == "private"


def test_md_legacy_ticker_inferred_public():
    """Legacy public file (no marker) inferred from the **Ticker:** line."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.md")
        with open(p, "w") as f:
            f.write("# Acme — Financial Profile\n**Ticker:** ACME\n")
        assert collect_financials.detect_existing_company_type(p) == "public"


def test_md_missing_returns_none():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.md")
        assert collect_financials.detect_existing_company_type(p) is None


def test_md_overwrite_guard_blocks_cross_type(capsys):
    """overwrite_guard exits 2 when a private write hits an existing public .md."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.md")
        with open(p, "w") as f:
            f.write("<!-- company_type: public -->\n# Acme\n")
        with pytest.raises(SystemExit) as exc:
            collect_financials.overwrite_guard(p, "private", force=False)
        assert exc.value.code == 2


def test_md_overwrite_guard_same_type_proceeds():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.md")
        with open(p, "w") as f:
            f.write("<!-- company_type: private -->\n# Acme\n")
        # Same type -> returns None (proceed), no SystemExit
        assert collect_financials.overwrite_guard(p, "private", force=False) is None


def test_md_overwrite_guard_force_backs_up():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "08-financial-profile.md")
        with open(p, "w") as f:
            f.write("<!-- company_type: public -->\n# Acme\n")
        collect_financials.overwrite_guard(p, "private", force=True)
        assert os.path.exists(p.replace(".md", ".public.bak"))


# ── ground_quotes: substring grounding + recency ──────────────────────────────

SOURCE = (
    "Operator: Thank you. Our first question comes from the line of an analyst.\n"
    'John Smith, CEO: We are investing heavily in search and personalization to '
    "improve our digital customer experience this year.\n"
)


def test_quote_verbatim_grounded_and_recent_accepted():
    v = gq.check_quote(
        quote="We are investing heavily in search and personalization",
        source_text=SOURCE,
        source_date="2025-03-14",
    )
    assert v["accepted"] is True
    assert v["grounded"] is True
    assert v["recent"] is True


def test_quote_paraphrase_rejected_not_grounded():
    """A paraphrase is NOT an exact substring -> rejected (the hallucination class)."""
    v = gq.check_quote(
        quote="We are pouring money into search technology",  # paraphrase
        source_text=SOURCE,
        source_date="2025-03-14",
    )
    assert v["accepted"] is False
    assert v["grounded"] is False
    assert any("not_grounded" in r for r in v["reasons"])


def test_quote_too_old_rejected():
    """Verbatim but dated 2024 -> rejected on recency (< Jan 2025)."""
    v = gq.check_quote(
        quote="We are investing heavily in search and personalization",
        source_text=SOURCE,
        source_date="2024-11-01",
    )
    assert v["accepted"] is False
    assert v["recent"] is False
    assert any("too_old" in r for r in v["reasons"])


def test_quote_missing_date_rejected_fail_closed():
    v = gq.check_quote(
        quote="We are investing heavily in search and personalization",
        source_text=SOURCE,
        source_date=None,
    )
    assert v["accepted"] is False
    assert any("recency_unverified" in r for r in v["reasons"])


def test_quote_smart_quote_normalization_still_grounds():
    """Curly quotes/dashes in the source still match a straight-quote candidate."""
    src = "She said: “We will modernize search—finally” in 2025."
    v = gq.check_quote(
        quote='We will modernize search-finally',
        source_text=src,
        source_date="2025-02-01",
    )
    assert v["grounded"] is True


def test_filter_quotes_splits_accepted_rejected():
    quotes = [
        {"quote": "We are investing heavily in search and personalization",
         "source_date": "2025-03-14", "speaker": "John Smith"},
        {"quote": "totally made up never said this",
         "source_date": "2025-03-14", "speaker": "Ghost"},
    ]
    accepted, rejected = gq.filter_quotes(quotes, SOURCE)
    assert len(accepted) == 1
    assert len(rejected) == 1
    assert accepted[0]["speaker"] == "John Smith"


def test_recency_floor_is_jan_2025():
    assert gq.RECENCY_FLOOR == date(2025, 1, 1)
