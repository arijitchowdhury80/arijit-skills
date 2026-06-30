#!/usr/bin/env python3
"""
collect-news.py — Phase 1: News Signals Collection
Part of the Algolia Search Audit modular intelligence pipeline.

Reads from:  {output_dir}/01-company-context.json  (company_name, domain)
Produces:    {output_dir}/09c-news-signals.md

Sources (keyless — no API key, no Tavily, no Apify):
  1. Google News RSS — 3 keyword queries × 10 items (free, keyword search, dated)
     URL: https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en
  2. Company RSS/newsroom feeds: {domain}/press, /newsroom, /news (direct HTTP)
  3. Lookback: 60 days

History: Apify (data_xplorer/google-news-scraper-fast) was abandoned — its API
dropped keyword search (topic-enum only). Tavily was retired in the Gemini-grounded
migration; news kept Google News RSS as its primary because RSS returns structured,
dated, keyless article items (the right shape for news) where Gemini-grounded search
returns prose. No external search API key is required.

Usage: python3 collect-news.py <domain> <output-dir> [--company-name "Name"]
"""

import sys, os, json, requests, re
from datetime import date, timedelta
from email.utils import parsedate

TODAY = date.today().isoformat()
CUTOFF = (date.today() - timedelta(days=60)).isoformat()

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

def fetch_google_news(query):
    """Primary source: Google News RSS — keyless keyword search, returns dated items."""
    articles, err = [], None
    try:
        rss_url = f'https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en'
        r = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        if r.status_code != 200:
            return [], f'Google News RSS "{query[:40]}": HTTP {r.status_code}'
        items_xml = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
        for item_xml in items_xml[:10]:
            title_m = re.search(r'<title><!\[CDATA\[(.+?)\]\]>|<title>([^<]+)</title>', item_xml)
            link_m  = re.search(r'<link>([^<]+)</link>', item_xml)
            date_m  = re.search(r'<pubDate>([^<]+)</pubDate>', item_xml)
            title = (title_m.group(1) or title_m.group(2) or '').strip() if title_m else ''
            url   = (link_m.group(1) or '').strip() if link_m else 'n/a'
            pub_date = TODAY
            if date_m:
                parsed = parsedate(date_m.group(1))
                if parsed:
                    pub_date = f'{parsed[0]}-{parsed[1]:02d}-{parsed[2]:02d}'
            if pub_date >= CUTOFF and title:
                articles.append({'title': title, 'url': url, 'date': pub_date,
                                 'source': f'[FACT — Google News, {pub_date}]',
                                 'category': categorize(title, '')})
    except Exception as e:
        err = f'Google News RSS "{query[:40]}": {e}'
    return articles, err

def fetch_rss(domain):
    """Supplementary: company's own RSS/newsroom feeds."""
    articles = []
    for path in ['/press','/newsroom','/news','/blog']:
        try:
            r = requests.get(f'https://www.{domain}{path}',headers={'User-Agent':'Mozilla/5.0'},timeout=10)
            if r.status_code == 200 and len(r.text) > 500:
                headlines = re.findall(r'<title[^>]*><!\[CDATA\[([^\]]+)\]\]>|<title[^>]*>([^<]{20,150})</title>', r.text)
                for h in headlines[:5]:
                    title = (h[0] or h[1]).strip()
                    if title and domain.lower() not in title.lower()[:30]:
                        articles.append({'title':title,'url':f'https://www.{domain}{path}','date':TODAY,
                                         'source':f'[FACT — {domain} newsroom, {TODAY}]','category':categorize(title)})
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
        f'*Sources: Google News RSS (primary) + {company} newsroom feeds | Lookback: 60 days | keyless*',
        '',
        f'## Collection Summary',
        f'- Total articles: {len(articles)} | Lookback cutoff: {CUTOFF}',
        f'- Collection method: Google News RSS (keyword search) + company newsroom RSS',
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
            f'- {a.get("source","[OBSERVED — news search, " + TODAY + "]")}',
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
        f'*Sourcing: Google News RSS + company newsroom, {TODAY}*',
    ]
    if not articles:
        lines += [
            '',
            '> ⚠ **No articles found** in the last 60 days via Google News RSS or the company '
            'newsroom. This is a real null result — do not fabricate signals to fill it.',
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

    # Primary: Google News RSS (keyless keyword search, dated structured items).
    articles = []
    for q in queries:
        found, err = fetch_google_news(q)
        articles.extend(found)
        if err: errors.append(err)

    # Supplementary: the company's own newsroom/RSS feeds.
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
    print(json.dumps({'status':'success' if unique else 'partial','domain':domain,'company_name':company,
                      'output_file':out,'size_bytes':os.path.getsize(out),'total_articles':len(unique),
                      'collection_method':'google_news_rss','errors':errors},indent=2))

if __name__ == '__main__':
    main()
