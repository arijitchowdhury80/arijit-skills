#!/usr/bin/env python3
"""Tests for collect-hiring.py v4.0 deterministic classifier + cross-layer dedup."""
import sys
import os
import importlib.util

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

spec = importlib.util.spec_from_file_location(
    "collect_hiring", os.path.join(parent_dir, "collect-hiring.py"))
ch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ch)


# ── classify() (the previously-dead, now-wired core) ─────────────────────────

def test_classify_economic_buyer_tier1():
    tier, score, _ = ch.classify("VP, Digital Commerce")
    assert tier == 1
    assert score >= 9


def test_classify_technical_buyer_tier2():
    tier, score, _ = ch.classify("Senior Software Engineer, Search Platform",
                                 "Build search relevance with Elasticsearch")
    assert tier == 2
    # base 7 + 2 HIGH kw (search relevance, Elasticsearch) → boosted
    assert score >= 8


def test_classify_champion_tier3():
    tier, _, _ = ch.classify("Product Manager, Ecommerce")
    assert tier == 3


def test_classify_context_tier4():
    tier, score, _ = ch.classify("Retail Sales Associate")
    assert tier == 4
    assert score <= 4


def test_classify_icp_keywords_boost_score():
    _, score_plain, _ = ch.classify("Director of Ecommerce")
    _, score_kw, kws = ch.classify("Director of Ecommerce",
                                   "owns search, personalization, and Algolia")
    assert score_kw > score_plain
    assert "Algolia" in kws


# ── classify_roles(): batch + cross-layer dedup ──────────────────────────────

def test_dedup_by_job_id_across_layers():
    roles = [
        {"title": "VP Digital", "job_id": "REQ-100", "layer": 1, "url": "a"},
        {"title": "VP Digital", "job_id": "REQ-100", "layer": 2, "url": "b",
         "desc": "leads digital commerce and search"},
    ]
    out = ch.classify_roles(roles)
    assert out["deduped_count"] == 1
    role = out["classified"][0]
    assert role["dedup_collapsed"] is True
    assert role["seen_in_layers"] == [1, 2]
    # Richer description (longer) survives the merge.
    assert "search" in role["desc"]


def test_dedup_by_title_location_when_no_job_id():
    roles = [
        {"title": "Search Engineer", "location": "Remote", "layer": 1},
        {"title": "search engineer", "location": "remote", "layer": 2},
    ]
    out = ch.classify_roles(roles)
    assert out["deduped_count"] == 1
    assert out["classified"][0]["seen_in_layers"] == [1, 2]


def test_distinct_roles_not_collapsed():
    roles = [
        {"title": "VP Digital", "location": "NYC", "layer": 1},
        {"title": "VP Digital", "location": "LA", "layer": 1},
    ]
    out = ch.classify_roles(roles)
    assert out["deduped_count"] == 2


def test_tier_summary_counts():
    roles = [
        {"title": "VP Ecommerce"},
        {"title": "Search Engineer"},
        {"title": "Product Manager, Digital"},
        {"title": "Warehouse Associate"},
    ]
    out = ch.classify_roles(roles)
    ts = out["tier_summary"]
    assert ts["tier1"] == 1
    assert ts["tier2"] == 1
    assert ts["tier3"] == 1
    assert ts["tier4"] == 1


def test_classified_sorted_by_icp_score_desc():
    roles = [
        {"title": "Warehouse Associate"},
        {"title": "VP Digital Commerce", "desc": "search personalization Algolia"},
    ]
    out = ch.classify_roles(roles)
    scores = [r["icp_score"] for r in out["classified"]]
    assert scores == sorted(scores, reverse=True)


def test_empty_title_skipped():
    out = ch.classify_roles([{"title": ""}, {"title": "VP Digital"}])
    assert out["deduped_count"] == 1


def test_label_and_method_present():
    out = ch.classify_roles([{"title": "VP Digital"}])
    role = out["classified"][0]
    assert "OBSERVED" in role["label"]
    assert role["classification_method"].startswith("deterministic")
