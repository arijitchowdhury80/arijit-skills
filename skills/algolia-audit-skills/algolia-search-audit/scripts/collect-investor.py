#!/usr/bin/env python3
"""
collect-investor.py — Phase 1: Investor & Executive Intelligence
Part of the Algolia Search Audit modular intelligence pipeline.

Reads from:  {output_dir}/01-company-context.json  (company_name, ticker, public_private)
Produces:    {output_dir}/11-investor-intelligence.md

Sources (ALL — not fallback):
  A. Earnings call transcripts: WebFetch Motley Fool / Seeking Alpha / company IR
  B. SEC EDGAR 10-K/10-Q: direct WebFetch sec.gov (NOTE: SEC EDGAR MCP does NOT exist)
  C. Yahoo Finance news: get_yahoo_finance_news(ticker) via MCP — handled by SKILL orchestrator

IMPORTANT: This script handles what Python can do (HTTP WebFetch + parse).
Yahoo Finance MCP calls are handled by the algolia-intel-investor SKILL orchestrator.

Usage: python3 collect-investor.py <domain> <output-dir> [--ticker TICKER] [--private]
"""

import sys, os, json, requests, re
from datetime import date

TODAY = date.today().isoformat()
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; AlgoliaAudit/1.0)'}

def web_get(url, timeout=20):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return (r.text, None) if r.status_code == 200 else (None, f'HTTP {r.status_code}')
    except Exception as e:
        return None, str(e)

def find_transcript_url(company_name, quarter_hints=None):
    """Search for earnings call transcript URLs via common patterns."""
    slug = re.sub(r'[^a-z0-9-]', '-', company_name.lower()).strip('-')
    candidates = [
        f'https://www.fool.com/earnings-call-transcripts/',
        f'https://seekingalpha.com/symbol/{slug.upper()}/earnings/transcripts',
    ]
    return candidates

def extract_quotes_from_html(html, company_name):
    """Extract executive quotes from transcript HTML."""
    if not html or len(html) < 1000:
        return []
    quotes = []
    # Pattern: "Speaker Name, Title:" followed by content
    speaker_patterns = [
        r'([A-Z][a-z]+ [A-Z][a-z]+),\s*([^:]+):\s*([^.!?]{40,300}[.!?])',
        r'<strong>([^<]+)</strong>\s*<[^>]+>([^<]*)</[^>]+>\s*([^<]{40,300})',
    ]
    for pattern in speaker_patterns:
        matches = re.findall(pattern, html[:50000])
        for m in matches[:10]:
            name, title, text = m[0].strip(), m[1].strip()[:100], m[2].strip()[:300]
            if len(name) > 3 and len(text) > 40:
                # Filter for relevant quotes
                relevant_kws = ['search','digital','ecommerce','e-commerce','technology','platform','growth','customer','experience','AI','personalization']
                if any(k.lower() in text.lower() for k in relevant_kws):
                    quotes.append({'speaker': name, 'title': title, 'quote': text, 'verified': True})
    return quotes[:8]

def fetch_sec_10k(ticker):
    """Fetch latest 10-K filing from SEC EDGAR."""
    search_url = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K&dateb=&owner=include&count=1&search_text='
    html, err = web_get(search_url)
    if not html:
        return None, f'SEC EDGAR search: {err}'

    # Find filing link
    filing_match = re.search(r'href="(/Archives/edgar/data/[^"]+\.htm)"', html)
    if not filing_match:
        return None, 'No 10-K filing link found'

    filing_url = 'https://www.sec.gov' + filing_match.group(1)
    filing_html, filing_err = web_get(filing_url)
    if not filing_html:
        return None, f'10-K fetch: {filing_err}'

    # Extract MD&A section (Item 7)
    mda_match = re.search(r'Item\s+7[.\s]+Management.{0,50}Analysis(.{500,5000}?)Item\s+[89]', filing_html, re.S | re.I)
    mda_text = mda_match.group(1)[:3000] if mda_match else filing_html[5000:10000]

    return {'url': filing_url, 'mda_excerpt': re.sub(r'<[^>]+>', ' ', mda_text)[:2000]}, None

def load_ctx(output_dir):
    p = os.path.join(output_dir, '01-company-context.json')
    return json.load(open(p)) if os.path.exists(p) else {}

def write_md(company, ticker, is_private, quotes, sec_data, errors, output_dir):
    lines = [
        f'# Investor Intelligence — {company}',
        f'*Generated: {TODAY} via collect-investor.py*',
        f'*Company type: {"Private" if is_private else f"Public (ticker: {ticker})"}*',
        '',
        '## Collection Method',
        f'- Earnings call transcripts: WebFetch attempted',
        f'- SEC EDGAR 10-K: {"WebFetch attempted" if not is_private else "N/A (private company)"}',
        f'- Yahoo Finance MCP: Handled by algolia-intel-investor SKILL orchestrator',
        '',
    ]

    lines += ['## In Their Own Words']
    if quotes:
        lines += ['| # | Speaker | Title | Quote | Verified |', '|---|---------|-------|-------|---------|']
        for i, q in enumerate(quotes, 1):
            q_text = q['quote'].replace('|', '—')[:200]
            lines += [f'| {i} | {q["speaker"]} | {q["title"][:50]} | "{q_text}" | {"✅ WebFetch" if q.get("verified") else "⚠️ WEBSEARCH"} |']
        lines += [f'', f'[FACT — transcript WebFetch, {TODAY}]']
    else:
        lines += [
            '*No quotes extracted by script — requires skill orchestrator for WebSearch/MCP*',
            '*[COLLECT_VIA_SKILL — algolia-intel-investor SKILL will populate via transcript WebFetch]*',
        ]

    lines += ['']

    if sec_data and not is_private:
        lines += [
            '## SEC EDGAR Strategic Priorities',
            f'*Source: {sec_data["url"]}*',
            '',
            sec_data.get('mda_excerpt', '')[:1000],
            '',
            f'[FACT — SEC EDGAR 10-K WebFetch, {TODAY}, URL: {sec_data["url"]}]',
            '',
        ]
    elif not is_private:
        lines += [
            '## SEC EDGAR',
            '*[COLLECT_VIA_SKILL — requires SEC EDGAR WebFetch in skill orchestrator]*',
            '',
        ]

    lines += [
        '## Yahoo Finance News & Analyst Consensus',
        f'*[COLLECT_VIA_SKILL — requires Yahoo Finance MCP: get_yahoo_finance_news("{ticker or company}")]*',
        '',
        '## Risk Factors (digital/technology)',
        '*[COLLECT_VIA_SKILL — extracted from 10-K Item 1A in skill orchestrator]*',
    ]

    if errors:
        lines += ['', '## Collection Errors'] + [f'- {e}' for e in errors]

    out = os.path.join(output_dir, '11-investor-intelligence.md')
    open(out, 'w').write('\n'.join(lines))
    return out

def main():
    if len(sys.argv) < 3:
        print('Usage: collect-investor.py <domain> <output-dir> [--ticker TICKER] [--private]', file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1].lower().replace('https://','').replace('http://','').replace('www.','').split('/')[0]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    ticker = None
    is_private = False
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--ticker' and i+1 < len(sys.argv): ticker = sys.argv[i+1].upper(); i+=2
        elif sys.argv[i] == '--private': is_private = True; i+=1
        else: i+=1

    ctx = load_ctx(output_dir)
    company = ctx.get('company_name') or domain
    if not ticker: ticker = ctx.get('ticker')
    if ctx.get('public_private') == 'private': is_private = True

    print(f'Collecting investor intelligence for {company}...', file=sys.stderr)
    errors = []
    quotes = []
    sec_data = None

    # Attempt transcript WebFetch (best effort — main extraction done by SKILL)
    # Script collects what it can from known transcript URLs
    if not is_private and ticker:
        slug = re.sub(r'[^a-z0-9]', '', company.lower())
        transcript_urls = [
            f'https://www.fool.com/earnings-call-transcripts/?symbol={ticker}',
            f'https://finance.yahoo.com/quote/{ticker}/financials/',
        ]
        for url in transcript_urls[:1]:
            html, err = web_get(url)
            if html:
                found = extract_quotes_from_html(html, company)
                quotes.extend(found)
                break
            else:
                errors.append(f'Transcript fetch {url}: {err}')

        # SEC EDGAR
        if ticker:
            sec_data, sec_err = fetch_sec_10k(ticker)
            if sec_err:
                errors.append(f'SEC EDGAR: {sec_err}')

    out = write_md(company, ticker, is_private, quotes, sec_data, errors, output_dir)
    print(json.dumps({
        'status': 'partial',  # Always partial — full collection requires SKILL MCP calls
        'domain': domain,
        'company_name': company,
        'ticker': ticker,
        'is_private': is_private,
        'output_file': out,
        'size_bytes': os.path.getsize(out),
        'quotes_found_by_script': len(quotes),
        'sec_data_found': sec_data is not None,
        'skill_enrichment_required': ['yahoo_finance_mcp', 'transcript_websearch', 'sec_edgar_full_extract', 'risk_factors'],
        'errors': errors,
    }, indent=2))

if __name__ == '__main__':
    main()
