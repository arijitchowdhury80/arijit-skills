#!/usr/bin/env python3
"""
collect-hiring.py — Layer 1H: ICP role classifier (v4.0)

Apify/LinkedIn scraping has been REMOVED (v3.0). Role *collection* is done by the
Claude agent via:
  - Layer 1: WebFetch on company careers page
  - Layer 2: WebSearch on job boards (ZipRecruiter, Indeed, company careers portal)

v4.0 WIRES the previously-dead deterministic classifier into the live pipeline.
Role *collection* stays with the agent (careers pages vary too much to script), but
role *tiering + ICP scoring + dedup* is now DETERMINISTIC code, not LLM keyword-guessing.

Flow:
  1. Agent collects roles via WebFetch/WebSearch and writes them to a roles JSON
     (list of {title, desc, url, location, layer, job_id, source}).
  2. This script reads that JSON, dedups across Layer 1 + Layer 2, and assigns
     tier (1 Economic / 2 Technical / 3 Champion / 4 Context) + ICP score 0–10
     deterministically via classify().
  3. Output: classified roles JSON + tier_summary + buying_committee scaffold.

ICP Tier Definitions:
  Tier 1 — Economic Buyer: VP/SVP/Director Digital, Ecommerce, Commerce, DTC, NDDC, CDO, Head of Digital
  Tier 2 — Technical Buyer: Search Engineer, Platform Engineer, Lead/Sr SWE (ecommerce/search/platform),
            Solutions Architect (commerce), Engineering Manager (ecommerce/platform)
  Tier 3 — Champion: Product Manager (Digital/Ecommerce/Search), UX/Product Designer (digital),
            CRO Manager, Personalization Manager, Digital Analytics Lead
  Tier 4 — Context: Operations, logistics, design, admin, retail, supply chain

Score modifiers: +1 per HIGH ICP keyword, +0.5 per MED keyword in description.

Usage:
  python3 collect-hiring.py <roles_json> <output_dir> [--company-name "Name"]
    <roles_json> : path to a JSON file (or "-" for stdin) holding a list of role dicts.
  python3 collect-hiring.py --reference   # print tier definitions only
"""

import re
import sys
import os
import json
from datetime import date

TODAY = date.today().isoformat()

TIER_NAMES = {
    1: "Economic Buyer",
    2: "Technical Buyer",
    3: "Champion",
    4: "Context",
}

TIER_1 = [
    r'VP.*(digital|ecommerce|e-commerce|product|commerce|direct)',
    r'SVP.*(digital|ecommerce|e-commerce|product|commerce|direct|experience)',
    r'Director.*(digital|ecommerce|e-commerce|product|commerce|direct|NDDC)',
    r'Head of.*(digital|ecommerce|commerce|product|direct)',
    r'Chief Digital Officer', r'\bCDO\b',
    r'(Senior|Sr\.?)\s+Director.*(digital|ecommerce|commerce|direct|product)',
    r'Director.*(Nike Direct|NDDC|D2C|DTC)',
    r'GM.*(digital|ecommerce|commerce)',
]
TIER_2 = [
    r'(Senior|Sr\.?|Staff|Principal|Lead).*(Engineer|Developer|Architect).*(ecommerce|search|platform|commerce|digital)',
    r'Search (Engineer|Architect|Developer|Relevance|Platform)',
    r'(Engineer|Developer|Architect).*(search|ecommerce|commerce|platform)',
    r'Solutions Architect.*(ecommerce|commerce|SFCC|Shopify|digital)',
    r'Technical Lead.*(SFCC|headless|composable|commerce|digital)',
    r'Platform Engineer',
    r'Software Engineer.*(ecommerce|commerce|platform|search)',
    r'(Senior|Sr\.?|Lead|Principal) Software Engineer',
    r'Engineering Manager.*(ecommerce|commerce|platform|digital|search)',
]
TIER_3 = [
    r'Product Manager.*(digital|ecommerce|e-commerce|search|platform|commerce|direct)',
    r'(Senior|Sr\.?|Lead|Principal)\s+Product Manager',
    r'(Head|Director|Manager).*(merchandising|performance marketing|growth|CRO|analytics|conversion)',
    r'(Conversion Rate|CRO).*(Manager|Analyst|Specialist)',
    r'(Head|Director|Manager).*(personalization|customer data|customer experience)',
    r'Digital Analytics', r'SEO.*(Manager|Director|Lead)',
    r'(Manager|Director|Lead).*(ecommerce|digital|commerce|product)',
    r'(UX|Product|Experience) Designer.*(digital|ecommerce|commerce)',
]

HIGH_KW = ['search', 'search relevance', 'NLP', 'natural language', 'personalization',
           'recommendation engine', 'product discovery', 'Algolia', 'Elasticsearch',
           'composable commerce', 'headless commerce', 'AI-powered search',
           'autocomplete', 'faceted search', 'typeahead']
MED_KW  = ['conversion rate', 'A/B testing', 'catalog management',
           'merchandising rules', 'ecommerce', 'product discovery', 'site search']


def classify(title, desc=''):
    text = (title + ' ' + desc).lower()
    hi = [k for k in HIGH_KW if k.lower() in text]
    md = [k for k in MED_KW if k.lower() in text]
    for t, patterns, base in [(1, TIER_1, 9), (2, TIER_2, 7), (3, TIER_3, 5)]:
        for p in patterns:
            if re.search(p, title, re.I):
                return t, min(base + len(hi) * 1 + len(md) * 0.5, 10), hi + md
    return 4, min(2 + len(hi), 10), hi + md


def _dedup_key(role):
    """Stable identity for a role: prefer job_id, else normalized title+location."""
    job_id = (role.get('job_id') or '').strip().lower()
    if job_id:
        return ('id', job_id)
    title = re.sub(r'\s+', ' ', (role.get('title') or '').strip().lower())
    location = re.sub(r'\s+', ' ', (role.get('location') or '').strip().lower())
    return ('title', title, location)


def classify_roles(roles):
    """
    Deterministically classify a list of collected roles.

    Each input role: {title, desc?, url?, location?, layer?, job_id?, source?}
    Dedup is applied ACROSS layers (Layer 1 careers page + Layer 2 job boards):
    a role seen in both layers is kept once, with merged layer provenance and the
    richer description (longer wins, so ICP keyword scoring isn't starved).

    Returns: {classified[], tier_summary{}, deduped_count, input_count}
    """
    by_key = {}
    order = []
    for role in roles:
        title = (role.get('title') or '').strip()
        if not title:
            continue
        key = _dedup_key(role)
        if key not in by_key:
            by_key[key] = dict(role)
            by_key[key]['_layers'] = set()
            order.append(key)
        merged = by_key[key]
        # Track every layer this role was seen in (dedup provenance).
        layer = role.get('layer')
        if layer is not None:
            merged['_layers'].add(layer)
        # Keep the richer (longer) description for scoring.
        if len(role.get('desc') or '') > len(merged.get('desc') or ''):
            merged['desc'] = role.get('desc')
        # Backfill url/location/source/job_id if missing.
        for f in ('url', 'location', 'source', 'job_id'):
            if not merged.get(f) and role.get(f):
                merged[f] = role.get(f)

    classified = []
    tier_summary = {'tier1': 0, 'tier2': 0, 'tier3': 0, 'tier4': 0}
    for key in order:
        role = by_key[key]
        tier, score, kws = classify(role.get('title', ''), role.get('desc', '') or '')
        layers = sorted(role.pop('_layers', set()))
        out = {
            'title': role.get('title'),
            'desc': role.get('desc', ''),
            'url': role.get('url'),
            'location': role.get('location'),
            'job_id': role.get('job_id'),
            'source': role.get('source'),
            'tier': tier,
            'tier_name': TIER_NAMES[tier],
            'icp_score': round(score, 1),
            'icp_keywords': kws,
            'seen_in_layers': layers,
            'dedup_collapsed': len(layers) > 1,
            'classification_method': 'deterministic_regex_tier+icp_keyword_score',
            'label': f'[OBSERVED — collect-hiring.classify, {TODAY}]',
        }
        classified.append(out)
        tier_summary[f'tier{tier}'] += 1

    # Highest ICP score first, then tier.
    classified.sort(key=lambda r: (-r['icp_score'], r['tier']))
    return {
        'classified': classified,
        'tier_summary': tier_summary,
        'input_count': len(roles),
        'deduped_count': len(classified),
    }


def _load_roles(path):
    if path == '-':
        raw = sys.stdin.read()
    else:
        with open(path) as f:
            raw = f.read()
    data = json.loads(raw)
    # Accept either a bare list or {roles: [...]}.
    if isinstance(data, dict):
        data = data.get('roles', [])
    if not isinstance(data, list):
        raise ValueError('roles JSON must be a list (or {"roles": [...]})')
    return data


def main():
    if '--reference' in sys.argv or len(sys.argv) < 2:
        print("collect-hiring.py v4.0 — deterministic ICP role classifier.")
        print("Tier 1 Economic / Tier 2 Technical / Tier 3 Champion / Tier 4 Context.")
        print("Usage: collect-hiring.py <roles_json|-> <output_dir> [--company-name NAME]")
        print("Role COLLECTION stays with the agent (WebFetch/WebSearch); this script")
        print("does deterministic tier + ICP scoring + cross-layer dedup.")
        return

    roles_json = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    os.makedirs(output_dir, exist_ok=True)

    company = None
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--company-name' and i + 1 < len(sys.argv):
            company = sys.argv[i + 1]; i += 2
        else:
            i += 1

    roles = _load_roles(roles_json)
    result = classify_roles(roles)
    result['meta'] = {
        'company_name': company,
        'classified_at': TODAY,
        'classification_script': 'collect-hiring.py v4.0',
        'collection_method': 'agent_webfetch_websearch+deterministic_classify',
    }

    out = os.path.join(output_dir, '09d-hiring-classified.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)

    print(json.dumps({
        'status': 'success',
        'output_json': out,
        'input_count': result['input_count'],
        'deduped_count': result['deduped_count'],
        'tier_summary': result['tier_summary'],
    }, indent=2))


if __name__ == '__main__':
    main()
