#!/usr/bin/env python3
"""
collect-news.py — Phase 1: News Signals Collection
Part of the Algolia Search Audit modular intelligence pipeline.

Reads from:  {output_dir}/01-company-context.json  (company_name, domain)
Produces:    {output_dir}/09c-news-signals.md

Sources (ALL attempted — not fallback):
  1. Apify: data_xplorer/google-news-scraper-fast — 3 queries × 7 items (requires APIFY_TOKEN)
  2. RSS feeds: {domain}/press, /newsroom, /news (direct HTTP)
  3. Lookback: 60 days

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
        f'*Sources: Google News (Apify), RSS/Newsroom WebFetch | Lookback: 60 days*',
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
    for q in queries:
        items, err = apify_run('data_xplorer/google-news-scraper-fast', {'query':q,'maxItems':7,'language':'en'})
        if err: errors.append(f'Google News query "{q[:40]}...": {err}')
        for item in (items or []):
            pub_date = item.get('pubDate',item.get('publishedAt',TODAY))[:10]
            if pub_date >= CUTOFF:
                articles.append({'title':item.get('title',''),'url':item.get('link',item.get('url','n/a')),'date':pub_date,'source':'Google News via Apify','category':categorize(item.get('title',''),item.get('description',''))})

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
