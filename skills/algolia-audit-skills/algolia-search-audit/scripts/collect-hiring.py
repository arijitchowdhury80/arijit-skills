#!/usr/bin/env python3
"""
collect-hiring.py — Layer 1H: ICP Classification Reference (v3.0)

Apify/LinkedIn scraping has been REMOVED (v3.0).
Data collection is now done entirely by the Claude agent via:
  - Layer 1: WebFetch on company careers page
  - Layer 2: WebSearch on job boards (ZipRecruiter, Indeed, company careers portal)

This script is retained as an ICP classification reference.
The tier patterns below define what constitutes Tier 1/2/3 roles.
Agents use these definitions when classifying roles found via WebFetch/WebSearch.

ICP Tier Definitions:
  Tier 1 — Economic Buyer: VP/SVP/Director Digital, Ecommerce, Commerce, DTC, NDDC, CDO, Head of Digital
  Tier 2 — Technical Buyer: Search Engineer, Platform Engineer, Lead/Sr SWE (ecommerce/search/platform),
            Solutions Architect (commerce), Engineering Manager (ecommerce/platform)
  Tier 3 — Champion: Product Manager (Digital/Ecommerce/Search), UX/Product Designer (digital),
            CRO Manager, Personalization Manager, Digital Analytics Lead
  Tier 4 — Context: Operations, logistics, design, admin, retail, supply chain

Score modifiers: +1 per ICP keyword in description
ICP keywords: search, NLP, personalization, ecommerce, product discovery, Algolia,
              Elasticsearch, composable commerce, headless commerce, autocomplete, faceted search
"""

import re

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


if __name__ == '__main__':
    print("collect-hiring.py v3.0 — ICP classification reference only.")
    print("Data collection moved to agent WebFetch/WebSearch layers.")
    print("See algolia-intel-hiring/SKILL.md for current module instructions.")
