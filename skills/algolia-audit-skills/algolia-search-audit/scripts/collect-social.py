#!/usr/bin/env python3
"""
collect-social.py — Phase 1: Social Signals Collection
Part of the Algolia Search Audit modular intelligence pipeline.

Reads from:  {output_dir}/01-company-context.json  (company_name, linkedin_url, twitter_handle)
Produces:    {output_dir}/09b-social-signals.md

Sources (ALL attempted — not fallback):
  1. Apify: harvestapi/linkedin-company-posts (requires APIFY_TOKEN)
  2. Apify: apidojo/tweet-scraper (requires APIFY_TOKEN)
  Known issue: LinkedIn posts actor may return 0 for some companies — document and continue.

Usage: python3 collect-social.py <domain> <output-dir> [--company-name "Name"]
Env:   APIFY_TOKEN
"""

import sys, os, json, requests, re, time
from datetime import date, timedelta

TODAY = date.today().isoformat()
CUTOFF = (date.today() - timedelta(days=30)).isoformat()
APIFY_TOKEN = os.environ.get('APIFY_TOKEN', '')
APIFY_BASE = 'https://api.apify.com/v2'

SIGNAL_CATEGORIES = {
    'SEARCH_PAIN': ['search','product discovery','findability','find product','search result'],
    'TECH_INVESTMENT': ['AI','machine learning','platform','modernization','tech','digital transformation','migration'],
    'INTERNATIONAL': ['international','global','expansion','new market','multi-language','cross-border'],
    'CONVERSION_FOCUS': ['conversion','AOV','revenue per','checkout','abandon'],
    'CX_INITIATIVE': ['customer experience','CX','UX','personalization','customer journey'],
    'EXEC_PRIORITY': [],  # Set for exec posts
    'PRODUCT_LAUNCH': ['launch','new product','new line','introducing','collection'],
    'COMPETITOR_SIGNAL': ['compete','market share','ahead of','leading'],
}

def score_post(text, is_exec=False):
    text_lower = text.lower()
    high = ['search','personalization','NLP','product discovery','conversion rate','recommendation']
    if any(k in text_lower for k in high): return 9, 'SEARCH_PAIN' if 'search' in text_lower else 'CX_INITIATIVE'
    for cat, kws in SIGNAL_CATEGORIES.items():
        if kws and any(k in text_lower for k in kws):
            return (8 if is_exec else 7), cat
    if is_exec: return 6, 'EXEC_PRIORITY'
    return 3, 'GENERAL'

def apify_run(actor_id, input_data, max_wait=90):
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

def load_ctx(output_dir):
    p = os.path.join(output_dir,'01-company-context.json')
    return json.load(open(p)) if os.path.exists(p) else {}

def write_md(company, signals, li_count, tw_count, errors, output_dir):
    qualifying = [s for s in signals if s['score'] >= 6]
    direct = [s for s in qualifying if s['score'] >= 9]
    strong = [s for s in qualifying if 7 <= s['score'] <= 8]
    context = [s for s in qualifying if s['score'] == 6]

    lines = [
        f'# Social Signals — {company}',
        f'*Generated: {TODAY} via collect-social.py*',
        f'*Sources: LinkedIn Company Posts + Twitter/X via Apify*',
        '',
        '## Collection Summary',
        f'- LinkedIn posts scraped: {li_count} | Twitter/X scraped: {tw_count}',
        f'- Qualifying signals (score ≥6): {len(qualifying)}',
        f'- Lookback: 30 days',
        '',
        '## 🔴 Direct Algolia Signals (Score 9-10)',
    ]
    for s in direct:
        lines += [
            f'**{s.get("platform","Social")} — {s.get("date",TODAY)}**',
            f'- Author: {s.get("author","company post")}',
            f'- Post: "{s.get("text","")[:200]}"',
            f'- Engagement: {s.get("reactions",0)} reactions · {s.get("comments",0)} comments',
            f'- Signal: {s["category"]} — {s.get("signal_note","")}',
            f'- URL: {s.get("url","n/a")}',
            f'- [FACT — Apify {s.get("platform","Social")}, {TODAY}]',
            '',
        ]
    if not direct: lines += ['*None found*','']

    lines += ['## 🟡 Strong Signals (Score 7-8)']
    for s in strong:
        lines += [f'- **{s.get("platform")} {s.get("date","")}**: "{s.get("text","")[:150]}" [{s["category"]}] — {s.get("url","n/a")}']
    if not strong: lines += ['*None found*']

    lines += ['','## 🟢 Context Signals (Score 6)']
    for s in context:
        lines += [f'- {s.get("text","")[:100]} [{s["category"]}]']
    if not context: lines += ['*None found*']

    lines += [
        '',
        '## Pattern Analysis (30-day themes)',
        '*(Populated by algolia-intel-social SKILL via pattern synthesis)*',
        '',
        '## Platform Notes',
        f'- LinkedIn: {li_count} posts scraped, {len([s for s in qualifying if s.get("platform")=="LinkedIn"])} qualifying',
        f'- Twitter/X: {tw_count} posts scraped, {len([s for s in qualifying if s.get("platform")=="Twitter"])} qualifying',
        '',
        f'[FACT — Apify harvestapi/linkedin-company-posts + apidojo/tweet-scraper, {TODAY}]',
    ]
    if errors: lines += ['','## Collection Errors'] + [f'- {e}' for e in errors]

    out = os.path.join(output_dir, '09b-social-signals.md')
    open(out,'w').write('\n'.join(lines))
    return out

def main():
    if len(sys.argv) < 3:
        print('Usage: collect-social.py <domain> <output-dir> [--company-name "Name"]', file=sys.stderr)
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
    linkedin_url = ctx.get('linkedin_url') or f'https://www.linkedin.com/company/{domain.replace(".com","")}'
    twitter_handle = ctx.get('twitter_handle') or f'@{domain.replace(".com","").replace(".","")}'

    errors = []

    # Source 1: LinkedIn posts
    li_posts, li_err = apify_run('harvestapi~linkedin-company-posts', {'url':linkedin_url,'maxPosts':30,'includeComments':False,'includeReactions':False})
    if li_err: errors.append(f'LinkedIn posts (Apify): {li_err}')
    li_posts = li_posts or []

    # Source 2: Twitter/X
    tw_posts, tw_err = apify_run('apidojo~tweet-scraper', {'searchTerms':[f'from:{twitter_handle}'],'maxTweets':30,'since':CUTOFF})
    if tw_err: errors.append(f'Twitter/X (Apify): {tw_err}')
    tw_posts = tw_posts or []

    signals = []
    for p in li_posts:
        text = p.get('text',p.get('content',''))[:500]
        if not text: continue
        score, cat = score_post(text)
        if score >= 4:
            signals.append({'platform':'LinkedIn','text':text,'date':p.get('publishedAt',TODAY)[:10],'author':p.get('authorName','company'),'reactions':p.get('numLikes',0),'comments':p.get('numComments',0),'url':p.get('url','n/a'),'score':score,'category':cat,'signal_note':f'{cat} signal from LinkedIn post'})

    for p in tw_posts:
        text = p.get('text',p.get('fullText',''))[:500]
        if not text: continue
        score, cat = score_post(text)
        if score >= 4:
            signals.append({'platform':'Twitter','text':text,'date':p.get('createdAt',TODAY)[:10],'author':twitter_handle,'reactions':p.get('likeCount',0),'comments':p.get('replyCount',0),'url':p.get('url','n/a'),'score':score,'category':cat,'signal_note':f'{cat} signal from Twitter post'})

    signals.sort(key=lambda x: x['score'], reverse=True)
    out = write_md(company, signals, len(li_posts), len(tw_posts), errors, output_dir)
    print(json.dumps({'status':'success' if li_posts or tw_posts else 'partial','domain':domain,'company_name':company,'output_file':out,'size_bytes':os.path.getsize(out),'qualifying_signals':len([s for s in signals if s['score']>=6]),'errors':errors},indent=2))

if __name__ == '__main__':
    main()
