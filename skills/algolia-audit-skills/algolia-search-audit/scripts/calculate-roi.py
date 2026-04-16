#!/usr/bin/env python3
"""
calculate-roi.py — Deterministic ROI calculator for Algolia Search Audit
Reads 08-financial-profile.md, extracts revenue figures, applies ROI formula.

Formula:
  digital_revenue = total_revenue × digital_share (auto-detected or default 7.2%)
  search_addressable = digital_revenue × search_share (default 15%)
  conservative = search_addressable × 5%
  moderate = search_addressable × 10%

Usage: python3 calculate-roi.py <workspace-dir> [options]
Options:
  --digital-share FLOAT    Digital revenue as % of total (default: auto-detect from file or 0.072)
  --search-share FLOAT     Search-driven share of digital (default: 0.15)
  --conservative FLOAT     Conservative improvement rate (default: 0.05)
  --moderate FLOAT         Moderate improvement rate (default: 0.10)

Label convention (per Platform Constitution):
  [FACT]     = sourced directly from audited document
  [ESTIMATE] = derived via formula or industry default
"""

import sys, os, re, json, argparse


def parse_revenue(filepath):
    """Extract revenue figures from 08-financial-profile.md.

    Extraction priority (most precise first):
      Total revenue:
        1. Named section bullet: '- FY2025: $275.235B'
        2. Code block:           'Total Revenue (FY2025):  $275.235 billion'
        3. Table row:            '| **Revenue** | $237.7B | $249.6B | $275.2B |'

      Digital/e-commerce revenue:
        1. Table row:            '| **E-commerce Revenue (Est.)** | ~$15.0B | ~$17.5B | ~$19.8B |'
        2. Inline mention:       '$19.8B in digital sales'

      Digital share %:
        1. Code block line:      'Digital Share (E-commerce %):  7.2% (actual)'
    """
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    result = {
        'total_revenue': None,
        'digital_revenue': None,
        'digital_share_pct': None,
        'revenue_source': 'unknown',
        'digital_source': 'unknown',
        'confidence': 'LOW',
    }

    # ── Total Revenue ─────────────────────────────────────────────────────────
    # Priority 1: bullet line  "- FY2025: $275.235B"
    m = re.search(r'-\s*FY2025\s*:\s*\$\s*([\d,.]+)\s*(billion|[BbMm])\b', content)
    if m:
        result['total_revenue'] = _to_dollars(m.group(1), m.group(2))
        result['revenue_source'] = 'FY2025 bullet line'
        result['confidence'] = 'HIGH'

    # Priority 2: code-block line  "Total Revenue (FY2025):  $275.235 billion"
    if result['total_revenue'] is None:
        m = re.search(
            r'Total Revenue\s*\(FY2025\)\s*:\s*\$?\s*([\d,.]+)\s*(billion|[BbMm])\b',
            content, re.IGNORECASE
        )
        if m:
            result['total_revenue'] = _to_dollars(m.group(1), m.group(2))
            result['revenue_source'] = 'code-block Total Revenue (FY2025)'
            result['confidence'] = 'HIGH'

    # Priority 3: markdown table  "| **Revenue** | $Xb | $Xb | $275.2B |"
    # The 4th pipe-delimited column is FY2025.
    if result['total_revenue'] is None:
        m = re.search(
            r'\|\s*\*{0,2}Revenue\*{0,2}\s*\|'       # row label
            r'[^|]+\|'                                 # FY2023 cell
            r'[^|]+\|'                                 # FY2024 cell
            r'\s*~?\$\s*([\d,.]+)([BbMm])',            # FY2025 cell (may have ~)
            content, re.IGNORECASE
        )
        if m:
            result['total_revenue'] = _to_dollars(m.group(1), m.group(2))
            result['revenue_source'] = 'Revenue table row (FY2025 column)'
            result['confidence'] = 'MEDIUM'

    # ── Digital / E-commerce Revenue ──────────────────────────────────────────
    # Priority 1: e-commerce table row (FY2025 is 4th pipe column)
    # "| **E-commerce Revenue (Est.)** | ~$15.0B | ~$17.5B | ~$19.8B |"
    m = re.search(
        r'\|\s*\*{0,2}E-?[Cc]ommerce Revenue[^|]*\*{0,2}\s*\|'
        r'[^|]+\|'                     # FY2023 cell
        r'[^|]+\|'                     # FY2024 cell
        r'\s*~?\$\s*([\d,.]+)([BbMm])',  # FY2025 cell
        content, re.IGNORECASE
    )
    if m:
        result['digital_revenue'] = _to_dollars(m.group(1), m.group(2))
        result['digital_source'] = 'E-commerce Revenue table row (FY2025 column)'

    # Priority 2: prose mention of digital/ecommerce revenue with dollar amount
    if result['digital_revenue'] is None:
        m = re.search(
            r'\$\s*([\d,.]+)([BbMm])\+?\s*in\s+(?:digital|e-?commerce|online)\s+(?:sales|revenue)',
            content, re.IGNORECASE
        )
        if m:
            result['digital_revenue'] = _to_dollars(m.group(1), m.group(2))
            result['digital_source'] = 'prose mention of digital/ecommerce revenue'

    # ── Digital Share % ───────────────────────────────────────────────────────
    # "Digital Share (E-commerce %):  7.2% (actual)"
    m = re.search(r'Digital Share[^:]*:\s*([\d.]+)%', content, re.IGNORECASE)
    if m:
        result['digital_share_pct'] = float(m.group(1)) / 100.0

    # Compute digital_share_pct from the two revenue figures if not found above
    if result['digital_share_pct'] is None and result['digital_revenue'] and result['total_revenue']:
        result['digital_share_pct'] = result['digital_revenue'] / result['total_revenue']

    return result


def _to_dollars(num_str: str, unit: str) -> float:
    """Convert '275.235', 'B' → 275235000000.0"""
    num = float(num_str.replace(',', ''))
    u = unit.strip().lower()
    if u in ('b', 'billion'):
        return num * 1e9
    elif u in ('m', 'million'):
        return num * 1e6
    return num


def format_currency(amount: float) -> str:
    """Format dollar amount: $148.5M, $2.97B, etc."""
    if amount >= 1e9:
        return f'${amount / 1e9:.1f}B'
    elif amount >= 1e6:
        return f'${amount / 1e6:.1f}M'
    else:
        return f'${amount:,.0f}'


def calculate_roi(revenue_data: dict, digital_share: float, search_share: float,
                  conservative_rate: float, moderate_rate: float) -> dict:
    """Apply ROI formula and return labelled breakdown.

    Formula (all steps shown):
      digital_revenue      = total_revenue × digital_share
      search_addressable   = digital_revenue × search_share
      conservative         = search_addressable × conservative_rate
      moderate             = search_addressable × moderate_rate
    """
    total_rev = revenue_data.get('total_revenue')
    digital_rev = revenue_data.get('digital_revenue')
    detected_share = revenue_data.get('digital_share_pct')

    # ── Resolve digital revenue ───────────────────────────────────────────────
    if digital_rev:
        dig_rev = digital_rev
        dig_share_used = dig_rev / total_rev if total_rev else digital_share
        dig_label = '[FACT] — extracted from 08-financial-profile.md'
        dig_source = revenue_data.get('digital_source', 'parsed')
    elif total_rev:
        # Use file-detected share if available, else CLI arg, else built-in default
        share_to_use = detected_share if detected_share else digital_share
        dig_rev = total_rev * share_to_use
        dig_share_used = share_to_use
        if detected_share:
            dig_label = f'[ESTIMATE] — total_revenue × {share_to_use*100:.1f}% (digital share from file)'
        else:
            dig_label = f'[ESTIMATE] — total_revenue × {share_to_use*100:.1f}% (industry default / CLI override)'
        dig_source = 'calculated'
    else:
        return {'error': 'Could not extract total revenue from 08-financial-profile.md'}

    search_addressable = dig_rev * search_share
    conservative = search_addressable * conservative_rate
    moderate = search_addressable * moderate_rate

    return {
        'inputs': {
            'total_revenue': format_currency(total_rev) if total_rev else None,
            'total_revenue_raw': total_rev,
            'total_revenue_label': '[FACT] — FY2025 from 08-financial-profile.md',
            'total_revenue_source': revenue_data.get('revenue_source', 'parsed'),
            'digital_revenue': format_currency(dig_rev),
            'digital_revenue_raw': dig_rev,
            'digital_revenue_source': dig_source,
            'digital_share_pct': f'{dig_share_used * 100:.1f}%',
            'digital_label': dig_label,
            'search_share_pct': f'{search_share * 100:.0f}%',
            'search_share_label': '[ESTIMATE] — Baymard Institute: 10-30% of digital revenue is search-driven; 15% used as conservative mid-point',
        },
        'formula': {
            'step1_digital': (
                f'digital_revenue = total_revenue × digital_share'
                f' = {format_currency(total_rev)} × {dig_share_used * 100:.1f}%'
                f' = {format_currency(dig_rev)}'
            ) if total_rev else 'digital_revenue read directly from file',
            'step2_search_addressable': (
                f'search_addressable = digital_revenue × search_share'
                f' = {format_currency(dig_rev)} × {search_share * 100:.0f}%'
                f' = {format_currency(search_addressable)}'
            ),
            'step3_conservative': (
                f'conservative = search_addressable × {conservative_rate * 100:.0f}%'
                f' = {format_currency(search_addressable)} × {conservative_rate * 100:.0f}%'
                f' = {format_currency(conservative)}'
            ),
            'step3_moderate': (
                f'moderate = search_addressable × {moderate_rate * 100:.0f}%'
                f' = {format_currency(search_addressable)} × {moderate_rate * 100:.0f}%'
                f' = {format_currency(moderate)}'
            ),
        },
        'results': {
            'search_addressable': format_currency(search_addressable),
            'search_addressable_raw': search_addressable,
            'search_addressable_label': '[ESTIMATE]',
            'conservative': format_currency(conservative),
            'conservative_raw': conservative,
            'conservative_label': f'[ESTIMATE] — {conservative_rate * 100:.0f}% improvement rate (industry baseline)',
            'moderate': format_currency(moderate),
            'moderate_raw': moderate,
            'moderate_label': f'[ESTIMATE] — {moderate_rate * 100:.0f}% improvement rate (with full Algolia deployment)',
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description='Deterministic ROI calculator for Algolia Search Audit'
    )
    parser.add_argument('workspace', help='Workspace directory containing 08-financial-profile.md')
    parser.add_argument(
        '--digital-share', type=float, default=0.072,
        help='Digital share of total revenue (default: 0.072 = 7.2%% — US retail e-commerce avg)'
    )
    parser.add_argument(
        '--search-share', type=float, default=0.15,
        help='Search-driven share of digital revenue (default: 0.15)'
    )
    parser.add_argument(
        '--conservative', type=float, default=0.05,
        help='Conservative improvement rate (default: 0.05)'
    )
    parser.add_argument(
        '--moderate', type=float, default=0.10,
        help='Moderate improvement rate (default: 0.10)'
    )
    args = parser.parse_args()

    profile_path = os.path.join(args.workspace, '08-financial-profile.md')
    if not os.path.exists(profile_path):
        print(json.dumps({
            'error': f'08-financial-profile.md not found at {profile_path}',
        }))
        sys.exit(1)

    revenue_data = parse_revenue(profile_path)
    result = calculate_roi(
        revenue_data,
        args.digital_share,
        args.search_share,
        args.conservative,
        args.moderate,
    )
    result['source'] = profile_path
    result['confidence'] = revenue_data.get('confidence', 'LOW')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
