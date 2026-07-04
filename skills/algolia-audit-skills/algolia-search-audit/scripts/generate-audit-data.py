#!/usr/bin/env python3
"""
generate-audit-data.py — Post-LLM JSON corrector for audit-data.json

WHY THIS EXISTS:
  The LLM generates correct synthesis content (intelligence signals, competitive
  analysis, exec quotes) but repeatedly produces wrong data types for structured
  fields that have no creative component: full_list as [{name,cat}] instead of
  ["string"], top_channels as a dict instead of array, wrong score key names, etc.

  This script patches the LLM's JSON with correctly-parsed values extracted
  directly from the structured .md scratchpad files. The LLM's synthesis fields
  are preserved unchanged. Only the mechanically-extractable fields are replaced.

USAGE:
  python3 generate-audit-data.py <slug> <workspace_dir>

  workspace_dir is the company folder, e.g. "$ALGOLIA_AUDIT_DIR/DSW"
  Output replaces: <workspace_dir>/deliverables/<slug>-audit-data.json

WHAT IT PATCHES (deterministic extraction, always correct):
  - tech_stack.full_list        → string[] from 02-tech-stack.md
  - tech_stack.primary_platform → string from summary table
  - tech_stack.search_provider  → string from summary table
  - traffic.top_channels        → [{source, share}] from traffic sources table
  - traffic.device_share        → {mobile, desktop} from device split
  - traffic.demographics        → [{age_group, pct, color}] from demographics
  - score.breakdown             → {canonical_key: number} from scoring matrix table
  - score.breakdown_severity    → {canonical_key: HIGH|MEDIUM|LOW}
  - score.breakdown_labels      → {canonical_key: display_name}
  - score.overall               → recalculated from weighted formula
  - score.verdict               → derived from overall score
  - score.critical_count        → counted from breakdown_severity (10-scoring-matrix.md HIGH)
  - score.moderate_count        → counted from breakdown_severity (10-scoring-matrix.md MEDIUM)
  - score.low_count             → counted from breakdown_severity (10-scoring-matrix.md LOW)
  - competitors[]               → [{name,domain,search_vendor,traffic,uses_algolia}]
  - intelligence_signals[]      → appends media_quote entries from 11-investor-intelligence.json
  - intelligence_signals[].urgency_score  → deterministic score by signal type + keyword boost
  - intelligence_signals[].category_tag   → ai_disruption / digital_transformation / cost_pressure / etc.
  - traffic.organic_search      → branded/NB split + top keywords from 03-traffic-data.json
  - traffic.geo_distribution    → top countries from 03-traffic-data.json
  - traffic.outgoing_traffic    → top link destinations from 03-traffic-data.json
  - traffic.rankings            → global/country/industry ranks from 03-traffic-data.json
  - traffic.referrals           → referring sites + industries from 03-traffic-data.json
  - financials.analyst_consensus → parsed from 08-financial-profile.json
  - financials.margins          → gross/EBITDA/operating/net margins from 08-financial-profile.json
  - financials.balance_sheet    → assets/debt/cash from 08-financial-profile.json
  - financials.digital_revenue  → latest FY estimate from 08-financial-profile.json
  - financials.roi_scenarios.{conservative,moderate}.value/value_num → re-derived
    from authoritative roi_conservative/roi_moderate strings (was: LLM hand-typed
    value could drop the leading digit, e.g. "8.4M" vs authoritative "$18.4M/year")
  - financials.total_digital_revenue → re-derived from authoritative d2c_digital_revenue
  - tech_stack.ai_search_gap    → NikeAI-type signal from 02-tech-stack.json
  - tech_stack.data_acquisitions → company acquisitions from 02-tech-stack.json
  - tech_stack.architecture_notes → frontend+cloud context from 02-tech-stack.json
  - hiring.total_open_roles     → from 09d-hiring-signals.md
  - hiring.icp_roles_count      → from 09d-hiring-signals.md
  - hiring.null_signal_note     → auto-generated when icp_roles_count == 0
  - partner_intel.unconfirmed_partners → Section B2 from partner-intel.md
  - partner_intel.sales_action_plan → Section C from partner-intel.md
  - partner_intel.cio_background_signal → CIO former employer from partner-intel.md

WHAT IT PRESERVES (LLM synthesis — not touched):
  executives, findings, gap_pairs, competitive_synthesis,
  golden_angle, company_snapshot, strategic_angles, icp_mapping, ae_fields,
  next_steps, abx_sequence, cover, meta, financials, hiring, bibliography
  (intelligence_signals[] is preserved AND augmented with media_quotes from 11-investor-intelligence.json)
"""

from __future__ import annotations
import json
import re
import sys
import os
from datetime import date

# ── Pydantic validation (runs BEFORE writing — catches field errors at write time) ──
from typing import Callable, Optional
_pydantic_validate: Optional[Callable[..., tuple[bool, list[str]]]] = None
_pydantic_available: bool = False
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    if _script_dir not in sys.path:
        sys.path.insert(0, _script_dir)
    from audit_data_schema import validate_audit_data as _pydantic_validate
    _pydantic_available = True
except ImportError:
    pass

# ── Canonical score area keys (SPA hardcodes these — NEVER change) ───────────
SCORE_AREAS = [
    ('latency', 'Latency'),
    ('typo_tolerance', 'Typo Tolerance'),
    ('query_suggestions_empty_state', 'Query Suggestions / Empty State'),
    ('intent_detection', 'Intent Detection'),
    ('merchandising_consistency', 'Merchandising Consistency'),
    ('content_commerce_ux', 'Content Commerce / Front-End UX'),
    ('semantic_nlp_search', 'Semantic / NLP Search'),
    ('dynamic_facets_personalization', 'Dynamic Facets & Personalization'),
    ('recommendations_merchandising', 'Recommendations & Merchandising'),
    ('search_intelligence', 'Search Intelligence'),
]
SCORE_KEY_MAP = {label.lower(): key for key, label in SCORE_AREAS}
# Extended aliases for common variations
SCORE_ALIASES = {
    'latency': 'latency',
    'typo tolerance': 'typo_tolerance',
    'typo': 'typo_tolerance',
    'query suggestions': 'query_suggestions_empty_state',
    'query suggestions / empty state': 'query_suggestions_empty_state',
    'intent detection': 'intent_detection',
    'merchandising consistency': 'merchandising_consistency',
    'merchandising': 'merchandising_consistency',
    'content commerce': 'content_commerce_ux',
    'content commerce / front-end ux': 'content_commerce_ux',
    'front-end ux': 'content_commerce_ux',
    'semantic / nlp search': 'semantic_nlp_search',
    'semantic nlp search': 'semantic_nlp_search',
    'semantic': 'semantic_nlp_search',
    'nlp': 'semantic_nlp_search',
    'dynamic facets': 'dynamic_facets_personalization',
    'dynamic facets & personalization': 'dynamic_facets_personalization',
    'personalization': 'dynamic_facets_personalization',
    'recommendations': 'recommendations_merchandising',
    'recommendations & merchandising': 'recommendations_merchandising',
    'search intelligence': 'search_intelligence',
}

WEIGHT_MAP = {'HIGH': 2.0, 'MEDIUM': 1.0, 'LOW': 0.5}
DEMOGRAPHIC_COLORS = ['#003DFF', '#5468FF', '#7B8FFF', '#A0AEFF', '#C5CCFF']


def read_file(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return f.read()


def log(msg):
    print(f'  [generate-audit-data] {msg}', flush=True)


def parse_money_amount(raw):
    """Extract (display_value, numeric_value) from an authoritative money string,
    e.g. '$18.4M/year' -> ('18.4M', 18400000), '$182M (jbl.com, 2024)' -> ('182M', 182000000).

    Root-cause fix for the leading-digit-drop bug (JBL 2026-07-01): a hand-written/
    LLM-written roi_scenarios.*.value ("8.4M") silently lost its first digit relative
    to the authoritative source string ("$18.4M/year"). Never trust the hand-written
    value — always regex-capture the FULL number (all leading digits) + unit from the
    source-of-truth string. This is intentionally NOT a strip-then-parseFloat: the
    capture group anchors on the digit/decimal run before the unit letter, so a
    leading "$" or trailing "/year" / "(jbl.com, 2024)" never eats into the number.

    Returns (None, None) if `raw` isn't a string or no $-amount pattern is found.
    """
    if not isinstance(raw, str):
        return None, None
    m = re.search(r'\$?\s*([0-9][0-9,]*\.?[0-9]*)\s*([BMK])\b', raw, re.IGNORECASE)
    if not m:
        return None, None
    num_str = m.group(1).replace(',', '')
    unit = m.group(2).upper()
    try:
        num = float(num_str)
    except ValueError:
        return None, None
    mult = {'B': 1e9, 'M': 1e6, 'K': 1e3}[unit]
    value_num = int(round(num * mult))
    value = f'{num_str}{unit}'
    return value, value_num


# ── TECH STACK parser ─────────────────────────────────────────────────────────

def parse_tech_stack(md_text):
    """Extract tech_stack fields that must be exact types."""
    result = {}

    # 1. full_list — bullet list of technology names (must be string[])
    # Scope extraction to sections that actually enumerate technologies (the
    # "Technology Stack" detection table and the "Adjacent stack" sentence),
    # NOT the whole document — a global bold-bullet regex over the entire .md
    # also matches field LABELS from unrelated sections (Search Vendor status
    # bullets, Oracle Method, Limitations, Sources Failed), and since those
    # labels are the bolded token while the actual value sits in plain text
    # after the colon, a global scrape produces label-only/blank chips
    # ("Status:", "Detected Vendor:", "Deal type:", etc.) instead of real
    # technology names.
    techs = []
    tech_section_match = re.search(
        r'##\s+Technology Stack.*?\n(.*?)(?=\n##|\Z)', md_text, re.IGNORECASE | re.DOTALL
    )
    tech_section = tech_section_match.group(1) if tech_section_match else ''
    # Detection table rows: | Category | Vendor |  — only keep rows with a real
    # detected value (not "Unable to detect" / WAF-blocked placeholders).
    for row in re.finditer(r'\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|', tech_section):
        cat, val = row.group(1).strip(), row.group(2).strip()
        if cat.lower() in ('category', 'detection') or not val:
            continue
        # Skip markdown table separator rows (e.g. "|----------|-----------|") — a row
        # is a separator if either column is made up entirely of dashes/colons/spaces.
        if re.fullmatch(r'[-:\s]+', cat) or re.fullmatch(r'[-:\s]+', val):
            continue
        if re.search(r'unable to detect|not fingerprinted|n/a|—|^-$', val, re.IGNORECASE):
            continue
        if val not in techs:
            techs.append(val)
    # "Adjacent stack (observed live): **Contentful** CMS (...), **Quantum
    # Metric** session replay..." — bolded technology names named as actually
    # observed, distinct from field-label bullets elsewhere in the doc.
    adjacent_match = re.search(r'Adjacent stack \(observed live\):\s*(.+)', md_text, re.IGNORECASE)
    if adjacent_match:
        for m in re.finditer(r'\*\*([^*]+)\*\*', adjacent_match.group(1)):
            name = re.sub(r'\s*\(.*', '', m.group(1)).strip()
            if len(name) > 1 and name not in techs:
                techs.append(name)

    if techs:
        result['full_list'] = techs
        log(f'tech_stack.full_list: {len(techs)} technologies extracted (string[])')
    else:
        log('tech_stack.full_list: could not parse — skipping')

    # 2. Technology Summary table
    # | Category | Vendor | Status | Confidence |
    summary_match = re.search(
        r'Technology Summary[^\n]*\n.*?\|.*?Category.*?\|.*?\n.*?\|[-| ]+\|\n((?:\|[^\n]+\n?)+)',
        md_text, re.IGNORECASE | re.DOTALL
    )
    if summary_match:
        for row in summary_match.group(1).strip().splitlines():
            cols = [c.strip() for c in row.split('|') if c.strip()]
            if len(cols) >= 2:
                cat = cols[0].lower()
                vendor = cols[1]
                if 'search' in cat and vendor and vendor not in ('N/A', 'TBD', '—', '-'):
                    result['search_provider'] = vendor
                elif ('ecommerce' in cat or 'e-commerce' in cat) and vendor:
                    result['ecommerce_platform'] = vendor
                elif 'cms' in cat and vendor:
                    result['cms'] = vendor
                elif 'tag' in cat and vendor:
                    result['tag_manager'] = vendor

    # 3. primary_platform — "Specific platform: X" or tech summary row or fallback.
    # Excludes "|" from the capture so this can't match a markdown TABLE ROW like
    # "| Ecommerce Platform | Unable to detect (WAF blocked) |" (the unscoped original
    # pattern treated "Ecommerce Platform" the table-header cell as a match trigger and
    # captured the rest of the row, pipes and all, as the platform name).
    plat_match = re.search(r'(?:primary platform|e[- ]?commerce platform)[:\s]+([^\n\[|]+)', md_text, re.IGNORECASE)
    candidate = plat_match.group(1).strip().rstrip('.').strip() if plat_match else None
    if candidate and re.search(r'unable to detect|not fingerprinted|n/a', candidate, re.IGNORECASE):
        candidate = None
    if candidate:
        result['primary_platform'] = candidate
    elif 'ecommerce_platform' in result:
        result['primary_platform'] = result['ecommerce_platform']
    else:
        # validate-json-schema.py's `if not ts.get('primary_platform'): fail(...)` treats
        # this field as REQUIRED-and-truthy, so we can't leave it None/unset when
        # detection genuinely failed (that would just fail the publish gate instead of
        # rendering a garbage value). Emit an honest, clean placeholder string instead
        # of the raw markdown table row an earlier, unscoped version of this regex used
        # to capture verbatim (e.g. "| Unable to detect (WAF blocked) |", pipes and all).
        result['primary_platform'] = 'Unable to detect (WAF-blocked; browser-based detection required)'

    # 4. search_provider — explicit line. Must require the label AND the value on the
    # SAME line, anchored to the start of a bullet — an unanchored pattern (previous
    # version) can match the bare "## Search Vendor" section HEADING itself, then
    # greedily capture the entire next line (the "- **Status:** ACTIVE..." bullet, not
    # the "**Detected Vendor:**" bullet one line further down, since that line has no
    # period to stop the capture).
    # NOTE: the source markdown wraps the colon INSIDE the bold span
    # (e.g. "- **Detected Vendor:** value"), not after it — the pattern below
    # tolerates the colon on either side of the closing "**" so it matches both
    # "**Detected Vendor:**" and "**Detected Vendor**:" forms.
    sp_match = re.search(
        r'^\s*-\s*\*\*(?:Detected Vendor|Search Vendor|Site Search):?\*\*:?\s*(.+)$',
        md_text, re.IGNORECASE | re.MULTILINE
    )
    if sp_match and 'search_provider' not in result:
        vendor = sp_match.group(1).strip()
        # Strip a leading bold wrapper (e.g. "**Proprietary / in-house** (Oracle...")
        # down to the plain vendor name, keeping any trailing parenthetical as-is.
        vendor = re.sub(r'^\*\*([^*]+)\*\*', r'\1', vendor).strip()
        result['search_provider'] = vendor

    # 5. algolia_detected
    result['algolia_detected'] = bool(re.search(r'algolia detected.*?yes', md_text, re.IGNORECASE))

    return result


# ── TRAFFIC parser ────────────────────────────────────────────────────────────

def parse_traffic(md_text):
    """Extract traffic fields with correct types."""
    result = {}

    # 1. Monthly visits — prefer MCP value, fall back to public page
    mv_match = re.search(r'Monthly Visits\s*(?:\(MCP\))?\s*\|\s*([0-9.,MBK]+)', md_text, re.IGNORECASE)
    if mv_match:
        result['monthly_visits'] = mv_match.group(1).strip()

    # 2. Bounce rate
    br_match = re.search(r'Bounce Rate\s*\|[^|]*?\|\s*([0-9.,]+%)', md_text, re.IGNORECASE)
    if not br_match:
        br_match = re.search(r'Bounce Rate\s*\|\s*([0-9.,]+%)', md_text, re.IGNORECASE)
    if br_match:
        result['bounce_rate'] = br_match.group(1).strip()

    # 3. Visit duration
    dur_match = re.search(r'(?:Avg )?(?:Visit|Session) Duration\s*\|[^|]*?\|\s*([^\|]+)', md_text, re.IGNORECASE)
    if not dur_match:
        dur_match = re.search(r'(?:Avg )?(?:Visit|Session) Duration\s*\|\s*([^\|\n]+)', md_text, re.IGNORECASE)
    if dur_match:
        result['visit_duration'] = dur_match.group(1).strip()

    # 4. Pages per visit
    ppv_match = re.search(r'Pages per Visit\s*\|\s*([^\|\n]+)', md_text, re.IGNORECASE)
    if ppv_match:
        val = ppv_match.group(1).strip()
        result['pages_per_visit'] = None if val.upper() in ('N/A', 'NA', '—', '-', '') else val

    # 5. top_channels — MUST be [{source, share}] array
    # Look for traffic sources table
    channels = []
    ch_section = re.search(
        r'(?:Traffic Sources?|Traffic Channels?)[^\n]*\n.*?\|.*?Channel.*?\|.*?\n.*?\|[-| ]+\|\n((?:\|[^\n]+\n?)+)',
        md_text, re.IGNORECASE | re.DOTALL
    )
    if ch_section:
        for row in ch_section.group(1).strip().splitlines():
            cols = [c.strip() for c in row.split('|') if c.strip()]
            if len(cols) >= 2:
                ch_name = re.sub(r'\*+', '', cols[0]).strip()
                # Normalize to the canonical bucket name the render template's DONUT_KEYS
                # strict-equality check expects (['Direct','Organic Search','Paid Search',
                # 'Social']) — upstream markdown headings vary in wording (e.g. "Google
                # (Organic Search)") and a verbatim label silently falls through to "Other",
                # zeroing out the "Via Search" KPI even when a genuine share was captured.
                if re.search(r'organic search', ch_name, re.IGNORECASE):
                    ch_name = 'Organic Search'
                elif re.search(r'paid search', ch_name, re.IGNORECASE):
                    ch_name = 'Paid Search'
                elif re.search(r'\bdirect\b', ch_name, re.IGNORECASE):
                    ch_name = 'Direct'
                elif re.search(r'\bsocial\b', ch_name, re.IGNORECASE):
                    ch_name = 'Social'
                share_raw = cols[1].strip()
                # A "share" must be a 0-100% share-of-traffic value, NOT a period-over-period
                # change metric. Some upstream tables put a MoM/YoY growth rate in the same
                # column as legitimate shares (e.g. "+276.44% MoM increase" next to "41.23%")
                # — reject those instead of silently accepting the first %-shaped number,
                # which previously produced impossible values like a 276% traffic share.
                is_change_metric = bool(re.search(
                    r'\bMoM\b|\bYoY\b|\bincrease\b|\bdecrease\b|\bchange\b|\bgrowth\b',
                    share_raw, re.IGNORECASE
                ))
                share_match = re.search(r'([\d.]+)%', share_raw)
                if (share_match and not is_change_metric and float(share_match.group(1)) <= 100
                        and ch_name and ch_name.lower() not in ('channel', 'source', 'total')):
                    channels.append({'channel': ch_name, 'share': share_match.group(1) + '%'})
                elif share_match and ch_name and ch_name.lower() not in ('channel', 'source', 'total'):
                    log(f'traffic.top_channels: skipped {ch_name!r} — {share_raw!r} is a period-change '
                        f'metric or out-of-range (>100%), not a genuine traffic share; leaving unset '
                        f'(real upstream gap, not fabricated)')

    if channels:
        result['top_channels'] = channels
        log(f'traffic.top_channels: {len(channels)} channels as array')
    else:
        log('traffic.top_channels: could not parse table — skipping')

    # 6. device_share — MUST have {mobile, desktop}
    mob_match = re.search(r'(?:Mobile|Mobile Web)\s*[\|:]\s*([\d.]+%)', md_text, re.IGNORECASE)
    desk_match = re.search(r'Desktop\s*[\|:]\s*([\d.]+%)', md_text, re.IGNORECASE)
    if mob_match:
        result['device_share'] = {
            'mobile': mob_match.group(1),  # keep % e.g. "54%"
            'desktop': desk_match.group(1) if desk_match else None,  # e.g. "46%"
        }
        log(f"traffic.device_share: mobile={result['device_share']['mobile']}")
    else:
        log('traffic.device_share: not found — skipping')

    # 7. demographics — MUST be [{age_group, pct, color}] array
    # Look specifically within a Demographics section header
    demographics = []
    demo_section_match = re.search(r'##\s+Demographics?\s*\n(.*?)(?=\n##|\Z)', md_text, re.IGNORECASE | re.DOTALL)
    demo_text = demo_section_match.group(1) if demo_section_match else md_text

    # Pattern 1: | Gender — Female | 76.46% | ...
    gender_rows = re.findall(r'\|\s*(Gender\s*[—-]\s*(?:Female|Male|Other)[^|]*)\s*\|\s*([\d.]+)%', demo_text, re.IGNORECASE)
    if gender_rows:
        for i, (label, pct) in enumerate(gender_rows):
            label_clean = re.sub(r'Gender\s*[—-]\s*', '', label, flags=re.IGNORECASE).strip()
            demographics.append({
                'age_group': label_clean,
                'pct': float(pct),
                'color': DEMOGRAPHIC_COLORS[i % len(DEMOGRAPHIC_COLORS)],
            })

    # Pattern 2: | 25-34 | 28% | ... (age group table)
    if not demographics:
        age_rows = re.findall(r'\|\s*(\d{2}[-–]\d{2}(?:\+)?)\s*\|\s*([\d.]+)%?', demo_text, re.IGNORECASE)
        for i, (age, pct) in enumerate(age_rows):
            demographics.append({
                'age_group': age,
                'pct': float(pct),
                'color': DEMOGRAPHIC_COLORS[i % len(DEMOGRAPHIC_COLORS)],
            })

    # Fallback: inline "76% female" or "| Gender — Female | 76.46% |" anywhere in doc
    if not demographics:
        female_match = re.search(r'(?:Gender\s*[—-]\s*Female|Female\s*Gender)[^\d]*([\d.]+)%', md_text, re.IGNORECASE)
        if not female_match:
            female_match = re.search(r'([\d.]+)%\s*female', md_text, re.IGNORECASE)
        male_match = re.search(r'(?:Gender\s*[—-]\s*Male|Male\s*Gender)[^\d]*([\d.]+)%', md_text, re.IGNORECASE)
        if not male_match:
            male_match = re.search(r'([\d.]+)%\s*male', md_text, re.IGNORECASE)
        if female_match:
            demographics = [
                {'age_group': 'Female', 'pct': float(female_match.group(1)), 'color': '#003DFF'},
                {'age_group': 'Male', 'pct': float(male_match.group(1)) if male_match else round(100 - float(female_match.group(1)), 1), 'color': '#5468FF'},
            ]

    if demographics:
        result['demographics'] = demographics
        log(f'traffic.demographics: {len(demographics)} entries as array')
        # Also extract gender into audience.gender so template's audience.gender.female/male works
        female_entry = next((d for d in demographics if 'female' in d.get('age_group','').lower()), None)
        male_entry   = next((d for d in demographics if d.get('age_group','').lower() == 'male'), None)
        if female_entry or male_entry:
            result.setdefault('audience', {})['gender'] = {
                'female': female_entry['pct'] if female_entry else None,
                'male':   male_entry['pct']   if male_entry   else None,
            }

    # 8. search_abandonment — google.com outbound traffic (quantified search abandonment)
    # Looks for google.com in the "Top Link Destinations" / "Outgoing Traffic" table
    google_pct_match = re.search(
        r'google\.com\s*\|\s*([\d.]+%)\s*\|\s*([↑↓][0-9.,]+%)',
        md_text, re.IGNORECASE
    )
    if not google_pct_match:
        google_pct_match = re.search(
            r'google\.com\s*\|\s*([\d.]+%)',
            md_text, re.IGNORECASE
        )
    if google_pct_match:
        pct = google_pct_match.group(1)
        mom = google_pct_match.group(2) if google_pct_match.lastindex >= 2 else None
        result['search_abandonment'] = {
            'google_outbound_pct': pct,
            'google_outbound_mom_change': mom,
            'narrative': f'{pct} of outbound traffic goes to Google{(" (" + mom + " MoM)") if mom else ""} — users abandoning on-site search and returning to Google to find products',
        }
        log(f'traffic.search_abandonment: google_outbound={pct}')
    else:
        log('traffic.search_abandonment: google.com outbound not found in outgoing traffic table')

    # 9. ai_referral — ChatGPT + Gemini referral share
    chatgpt_match = re.search(
        r'chatgpt\.com\s*\|\s*([\d.]+%)\s*\|\s*([↑↓][0-9.,]+%)',
        md_text, re.IGNORECASE
    )
    if not chatgpt_match:
        chatgpt_match = re.search(r'chatgpt\.com\s*\|\s*([\d.]+%)', md_text, re.IGNORECASE)
    gemini_match = re.search(
        r'gemini\.google\.com\s*\|\s*([\d.]+%)',
        md_text, re.IGNORECASE
    )
    ai_industry_match = re.search(
        r'AI Chatbots and Tools\s*\|\s*([\d.]+%)',
        md_text, re.IGNORECASE
    )
    if chatgpt_match:
        chatgpt_pct = chatgpt_match.group(1)
        chatgpt_mom = chatgpt_match.group(2) if chatgpt_match.lastindex >= 2 else None
        gemini_pct = gemini_match.group(1) if gemini_match else None
        ai_total = ai_industry_match.group(1) if ai_industry_match else None
        result['ai_referral'] = {
            'chatgpt_pct': chatgpt_pct,
            'chatgpt_mom': chatgpt_mom,
            'gemini_pct': gemini_pct,
            'total_ai_pct': ai_total,
            'narrative': f'ChatGPT is sending {chatgpt_pct} of referral traffic{(" (" + chatgpt_mom + " MoM)") if chatgpt_mom else ""}. AI chatbots represent {(ai_total + " of") if ai_total else "a growing share of"} all referral traffic — your buyers discover products via AI before visiting your site.',
        }
        log(f'traffic.ai_referral: chatgpt={chatgpt_pct}, ai_total={ai_total}')
    else:
        log('traffic.ai_referral: ChatGPT referral not found')

    # 10. top_referrers — top referring websites table
    referrers = []
    ref_section = re.search(
        r'Top Referring Websites?\s*\n.*?\|.*?Domain.*?\|.*?\n.*?\|[-| ]+\|\n((?:\|[^\n]+\n?)+)',
        md_text, re.IGNORECASE | re.DOTALL
    )
    if ref_section:
        for row in ref_section.group(1).strip().splitlines():
            cols = [c.strip() for c in row.split('|') if c.strip()]
            if len(cols) >= 2:
                domain = re.sub(r'\*+', '', cols[0]).strip()
                share_match = re.search(r'([\d.]+%)', cols[1])
                mom = cols[2].strip() if len(cols) >= 3 else None
                if share_match and domain and domain.lower() not in ('domain', 'site'):
                    referrers.append({
                        'domain': domain,
                        'share_pct': share_match.group(1),
                        'mom_change': mom if mom and re.search(r'[↑↓%]', mom or '') else None,
                    })
    if referrers:
        result['top_referrers'] = referrers
        log(f'traffic.top_referrers: {len(referrers)} referrers parsed')
    else:
        log('traffic.top_referrers: could not parse referrer table')

    # 11. paid_search — paid channel share + top keywords + competitor bidding
    paid_mom_change = None
    paid_share_match = re.search(r'Paid Search.*?(\d+\.?\d*)%\s*of.*?traffic', md_text, re.IGNORECASE)
    if not paid_share_match:
        # Try channel table row: | Paid Search | 10.05% |  — but guard against conflating a
        # MoM/YoY *change* metric (e.g. "+276.44% MoM increase") with a genuine share value.
        # A share must be 0-100% with no change-language qualifier in the same cell.
        paid_candidate = re.search(r'\|\s*Paid(?:\s+Search)?\s*\|\s*([^\|]+)\|', md_text, re.IGNORECASE)
        if paid_candidate:
            cell = paid_candidate.group(1).strip()
            is_change_metric = bool(re.search(
                r'\bMoM\b|\bYoY\b|\bincrease\b|\bdecrease\b|\bchange\b|\bgrowth\b',
                cell, re.IGNORECASE
            ))
            pct_m = re.search(r'([\d.]+)%', cell)
            if pct_m and not is_change_metric and float(pct_m.group(1)) <= 100:
                paid_share_match = pct_m
            elif pct_m:
                paid_mom_change = pct_m.group(1) + '%'
                log(f'traffic.paid_search: rejected share_of_total_pct candidate {cell!r} — '
                    f'MoM/YoY change metric or >100%, not a genuine share; leaving '
                    f'share_of_total_pct unset (real upstream gap, not fabricated)')
    paid_keywords = []
    paid_kw_section = re.search(
        r'Top [Pp]aid (?:Non-[Bb]randed )?[Ss]earch [Tt]erms?\s*\n.*?\|.*?Keyword.*?\|.*?\n.*?\|[-| ]+\|\n((?:\|[^\n]+\n?)+)',
        md_text, re.IGNORECASE | re.DOTALL
    )
    if paid_kw_section:
        for row in paid_kw_section.group(1).strip().splitlines():
            cols = [c.strip() for c in row.split('|') if c.strip()]
            if len(cols) >= 2:
                kw = re.sub(r'\*+', '', cols[0]).strip()
                share_m = re.search(r'([\d.]+%)', cols[1])
                mom = cols[2].strip() if len(cols) >= 3 else None
                if share_m and kw and kw.lower() not in ('keyword', 'term'):
                    paid_keywords.append({
                        'keyword': kw,
                        'share_pct': share_m.group(1),
                        'mom_change': mom if mom and re.search(r'[↑↓%]', mom or '') else None,
                    })
    # Detect competitor brand bidding — look for competitor names in paid keywords
    competitor_bid = None
    known_competitors_pattern = r'\b(party\s*city|partycity|adidas|underarmour|under\s*armour|puma|target|walmart|amazon|michaels)\b'
    for kw_obj in paid_keywords:
        if re.search(known_competitors_pattern, kw_obj.get('keyword',''), re.IGNORECASE):
            competitor_bid = kw_obj['keyword']
            break
    if paid_share_match or paid_keywords or paid_mom_change:
        paid_obj = {}
        if paid_share_match:
            paid_obj['share_of_total_pct'] = paid_share_match.group(1).strip().rstrip('%') + '%' if '%' not in paid_share_match.group(1) else paid_share_match.group(1).strip()
        if paid_mom_change:
            paid_obj['mom_change_pct'] = paid_mom_change
        if paid_keywords:
            paid_obj['top_keywords'] = paid_keywords
        if competitor_bid:
            paid_obj['competitor_bidding'] = competitor_bid
            paid_obj['narrative'] = f'Bidding on "{competitor_bid}" — direct competitor conquest in paid search. Improve on-site search to convert these intercept arrivals.'
        result['paid_search'] = paid_obj
        log(f'traffic.paid_search: {len(paid_keywords)} paid keywords, competitor_bid={competitor_bid}')
    else:
        log('traffic.paid_search: no paid search data found')

    # 12. competitor_traffic — visits comparison table
    comp_traffic = []
    ct_section = re.search(
        r'Competitor Traffic Comparison\s*\n.*?\|.*?Domain.*?\|.*?\n.*?\|[-| ]+\|\n((?:\|[^\n]+\n?)+)',
        md_text, re.IGNORECASE | re.DOTALL
    )
    if ct_section:
        for row in ct_section.group(1).strip().splitlines():
            cols = [c.strip() for c in row.split('|') if c.strip()]
            if len(cols) >= 2:
                domain = re.sub(r'[\*\[\]`]', '', cols[0]).strip()
                visits = re.sub(r'[\*\[\]`]', '', cols[1]).strip()
                if domain and visits and domain.lower() not in ('domain', 'site', 'company'):
                    comp_traffic.append({'domain': domain, 'visits_3mo': visits})
    if comp_traffic:
        result['competitor_traffic'] = comp_traffic
        log(f'traffic.competitor_traffic: {len(comp_traffic)} competitors')
    else:
        log('traffic.competitor_traffic: comparison table not found')

    return result


# ── COMPETITORS parser ────────────────────────────────────────────────────────

def parse_competitors(md_text):
    """Extract competitor list with correct schema.

    Handles two table layouts:
      A) Rank | Domain | Monthly Visits | Detection | Search Provider  (DSW style)
      B) Rank | Competitor Name | Domain | Rationale | ...             (Costco style)
    Detects layout by finding which column contains a domain (.com/.net/.org).
    """
    competitors = []
    seen = set()

    comp_section = re.search(
        r'Top (?:5 )?Competitors?[^\n]*\n.*?\|[^|]*(?:Rank|Domain|Competitor)[^\n]*\n.*?\|[-| ]+\|\n((?:\|[^\n]+\n?)+)',
        md_text, re.IGNORECASE | re.DOTALL
    )
    if not comp_section:
        log('competitors: could not parse table — skipping')
        return competitors

    for row in comp_section.group(1).strip().splitlines():
        cols = [re.sub(r'\*+', '', c).strip() for c in row.split('|') if c.strip()]
        if len(cols) < 2:
            continue

        # Find the domain column — it's the first column containing a .tld
        domain = None
        domain_col_idx = None
        for i, col in enumerate(cols):
            # Look for something like samsclub.com or www.amazon.com
            dm = re.search(r'\b([a-z0-9\-]+\.[a-z]{2,6})\b', col.lower())
            if dm and '.' in dm.group(1):
                candidate = dm.group(1).lower()
                # Filter out source labels and date strings
                if not any(x in candidate for x in ['http', 'est.', 'score', 'fact', 'web', 'search', 'api']):
                    domain = candidate
                    domain_col_idx = i
                    break

        if not domain or domain in seen:
            continue
        seen.add(domain)

        # Name: prefer the column before domain (or after rank), else derive from domain
        name = None
        if domain_col_idx is not None and domain_col_idx > 0:
            name_raw = cols[domain_col_idx - 1]
            if not name_raw.isdigit():
                name = re.sub(r'\s*\[.*?\]', '', name_raw).strip()
        if not name or name.isdigit():
            name_match = re.search(rf'\*?\*?([A-Za-z][A-Za-z0-9\s\'\-\.]+?)\*?\*?\s*\(?{re.escape(domain)}\)?', md_text, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else domain.split('.')[0].title()

        # Search vendor / traffic from remaining columns
        traffic = None
        sv = 'Unknown'
        for i, col in enumerate(cols):
            if i == domain_col_idx:
                continue
            # Traffic: looks like "14.5M" or "68.4M"
            if re.match(r'^[\d.,]+[MBK]?$', col.strip()) and not traffic:
                traffic = col.strip()
            # Search vendor
            if any(x in col.lower() for x in ['algolia', 'elastic', 'solr', 'lucid', 'searchspring', 'constructor', 'bloomreach', 'coveo', 'amazon', 'azure', 'custom']):
                sv = re.sub(r'\s*\[.*?\]', '', col).strip()

        uses_algolia = bool(re.search(r'algolia', sv, re.IGNORECASE))

        competitors.append({
            'name': name,
            'domain': domain,
            'search_vendor': sv,
            'monthly_traffic': traffic,
            'traffic_rank': None,
            'uses_algolia': uses_algolia,
            'notes': None,
        })

    if competitors:
        log(f'competitors: {len(competitors)} extracted')
    else:
        log('competitors: could not parse table — skipping')

    return competitors


# ── SCORE parser ──────────────────────────────────────────────────────────────

def parse_score(md_text):
    """Extract the 10-area score with canonical key names.

    Handles two table formats:
      A) | # | **Area** | Score | Severity | Weight | Evidence |   (DSW — weight included)
      B) | # | **Area** | Score/10 | Severity | Evidence | ...     (Costco — no weight, /10 suffix)
      C) | Area | Score | Severity | Weight | Score×Weight |       (weighted calc table — plain numbers)
    """
    breakdown = {}
    breakdown_severity = {}
    breakdown_labels = {key: label for key, label in SCORE_AREAS}

    # Pattern A/B: # | Area | Score or Score/10 | Severity | ...
    # Accepts "7" or "7/10" or "7.5" in the score column
    row_pattern = re.compile(
        r'\|\s*\d+\.?\s*\|\s*\*?\*?([^|*]+?)\*?\*?\s*\|\s*(\d+(?:\.\d+)?)(?:/10)?\s*\|\s*(HIGH|MEDIUM|LOW)\s*\|',
        re.IGNORECASE
    )
    for m in row_pattern.finditer(md_text):
        area_raw = m.group(1).strip().lower()
        score_val = float(m.group(2))
        severity = m.group(3).upper()

        # Map to canonical key. Normalize punctuation (hyphens/slashes/ampersands -> spaces)
        # and match the LONGEST alias first, so bare 'merchandising' cannot steal
        # 'Recommendations / Merchandising' and hyphenated 'Content-Commerce UX' still
        # matches the 'content commerce' alias.
        area_norm = re.sub(r'[^a-z0-9]+', ' ', area_raw.lower()).strip()
        canonical = None
        for alias, key in sorted(SCORE_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True):
            a = re.sub(r'[^a-z0-9]+', ' ', alias.lower()).strip()
            if a == area_norm or a in area_norm or area_norm in a:
                canonical = key
                break

        if canonical and canonical not in breakdown:
            breakdown[canonical] = score_val
            breakdown_severity[canonical] = severity

    if len(breakdown) < 8:
        log(f'score: only {len(breakdown)}/10 areas parsed from table — partial patch')
    else:
        log(f'score: {len(breakdown)}/10 areas parsed correctly')

    if not breakdown:
        return {}

    # Recalculate overall score
    total_weighted = sum(breakdown[k] * WEIGHT_MAP.get(breakdown_severity.get(k, 'MEDIUM'), 1.0) for k in breakdown)
    total_weight = sum(WEIGHT_MAP.get(breakdown_severity.get(k, 'MEDIUM'), 1.0) for k in breakdown)
    overall = round(total_weighted / total_weight, 1) if total_weight > 0 else None

    # Verdict
    if overall is None:
        verdict = 'Unknown'
        verdict_class = 'unknown'
    elif overall >= 8.0:
        verdict, verdict_class = 'Strong Foundation', 'good'
    elif overall >= 6.0:
        verdict, verdict_class = 'Needs Improvement', 'moderate'
    elif overall >= 4.0:
        verdict, verdict_class = 'Needs Significant Work', 'critical'
    else:
        verdict, verdict_class = 'Critical Gaps', 'critical'

    # Deterministic severity counts — root-cause fix (JBL 2026-07-01, lululemon earlier):
    # the old formula gated HIGH/MEDIUM membership on an ARBITRARY score cutoff
    # (severity=='HIGH' AND score<5; severity in ('MEDIUM','HIGH') AND score<7),
    # which (a) double-counted HIGH areas into moderate_count whenever their score
    # was also <7, and (b) silently dropped any HIGH/MEDIUM area whose score sat on
    # the wrong side of the cutoff — producing wrong totals (JBL: critical 4 not 5,
    # moderate 7 not 4) and never emitting low_count at all. breakdown_severity IS
    # the 10-scoring-matrix.md HIGH/MEDIUM/LOW classification (parsed above) — count
    # it directly, no secondary score-based filter.
    critical_count = sum(1 for v in breakdown_severity.values() if v == 'HIGH')
    moderate_count = sum(1 for v in breakdown_severity.values() if v == 'MEDIUM')
    low_count = sum(1 for v in breakdown_severity.values() if v == 'LOW')

    return {
        'overall': overall,
        'verdict': verdict,
        'verdict_class': verdict_class,
        'breakdown': breakdown,
        'breakdown_severity': breakdown_severity,
        'breakdown_labels': breakdown_labels,
        'critical_count': critical_count,
        'moderate_count': moderate_count,
        'low_count': low_count,
        'formula_shown': 'sum(score×weight)/sum(weights)',
        'source': '10-scoring-matrix.md',
    }


# ── MEDIA QUOTES lifter ───────────────────────────────────────────────────────

def lift_media_quotes(research_dir):
    """Read media_quotes[] from 11-investor-intelligence.json and return them
    as intelligence_signals[] entries with type='media_quote'.

    Skips entries where:
      - source_url is null / empty
      - quote is '[COLLECT_VIA_SKILL]' or empty

    Returns an empty list if the file is missing or has no media_quotes key
    (graceful backward-compat for pre-v1.1 audits).
    """
    investor_path = os.path.join(research_dir, '11-investor-intelligence.json')
    if not os.path.exists(investor_path):
        log('intelligence_signals (media): 11-investor-intelligence.json not found — skipping')
        return []

    try:
        with open(investor_path, encoding='utf-8') as f:
            investor_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log(f'intelligence_signals (media): could not parse 11-investor-intelligence.json — {e}')
        return []

    if 'media_quotes' not in investor_data:
        log('intelligence_signals (media): no media_quotes key in 11-investor-intelligence.json — skipping')
        return []
    raw_quotes = investor_data['media_quotes']
    if not raw_quotes:
        log('intelligence_signals (media): media_quotes is empty (0 entries) — skipping')
        return []

    signals = []
    skipped = 0
    for mq in raw_quotes:
        # Skip placeholder / unresolved entries
        source_url = mq.get('source_url') or ''
        quote = mq.get('quote') or ''
        if not source_url.strip():
            skipped += 1
            continue
        if quote.strip() in ('', '[COLLECT_VIA_SKILL]'):
            skipped += 1
            continue

        speaker = mq.get('speaker', '')
        speaker_title = mq.get('title', '')
        signal = {
            'type': 'media_quote',
            # Speaker kept as first-class fields so the synthesis step can group
            # multiple statements from the SAME person into one signal (see
            # dedupe_merge_signals). Without these, per-speaker merge is impossible.
            'speaker': speaker,
            'speaker_title': speaker_title,
            # Canonical fields the template reads (badge_label→title, signal→body, algolia_angle→Algolia angle)
            'badge_label': f"{speaker}, {speaker_title}".strip(', ') if speaker else speaker_title,
            'text': quote[:120],
            'algolia_angle': mq.get('context', '') or mq.get('algolia_relevance', ''),
            # Preserved originals for source attribution
            'source_url': source_url,
            'source_name': mq.get('publication', ''),
            'source_date': mq.get('source_date', ''),
            'confidence': mq.get('confidence', 'FACT'),
            'label': mq.get('label', ''),
        }
        signals.append(signal)

    log(f'intelligence_signals (media): {len(signals)} media_quote entries lifted'
        + (f', {skipped} skipped (no URL or placeholder)' if skipped else ''))
    return signals


def lift_hiring_signals(research_dir, hiring_obj):
    """Emit intelligence_signals[] entries with type='hiring' so the renderer's
    hiring section populates.

    WHY THIS EXISTS: render-audit.ts buildHiringBarRows/buildHiringCallout read
    ONLY data.intelligence_signals[type=='hiring'] (s.text, s.source_url,
    s.source_name). The rich `hiring` object (summary, buying_committee, roles)
    was NEVER converted into those signals, so every audit rendered
    "Hiring signal data not available." even with a fully-populated hiring object.

    Sources, in priority order:
      1. hiring_obj.summary + hiring_obj.top_signals (LLM synthesis, keyword-rich)
      2. 09d-hiring-signals.json roles_by_tier / buying_committee (fallback)
    source_url comes from 01-company-context.json careers_url (real, no fabrication).
    Returns [] when there is genuinely nothing to emit.
    """
    hiring_obj = hiring_obj or {}

    # Real careers URL for the callout citation (no fabricated links)
    careers_url = None
    source_name = 'Company Careers + job boards'
    ctx_path = os.path.join(research_dir, '01-company-context.json')
    if os.path.exists(ctx_path):
        try:
            with open(ctx_path, encoding='utf-8') as f:
                ctx = json.load(f)
            careers_url = ctx.get('careers_url') or ctx.get('about_url')
            cname = ctx.get('company_name')
            if cname:
                source_name = f'{cname} Careers + job boards'
        except (json.JSONDecodeError, OSError):
            pass

    texts = []  # ordered; first entry drives the callout
    if hiring_obj.get('summary'):
        texts.append(hiring_obj['summary'])
    for role in (hiring_obj.get('top_signals') or []):
        if isinstance(role, str) and role.strip():
            texts.append(role.strip())

    # Fallback to 09d research JSON if the hiring object was thin
    if not texts:
        h_path = os.path.join(research_dir, '09d-hiring-signals.json')
        if os.path.exists(h_path):
            try:
                with open(h_path, encoding='utf-8') as f:
                    hj = json.load(f)
                for r in (hj.get('roles_by_tier') or []):
                    if isinstance(r, dict) and r.get('role'):
                        label = r['role']
                        if r.get('name'):
                            label += f" ({r['name']})"
                        texts.append(label)
                for vs in (hj.get('vacancy_signals') or []):
                    if isinstance(vs, str) and vs.strip():
                        texts.append(vs.strip())
            except (json.JSONDecodeError, OSError):
                pass

    if not texts:
        log('intelligence_signals (hiring): no hiring summary/roles found — skipping')
        return []

    signals = []
    for i, t in enumerate(texts):
        signals.append({
            'type': 'hiring',
            'text': t,
            'source_url': careers_url,
            'source_name': source_name,
            'confidence': 'FACT',
        })
    log(f'intelligence_signals (hiring): built {len(signals)} hiring signal(s) '
        f'(source_url={"set" if careers_url else "MISSING"})')
    return signals


# ── INDUSTRY CONTEXT builder ──────────────────────────────────────────────────

def build_industry_context(research_dir):
    """Read industry-intel.json from research_dir and build the industry_context dict.

    Population rules (DATA-CONTRACT v1.1):
      - Max 3 benchmarks in key_benchmarks[] — highest confidence (FACT first),
        then most recent source_date.
      - primary_market mirrors 01-company-context.json → primary_market (or 'US' fallback).
      - algolia_angle mirrors industry-intel.json → algolia_angle.
      - Returns None if file missing OR (no benchmarks AND no trend_headline).

    Graceful: returns None on any parse error or insufficient data.
    """
    intel_path = os.path.join(research_dir, 'industry-intel.json')
    if not os.path.exists(intel_path):
        log('industry_context: industry-intel.json not found — setting null')
        return None

    try:
        with open(intel_path, encoding='utf-8') as f:
            intel = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log(f'industry_context: could not parse industry-intel.json — {e}')
        return None

    # ── primary_market: prefer 01-company-context.json, fallback to intel or 'US'
    primary_market = 'US'
    ctx_path = os.path.join(research_dir, '01-company-context.json')
    if os.path.exists(ctx_path):
        try:
            with open(ctx_path, encoding='utf-8') as f:
                ctx = json.load(f)
            primary_market = ctx.get('primary_market') or intel.get('primary_market') or 'US'
        except (json.JSONDecodeError, OSError):
            primary_market = intel.get('primary_market') or 'US'
    else:
        primary_market = intel.get('primary_market') or 'US'

    # ── benchmarks: sort FACT first (conf_rank ASC), then newest date first (DESC)
    raw_benchmarks = intel.get('benchmarks') or []

    # Invert the date string digit-by-digit so that a later date sorts earlier
    # under Python's default ascending lexicographic order.
    # e.g. '2024-11-01' → '7975-88-98'  (9 - digit for each digit character)
    def _invert_date(d):
        return ''.join(str(9 - int(c)) if c.isdigit() else c for c in (d or '0000-00-00'))

    sorted_benchmarks = sorted(
        raw_benchmarks,
        key=lambda b: (
            0 if (b.get('confidence') or '').upper() == 'FACT' else 1,
            _invert_date(b.get('source_date')),
        )
    )

    top_benchmarks = sorted_benchmarks[:3]

    key_benchmarks = []
    for b in top_benchmarks:
        conf = (b.get('confidence') or 'ESTIMATE').upper()
        # Normalise confidence to FACT or ESTIMATE
        if 'FACT' in conf:
            conf_norm = 'FACT'
        else:
            conf_norm = 'ESTIMATE'

        key_benchmarks.append({
            'metric':       b.get('metric', ''),
            'value':        b.get('value', ''),
            'context':      b.get('context', ''),
            'source_name':  b.get('source_name', ''),
            'source_url':   b.get('source_url', ''),
            'source_date':  b.get('source_date', ''),
            'confidence':   conf_norm,
            'label':        b.get('label', ''),
        })

    trend_headline   = intel.get('trend_headline') or ''
    trend_source_url = intel.get('trend_source_url') or ''
    trend_source_label = intel.get('trend_source_label') or ''
    algolia_angle    = intel.get('algolia_angle') or ''
    vertical         = intel.get('vertical') or ''

    # Insufficient data guard: must have benchmarks OR a trend_headline
    if not key_benchmarks and not trend_headline:
        log('industry_context: no benchmarks and no trend_headline — setting null')
        return None

    result = {
        'vertical':            vertical,
        'primary_market':      primary_market,
        'key_benchmarks':      key_benchmarks,
        'trend_headline':      trend_headline,
        'trend_source_url':    trend_source_url,
        'trend_source_label':  trend_source_label,
        'algolia_angle':       algolia_angle,
    }

    log(f'industry_context: built — vertical={vertical!r}, '
        f'{len(key_benchmarks)} benchmark(s), trend_headline={bool(trend_headline)}')
    return result


# ── PHASE 1: TRAFFIC JSON LIFTER ─────────────────────────────────────────────

def lift_traffic_json(research_dir):
    """Lift structured traffic fields from 03-traffic-data.json that the MD parser can't easily extract.
    Returns a dict of fields to merge into the traffic object (MD parser fields take priority for overlap).
    """
    path = os.path.join(research_dir, '03-traffic-data.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding='utf-8') as f:
            tj = json.load(f)
    except Exception:
        return {}

    result = {}

    # organic_search — branded/non-branded split + top keywords
    os_data = tj.get('organic_search')
    if os_data and os_data.get('branded_pct') is not None:
        kws = os_data.get('top_non_branded_keywords', [])
        result['organic_search'] = {
            'share_of_total_pct': os_data.get('share_of_total_pct'),
            'branded_pct': os_data.get('branded_pct'),
            'non_branded_pct': os_data.get('non_branded_pct'),
            'top_non_branded_keywords': kws,
        }
        log(f'traffic (JSON lift): organic_search — branded={os_data.get("branded_pct")}%, nb={os_data.get("non_branded_pct")}%')

    # geo_distribution — top countries with MoM changes
    geo = tj.get('geography', {}).get('top_countries', [])
    if geo:
        result['geo_distribution'] = geo
        log(f'traffic (JSON lift): geo_distribution — {len(geo)} countries')

    # outgoing_traffic — top link destinations
    outgoing = tj.get('outgoing_traffic', {}).get('top_link_destinations', [])
    if outgoing:
        result['outgoing_traffic'] = outgoing
        log(f'traffic (JSON lift): outgoing_traffic — {len(outgoing)} destinations')

    # rankings — global, country, industry
    ranks = tj.get('rankings', {})
    if ranks.get('global_rank'):
        result['rankings'] = ranks
        # Also set convenience top-level fields for KPI tiles
        result['global_rank'] = ranks.get('global_rank')
        result['category_rank'] = ranks.get('industry_rank')
        result['category'] = ranks.get('industry_category')
        log(f'traffic (JSON lift): rankings — global #{ranks.get("global_rank")}, industry #{ranks.get("industry_rank")}')

    # referrals — referring sites + industries
    referrals = tj.get('referrals', {})
    if referrals:
        result['referrals'] = referrals
        industries = referrals.get('top_referring_industries', [])
        if industries:
            result['referring_industries'] = industries
        log(f'traffic (JSON lift): referrals — {len(referrals.get("top_referring_sites", []))} sites, {len(industries)} industries')

    # data_vintage — so the render template's "Data as of {{data_vintage}}" footer is no
    # longer blank. Prefer meta.period (the actual data window the figures cover); fall
    # back to meta.collection_date (when the fetch/scrape ran) if period is absent.
    meta = tj.get('meta', {})
    vintage = meta.get('period') or meta.get('collection_date')
    if vintage:
        result['data_vintage'] = vintage
        log(f'traffic (JSON lift): data_vintage={vintage}')

    return result


# ── PHASE 2: FINANCIAL JSON LIFTER ───────────────────────────────────────────

def lift_financial_json(research_dir):
    """Lift structured financial fields from 08-financial-profile.json.
    Adds analyst_consensus, margins, balance_sheet, digital_revenue to the financials object.
    """
    path = os.path.join(research_dir, '08-financial-profile.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding='utf-8') as f:
            fj = json.load(f)
    except Exception:
        return {}

    result = {}
    fin = fj.get('financials', {})

    # analyst_consensus — parse from string (e.g. "BUY — 33 analysts: 5 Strong Buy...")
    ac_raw = fj.get('analyst_consensus')
    if isinstance(ac_raw, str) and ac_raw.strip():
        ac = {'raw': ac_raw}
        rating_m = re.search(r'^(STRONG BUY|BUY|HOLD|SELL|STRONG SELL)', ac_raw.strip().upper())
        score_m  = re.search(r'mean score ([\d.]+)', ac_raw, re.IGNORECASE)
        target_m = re.search(r'median price target \$?([\d.]+)', ac_raw, re.IGNORECASE)
        current_m = re.search(r'current \$?([\d.]+)', ac_raw, re.IGNORECASE)
        upside_m = re.search(r'~?(\d+)%\s*implied upside', ac_raw, re.IGNORECASE)
        count_m  = re.search(r'(\d+) analysts', ac_raw, re.IGNORECASE)
        if rating_m:  ac['rating']              = rating_m.group(1)
        if score_m:   ac['mean_score']          = float(score_m.group(1))
        if target_m:  ac['price_target_median'] = float(target_m.group(1))
        if current_m: ac['price_current']       = float(current_m.group(1))
        if upside_m:  ac['upside_pct']          = float(upside_m.group(1))
        if count_m:   ac['analysts_count']      = int(count_m.group(1))
        result['analyst_consensus'] = ac
        log(f'financials (JSON lift): analyst_consensus — {ac.get("rating","?")} {ac.get("analysts_count","?")} analysts, target ${ac.get("price_target_median","?")}')
    elif isinstance(ac_raw, dict):
        result['analyst_consensus'] = ac_raw
        log(f'financials (JSON lift): analyst_consensus — (structured object)')

    # margins
    margins_raw = fin.get('margins', {})
    if margins_raw and margins_raw.get('gross_margin_pct') is not None:
        result['margins'] = {
            'gross_margin_pct':     margins_raw.get('gross_margin_pct') or margins_raw.get('gross_margin_fy2025_10k_pct'),
            'ebitda_margin_pct':    margins_raw.get('ebitda_margin_pct'),
            'operating_margin_pct': margins_raw.get('operating_margin_pct'),
            'net_margin_pct':       margins_raw.get('net_margin_pct'),
            'margin_zone':          fj.get('margin_zone'),
        }
        log(f'financials (JSON lift): margins — gross={result["margins"].get("gross_margin_pct")}%, ebitda={result["margins"].get("ebitda_margin_pct")}%')

    # balance_sheet
    bs = fin.get('balance_sheet', {})
    if bs and bs.get('total_assets'):
        def fmt_b(n):
            if n is None: return None
            return f'${n/1e9:.3f}B'
        result['balance_sheet'] = {
            'total_assets':         bs['total_assets'],
            'total_debt':           bs.get('total_debt'),
            'cash_and_equivalents': bs.get('cash_and_equivalents'),
            'total_assets_fmt':     fmt_b(bs['total_assets']),
            'total_debt_fmt':       fmt_b(bs.get('total_debt')),
            'cash_fmt':             fmt_b(bs.get('cash_and_equivalents')),
        }
        log(f'financials (JSON lift): balance_sheet — assets={result["balance_sheet"]["total_assets_fmt"]}, cash={result["balance_sheet"]["cash_fmt"]}')

    # digital_revenue — latest fiscal year
    dr = fin.get('digital_revenue', {})
    if dr:
        # Find the latest FY key (fy2025, fy2024, etc.)
        fy_keys = sorted([k for k in dr if re.match(r'fy\d{4}', k)], reverse=True)
        if fy_keys:
            latest_key = fy_keys[0]
            latest = dr[latest_key]
            result['digital_revenue'] = {
                'latest_year':      latest_key.upper(),
                'estimated_amount': latest.get('nike_brand_digital_estimated_formatted') or latest.get('digital_revenue_formatted'),
                'pct_of_total':     latest.get('digital_pct_of_total_estimated') or latest.get('nike_brand_digital_pct_of_total_estimated'),
                'yoy_change_pct':   latest.get('nike_brand_digital_yoy_pct') or latest.get('yoy_pct'),
                'confidence':       latest.get('confidence', 'ESTIMATE'),
            }
            log(f'financials (JSON lift): digital_revenue — {latest_key}, {result["digital_revenue"].get("estimated_amount","?")} ({result["digital_revenue"].get("pct_of_total","?")}% of total)')

    # revenue_trend — year-keyed {total_revenue, gross_profit, ebit, ebitda, net_income,
    # operating_income} per fiscal year. Stashed under a private key here; enrich_revenue_3y()
    # (called at merge time in main()) uses it to backfill financials.revenue_3y, which the
    # LLM synthesis pass emits as {year, revenue} ONLY — dropping every other per-year metric
    # even though the raw collector data has them. See docs/workspace fix-and-learn note:
    # producer/renderer field-shape mismatch, not a data-fetch gap.
    revenue_trend = fin.get('revenue_trend')
    if revenue_trend and isinstance(revenue_trend, dict):
        result['_revenue_trend'] = revenue_trend
        log(f'financials (JSON lift): revenue_trend — {len(revenue_trend)} fiscal year(s) available to enrich revenue_3y')

    # data_vintage — collector's fetch timestamp, so the render template's
    # "Data as of {{data_vintage}}" footer is no longer blank.
    collection_date = (fj.get('meta') or {}).get('collection_date')
    if collection_date:
        result['data_vintage'] = collection_date
        log(f'financials (JSON lift): data_vintage={collection_date}')

    return result


# ── PHASE 2b: REVENUE_3Y ENRICHMENT (backfill gross_profit/ebitda/operating_income/net_income) ──

def enrich_revenue_3y(revenue_3y, revenue_trend):
    """Backfill gross_profit/ebitda/operating_income/net_income/net_margin onto each
    financials.revenue_3y entry by MATCHING ON THE DOLLAR VALUE of its 'revenue' field
    against 08-financial-profile.json's revenue_trend (a dict keyed fy2025/fy2024/fy2023...).

    Why match by value and not by year key: the LLM synthesis pass labels revenue_3y
    entries as e.g. "FY2026 (TTM)"/"FY2025"/"FY2024", but revenue_trend's fy2025/fy2024/fy2023
    keys follow the company's SEC fiscal-year numbering (e.g. Lululemon's FY2025 10-K covers
    the period the synthesis pass calls "FY2026 (TTM)"). Joining on the label string produces
    a silent off-by-one; joining on the actual revenue dollar amount (which both sides agree on
    to 3 decimal places) is unambiguous.
    """
    if not revenue_3y or not revenue_trend:
        return revenue_3y, 0

    def fmt_b(n):
        if n is None:
            return None
        return f'${n / 1e9:.3f}B'

    def parse_rev_b(s):
        if not s:
            return None
        m = re.search(r'([\d.]+)\s*B', str(s), re.IGNORECASE)
        return float(m.group(1)) if m else None

    trend_entries = [te for te in revenue_trend.values() if isinstance(te, dict) and te.get('total_revenue')]
    enriched = 0
    for entry in revenue_3y:
        target = parse_rev_b(entry.get('revenue'))
        if target is None:
            continue
        best, best_diff = None, None
        for te in trend_entries:
            diff = abs((te['total_revenue'] / 1e9) - target)
            if best_diff is None or diff < best_diff:
                best, best_diff = te, diff
        # Accept only a close match (within 1% of the target, floor 0.02B) — a loose match
        # would silently attach the wrong fiscal year's figures to an entry.
        if best is not None and best_diff is not None and best_diff <= max(0.02, target * 0.01):
            if entry.get('gross_profit') is None:
                entry['gross_profit'] = fmt_b(best.get('gross_profit'))
            if entry.get('ebitda') is None:
                entry['ebitda'] = fmt_b(best.get('ebitda'))
            if entry.get('operating_income') is None:
                entry['operating_income'] = fmt_b(best.get('operating_income') or best.get('ebit'))
            if entry.get('net_income') is None:
                entry['net_income'] = fmt_b(best.get('net_income'))
            if entry.get('net_margin') is None and best.get('net_income') and best.get('total_revenue'):
                entry['net_margin'] = f"{(best['net_income'] / best['total_revenue']) * 100:.1f}%"
            enriched += 1
    return revenue_3y, enriched


# ── PHASE 3: TECH STACK JSON LIFTER ──────────────────────────────────────────

def lift_techstack_json(research_dir):
    """Lift structured tech stack fields from 02-tech-stack.json.
    Extracts headline, takeaway, ai_search_gap, data_acquisitions, architecture context.
    """
    path = os.path.join(research_dir, '02-tech-stack.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding='utf-8') as f:
            tj = json.load(f)
    except Exception:
        return {}

    result = {}

    # tech_stack_summary — already parsed from MD, but JSON may have a richer version
    summary = tj.get('tech_stack_summary')
    if summary and isinstance(summary, str):
        result['tech_stack_summary'] = summary

    # ai_search_gap — NikeAI-type signal: app has AI search but website does not
    nikeai = tj.get('nikeai_search')
    search_vendor = tj.get('search_vendor', '')
    if nikeai and isinstance(nikeai, dict):
        description = nikeai.get('description', '')
        # web_has_ai = True only if description explicitly says website ALSO has AI
        # Explicit negation patterns like "website...not powered" → False
        web_negation = bool(re.search(r'website[^.]*(?:not|separate|different|does not)', description, re.IGNORECASE))
        web_positive = bool(re.search(r'website[^.]*(?:powered by|uses|has)\s+(?:AI|NeuralSearch|NikeAI)', description, re.IGNORECASE))
        web_has_ai = web_positive and not web_negation
        app_has_ai = True  # field exists implies app has AI
        result['ai_search_gap'] = {
            'app_has_ai':          app_has_ai,
            'web_has_ai':          web_has_ai,
            'app_ai_name':         nikeai.get('launched', '') and 'NikeAI' or 'App AI Search',
            'app_platform':        nikeai.get('platform', ''),
            'app_ai_description':  description,
            'web_search_vendor':   search_vendor,
            'narrative': (
                f'Nike has AI-powered search in the app (NikeAI, launched {nikeai.get("launched","")}) '
                f'but nike.com still runs {search_vendor}. '
                f'The gap between app experience and web experience is a quantified conversion risk.'
                if not web_has_ai else
                f'Nike has AI search in both the app and website.'
            ),
        }
        log(f'tech_stack (JSON lift): ai_search_gap — app_has_ai=True, web_has_ai={web_has_ai}')

    # data_acquisitions — from data_infrastructure
    data_infra = tj.get('data_infrastructure', {})
    acq_raw = data_infra.get('data_acquisitions', [])
    if acq_raw:
        acquisitions = []
        for entry in acq_raw:
            # Format: "Datalogue (2021) — data integration / automated data translation"
            m = re.match(r'([^(]+)\s*\((\d{4})\)\s*[—–-]\s*(.+)', entry)
            if m:
                acquisitions.append({
                    'company': m.group(1).strip(),
                    'year':    int(m.group(2)),
                    'purpose': m.group(3).strip(),
                })
            else:
                acquisitions.append({'company': entry, 'year': None, 'purpose': None})
        if acquisitions:
            result['data_acquisitions'] = acquisitions
            log(f'tech_stack (JSON lift): data_acquisitions — {len(acquisitions)} companies')

    # architecture_notes — frontend framework context
    fe = tj.get('frontend_framework', '')
    cloud = tj.get('cloud_infrastructure', '')
    if fe or cloud:
        notes_parts = []
        if fe:
            notes_parts.append(f'Frontend: {fe}')
        if cloud:
            notes_parts.append(f'Cloud: {cloud}')
        result['architecture_notes'] = '; '.join(notes_parts)

    return result


# ── PHASE 5: HIRING + PARTNER PARSER ─────────────────────────────────────────

def parse_hiring_extended(md_text):
    """Extract extended hiring fields from 09d-hiring-signals.md.
    Returns fields to merge into the hiring object.
    """
    if not md_text:
        return {}
    result = {}

    # total_open_roles
    total_m = re.search(r'Total\s+(?:Jobs?|Roles?|Positions?)\s*:?\s*(\d+)', md_text, re.IGNORECASE)
    if not total_m:
        total_m = re.search(r'(\d+)\s+(?:total|open)\s+(?:jobs?|roles?|positions?)', md_text, re.IGNORECASE)
    if total_m:
        result['total_open_roles'] = int(total_m.group(1))
        log(f'hiring (extended): total_open_roles={result["total_open_roles"]}')

    # icp_roles_count — ICP-relevant roles found
    icp_m = re.search(r'ICP[\s-]+(?:Relevant\s+)?(?:Roles?|Positions?)\s*(?:Found)?\s*:?\s*(\d+)', md_text, re.IGNORECASE)
    if not icp_m:
        icp_m = re.search(r'(\d+)\s+ICP[\s-]+(?:Relevant\s+)?(?:Roles?|Positions?)', md_text, re.IGNORECASE)
    if icp_m:
        result['icp_roles_count'] = int(icp_m.group(1))

    # null_signal_note — when 0 ICP roles, that IS a signal
    icp_count = result.get('icp_roles_count', None)
    if icp_count == 0:
        result['null_signal_note'] = (
            'No ICP-relevant roles (search, personalization, product discovery) found in current job postings. '
            'This is itself a signal: the company is not actively staffing search/personalization capabilities, '
            'meaning incumbent tools may go unchallenged unless an external catalyst (like this audit) forces evaluation. '
            'Use this in outreach: "You\'re not hiring for search — meaning your current stack gets no internal champion. That\'s our opening."'
        )
        log('hiring (extended): null_signal_note set — 0 ICP roles is itself a signal')

    return result


def lift_hiring_roles_json(research_dir):
    """Lift the full classified per-role array from 09d-hiring-classified.json.

    parse_hiring_extended() (above) only ever lifted aggregate scalars
    (total_open_roles, icp_roles_count, top_signals text) — the actual per-role
    list (title, tier, tier_name, icp_score, url, location) that already exists
    upstream in 09d-hiring-classified.json was never carried forward, and
    audit-data.json had nowhere to put it. sectionHiring() in index-template.html
    currently falls back to filtering intelligence_signals for hiring-tagged
    entries, which only ever surfaces ~1 signal regardless of company size.
    Lifting hiring.roles[] here gives the render layer a real array to switch to.
    """
    path = os.path.join(research_dir, '09d-hiring-classified.json')
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding='utf-8') as f:
            hj = json.load(f)
    except Exception:
        return {}

    raw_roles = hj.get('roles') or []
    if not raw_roles:
        return {}

    # Only ICP-relevant tiers (1=Economic Buyer, 2=Technical Buyer, 3=Champion) —
    # tier 4 ("Context") roles are excluded, matching how icp_roles_count is scoped.
    roles = []
    for r in raw_roles:
        if r.get('tier') in (1, 2, 3):
            roles.append({
                'title':     r.get('title'),
                'tier':      r.get('tier'),
                'tier_name': r.get('tier_name'),
                'icp_score': r.get('icp_score'),
                'url':       r.get('url'),
                'location':  r.get('location'),
            })
    roles.sort(key=lambda r: r.get('icp_score') or 0, reverse=True)

    result = {}
    if roles:
        result['roles'] = roles
        log(f'hiring (roles lift): {len(roles)} ICP-tier roles lifted from 09d-hiring-classified.json')

    # total_open_roles / icp_roles_count — ALWAYS derive from this classified JSON
    # (source of truth) rather than trusting parse_hiring_extended()'s markdown-regex
    # extraction, which has been observed matching the WRONG number entirely — e.g.
    # its "N open roles" regex can match a Tier-2 section heading ("Tier 2: Technical
    # Buyer Vacancies (5 open roles)") instead of the document's actual
    # "Total roles in analysis: 13" line, silently producing total_open_roles=5 while
    # icp_roles_count=9 and roles[] has 9 entries — three numbers that all disagree.
    # This override forces all three to agree, since they're computed from the same
    # array. It runs AFTER parse_hiring_extended() is merged (see main()), so it wins.
    result['total_open_roles'] = len(raw_roles)
    result['icp_roles_count'] = len(roles)
    log(f'hiring (roles lift): reconciled total_open_roles={len(raw_roles)}, '
        f'icp_roles_count={len(roles)} (overriding any markdown-regex-derived counts)')
    return result


def parse_partner_extended(md_text):
    """Extract extended partner intel from partner-intel.md.
    Returns fields to merge into the partner_intel object.
    """
    if not md_text:
        return {}
    result = {}

    # Section B2: Potential SI Partners (Investigate) table
    unconfirmed = []
    b2_section = re.search(
        r'(?:B2|Potential SI Partners?|SI Partners?\s+(?:to\s+)?Investigate)[^\n]*\n.*?\|.*?(?:SI Partner|Name)[^\n]*\n.*?\|[-| ]+\|\n((?:\|[^\n]+\n?)+)',
        md_text, re.IGNORECASE | re.DOTALL
    )
    if b2_section:
        for row in b2_section.group(1).strip().splitlines():
            cols = [c.strip() for c in row.split('|') if c.strip()]
            if len(cols) >= 2:
                name = re.sub(r'\*+', '', cols[0]).strip()
                evidence = cols[1].strip()[:300] if len(cols) > 1 else ''
                next_step = cols[2].strip()[:300] if len(cols) > 2 else ''
                if name and name.lower() not in ('si partner', 'name', 'partner'):
                    unconfirmed.append({
                        'name':       name,
                        'evidence':   evidence,
                        'next_step':  next_step,
                        'confidence': 'INVESTIGATE',
                    })
    if unconfirmed:
        result['unconfirmed_partners'] = unconfirmed
        log(f'partner_intel (extended): {len(unconfirmed)} unconfirmed/investigate SI partners')

    # Section C: Sales Action Plan — numbered actions with contact names
    actions = []
    # Match sections headed "Sales Action Plan", "Section C", "Immediate Actions", etc.
    action_section = re.search(
        r'(?:Sales Action Plan|Section C|Immediate Actions?)[^\n]*\n(.*?)(?=\n#{1,3}\s|\Z)',
        md_text, re.IGNORECASE | re.DOTALL
    )
    action_text = action_section.group(1) if action_section else md_text

    # Match numbered or bulleted action items
    action_items = re.findall(
        r'(?:^\d+\.|^[-*])\s+\*\*([^*]+)\*\*:?\s*([^\n]+(?:\n(?!(?:\d+\.|[-*])\s+\*\*).+)*)',
        action_text, re.IGNORECASE | re.MULTILINE
    )
    priority_map = ['immediate', 'immediate', 'secondary', 'secondary', 'long_term']
    for i, (label, body) in enumerate(action_items[:6]):
        body_clean = re.sub(r'\s+', ' ', body.strip())[:300]
        # Extract contact name (FirstName LastName pattern before a comma or dash)
        contact_m = re.search(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', body_clean)
        title_m   = re.search(r'\b(CIO|CTO|CEO|VP|Director|Partner|Lead|Manager)[^,.\n]*', body_clean)
        actions.append({
            'action':        label.strip()[:100],
            'detail':        body_clean,
            'contact_name':  contact_m.group(1) if contact_m else None,
            'contact_title': title_m.group(0)[:80] if title_m else None,
            'priority':      priority_map[min(i, len(priority_map)-1)],
        })
    if actions:
        result['sales_action_plan'] = actions
        log(f'partner_intel (extended): {len(actions)} sales action items')

    # CIO background signal — former employer as warm contact signal
    cio_m = re.search(
        r'CIO[^.\n]*(?:former(?:ly)?|previously|ex-|was at)\s+([A-Z][A-Za-z\s&]+?)(?:[,.\s]|$)',
        md_text, re.IGNORECASE
    )
    if cio_m:
        former = cio_m.group(1).strip().rstrip('.,')
        result['cio_background_signal'] = f'CIO previously at {former} — potential warm introduction via {former} alumni network or Algolia {former} partnership'
        log(f'partner_intel (extended): cio_background_signal — former {former}')

    return result


# ── PHASE 4 (PARTIAL): SIGNAL ENRICHMENT ─────────────────────────────────────

URGENCY_BY_TYPE = {
    'earnings_quote': 8,
    'media_quote':    6,
    'sec_risk':       7,
    'hiring':         7,
    'hiring_signal':  7,
    'funding':        8,
    'news_signal':    5,
    'social_signal':  4,
    'media':          6,
    'competitor':     7,
    'partner':        6,
    'exec':           8,
    'industry-opp':   6,
    'industry-risk':  5,
    'customer':       7,
}

CATEGORY_KEYWORDS = {
    'ai_disruption':          ['ai', 'artificial intelligence', 'machine learning', 'neural', 'generative', 'llm', 'chatgpt'],
    'digital_transformation': ['digital', 'ecommerce', 'online', 'dtc', 'd2c', 'direct-to-consumer', 'website', 'platform'],
    'cost_pressure':          ['revenue', 'decline', 'margin', 'cost', 'layoff', 'restructure', 'tariff', 'headwind'],
    'leadership_change':      ['ceo', 'cto', 'cio', 'coo', 'cmo', 'president', 'appoint', 'hire', 'depart', 'resign', 'exit'],
    'competitive_threat':     ['competitor', 'adidas', 'puma', 'under armour', 'asics', 'market share', 'losing'],
    'tech_investment':        ['invest', 'platform', 'technology', 'infrastructure', 'moderniz', 'upgrade', 'cloud'],
    'expansion':              ['launch', 'expand', 'market', 'international', 'new product', 'growth'],
}

TOPIC_TO_PITCH = {
    'technology_investment':    'Tech investment is confirmed. Algolia fits as the search modernization layer with immediate ROI.',
    'digital_direct_strategy':  'Nike Direct is the recovery play. Algolia makes Nike Direct convert — position as the on-site search that closes the gap between app AI and web.',
    'digital_decline':          'Digital revenue is declining. Algolia is a 4-week conversion recovery lever — no re-platform needed.',
    'ai_strategy':              'AI is on the roadmap. NeuralSearch is the AI search layer that ships this quarter, not next year.',
    'cost_pressure':            'Margin pressure makes ROI-positive tech more attractive. Algolia pays back in <1 quarter.',
    'turnaround':               '"Comeback" language = decisions in flight. Platform evaluations happen now, not after the turnaround completes.',
    'investor_day':             'Investor Day creates urgency. Platform decisions get locked in before the big analyst presentation.',
    'china_risk':               'China headwinds make DTC digital more important, not less. Search quality directly impacts DTC conversion.',
}


_BADGE_LABEL_BY_TYPE = {
    'exec':                  'Executive Signal',
    'media_quote':           'Executive Quote',
    'competitor':            'Competitor Signal',
    'partner':               'Partnership',
    'funding':               'Funding',
    'hiring':                'Hiring Signal',
    'industry-risk':         'Industry Risk',
    'industry-opp':          'Industry Opportunity',
    'digital_transformation':'Digital Transformation',
    'news_signal':           'News',
    'earnings_quote':        'Earnings',
    'leadership_change':     'Leadership Change',
    'cost_pressure':         'Cost Pressure',
    'ai_disruption':         'AI Disruption',
    'tech_investment':       'Tech Investment',
}


def _kw_hit(kw, text):
    """True if keyword-stem kw appears at a word start in text. Start-boundary
    only, so 'ai' matches 'ai'/'ai-native' but NOT 'chairman'/'email', while
    prefixes like 'moderniz'/'appoint' still match their inflected forms."""
    return re.search(r'\b' + re.escape(kw), text) is not None


def enrich_signals(signals):
    """Normalize field names and add urgency_score, category_tag to each signal."""
    if not signals:
        return signals
    for sig in signals:
        sig_type = (sig.get('type') or '').lower()

        # Normalize: 'signal' → 'text' (renderer reads sig.text)
        if not sig.get('text') and sig.get('signal'):
            sig['text'] = sig['signal']

        # Auto-generate badge_label if missing
        if not sig.get('badge_label'):
            sig['badge_label'] = (
                _BADGE_LABEL_BY_TYPE.get(sig_type)
                or sig_type.replace('_', ' ').replace('-', ' ').title()
            )

        text = ' '.join(filter(None, [
            sig.get('text', ''), sig.get('body', ''), sig.get('signal', ''),
            sig.get('relevance', ''), sig.get('badge_label', ''),
        ])).lower()

        # urgency_score — start from type-based default, boost for high-value keywords.
        # _kw_hit uses a start word-boundary so short stems ('ai') do not falsely
        # match inside longer words ('ch-ai-rman') while prefixes ('moderniz',
        # 'appoint') still match their inflections.
        score = URGENCY_BY_TYPE.get(sig_type, 5)
        if any(_kw_hit(w, text) for w in ['leadership', 'ceo', 'cto', 'cio', 'appoint', 'depart', 'resign']):
            score = min(10, score + 2)
        if any(_kw_hit(w, text) for w in ['funding', 'acquisition', 'merger', 'ipo']):
            score = min(10, score + 1)
        if not sig.get('urgency_score'):
            sig['urgency_score'] = score

        # category_tag
        if not sig.get('category_tag'):
            matched = 'strategic_signal'
            for cat, keywords in CATEGORY_KEYWORDS.items():
                if any(_kw_hit(kw, text) for kw in keywords):
                    matched = cat
                    break
            sig['category_tag'] = matched

    return signals


# ── SALES-SIGNAL SYNTHESIS ────────────────────────────────────────────────────
# The deterministic "synthesize hard, first-citizen" pass over the collated
# intelligence_signals[] array. Contract + numbered process live in the SKILL.md
# and docs/sop/sales-signal-synthesis.md. Steps, in order:
#   1. GATHER   — already done upstream (LLM signals + hiring + media lifted into
#                 data['intelligence_signals']). This module operates on that array.
#   2. SCORE    — enrich_signals(): urgency_score (type default + keyword boost)
#                 + category_tag.
#   3. DEDUPE/MERGE — dedupe_merge_signals(): quote signals from the SAME speaker
#                 collapse into ONE grouped signal; individual quotes kept as
#                 nested sub_quotes[]. Conservative: only same-speaker quote types.
#   4. WHY_LEAD — build_why_lead(): one concise line per signal, why an AE leads.
# Cross-cutting: drop empty / placeholder fields (no "—" angle entries).
# CONTRACT: emit clean signals + urgency_score + category_tag + why_lead
# (+ sub_quotes/merged_count on grouped signals). Do NOT hardcode tier
# (RED>=8 / AMBER 6-7 / GREEN<=5) or the top-3 selection — the render derives
# both from urgency_score.

# Values that mean "no data" — never emitted as a field value.
_PLACEHOLDER_VALUES = {
    '', '-', '--', '—', '–', 'n/a', 'na', 'null', 'none', 'tbd', 'todo',
    '[collect_via_skill]', '[collect]', 'unknown', '?',
}

# Quote-type signals are the only ones grouped by speaker (an exec making 5
# statements = ONE priority, not 5 signals). Event signals (news/hiring/etc.)
# each stand alone and are never merged.
_QUOTE_TYPES = {'media_quote', 'earnings_quote', 'executive_quote', 'exec', 'media'}

# category_tag → short human label used to synthesize a grouped headline.
CATEGORY_LABEL = {
    'ai_disruption':          'AI',
    'digital_transformation': 'digital transformation',
    'cost_pressure':          'cost & margin',
    'leadership_change':      'leadership change',
    'competitive_threat':     'competitive',
    'tech_investment':        'tech investment',
    'expansion':              'expansion',
    'strategic_signal':       'strategic',
}

# why_lead: the AE's reason to open with this signal. Category first, type fallback.
WHY_LEAD_BY_CATEGORY = {
    'ai_disruption':          'AI is a stated exec priority — lead with Algolia as the AI-native search layer that ships this quarter.',
    'digital_transformation': 'Digital/DTC is the growth bet — lead with search as the conversion lever on the site they are already investing in.',
    'cost_pressure':          'Margin pressure is on record — lead with ROI-positive search that pays back in under a quarter, no re-platform.',
    'leadership_change':      'New leadership resets the budget cycle — lead now, before status-quo tools get re-committed.',
    'competitive_threat':     'A competitor is named as a threat — lead with the head-to-head search-experience gap.',
    'tech_investment':        'Tech investment is confirmed — lead with Algolia as the search modernization layer with immediate ROI.',
    'expansion':              'Expansion/launch is underway — lead with search that scales across new markets and catalog.',
    'strategic_signal':       'A live strategic signal — lead with how Algolia advances the stated priority.',
}
WHY_LEAD_BY_TYPE = {
    'hiring':        'Open ICP roles signal budget and ownership — lead with the team being built to own search/discovery.',
    'hiring_signal': 'Open ICP roles signal budget and ownership — lead with the team being built to own search/discovery.',
    'news_signal':   'A fresh, dated event — lead with the timing window it opens.',
    'competitor':    'A competitor uses or lacks modern search — lead with the head-to-head gap.',
    'partner':       'A warm partner path exists — lead with the co-sell introduction.',
}


def _is_placeholder(value):
    return isinstance(value, str) and value.strip().lower() in _PLACEHOLDER_VALUES


def drop_placeholder_fields(sig):
    """Return a copy of sig with empty / placeholder string fields removed
    (no bare '—' angle entries). None values and placeholders are dropped;
    numbers, lists and dicts are kept as-is."""
    return {
        k: v for k, v in sig.items()
        if v is not None and not _is_placeholder(v)
    }


def _signal_body(sig):
    """The strongest human-readable body text in a signal, for emptiness checks."""
    for k in ('signal', 'text', 'body', 'headline', 'badge_label', 'quote', 'title', 'relevance'):
        v = sig.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ''


def _ensure_display_fields(sig):
    """Guarantee every signal carries the fields the renderer AND schema need:
      - `text`  — render-audit.ts reads sig.text for hiring/news bars (backfill from signal).
      - `badge_label` — audit_data_schema requires one of title/signal/badge_label/detail;
                        text-only hiring signals would otherwise fail validation.
    Backfill only — never overwrites an existing value."""
    if not sig.get('text') and sig.get('signal'):
        sig['text'] = sig['signal']
    if not sig.get('badge_label'):
        for k in ('title', 'signal', 'text', 'headline'):
            v = sig.get(k)
            if isinstance(v, str) and v.strip():
                sig['badge_label'] = v.strip()[:120]
                break
    return sig


def _short_role(title):
    """Extract a compact role token (CEO/CTO/CIO/…) from a free-text title."""
    t = (title or '').lower()
    for role, needles in (
        ('CEO',       ('chief executive', 'ceo')),
        ('CTO',       ('chief technology', 'chief ai', 'cto')),
        ('CIO',       ('chief information', 'chief digital', 'cio', 'cdo')),
        ('CFO',       ('chief financial', 'cfo')),
        ('COO',       ('chief operating', 'co-coo', 'coo')),
        ('Chairman',  ('chairman',)),
        ('President', ('president',)),
        ('VP',        ('vice president', 'vp ', ' svp', ' evp')),
    ):
        if any(n in t for n in needles):
            return role
    return 'Exec'


def build_why_lead(sig):
    """One concise line: why an AE leads with this signal. Deterministic —
    category_tag first, then signal type, then a safe generic."""
    cat = (sig.get('category_tag') or '').lower()
    if cat in WHY_LEAD_BY_CATEGORY:
        return WHY_LEAD_BY_CATEGORY[cat]
    stype = (sig.get('type') or '').lower()
    if stype in WHY_LEAD_BY_TYPE:
        return WHY_LEAD_BY_TYPE[stype]
    return 'A live buying signal — lead with how it maps to an Algolia search win.'


def dedupe_merge_signals(signals):
    """Collapse quote signals from the SAME speaker into ONE grouped signal.

    Conservative + deterministic: only signals whose type is in _QUOTE_TYPES and
    that carry a non-empty `speaker` are grouped. Everything else (news, hiring,
    competitor, partner, unattributed quotes) passes through untouched, order
    preserved. Within a speaker group:
      - the highest-urgency member becomes the primary (its angle/source lead),
      - a synthesized headline is written: "<role>: <category> priority",
      - every member quote is preserved under sub_quotes[],
      - urgency_score = max member score, merged_count = group size.
    A speaker with only ONE quote is left as a plain signal (no forced grouping).
    """
    if not signals:
        return signals

    groups = {}          # speaker_key -> [members]
    group_order = []     # first-seen order of speaker_keys
    passthrough = []     # (index, signal) for non-grouped signals

    for idx, sig in enumerate(signals):
        stype = (sig.get('type') or '').lower()
        speaker = (sig.get('speaker') or '').strip()
        if stype in _QUOTE_TYPES and speaker:
            key = speaker.lower()
            if key not in groups:
                groups[key] = []
                group_order.append((idx, key))
            groups[key].append(sig)
        else:
            passthrough.append((idx, sig))

    merged_by_first_idx = {}
    for first_idx, key in group_order:
        members = groups[key]
        if len(members) == 1:
            merged_by_first_idx[first_idx] = members[0]
            continue

        primary = max(members, key=lambda s: s.get('urgency_score') or 0)
        merged = dict(primary)

        title = primary.get('speaker_title') or primary.get('title') or ''
        role = _short_role(title)
        cat_label = CATEGORY_LABEL.get(primary.get('category_tag', ''), 'strategic')
        speaker_name = primary.get('speaker', '')

        merged['badge_label'] = f"{role}: {cat_label} priority ({len(members)} sourced statements)"
        merged['merged_count'] = len(members)
        merged['urgency_score'] = max((s.get('urgency_score') or 0) for s in members)
        merged['sub_quotes'] = [
            drop_placeholder_fields({
                'speaker': m.get('speaker', speaker_name),
                'quote': (m.get('quote') or m.get('signal') or m.get('text') or '').strip(),
                'source_url': m.get('source_url', ''),
                'source_name': m.get('source_name') or m.get('publication', ''),
                'source_date': m.get('source_date') or m.get('date', ''),
            })
            for m in members
            if (m.get('quote') or m.get('signal') or m.get('text') or '').strip()
        ]
        merged_by_first_idx[first_idx] = merged

    # Reassemble by original index: grouped signals land at their first-seen
    # position, passthrough signals keep their slots — stable, predictable order.
    passthrough_indexed = sorted(passthrough, key=lambda t: t[0])
    group_first_indexed = sorted(merged_by_first_idx.items(), key=lambda t: t[0])
    combined = []
    gi = gp = 0
    while gi < len(group_first_indexed) or gp < len(passthrough_indexed):
        next_group_idx = group_first_indexed[gi][0] if gi < len(group_first_indexed) else float('inf')
        next_pass_idx = passthrough_indexed[gp][0] if gp < len(passthrough_indexed) else float('inf')
        if next_group_idx <= next_pass_idx:
            combined.append(group_first_indexed[gi][1])
            gi += 1
        else:
            combined.append(passthrough_indexed[gp][1])
            gp += 1
    return combined


def synthesize_signals(signals):
    """The full deterministic sales-signal synthesis pass (steps 2-4 + cleanup).
    GATHER (step 1) happens upstream in main(); this runs on the collated array.
    Idempotent: safe to re-run over already-synthesized data."""
    if not signals:
        return signals

    # cleanup — drop empty / placeholder fields, then drop bodyless signals
    cleaned = [drop_placeholder_fields(s) for s in signals]
    cleaned = [s for s in cleaned if _signal_body(s)]

    # step 2 — score + category
    cleaned = enrich_signals(cleaned)

    # step 3 — dedupe/merge same-speaker quote signals
    cleaned = dedupe_merge_signals(cleaned)

    # merged signals inherit urgency_score already; re-run enrich only to fill any gaps
    cleaned = enrich_signals(cleaned)

    # step 4 — why_lead one-liner per signal + guarantee display/schema fields
    for s in cleaned:
        s['why_lead'] = build_why_lead(s)
        _ensure_display_fields(s)

    return cleaned


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print('Usage: python3 generate-audit-data.py <slug> <workspace_dir>')
        print('  slug: company slug (e.g. dsw)')
        print('  workspace_dir: company folder (e.g. ~/audits/DSW)')
        sys.exit(1)

    slug = sys.argv[1]
    workspace = sys.argv[2].rstrip('/')

    deliverables_dir = os.path.join(workspace, 'deliverables')
    research_dir = os.path.join(workspace, 'research')
    data_path = os.path.join(deliverables_dir, f'{slug}-audit-data.json')

    print(f'\n🔧 generate-audit-data.py — patching {slug}-audit-data.json\n')

    # Load existing LLM-generated JSON (or empty dict if none exists)
    if os.path.exists(data_path):
        with open(data_path) as f:
            data = json.load(f)
        log(f'Loaded existing {slug}-audit-data.json ({os.path.getsize(data_path):,} bytes)')
    else:
        data = {}
        log(f'No existing JSON found — creating from scratch')

    patch_count = 0

    # ── Patch: tech_stack ────────────────────────────────────────────────────
    ts_text = read_file(os.path.join(research_dir, '02-tech-stack.md'))
    if ts_text:
        ts_parsed = parse_tech_stack(ts_text)
        if ts_parsed:
            existing_ts = data.get('tech_stack', {}) or {}
            # Only patch fields we successfully parsed
            for field, val in ts_parsed.items():
                existing_ts[field] = val
                patch_count += 1
            data['tech_stack'] = existing_ts
            log(f'tech_stack: patched {len(ts_parsed)} fields')
    else:
        log('tech_stack: 02-tech-stack.md not found — skipping')

    # ── Patch: traffic ───────────────────────────────────────────────────────
    tr_text = read_file(os.path.join(research_dir, '03-traffic-data.md'))
    if tr_text:
        tr_parsed = parse_traffic(tr_text)
        if tr_parsed:
            existing_tr = data.get('traffic', {}) or {}
            for field, val in tr_parsed.items():
                if val is not None:
                    existing_tr[field] = val
                    patch_count += 1
            data['traffic'] = existing_tr
            log(f'traffic: patched {len(tr_parsed)} fields')
    else:
        log('traffic: 03-traffic-data.md not found — skipping')

    # ── Patch: competitors ───────────────────────────────────────────────────
    comp_text = read_file(os.path.join(research_dir, '04-competitors.md'))
    if comp_text:
        comp_parsed = parse_competitors(comp_text)
        if comp_parsed:
            data['competitors'] = comp_parsed
            patch_count += len(comp_parsed)
    else:
        log('competitors: 04-competitors.md not found — skipping')

    # ── Patch: score ─────────────────────────────────────────────────────────
    score_text = read_file(os.path.join(research_dir, '10-scoring-matrix.md'))
    if score_text:
        score_parsed = parse_score(score_text)
        if score_parsed and len(score_parsed.get('breakdown', {})) >= 8:
            data['score'] = score_parsed
            patch_count += 1
            log(f"score: patched — overall={score_parsed['overall']}, {len(score_parsed['breakdown'])} areas")
        elif score_parsed:
            # Partial — only patch what we have
            existing_score = data.get('score', {}) or {}
            for field, val in score_parsed.items():
                # `is not None` (not truthy) so a legitimate 0 for critical_count/
                # moderate_count/low_count still gets patched in on a partial parse.
                if val is not None:
                    existing_score[field] = val
            data['score'] = existing_score
            log(f"score: partial patch — {len(score_parsed.get('breakdown', {}))} areas found")
    else:
        log('score: 10-scoring-matrix.md not found — skipping')

    # ── Patch: traffic (Phase 1 — JSON lift for organic_search, geo, outgoing, rankings, referrals) ─
    tr_json = lift_traffic_json(research_dir)
    if tr_json:
        existing_tr = data.get('traffic', {}) or {}
        added = 0
        for field, val in tr_json.items():
            if val is not None and field not in existing_tr:  # MD parser fields take priority
                existing_tr[field] = val
                added += 1
        data['traffic'] = existing_tr
        if added:
            patch_count += added
            log(f'traffic (Phase 1 JSON lift): added {added} new fields')

    # ── Patch: financials (Phase 2 — analyst_consensus, margins, balance_sheet, digital_revenue) ─
    fin_json = lift_financial_json(research_dir)
    if fin_json:
        existing_fin = data.get('financials', {}) or {}
        added = 0
        for field, val in fin_json.items():
            if val is not None:
                existing_fin[field] = val
                added += 1
        data['financials'] = existing_fin
        if added:
            patch_count += added
            log(f'financials (Phase 2 JSON lift): added {added} fields')

    # ── Enrich: financials.revenue_3y (Phase 2b — backfill gross_profit/ebitda/       ─
    # ── operating_income/net_income/net_margin per year, matched by revenue value) ─
    fin_obj = data.get('financials') or {}
    revenue_trend_for_enrich = fin_obj.pop('_revenue_trend', None)
    if revenue_trend_for_enrich and fin_obj.get('revenue_3y'):
        fin_obj['revenue_3y'], n_enriched = enrich_revenue_3y(fin_obj['revenue_3y'], revenue_trend_for_enrich)
        data['financials'] = fin_obj
        if n_enriched:
            patch_count += n_enriched
            log(f'financials: enriched {n_enriched} revenue_3y year(s) with gross_profit/ebitda/operating_income/net_income/net_margin')
    elif '_revenue_trend' in (data.get('financials') or {}):
        data['financials'].pop('_revenue_trend', None)  # never leak this internal key into the output

    # ── Patch: financials.roi_scenarios.{conservative,moderate}.value/value_num +      ─
    # ── financials.total_digital_revenue — deterministic re-derivation from the       ─
    # ── authoritative source strings (roi_conservative/roi_moderate/d2c_digital_revenue) ─
    # Root cause (JBL 2026-07-01): the LLM hand-types roi_scenarios[*].value and
    # total_digital_revenue as separate fields from the authoritative strings it also
    # writes (roi_conservative/roi_moderate/d2c_digital_revenue) — and was observed
    # dropping the leading digit ("8.4M" vs authoritative "$18.4M/year"; "82M" vs
    # authoritative "$182M"). Never trust the hand-written value: regex-extract the
    # full number+unit from the authoritative string every time. `aggressive` has no
    # authoritative roi_aggressive source field (known gap — see factcheck manifest
    # "ROI Scenario Gap" AE-action item), so it is left as the LLM wrote it.
    fin_obj = data.get('financials') or {}
    roi_scenarios = fin_obj.get('roi_scenarios') or {}
    scenario_sources = {
        'conservative': fin_obj.get('roi_conservative'),
        'moderate': fin_obj.get('roi_moderate'),
        'aggressive': fin_obj.get('roi_aggressive'),
    }
    roi_fixed = 0
    for scenario, source_str in scenario_sources.items():
        value, value_num = parse_money_amount(source_str)
        if value is None:
            continue
        existing = roi_scenarios.get(scenario) or {}
        if existing.get('value') != value or existing.get('value_num') != value_num:
            existing['value'] = value
            existing['value_num'] = value_num
            existing.setdefault('label', scenario.capitalize())
            roi_scenarios[scenario] = existing
            roi_fixed += 1
    if roi_scenarios:
        fin_obj['roi_scenarios'] = roi_scenarios
        data['financials'] = fin_obj
        if roi_fixed:
            patch_count += roi_fixed
            log(f'financials: corrected {roi_fixed} roi_scenarios value(s) from authoritative roi_conservative/roi_moderate strings')

    td_value, _td_value_num = parse_money_amount(fin_obj.get('d2c_digital_revenue'))
    if td_value is not None and fin_obj.get('total_digital_revenue') != td_value:
        log(f'financials: corrected total_digital_revenue "{fin_obj.get("total_digital_revenue")}" '
            f'-> "{td_value}" (from authoritative d2c_digital_revenue)')
        fin_obj['total_digital_revenue'] = td_value
        data['financials'] = fin_obj
        patch_count += 1

    # ── Patch: tech_stack (Phase 3 — ai_search_gap, data_acquisitions, architecture_notes) ─
    ts_json = lift_techstack_json(research_dir)
    if ts_json:
        existing_ts = data.get('tech_stack', {}) or {}
        added = 0
        for field, val in ts_json.items():
            if val is not None and field not in existing_ts:  # MD parser takes priority for overlap
                existing_ts[field] = val
                added += 1
        data['tech_stack'] = existing_ts
        if added:
            patch_count += added
            log(f'tech_stack (Phase 3 JSON lift): added {added} fields')

    # ── Patch: hiring (Phase 5 — extended fields: total_open_roles, icp_roles_count, null_signal_note) ─
    hiring_text = read_file(os.path.join(research_dir, '09d-hiring-signals.md'))
    hiring_ext = parse_hiring_extended(hiring_text)
    if hiring_ext:
        existing_hiring = data.get('hiring', {}) or {}
        added = 0
        for field, val in hiring_ext.items():
            if val is not None:
                existing_hiring[field] = val
                added += 1
        data['hiring'] = existing_hiring
        if added:
            patch_count += added

    # ── Patch: hiring.roles (per-role array for a future sectionHiring() card list) ─
    hiring_roles_ext = lift_hiring_roles_json(research_dir)
    if hiring_roles_ext:
        existing_hiring = data.get('hiring', {}) or {}
        existing_hiring.update(hiring_roles_ext)
        data['hiring'] = existing_hiring
        patch_count += 1

        # ── Patch: hiring.summary — correct the LLM-synthesized narrative string,
        # which is never validated against the deterministic counts above and has
        # been observed stating the RAW total ("13 ICP-relevant open roles") instead
        # of the tier-filtered ICP count (9) — the module's own tiering explicitly
        # excludes tier-4 "Context" roles from ICP relevance, so quoting the raw
        # total as "ICP-relevant" overstates buying-committee size to the reader
        # (this string is quoted verbatim into ae-precall-brief.md,
        # strategic-signal-brief.md, and the published "Why Act Now" tile).
        icp_n = hiring_roles_ext.get('icp_roles_count')
        total_n = hiring_roles_ext.get('total_open_roles')
        summary = existing_hiring.get('summary')
        # Idempotency guard: strip any parenthetical this same patch step added on a
        # prior run before re-substituting, so re-running generate-audit-data.py on an
        # already-patched JSON never stacks "(of N total scraped)" more than once.
        if icp_n is not None and total_n is not None and isinstance(summary, str) and summary.strip():
            summary = re.sub(r'\s*\(of \d+ total scraped\)', '', summary)
            fixed_summary, n_subs = re.subn(
                r'\d+\s+ICP-relevant open roles',
                f'{icp_n} ICP-relevant open roles (of {total_n} total scraped)',
                summary, count=1, flags=re.IGNORECASE
            )
            if n_subs:
                existing_hiring['summary'] = fixed_summary
                data['hiring'] = existing_hiring
                log(f'hiring: corrected summary ICP-count wording to "{icp_n} ICP-relevant '
                    f'open roles (of {total_n} total scraped)"')

    # ── Patch: partner_intel (Phase 5 — unconfirmed_partners, sales_action_plan, cio_background_signal) ─
    partner_text = read_file(os.path.join(research_dir, 'partner-intel.md'))
    partner_ext = parse_partner_extended(partner_text)
    if partner_ext:
        existing_pi = data.get('partner_intel') or {}
        if existing_pi is None:
            existing_pi = {}
        added = 0
        for field, val in partner_ext.items():
            if val is not None:
                existing_pi[field] = val
                added += 1
        data['partner_intel'] = existing_pi
        if added:
            patch_count += added

    # ── Patch: intelligence_signals — emit hiring signals so the hiring section renders ─
    #    (renderer reads ONLY intelligence_signals[type=='hiring']; the rich `hiring`
    #     object alone renders the "not available" fallback)
    hiring_signals = lift_hiring_signals(research_dir, data.get('hiring'))
    if hiring_signals:
        existing_signals = data.get('intelligence_signals', []) or []
        # Idempotent: drop any prior hiring signals, then append fresh
        existing_signals = [s for s in existing_signals if s.get('type') != 'hiring']
        data['intelligence_signals'] = existing_signals + hiring_signals
        patch_count += len(hiring_signals)
        log(f'intelligence_signals: emitted {len(hiring_signals)} hiring signal(s)')

    # ── Patch: intelligence_signals — lift media_quotes from 11-investor-intelligence.json ─
    media_signals = lift_media_quotes(research_dir)
    if media_signals:
        existing_signals = data.get('intelligence_signals', []) or []
        # Avoid duplicates: skip if a media_quote with same source_url already exists
        existing_media_urls = {
            sig.get('source_url') for sig in existing_signals
            if sig.get('type') == 'media_quote'
        }
        new_signals = [
            sig for sig in media_signals
            if sig.get('source_url') not in existing_media_urls
        ]
        if new_signals:
            data['intelligence_signals'] = existing_signals + new_signals
            patch_count += len(new_signals)
            log(f'intelligence_signals: appended {len(new_signals)} media_quote entries '
                f'(total signals: {len(data["intelligence_signals"])})')
        else:
            log('intelligence_signals: all media_quotes already present — skipping duplicates')

    # ── Patch: intelligence_signals — SALES-SIGNAL SYNTHESIS (score → merge → why_lead) ─
    #    Deterministic synthesis pass over the fully collated array:
    #      2. score (urgency_score + category_tag)
    #      3. dedupe/merge same-speaker quote signals into grouped signals w/ sub_quotes
    #      4. why_lead one-liner per signal
    #    + drop empty/placeholder fields. Tier + top-3 stay render-derived from urgency_score.
    if data.get('intelligence_signals'):
        before = len(data['intelligence_signals'])
        data['intelligence_signals'] = synthesize_signals(data['intelligence_signals'])
        after = len(data['intelligence_signals'])
        merged_n = sum(1 for s in data['intelligence_signals'] if s.get('merged_count'))
        log(f'intelligence_signals (synthesis): {before} raw → {after} synthesized '
            f'({merged_n} grouped by speaker); urgency_score + category_tag + why_lead set')

    # ── Patch: industry_context — from industry-intel.json ───────────────────
    industry_ctx = build_industry_context(research_dir)
    data['industry_context'] = industry_ctx  # None → JSON null; dict → object
    if industry_ctx is not None:
        patch_count += 1

    # ── Patch: company_snapshot — portfolio fields from 01-company-context.json ─
    ctx_path = os.path.join(research_dir, '01-company-context.json')
    if os.path.exists(ctx_path):
        try:
            with open(ctx_path, encoding='utf-8') as f:
                ctx_json = json.load(f)

            portfolio_brands   = ctx_json.get('portfolio_brands')    # may be absent (pre-v1.1)
            parent_entity      = ctx_json.get('parent_entity')
            is_conglomerate    = ctx_json.get('is_conglomerate')

            # Graceful: if none of the new fields exist (old audit), set safe defaults
            if portfolio_brands is None and parent_entity is None and is_conglomerate is None:
                log('company_snapshot (portfolio): no portfolio fields in 01-company-context.json — pre-v1.1 audit, setting null/empty')
                portfolio_brands  = []
                parent_entity     = None
                is_conglomerate   = None

            # Compute portfolio_opportunity_note
            if portfolio_brands and len(portfolio_brands) > 1:
                n = len(portfolio_brands)
                portfolio_opportunity_note = f'{n}-brand portfolio = {n}\u00d7 the search optimization surface'
            else:
                portfolio_opportunity_note = None

            # Merge into company_snapshot (preserve LLM synthesis fields already present)
            existing_cs = data.get('company_snapshot', {}) or {}
            existing_cs['parent_entity']             = parent_entity
            existing_cs['is_conglomerate']           = is_conglomerate
            existing_cs['portfolio_brands']          = portfolio_brands if portfolio_brands is not None else []
            existing_cs['portfolio_opportunity_note'] = portfolio_opportunity_note
            data['company_snapshot'] = existing_cs
            patch_count += 1

            brand_count = len(portfolio_brands) if portfolio_brands else 0
            log(f'company_snapshot (portfolio): parent_entity={parent_entity!r}, '
                f'is_conglomerate={is_conglomerate}, {brand_count} portfolio_brand(s)')

        except (json.JSONDecodeError, OSError) as e:
            log(f'company_snapshot (portfolio): could not parse 01-company-context.json — {e} — skipping')
    else:
        log('company_snapshot (portfolio): 01-company-context.json not found — skipping portfolio patch')

    # ── Patch: ae_fields — map LLM field names to renderer field names ────────
    ae = data.get('ae_fields') or {}
    if ae:
        # next_step_action: renderer reads ae.next_step_action; LLM outputs ae.cta, but has
        # also been observed emitting the bare, non-canonical key 'next_step' instead (with
        # real content) while cta stayed empty — broaden the fallback chain to catch it too.
        if not ae.get('next_step_action'):
            ae['next_step_action'] = ae.get('cta') or ae.get('next_step') or ''
        # urgency_label: renderer/template_contract document a fallback chain
        # (ae.urgency_label || ae.urgency || ae.urgency_level.split('—')[0]) that was never
        # actually populated by the LLM synthesis pass — urgency_level ('HIGH') exists but
        # urgency_label does not. Backfill it directly so the header chip isn't blank.
        if not ae.get('urgency_label') and ae.get('urgency_level'):
            ae['urgency_label'] = str(ae['urgency_level']).split('—')[0].strip()
        # talk_track_opener: LLM writes the real opening talk-track text under
        # golden_angle.talk_track, not ae_fields.talk_track_opener — backfill so any
        # consumer reading the canonical ae_fields path finds real content instead of
        # falling through to an empty-string default.
        if not ae.get('talk_track_opener'):
            golden_angle = data.get('golden_angle') or {}
            if golden_angle.get('talk_track'):
                ae['talk_track_opener'] = golden_angle['talk_track']
        # next_step_owner: renderer reads ae.next_step_owner; LLM outputs ae.champion or ae.economic_buyer
        if not ae.get('next_step_owner'):
            ae['next_step_owner'] = ae.get('champion') or ae.get('economic_buyer') or ''
        # next_step_date: default if missing
        if not ae.get('next_step_date'):
            ae['next_step_date'] = 'Within 30 days'
        # opportunity_headline: derive from company name + industry if missing
        if not ae.get('opportunity_headline'):
            cs = data.get('company_snapshot') or {}
            company_name = (data.get('meta') or {}).get('company', '')
            industry = cs.get('industry', '')
            if company_name and industry:
                ae['opportunity_headline'] = f'The {industry} Search Opportunity for {company_name}'
            elif company_name:
                ae['opportunity_headline'] = f'The Search Opportunity for {company_name}'
        # benchmark_proof: derive from best case study if missing
        if not ae.get('benchmark_proof'):
            studies = data.get('case_studies') or []
            if studies:
                best = studies[0]
                result = best.get('result', '')
                company = best.get('company', '')
                product = best.get('product', '')
                url = best.get('url', '')
                if result and company:
                    proof = f'{company}: {result}'
                    if product:
                        proof += f' after deploying Algolia {product}'
                    if url:
                        proof += f' — {url}'
                    ae['benchmark_proof'] = proof
        data['ae_fields'] = ae
        log('ae_fields: mapped cta→next_step_action, champion→next_step_owner, derived opportunity_headline/benchmark_proof/urgency_label/talk_track_opener where missing')

    # ── Patch: company_snapshot.revenue_source / revenue_source_label — same data already ─
    # ── lives on financials.revenue_source(_label) (populated with a real SEC/Yahoo citation) ─
    cs = data.get('company_snapshot') or {}
    fin_for_cs = data.get('financials') or {}
    if cs and (not cs.get('revenue_source')) and fin_for_cs.get('revenue_source'):
        cs['revenue_source'] = fin_for_cs['revenue_source']
        cs['revenue_source_label'] = fin_for_cs.get('revenue_source_label') or cs.get('revenue_source_label')
        data['company_snapshot'] = cs
        patch_count += 1
        log('company_snapshot: backfilled revenue_source/revenue_source_label from financials')

    # ── Ensure meta.generated_by ─────────────────────────────────────────────
    meta = data.get('meta', {}) or {}
    meta['generated_by'] = 'generate-audit-data.py + LLM synthesis'
    meta['patch_date'] = date.today().isoformat()
    data['meta'] = meta

    # ── Pydantic pre-write validation (catches errors BEFORE touching disk) ──
    if _pydantic_available and _pydantic_validate is not None:
        _ok, _errs = _pydantic_validate(data)
        if not _ok:
            print(f'\n🚫 PYDANTIC PRE-WRITE VIOLATIONS ({len(_errs)}) — JSON NOT WRITTEN\n')
            print('Fix these before generate-audit-data.py will write the file:\n')
            for _e in _errs:
                print(f'  ❌ {_e}')
            sys.exit(1)
        else:
            print('  [pydantic] Pre-write validation passed ✅')

    # ── Write patched JSON ───────────────────────────────────────────────────
    os.makedirs(deliverables_dir, exist_ok=True)
    with open(data_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    size = os.path.getsize(data_path)
    print(f'\n✅ Patched {patch_count} fields → {slug}-audit-data.json ({size:,} bytes)')

    # ── Run schema validator ─────────────────────────────────────────────────
    validator = os.path.expanduser('~/.claude/skills/algolia-search-audit/scripts/validate-json-schema.py')
    if os.path.exists(validator):
        import subprocess
        result = subprocess.run(
            ['python3', validator, slug],
            cwd=deliverables_dir,
            capture_output=True, text=True
        )
        print('\n' + result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            print('\n⚠️  Schema validation failed — fix violations before rendering.')
            sys.exit(1)
        else:
            print('Schema validation passed.')
    else:
        log('validate-json-schema.py not found — skipping validation')


if __name__ == '__main__':
    main()
