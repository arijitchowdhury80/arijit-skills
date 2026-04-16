#!/usr/bin/env python3
"""
collect-traffic.py v2.0 — Collect complete traffic data via SimilarWeb API
Updated: 2026-04-15 — uses current v4 endpoints, removes all deprecated Search 1.0 calls.

Deprecated endpoints removed:
  - /organic-search/keywords (Search 1.0 — sunset Feb 28 2025)
  - /demographics/age-gender (Demographics 1.0 — sunset Jan 1 2025)

Current endpoints called:
  Traffic & Engagement (v1):
    1. traffic-and-engagement/visits (total)
    2. traffic-and-engagement/bounce-rate
    3. traffic-and-engagement/pages-per-visit
    4. traffic-and-engagement/average-visit-duration
    5. traffic-and-engagement/visits (desktop) — for device split
    6. traffic-and-engagement/visits (mobile_web) — for device split

  Marketing Channels (v1):
    7. traffic-sources/overview-share — 7-channel breakdown

  Keywords — Search 3.0 (v4 — current):
    8. website-analysis/keywords?traffic_source=organic&branded_type=non_branded (top organic NB)
    9. website-analysis/keywords?traffic_source=organic&branded_type=branded (branded organic)
   10. website-analysis/keywords?traffic_source=paid&branded_type=non_branded (top paid NB)

  Referrals (v4):
   11. traffic-sources/referrals — incoming referring sites
   12. traffic-sources/outgoing-referrals — outbound destinations (search abandonment signal)

  Geography (v4):
   13. geo/total-traffic-by-country

  Demographics v2 (v4 — Business plan, graceful skip on 403):
   14. demographics_v2/age — age group breakdown

  Rank (v4):
   15. category-rank/category-rank

Usage:
  python3 collect-traffic.py <domain> <output-dir>
  SIMILARWEB_API_KEY env var (falls back to hardcoded key)

Output:
  <output-dir>/03-traffic-data.md   — human-readable scratchpad
  <output-dir>/03-traffic-data.json — structured JSON for generate-audit-data.py
"""

import sys, os, json, requests
from datetime import date, timedelta

API_KEY = os.environ.get('SIMILARWEB_API_KEY', '***REMOVED***')
TODAY = date.today().isoformat()

# Date range: last 3 completed months
END_DATE   = date.today().replace(day=1) - timedelta(days=1)
START_DATE = END_DATE.replace(month=max(1, END_DATE.month - 2))
START_STR  = START_DATE.strftime('%Y-%m')
END_STR    = END_DATE.strftime('%Y-%m')

# ── API helpers ────────────────────────────────────────────────────────────────

def _get(url, params):
    """Shared GET with error handling."""
    params = {**params, 'api_key': API_KEY}
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 403:
            return {'_error': f'403 — not available on this plan: {url}', '_status': 403}
        if r.status_code == 404:
            return {'_error': f'404 — domain not indexed: {url}', '_status': 404}
        if r.status_code == 429:
            return {'_error': '429 — rate limit hit', '_status': 429}
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {'_error': str(e)}

def v1(path, params=None):
    """Call a v1 SimilarWeb endpoint."""
    return _get(f"https://api.similarweb.com/v1/{path}", params or {})

def v4(path, params=None):
    """Call a v4 SimilarWeb endpoint."""
    return _get(f"https://api.similarweb.com/v4/{path}", params or {})

def ok(r):
    return '_error' not in r

# ── Formatters ─────────────────────────────────────────────────────────────────

def fmt_visits(v):
    try:
        v = float(v)
        if v >= 1e9: return f"{v/1e9:.1f}B"
        if v >= 1e6: return f"{v/1e6:.2f}M"
        if v >= 1e3: return f"{v/1e3:.0f}K"
        return f"{v:,.0f}"
    except: return str(v)

def fmt_pct(v, dec=2):
    try: return round(float(v) * 100, dec)
    except: return None

def fmt_dur(secs):
    try:
        s = int(float(secs))
        return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"
    except: return str(secs)

# ── Data collection ────────────────────────────────────────────────────────────

def collect(domain):
    base = {'start_date': START_STR, 'end_date': END_STR, 'country': 'world',
            'main_domain_only': 'false', 'granularity': 'monthly'}
    r = {}

    # 1-4. Engagement metrics (v1)
    r['visits_total']   = v1(f"website/{domain}/traffic-and-engagement/visits",          {**base, 'web_source': 'total'})
    r['bounce_rate']    = v1(f"website/{domain}/traffic-and-engagement/bounce-rate",     {**base, 'web_source': 'total'})
    r['pages_per_visit']= v1(f"website/{domain}/traffic-and-engagement/pages-per-visit", {**base, 'web_source': 'total'})
    r['avg_duration']   = v1(f"website/{domain}/traffic-and-engagement/average-visit-duration", {**base, 'web_source': 'total'})

    # 5-6. Device split (v1)
    r['visits_desktop'] = v1(f"website/{domain}/traffic-and-engagement/visits", {**base, 'web_source': 'desktop'})
    r['visits_mobile']  = v1(f"website/{domain}/traffic-and-engagement/visits", {**base, 'web_source': 'mobile_web'})

    # 7. Marketing channels (v1 — correct endpoint name)
    r['channels'] = v1(f"website/{domain}/traffic-sources/overview-share",
                       {'start_date': START_STR, 'end_date': END_STR, 'country': 'world', 'main_domain_only': 'false'})

    # 8-10. Keywords — Search 3.0 (v4, replaces deprecated Search 1.0)
    kw_base = {'domain': domain, 'start_date': START_STR, 'end_date': END_STR,
               'country': 'world', 'limit': 100}
    r['kw_organic_nb']  = v4("website-analysis/keywords", {**kw_base, 'traffic_source': 'organic',  'branded_type': 'non_branded'})
    r['kw_organic_br']  = v4("website-analysis/keywords", {**kw_base, 'traffic_source': 'organic',  'branded_type': 'branded'})
    r['kw_paid_nb']     = v4("website-analysis/keywords", {**kw_base, 'traffic_source': 'paid',     'branded_type': 'non_branded'})

    # 11. Incoming referrals (v4)
    r['referrals_in']   = v4(f"website/{domain}/traffic-sources/referrals",
                              {'start_date': START_STR, 'end_date': END_STR, 'country': 'world', 'limit': 10})

    # 12. Outgoing referrals — search abandonment signal (v4, was missing entirely)
    r['referrals_out']  = v4(f"website/{domain}/traffic-sources/outgoing-referrals",
                              {'start_date': START_STR, 'end_date': END_STR, 'country': 'world', 'limit': 10})

    # 13. Geography (v4)
    r['geo'] = v4(f"website/{domain}/geo/total-traffic-by-country",
                  {'start_date': START_STR, 'end_date': END_STR})

    # 14. Demographics v2 (v4 — Business plan, gracefully skip on 403)
    r['demo_age']   = v4(f"website/{domain}/demographics_v2/age",
                         {'start_date': START_STR, 'end_date': END_STR, 'country': 'world'})

    # 15. Rank (v4)
    r['rank'] = v4(f"website/{domain}/category-rank/category-rank")

    return r

# ── Extract helpers ────────────────────────────────────────────────────────────

def latest_val(data, *keys):
    """Extract the most recent value from a time-series response."""
    if not ok(data): return None
    for k in keys:
        arr = data.get(k)
        if isinstance(arr, list) and arr:
            last = arr[-1]
            for fk in keys + ('value', 'visits'):
                if fk in last: return last[fk]
    return None

def extract_channels(data):
    """Return list of {channel, share_pct} from overview-share response."""
    if not ok(data): return []
    # v1 overview-share returns a list of channel objects
    rows = data.get('overview', data.get('visits', []))
    if not isinstance(rows, list): return []
    out = []
    for row in rows:
        name = row.get('source_type') or row.get('channel') or row.get('name') or 'Unknown'
        share = row.get('share') or row.get('visits_share') or 0
        try: share = round(float(share) * 100, 2)
        except: share = 0.0
        out.append({'channel': name, 'share_pct': share})
    return sorted(out, key=lambda x: x['share_pct'], reverse=True)

def extract_kw(data, limit=5):
    """Return list of {keyword, share_pct, volume, position} from Search 3.0 response."""
    if not ok(data): return []
    kws = data.get('keywords') or data.get('data', {}).get('keywords') or []
    out = []
    for k in kws[:limit]:
        out.append({
            'keyword':    k.get('name') or k.get('keyword') or k.get('query') or '',
            'share_pct':  round(float(k.get('share') or k.get('organic_share') or 0), 4),
            'volume':     k.get('search_volume') or k.get('volume'),
            'position':   k.get('position'),
            'mom_change': k.get('change') or k.get('mom_change') or '—'
        })
    return out

def extract_referrals(data, limit=5):
    """Return list of {domain, share_pct, mom_change} from referrals response."""
    if not ok(data): return []
    sites = data.get('sites') or data.get('referrals') or data.get('data', {}).get('sites') or []
    out = []
    for s in sites[:limit]:
        dom = s.get('site') or s.get('domain') or s.get('name') or ''
        share = round(float(s.get('share') or s.get('referral_share') or s.get('traffic_share') or 0) * 100, 2)
        mom   = s.get('change') or s.get('mom_change') or '—'
        out.append({'domain': dom, 'share_pct': share, 'mom_change': mom})
    return out

def extract_geo(data, limit=5):
    """Return list of {country, traffic_share_pct, mom_change}."""
    if not ok(data): return []
    records = data.get('records') or data.get('data', {}).get('records') or []
    out = []
    for c in records[:limit]:
        country = c.get('country_name') or c.get('country') or ''
        share   = round(float(c.get('share') or c.get('traffic_share') or 0) * 100, 2)
        mom     = c.get('change') or '—'
        out.append({'country': country, 'traffic_share_pct': share, 'mom_change': mom})
    return out

def extract_age(data):
    """Return age distribution dict from demographics_v2/age response."""
    if not ok(data): return {}
    age_arr = data.get('age') or data.get('data', {}).get('age') or []
    out = {}
    for item in age_arr:
        group = item.get('age_group') or item.get('group') or ''
        share = round(float(item.get('share') or item.get('percentage') or 0) * 100, 2)
        if group: out[group] = share
    return out

# ── Build structured JSON ──────────────────────────────────────────────────────

def build_json(domain, r):
    sw_url = f"https://www.similarweb.com/website/{domain}/"
    source = f"[FACT — SimilarWeb API v4, {sw_url}, {TODAY}]"

    # Visits
    visits_raw = latest_val(r['visits_total'], 'visits', 'value')
    bounce_raw = latest_val(r['bounce_rate'],  'bounce_rate', 'value')
    pages_raw  = latest_val(r['pages_per_visit'], 'pages_per_visit', 'value')
    dur_raw    = latest_val(r['avg_duration'], 'average_visit_duration', 'value')

    # Device split
    d_raw = latest_val(r['visits_desktop'], 'visits', 'value') or 0
    m_raw = latest_val(r['visits_mobile'],  'visits', 'value') or 0
    total_dv = (d_raw or 0) + (m_raw or 0)
    mobile_pct  = round(m_raw / total_dv * 100, 2) if total_dv > 0 else None
    desktop_pct = round(d_raw / total_dv * 100, 2) if total_dv > 0 else None

    # Channels
    channels = extract_channels(r['channels'])

    # Organic % and branded split
    organic_share = next((c['share_pct'] for c in channels if 'organic' in c['channel'].lower()), None)
    paid_share    = next((c['share_pct'] for c in channels if 'paid' in c['channel'].lower()), None)

    kw_nb = extract_kw(r['kw_organic_nb'], 5)
    kw_br = extract_kw(r['kw_organic_br'], 5)
    kw_pd = extract_kw(r['kw_paid_nb'], 5)

    # Branded vs non-branded estimation from keyword volumes
    # (Search 3.0 doesn't return a single branded_pct — compute from share totals)
    br_total_share = sum(k['share_pct'] for k in kw_br) if kw_br else None
    nb_total_share = sum(k['share_pct'] for k in kw_nb) if kw_nb else None

    # Referrals
    refs_in  = extract_referrals(r['referrals_in'],  5)
    refs_out = extract_referrals(r['referrals_out'], 5)

    # Search abandonment: google.com in outgoing
    google_out = next((x for x in refs_out if 'google.com' == x.get('domain', '')), None)

    # AI referral: chatgpt.com in incoming
    chatgpt_ref = next((x for x in refs_in if 'chatgpt.com' in x.get('domain', '')), None)
    gemini_ref  = next((x for x in refs_in if 'gemini.google.com' in x.get('domain', '')), None)

    # Geography
    geo = extract_geo(r['geo'], 5)

    # Demographics
    age = extract_age(r['demo_age'])
    demo_status = 'ok' if ok(r['demo_age']) else r['demo_age'].get('_error', 'failed')

    # Rank
    rank_data = r['rank'] if ok(r['rank']) else {}
    global_rank   = rank_data.get('global_rank')
    category      = rank_data.get('category')
    category_rank = rank_data.get('category_rank')

    # Search audit signals
    signals = []
    if organic_share:
        signals.append(f"Organic search is {organic_share}% of traffic — search-dependent acquisition")
    if paid_share:
        signals.append(f"Paid search is {paid_share}% — spending to drive traffic that site search must convert")
    if google_out:
        signals.append(f"{google_out['share_pct']}% of outbound goes to google.com ({google_out.get('mom_change','')}) — quantified search abandonment")
    if chatgpt_ref:
        signals.append(f"ChatGPT is a top referral source at {chatgpt_ref['share_pct']}% ({chatgpt_ref.get('mom_change','')}) — AI discovery channel")
    if bounce_raw:
        try: signals.append(f"Bounce rate {round(float(bounce_raw)*100,2)}% — search quality directly affects this metric")
        except: pass
    if mobile_pct and mobile_pct > 60:
        signals.append(f"Mobile is {mobile_pct}% of traffic — mobile search UX is the primary conversion lever")

    # Errors summary
    errors = {k: v['_error'] for k, v in r.items() if not ok(v)}

    return {
        'meta': {
            'skill_enrichment_completed': True,
            'domain': domain,
            'collection_date': TODAY,
            'data_quality': 'API_COLLECTED',
            'source_primary': f'SimilarWeb API v4 — {TODAY}',
            'period': f'{START_STR} – {END_STR}',
            'geography': 'Worldwide',
            'traffic_type': 'All Traffic',
            'api_version': 'v4 (Search 3.0 keywords)',
            'endpoints_called': len(r),
            'endpoints_ok':     sum(1 for v in r.values() if ok(v)),
            'errors': errors
        },
        'monthly_visits':          fmt_visits(visits_raw) if visits_raw else None,
        'bounce_rate_pct':         round(float(bounce_raw) * 100, 2) if bounce_raw else None,
        'pages_per_visit':         round(float(pages_raw), 2) if pages_raw else None,
        'visit_duration_formatted': fmt_dur(dur_raw) if dur_raw else None,
        'visit_duration_seconds':   int(float(dur_raw)) if dur_raw else None,
        'device_split': {
            'mobile_web_pct': mobile_pct,
            'desktop_pct':    desktop_pct,
            'source': source
        },
        'rankings': {
            'global_rank':     global_rank,
            'category':        category,
            'category_rank':   category_rank,
            'source': source
        },
        'traffic_channels': [
            {'channel': c['channel'], 'share_pct': c['share_pct']} for c in channels
        ],
        'channels_source': source,
        'organic_search': {
            'share_of_total_pct':        organic_share,
            'branded_pct':               None,   # not a direct API field in Search 3.0
            'non_branded_pct':           None,   # computed manually if needed
            'branded_kw_share_sample':   br_total_share,
            'non_branded_kw_share_sample': nb_total_share,
            'top_non_branded_keywords':  kw_nb,
            'top_branded_keywords':      kw_br,
            'source': source
        },
        'paid_search': {
            'share_of_total_pct':        paid_share,
            'top_non_branded_keywords':  kw_pd,
            'competitor_bidding':        None,
            'source': source
        },
        'geography': {
            'top_countries': geo,
            'source': source
        },
        'referrals': {
            'top_referring_sites': refs_in,
            'top_referring_industries': [],   # UI-only — not available via API
            'source': source
        },
        'outgoing_traffic': {
            'top_link_destinations': refs_out,
            'source': source
        },
        'search_abandonment': {
            'google_outbound_pct':        f"{google_out['share_pct']}%" if google_out else None,
            'google_outbound_mom_change': google_out.get('mom_change') if google_out else None,
            'narrative': f"{google_out['share_pct']}% of outbound traffic goes to Google — users abandoning on-site search" if google_out else None,
            'source': source
        } if google_out else None,
        'ai_referral': {
            'chatgpt_pct':   f"{chatgpt_ref['share_pct']}%" if chatgpt_ref else None,
            'chatgpt_mom':   chatgpt_ref.get('mom_change') if chatgpt_ref else None,
            'gemini_pct':    f"{gemini_ref['share_pct']}%" if gemini_ref else None,
            'total_ai_pct':  None,   # sum of all AI referrers — compute manually
            'narrative':     f"ChatGPT sends {chatgpt_ref['share_pct']}% of referrals ({chatgpt_ref.get('mom_change','')}) — AI discovery channel growing" if chatgpt_ref else None,
            'source': source
        } if chatgpt_ref else None,
        'demographics': {
            'age': age,
            'gender': None,   # demographics_v2/groups endpoint needed (separate call)
            'status': demo_status,
            'source': source if ok(r['demo_age']) else 'demographics_v2 requires Business plan'
        },
        'search_audit_signals': signals
    }

# ── Write markdown ─────────────────────────────────────────────────────────────

def build_md(domain, data):
    sw_url = f"https://www.similarweb.com/website/{domain}/"
    src = f"[FACT — SimilarWeb API v4, {sw_url}, {TODAY}]"
    lines = [
        f"# Traffic Data — {domain}",
        f"*Generated: {TODAY} via collect-traffic.py v2.0 (SimilarWeb API v4)*",
        "",
        f"## API Parameters",
        f"- Source: SimilarWeb API (v4 endpoints, Search 3.0 keywords)",
        f"- Period: {START_STR} to {END_STR} | Country: Worldwide | web_source: total",
        f"- Endpoints called: {data['meta']['endpoints_called']} | Successful: {data['meta']['endpoints_ok']}",
        f"- Deprecated endpoints removed: /organic-search/keywords (Search 1.0), /demographics/age-gender (Demo 1.0)",
        "",
        "## Monthly Traffic (Total — Desktop + Mobile)",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Monthly Visits | {data.get('monthly_visits','N/A')} |",
        f"| Bounce Rate | {data.get('bounce_rate_pct','N/A')}% |",
        f"| Pages per Visit | {data.get('pages_per_visit','N/A')} |",
        f"| Avg Visit Duration | {data.get('visit_duration_formatted','N/A')} |",
        src, "",
    ]

    # Device split
    ds = data.get('device_split', {})
    if ds.get('mobile_web_pct'):
        lines += [
            "## Device Split",
            f"- Mobile: {ds['mobile_web_pct']}%",
            f"- Desktop: {ds['desktop_pct']}%",
            src, ""
        ]

    # Traffic channels
    chs = data.get('traffic_channels', [])
    if chs:
        lines += ["## Traffic Channels (Marketing Mix)", "| Channel | Share |", "|---------|-------|"]
        for c in chs:
            lines.append(f"| {c['channel']} | {c['share_pct']}% |")
        lines += [src, ""]

    # Organic search
    og = data.get('organic_search', {})
    if og.get('top_non_branded_keywords'):
        lines += [
            f"## Organic Search",
            f"- Share of total traffic: {og.get('share_of_total_pct','N/A')}%",
            f"- Note: Branded/non-branded split not a direct API field in Search 3.0 (requires manual calculation from keyword share totals)",
            "",
            "### Top Organic Non-Branded Keywords (Search 3.0)",
            "| Keyword | Share | Volume | MoM |",
            "|---------|-------|--------|-----|",
        ]
        for k in og['top_non_branded_keywords']:
            lines.append(f"| {k['keyword']} | {k['share_pct']} | {k.get('volume','N/A')} | {k.get('mom_change','—')} |")
        lines += [src, ""]

    # Paid search
    ps = data.get('paid_search', {})
    if ps.get('top_non_branded_keywords'):
        lines += [
            f"## Paid Search",
            f"- Share of total traffic: {ps.get('share_of_total_pct','N/A')}%",
            "",
            "### Top Paid Non-Branded Keywords (Search 3.0)",
            "| Keyword | Share | Volume | MoM |",
            "|---------|-------|--------|-----|",
        ]
        for k in ps['top_non_branded_keywords']:
            lines.append(f"| {k['keyword']} | {k['share_pct']} | {k.get('volume','N/A')} | {k.get('mom_change','—')} |")
        lines += [src, ""]

    # Referrals (incoming)
    refs = data.get('referrals', {}).get('top_referring_sites', [])
    if refs:
        lines += ["## Top Referring Websites", "| Domain | Share | MoM |", "|--------|-------|-----|"]
        for r in refs:
            lines.append(f"| {r['domain']} | {r['share_pct']}% | {r.get('mom_change','—')} |")
        lines += [src, ""]

    # Outgoing traffic
    out_refs = data.get('outgoing_traffic', {}).get('top_link_destinations', [])
    if out_refs:
        lines += ["## Outgoing Traffic (Top Destinations)", "| Domain | Share | MoM |", "|--------|-------|-----|"]
        for r in out_refs:
            lines.append(f"| {r['domain']} | {r['share_pct']}% | {r.get('mom_change','—')} |")
        lines += [src, ""]

    # Geography
    geo = data.get('geography', {}).get('top_countries', [])
    if geo:
        lines += ["## Top Countries", "| Country | Share | MoM |", "|---------|-------|-----|"]
        for c in geo:
            lines.append(f"| {c['country']} | {c['traffic_share_pct']}% | {c.get('mom_change','—')} |")
        lines += [src, ""]

    # Demographics
    demo = data.get('demographics', {})
    if demo.get('age'):
        lines += ["## Age Distribution (Demographics v2)", "| Age Group | Share |", "|-----------|-------|"]
        for group, pct in demo['age'].items():
            lines.append(f"| {group} | {pct}% |")
        lines += [src, ""]
    elif '403' in str(demo.get('status', '')):
        lines += ["## Demographics", "- Requires Business plan — 403 returned", ""]

    # Search audit signals
    sigs = data.get('search_audit_signals', [])
    if sigs:
        lines += ["## Search Audit Signals"]
        for s in sigs:
            lines.append(f"- {s}")
        lines += [src, ""]

    # Errors
    errors = data['meta'].get('errors', {})
    if errors:
        lines += ["## API Errors"]
        for ep, err in errors.items():
            lines.append(f"- {ep}: {err}")
        lines.append("")

    return "\n".join(lines)

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("Usage: collect-traffic.py <domain> <output-dir>", file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1].lower().replace('https://','').replace('http://','').replace('www.','').split('/')[0]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    print(f"Collecting traffic data for {domain} via SimilarWeb API v4...", file=sys.stderr)
    raw = collect(domain)

    ok_count = sum(1 for v in raw.values() if ok(v))
    total    = len(raw)
    print(f"Endpoints: {ok_count}/{total} successful", file=sys.stderr)

    # Build structured output
    data = build_json(domain, raw)

    # Write JSON
    json_path = os.path.join(output_dir, '03-traffic-data.json')
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    # Write MD
    md_path = os.path.join(output_dir, '03-traffic-data.md')
    with open(md_path, 'w') as f:
        f.write(build_md(domain, data))

    print(json.dumps({
        'status':           'success' if ok_count > total // 2 else 'partial',
        'domain':           domain,
        'endpoints_called': total,
        'endpoints_ok':     ok_count,
        'json_output':      json_path,
        'md_output':        md_path,
        'json_bytes':       os.path.getsize(json_path),
        'md_bytes':         os.path.getsize(md_path),
        'errors':           data['meta']['errors']
    }, indent=2))

if __name__ == '__main__':
    main()
