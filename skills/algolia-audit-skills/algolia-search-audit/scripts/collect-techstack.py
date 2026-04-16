#!/usr/bin/env python3
"""
collect-techstack.py — Collect technology stack data
Calls BuiltWith API + SimilarWeb technologies endpoint.
Pipes BuiltWith response through parse-builtwith.js to filter 190KB → <15KB.

Usage: python3 collect-techstack.py <domain> <output-dir>
Env: BUILTWITH_API_KEY, SIMILARWEB_API_KEY
"""

import sys, os, json, requests, subprocess
from datetime import date

BW_KEY = os.environ.get('BUILTWITH_API_KEY', '***REMOVED***')
SW_KEY = os.environ.get('SIMILARWEB_API_KEY', '***REMOVED***')
TODAY = date.today().isoformat()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARSE_SCRIPT = os.path.join(SCRIPT_DIR, 'parse-builtwith.js')

def call_builtwith(domain):
    """Call BuiltWith API for full domain tech stack."""
    url = f"https://api.builtwith.com/v21/api.json"
    params = {'KEY': BW_KEY, 'LOOKUP': domain, 'HIDETEXT': 1, 'NOMETA': 1, 'NOLIVE': 0}
    try:
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        raw = r.json()
        raw_size = len(r.content)
        return raw, raw_size, None
    except Exception as e:
        return None, 0, str(e)

def filter_builtwith(raw_data):
    """Pipe BuiltWith response through parse-builtwith.js filter."""
    if not os.path.exists(PARSE_SCRIPT):
        return None, f"parse-builtwith.js not found at {PARSE_SCRIPT}"

    try:
        raw_json = json.dumps(raw_data if isinstance(raw_data, list) else [{'text': json.dumps(raw_data)}])
        result = subprocess.run(
            ['node', PARSE_SCRIPT],
            input=raw_json,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return None, f"parse-builtwith.js error: {result.stderr}"
        return json.loads(result.stdout), None
    except Exception as e:
        return None, str(e)

def call_similarweb_tech(domain):
    """Call SimilarWeb technology endpoint as cross-check."""
    from datetime import timedelta
    end = date.today().replace(day=1) - timedelta(days=1)
    start = end.replace(month=max(1, end.month - 2))

    url = f"https://api.similarweb.com/v1/website/{domain}/content/technologies"
    params = {
        'api_key': SW_KEY,
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

def find_search_vendor(filtered):
    """Check if any known search vendor detected."""
    if not filtered:
        return None, 'unknown'

    vendors = {
        'algolia': 'EXISTING CUSTOMER — ABORT AUDIT',
        'lucidworks': 'LucidWorks Fusion — DISPLACEMENT OPPORTUNITY',
        'coveo': 'Coveo — COMPETITOR',
        'bloomreach': 'BloomReach — COMPETITOR',
        'constructor': 'Constructor.io — COMPETITOR',
        'searchspring': 'SearchSpring — COMPETITOR',
        'klevu': 'Klevu — COMPETITOR',
        'elasticsearch': 'Elasticsearch — DIY (build opportunity)'
    }

    detected = []
    for tech in filtered.get('search_vendors', []):
        name_lower = tech.get('name', '').lower()
        for vendor, desc in vendors.items():
            if vendor in name_lower:
                detected.append((tech['name'], desc))

    return detected or None, 'not_detected'

def main():
    if len(sys.argv) < 3:
        print("Usage: collect-techstack.py <domain> <output-dir>", file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1].lower().replace('https://','').replace('http://','').replace('www.','').split('/')[0]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    print(f"Collecting tech stack for {domain}...", file=sys.stderr)

    # 1. BuiltWith
    raw_bw, raw_size, bw_err = call_builtwith(domain)
    filtered = None
    filter_err = None

    if raw_bw:
        print(f"BuiltWith raw response: {raw_size:,} bytes — filtering...", file=sys.stderr)
        filtered, filter_err = filter_builtwith(raw_bw)
        if filtered:
            print(f"Filtered: {len(json.dumps(filtered))} bytes ({len(filtered.get('all_relevant',[]))} relevant techs)", file=sys.stderr)

    # 2. SimilarWeb technologies (cross-check)
    sw_tech, sw_err = call_similarweb_tech(domain)

    # 3. Determine search vendor
    search_vendors, _ = find_search_vendor(filtered)

    # Build output sections
    sections = [f"""# Tech Stack — {domain}
*Generated: {TODAY} via collect-techstack.py*

## API Parameters
- BuiltWith API: domain-lookup (live technologies)
- SimilarWeb Technologies API: cross-check
- Raw BuiltWith size: {raw_size:,} bytes → filtered via parse-builtwith.js
- Date: {TODAY}

## Search Vendor Status
"""]

    if search_vendors:
        for name, desc in search_vendors:
            if 'EXISTING CUSTOMER' in desc:
                sections[0] += f"ALGOLIA DETECTED — {name}: {desc}\n"
                sections[0] += "ABORT AUDIT — This is an existing Algolia customer.\n"
            else:
                sections[0] += f"**{name}** — {desc} | Status: TAG DETECTED (unverified — confirm via Phase 2 network inspection)\n"
    else:
        sections[0] += "No known search vendor detected in current stack.\n"

    sections[0] += f"[FACT — BuiltWith API + SimilarWeb technologies, {TODAY}]\n\nAll vendors marked TAG DETECTED until Phase 2 Step 2a½ confirms active API calls.\n"

    if filtered:
        # Ecommerce platform
        ecomm = filtered.get('ecommerce_platform', [])
        if ecomm:
            sections.append(f"## Ecommerce Platform\n" +
                "\n".join(f"- **{t['name']}** ({t.get('tag','')}) — {t.get('link','')}" for t in ecomm) +
                f"\n[FACT — BuiltWith API, {TODAY}]\n")

        # CDN/WAF
        cdn = filtered.get('cdn_waf', [])
        if cdn:
            sections.append(f"## CDN / WAF\n" +
                "\n".join(f"- **{t['name']}** ({t.get('tag','')})" for t in cdn) +
                f"\n[FACT — BuiltWith API, {TODAY}]\n")

        # Analytics
        analytics = filtered.get('analytics', [])
        if analytics:
            sections.append(f"## Analytics\n" +
                "\n".join(f"- {t['name']}" for t in analytics) +
                f"\n[FACT — BuiltWith API, {TODAY}]\n")

        # Personalization
        pers = filtered.get('personalization', [])
        sections.append(f"## Personalization\n" +
            ("\n".join(f"- {t['name']}" for t in pers) if pers else "- None detected — GAP for Algolia AI Personalization") +
            f"\n[FACT — BuiltWith API, {TODAY}]\n")

        # Reviews
        reviews = filtered.get('reviews', [])
        if reviews:
            sections.append(f"## Reviews\n" +
                "\n".join(f"- {t['name']}" for t in reviews) +
                f"\n[FACT — BuiltWith API, {TODAY}]\n")

        # Removed technologies
        removed = filtered.get('removed_technologies', [])
        if removed:
            sections.append(f"## Removed Technologies (Displacement Signals)\n" +
                "\n".join(f"- ~~{t['name']}~~ (removed)" for t in removed) +
                f"\n[FACT — BuiltWith API, {TODAY}]\n")

        sections.append(f"## Technology Summary\nTotal relevant technologies detected: {len(filtered.get('all_relevant',[]))}\nAlgolia detected: {'YES — ABORT AUDIT' if filtered.get('algolia_detected') else 'No'}\nCompetitor detected: {'YES' if filtered.get('competitor_detected') else 'No'}\n[FACT — BuiltWith API, {TODAY}]\nSource: https://builtwith.com/{domain}\n")
    else:
        sections.append(f"## BuiltWith Data\n*{'Unavailable: ' + (bw_err or filter_err or 'unknown error')}*\nFallback: Use SimilarWeb technologies as primary source.\n")

    # SimilarWeb cross-check
    if sw_tech and not sw_err:
        sw_techs = sw_tech.get('technologies', sw_tech.get('data', {}).get('technologies', []))
        if sw_techs:
            sections.append(f"## SimilarWeb Technology Cross-Check (top 10)\n" +
                "\n".join(f"- {t.get('name', t.get('technology', 'Unknown'))} ({t.get('category', '')})" for t in sw_techs[:10]) +
                f"\n[FACT — SimilarWeb API technologies, {TODAY}]\n")

    if bw_err: sections.append(f"## Errors\n- BuiltWith API: {bw_err}\n")
    if sw_err: sections.append(f"- SimilarWeb Technologies: {sw_err}\n")

    out_path = os.path.join(output_dir, '02-tech-stack.md')
    with open(out_path, 'w') as f:
        f.write("\n".join(sections))

    algolia_detected = filtered.get('algolia_detected', False) if filtered else False

    result = {
        'status': 'success',
        'domain': domain,
        'output_file': out_path,
        'size_bytes': os.path.getsize(out_path),
        'builtwith_raw_size': raw_size,
        'filtered_techs': len(filtered.get('all_relevant', [])) if filtered else 0,
        'algolia_detected': algolia_detected,
        'competitor_detected': filtered.get('competitor_detected', False) if filtered else False,
        'search_vendors': [s[0] for s in search_vendors] if search_vendors else []
    }
    if algolia_detected:
        result['action'] = 'ABORT_AUDIT — existing Algolia customer detected'

    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
