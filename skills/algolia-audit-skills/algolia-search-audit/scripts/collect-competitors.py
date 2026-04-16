#!/usr/bin/env python3
"""
collect-competitors.py — Collect competitor data via SimilarWeb API
Calls similar-sites and keywords-competitors endpoints.
Writes 04-competitors.md with top 5-8 competitors.

Usage: python3 collect-competitors.py <domain> <output-dir>
Env: SIMILARWEB_API_KEY — SimilarWeb API key
"""

import sys, os, json, requests
from datetime import date, timedelta

API_KEY = os.environ.get('SIMILARWEB_API_KEY', '***REMOVED***')
BASE_URL = "https://api.similarweb.com/v1"
TODAY = date.today().isoformat()
END_DATE = date.today().replace(day=1) - timedelta(days=1)
START_DATE = END_DATE.replace(month=max(1, END_DATE.month - 2))
START_STR = START_DATE.strftime('%Y-%m')
END_STR = END_DATE.strftime('%Y-%m')

def call_api(endpoint, params=None):
    params = params or {}
    params['api_key'] = API_KEY
    url = f"{BASE_URL}/{endpoint}"
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        return {'error': str(e), 'status_code': r.status_code}
    except Exception as e:
        return {'error': str(e)}

def get_similar_sites(domain):
    data = call_api(f"website/{domain}/similar-sites/similarsites", {
        'start_date': START_STR, 'end_date': END_STR,
        'country': 'world', 'main_domain_only': 'false', 'limit': 10
    })
    if 'error' in data:
        # Try alternate endpoint
        data = call_api(f"website/{domain}/audience-overlap/similar-sites", {
            'start_date': START_STR, 'end_date': END_STR,
            'country': 'world', 'limit': 10
        })
    return data

def get_keyword_competitors(domain):
    data = call_api(f"website/{domain}/organic-search/keyword-competitors", {
        'start_date': START_STR, 'end_date': END_STR,
        'country': 'world', 'limit': 10
    })
    return data

def format_visits(v):
    try:
        v = float(v)
        if v >= 1e9: return f"{v/1e9:.1f}B"
        if v >= 1e6: return f"{v/1e6:.1f}M"
        if v >= 1e3: return f"{v/1e3:.1f}K"
        return str(int(v))
    except: return str(v)

def main():
    if len(sys.argv) < 3:
        print("Usage: collect-competitors.py <domain> <output-dir>", file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1].lower().replace('https://','').replace('http://','').replace('www.','').split('/')[0]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    print(f"Collecting competitors for {domain}...", file=sys.stderr)

    similar = get_similar_sites(domain)
    kw_comp = get_keyword_competitors(domain)

    # Extract competitors from similar sites
    competitors = {}

    similar_list = (
        similar.get('similar_sites') or
        similar.get('SimilarSites') or
        similar.get('data', {}).get('similar_sites', []) or
        []
    )
    for site in similar_list[:8]:
        comp_domain = site.get('url', site.get('domain', site.get('site', '')))
        if comp_domain and comp_domain != domain:
            competitors[comp_domain] = {
                'domain': comp_domain,
                'affinity': site.get('score', site.get('affinity', 0)),
                'visits': format_visits(site.get('visits', site.get('global_rank', 'N/A'))),
                'from_similar_sites': True
            }

    # Add from keyword competitors
    kw_list = (
        kw_comp.get('competitors') or
        kw_comp.get('data', {}).get('competitors', []) or
        []
    )
    for site in kw_list[:5]:
        comp_domain = site.get('domain', site.get('url', ''))
        if comp_domain and comp_domain != domain and comp_domain not in competitors:
            competitors[comp_domain] = {
                'domain': comp_domain,
                'affinity': site.get('affinity', 0),
                'visits': format_visits(site.get('visits', 'N/A')),
                'from_keyword_comp': True
            }

    # Build output
    comp_list = sorted(competitors.values(), key=lambda x: x.get('affinity', 0), reverse=True)[:6]

    table_rows = []
    for i, c in enumerate(comp_list, 1):
        sources = []
        if c.get('from_similar_sites'): sources.append('Similar Sites')
        if c.get('from_keyword_comp'): sources.append('Keyword Competitors')
        table_rows.append(f"| {i} | **{c['domain']}** | {c.get('visits','N/A')} | {c.get('affinity', 'N/A')} | {', '.join(sources)} | TBD — requires Phase 2 verification |")

    if not table_rows:
        table_rows = ["| — | *No competitors detected via API — verify SimilarWeb API key* | — | — | — | — |"]

    output = f"""# Competitor Analysis — {domain}
**Generated:** {TODAY}
**Source:** SimilarWeb API (similar-sites + keyword-competitors) [FACT — collect-competitors.py, {TODAY}]
**Period:** {START_STR} to {END_STR}
**Note:** Search vendor detection requires Phase 2 network request inspection (BuiltWith alone is insufficient)

---

## Top Competitors

| Rank | Domain | Monthly Visits | Affinity Score | Detection Method | Search Provider |
|------|--------|---------------|----------------|-----------------|-----------------|
{chr(10).join(table_rows)}

[FACT — SimilarWeb API, {TODAY}]
Source: https://www.similarweb.com/website/{domain}/competitors/

---

## Search Provider Status
All search providers marked **TBD** until Phase 2 browser network inspection confirms active API calls.
BuiltWith tag detection != active search provider. Update this table after Phase 2 Step 2a.

---

## Step 6 Append Zone
*Competitor search analysis (Step 6) and competitive gap analysis (Step 6b) will be appended here after Phase 2.*
"""

    out_path = os.path.join(output_dir, '04-competitors.md')
    with open(out_path, 'w') as f:
        f.write(output)

    result = {
        'status': 'success',
        'domain': domain,
        'competitors_found': len(comp_list),
        'output_file': out_path,
        'size_bytes': os.path.getsize(out_path),
        'competitors': [c['domain'] for c in comp_list]
    }
    if 'error' in similar:
        result['similar_sites_error'] = similar['error']
    if 'error' in kw_comp:
        result['keyword_comp_error'] = kw_comp['error']

    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
