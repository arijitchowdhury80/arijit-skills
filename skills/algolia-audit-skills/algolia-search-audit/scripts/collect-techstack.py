#!/usr/bin/env python3
"""
collect-techstack.py — Collect technology stack data
Source: SimilarWeb technologies endpoint (optional — requires SIMILARWEB_API_KEY).

Search-vendor / tech-stack detection is delegated to detect-search (map-detect-search.py),
which uses network packet inspection and requires no API keys.

Usage: python3 collect-techstack.py <domain> <output-dir>
Env:   SIMILARWEB_API_KEY  (optional — if absent, SimilarWeb section is skipped gracefully)

Note: BuiltWith removed from pipeline (2026-06-29). No BUILTWITH_API_KEY is required or read.
      Search-vendor detection runs via detect-search (packet inspection, zero keys needed).
"""

import sys, os, json, requests
from datetime import date

SIMILARWEB_API_KEY = os.environ.get('SIMILARWEB_API_KEY', '')
TODAY = date.today().isoformat()


def call_similarweb_tech(domain):
    """Call SimilarWeb technology endpoint as cross-check."""
    from datetime import timedelta
    end = date.today().replace(day=1) - timedelta(days=1)
    start = end.replace(month=max(1, end.month - 2))

    url = f"https://api.similarweb.com/v1/website/{domain}/content/technologies"
    params = {
        'api_key': SIMILARWEB_API_KEY,
        'start_date': start.strftime('%Y-%m'),
        'end_date': end.strftime('%Y-%m')
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code in (403, 404):
            return None, f"HTTP {r.status_code}"
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)


def main():
    if len(sys.argv) < 3:
        print("Usage: collect-techstack.py <domain> <output-dir>", file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1].lower().replace('https://','').replace('http://','').replace('www.','').split('/')[0]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    print(f"Collecting tech stack for {domain}...", file=sys.stderr)

    sources_failed = []

    # SimilarWeb technologies (optional — skip gracefully if key absent)
    sw_tech = None
    sw_err = None
    if SIMILARWEB_API_KEY:
        sw_tech, sw_err = call_similarweb_tech(domain)
        if sw_err:
            sources_failed.append(f"similarweb_technologies: {sw_err}")
            print(f"  SimilarWeb: {sw_err}", file=sys.stderr)
        else:
            print(f"  SimilarWeb: OK", file=sys.stderr)
    else:
        sw_err = "SIMILARWEB_API_KEY not set — section skipped"
        sources_failed.append("similarweb_technologies: key not configured")
        print(f"  SimilarWeb: key not set — skipping", file=sys.stderr)

    # Build output sections
    sections = [f"""# Tech Stack — {domain}
*Generated: {TODAY} via collect-techstack.py*

## Data Sources
- SimilarWeb Technologies API: {"available" if SIMILARWEB_API_KEY else "skipped (SIMILARWEB_API_KEY not set)"}
- Search vendor / tech detection: delegated to detect-search (map-detect-search.py — network packet inspection, no API key required)
- Date: {TODAY}

## Search Vendor Status
Search vendor detection is handled by detect-search (packet-level network inspection, no keys needed).
Run `map-detect-search.py` against the prospect domain to populate this section.
TAG DETECTED results from detect-search will appear here after Phase 2 Step 2a½.
"""]

    # SimilarWeb cross-check
    if sw_tech and not sw_err:
        sw_techs = sw_tech.get('technologies', sw_tech.get('data', {}).get('technologies', []))
        if sw_techs:
            sections.append(
                f"## SimilarWeb Technology Cross-Check (top 10)\n" +
                "\n".join(
                    f"- {t.get('name', t.get('technology', 'Unknown'))} ({t.get('category', '')})"
                    for t in sw_techs[:10]
                ) +
                f"\n[FACT — SimilarWeb API technologies, {TODAY}]\n"
            )
        else:
            sections.append("## SimilarWeb Technology Cross-Check\n*No technology data returned.*\n")
    else:
        sections.append(f"## SimilarWeb Technology Cross-Check\n*Unavailable: {sw_err}*\n")

    if sources_failed:
        sections.append(
            "## Sources Failed\n" +
            "\n".join(f"- {s}" for s in sources_failed) +
            "\n"
        )

    out_path = os.path.join(output_dir, '02-tech-stack.md')
    with open(out_path, 'w') as f:
        f.write("\n".join(sections))

    result = {
        'status': 'success',
        'domain': domain,
        'output_file': out_path,
        'size_bytes': os.path.getsize(out_path),
        # search_vendors / algolia_detected / competitor_detected are populated by
        # detect-search (map-detect-search.py) — not by this script.
        'search_vendors': [],
        'algolia_detected': False,
        'competitor_detected': False,
        'sources_failed': sources_failed,
        'note': (
            'Search-vendor detection delegated to detect-search (map-detect-search.py). '
            'BuiltWith removed from pipeline.'
        ),
    }

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
