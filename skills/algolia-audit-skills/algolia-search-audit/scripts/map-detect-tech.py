#!/usr/bin/env python3
"""map-detect-tech.py — full tech-stack JSON bridge.

Translates the output of `detect-search.js --full-tech` (which covers
ecommerce platform, analytics, CDN/WAF, etc. alongside search) into the
`02-tech-stack.json` audit schema consumed by algolia-intel-techstack (1B)
and downstream skills.

The search block in the --full-tech payload is folded into `search_vendors`
(richer than the `detected[]` "search" category items, which are skipped to
avoid double-listing).

Usage
-----
  # from a --full-tech json file:
  python3 map-detect-tech.py --detect path/to/full-tech.json

  # piping detect-search output straight in:
  node detect-search.js https://site.com --full-tech \\
    | python3 map-detect-tech.py --detect -

  # explicit domain override:
  python3 map-detect-tech.py --detect full-tech.json --domain petsmart.com

Output: the 02-tech-stack.json object on stdout. Pure stdlib, no network, no LLM.
Deterministic: same input -> same output.
"""
import argparse
import json
import re
import sys
from urllib.parse import urlparse

# All non-search categories the output schema declares (order determines key order).
TECH_STACK_CATEGORIES = [
    "ecommerce_platform",
    "analytics",
    "tag_manager",
    "cdn_waf",
    "personalization",
    "reviews_ugc",
    "consent_cmp",
    "ad_pixels",
    "payment_processors",
    "cdp",
    "frontend_framework",
    "marketing_automation",
    "hosting",
]

# Confidence ordering: higher index = higher precedence.
_CONFIDENCE_RANK = {
    "likely-opendb": 0,
    "likely": 1,
    "confirmed": 2,
}

LIMITATIONS = [
    "client-side only — backend tech invisible",
    "no historical/removed-tech (live load sees only current state)",
]

DETECTION_METHOD = "detect-search network fingerprinting (client-side, keyless)"

# Pattern: trailing "(page: home)" or "(page: home, plp)" on evidence strings.
_PAGE_RE = re.compile(r'\(page:\s*([^)]+)\)\s*$')


def _parse_pages(evidence):
    """Extract page labels from evidence '(page: home, plp)' suffix.

    Returns a list of stripped page strings, or [] if no suffix present.
    """
    if not evidence:
        return []
    m = _PAGE_RE.search(evidence)
    if not m:
        return []
    return [p.strip() for p in m.group(1).split(',') if p.strip()]


def _strip_page_suffix(evidence):
    """Return evidence text without the trailing (page: ...) suffix."""
    if not evidence:
        return evidence
    return _PAGE_RE.sub('', evidence).rstrip()


def _confidence_rank(c):
    return _CONFIDENCE_RANK.get(c or "", -1)


def _first_endpoint(search_requests):
    """Return the first URL from a search_requests list, or None."""
    if not search_requests or not isinstance(search_requests, list):
        return None
    for r in search_requests:
        if isinstance(r, dict) and r.get("url"):
            return r["url"]
    return None


def _group_by_category(detected):
    """Group and deduplicate detected[] items by category.

    Skips the "search" category (folded separately via the richer search block).
    Skips categories not in the output schema (forward-compat: unknown cats ignored).

    Dedup rules for same technology within a category:
      - Merged pages list (union, insertion order).
      - Highest confidence wins (confirmed > likely > likely-opendb).
      - Tie on confidence: prefer source "detect-search" over "opendb".
      - Winning entry's evidence text replaces the losing one's.
    """
    groups = {}  # category -> { tech_key -> entry dict }

    for item in detected:
        cat = item.get("category") or ""
        if cat == "search" or cat not in TECH_STACK_CATEGORIES:
            continue
        tech = item.get("technology") or ""
        if not tech:
            continue

        evidence = item.get("evidence") or ""
        confidence = item.get("confidence") or ""
        source = item.get("source") or ""
        pages = _parse_pages(evidence)
        clean_evidence = _strip_page_suffix(evidence)

        key = tech.lower()
        bucket = groups.setdefault(cat, {})

        if key not in bucket:
            bucket[key] = {
                "technology": tech,
                "confidence": confidence,
                "evidence": clean_evidence,
                "source": source,
                "pages": pages,
            }
        else:
            existing = bucket[key]
            # Merge pages (union, preserve insertion order).
            for p in pages:
                if p not in existing["pages"]:
                    existing["pages"].append(p)

            new_rank = _confidence_rank(confidence)
            old_rank = _confidence_rank(existing["confidence"])
            new_is_better = (
                new_rank > old_rank
                or (
                    new_rank == old_rank
                    and source == "detect-search"
                    and existing["source"] != "detect-search"
                )
            )
            if new_is_better:
                existing["confidence"] = confidence
                existing["evidence"] = clean_evidence
                existing["source"] = source
            # pages already merged above; existing keeps the rest if not better.

    return groups


def _build_tech_stack(groups):
    """Return the tech_stack dict with ALL schema categories present (even if empty)."""
    out = {}
    for cat in TECH_STACK_CATEGORIES:
        bucket = groups.get(cat, {})
        out[cat] = list(bucket.values())
    return out


def _build_search_vendors(search):
    """Build search_vendors list and algolia_detected flag from the search block.

    Returns (vendors_list, algolia_detected_bool).
    If search_detected is False/missing, returns ([], False).
    """
    if not search or not search.get("search_detected"):
        return [], False

    search_requests = search.get("search_requests") or []
    all_platforms = search.get("all_platforms_found") or []
    vendors = []
    algolia_detected = False

    if all_platforms:
        for plat in all_platforms:
            # detect-search emits `id` on all_platforms_found entries (not `platform_id`).
            pid = plat.get("platform_id") or plat.get("id") or ""
            name = plat.get("search_platform") or plat.get("name") or pid
            conf = plat.get("confidence") or "confirmed"
            details = plat.get("platform_details") or plat.get("details") or {}
            # Platform may carry its own requests; fall back to search-block level.
            plat_requests = plat.get("search_requests") or search_requests
            endpoint = _first_endpoint(plat_requests)
            if pid == "algolia":
                algolia_detected = True
            vendors.append({
                "vendor": name,
                "platform_id": pid,
                "confidence": conf,
                "details": details,
                "network_endpoint": endpoint,
            })
    else:
        # Fallback: single-platform from the primary search block fields.
        pid = search.get("platform_id") or ""
        name = search.get("search_platform") or pid
        conf = "confirmed"  # we're in the search_detected=True branch
        details = search.get("platform_details") or {}
        endpoint = _first_endpoint(search_requests)
        if pid == "algolia":
            algolia_detected = True
        vendors.append({
            "vendor": name,
            "platform_id": pid,
            "confidence": conf,
            "details": details,
            "network_endpoint": endpoint,
        })

    return vendors, algolia_detected


def _domain_from_url(url):
    """Extract bare domain (no www., no port) from a URL string."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        host = parsed.netloc or parsed.path or ""
        host = host.split(":")[0]
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return url


def map_tech(data, domain_override=None):
    """Translate a detect-search --full-tech payload into 02-tech-stack.json.

    Parameters
    ----------
    data : dict
        Parsed JSON from `detect-search.js --full-tech`.
    domain_override : str or None
        If provided, uses this as the `domain` field instead of parsing from url.

    Returns
    -------
    dict
        The 02-tech-stack.json output object.
    """
    if not isinstance(data, dict):
        raise ValueError("detect-search --full-tech payload must be a JSON object")

    url = data.get("url") or ""
    domain = domain_override or _domain_from_url(url) or url
    pages_visited = data.get("pages_visited") or []
    detected = data.get("detected") or []
    search = data.get("search") or {}
    not_detectable_note = data.get("not_detectable_note") or ""
    bot_blocked = bool(data.get("bot_blocked"))

    groups = _group_by_category(detected)
    tech_stack = _build_tech_stack(groups)
    search_vendors, algolia_detected = _build_search_vendors(search)

    return {
        "domain": domain,
        "detection_method": DETECTION_METHOD,
        "pages_visited": pages_visited,
        "tech_stack": tech_stack,
        "search_vendors": search_vendors,
        "algolia_detected": algolia_detected,
        "not_detectable_note": not_detectable_note,
        "bot_blocked": bot_blocked,
        "limitations": LIMITATIONS,
    }


def _load(path):
    """Load JSON from a file path or '-' for stdin.

    If the payload is a list (bulk mode), returns the first element.
    """
    if path == "-":
        raw = sys.stdin.read()
    else:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    data = json.loads(raw)
    if isinstance(data, list):
        if not data:
            raise ValueError("detect-search returned an empty list")
        return data[0]
    return data


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Map detect-search --full-tech output to 02-tech-stack.json audit schema."
    )
    p.add_argument(
        "--detect", required=True,
        help="path to detect-search --full-tech JSON, or '-' for stdin",
    )
    p.add_argument(
        "--domain", default=None,
        help="override domain name (otherwise parsed from url field)",
    )
    args = p.parse_args(argv)

    try:
        data = _load(args.detect)
        result = map_tech(data, domain_override=args.domain)
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
