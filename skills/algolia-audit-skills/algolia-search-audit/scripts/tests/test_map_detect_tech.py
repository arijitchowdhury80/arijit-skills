#!/usr/bin/env python3
"""Tests for map-detect-tech.py — full tech-stack JSON bridge.

Verifies that detect-search --full-tech JSON is translated deterministically
into 02-tech-stack.json:
  - detected[] grouped correctly by category
  - search block folded into search_vendors (no double-listing)
  - (page: X) suffix parsed and merged across duplicate tech entries
  - confidence precedence: confirmed > likely > likely-opendb
  - source preference: detect-search over opendb on dedup
  - empty schema categories always present as []
  - limitations and not_detectable_note carried through
  - bot_blocked state carried through
"""
import importlib.util
import json
import os
import sys

import pytest

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

_spec = importlib.util.spec_from_file_location(
    "map_detect_tech", os.path.join(parent_dir, "map-detect-tech.py")
)
mdt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mdt)


# ── fixtures ─────────────────────────────────────────────────────────────────

def _full_tech_fixture():
    """Representative --full-tech payload:
    - ecommerce_platform: Shopify confirmed+detect-search (home) AND Shopify likely+opendb (plp)
      → one merged entry: confirmed, detect-search, pages ["home","plp"]
    - analytics: Google Analytics confirmed+detect-search (home)
    - tag_manager: Google Tag Manager likely+opendb (home)
    - cdn_waf: Cloudflare confirmed+detect-search (home)
    - search: Algolia (should fold into search_vendors, NOT appear in tech_stack)
    - All other categories absent → present as [] in output
    """
    return {
        "url": "https://www.example-shop.com",
        "pages_visited": ["home", "plp", "pdp"],
        "detected": [
            # ecommerce_platform — confirmed detect-search entry (home)
            {
                "category": "ecommerce_platform",
                "technology": "Shopify",
                "confidence": "confirmed",
                "evidence": "Shopify checkout API detected (page: home)",
                "source": "detect-search",
            },
            # ecommerce_platform — duplicate Shopify, lower confidence + opendb (plp)
            # After dedup: pages merged, "confirmed"+"detect-search" wins over "likely"+"opendb"
            {
                "category": "ecommerce_platform",
                "technology": "Shopify",
                "confidence": "likely",
                "evidence": "Shopify meta tag found (page: plp)",
                "source": "opendb",
            },
            # analytics — single entry, source opendb (kept as-is, no dup)
            {
                "category": "analytics",
                "technology": "Google Analytics",
                "confidence": "confirmed",
                "evidence": "GA4 measurement ID found (page: home)",
                "source": "detect-search",
            },
            # tag_manager — opendb source, should surface in output with source=opendb
            {
                "category": "tag_manager",
                "technology": "Google Tag Manager",
                "confidence": "likely-opendb",
                "evidence": "GTM container script (page: home)",
                "source": "opendb",
            },
            # cdn_waf — confirmed
            {
                "category": "cdn_waf",
                "technology": "Cloudflare",
                "confidence": "confirmed",
                "evidence": "CF-RAY response header (page: home)",
                "source": "detect-search",
            },
            # search — MUST be ignored here; folded via the search block instead
            {
                "category": "search",
                "technology": "Algolia",
                "confidence": "confirmed",
                "evidence": "Algolia API call observed (page: home)",
                "source": "detect-search",
            },
        ],
        "search": {
            "search_detected": True,
            "search_platform": "Algolia",
            "platform_id": "algolia",
            "platform_details": {
                "app_id": "EXAMPLEAPPID",
                "api_key": "exampleapikey123",
                "indexes": ["prod_products"],
            },
            "all_platforms_found": [
                {
                    "search_platform": "Algolia",
                    "platform_id": "algolia",
                    "confidence": "confirmed",
                    "platform_details": {
                        "app_id": "EXAMPLEAPPID",
                        "api_key": "exampleapikey123",
                        "indexes": ["prod_products"],
                    },
                    "search_requests": [
                        {
                            "url": "https://exampleappid-dsn.algolia.net/1/indexes/prod_products/query",
                            "method": "POST",
                        }
                    ],
                }
            ],
            "search_requests": [
                {
                    "url": "https://exampleappid-dsn.algolia.net/1/indexes/prod_products/query",
                    "method": "POST",
                }
            ],
        },
        "categories_covered": ["ecommerce_platform", "analytics", "tag_manager", "cdn_waf", "search"],
        "not_detectable_note": "backend services and server-side rendering tech not visible",
        "network_calls_total": 200,
        "bot_blocked": False,
        "error": None,
        "timestamp": "2026-06-29T10:00:00Z",
    }


def _empty_blocked_fixture():
    """Minimal payload: no detections, search not found, bot blocked."""
    return {
        "url": "https://www.walled-site.com",
        "pages_visited": ["home"],
        "detected": [],
        "search": {
            "search_detected": False,
            "search_platform": None,
            "platform_id": None,
            "platform_details": {},
            "all_platforms_found": [],
            "search_requests": [],
        },
        "not_detectable_note": "site blocked bot before any content loaded",
        "network_calls_total": 3,
        "bot_blocked": True,
        "error": None,
        "timestamp": "2026-06-29T11:00:00Z",
    }


# ── helpers ───────────────────────────────────────────────────────────────────

def _tech_by_name(stack_list, name):
    """Return the entry in a tech_stack category list whose technology == name."""
    matches = [e for e in stack_list if e["technology"] == name]
    assert len(matches) == 1, f"Expected exactly one '{name}' entry, got {matches}"
    return matches[0]


# ── representative fixture tests ──────────────────────────────────────────────

class TestFullTechFixture:

    def setup_method(self):
        self.result = mdt.map_tech(_full_tech_fixture())

    # domain + metadata
    def test_domain_parsed_from_url(self):
        assert self.result["domain"] == "example-shop.com"

    def test_detection_method_verbatim(self):
        assert self.result["detection_method"] == mdt.DETECTION_METHOD

    def test_pages_visited_carried(self):
        assert self.result["pages_visited"] == ["home", "plp", "pdp"]

    # tech_stack grouping
    def test_ecommerce_platform_has_shopify(self):
        assert len(self.result["tech_stack"]["ecommerce_platform"]) == 1

    def test_shopify_pages_merged_from_both_entries(self):
        entry = _tech_by_name(self.result["tech_stack"]["ecommerce_platform"], "Shopify")
        assert "home" in entry["pages"]
        assert "plp" in entry["pages"]

    def test_shopify_confidence_precedence_confirmed_beats_likely(self):
        entry = _tech_by_name(self.result["tech_stack"]["ecommerce_platform"], "Shopify")
        assert entry["confidence"] == "confirmed"

    def test_shopify_source_detect_search_beats_opendb(self):
        entry = _tech_by_name(self.result["tech_stack"]["ecommerce_platform"], "Shopify")
        assert entry["source"] == "detect-search"

    def test_analytics_single_entry(self):
        entries = self.result["tech_stack"]["analytics"]
        assert len(entries) == 1
        assert entries[0]["technology"] == "Google Analytics"

    def test_analytics_pages_parsed(self):
        entry = self.result["tech_stack"]["analytics"][0]
        assert entry["pages"] == ["home"]

    def test_tag_manager_opendb_source_preserved(self):
        entry = _tech_by_name(self.result["tech_stack"]["tag_manager"], "Google Tag Manager")
        assert entry["source"] == "opendb"

    def test_cdn_waf_has_cloudflare(self):
        entries = self.result["tech_stack"]["cdn_waf"]
        assert any(e["technology"] == "Cloudflare" for e in entries)

    # search NOT in tech_stack
    def test_search_category_absent_from_tech_stack(self):
        assert "search" not in self.result["tech_stack"]

    def test_algolia_not_listed_in_any_tech_stack_category(self):
        for cat, entries in self.result["tech_stack"].items():
            names = [e["technology"] for e in entries]
            assert "Algolia" not in names, f"Algolia unexpectedly in tech_stack[{cat}]"

    # empty categories
    def test_all_schema_categories_present(self):
        for cat in mdt.TECH_STACK_CATEGORIES:
            assert cat in self.result["tech_stack"], f"Missing category: {cat}"

    def test_empty_categories_are_empty_lists(self):
        populated = {"ecommerce_platform", "analytics", "tag_manager", "cdn_waf"}
        for cat in mdt.TECH_STACK_CATEGORIES:
            if cat not in populated:
                assert self.result["tech_stack"][cat] == [], \
                    f"Expected [] for {cat}, got {self.result['tech_stack'][cat]}"

    # search_vendors folding
    def test_search_vendors_has_algolia(self):
        vendors = self.result["search_vendors"]
        assert len(vendors) == 1
        assert vendors[0]["vendor"] == "Algolia"
        assert vendors[0]["platform_id"] == "algolia"

    def test_algolia_detected_true(self):
        assert self.result["algolia_detected"] is True

    def test_search_vendor_network_endpoint_present(self):
        vendor = self.result["search_vendors"][0]
        assert vendor["network_endpoint"] is not None
        assert "algolia.net" in vendor["network_endpoint"]

    def test_search_vendor_details_present(self):
        vendor = self.result["search_vendors"][0]
        assert vendor["details"].get("app_id") == "EXAMPLEAPPID"

    # passthrough fields
    def test_not_detectable_note_carried(self):
        assert "backend services" in self.result["not_detectable_note"]

    def test_bot_blocked_false_carried(self):
        assert self.result["bot_blocked"] is False

    def test_limitations_verbatim(self):
        lims = self.result["limitations"]
        assert len(lims) == 2
        assert any("client-side" in l for l in lims)
        assert any("historical" in l for l in lims)

    # no fabricated entries
    def test_no_extra_tech_entries_fabricated(self):
        # Only ecommerce_platform, analytics, tag_manager, cdn_waf should be non-empty
        non_empty = {cat for cat, entries in self.result["tech_stack"].items() if entries}
        assert non_empty == {"ecommerce_platform", "analytics", "tag_manager", "cdn_waf"}


# ── empty / bot-blocked input ─────────────────────────────────────────────────

class TestEmptyBotBlockedInput:

    def setup_method(self):
        self.result = mdt.map_tech(_empty_blocked_fixture())

    def test_all_tech_stack_categories_empty(self):
        for cat in mdt.TECH_STACK_CATEGORIES:
            assert self.result["tech_stack"][cat] == [], \
                f"Expected [] for {cat}, got {self.result['tech_stack'][cat]}"

    def test_search_vendors_empty(self):
        assert self.result["search_vendors"] == []

    def test_algolia_detected_false(self):
        assert self.result["algolia_detected"] is False

    def test_bot_blocked_true_carried(self):
        assert self.result["bot_blocked"] is True

    def test_not_detectable_note_carried(self):
        assert "blocked bot" in self.result["not_detectable_note"]

    def test_all_schema_categories_present(self):
        for cat in mdt.TECH_STACK_CATEGORIES:
            assert cat in self.result["tech_stack"]


# ── unit: _parse_pages ────────────────────────────────────────────────────────

def test_parse_pages_single():
    assert mdt._parse_pages("Shopify checkout detected (page: home)") == ["home"]


def test_parse_pages_multi():
    assert mdt._parse_pages("Script seen (page: home, plp)") == ["home", "plp"]


def test_parse_pages_no_suffix():
    assert mdt._parse_pages("No page suffix here") == []


def test_parse_pages_empty_string():
    assert mdt._parse_pages("") == []


def test_parse_pages_strips_whitespace():
    assert mdt._parse_pages("foo (page:  home ,  pdp )") == ["home", "pdp"]


# ── unit: confidence precedence ───────────────────────────────────────────────

def test_confidence_rank_ordering():
    assert mdt._confidence_rank("confirmed") > mdt._confidence_rank("likely")
    assert mdt._confidence_rank("likely") > mdt._confidence_rank("likely-opendb")
    assert mdt._confidence_rank("likely-opendb") >= 0


def test_dedup_confirmed_beats_likely_opendb():
    """When same tech appears twice with different confidence, confirmed wins."""
    detected = [
        {
            "category": "analytics",
            "technology": "Mixpanel",
            "confidence": "likely-opendb",
            "evidence": "BuiltWith signal (page: home)",
            "source": "opendb",
        },
        {
            "category": "analytics",
            "technology": "Mixpanel",
            "confidence": "confirmed",
            "evidence": "Mixpanel API call intercepted (page: plp)",
            "source": "detect-search",
        },
    ]
    data = {
        "url": "https://test.com",
        "pages_visited": ["home", "plp"],
        "detected": detected,
        "search": {"search_detected": False},
        "bot_blocked": False,
    }
    result = mdt.map_tech(data)
    entries = result["tech_stack"]["analytics"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["confidence"] == "confirmed"
    assert entry["source"] == "detect-search"
    assert "home" in entry["pages"]
    assert "plp" in entry["pages"]


def test_dedup_same_confidence_detect_search_beats_opendb():
    """When confidence is identical, detect-search source wins over opendb."""
    detected = [
        {
            "category": "cdn_waf",
            "technology": "Fastly",
            "confidence": "likely",
            "evidence": "opendb signal (page: home)",
            "source": "opendb",
        },
        {
            "category": "cdn_waf",
            "technology": "Fastly",
            "confidence": "likely",
            "evidence": "Fastly response header (page: pdp)",
            "source": "detect-search",
        },
    ]
    data = {
        "url": "https://test.com",
        "pages_visited": ["home", "pdp"],
        "detected": detected,
        "search": {"search_detected": False},
        "bot_blocked": False,
    }
    result = mdt.map_tech(data)
    entry = result["tech_stack"]["cdn_waf"][0]
    assert entry["source"] == "detect-search"
    assert entry["confidence"] == "likely"


# ── unit: search_vendors with no all_platforms_found ─────────────────────────

def test_search_vendors_fallback_to_primary_fields():
    """When all_platforms_found is empty, uses primary search block fields."""
    data = {
        "url": "https://site.com",
        "pages_visited": ["home"],
        "detected": [],
        "search": {
            "search_detected": True,
            "search_platform": "Coveo",
            "platform_id": "coveo",
            "platform_details": {"org_id": "coveoorg"},
            "all_platforms_found": [],
            "search_requests": [{"url": "https://platform.cloud.coveo.com/rest/search", "method": "GET"}],
        },
        "bot_blocked": False,
    }
    result = mdt.map_tech(data)
    assert len(result["search_vendors"]) == 1
    v = result["search_vendors"][0]
    assert v["vendor"] == "Coveo"
    assert v["platform_id"] == "coveo"
    assert v["confidence"] == "confirmed"
    assert v["network_endpoint"] == "https://platform.cloud.coveo.com/rest/search"
    assert result["algolia_detected"] is False


# ── unit: domain parsing ──────────────────────────────────────────────────────

def test_domain_strips_www():
    data = {"url": "https://www.petsmart.com", "detected": [], "search": {"search_detected": False}, "bot_blocked": False}
    result = mdt.map_tech(data)
    assert result["domain"] == "petsmart.com"


def test_domain_override_takes_precedence():
    data = {"url": "https://www.example.com", "detected": [], "search": {"search_detected": False}, "bot_blocked": False}
    result = mdt.map_tech(data, domain_override="my-override.com")
    assert result["domain"] == "my-override.com"


# ── unit: _load ───────────────────────────────────────────────────────────────

def test_load_from_file(tmp_path):
    payload = {"url": "https://test.com", "detected": [], "search": {"search_detected": False}, "bot_blocked": False}
    p = tmp_path / "full-tech.json"
    p.write_text(json.dumps(payload))
    loaded = mdt._load(str(p))
    assert loaded["url"] == "https://test.com"


def test_load_handles_list_wrapping(tmp_path):
    payload = {"url": "https://test.com", "detected": [], "search": {"search_detected": False}, "bot_blocked": False}
    p = tmp_path / "bulk.json"
    p.write_text(json.dumps([payload]))
    loaded = mdt._load(str(p))
    assert loaded["url"] == "https://test.com"


def test_load_raises_on_empty_list(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text("[]")
    with pytest.raises(ValueError, match="empty list"):
        mdt._load(str(p))


# ── unit: bad payload ─────────────────────────────────────────────────────────

def test_map_tech_raises_on_non_dict():
    with pytest.raises(ValueError):
        mdt.map_tech(["not", "a", "dict"])


# ── main() CLI ────────────────────────────────────────────────────────────────

def test_main_prints_json_to_stdout(tmp_path, capsys):
    payload = _full_tech_fixture()
    p = tmp_path / "full-tech.json"
    p.write_text(json.dumps(payload))
    rc = mdt.main(["--detect", str(p)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["algolia_detected"] is True
    assert "tech_stack" in out


def test_main_domain_override(tmp_path, capsys):
    payload = _empty_blocked_fixture()
    p = tmp_path / "ft.json"
    p.write_text(json.dumps(payload))
    rc = mdt.main(["--detect", str(p), "--domain", "override.com"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["domain"] == "override.com"


def test_main_returns_2_on_bad_json(tmp_path, capsys):
    p = tmp_path / "bad.json"
    p.write_text("not json {{{")
    rc = mdt.main(["--detect", str(p)])
    assert rc == 2


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
