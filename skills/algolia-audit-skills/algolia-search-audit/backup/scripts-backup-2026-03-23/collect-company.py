#!/usr/bin/env python3
"""
collect-company.py — Phase 1, Step 1: Company Context Collection
Part of the Algolia Search Audit modular intelligence pipeline.

Produces two output files:
  {output_dir}/01-company-context.md   — human-readable scratchpad
  {output_dir}/01-company-context.json — machine-readable for downstream scripts

Downstream consumers of 01-company-context.json:
  collect-hiring.py   → reads: company_name, linkedin_url, domain
  collect-social.py   → reads: company_name, linkedin_url, twitter_handle, domain
  collect-news.py     → reads: company_name, domain
  collect-investor.py → reads: company_name, domain, ticker, public_private
  algolia-intel-queries SKILL → reads: vertical, company_name

Sources (ALL attempted — not fallback):
  1. BuiltWith keywords-api — SEO meta, company description (requires BUILTWITH_API_KEY)
  2. Company website WebFetch: /about, /company, /about-us (direct HTTP)
  3. LinkedIn company page WebFetch (best-effort — may require auth)

Note: Fields requiring WebSearch/MCP (executives, HQ, founded, vertical classification)
are marked as null in JSON output and populated by the algolia-intel-company SKILL.

Usage:
  python3 collect-company.py <domain> <output-dir> [--company-name "Name"] [--ticker TICKER]

Environment:
  BUILTWITH_API_KEY — BuiltWith API key (optional, improves meta extraction)
"""

import sys, os, json, requests, re
from datetime import date

TODAY = date.today().isoformat()
BUILTWITH_API_KEY = os.environ.get('BUILTWITH_API_KEY', '')

# ── HTTP ──────────────────────────────────────────────────────────────────────

def web_get(url, timeout=20):
    """HTTP GET. Returns (text_or_none, error_or_none)."""
    try:
        r = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; AlgoliaAudit/1.0)'},
            timeout=timeout,
            allow_redirects=True
        )
        if r.status_code == 200:
            return r.text, None
        return None, f'HTTP {r.status_code}'
    except requests.exceptions.Timeout:
        return None, 'timeout'
    except Exception as e:
        return None, str(e)

# ── Source: BuiltWith keywords-api ───────────────────────────────────────────

def builtwith_keywords(domain):
    """Call BuiltWith keywords-api. Returns (data_dict, error)."""
    if not BUILTWITH_API_KEY:
        return None, 'BUILTWITH_API_KEY not configured'
    url = f'https://api.builtwith.com/kw1/api.json?KEY={BUILTWITH_API_KEY}&LOOKUP={domain}'
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)

def extract_bw_meta(bw_data):
    """Extract company description from BuiltWith keywords response."""
    if not bw_data:
        return None
    results = bw_data.get('Results', [])
    if not results:
        return None
    kw = results[0].get('Keywords', {})
    return kw.get('MetaDescription') or kw.get('Description')

# ── Source: Company website ───────────────────────────────────────────────────

def extract_meta_description(html):
    if not html:
        return None
    for pattern in [
        r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)',
        r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']description',
        r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)',
    ]:
        m = re.search(pattern, html, re.I)
        if m:
            return m.group(1).strip()[:500]
    return None

def extract_page_title(html):
    if not html:
        return None
    m = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
    return m.group(1).strip()[:200] if m else None

def fetch_company_website(domain):
    """Try common about/company pages. Returns (url, description, title, error)."""
    paths = ['/about', '/about-us', '/company', '/our-story', '/who-we-are', '']
    for path in paths:
        url = f'https://www.{domain}{path}'
        html, err = web_get(url)
        if html and len(html) > 2000:
            desc = extract_meta_description(html)
            title = extract_page_title(html)
            if desc or title:
                return url, desc, title, None
    return f'https://www.{domain}', None, None, 'no accessible about page with meta description'

# ── Data collection ───────────────────────────────────────────────────────────

def collect(domain, company_name_override=None, ticker=None):
    """Run all sources. Returns structured results dict."""
    results = {
        'builtwith': {'data': None, 'error': None},
        'website':   {'url': None, 'description': None, 'title': None, 'error': None},
        'linkedin':  {'url': None, 'accessible': False, 'error': None},
    }

    # Source 1: BuiltWith
    bw_data, bw_err = builtwith_keywords(domain)
    results['builtwith']['data'] = bw_data
    results['builtwith']['error'] = bw_err

    # Source 2: Company website
    ws_url, ws_desc, ws_title, ws_err = fetch_company_website(domain)
    results['website']['url'] = ws_url
    results['website']['description'] = ws_desc
    results['website']['title'] = ws_title
    results['website']['error'] = ws_err

    # Source 3: LinkedIn (best-effort)
    company_slug = re.sub(r'[^a-z0-9-]', '-', domain.replace('.com', '').replace('.', '-').lower())
    li_url = f'https://www.linkedin.com/company/{company_slug}/'
    li_html, li_err = web_get(li_url)
    if li_html and 'linkedin' in li_html.lower() and len(li_html) > 1000:
        results['linkedin']['url'] = li_url
        results['linkedin']['accessible'] = True
    else:
        results['linkedin']['url'] = li_url
        results['linkedin']['accessible'] = False
        results['linkedin']['error'] = li_err or 'page requires auth or unavailable'

    return results

# ── Output writers ────────────────────────────────────────────────────────────

def build_json_record(domain, company_name_override, ticker, results):
    """
    Build the canonical JSON record consumed by downstream scripts.
    Fields that require WebSearch/MCP are set to null — populated by SKILL orchestrator.
    """
    # Best available description
    desc = results['website']['description'] or extract_bw_meta(results['builtwith']['data'])
    desc_source = None
    if results['website']['description']:
        desc_source = f"website WebFetch {results['website']['url']}"
    elif extract_bw_meta(results['builtwith']['data']):
        desc_source = 'BuiltWith keywords-api'

    # Infer display name
    display_name = company_name_override or results['website'].get('title', '').split('|')[0].split('-')[0].strip() or domain

    return {
        # ── Identity (collected by script) ──
        'domain': domain,
        'company_name': display_name,
        'company_slug': re.sub(r'[^a-z0-9-]', '-', display_name.lower()),
        'description': desc,
        'description_source': desc_source,
        'description_label': f'[FACT — {desc_source}, {TODAY}]' if desc_source else None,

        # ── URLs (collected by script) ──
        'about_url': results['website']['url'],
        'linkedin_url': results['linkedin']['url'],
        'linkedin_accessible': results['linkedin']['accessible'],
        'careers_url': f'https://www.{domain}/careers',  # verify manually
        'ir_url': None,  # populated by SKILL if public company

        # ── Fields requiring WebSearch/MCP — set null, populated by SKILL ──
        'hq': None,
        'hq_source': None,
        'founded': None,
        'founded_source': None,
        'employee_count': None,
        'employee_count_source': None,
        'public_private': None,
        'public_private_source': None,
        'vertical': None,
        'vertical_source': None,
        'business_model': None,  # B2C / B2B / Marketplace
        'ticker': ticker,        # passed as CLI arg if known
        'executives': [],        # populated by SKILL via WebSearch

        # ── Twitter/X (requires WebSearch — populated by SKILL) ──
        'twitter_handle': None,
        'twitter_handle_source': None,

        # ── Collection metadata ──
        'collected_at': TODAY,
        'collection_script': 'collect-company.py',
        'sources_attempted': ['builtwith_keywords_api', 'website_webfetch', 'linkedin_webfetch'],
        'sources_succeeded': [
            s for s, r in [
                ('builtwith_keywords_api', results['builtwith']['data'] is not None),
                ('website_webfetch', results['website']['description'] is not None),
                ('linkedin_webfetch', results['linkedin']['accessible']),
            ] if r
        ],
        'errors': {k: v.get('error') for k, v in results.items() if v.get('error')},
        'skill_enrichment_required': [
            'hq', 'founded', 'employee_count', 'public_private',
            'vertical', 'business_model', 'ticker', 'executives', 'twitter_handle', 'ir_url'
        ],
    }

def write_md(rec, output_dir):
    """Write human-readable 01-company-context.md."""
    name = rec['company_name']
    lines = [
        f'# Company Context — {name}',
        f'*Generated: {TODAY} via collect-company.py*',
        f'*Skill enrichment required for: {", ".join(rec["skill_enrichment_required"])}*',
        '',
        '## Collection Parameters',
        f'- Domain: {rec["domain"]}',
        f'- Sources attempted: {", ".join(rec["sources_attempted"])}',
        f'- Sources succeeded: {", ".join(rec["sources_succeeded"]) or "none"}',
        f'- Date: {TODAY}',
        '',
        '## Company Overview',
        '| Field | Value | Label |',
        '|-------|-------|-------|',
        f'| Company Name | {name} | [FACT — domain] |',
        f'| Domain | {rec["domain"]} | [FACT] |',
        f'| HQ | {rec["hq"] or "— populate via WebSearch"} | {rec.get("hq_source") or "[COLLECT_VIA_SKILL]"} |',
        f'| Founded | {rec["founded"] or "— populate via WebSearch"} | {rec.get("founded_source") or "[COLLECT_VIA_SKILL]"} |',
        f'| Employees | {rec["employee_count"] or "— populate via WebSearch/LinkedIn"} | {rec.get("employee_count_source") or "[COLLECT_VIA_SKILL]"} |',
        f'| Public/Private | {rec["public_private"] or "— populate via WebSearch"} | {rec.get("public_private_source") or "[COLLECT_VIA_SKILL]"} |',
        f'| Ticker | {rec["ticker"] or "— n/a or populate via WebSearch"} | |',
        f'| Vertical | {rec["vertical"] or "— classify via WebSearch"} | {rec.get("vertical_source") or "[COLLECT_VIA_SKILL]"} |',
        f'| Business Model | {rec["business_model"] or "— B2C/B2B/Marketplace"} | [COLLECT_VIA_SKILL] |',
        '',
    ]

    if rec['description']:
        lines += [
            '## Company Description',
            rec['description'],
            rec['description_label'] or '',
            '',
        ]

    lines += [
        '## Key URLs',
        f'- Website: https://www.{rec["domain"]}/',
        f'- About: {rec["about_url"]}',
        f'- LinkedIn: {rec["linkedin_url"]} {"[accessible]" if rec["linkedin_accessible"] else "[requires auth]"}',
        f'- Careers: {rec["careers_url"]} [verify manually]',
        f'- Twitter/X: {rec["twitter_handle"] or "— populate via WebSearch"} | [COLLECT_VIA_SKILL]',
        f'- IR page: {rec["ir_url"] or "— populate if public company"} | [COLLECT_VIA_SKILL]',
        '',
        '## Executive Team',
        '*(Populated by algolia-intel-company SKILL via WebSearch)*',
        '| Name | Title | LinkedIn | Source |',
        '|------|-------|----------|--------|',
        '',
        '## Collection Errors',
    ]
    for src, err in rec['errors'].items():
        lines.append(f'- {src}: {err}')
    if not rec['errors']:
        lines.append('- None')

    out = os.path.join(output_dir, '01-company-context.md')
    with open(out, 'w') as f:
        f.write('\n'.join(lines))
    return out

def write_json(rec, output_dir):
    """Write machine-readable 01-company-context.json for downstream scripts."""
    out = os.path.join(output_dir, '01-company-context.json')
    with open(out, 'w') as f:
        json.dump(rec, f, indent=2)
    return out

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print('Usage: collect-company.py <domain> <output-dir> [--company-name "Name"] [--ticker TICKER]', file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1].lower().replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    company_name_override = None
    ticker = None
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--company-name' and i + 1 < len(sys.argv):
            company_name_override = sys.argv[i + 1]; i += 2
        elif sys.argv[i] == '--ticker' and i + 1 < len(sys.argv):
            ticker = sys.argv[i + 1].upper(); i += 2
        else:
            i += 1

    print(f'Collecting company context for {domain}...', file=sys.stderr)
    results = collect(domain, company_name_override, ticker)
    rec = build_json_record(domain, company_name_override, ticker, results)

    md_path = write_md(rec, output_dir)
    json_path = write_json(rec, output_dir)

    print(json.dumps({
        'status': 'success' if rec['sources_succeeded'] else 'partial',
        'domain': domain,
        'company_name': rec['company_name'],
        'output_md': md_path,
        'output_json': json_path,
        'size_md_bytes': os.path.getsize(md_path),
        'size_json_bytes': os.path.getsize(json_path),
        'sources_succeeded': rec['sources_succeeded'],
        'errors': rec['errors'],
        'skill_enrichment_required': rec['skill_enrichment_required'],
    }, indent=2))

if __name__ == '__main__':
    main()
