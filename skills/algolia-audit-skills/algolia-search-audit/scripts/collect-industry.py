#!/usr/bin/env python3
"""
collect-industry.py — Phase 1: Industry & Vertical Signals Collection (Tavily Signals)
Part of the Algolia Search Audit modular intelligence pipeline.

Reads from:  {output_dir}/01-company-context.json  (vertical, primary_market, company_name)
Produces:    {output_dir}/industry-intel.md
             {output_dir}/industry-intel.json

Sources:
  1. Tavily advanced web search — 3 targeted queries per locale (benchmarks, trends, expert quotes)
     Staleness: source_date within 24 months of collected_at — older results excluded
  2. Falls back to websearch_fallback mode when TAVILY_API_KEY not set
     (skill_enrichment_required flags set — SKILL LLM fills missing fields)

Data contract: Schema 1L additions — industry-intel.json
  benchmarks[]:     metric, value, context, source_name, source_url, source_date,
                    source_type, confidence, age_months, verified, label
  trends_2025_2026[]: title, description, source_url, source_date, source_type,
                      confidence, age_months, label
  expert_quotes[]:  quote, speaker, organization, source_url, source_date,
                    source_type, confidence, label
  LLM-enriched fields (set to null here): algolia_angle, competitor_search_landscape
  Note: algolia_angle left as null with [COLLECT_VIA_SKILL] marker — filled by SKILL Step 2

Usage: python3 collect-industry.py <domain> <output-dir> [--company-name "Name"] [--vertical "footwear-retail"]
Env:   TAVILY_API_KEY
"""

import sys, os, json, re, math
sys.path.insert(0, os.path.dirname(__file__))
from platform_utils import (
    tavily_search, tavily_available, load_upstream,
    normalize_domain, build_summary, base_meta
)
from datetime import date, timedelta

TODAY = date.today().isoformat()
TODAY_DATE = date.today()

# Staleness cutoff: 24 months
STALE_MONTHS = 24


# ── Locale-based query templates ──────────────────────────────────────────────

BENCHMARK_QUERIES = {
    'US': '{vertical} ecommerce search conversion benchmark 2025 site:nrf.com OR site:baymard.com OR site:forrester.com',
    'UK': 'UK {vertical} ecommerce search benchmark 2025 site:econsultancy.com OR site:imrg.org OR site:baymard.com',
    'EU': 'Europe {vertical} ecommerce search personalization benchmark 2025 site:forrester.com OR site:econsultancy.com',
    'CA': '{vertical} ecommerce search conversion benchmark 2025 site:nrf.com OR site:baymard.com OR site:forrester.com',
    'AU': '{vertical} ecommerce search conversion benchmark 2025 site:nrf.com OR site:baymard.com OR site:forrester.com',
}

TREND_QUERIES = {
    'US': '{vertical} ecommerce AI search personalization technology trends 2025 2026',
    'UK': 'UK {vertical} ecommerce search AI personalization investment trends 2025 2026',
    'EU': 'Europe {vertical} ecommerce search personalization AI 2025 2026 investment',
    'CA': '{vertical} ecommerce AI search personalization technology trends 2025 2026',
    'AU': '{vertical} ecommerce AI search personalization technology trends 2025 2026',
}

EXPERT_QUOTE_QUERIES = {
    'US': '{vertical} ecommerce search expert analyst quote 2025 site:nrf.com OR site:baymard.com OR site:forrester.com OR site:gartner.com',
    'UK': 'UK {vertical} ecommerce search analyst expert opinion quote 2025 site:econsultancy.com OR site:imrg.org',
    'EU': 'Europe {vertical} ecommerce search expert analyst quote 2025 site:econsultancy.com OR site:forrester.com',
    'CA': '{vertical} ecommerce search expert analyst quote 2025 site:nrf.com OR site:baymard.com OR site:forrester.com',
    'AU': '{vertical} ecommerce search expert analyst quote 2025 site:nrf.com OR site:baymard.com OR site:forrester.com',
}

# ── Source classification ─────────────────────────────────────────────────────

RESEARCH_FIRM_DOMAINS = [
    'baymard.com', 'forrester.com', 'gartner.com', 'mckinsey.com',
    'nrf.com', 'emarketer.com', 'nngroup.com', 'econsultancy.com',
    'imrg.org', 'digitalcommerce360.com', 'shopify.com/enterprise',
    'hbr.org', 'bcg.com', 'deloitte.com', 'pwc.com', 'accenture.com',
]

SOURCE_NAME_MAP = {
    'baymard.com': 'Baymard Institute',
    'forrester.com': 'Forrester',
    'gartner.com': 'Gartner',
    'mckinsey.com': 'McKinsey',
    'nrf.com': 'NRF',
    'emarketer.com': 'eMarketer',
    'nngroup.com': 'Nielsen Norman Group',
    'econsultancy.com': 'Econsultancy',
    'imrg.org': 'IMRG',
    'digitalcommerce360.com': 'Digital Commerce 360',
    'hbr.org': 'Harvard Business Review',
    'retaildive.com': 'Retail Dive',
    'modernretail.co': 'Modern Retail',
    'chainstoreage.com': 'Chain Store Age',
    'progressivegrocer.com': 'Progressive Grocer',
    'wwd.com': 'WWD',
    'fashionunited.com': 'FashionUnited',
    'businessinsider.com': 'Business Insider',
    'forbes.com': 'Forbes',
    'bloomberg.com': 'Bloomberg',
}


def classify_source(url):
    """Classify source_type and source_name from URL."""
    url_lower = url.lower()
    for dom in RESEARCH_FIRM_DOMAINS:
        if dom in url_lower:
            name = SOURCE_NAME_MAP.get(dom, dom.split('.')[0].title())
            return 'industry_report', name
    # Fall through to trade press
    try:
        host = url_lower.split('/')[2].replace('www.', '')
        name = SOURCE_NAME_MAP.get(host, host.split('.')[0].title())
    except Exception:
        name = 'Trade Press'
    return 'news_article', name


def parse_source_date(result):
    """Extract and normalize source_date from a Tavily result. Returns None if unparseable."""
    raw = result.get('published_date', '')
    if not raw:
        return None
    try:
        d = raw[:10]  # YYYY-MM-DD
        date.fromisoformat(d)
        return d
    except Exception:
        return None


def compute_age_months(source_date_str):
    """Compute age_months = floor((today - source_date).days / 30). Returns None if date missing."""
    if not source_date_str:
        return None
    try:
        src = date.fromisoformat(source_date_str)
        delta_days = (TODAY_DATE - src).days
        return math.floor(delta_days / 30)
    except Exception:
        return None


def is_stale(age_months):
    """Return True if age_months exceeds STALE_MONTHS threshold (24)."""
    if age_months is None:
        return False  # unknown age — include but flag
    return age_months > STALE_MONTHS


def build_label(confidence, source_name, source_date, url):
    """Build the source label string per DATA-CONTRACT label format."""
    method = 'Tavily WebFetch' if confidence == 'FACT' else 'Tavily snippet'
    return f'[{confidence} — {source_name} via {method}, {source_date or "date unknown"}, {url}]'


# ── Stat extraction from raw content ─────────────────────────────────────────

STAT_PATTERNS = [
    r'\d+(?:\.\d+)?%',           # percentages: 43%, 3.2x
    r'\d+(?:\.\d+)?[xX] ',       # multipliers: 3x more
    r'\$[\d,]+(?:\.\d+)?[BMK]',  # dollar amounts: $1.2B
    r'\d{1,3}(?:,\d{3})+',       # large numbers: 1,200,000
]

# Sentences containing these keywords are preferred — they're more likely
# to be search/commerce benchmarks rather than incidental stats
RELEVANCE_KEYWORDS = [
    'search', 'ecommerce', 'e-commerce', 'shopper', 'convert', 'conversion',
    'abandon', 'cart', 'checkout', 'retail', 'personali', 'recommend',
    'product', 'discovery', 'navigation', 'filter', 'facet',
]


def _sentence_relevance(sent):
    """Return True if sentence contains at least one commerce/search keyword."""
    low = sent.lower()
    return any(kw in low for kw in RELEVANCE_KEYWORDS)


def extract_stat_from_content(content, title):
    """
    Extract the most relevant stat (percentage, multiplier, dollar amount)
    from raw_content. Prefers sentences containing search/commerce keywords.
    Falls back to the first matching sentence, then to the title.
    Returns (value, context) where value is the stat string and context is the surrounding sentence.
    """
    if content:
        sentences = re.split(r'(?<=[.!?])\s+', content)
        relevant, fallback = [], []
        for sent in sentences[:50]:
            sent = sent.strip()
            if not (10 < len(sent) < 400):
                continue
            for pat in STAT_PATTERNS:
                m = re.search(pat, sent)
                if m:
                    entry = (m.group(0).strip(), sent)
                    if _sentence_relevance(sent):
                        relevant.append(entry)
                    else:
                        fallback.append(entry)
                    break  # one entry per sentence
        if relevant:
            return relevant[0]
        if fallback:
            return fallback[0]

    # Fall back to title
    for pat in STAT_PATTERNS:
        m = re.search(pat, title)
        if m:
            return m.group(0).strip(), title[:200]

    return None, title[:150]


def _clean_metric_title(title):
    """
    Convert an article title into a short metric name.
    Strips author/publisher suffixes and year noise.
    e.g. "Checkout UX Best Practices 2025 – Baymard Institute" → "Checkout UX Best Practices"
    """
    if not title:
        return 'Ecommerce benchmark'
    # Strip " – Source", " | Source", " - Source" publisher suffixes
    t = re.split(r'\s[–|—\-]\s+[A-Z]', title)[0].strip()
    # Strip trailing year "(2024)" or "2024" or "2025"
    t = re.sub(r'\s*[\(\[]?\b(20\d{2})\b[\)\]]?\s*$', '', t).strip()
    return t[:100] if t else title[:100]


def extract_expert_quote(content, title):
    """
    Find a sentence that looks like a named quote or analyst statement.
    Returns (quote, speaker, organization) or (None, None, None).
    """
    if not content:
        return None, None, None

    sentences = re.split(r'(?<=[.!?])\s+', content)
    # Look for quote patterns: "according to", "said", named-person patterns
    quote_patterns = [
        r'"([^"]{40,300})"',                # verbatim quoted text
        r'(?:said|noted|stated|explained)\s+that\s+(.{40,300}?)(?:\.|$)',
        r'(?:according to|per)\s+[\w\s]+?,\s*(.{40,300}?)(?:\.|$)',
    ]
    speaker_patterns = [
        r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(?:head of|director|VP|SVP|chief|analyst|president|manager)',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:of|at|from)\s+(?:Baymard|Forrester|Gartner|NRF|Nielsen)',
    ]

    for sent in sentences[:40]:
        for pat in quote_patterns:
            m = re.search(pat, sent, re.IGNORECASE)
            if m:
                quote_text = m.group(1).strip() if m.lastindex else sent.strip()
                if 40 < len(quote_text) < 400:
                    # Try to find speaker in surrounding context
                    speaker = None
                    org = None
                    for spat in speaker_patterns:
                        sm = re.search(spat, sent, re.IGNORECASE)
                        if sm:
                            speaker = sm.group(1)
                            break
                    return quote_text, speaker, org

    return None, None, None


# ── Main collection logic ─────────────────────────────────────────────────────

def build_queries(vertical, primary_market):
    """Build 3 Tavily queries based on vertical and primary_market locale."""
    locale = primary_market if primary_market in BENCHMARK_QUERIES else 'US'

    q_benchmark = BENCHMARK_QUERIES[locale].replace('{vertical}', vertical)
    q_trend = TREND_QUERIES[locale].replace('{vertical}', vertical)
    q_expert = EXPERT_QUOTE_QUERIES[locale].replace('{vertical}', vertical)

    return q_benchmark, q_trend, q_expert


def collect_benchmarks(vertical, primary_market, errors):
    """
    Run Tavily benchmark query + trend query, parse results into benchmarks[] and trends_2025_2026[].
    Returns (benchmarks, trends, sources_succeeded, sources_failed).
    """
    benchmarks = []
    trends = []
    sources_succeeded = []
    sources_failed = []

    if not tavily_available():
        errors.append('TAVILY_API_KEY not set — Tavily benchmark collection skipped')
        return benchmarks, trends, sources_succeeded, sources_failed

    q_benchmark, q_trend, _ = build_queries(vertical, primary_market)

    # ── Query 1: Benchmarks ───────────────────────────────────────────────────
    try:
        results = tavily_search(
            query=q_benchmark,
            topic='general',
            max_results=8,
            search_depth='advanced',
        )
        sources_succeeded.append('tavily:benchmarks')
    except Exception as e:
        errors.append(f'Tavily benchmark query failed: {e}')
        sources_failed.append('tavily:benchmarks')
        results = []

    for result in results:
        url = result.get('url', '')
        title = result.get('title', '')
        content = result.get('content', '')
        source_date = parse_source_date(result)
        age_months = compute_age_months(source_date)

        if is_stale(age_months):
            continue  # skip results older than 24 months

        source_type, source_name = classify_source(url)
        has_raw_content = bool(content and len(content) > 100)
        confidence = 'FACT' if has_raw_content else 'ESTIMATE'

        value, context = extract_stat_from_content(content, title)
        if not value:
            continue  # no stat extractable — skip

        label = build_label(confidence, source_name, source_date, url)

        entry = {
            'metric': _clean_metric_title(title),
            'value': value,
            'context': context,
            'source_name': source_name,
            'source_url': url,
            'source_date': source_date,
            'source_type': source_type,
            'confidence': confidence,
            'age_months': age_months,
            'verified': has_raw_content,
            'label': label,
        }
        benchmarks.append(entry)

        if len(benchmarks) >= 6:
            break

    # Sort: FACT before ESTIMATE, then by age (newer first)
    benchmarks.sort(key=lambda b: (0 if b['confidence'] == 'FACT' else 1, b.get('age_months') or 999))

    # ── Query 2: Trends ───────────────────────────────────────────────────────
    try:
        trend_results = tavily_search(
            query=q_trend,
            topic='general',
            max_results=6,
            search_depth='advanced',
        )
        sources_succeeded.append('tavily:trends')
    except Exception as e:
        errors.append(f'Tavily trend query failed: {e}')
        sources_failed.append('tavily:trends')
        trend_results = []

    for result in trend_results:
        url = result.get('url', '')
        title = result.get('title', '')
        content = result.get('content', '')
        source_date = parse_source_date(result)
        age_months = compute_age_months(source_date)

        if is_stale(age_months):
            continue

        source_type, source_name = classify_source(url)
        has_raw_content = bool(content and len(content) > 100)
        confidence = 'FACT' if has_raw_content else 'ESTIMATE'

        # Use title as trend headline, content first 300 chars as description
        description = content[:300].strip() if content else title
        label = build_label(confidence, source_name, source_date, url)

        entry = {
            'title': title[:140] if title else f'{vertical.title()} ecommerce trend 2025',
            'description': description,
            'source_url': url,
            'source_date': source_date,
            'source_type': source_type,
            'confidence': confidence,
            'age_months': age_months,
            'label': label,
        }
        trends.append(entry)

        if len(trends) >= 4:
            break

    return benchmarks, trends, sources_succeeded, sources_failed


def collect_expert_quotes(vertical, primary_market, errors):
    """
    Run Tavily expert quote query, parse into expert_quotes[].
    Returns (expert_quotes, sources_succeeded, sources_failed).
    """
    expert_quotes = []
    sources_succeeded = []
    sources_failed = []

    if not tavily_available():
        return expert_quotes, sources_succeeded, sources_failed

    _, _, q_expert = build_queries(vertical, primary_market)

    try:
        results = tavily_search(
            query=q_expert,
            topic='general',
            max_results=6,
            search_depth='advanced',
        )
        sources_succeeded.append('tavily:expert_quotes')
    except Exception as e:
        errors.append(f'Tavily expert quote query failed: {e}')
        sources_failed.append('tavily:expert_quotes')
        return expert_quotes, sources_succeeded, sources_failed

    for result in results:
        url = result.get('url', '')
        title = result.get('title', '')
        content = result.get('content', '')
        source_date = parse_source_date(result)
        age_months = compute_age_months(source_date)

        if is_stale(age_months):
            continue

        source_type, source_name = classify_source(url)
        has_raw_content = bool(content and len(content) > 100)
        confidence = 'FACT' if has_raw_content else 'ESTIMATE'

        quote_text, speaker, org = extract_expert_quote(content, title)
        if not quote_text:
            # Use title as fallback context — mark as ESTIMATE
            quote_text = title[:200]
            confidence = 'ESTIMATE'
            speaker = None
            org = source_name

        label = build_label(confidence, source_name, source_date, url)

        entry = {
            'quote': quote_text,
            'speaker': speaker,
            'organization': org or source_name,
            'source_url': url,
            'source_date': source_date,
            'source_type': source_type,
            'confidence': confidence,
            'age_months': age_months,
            'label': label,
        }
        expert_quotes.append(entry)

        if len(expert_quotes) >= 4:
            break

    return expert_quotes, sources_succeeded, sources_failed


# ── Trend headline extraction ─────────────────────────────────────────────────

def derive_trend_headline(trends):
    """
    Pick the most concrete trend headline from the trends list.
    Prefers entries with a stat (percentage/number) in the title.
    Returns a string or a generic placeholder.
    """
    for t in trends:
        title = t.get('title', '')
        for pat in STAT_PATTERNS:
            if re.search(pat, title):
                return title[:200]
    if trends:
        return trends[0].get('title', '')[:200]
    return '[COLLECT_VIA_SKILL] — trend headline to be filled by SKILL Step 2'


# ── Output writers ────────────────────────────────────────────────────────────

def write_json(output_dir, domain, company_name, vertical, primary_market,
               collection_method, benchmarks, trends, expert_quotes,
               trend_headline, errors, sources_succeeded, sources_failed):
    """
    Write industry-intel.json per DATA-CONTRACT Schema 1L.
    LLM-enriched fields (algolia_angle, competitor_search_landscape) left null.
    """
    json_path = os.path.join(output_dir, 'industry-intel.json')

    skill_enrichment_required = []
    if not benchmarks:
        skill_enrichment_required.append('benchmarks')
    if not trends:
        skill_enrichment_required.append('trends_2025_2026')
    if not expert_quotes:
        skill_enrichment_required.append('expert_quotes')
    skill_enrichment_required.append('algolia_angle')  # always — LLM fills
    skill_enrichment_required.append('competitor_search_landscape')  # always — LLM fills

    meta_block = base_meta(
        module='industry-intel',
        module_id='1L',
        script='collect-industry.py',
        domain=domain,
        company_name=company_name,
        sources_succeeded=sources_succeeded,
        sources_failed=sources_failed,
        skill_enrichment_required=skill_enrichment_required,
    )

    data = {
        '_meta': meta_block['meta'],
        'vertical': vertical,
        'primary_market': primary_market,
        'collection_method': collection_method,
        'benchmarks': benchmarks,
        'expert_quotes': expert_quotes,
        'trends_2025_2026': trends,
        'trend_headline': trend_headline,
        'trend_source_url': trends[0].get('source_url') if trends else None,
        'trend_source_label': trends[0].get('label') if trends else None,
        'algolia_angle': None,       # [COLLECT_VIA_SKILL] — SKILL Step 2 fills this
        'competitor_search_landscape': None,  # [COLLECT_VIA_SKILL] — SKILL Step 2 fills this
    }

    # Update meta status based on content
    if not errors:
        data['_meta']['status'] = 'success'
    elif benchmarks or trends:
        data['_meta']['status'] = 'partial'
    else:
        data['_meta']['status'] = 'failed'

    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    return json_path


def write_md(output_dir, domain, company_name, vertical, primary_market,
             collection_method, benchmarks, trends, expert_quotes, trend_headline):
    """
    Write industry-intel.md in the SKILL-expected format.
    Marks LLM-enriched fields with [COLLECT_VIA_SKILL].
    """
    md_path = os.path.join(output_dir, 'industry-intel.md')

    locale_note = primary_market or 'US (default)'
    method_note = 'Tavily advanced search' if collection_method == 'tavily_advanced' else 'WebSearch fallback required'

    lines = [
        f'# Industry Intelligence — {company_name} / {vertical.title()}',
        f'*Generated: {TODAY} via collect-industry.py | Vertical: {vertical} | Market: {locale_note}*',
        f'*Collection method: {method_note}*',
        '',
    ]

    # ── Vertical Overview placeholder ─────────────────────────────────────────
    lines += [
        '## Vertical Overview',
        '`[COLLECT_VIA_SKILL]` — SKILL Step 2 will write a 2-3 sentence overview connecting',
        f'the {vertical.title()} vertical\'s search/discovery challenges to the benchmarks below.',
        '',
    ]

    # ── Benchmarks ────────────────────────────────────────────────────────────
    lines += [
        f'## Key Benchmarks for {vertical.title()}',
        '',
        '| Metric | Value | Source | Age | Confidence | Verified |',
        '|--------|-------|--------|-----|------------|----------|',
    ]

    if benchmarks:
        for b in benchmarks:
            metric = b.get('metric', 'Unknown metric')[:80]
            value = b.get('value', 'N/A')
            source_name = b.get('source_name', 'Unknown')
            source_url = b.get('source_url', '')
            age = f"{b.get('age_months', '?')}mo" if b.get('age_months') is not None else '?'
            conf = b.get('confidence', 'ESTIMATE')
            verified = 'YES' if b.get('verified') else 'NO'
            src_display = f'[{source_name}]({source_url})' if source_url else source_name
            lines.append(f'| {metric} | {value} | {src_display} | {age} | {conf} | {verified} |')
    else:
        lines.append('| *No benchmarks collected — TAVILY_API_KEY not set or no qualifying results* | | | | | |')
        lines.append('| *Run SKILL Step 2 with WebSearch to collect benchmark data* | | | | | |')

    lines += ['', '### Benchmark Source Labels']
    for b in benchmarks:
        lines.append(f'- {b.get("label", "")}')
    lines.append('')

    # ── Trends 2025-2026 ──────────────────────────────────────────────────────
    lines += [
        '## 2025-2026 Trends',
        '',
    ]

    if trends:
        for i, t in enumerate(trends, 1):
            title = t.get('title', f'Trend {i}')
            desc = t.get('description', '')
            source_url = t.get('source_url', '')
            source_date = t.get('source_date', '')
            label = t.get('label', '')
            conf = t.get('confidence', 'ESTIMATE')

            lines += [
                f'{i}. **{title}**',
                f'   {desc[:300]}' if desc else '',
                f'   Source: [{source_url}]({source_url}) | Date: {source_date} | {conf}',
                f'   {label}',
                '',
            ]
    else:
        lines += [
            '*No trends collected — TAVILY_API_KEY not set or no qualifying results.*',
            '*Run SKILL Step 2 WebSearch fallback queries to collect trend data.*',
            '',
        ]

    # ── Trend headline ────────────────────────────────────────────────────────
    lines += [
        '### Trend Headline (for use in deliverables)',
        f'**{trend_headline}**',
        f'Source: {trends[0].get("source_url", "[COLLECT_VIA_SKILL]") if trends else "[COLLECT_VIA_SKILL]"}',
        '',
    ]

    # ── Expert Quotes ─────────────────────────────────────────────────────────
    lines += [
        '## Expert Quotes on Search in ' + vertical.title(),
        '',
        '| Quote | Speaker | Organization | Source | Date | Confidence |',
        '|-------|---------|--------------|--------|------|------------|',
    ]

    if expert_quotes:
        for q in expert_quotes:
            quote = (q.get('quote') or '')[:120].replace('|', '\\|')
            speaker = q.get('speaker') or 'Unnamed analyst'
            org = q.get('organization') or 'Unknown'
            source_url = q.get('source_url', '')
            source_date = q.get('source_date', '')
            conf = q.get('confidence', 'ESTIMATE')
            src_display = f'[link]({source_url})' if source_url else 'N/A'
            lines.append(f'| {quote} | {speaker} | {org} | {src_display} | {source_date} | {conf} |')
    else:
        lines.append('| *No expert quotes collected* | | | | | |')

    lines += ['', '### Expert Quote Labels']
    for q in expert_quotes:
        lines.append(f'- {q.get("label", "")}')
    lines.append('')

    # ── Algolia angle — LLM fills ─────────────────────────────────────────────
    lines += [
        '## Algolia Vertical Positioning',
        '',
        '**Algolia Angle:** `[COLLECT_VIA_SKILL]` — SKILL Step 2 will write one sentence',
        f'connecting the {vertical.title()} vertical trend to why this company needs Algolia now.',
        '',
        '**Competitor Search Landscape:** `[COLLECT_VIA_SKILL]` — SKILL Step 2 will write',
        'a paragraph on what search investments top competitors are making in this vertical.',
        '',
    ]

    # ── Sources ───────────────────────────────────────────────────────────────
    all_urls = set()
    for b in benchmarks:
        if b.get('source_url'):
            all_urls.add(b['source_url'])
    for t in trends:
        if t.get('source_url'):
            all_urls.add(t['source_url'])
    for q in expert_quotes:
        if q.get('source_url'):
            all_urls.add(q['source_url'])

    lines += [
        '## Sources',
        '',
    ]
    for url in sorted(all_urls):
        _, src_name = classify_source(url)
        lines.append(f'- [{src_name}]({url}) — Tavily advanced search')

    if not all_urls:
        lines.append('*No sources collected — see SKILL Step 2 WebSearch fallback.*')

    lines.append('')

    with open(md_path, 'w') as f:
        f.write('\n'.join(lines))

    return md_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print(
            'Usage: collect-industry.py <domain> <output-dir> [--company-name "Name"] [--vertical "footwear-retail"]',
            file=sys.stderr
        )
        sys.exit(1)

    domain = normalize_domain(sys.argv[1])
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    # Parse optional flags
    company_override = None
    vertical_override = None
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--company-name' and i + 1 < len(sys.argv):
            company_override = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--vertical' and i + 1 < len(sys.argv):
            vertical_override = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # Load upstream company context (graceful if missing)
    ctx = load_upstream(output_dir, '01-company-context.json')
    company_name = company_override or ctx.get('company_name') or domain
    # --vertical flag takes precedence over upstream value
    vertical = vertical_override or ctx.get('vertical') or 'ecommerce'
    primary_market = ctx.get('primary_market') or 'US'

    errors = []

    # ── Determine collection_method ───────────────────────────────────────────
    collection_method = 'tavily_advanced' if tavily_available() else 'websearch_fallback'

    # ── Collect benchmarks + trends ───────────────────────────────────────────
    benchmarks, trends, b_succeeded, b_failed = collect_benchmarks(
        vertical, primary_market, errors
    )

    # ── Collect expert quotes ─────────────────────────────────────────────────
    expert_quotes, q_succeeded, q_failed = collect_expert_quotes(
        vertical, primary_market, errors
    )

    sources_succeeded = b_succeeded + q_succeeded
    sources_failed = b_failed + q_failed

    # ── Trend headline ────────────────────────────────────────────────────────
    trend_headline = derive_trend_headline(trends)

    # ── Determine skill_enrichment_required ───────────────────────────────────
    skill_enrichment_required = ['algolia_angle', 'competitor_search_landscape']
    if collection_method == 'websearch_fallback':
        skill_enrichment_required += ['benchmarks', 'trends_2025_2026', 'expert_quotes']
    else:
        if not benchmarks:
            skill_enrichment_required.append('benchmarks')
        if not trends:
            skill_enrichment_required.append('trends_2025_2026')
        if not expert_quotes:
            skill_enrichment_required.append('expert_quotes')

    # ── Write outputs ─────────────────────────────────────────────────────────
    json_path = write_json(
        output_dir, domain, company_name, vertical, primary_market,
        collection_method, benchmarks, trends, expert_quotes,
        trend_headline, errors, sources_succeeded, sources_failed
    )
    md_path = write_md(
        output_dir, domain, company_name, vertical, primary_market,
        collection_method, benchmarks, trends, expert_quotes, trend_headline
    )

    # ── stdout JSON summary per DATA-CONTRACT §1.5 ────────────────────────────
    summary = build_summary(
        module='industry-intel',
        script='collect-industry.py',
        domain=domain,
        company_name=company_name,
        output_md=md_path,
        output_json=json_path,
        sources_succeeded=sources_succeeded,
        sources_failed=sources_failed,
        skill_enrichment_required=skill_enrichment_required,
        errors=errors,
    )
    summary['collection_method'] = collection_method
    summary['vertical'] = vertical
    summary['primary_market'] = primary_market
    summary['benchmarks_collected'] = len(benchmarks)
    summary['trends_collected'] = len(trends)
    summary['expert_quotes_collected'] = len(expert_quotes)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
