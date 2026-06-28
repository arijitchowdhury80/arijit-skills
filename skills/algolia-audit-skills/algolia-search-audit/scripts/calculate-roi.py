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


# ════════════════════════════════════════════════════════════════════════════
# 6-COMPONENT ROI MODEL (deterministic) — used by algolia-synth-business-case
# ════════════════════════════════════════════════════════════════════════════
#
# The LLM supplies LABELED assumptions only; this code does ALL arithmetic.
# Each component mirrors the formula documented in algolia-synth-business-case
# SKILL.md. Every component is computed for BOTH scenarios (conservative,
# moderate). Component "improvement" rates default to the SKILL.md baselines and
# can be overridden per-component via the assumptions JSON.
#
# Required assumptions (the LLM extracts/asks for these and passes them in):
#   monthly_visits        int    — from 03-traffic-data.md  [FACT — SimilarWeb]
#   aov                   float  — average order value      [AE fill-in / ESTIMATE]
#   search_usage_rate     float  — default 0.15             [ESTIMATE — industry]
#   current_conversion    float  — search→purchase rate     [AE fill-in]  (C2 only)
#   bounce_rate           float  — from 03-traffic-data.md  [FACT — SimilarWeb] (informational)
#   no_results_rate       float  — default 0.05             [ESTIMATE]    (C4)
#   nlp_fail_rate         float  — default 0.20             [ESTIMATE]    (C6)
#
# Scenario improvement defaults (SKILL.md baselines):
#   C1 conversion_delta:      conservative 0.15  moderate 0.20
#   C2 aov_delta:             conservative 0.05  moderate 0.10
#   C3 bounce_delta_pp:       conservative 0.10  moderate 0.15  (percentage points)
#      bounce recovery_conv:  conservative 0.10  moderate 0.12
#   C4 no_results_reduction:  recovery_rate 0.15 (both); moderate no_results_rate +0.03
#   C5 delay_buckets:         conservative 1     moderate 3   (×1% revenue per 100ms)
#   C6 nlp recovery_rate:     conservative 0.12  moderate 0.15; moderate nlp_fail_rate +0.10
#
# A component is only computed if its required inputs are present (else marked
# SKIPPED with the reason). AOV and the per-component assumption flags decide
# ACTIVE vs CONDITIONAL — that judgment stays with the LLM and is passed in.

COMPONENT_DEFAULTS = {
    'search_usage_rate': 0.15,
    'no_results_rate': 0.05,
    'nlp_fail_rate': 0.20,
    'c1_conv_delta_conservative': 0.15,
    'c1_conv_delta_moderate': 0.20,
    'c2_aov_delta_conservative': 0.05,
    'c2_aov_delta_moderate': 0.10,
    'c3_bounce_delta_pp_conservative': 0.10,
    'c3_bounce_delta_pp_moderate': 0.15,
    'c3_recovery_conv_conservative': 0.10,
    'c3_recovery_conv_moderate': 0.12,
    'c4_recovery_rate': 0.15,
    'c4_no_results_rate_moderate_bump': 0.03,
    'c5_delay_buckets_conservative': 1,
    'c5_delay_buckets_moderate': 3,
    'c5_revenue_per_100ms': 0.01,
    'c6_recovery_rate_conservative': 0.12,
    'c6_recovery_rate_moderate': 0.15,
    'c6_nlp_fail_rate_moderate_bump': 0.10,
}


def _money(x):
    return format_currency(x)


def calculate_components(a: dict) -> dict:
    """Compute all 6 ROI components × 2 scenarios from labeled assumptions `a`.

    `a` merges caller-supplied assumptions over COMPONENT_DEFAULTS. The LLM is
    responsible for the LABELS (FACT/ESTIMATE/AE-fill-in); this function never
    invents a value — if a required input is absent the component is SKIPPED.
    Annual figures use the 12-month multiplier exactly as the SKILL.md formulas.
    """
    d = dict(COMPONENT_DEFAULTS)
    d.update({k: v for k, v in a.items() if v is not None})

    visits = d.get('monthly_visits')
    aov = d.get('aov')
    sur = d.get('search_usage_rate')
    components = []

    def add(num, name, status, scenarios, formula_conservative, formula_moderate, note=None):
        comp = {
            'component': num,
            'name': name,
            'status': status,
            'conservative': _money(scenarios[0]) if scenarios[0] is not None else None,
            'conservative_raw': scenarios[0],
            'moderate': _money(scenarios[1]) if scenarios[1] is not None else None,
            'moderate_raw': scenarios[1],
            'formula_conservative': formula_conservative,
            'formula_moderate': formula_moderate,
        }
        if note:
            comp['note'] = note
        components.append(comp)

    # Monthly search sessions = monthly_visits × search_usage_rate
    sessions = visits * sur if (visits is not None and sur is not None) else None

    # ── Component 1: Search Conversion Lift ──────────────────────────────────
    # sessions × conversion_delta × AOV × 12
    if sessions is not None and aov is not None:
        c1c = sessions * d['c1_conv_delta_conservative'] * aov * 12
        c1m = sessions * d['c1_conv_delta_moderate'] * aov * 12
        add(1, 'Search Conversion Lift', d.get('c1_status', 'ACTIVE'), (c1c, c1m),
            f"{visits:,.0f} visits × {sur:.0%} search usage × {d['c1_conv_delta_conservative']:.0%} conv delta × ${aov:,.2f} AOV × 12 = {_money(c1c)}",
            f"{visits:,.0f} visits × {sur:.0%} search usage × {d['c1_conv_delta_moderate']:.0%} conv delta × ${aov:,.2f} AOV × 12 = {_money(c1m)}")
    else:
        add(1, 'Search Conversion Lift', 'SKIPPED', (None, None),
            'SKIPPED — needs monthly_visits, search_usage_rate, aov', 'SKIPPED')

    # ── Component 2: AOV Increase ────────────────────────────────────────────
    # search_initiated_orders/mo × aov_delta(× AOV) × 12
    # orders = sessions × current_conversion ; aov_delta is a % uplift on AOV
    cur_conv = d.get('current_conversion')
    if sessions is not None and aov is not None and cur_conv is not None:
        orders = sessions * cur_conv
        c2c = orders * (d['c2_aov_delta_conservative'] * aov) * 12
        c2m = orders * (d['c2_aov_delta_moderate'] * aov) * 12
        add(2, 'Average Order Value Increase', d.get('c2_status', 'CONDITIONAL'), (c2c, c2m),
            f"({visits:,.0f} × {sur:.0%} × {cur_conv:.1%} conv) orders × {d['c2_aov_delta_conservative']:.0%} × ${aov:,.2f} AOV × 12 = {_money(c2c)}",
            f"({visits:,.0f} × {sur:.0%} × {cur_conv:.1%} conv) orders × {d['c2_aov_delta_moderate']:.0%} × ${aov:,.2f} AOV × 12 = {_money(c2m)}")
    else:
        add(2, 'Average Order Value Increase', 'SKIPPED', (None, None),
            'SKIPPED — needs sessions, aov, current_conversion (AE fill-in)', 'SKIPPED')

    # ── Component 3: Bounce Rate Reduction ───────────────────────────────────
    # visits × search_usage × bounce_delta_pp × recovery_conv × AOV × 12
    if visits is not None and sur is not None and aov is not None:
        c3c = visits * sur * d['c3_bounce_delta_pp_conservative'] * d['c3_recovery_conv_conservative'] * aov * 12
        c3m = visits * sur * d['c3_bounce_delta_pp_moderate'] * d['c3_recovery_conv_moderate'] * aov * 12
        add(3, 'Bounce Rate Reduction', d.get('c3_status', 'CONDITIONAL'), (c3c, c3m),
            f"{visits:,.0f} × {sur:.0%} × {d['c3_bounce_delta_pp_conservative']:.0%}pp bounce delta × {d['c3_recovery_conv_conservative']:.0%} recovery × ${aov:,.2f} × 12 = {_money(c3c)}",
            f"{visits:,.0f} × {sur:.0%} × {d['c3_bounce_delta_pp_moderate']:.0%}pp bounce delta × {d['c3_recovery_conv_moderate']:.0%} recovery × ${aov:,.2f} × 12 = {_money(c3m)}")
    else:
        add(3, 'Bounce Rate Reduction', 'SKIPPED', (None, None),
            'SKIPPED — needs monthly_visits, search_usage_rate, aov', 'SKIPPED')

    # ── Component 4: No-Results Recovery ─────────────────────────────────────
    # monthly_searches × no_results_rate × AOV × recovery_rate × 12
    # monthly_searches == sessions (a search session issues ≥1 search)
    if sessions is not None and aov is not None:
        nrr_c = d['no_results_rate']
        nrr_m = d['no_results_rate'] + d['c4_no_results_rate_moderate_bump']
        rr = d['c4_recovery_rate']
        c4c = sessions * nrr_c * aov * rr * 12
        c4m = sessions * nrr_m * aov * rr * 12
        add(4, 'No-Results Recovery', d.get('c4_status', 'CONDITIONAL'), (c4c, c4m),
            f"{sessions:,.0f} searches × {nrr_c:.0%} no-results × ${aov:,.2f} × {rr:.0%} recovery × 12 = {_money(c4c)}",
            f"{sessions:,.0f} searches × {nrr_m:.0%} no-results × ${aov:,.2f} × {rr:.0%} recovery × 12 = {_money(c4m)}")
    else:
        add(4, 'No-Results Recovery', 'SKIPPED', (None, None),
            'SKIPPED — needs sessions, aov', 'SKIPPED')

    # ── Component 5: Speed / Latency Gain ────────────────────────────────────
    # visits × search_usage × (delay_buckets × revenue_per_100ms) × AOV × 12
    if visits is not None and sur is not None and aov is not None:
        rev100 = d['c5_revenue_per_100ms']
        bc = d['c5_delay_buckets_conservative']
        bm = d['c5_delay_buckets_moderate']
        c5c = visits * sur * (bc * rev100) * aov * 12
        c5m = visits * sur * (bm * rev100) * aov * 12
        add(5, 'Speed / Latency Gain', d.get('c5_status', 'CONDITIONAL'), (c5c, c5m),
            f"{visits:,.0f} × {sur:.0%} × ({bc} bucket × {rev100:.0%}/100ms) × ${aov:,.2f} × 12 = {_money(c5c)}",
            f"{visits:,.0f} × {sur:.0%} × ({bm} buckets × {rev100:.0%}/100ms) × ${aov:,.2f} × 12 = {_money(c5m)}")
    else:
        add(5, 'Speed / Latency Gain', 'SKIPPED', (None, None),
            'SKIPPED — needs monthly_visits, search_usage_rate, aov', 'SKIPPED')

    # ── Component 6: Long-Tail Discovery ─────────────────────────────────────
    # monthly_searches × nlp_fail_rate × AOV × recovery_rate × 12
    if sessions is not None and aov is not None:
        nlp_c = d['nlp_fail_rate']
        nlp_m = d['nlp_fail_rate'] + d['c6_nlp_fail_rate_moderate_bump']
        rr_c = d['c6_recovery_rate_conservative']
        rr_m = d['c6_recovery_rate_moderate']
        c6c = sessions * nlp_c * aov * rr_c * 12
        c6m = sessions * nlp_m * aov * rr_m * 12
        add(6, 'Long-Tail Discovery', d.get('c6_status', 'CONDITIONAL'), (c6c, c6m),
            f"{sessions:,.0f} searches × {nlp_c:.0%} NLP fail × ${aov:,.2f} × {rr_c:.0%} recovery × 12 = {_money(c6c)}",
            f"{sessions:,.0f} searches × {nlp_m:.0%} NLP fail × ${aov:,.2f} × {rr_m:.0%} recovery × 12 = {_money(c6m)}")
    else:
        add(6, 'Long-Tail Discovery', 'SKIPPED', (None, None),
            'SKIPPED — needs sessions, aov', 'SKIPPED')

    cons_total = sum(c['conservative_raw'] for c in components
                     if c['status'] != 'SKIPPED' and c['conservative_raw'] is not None)
    mod_total = sum(c['moderate_raw'] for c in components
                    if c['status'] != 'SKIPPED' and c['moderate_raw'] is not None)

    return {
        'mode': 'components',
        'assumptions_used': {
            'monthly_visits': visits,
            'aov': aov,
            'search_usage_rate': sur,
            'current_conversion': cur_conv,
            'no_results_rate': d['no_results_rate'],
            'nlp_fail_rate': d['nlp_fail_rate'],
            'monthly_search_sessions': sessions,
        },
        'components': components,
        'totals': {
            'conservative': _money(cons_total),
            'conservative_raw': cons_total,
            'conservative_formula': ' + '.join(
                c['conservative'] for c in components
                if c['status'] != 'SKIPPED' and c['conservative_raw'] is not None
            ) + f' = {_money(cons_total)}',
            'moderate': _money(mod_total),
            'moderate_raw': mod_total,
            'moderate_formula': ' + '.join(
                c['moderate'] for c in components
                if c['status'] != 'SKIPPED' and c['moderate_raw'] is not None
            ) + f' = {_money(mod_total)}',
        },
        'note': 'All arithmetic computed by calculate-roi.py. LLM supplies labeled '
                'assumptions only; it must NOT recompute or alter any figure here.',
    }


def _load_assumptions(args) -> dict:
    """Merge --assumptions JSON (file or inline) with individual CLI flags.

    CLI flags win over the JSON file (explicit override). All keys are optional;
    missing required inputs cause the dependent component to be SKIPPED, never
    fabricated.
    """
    a = {}
    if args.assumptions:
        raw = args.assumptions
        if os.path.exists(raw):
            with open(raw, encoding='utf-8') as f:
                a.update(json.load(f))
        else:
            a.update(json.loads(raw))
    # individual flags override
    for key in ('monthly_visits', 'aov', 'search_usage_rate', 'current_conversion',
                'bounce_rate', 'no_results_rate', 'nlp_fail_rate'):
        v = getattr(args, key, None)
        if v is not None:
            a[key] = v
    return a


def main():
    parser = argparse.ArgumentParser(
        description='Deterministic ROI calculator for Algolia Search Audit'
    )
    parser.add_argument('workspace', nargs='?',
                        help='Workspace directory containing 08-financial-profile.md '
                             '(top-down mode). Optional in --components mode.')
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
    # ── 6-component mode ──────────────────────────────────────────────────────
    parser.add_argument('--components', action='store_true',
                        help='Compute the 6-component ROI model from labeled assumptions '
                             '(used by algolia-synth-business-case).')
    parser.add_argument('--assumptions',
                        help='Path to a JSON file OR an inline JSON string of labeled '
                             'assumptions (monthly_visits, aov, search_usage_rate, '
                             'current_conversion, no_results_rate, nlp_fail_rate, ...).')
    parser.add_argument('--monthly-visits', dest='monthly_visits', type=float)
    parser.add_argument('--aov', type=float)
    parser.add_argument('--search-usage-rate', dest='search_usage_rate', type=float)
    parser.add_argument('--current-conversion', dest='current_conversion', type=float)
    parser.add_argument('--bounce-rate', dest='bounce_rate', type=float)
    parser.add_argument('--no-results-rate', dest='no_results_rate', type=float)
    parser.add_argument('--nlp-fail-rate', dest='nlp_fail_rate', type=float)
    args = parser.parse_args()

    if args.components:
        assumptions = _load_assumptions(args)
        if not assumptions.get('monthly_visits') or not assumptions.get('aov'):
            print(json.dumps({
                'error': 'components mode requires at least monthly_visits and aov. '
                         'Pass via --assumptions JSON or --monthly-visits/--aov. '
                         'Do NOT invent these — extract from 03-traffic-data.md / AE.',
            }, indent=2))
            sys.exit(1)
        result = calculate_components(assumptions)
        print(json.dumps(result, indent=2))
        return

    # ── top-down mode (original behaviour) ────────────────────────────────────
    if not args.workspace:
        print(json.dumps({'error': 'workspace dir required in top-down mode'}))
        sys.exit(1)

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
