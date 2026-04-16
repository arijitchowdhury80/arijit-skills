#!/usr/bin/env python3
"""
collect-traffic.py — Collect complete traffic data via SimilarWeb API
Calls ALL 11 required endpoints. No skipping.

Endpoints called:
1. traffic-and-engagement (total)
2. traffic-and-engagement (desktop)
3. traffic-and-engagement (mobile_web)
4. traffic-sources
5. geography
6. demographics
7. keywords (top organic)
8. audience-interests
9. website-rank
10. referrals
11. leading-folders (popular pages proxy)

Usage: python3 collect-traffic.py <domain> <output-dir>
Env: SIMILARWEB_API_KEY
"""

import sys, os, json, requests
from datetime import date, timedelta

API_KEY = os.environ.get('SIMILARWEB_API_KEY', '***REMOVED***')
TODAY = date.today().isoformat()

# Date range: last 3 months
END_DATE = date.today().replace(day=1) - timedelta(days=1)
START_DATE = END_DATE.replace(month=max(1, END_DATE.month - 2))
START_STR = START_DATE.strftime('%Y-%m')
END_STR = END_DATE.strftime('%Y-%m')

def api_get(path, params=None):
    """Call SimilarWeb API with error handling."""
    params = params or {}
    params['api_key'] = API_KEY
    url = f"https://api.similarweb.com/v1/{path}"
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 403:
            return {'_error': f'403 Forbidden — endpoint not available on this API plan: {path}'}
        if r.status_code == 404:
            return {'_error': f'404 Not Found — domain may not be indexed: {path}'}
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {'_error': str(e)}

def pct(v, dec=1):
    try: return f"{float(v)*100:.{dec}f}%"
    except: return str(v)

def fmt_visits(v):
    try:
        v = float(v)
        if v >= 1e9: return f"{v/1e9:.1f}B"
        if v >= 1e6: return f"{v/1e6:.1f}M"
        return f"{v:,.0f}"
    except: return str(v)

def fmt_duration(secs):
    try:
        s = int(float(secs))
        return f"{s//60}m {s%60:02d}s"
    except: return str(secs)

def collect_all(domain):
    """Call all 14 endpoints. Returns dict of results."""
    base_params = {'start_date': START_STR, 'end_date': END_STR, 'country': 'world', 'main_domain_only': 'false', 'granularity': 'monthly'}

    results = {}

    # 1a. Total visits
    results['total'] = api_get(f"website/{domain}/traffic-and-engagement/visits",
        {**base_params, 'web_source': 'total'})

    # 1b. Bounce rate (separate endpoint — same conceptual group as total engagement)
    results['bounce_rate'] = api_get(f"website/{domain}/traffic-and-engagement/bounce-rate",
        {**base_params, 'web_source': 'total'})

    # 1c. Pages per visit
    results['pages_per_visit'] = api_get(f"website/{domain}/traffic-and-engagement/pages-per-visit",
        {**base_params, 'web_source': 'total'})

    # 1d. Average visit duration
    results['avg_duration'] = api_get(f"website/{domain}/traffic-and-engagement/average-visit-duration",
        {**base_params, 'web_source': 'total'})

    # 2. Desktop
    results['desktop'] = api_get(f"website/{domain}/traffic-and-engagement/visits",
        {**base_params, 'web_source': 'desktop'})

    # 3. Mobile web
    results['mobile'] = api_get(f"website/{domain}/traffic-and-engagement/visits",
        {**base_params, 'web_source': 'mobile_web'})

    # 4. Traffic sources
    results['sources'] = api_get(f"website/{domain}/traffic-sources/overview",
        {'api_key': API_KEY, 'start_date': START_STR, 'end_date': END_STR, 'country': 'world', 'main_domain_only': 'false'})

    # 5. Geography
    results['geo'] = api_get(f"website/{domain}/geo/traffic-by-country",
        {'api_key': API_KEY, 'start_date': START_STR, 'end_date': END_STR})

    # 6. Demographics
    results['demo'] = api_get(f"website/{domain}/demographics/age-gender",
        {'api_key': API_KEY, 'start_date': START_STR, 'end_date': END_STR, 'country': 'world'})

    # 7. Keywords
    results['keywords'] = api_get(f"website/{domain}/organic-search/keywords",
        {'api_key': API_KEY, 'start_date': START_STR, 'end_date': END_STR, 'country': 'world', 'main_domain_only': 'false', 'limit': 10})

    # 8. Audience interests
    results['interests'] = api_get(f"website/{domain}/audience-interests/also-visited",
        {'api_key': API_KEY, 'start_date': START_STR, 'end_date': END_STR, 'country': 'world'})

    # 9. Rank
    results['rank'] = api_get(f"website/{domain}/rank",
        {'api_key': API_KEY})

    # 10. Referrals
    results['referrals'] = api_get(f"website/{domain}/traffic-sources/referrals",
        {'api_key': API_KEY, 'start_date': START_STR, 'end_date': END_STR, 'country': 'world', 'limit': 10})

    # 11. Leading folders (popular pages proxy)
    results['folders'] = api_get(f"website/{domain}/content/pages/leading-folders",
        {'api_key': API_KEY, 'start_date': START_STR, 'end_date': END_STR, 'country': 'world'})

    return results

def extract_engagement(data, source_name):
    """Extract key metrics from engagement endpoint."""
    if '_error' in data:
        return None, data['_error']

    # Try different data structures
    visits_data = (
        data.get('visits') or
        data.get('data', {}).get('visits') or
        data.get('Visits') or
        []
    )

    if not visits_data:
        return None, "No visits data in response"

    # Get most recent month
    latest = visits_data[-1] if visits_data else {}
    return {
        'visits': fmt_visits(latest.get('visits', latest.get('value', 0))),
        'bounce_rate': pct(latest.get('bounce_rate', latest.get('bounceRate', 0))),
        'pages_per_visit': f"{float(latest.get('pages_per_visit', latest.get('pagesPerVisit', 0))):.2f}",
        'avg_duration': fmt_duration(latest.get('average_visit_duration', latest.get('avgVisitDuration', 0))),
        'month': latest.get('date', latest.get('year_month', 'N/A'))
    }, None

def write_output(domain, results, output_dir):
    errors = []
    sections = []
    sw_url = f"https://www.similarweb.com/website/{domain}/"

    # API parameters header (MANDATORY for fact-check reproducibility)
    sections.append(f"""# Traffic Data — {domain}
*Generated: {TODAY} via collect-traffic.py*

## API Parameters (fact-check reproducibility)
- Primary Source: SimilarWeb API
- web_source: total (desktop+mobile combined)
- country: world (ww)
- Period: {START_STR} to {END_STR}
- Endpoints called: 14 of 14 (11 core + 3 engagement sub-metrics)
- Script: collect-traffic.py [FACT — collect-traffic.py, {TODAY}]
- Source: {sw_url} [FACT — SimilarWeb API, {sw_url}, {TODAY}]
""")

    # Total engagement — visits from visits endpoint, other metrics from dedicated endpoints
    eng, err = extract_engagement(results['total'], 'total')

    # Extract bounce rate from dedicated endpoint
    def extract_latest(data, *field_keys):
        """Try multiple field names in a list-of-dicts or nested structure."""
        if '_error' in data:
            return 'N/A'
        for fk in field_keys:
            arr = data.get(fk)
            if isinstance(arr, list) and arr:
                val = arr[-1].get(fk, arr[-1].get('value'))
                if val is not None:
                    return val
            elif isinstance(arr, dict):
                # Nested {date, field} structure
                val = arr.get(fk)
                if val is not None:
                    return val
        return 'N/A'

    bounce_raw = extract_latest(results.get('bounce_rate', {}), 'bounce_rate')
    pages_raw = extract_latest(results.get('pages_per_visit', {}), 'pages_per_visit')
    duration_raw = extract_latest(results.get('avg_duration', {}), 'average_visit_duration')

    bounce_str = pct(bounce_raw) if bounce_raw != 'N/A' else 'N/A'
    pages_str = f"{float(pages_raw):.2f}" if pages_raw != 'N/A' else 'N/A'
    duration_str = fmt_duration(duration_raw) if duration_raw != 'N/A' else 'N/A'

    if eng:
        sections.append(f"""## Monthly Traffic (Total — Desktop + Mobile)
| Metric | Value |
|--------|-------|
| Monthly Visits | {eng['visits']} |
| Bounce Rate | {bounce_str} |
| Pages per Visit | {pages_str} |
| Avg Visit Duration | {duration_str} |
| Period | {eng['month']} |
[FACT — SimilarWeb API, {sw_url}, {TODAY}]
""")
    else:
        errors.append(f"Total engagement: {err}")
        sections.append(f"## Monthly Traffic\n*Unavailable: {err}*\n")

    # Device split
    desk_eng, _ = extract_engagement(results['desktop'], 'desktop')
    mob_eng, _ = extract_engagement(results['mobile'], 'mobile_web')
    if desk_eng and mob_eng:
        try:
            d_visits = float(results['desktop'].get('visits', [{}])[-1].get('visits', 0))
            m_visits = float(results['mobile'].get('visits', [{}])[-1].get('visits', 0))
            total_v = d_visits + m_visits
            mobile_pct = f"{m_visits/total_v*100:.1f}%" if total_v > 0 else "N/A"
            desktop_pct = f"{d_visits/total_v*100:.1f}%" if total_v > 0 else "N/A"
            sections.append(f"""## Device Split
- Mobile: {mobile_pct}
- Desktop: {desktop_pct}
Formula: mobile_visits / (mobile_visits + desktop_visits) × 100
[FACT — SimilarWeb API, {sw_url}, {TODAY}]
""")
        except:
            sections.append("## Device Split\n*Could not calculate device split*\n")

    # Traffic sources — aggregate by channel type, top rows only
    src = results['sources']
    if '_error' not in src:
        src_data = src.get('overview', src.get('data', {}).get('overview', []))
        if src_data:
            # Aggregate shares by channel type to collapse granular rows
            channel_agg = {}
            for ch in src_data:
                name = ch.get('source_type', ch.get('channel', ch.get('name', 'Unknown')))
                try:
                    share_val = float(ch.get('share', ch.get('visits_share', 0)))
                except:
                    share_val = 0.0
                channel_agg[name] = channel_agg.get(name, 0.0) + share_val
            # Sort descending, keep top 8 named channels
            sorted_channels = sorted(channel_agg.items(), key=lambda x: x[1], reverse=True)[:8]
            sections.append("## Traffic Sources\n| Channel | Share |\n|---------|-------|\n")
            for name, share_val in sorted_channels:
                sections[-1] += f"| {name} | {share_val*100:.1f}% |\n"
            sections[-1] += f"[FACT — SimilarWeb API, {sw_url}, {TODAY}]\n"
    else:
        errors.append(f"Sources: {src['_error']}")

    # Geography
    geo = results['geo']
    if '_error' not in geo:
        countries = geo.get('records', geo.get('data', {}).get('records', []))
        if countries:
            sections.append("## Top Countries\n| Country | Traffic Share |\n|---------|---------------|\n")
            for c in countries[:5]:
                country = c.get('country_name', c.get('country', 'Unknown'))
                share = pct(c.get('share', c.get('traffic_share', 0)))
                sections[-1] += f"| {country} | {share} |\n"
            sections[-1] += f"[FACT — SimilarWeb API, {sw_url}, {TODAY}]\n"
    else:
        errors.append(f"Geography: {geo['_error']}")

    # Demographics
    demo = results['demo']
    if '_error' not in demo:
        age_data = demo.get('age', demo.get('data', {}).get('age', []))
        gender = demo.get('gender', demo.get('data', {}).get('gender', {}))
        if age_data:
            sections.append("## Demographics\n### Age Distribution\n| Age Group | Share |\n|-----------|-------|\n")
            for a in age_data:
                group = a.get('age_group', a.get('group', 'Unknown'))
                share = pct(a.get('share', a.get('percentage', 0)))
                sections[-1] += f"| {group} | {share} |\n"
            if gender:
                male = pct(gender.get('male', gender.get('Male', 0)))
                female = pct(gender.get('female', gender.get('Female', 0)))
                sections[-1] += f"\n### Gender\n- Male: {male} | Female: {female}\n"
            sections[-1] += f"[FACT — SimilarWeb API, {sw_url}, {TODAY}]\n"
    else:
        errors.append(f"Demographics: {demo['_error']}")

    # Keywords
    kw = results['keywords']
    if '_error' not in kw:
        kw_data = kw.get('keywords', kw.get('data', {}).get('keywords', kw.get('response', {}).get('keywords', [])))
        if kw_data:
            sections.append("## Top Organic Keywords\n| Keyword | Volume | Share |\n|---------|--------|-------|\n")
            for k in kw_data[:10]:
                term = k.get('name', k.get('keyword', k.get('query', 'Unknown')))
                vol = k.get('search_volume', k.get('volume', k.get('estimated_value', 'N/A')))
                share = pct(k.get('share', k.get('organic_share', 0)))
                sections[-1] += f"| {term} | {vol} | {share} |\n"
            sections[-1] += f"[FACT — SimilarWeb API, {sw_url}, {TODAY}]\n"
    else:
        errors.append(f"Keywords: {kw['_error']}")

    # Audience interests
    interests = results['interests']
    if '_error' not in interests:
        int_data = interests.get('sites', interests.get('data', {}).get('sites', interests.get('also_visited', [])))
        if int_data:
            sections.append("## Audience Interests (Also Visited)\n| Site | Affinity |\n|------|----------|\n")
            for site in int_data[:8]:
                name = site.get('domain', site.get('site', site.get('name', 'Unknown')))
                affinity = site.get('affinity', site.get('score', site.get('overlap', 'N/A')))
                try:
                    affinity = f"{float(affinity):.3f}"
                except:
                    pass
                sections[-1] += f"| {name} | {affinity} |\n"
            sections[-1] += f"[FACT — SimilarWeb API, {sw_url}, {TODAY}]\n"
    else:
        errors.append(f"Audience interests: {interests['_error']}")

    # Rank
    rank = results['rank']
    if '_error' not in rank:
        global_rank = rank.get('global_rank', rank.get('data', {}).get('global_rank', 'N/A'))
        sections.append(f"## Site Rank\n- Global Rank: #{global_rank}\n[FACT — SimilarWeb API, {sw_url}, {TODAY}]\n")
    else:
        errors.append(f"Rank: {rank['_error']}")

    # Referrals
    ref = results['referrals']
    if '_error' not in ref:
        ref_data = ref.get('sites', ref.get('data', {}).get('sites', ref.get('referrals', [])))
        if ref_data:
            sections.append("## Top Referral Sources\n| Referrer | Share |\n|----------|-------|\n")
            for r in ref_data[:10]:
                site = r.get('site', r.get('domain', r.get('name', 'Unknown')))
                share = pct(r.get('share', r.get('referral_share', r.get('traffic_share', 0))))
                sections[-1] += f"| {site} | {share} |\n"
            sections[-1] += f"[FACT — SimilarWeb API, {sw_url}, {TODAY}]\n"
    else:
        errors.append(f"Referrals: {ref['_error']}")

    # Leading folders
    folders = results['folders']
    if '_error' not in folders:
        folder_data = folders.get('folders', folders.get('data', {}).get('folders', folders.get('pages', [])))
        if folder_data:
            sections.append("## Leading Folders (Popular Page Categories)\n| Folder | Traffic Share |\n|--------|---------------|\n")
            for f in folder_data[:10]:
                path = f.get('folder', f.get('path', f.get('page', 'Unknown')))
                share = pct(f.get('share', f.get('traffic_share', f.get('visits_share', 0))))
                sections[-1] += f"| {path} | {share} |\n"
            sections[-1] += f"[FACT — SimilarWeb API, {sw_url}, {TODAY}]\n"
    else:
        errors.append(f"Leading folders: {folders['_error']}")

    # Errors summary
    if errors:
        sections.append(f"## API Errors / Fallbacks\n" + "\n".join(f"- {e}" for e in errors) + "\n")

    out_path = os.path.join(output_dir, '03-traffic-data.md')
    with open(out_path, 'w') as f:
        f.write("\n".join(sections))

    return out_path, errors

def main():
    if len(sys.argv) < 3:
        print("Usage: collect-traffic.py <domain> <output-dir>", file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1].lower().replace('https://','').replace('http://','').replace('www.','').split('/')[0]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    print(f"Collecting traffic data for {domain} (11 endpoints)...", file=sys.stderr)
    results = collect_all(domain)

    endpoints_ok = sum(1 for v in results.values() if '_error' not in v)
    total_endpoints = len(results)
    print(f"Endpoints successful: {endpoints_ok}/{total_endpoints}", file=sys.stderr)

    out_path, errors = write_output(domain, results, output_dir)

    print(json.dumps({
        'status': 'success' if not errors else 'partial',
        'domain': domain,
        'endpoints_called': total_endpoints,
        'endpoints_ok': endpoints_ok,
        'output_file': out_path,
        'size_bytes': os.path.getsize(out_path),
        'errors': errors
    }, indent=2))

if __name__ == '__main__':
    main()
