#!/usr/bin/env python3
"""map-detect-search.py — canonical search-vendor oracle bridge.

Cluster B wiring (search-vendor truth). `detect-search` (Playwright packet
inspection at ~/.claude/skills/detect-search/detect-search.js) is the canonical,
deterministic oracle for "what search vendor does site X run". This script
translates ITS json output into the search-vendor fields that
`02-tech-stack.json` (techstack 1B) and `04-competitors.json` (competitors 1D)
consume — so the live skills stop doing LLM pattern-matching-from-BuiltWith and
instead read a deterministic verdict.

BuiltWith stays a SECONDARY signal: this script never erases BuiltWith's
`search_vendor`; it layers the network-confirmed verdict on top and records both,
flagging disagreement so the LLM (and factcheck) can see it.

Usage
-----
  # from a detect-search json file (single-object form, `--no-csv`):
  python3 map-detect-search.py --detect path/to/detect.json

  # piping detect-search output straight in:
  node ~/.claude/skills/detect-search/detect-search.js https://site.com \
    | python3 map-detect-search.py --detect -

  # cross-check against what BuiltWith already found (optional, enables agreement flag):
  python3 map-detect-search.py --detect detect.json --builtwith-vendor "Algolia"

Output: a json object on stdout with the canonical fields. Pure stdlib, no network,
no LLM. Deterministic: same input -> same output.
"""
import argparse
import json
import sys
from datetime import date

# detect-search platform_id -> canonical display name used in the audit JSON.
# Mirrors the `id`/`name` pairs in detect-search.js. Unknown ids pass through
# title-cased so a newly-added detector still surfaces a usable vendor name.
PLATFORM_NAMES = {
    "algolia": "Algolia",
    "constructor_io": "Constructor.io",
    "coveo": "Coveo",
    "bloomreach": "Bloomreach",
    "searchspring": "Searchspring",
    "elasticsearch": "Elasticsearch",
    "swiftype": "Swiftype",
    "yext": "Yext",
    "klevu": "Klevu",
    "typesense": "Typesense",
    "meilisearch": "Meilisearch",
    "doofinder": "Doofinder",
    "google_retail": "Google Retail",
    "unbxd": "Unbxd",
    "hawksearch": "HawkSearch",
    "attraqt": "Attraqt",
    "nosto": "Nosto",
    "loop54": "Loop54",
    "fast_simon": "Fast Simon",
    "lucidworks": "Lucidworks",
}


def canonical_name(platform_id, raw_name=None):
    if not platform_id:
        return None
    if platform_id in PLATFORM_NAMES:
        return PLATFORM_NAMES[platform_id]
    if raw_name:
        return raw_name
    return platform_id.replace("_", " ").title()


def map_verdict(detect, builtwith_vendor=None):
    """Translate a single detect-search result dict into canonical fields.

    Returns a flat dict ready to merge into 02-tech-stack.json / 04-competitors.json.
    """
    if not isinstance(detect, dict):
        raise ValueError("detect-search payload must be a json object")

    detected = bool(detect.get("search_detected"))
    bot_blocked = bool(detect.get("bot_blocked"))
    platform_id = detect.get("platform_id")
    raw_name = detect.get("search_platform")
    vendor = canonical_name(platform_id, raw_name) if detected else None
    details = detect.get("platform_details") or {}

    # Status precedence: a live network call beats everything; a WAF block is its
    # own finding (NOT silently downgraded to "undetected"); only a clean run with
    # no search call is "undetected".
    if detected and vendor:
        status = "ACTIVE"  # network-confirmed by packet inspection
    elif bot_blocked:
        status = "UNCONFIRMED_WAF_BLOCK"
    else:
        status = "UNDETECTED"

    out = {
        "search_vendor": vendor,
        "search_vendor_status": status,
        "search_vendor_oracle": "detect-search",
        "search_vendor_network_confirmed": detected and bool(vendor),
        "search_vendor_network_endpoint": _first_endpoint(detect),
        "search_vendor_details": {
            "app_id": details.get("app_id"),
            "api_key": details.get("api_key"),
            "indexes": details.get("indexes"),
            "agent": details.get("agent"),
            "org_id": details.get("org_id"),
            "site_id": details.get("site_id"),
        },
        "network_check_date": date.today().isoformat(),
        "network_check_note": _note(detect, status),
        "algolia_detected": (vendor == "Algolia"),
    }

    # BuiltWith stays a secondary signal — record it and whether the two agree.
    if builtwith_vendor is not None:
        bw = builtwith_vendor.strip() or None
        out["search_vendor_builtwith"] = bw
        if bw and vendor:
            out["search_vendor_agreement"] = (
                bw.lower() == vendor.lower()
            )
        else:
            out["search_vendor_agreement"] = None
    return out


def _first_endpoint(detect):
    reqs = detect.get("search_requests") or []
    if reqs and isinstance(reqs, list) and isinstance(reqs[0], dict):
        return reqs[0].get("url")
    return None


def _note(detect, status):
    if status == "ACTIVE":
        n = detect.get("network_calls_total")
        c = detect.get("search_calls_count")
        return f"detect-search confirmed via network ({c} search call(s) of {n} total)"
    if status == "UNCONFIRMED_WAF_BLOCK":
        return "detect-search reached site but search call was bot-blocked (WAF) — stealth retry needed in Phase 2"
    return "detect-search ran but observed no search API call"


def _load(path):
    if path == "-":
        raw = sys.stdin.read()
    else:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    data = json.loads(raw)
    # Bulk (non-csv) mode emits a list; single mode emits one object.
    if isinstance(data, list):
        if not data:
            raise ValueError("detect-search returned an empty list")
        return data[0]
    return data


def main(argv=None):
    p = argparse.ArgumentParser(description="Map detect-search output to canonical audit search-vendor fields.")
    p.add_argument("--detect", required=True, help="path to detect-search json, or '-' for stdin")
    p.add_argument("--builtwith-vendor", default=None, help="vendor BuiltWith reported (secondary signal, optional)")
    args = p.parse_args(argv)
    try:
        detect = _load(args.detect)
        result = map_verdict(detect, builtwith_vendor=args.builtwith_vendor)
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
