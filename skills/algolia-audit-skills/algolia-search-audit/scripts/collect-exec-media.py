#!/usr/bin/env python3
"""
collect-exec-media.py — Phase 1: Executive Media Quote Collection (Tavily Signals)
Part of the Algolia Search Audit modular intelligence pipeline.

Reads from:  {output_dir}/01-company-context.json  (company_name, executives, primary_market)
Produces:    {output_dir}/11-investor-intelligence.json  (appends/updates media_quotes key)
             {output_dir}/11-investor-intelligence.md   (appends ## Media Quotes section)

Sources:
  1. Tavily advanced web search — per exec, trade press only, last 18 months
     Skips: sec.gov, fool.com, seekingalpha.com (earnings call sources, not media)
  2. Falls back to WebSearch if TAVILY_API_KEY not set (enrichment required flag set)

Data contract: Schema 1G additions — media_quotes[] in 11-investor-intelligence.json
  Collected fields: speaker, title, publication, source_url, source_date, source_type,
                    confidence, label, quote
  LLM-enriched fields (set to null here, filled by SKILL Step 3): context, algolia_relevance

Usage: python3 collect-exec-media.py <domain> <output-dir> [--company-name "Name"]
Env:   TAVILY_API_KEY
"""

import sys, os, json, re
sys.path.insert(0, os.path.dirname(__file__))
from platform_utils import (
    tavily_search, tavily_available, load_upstream,
    normalize_domain, build_summary, base_meta
)
from datetime import date, timedelta

TODAY = date.today().isoformat()
CUTOFF_DATE = (date.today() - timedelta(days=548)).isoformat()  # ~18 months

# Sources that are earnings/financial — skip these (not trade press)
SKIP_DOMAINS = [
    'sec.gov', 'fool.com', 'seekingalpha.com',
    'macrotrends.net', 'wsj.com/market-data', 'finance.yahoo.com',
    'marketwatch.com', 'nasdaq.com/market-activity',
]

# Exec titles to prioritize (in order)
PRIORITY_TITLES = ['CEO', 'CMO', 'CTO', 'CDO', 'CPO', 'President', 'COO', 'CFO']

# Max execs to query (avoids excessive Tavily credit usage)
MAX_EXECS = 3


def is_earnings_source(url):
    """Return True if the URL is a financial/earnings source we want to skip."""
    url_lower = url.lower()
    return any(skip in url_lower for skip in SKIP_DOMAINS)


def extract_publication(url):
    """Derive a human-readable publication name from a URL."""
    try:
        host = url.lower().split('/')[2].replace('www.', '')
        name_map = {
            'retaildive.com': 'Retail Dive',
            'businessinsider.com': 'Business Insider',
            'nrf.com': 'NRF',
            'forbes.com': 'Forbes',
            'fortune.com': 'Fortune',
            'wsj.com': 'Wall Street Journal',
            'nytimes.com': 'New York Times',
            'bloomberg.com': 'Bloomberg',
            'techcrunch.com': 'TechCrunch',
            'wwd.com': 'WWD',
            'fashionunited.com': 'FashionUnited',
            'chainstoreage.com': 'Chain Store Age',
            'digitalcommerce360.com': 'Digital Commerce 360',
            'progressivegrocer.com': 'Progressive Grocer',
            'grocerydive.com': 'Grocery Dive',
            'supplychaindive.com': 'Supply Chain Dive',
            'modernretail.co': 'Modern Retail',
            'pymnts.com': 'PYMNTS',
            'digiday.com': 'Digiday',
            'emarketer.com': 'eMarketer',
            'gartner.com': 'Gartner',
            'forrester.com': 'Forrester',
            'mckinsey.com': 'McKinsey',
            'hbr.org': 'Harvard Business Review',
            'inc.com': 'Inc.',
            'entrepreneur.com': 'Entrepreneur',
        }
        return name_map.get(host, host.split('.')[0].title())
    except Exception:
        return 'Trade Press'


def extract_quote_from_content(content, exec_name, snippet=''):
    """
    Extract the first verbatim sentence from raw_content that contains the exec name.
    Falls back to first 200 chars of snippet if raw_content is missing or no match.
    Returns (quote_text, confidence).
    """
    if content and exec_name:
        # Split on sentence boundaries, find first sentence with exec name
        sentences = re.split(r'(?<=[.!?])\s+', content)
        for sent in sentences:
            if exec_name.split()[-1] in sent:  # match on last name
                cleaned = sent.strip().strip('"').strip("'")
                if 20 < len(cleaned) < 600:
                    return cleaned, 'FACT'

    # Fall back to snippet
    if snippet:
        fallback = snippet[:200].strip()
        if exec_name.split()[-1] in fallback:
            return f'*said that* {fallback}', 'ESTIMATE'
        return fallback, 'ESTIMATE'

    return None, None


def parse_source_date(result):
    """Extract and normalize source_date from a Tavily result. Returns None if unparseable."""
    raw = result.get('published_date', '')
    if not raw:
        return None
    # Tavily returns ISO dates like "2025-03-15" or RFC-2822
    try:
        # Try ISO format first
        d = raw[:10]  # take first 10 chars: YYYY-MM-DD
        date.fromisoformat(d)  # validate
        return d
    except Exception:
        return None


def prioritize_execs(executives):
    """
    Sort executives list to put CEO/CMO/CTO/CDO/CPO first.
    Each exec is expected to be a dict with 'name' and 'title' keys,
    or a string name. Returns list of (name, title) tuples.
    """
    execs = []
    for ex in executives:
        if isinstance(ex, dict):
            name = ex.get('name', '')
            title = ex.get('title', '')
        elif isinstance(ex, str):
            name = ex
            title = ''
        else:
            continue
        if name:
            execs.append((name, title))

    def priority_score(ex):
        title_upper = ex[1].upper()
        for i, kw in enumerate(PRIORITY_TITLES):
            if kw in title_upper:
                return i
        return len(PRIORITY_TITLES)

    return sorted(execs, key=priority_score)[:MAX_EXECS]


def collect_media_quotes(company_name, executives, domain, errors):
    """
    For each prioritized exec, run a Tavily search and extract media quotes.
    Returns list of media_quote dicts per DATA-CONTRACT Schema 1G.
    """
    media_quotes = []
    sources_succeeded = []
    sources_failed = []

    if not tavily_available():
        errors.append('TAVILY_API_KEY not set — Tavily collection skipped')
        return media_quotes, sources_succeeded, sources_failed

    exec_list = prioritize_execs(executives)
    if not exec_list:
        errors.append('No executives found in 01-company-context.json — using generic company search')
        # Fallback: search for company in trade press without exec targeting
        exec_list = [(company_name, 'Leadership')]

    for exec_name, exec_title in exec_list:
        query = f'"{exec_name}" "{company_name}" interview OR quote OR said'
        try:
            results = tavily_search(
                query=query,
                topic='general',
                max_results=5,
                search_depth='advanced',
            )
        except Exception as e:
            err_msg = f'Tavily query for {exec_name}: {e}'
            errors.append(err_msg)
            sources_failed.append(f'tavily:{exec_name}')
            continue

        if not results:
            sources_failed.append(f'tavily:{exec_name}:no_results')
            continue

        sources_succeeded.append(f'tavily:{exec_name}')
        found_for_exec = 0

        for result in results:
            url = result.get('url', '')
            if not url:
                continue

            # Skip earnings/financial sources
            if is_earnings_source(url):
                continue

            # Check date within 18 months
            source_date = parse_source_date(result)
            if source_date and source_date < CUTOFF_DATE:
                continue  # too old

            # Use today as fallback date if unparseable
            if not source_date:
                source_date = TODAY

            raw_content = result.get('content', '')  # Tavily 'content' is extracted text
            snippet = result.get('content', '')[:300]

            quote_text, confidence = extract_quote_from_content(raw_content, exec_name, snippet)
            if not quote_text:
                continue

            publication = extract_publication(url)
            label = f'[{"FACT" if confidence == "FACT" else "ESTIMATE"} — {publication} via Tavily WebFetch, {source_date}, {url}]'

            entry = {
                'speaker': exec_name,
                'title': exec_title if exec_title else f'Executive, {company_name}',
                'quote': quote_text,
                'context': None,            # [COLLECT_VIA_SKILL] — LLM fills in Step 3
                'publication': publication,
                'source_url': url,
                'source_date': source_date,
                'source_type': 'media_interview',
                'confidence': confidence,
                'label': label,
                'algolia_relevance': None,  # [COLLECT_VIA_SKILL] — LLM fills in Step 3
            }
            media_quotes.append(entry)
            found_for_exec += 1

            # One entry per result per exec (no forced dedup — same exec in multiple outlets = multiple entries)

    return media_quotes, sources_succeeded, sources_failed


def update_json_file(output_dir, media_quotes, company_name, domain, errors,
                     sources_succeeded, sources_failed):
    """
    Read existing 11-investor-intelligence.json (if present), add/overwrite
    media_quotes key, and rewrite. If file missing, write minimal valid JSON
    with _meta + media_quotes only.
    Returns path to the JSON file.
    """
    json_path = os.path.join(output_dir, '11-investor-intelligence.json')
    skill_enrichment_required = []

    if not media_quotes:
        skill_enrichment_required.append('media_quotes')

    if os.path.exists(json_path):
        try:
            with open(json_path) as f:
                data = json.load(f)
        except Exception as e:
            errors.append(f'Could not read existing 11-investor-intelligence.json: {e}')
            data = {}
    else:
        # Minimal skeleton when the parent file doesn't exist yet
        meta_block = base_meta(
            module='investor-intelligence',
            module_id='1G',
            script='collect-exec-media.py',
            domain=domain,
            company_name=company_name,
            sources_succeeded=sources_succeeded,
            sources_failed=sources_failed,
            skill_enrichment_required=skill_enrichment_required,
        )
        # base_meta returns {'meta': {...}} — we store as '_meta' per DATA-CONTRACT
        data = {'_meta': meta_block['meta']}

    # Overwrite (or add) media_quotes key
    data['media_quotes'] = media_quotes

    # Update _meta if it exists (keep existing data intact)
    if '_meta' in data:
        data['_meta']['sources_succeeded'] = list(set(
            data['_meta'].get('sources_succeeded', []) + sources_succeeded
        ))
        data['_meta']['sources_failed'] = list(set(
            data['_meta'].get('sources_failed', []) + sources_failed
        ))
        if skill_enrichment_required:
            existing_ser = data['_meta'].get('skill_enrichment_required', [])
            for item in skill_enrichment_required:
                if item not in existing_ser:
                    existing_ser.append(item)
            data['_meta']['skill_enrichment_required'] = existing_ser

    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    return json_path


def update_md_file(output_dir, media_quotes, company_name):
    """
    Append (or replace) a ## Media Quotes (Trade Press) section in
    11-investor-intelligence.md. If the file doesn't exist, create it.
    Returns path to the MD file.
    """
    md_path = os.path.join(output_dir, '11-investor-intelligence.md')
    section_header = '## Media Quotes (Trade Press)'

    # Build the new section
    lines = [
        '',
        section_header,
        f'*Collected: {TODAY} via collect-exec-media.py | Source: Tavily advanced search*',
        f'*Lookback: 18 months | context + algolia_relevance: \\[COLLECT_VIA_SKILL\\]*',
        '',
    ]

    if not media_quotes:
        lines += [
            '*No media quotes collected — TAVILY_API_KEY not set or no qualifying results.*',
            '*Run Step 3 of algolia-intel-investor SKILL to collect via WebSearch fallback.*',
            '',
        ]
    else:
        for mq in media_quotes:
            speaker = mq.get('speaker', 'Unknown')
            title = mq.get('title', '')
            quote = mq.get('quote', '')
            publication = mq.get('publication', '')
            source_url = mq.get('source_url', '')
            source_date = mq.get('source_date', '')
            confidence = mq.get('confidence', 'ESTIMATE')
            label = mq.get('label', '')

            conf_badge = '[FACT]' if confidence == 'FACT' else '[ESTIMATE]'
            lines += [
                f'### {speaker} — {title}',
                f'> "{quote}"',
                f'',
                f'- **Publication:** {publication}',
                f'- **Date:** {source_date}',
                f'- **Source:** [{source_url}]({source_url})',
                f'- **Confidence:** {conf_badge}',
                f'- **Context (Algolia pitch):** `[COLLECT_VIA_SKILL]`',
                f'- **Algolia Relevance:** `[COLLECT_VIA_SKILL]`',
                f'- {label}',
                '',
            ]

    new_section = '\n'.join(lines)

    if os.path.exists(md_path):
        with open(md_path) as f:
            existing = f.read()
        # Replace existing section if present, else append
        if section_header in existing:
            # Find section start and next ## heading
            start = existing.index(section_header)
            # Find the next section after this one
            remainder = existing[start + len(section_header):]
            next_section = re.search(r'\n## ', remainder)
            if next_section:
                end = start + len(section_header) + next_section.start()
                updated = existing[:start] + new_section + existing[end:]
            else:
                updated = existing[:start] + new_section
        else:
            updated = existing.rstrip() + '\n' + new_section
        with open(md_path, 'w') as f:
            f.write(updated)
    else:
        # Create minimal MD file
        header = '\n'.join([
            f'# Investor & Executive Intelligence — {company_name}',
            f'*Generated: {TODAY} via collect-exec-media.py*',
            f'*Note: earnings call + 10-K sections populated by algolia-intel-investor SKILL Step 1-2*',
        ])
        with open(md_path, 'w') as f:
            f.write(header + new_section)

    return md_path


def main():
    if len(sys.argv) < 3:
        print(
            'Usage: collect-exec-media.py <domain> <output-dir> [--company-name "Name"]',
            file=sys.stderr
        )
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    # Parse optional flags: --company-name, --execs
    company_override = None
    execs_override = None  # comma-separated: "Doug Howe,Jared Poff"
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--company-name' and i + 1 < len(sys.argv):
            company_override = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--execs' and i + 1 < len(sys.argv):
            execs_override = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # Load upstream company context
    ctx = load_upstream(output_dir, '01-company-context.json')
    company_name = company_override or ctx.get('company_name') or domain

    # Build executives list: --execs flag > 01-company-context.json
    if execs_override:
        executives = [
            {'name': n.strip(), 'title': 'Executive'}
            for n in execs_override.split(',') if n.strip()
        ]
    else:
        executives = ctx.get('executives', [])

    if not ctx:
        # Graceful: no upstream file — derive company from domain, no exec targeting
        pass

    errors = []

    # Collect media quotes via Tavily
    media_quotes, sources_succeeded, sources_failed = collect_media_quotes(
        company_name, executives, domain, errors
    )

    # Determine skill enrichment required
    skill_enrichment_required = []
    if not tavily_available():
        skill_enrichment_required.append('media_quotes')
    elif not media_quotes:
        skill_enrichment_required.append('media_quotes')

    # Write/update output files
    json_path = update_json_file(
        output_dir, media_quotes, company_name, domain, errors,
        sources_succeeded, sources_failed
    )
    md_path = update_md_file(output_dir, media_quotes, company_name)

    # Print stdout JSON summary per DATA-CONTRACT §1.5
    summary = build_summary(
        module='investor-intelligence',
        script='collect-exec-media.py',
        domain=domain,
        company_name=company_name,
        output_md=md_path,
        output_json=json_path,
        sources_succeeded=sources_succeeded,
        sources_failed=sources_failed,
        skill_enrichment_required=skill_enrichment_required,
        errors=errors,
    )
    # Add media_quotes count to summary for caller convenience
    summary['media_quotes_collected'] = len(media_quotes)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
