#!/usr/bin/env python3
"""
collect-hiring.py — Phase 1: Hiring Signals Collection
Part of the Algolia Search Audit modular intelligence pipeline.

Reads from:  {output_dir}/01-company-context.json  (company_name, linkedin_url, domain)
Produces:    {output_dir}/09d-hiring-signals.md

Sources (ALL attempted — not fallback):
  1. Apify LinkedIn Jobs scraper (requires APIFY_TOKEN)
  2. Company careers page WebFetch: /careers, /jobs
  3. Indeed WebSearch stub (actual search via skill MCP)

Usage: python3 collect-hiring.py <domain> <output-dir> [--company-name "Name"]
Env:   APIFY_TOKEN
"""

import sys, os, json, requests, re, time
from datetime import date

TODAY = date.today().isoformat()
APIFY_TOKEN = os.environ.get('APIFY_TOKEN', '')
APIFY_BASE = 'https://api.apify.com/v2'

# ── ICP Role Classification ─────────────────────────────────────────────────

TIER_1 = [
    r'VP.*(digital|ecommerce|e-commerce|product|digital transformation)',
    r'Director.*(digital|ecommerce|e-commerce|product)',
    r'Head of.*(digital|ecommerce|commerce|digital products)',
    r'Chief Digital Officer', r'\bCDO\b', r'SVP.*(digital|experience)',
]
TIER_2 = [
    r'(Senior|Staff|Principal|Lead).*(Engineer|Developer|Architect).*(ecommerce|search|platform|backend)',
    r'Search (Engineer|Architect|Developer|Relevance)',
    r'Solutions Architect.*(ecommerce|commerce|SFCC|Shopify)',
    r'Technical Lead.*(SFCC|headless|composable|commerce)',
    r'Platform Engineer',
]
TIER_3 = [
    r'(Head|Director|Manager).*(merchandising|performance marketing|growth|CRO|analytics)',
    r'(Conversion Rate|CRO) (Manager|Analyst)',
    r'(Head|Director|Manager).*(personalization|customer data)',
    r'Digital Analytics', r'SEO.*(Manager|Director)',
]

HIGH_KW = ['search','search relevance','NLP','natural language','personalization',
           'recommendation engine','product discovery','Algolia','Elasticsearch',
           'composable commerce','headless commerce','AI-powered search']
MED_KW  = ['conversion rate','A/B testing','experimentation','catalog management',
           'merchandising rules','faceted search','typeahead','autocomplete']

def classify(title, desc=''):
    text = (title + ' ' + desc).lower()
    hi = [k for k in HIGH_KW if k.lower() in text]
    md = [k for k in MED_KW  if k.lower() in text]
    for t, patterns, base in [(1,TIER_1,9),(2,TIER_2,7),(3,TIER_3,5)]:
        for p in patterns:
            if re.search(p, title, re.I):
                return t, min(base + len(hi)*1 + len(md)*0.5, 10), hi+md
    return 4, min(2 + len(hi), 10), hi+md

# ── Apify ────────────────────────────────────────────────────────────────────

def apify_run(actor_id, input_data, max_wait=120):
    if not APIFY_TOKEN:
        return None, 'APIFY_TOKEN not set'
    try:
        r = requests.post(f'{APIFY_BASE}/acts/{actor_id}/runs?token={APIFY_TOKEN}',
                          json=input_data, timeout=30)
        r.raise_for_status()
        run_id = r.json()['data']['id']
    except Exception as e:
        return None, str(e)
    elapsed = 0
    status = 'RUNNING'
    while elapsed < max_wait and status not in ('SUCCEEDED','FAILED','ABORTED'):
        time.sleep(5); elapsed += 5
        try:
            status = requests.get(f'{APIFY_BASE}/actor-runs/{run_id}?token={APIFY_TOKEN}',
                                  timeout=10).json()['data']['status']
        except Exception:
            pass
    if status != 'SUCCEEDED':
        return None, f'Actor status: {status}'
    try:
        ir = requests.get(f'{APIFY_BASE}/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}&clean=true',
                          timeout=30)
        ir.raise_for_status()
        return ir.json(), None
    except Exception as e:
        return None, str(e)

# ── Careers page ─────────────────────────────────────────────────────────────

def fetch_careers(domain):
    for path in ['/careers','/jobs','/work-with-us','/job-openings']:
        try:
            r = requests.get(f'https://www.{domain}{path}',
                             headers={'User-Agent':'Mozilla/5.0'},
                             timeout=15, allow_redirects=True)
            if r.status_code == 200 and len(r.text) > 1000:
                titles = re.findall(r'<h[23][^>]*>([^<]{15,80})</h[23]>', r.text)
                jobs = [{'title':t.strip(),'url':f'https://www.{domain}{path}',
                         'source_label':f'[FACT — careers page WebFetch, {TODAY}]'}
                        for t in titles[:20] if t.strip()]
                if jobs:
                    return jobs, f'https://www.{domain}{path}', None
        except Exception:
            continue
    return [], None, 'no accessible careers page'

# ── Load upstream context ─────────────────────────────────────────────────────

def load_ctx(output_dir):
    p = os.path.join(output_dir, '01-company-context.json')
    return json.load(open(p)) if os.path.exists(p) else {}

# ── Write output ──────────────────────────────────────────────────────────────

def write_md(domain, company, classified, careers_url, errors, output_dir):
    t1 = [j for j in classified if j['tier']==1 and j['score']>=7]
    t2 = [j for j in classified if j['tier']==2 and j['score']>=7]
    t3 = [j for j in classified if j['tier']==3]
    t4 = [j for j in classified if j['tier']==4]

    lines = [
        f'# Hiring Signals — {company}',
        f'*Generated: {TODAY} via collect-hiring.py*',
        '',
        '## Collection Summary',
        f'- Total jobs: {len(classified)} | ICP roles (Tier 1-3): {len(t1)+len(t2)+len(t3)}',
        f'- Vacancy signals (score ≥7): {len(t1)+len(t2)}',
        f'- Careers page: {careers_url or "not found"}',
        '',
        '## 🔴 Critical Vacancy Signals (Tier 1-2, score ≥7)',
    ]
    for j in t1+t2:
        lines += [
            f'### {j["title"]}',
            f'- Tier: {j["tier"]} | Score: {j["score"]:.1f}/10',
            f'- URL: {j.get("url","n/a")}',
            f'- Keywords: {", ".join(j.get("keywords",[]))}',
            f'- {j.get("source_label","[FACT — LinkedIn Jobs via Apify, "+TODAY+"]")}',
            '',
        ]
    if not (t1+t2): lines += ['*None found*','']

    lines += ['## 🟡 Champion Signals (Tier 3)']
    for j in t3[:10]: lines += [f'- {j["title"]} ({j.get("url","n/a")})']
    if not t3: lines += ['*None found*']

    lines += [
        '', f'## 🟢 Context Roles (Tier 4): {len(t4)} total',
        '',
        '## Buying Committee Assessment',
        f'- Economic Buyer (Tier 1): {"VACANT" if t1 else "not in current postings"}',
        f'- Technical Buyer (Tier 2): {"VACANT" if t2 else "not in current postings"}',
        f'- Champion roles: {len(t3)}',
        '',
        '## ICP Summary',
        '| Tier | Count | Signal |',
        '|------|-------|--------|',
        f'| 1 — Economic Buyer | {len(t1)} | {"🔴 VACANCY" if t1 else "⚫"} |',
        f'| 2 — Technical Buyer | {len(t2)} | {"🔴 VACANCY" if t2 else "⚫"} |',
        f'| 3 — Champion | {len(t3)} | {"🟡" if t3 else "⚫"} |',
        '',
        f'[FACT — LinkedIn Jobs via Apify (curious_coder/linkedin-jobs-scraper), {TODAY}]',
    ]
    if errors: lines += ['','## Errors'] + [f'- {e}' for e in errors]

    out = os.path.join(output_dir, '09d-hiring-signals.md')
    open(out,'w').write('\n'.join(lines))
    return out

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print('Usage: collect-hiring.py <domain> <output-dir> [--company-name "Name"]', file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1].lower().replace('https://','').replace('http://','').replace('www.','').split('/')[0]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    override = None
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--company-name' and i+1 < len(sys.argv): override = sys.argv[i+1]; i+=2
        else: i+=1

    ctx = load_ctx(output_dir)
    company = override or ctx.get('company_name') or domain
    linkedin_url = ctx.get('linkedin_url')

    print(f'Collecting hiring signals for {company}...', file=sys.stderr)
    errors = []

    # Source 1: Apify LinkedIn Jobs
    raw, err = apify_run('curious_coder/linkedin-jobs-scraper', {
        'searchTerms':[company], 'location':'', 'limit':50, 'datePosted':'past-3-months',
        **({'companyUrls':[linkedin_url]} if linkedin_url else {})
    })
    if err: errors.append(f'LinkedIn Jobs (Apify): {err}')
    raw = raw or []

    # Source 2: Careers page
    careers_jobs, careers_url, cp_err = fetch_careers(domain)
    if cp_err: errors.append(f'Careers page: {cp_err}')

    all_raw = []
    for j in raw:
        all_raw.append({'title':j.get('title',j.get('jobTitle','')),'url':j.get('jobUrl',j.get('url','')),'description':j.get('description',''),'source_label':f'[FACT — LinkedIn Jobs via Apify, {TODAY}]'})
    for j in careers_jobs:
        all_raw.append({**j,'description':''})

    classified = []
    for j in all_raw:
        tier, score, kw = classify(j['title'], j.get('description',''))
        classified.append({**j,'tier':tier,'score':score,'keywords':kw})
    classified.sort(key=lambda x: x['score'], reverse=True)

    out = write_md(domain, company, classified, careers_url, errors, output_dir)
    print(json.dumps({'status':'success' if raw or careers_jobs else 'partial','domain':domain,'company_name':company,'output_file':out,'size_bytes':os.path.getsize(out),'total_jobs':len(classified),'icp_roles':len([j for j in classified if j['tier']<=3]),'vacancy_signals':len([j for j in classified if j['tier']<=2 and j['score']>=7]),'errors':errors},indent=2))

if __name__ == '__main__':
    main()
