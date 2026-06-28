#!/usr/bin/env python3
"""Tests for map-detect-search.py — the canonical search-vendor oracle bridge.

Verifies that detect-search json is translated deterministically into the
canonical search-vendor fields consumed by 02-tech-stack.json (1B) and
04-competitors.json (1D), with BuiltWith retained as a secondary signal.
"""
import importlib.util
import os
import sys
from datetime import date

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

spec = importlib.util.spec_from_file_location(
    "map_detect_search", os.path.join(parent_dir, "map-detect-search.py"))
mds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mds)


# ── canonical_name ───────────────────────────────────────────────────────────

def test_known_platform_id_maps_to_display_name():
    assert mds.canonical_name("constructor_io") == "Constructor.io"
    assert mds.canonical_name("algolia") == "Algolia"


def test_unknown_platform_id_falls_back_to_titlecase():
    assert mds.canonical_name("brand_new_vendor") == "Brand New Vendor"


def test_unknown_platform_id_prefers_raw_name_when_present():
    assert mds.canonical_name("xyz", raw_name="XYZ Search") == "XYZ Search"


# ── map_verdict: the active/algolia path (PetSmart-shaped, proxied) ──────────

def _petsmart_detect():
    # Shape mirrors detect-search.js output for PetSmart (proxied Algolia).
    return {
        "url": "https://www.petsmart.com",
        "search_detected": True,
        "search_platform": "Algolia",
        "platform_id": "algolia",
        "platform_details": {
            "app_id": "97P6EWKR25",
            "api_key": "89538b14986f30460d07967cc3717153",
            "agent": "Algolia for JavaScript (4.24.0)",
            "indexes": ["p-US_products"],
        },
        "search_requests": [{"url": "https://www.petsmart.com/api/search", "method": "POST"}],
        "network_calls_total": 245,
        "search_calls_count": 4,
        "bot_blocked": False,
        "error": None,
    }


def test_active_algolia_verdict():
    out = mds.map_verdict(_petsmart_detect())
    assert out["search_vendor"] == "Algolia"
    assert out["search_vendor_status"] == "ACTIVE"
    assert out["search_vendor_oracle"] == "detect-search"
    assert out["search_vendor_network_confirmed"] is True
    assert out["algolia_detected"] is True
    assert out["search_vendor_details"]["app_id"] == "97P6EWKR25"
    assert out["search_vendor_network_endpoint"] == "https://www.petsmart.com/api/search"
    assert out["network_check_date"] == date.today().isoformat()


def test_non_algolia_vendor_not_flagged_as_algolia():
    detect = {
        "search_detected": True, "search_platform": "Constructor.io",
        "platform_id": "constructor_io", "platform_details": {"api_key": "key_x"},
        "search_requests": [], "bot_blocked": False,
    }
    out = mds.map_verdict(detect)
    assert out["search_vendor"] == "Constructor.io"
    assert out["search_vendor_status"] == "ACTIVE"
    assert out["algolia_detected"] is False


# ── WAF block is its own status, NOT silently "undetected" ───────────────────

def test_waf_block_is_distinct_status():
    detect = {"search_detected": False, "platform_id": None, "bot_blocked": True,
              "search_requests": []}
    out = mds.map_verdict(detect)
    assert out["search_vendor_status"] == "UNCONFIRMED_WAF_BLOCK"
    assert out["search_vendor"] is None
    assert out["search_vendor_network_confirmed"] is False


def test_clean_run_no_search_is_undetected():
    detect = {"search_detected": False, "platform_id": None, "bot_blocked": False,
              "search_requests": []}
    out = mds.map_verdict(detect)
    assert out["search_vendor_status"] == "UNDETECTED"
    assert out["search_vendor"] is None


# ── BuiltWith stays a SECONDARY signal — agreement flag ──────────────────────

def test_builtwith_agreement_true_when_matches():
    out = mds.map_verdict(_petsmart_detect(), builtwith_vendor="Algolia")
    assert out["search_vendor_builtwith"] == "Algolia"
    assert out["search_vendor_agreement"] is True


def test_builtwith_disagreement_flagged():
    out = mds.map_verdict(_petsmart_detect(), builtwith_vendor="Coveo")
    assert out["search_vendor_builtwith"] == "Coveo"
    # detect-search (network truth) wins; the disagreement is surfaced, not hidden.
    assert out["search_vendor"] == "Algolia"
    assert out["search_vendor_agreement"] is False


def test_builtwith_omitted_means_no_agreement_field_pollution():
    out = mds.map_verdict(_petsmart_detect())
    assert "search_vendor_agreement" not in out


# ── bulk-list payload (detect-search non-csv bulk emits a list) ──────────────

def test_load_handles_list_payload(tmp_path):
    import json
    p = tmp_path / "bulk.json"
    p.write_text(json.dumps([_petsmart_detect()]))
    loaded = mds._load(str(p))
    assert loaded["platform_id"] == "algolia"


def test_bad_payload_raises():
    import pytest
    with pytest.raises(ValueError):
        mds.map_verdict(["not", "a", "dict"])


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
