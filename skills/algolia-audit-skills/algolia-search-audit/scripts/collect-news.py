#!/usr/bin/env python3
"""
collect-news.py — Phase 1: News Signals Collection
Part of the Algolia Search Audit modular intelligence pipeline.

Reads from:  {output_dir}/01-company-context.json  (company_name, domain)
Produces:    {output_dir}/09c-news-signals.md

Sources (ALL attempted — not fallback):
  1. Google News RSS — 3 queries × 10 items (free, no API key, keyword search)
     URL: https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en
  2. RSS feeds: {domain}/press, /newsroom, /news (direct HTTP)
  3. Lookback: 60 days

Note: The Apify data_xplorer/google-news-scraper-fast actor no longer supports keyword search
(changed API: only accepts topic category enums like BUSINESS, TECHNOLOGY). Replaced with
direct Google News RSS which is free, always available, and supports keyword search.

Usage: python3 collect-news.py <domain> <output-dir> [--company-name "Name"]
Env:   APIFY_TOKEN
"""

import sys, os, json, requests, re, time
from datetime import date, timedelta

TODAY = date.today().isoformat()
CUTOFF = (date.today() - timedelta(days=60)).isoformat()
APIFY_TOKEN = os.environ.get('APIFY_TOKEN', '')
APIFY_BASE = 'https://api.apify.com/v2'

CATEGORIES = {
    'LEADERSHIP_CHANGE': ['hired','appointed','named','joins as','new CEO','new CTO','new CDO','new VP'],
    'FUNDING_EVENT':     ['raised','funding','investment','Series','IPO','M&A','acquisition','merger'],
    'TECH_INVESTMENT':   ['AI','machine learning','platform','modernization','migration','cloud','digital'],
    'PRODUCT_LAUNCH':    ['launches','introduces','new product','new category','new collection'],
    'INTERNATIONAL':     ['expansion','global','enters market','international','cross-border'],
    'DIGITAL_INITIATIVE':['digital','ecommerce','online','D2C','omnichannel'],
    'COMPETITIVE':       ['loses to','faces competition','market share','rival'],
}

def categorize(title, summary=''):
    text = (title + ' ' + summary).lower()
    for cat, kws in CATEGORIES.items():
        if any(k.lower() in text for k in kws):
            return cat
    return 'GENERAL'

def apify_run(actor_id, input_data, max_wait=60):
    if not APIFY_TOKEN: return None, 'APIFY_TOKEN not set'
    try:
        r = requests.post(f'{APIFY_BASE}/acts/{actor_id}/runs?token={APIFY_TOKEN}', json=input_data, timeout=30)
        r.raise_for_status()
        run_id = r.json()['data']['id']
    except Exception as e: return None, str(e)
    elapsed, status = 0, 'RUNNING'
    while elapsed < max_wait and status not in ('SUCCEEDED','FAILED','ABORTED'):
        time.sleep(5); elapsed += 5
        try: status = requests.get(f'{APIFY_BASE}/actor-runs/{run_id}?token={APIFY_TOKEN}',timeout=10).json()['data']['status']
        except Exception: pass
    if status != 'SUCCEEDED': return None, f'Actor: {status}'
    try:
        ir = requests.get(f'{APIFY_BASE}/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}&clean=true',timeout=30)
        ir.raise_for_status(); return ir.json(), None
    except Exception as e: return None, str(e)

def fetch_rss(domain):
    """Try company RSS/newsroom feeds."""
    articles = []
    for path in ['/press','/newsroom','/news','/blog']:
        try:
            r = requests.get(f'https://www.{domain}{path}',headers={'User-Agent':'Mozilla/5.0'},timeout=10)
            if r.status_code == 200 and len(r.text) > 500:
                headlines = re.findall(r'<title[^>]*><!\[CDATA\[([^\]]+)\]\]>|<title[^>]*>([^<]{20,150})</title>', r.text)
                for h in headlines[:5]:
                    title = (h[0] or h[1]).strip()
                    if title and domain.lower() not in title.lower()[:30]:
                        articles.append({'title':title,'url':f'https://www.{domain}{path}','date':TODAY,'source':'RSS/Newsroom WebFetch','category':categorize(title)})
                if articles: break
        except Exception:
            continue
    return articles

def load_ctx(output_dir):
    p = os.path.join(output_dir,'01-company-context.json')
    return json.load(open(p)) if os.path.exists(p) else {}

def write_md(company, articles, errors, output_dir):
    immediate = [a for a in articles if a['category'] in ('LEADERSHIP_CHANGE','FUNDING_EVENT')]
    strategic = [a for a in articles if a['category'] in ('TECH_INVESTMENT','DIGITAL_INITIATIVE','INTERNATIONAL')]
    context_  = [a for a in articles if a['category'] in ('PRODUCT_LAUNCH','COMPETITIVE','GENERAL')]

    lines = [
        f'# News Signals — {company}',
        f'*Generated: {TODAY} via collect-news.py*',
        f'*Sources: Tavily (primary) / Google News RSS (fallback) / RSS/Newsroom WebFetch | Lookback: 60 days*',
        '',
        f'## Collection Summary',
        f'- Total articles: {len(articles)} | Lookback cutoff: {CUTOFF}',
        '',
        '## 🔴 Immediate Action Signals (Leadership + Funding)',
    ]
    for a in immediate:
        lines += [
            f'### {a["title"]}',
            f'- Source: {a.get("source","Google News")} | Date: {a.get("date",TODAY)}',
            f'- Category: {a["category"]}',
            f'- Algolia angle: {"New exec = tech review window open" if a["category"]=="LEADERSHIP_CHANGE" else "Budget signal — evaluate timing"}',
            f'- URL: {a.get("url","n/a")}',
            f'- [FACT — Google News via Apify, {TODAY}]',
            '',
        ]
    if not immediate: lines += ['*None found*','']

    lines += ['## 🟡 Strategic Signals (Tech + Digital + International)']
    for a in strategic:
        lines += [f'- **{a["title"]}** ({a.get("date","")}) [{a["category"]}] — {a.get("url","n/a")}']
    if not strategic: lines += ['*None found*']

    lines += ['','## 🟢 Context Signals']
    for a in context_[:5]:
        lines += [f'- {a["title"]} [{a["category"]}]']
    if not context_: lines += ['*None found*']

    lines += [
        '',
        '## Summary (last 60 days)',
        '*(Pattern synthesis populated by algolia-intel-news SKILL)*',
        '',
        f'[FACT — Google News via Apify (data_xplorer/google-news-scraper-fast), {TODAY}]',
    ]
    if errors: lines += ['','## Collection Errors'] + [f'- {e}' for e in errors]

    out = os.path.join(output_dir, '09c-news-signals.md')
    open(out,'w').write('\n'.join(lines))
    return out

def main():
    if len(sys.argv) < 3:
        print('Usage: collect-news.py <domain> <output-dir> [--company-name "Name"]', file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1].lower().replace('https://','').replace('http://','').replace('www.','').split('/')[0]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    override = None; i = 3
    while i < len(sys.argv):
        if sys.argv[i]=='--company-name' and i+1<len(sys.argv): override=sys.argv[i+1]; i+=2
        else: i+=1

    ctx = load_ctx(output_dir)
    company = override or ctx.get('company_name') or domain
    errors = []

    queries = [
        f'"{company}" digital OR ecommerce OR technology OR search',
        f'"{company}" executive OR leadership OR hire OR appoint',
        f'"{company}" launch OR expansion OR international OR AI',
    ]

    articles = []
    use_tavily = bool(os.environ.get('TAVILY_API_KEY', ''))

    for q in queries:
        if use_tavily:
            # Primary: Tavily news search — AI-optimised, returns clean extracted text,
            # supports date filtering natively, no actor schema drift risk.
            # No layering needed here: Tavily returns structured data directly,
            # keyword classifier handles categorisation — no LLM required.
            try:
                from tavily import TavilyClient
                client = TavilyClient(api_key=os.environ['TAVILY_API_KEY'])
                response = client.search(
                    query=q,
                    topic='news',
                    days=60,
                    max_results=10,
                )
                for item in response.get('results', []):
                    pub_date = (item.get('published_date') or TODAY)[:10]
                    if pub_date >= CUTOFF and item.get('title'):
                        articles.append({
                            'title': item['title'],
                            'url': item.get('url', 'n/a'),
                            'date': pub_date,
                            'source': f'[FACT — Tavily news search, {pub_date}]',
                            'category': categorize(item['title'], item.get('content', '')),
                        })
            except Exception as e:
                errors.append(f'Tavily query "{q[:40]}": {e}')
                # Fall through to RSS fallback below
        else:
            # Fallback: Google News RSS (free, no key, keyword search works)
            try:
                rss_url = f'https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=en-US&gl=US&ceid=US:en'
                r = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                if r.status_code == 200:
                    items_xml = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
                    for item_xml in items_xml[:10]:
                        title_m = re.search(r'<title><!\[CDATA\[(.+?)\]\]>|<title>([^<]+)</title>', item_xml)
                        link_m  = re.search(r'<link>([^<]+)</link>', item_xml)
                        date_m  = re.search(r'<pubDate>([^<]+)</pubDate>', item_xml)
                        title = (title_m.group(1) or title_m.group(2) or '').strip() if title_m else ''
                        url   = (link_m.group(1) or '').strip() if link_m else 'n/a'
                        pub_date = TODAY
                        if date_m:
                            from email.utils import parsedate
                            parsed = parsedate(date_m.group(1))
                            if parsed:
                                pub_date = f'{parsed[0]}-{parsed[1]:02d}-{parsed[2]:02d}'
                        if pub_date >= CUTOFF and title:
                            articles.append({'title': title, 'url': url, 'date': pub_date,
                                             'source': f'[FACT — Google News RSS, {pub_date}]',
                                             'category': categorize(title, '')})
                else:
                    errors.append(f'Google News RSS query "{q[:40]}": HTTP {r.status_code}')
            except Exception as e:
                errors.append(f'Google News RSS query "{q[:40]}": {e}')
    # RSS fallback
    rss = fetch_rss(domain)
    if rss:
        articles.extend(rss)
    else:
        errors.append(f'RSS/Newsroom: no accessible feed at {domain}')

    # Deduplicate by title
    seen = set()
    unique = []
    for a in articles:
        key = a['title'][:60].lower()
        if key not in seen: seen.add(key); unique.append(a)
    unique.sort(key=lambda x: x.get('date',''), reverse=True)

    out = write_md(company, unique, errors, output_dir)
    print(json.dumps({'status':'success' if unique else 'partial','domain':domain,'company_name':company,'output_file':out,'size_bytes':os.path.getsize(out),'total_articles':len(unique),'errors':errors},indent=2))

if __name__ == '__main__':
    main()
