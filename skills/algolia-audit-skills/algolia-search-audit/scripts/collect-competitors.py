#!/usr/bin/env python3
"""
collect-competitors.py — Collect competitor data via SimilarWeb browser session.
Replaces dead SimilarWeb API calls with collect-similarweb-browser.js --mode competitors-discovery.
Writes 04-competitors.md and 04-competitors.json.

Usage: python3 collect-competitors.py <domain> <output-dir>

Sources:
  1. SimilarWeb Competitors tab (browser) — similar-sites domain list
  2. WebSearch fallback — if SW returns 0 results (raw_fallback parsing)

Search vendor detection happens in the SKILL enrichment step (Step 2),
not in this script. BuiltWith MCP per competitor is called by the skill.
"""

import sys, os, json, subprocess
from datetime import date

TODAY    = date.today().isoformat()
SCRIPTS  = os.path.dirname(os.path.abspath(__file__))
SW_BROWSER = os.path.join(SCRIPTS, 'collect-similarweb-browser.js')

def run_sw_discovery(domain):
    """Call SW browser competitors-discovery mode. Returns list of competitor dicts."""
    try:
        result = subprocess.run(
            ['node', SW_BROWSER, '--mode', 'competitors-discovery', '--domain', domain],
            capture_output=True, text=True, timeout=120, cwd=SCRIPTS
        )
        if result.returncode == 1:
            return None, 'SW session expired — run: node collect-similarweb-browser.js --setup'
        if result.returncode != 0:
            return None, f'SW browser exit {result.returncode}: {result.stderr[:300]}'

        data = json.loads(result.stdout)
        discovery = data.get('competitors_discovery', {})
        competitors = discovery.get('competitors', [])
        raw_fallback = discovery.get('raw_fallback')
        screenshot = discovery.get('screenshot')
        return {
            'competitors': competitors,
            'raw_fallback': raw_fallback,
            'screenshot': screenshot,
            'source_url': discovery.get('source_url'),
        }, None
    except subprocess.TimeoutExpired:
        return None, 'SW browser timed out after 120s'
    except json.JSONDecodeError as e:
        return None, f'SW browser output not valid JSON: {e}'
    except Exception as e:
        return None, str(e)

def format_visits(v):
    if not v: return 'N/A'
    try:
        v = float(str(v).replace(',', '').replace('K', 'e3').replace('M', 'e6').replace('B', 'e9'))
        if v >= 1e9: return f"{v/1e9:.1f}B"
        if v >= 1e6: return f"{v/1e6:.1f}M"
        if v >= 1e3: return f"{v/1e3:.0f}K"
        return str(int(v))
    except:
        return str(v)

def main():
    if len(sys.argv) < 3:
        print('Usage: collect-competitors.py <domain> <output-dir>', file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1].lower().replace('https://','').replace('http://','').replace('www.','').split('/')[0]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    print(f'Collecting competitors for {domain}...', file=sys.stderr)

    # Step 1: Try SW browser competitor discovery (best-effort)
    # SW Competitors tab has CloudFront bot protection — this may return 0.
    # WebSearch in skill enrichment Step 2 is the reliable primary path.
    sw_result, sw_err = run_sw_discovery(domain)

    comp_list = []
    source_note = ''
    raw_fallback = None

    if sw_err:
        print(f'  ⚠ SW browser error: {sw_err}', file=sys.stderr)
    elif sw_result:
        error_flag = sw_result.get('error')
        if error_flag and 'CloudFront' in str(error_flag):
            print(f'  ⚠ SW Competitors tab blocked by CloudFront — using WebSearch fallback', file=sys.stderr)
        else:
            raw = sw_result.get('competitors', [])
            raw_fallback = sw_result.get('raw_fallback')
            for c in raw:
                d = c.get('domain', '').lower()
                if not d or d == domain or 'similarweb' in d:
                    continue
                comp_list.append({
                    'domain': d,
                    'name': c.get('name', d),
                    'visits': format_visits(c.get('visits')),
                    'search_vendor': 'TBD',
                    'from_sw_browser': True,
                })
            source = sw_result.get('source_url', f'https://www.similarweb.com/website/{domain}/competitors/')
            source_note = f'SimilarWeb Competitors tab (browser session) — {source}'
            print(f'  Found {len(comp_list)} competitors via SW browser', file=sys.stderr)

    # Step 2: WebSearch is the reliable fallback (and often primary) source.
    # The skill enrichment step (Step 2 in SKILL.md) runs WebSearch + BuiltWith
    # to identify and verify competitors when SW returns 0.
    if not comp_list:
        source_note = 'WebSearch enrichment required — SW browser returned 0 competitors (CloudFront block)'
        print('  → Competitor list empty — skill enrichment Step 2 (WebSearch) is required', file=sys.stderr)

    # Step 3: Build markdown output
    table_rows = []
    for i, c in enumerate(comp_list, 1):
        table_rows.append(
            f"| {i} | **{c['domain']}** | {c.get('name', c['domain'])} | "
            f"{c.get('visits','N/A')} | {c.get('search_vendor','TBD')} |"
        )

    if not table_rows:
        table_rows = [
            "| — | *No competitors detected — run skill enrichment with WebSearch fallback* | — | — | — |"
        ]

    md = f"""# Competitor Analysis — {domain}
**Generated:** {TODAY}
**Source:** {source_note or 'N/A'}
**Note:** Search vendor = TBD until Step 2 BuiltWith + network inspection confirms active vendor.

---

## Top Competitors

| Rank | Domain | Name | Monthly Visits | Search Vendor |
|------|--------|------|---------------|---------------|
{chr(10).join(table_rows)}

[FACT — SimilarWeb Competitors tab via browser, {TODAY}]
Source: https://www.similarweb.com/website/{domain}/competitors/

---

## Search Vendor Status
All search vendors marked **TBD** until Step 2 BuiltWith MCP detection + Phase 2 network inspection.
Update this table after running skill enrichment (Step 2).

---

## Step 6 Append Zone
*Competitor search analysis and competitive gap analysis will be appended here after Phase 2.*
"""

    md_path = os.path.join(output_dir, '04-competitors.md')
    with open(md_path, 'w') as f:
        f.write(md)

    json_record = {
        'domain': domain,
        'generated_at': TODAY,
        'source': 'SimilarWeb Competitors tab — browser session',
        'competitors': comp_list,
        'competitors_count': len(comp_list),
        'raw_fallback': raw_fallback,
        'sw_error': sw_err,
        'output_file': md_path,
        'skill_enrichment_required': [
            'search_vendor per competitor (BuiltWith MCP)',
            'golden_angle detection',
            'algolia_customers in vertical (WebSearch)',
        ],
        'meta': {
            'skill_enrichment_completed': False,
            'competitive_scenario': None,
        }
    }

    json_path = os.path.join(output_dir, '04-competitors.json')
    with open(json_path, 'w') as f:
        json.dump(json_record, f, indent=2)

    print(json.dumps({
        'status': 'success' if comp_list else ('partial' if raw_fallback else 'empty'),
        'domain': domain,
        'competitors_found': len(comp_list),
        'competitors': [c['domain'] for c in comp_list],
        'sw_error': sw_err,
        'raw_fallback_available': raw_fallback is not None,
        'output_md': md_path,
        'output_json': json_path,
    }, indent=2))

if __name__ == '__main__':
    main()
