#!/usr/bin/env python3
"""
JSON Schema Validator — checks audit-data.json keys match exactly what the template reads.
Blocks render if critical fields are missing or use wrong key names.
Run before render-audit.ts. Exits 1 if violations found.
Usage: python3 validate-json-schema.py {slug}

Now runs Pydantic schema validation FIRST (strict structural checks),
then legacy manual checks for template-specific field name requirements.
Pydantic catches: wrong field names, missing required fields, placeholder text in body,
missing video_script on video touches, missing citations, invalid score keys.
"""
import json, sys, os

# ── Pydantic validation (structural layer) ────────────────────────────────────
from typing import Callable, Optional
_pydantic_validate: Optional[Callable[..., tuple[bool, list[str]]]] = None
_pydantic_available: bool = False
try:
    import sys as _sys
    import os as _os
    _schema_dir = _os.path.dirname(_os.path.abspath(__file__))
    if _schema_dir not in _sys.path:
        _sys.path.insert(0, _schema_dir)
    from audit_data_schema import validate_audit_data as _pydantic_validate
    _pydantic_available = True
except ImportError:
    print("⚠️  audit_data_schema.py not found — Pydantic validation skipped. "
          "Run: python3 audit_data_schema.py to validate schema.")

slug = sys.argv[1] if len(sys.argv) > 1 else None
if not slug:
    print("Usage: python3 validate-json-schema.py {slug}")
    sys.exit(1)

data_path = f'{slug}-audit-data.json'
if not os.path.exists(data_path):
    print(f"❌ {data_path} not found")
    sys.exit(1)

with open(data_path) as f:
    d = json.load(f)

violations = []

def fail(msg: str) -> None: violations.append(f'  ❌ {msg}')
def warn(msg: str) -> None: violations.append(f'  ⚠️  {msg}')

# ── Run Pydantic structural validation FIRST ──────────────────────────────────
# This catches field name mismatches, missing required fields, placeholder text,
# missing video_script on video touches, source notes in email bodies, etc.
# Pydantic errors are BLOCKING — they exit before any legacy checks run.
if _pydantic_available and _pydantic_validate is not None:
    _pydantic_ok, _pydantic_errors = _pydantic_validate(d)
    if not _pydantic_ok:
        print(f'\n🚫 PYDANTIC SCHEMA VIOLATIONS ({len(_pydantic_errors)}) — RENDER BLOCKED\n')
        print('These are structural errors caught before template rendering.')
        print('Fix them first — legacy checks not run until schema is clean.\n')
        for e in _pydantic_errors:
            print(f'  ❌ {e}')
        sys.exit(1)
    else:
        print(f'✅ Pydantic schema validation passed ({slug})')

# ── gap_pairs — template reads these EXACT keys ────────────────────────────────
REQUIRED_GAP_KEYS = ['said_quote','said_attr','found_title','found_evidence','finding_id','algolia_angle']
for i, gap in enumerate(d.get('gap_pairs') or []):
    for key in REQUIRED_GAP_KEYS:
        if not gap.get(key):
            fail(f'gap_pairs[{i}] missing key "{key}" — template reads g.{key} (renders blank)')
    # Catch common wrong key names
    for wrong in ['exec_quote','exec_name','audit_finding','algolia_product','expected_impact']:
        if wrong in gap:
            fail(f'gap_pairs[{i}] uses wrong key "{wrong}" — template ignores this, will render blank')

# ── executives — must have quote_source for citations to render ───────────────
# Canonical field per schema: quote_source (URI). Note: source_url belongs to
# intelligence_signals and traffic objects — NOT executives. Use quote_source here.
for i, e in enumerate(d.get('executives') or []):
    if not e.get('quote_source'):
        fail(f'executives[{i}] ({e.get("name","?")}) missing quote_source — citation will not render')
    if not e.get('quote'):
        fail(f'executives[{i}] ({e.get("name","?")}) missing quote')

# ── golden_angle — must have either talk_track OR competitors_using_algolia ───
ga = d.get('golden_angle') or {}
if not ga.get('talk_track') and not (ga.get('competitors_using_algolia') or []):
    fail('golden_angle has no talk_track AND no competitors_using_algolia — "Who uses Algolia" section renders blank')

# ── competitive_synthesis ─────────────────────────────────────────────────────
cs = d.get('competitive_synthesis') or {}
if not cs.get('matrix_col_labels'):
    fail('competitive_synthesis.matrix_col_labels missing — capability matrix shows Nike/Asics/etc for every company')
if not cs.get('competitor_tiers'):
    fail('competitive_synthesis.competitor_tiers missing — competitor table empty')
pm = cs.get('positioning_matrix') or []
for i, row in enumerate(pm):
    if not row.get('capability'):
        fail(f'positioning_matrix[{i}] missing "capability" key')
    if 'prospect_today' not in row:
        fail(f'positioning_matrix[{i}] missing "prospect_today" key')
    if 'prospect_with_algolia' not in row:
        fail(f'positioning_matrix[{i}] missing "prospect_with_algolia" key')

# ── financials — total_digital_revenue required ───────────────────────────────
fin = d.get('financials') or {}
if not fin.get('total_digital_revenue'):
    fail('financials.total_digital_revenue missing — template falls back to ~$540M default (Brooks Running value)')
if not fin.get('roi_scenarios'):
    fail('financials.roi_scenarios missing — bounce cards show $4.85M/$9.7M/$14.55M defaults')

# ── traffic — format requirements ────────────────────────────────────────────
tr = d.get('traffic') or {}
if not tr.get('top_channels'):
    fail('traffic.top_channels missing — donut chart shows 0%')
elif isinstance(tr['top_channels'], dict):
    fail('traffic.top_channels must be an ARRAY [{source, share}], not an object')
if not (tr.get('device_share') or {}).get('mobile'):
    fail('traffic.device_share.mobile missing — device bar shows nothing')
if not tr.get('demographics'):
    fail('traffic.demographics missing — demographics chart empty')
elif isinstance(tr['demographics'], dict) and not isinstance(tr['demographics'], list):
    # Check if it's the old flat object format
    if 'age_18_24' in tr['demographics']:
        fail('traffic.demographics must be ARRAY [{age_group, pct, color}], not flat object')

# ── tech_stack ────────────────────────────────────────────────────────────────
ts = d.get('tech_stack') or {}
if not ts.get('primary_platform'):
    fail('tech_stack.primary_platform missing')
if not ts.get('full_list'):
    fail('tech_stack.full_list missing — tech stack section shows nothing')

# ── abx_sequence ──────────────────────────────────────────────────────────────
abx = d.get('abx_sequence') or {}
if isinstance(abx, dict):
    touches = abx.get('touches') or []
    contacts = abx.get('contacts') or []
    if not touches:
        fail('abx_sequence.touches empty — ABX sequence section shows nothing')
    else:
        for i, t in enumerate(touches):
            if not t.get('body') and not t.get('message') and not t.get('email_body'):
                warn(f'abx touch {i+1} (T{t.get("touch","?")}) has no body/message — content will be empty')
    if not contacts:
        fail('abx_sequence.contacts empty — no contacts shown in ABX section')
    # Check for CEO as contact
    for c in contacts:
        if any(word in (c.get('title','') or '').lower() for word in ['chief executive','ceo','president & ceo']):
            fail(f'abx contact "{c.get("name","?")}" is CEO — CEOs do not evaluate SaaS tools, use digital/ecommerce decision makers')

# ── strategic_angles — all required fields ────────────────────────────────────
for i, angle in enumerate(d.get('strategic_angles') or []):
    lbl = angle.get('label', f'angle[{i}]')
    if not angle.get('label'):
        fail(f'strategic_angles[{i}] missing label — angle has no name')
    if not angle.get('source'):
        fail(f'strategic_angles[{i}] ("{lbl}") missing source — every angle must cite its trigger signal origin')
    if not angle.get('hook'):
        fail(f'strategic_angles[{i}] ("{lbl}") missing hook — extract verbatim "Pitch angle:" sentence from 06-strategic-context.md')
    if not angle.get('discovery_question'):
        fail(f'strategic_angles[{i}] ("{lbl}") missing discovery_question — extract from 06-strategic-context.md angle evidence')
    if not angle.get('algolia_proof'):
        fail(f'strategic_angles[{i}] ("{lbl}") missing algolia_proof — must cite a verified Algolia case study metric')
    if not isinstance(angle.get('pain_points'), list) or not angle.get('pain_points'):
        fail(f'strategic_angles[{i}] ("{lbl}") pain_points must be a non-empty list — extract bullet evidence from 06-strategic-context.md')
    if not angle.get('objection'):
        fail(f'strategic_angles[{i}] ("{lbl}") missing objection — extract from "Objection Pre-Emption" table in 06-strategic-context.md')
    if not angle.get('objection_counter'):
        fail(f'strategic_angles[{i}] ("{lbl}") missing objection_counter — extract evidence response from "Objection Pre-Emption" table in 06-strategic-context.md')

# ── hiring ────────────────────────────────────────────────────────────────────
hir = d.get('hiring') or {}
if not hir.get('buying_committee'):
    fail('hiring.buying_committee missing — buying committee section empty')

# ── demos — must be a list if present ─────────────────────────────────────────────
demos = d.get('demos')
if demos is not None and not isinstance(demos, list):
    fail('demos field must be a list/array — template calls demos.map() and will crash if not a list')

# ── score recalculation — verify denominator and result are correct ────────
score_data = d.get('score') or {}
breakdown = score_data.get('breakdown') or {}
severity = score_data.get('breakdown_severity') or {}
overall = score_data.get('overall')

if breakdown and severity and overall is not None:
    weight_map = {'HIGH': 2.0, 'MEDIUM': 1.0, 'LOW': 0.5}
    total_weighted = 0.0
    total_weight = 0.0
    for area, score_val in breakdown.items():
        sev = severity.get(area, 'MEDIUM')
        w = weight_map.get(sev, 1.0)
        total_weighted += score_val * w
        total_weight += w

    if total_weight > 0:
        correct_score = round(total_weighted / total_weight, 2)
        reported_score = round(float(overall), 2)
        if abs(correct_score - reported_score) > 0.1:
            fail(f'score.overall is {reported_score} but recalculation gives {correct_score} '
                 f'(weighted sum {total_weighted:.1f} / weight total {total_weight:.1f}) — '
                 f'check scoring matrix denominator')

# ── new fields — tab_subtitles is BLOCKING (blank tabs = broken UX) ───────
if not d.get('tab_subtitles'):
    fail('tab_subtitles missing — SPA shows generic tab names. Every audit MUST set custom subtitles (BLOCKING)')
if not d.get('recommended_first_play'):
    warn('recommended_first_play missing — Summary highlights grid will show 3 cards instead of 4')
if d.get('partner_intel') is None:
    warn('partner_intel missing — Partner section will be hidden in Account tab (graceful degradation OK)')

# ── CHECK 1: 11-investor-intelligence.json — media_quotes[] validation ────────
# File lives at ../research/ relative to deliverables/ (where audit-data.json lives).
# Absent media_quotes key = acceptable (pre-v1.1 audit), so all checks are WARNINGs.
investor_path = os.path.join('..', 'research', '11-investor-intelligence.json')
investor_data = None
media_quotes = []
if os.path.exists(investor_path):
    try:
        with open(investor_path, encoding='utf-8') as _f:
            investor_data = json.load(_f)
        media_quotes = investor_data.get('media_quotes') or []
    except (json.JSONDecodeError, OSError) as _e:
        warn(f'11-investor-intelligence.json could not be parsed: {_e}')

if investor_data is not None and media_quotes:
    print(f'  ℹ️  media_quotes: {len(media_quotes)} entr{"y" if len(media_quotes) == 1 else "ies"} found in 11-investor-intelligence.json')
    for _i, _mq in enumerate(media_quotes):
        _url = _mq.get('source_url')
        if not _url:
            warn(f'media_quotes[{_i}] ({_mq.get("speaker","?")}) source_url is null or missing — citation unverifiable')
        _quote = _mq.get('quote') or ''
        if '[COLLECT_VIA_SKILL]' in _quote:
            warn(f'media_quotes[{_i}] ({_mq.get("speaker","?")}) quote contains [COLLECT_VIA_SKILL] — enrichment not run')
        _context = _mq.get('context')
        if not _context:
            warn(f'media_quotes[{_i}] ({_mq.get("speaker","?")}) context is null — should be filled by SKILL enrichment')

# ── CHECK 2: {slug}-audit-data.json — intelligence_signals[] type validation ─
VALID_SIGNAL_TYPES = {'earnings_quote', 'media_quote', 'sec_risk', 'hiring_signal', 'social_signal', 'news_signal'}
for _i, _sig in enumerate(d.get('intelligence_signals') or []):
    _stype = _sig.get('type')
    if _stype and _stype not in VALID_SIGNAL_TYPES:
        warn(f'intelligence_signals[{_i}] type "{_stype}" is not a valid type — must be one of: {", ".join(sorted(VALID_SIGNAL_TYPES))}')
    if _stype == 'media_quote':
        if not _sig.get('source_url'):
            warn(f'intelligence_signals[{_i}] type="media_quote" has null source_url — citation will not render')
        if not _sig.get('publication'):
            warn(f'intelligence_signals[{_i}] type="media_quote" has null publication — source label will be empty')

# ── CHECK 3: Cross-file consistency — media_quotes lifted to audit-data.json ─
# If media_quotes exist in 11-investor-intelligence.json but no media_quote entries
# appear in intelligence_signals, generate-audit-data.py was not run after collection.
if media_quotes:
    _media_signal_count = sum(
        1 for _s in (d.get('intelligence_signals') or [])
        if _s.get('type') == 'media_quote'
    )
    if _media_signal_count == 0:
        warn(
            f'{len(media_quotes)} media_quote(s) exist in 11-investor-intelligence.json '
            f'but none appear in intelligence_signals[] — run generate-audit-data.py to lift them'
        )

# ── CHECK 4: industry-intel.json — field completeness ────────────────────────
# Absent file is acceptable for older audits — all checks are WARNINGs (non-blocking).
# File lives at ../research/ relative to deliverables/ (where audit-data.json lives).
VALID_COLLECTION_METHODS = {'tavily_advanced', 'websearch_fallback'}
industry_intel_path = os.path.join('..', 'research', 'industry-intel.json')
industry_intel_data = None
industry_benchmarks = []
if os.path.exists(industry_intel_path):
    try:
        with open(industry_intel_path, encoding='utf-8') as _f:
            industry_intel_data = json.load(_f)
    except (json.JSONDecodeError, OSError) as _e:
        warn(f'industry-intel.json could not be parsed: {_e}')

if industry_intel_data is not None:
    # primary_market required for geographic locale targeting
    if not industry_intel_data.get('primary_market'):
        warn('industry-intel.json: primary_market is null or missing — required for geographic locale targeting')

    # benchmarks array
    industry_benchmarks = industry_intel_data.get('benchmarks') or []
    if 'benchmarks' not in industry_intel_data or not industry_benchmarks:
        warn('industry-intel.json: benchmarks key missing or empty array — no benchmark data available')
    else:
        for _i, _bm in enumerate(industry_benchmarks):
            # FACT confidence requires a verifiable source_url
            if _bm.get('confidence') == 'FACT' and not _bm.get('source_url'):
                warn(f'industry-intel.json benchmarks[{_i}] confidence="FACT" but source_url is null — FACT claims must be verifiable')
            # Stale data guard — collection script should filter, this is a backup
            _age = _bm.get('age_months')
            if _age is not None and _age > 24:
                warn(f'industry-intel.json benchmarks[{_i}] age_months={_age} exceeds 24 — stale benchmark, should have been excluded at collection')

    # algolia_angle — absence means SKILL enrichment step was skipped
    if not industry_intel_data.get('algolia_angle'):
        warn('industry-intel.json: algolia_angle is null — SKILL enrichment step may have been skipped')

    # collection_method — must be a known value
    _cm = industry_intel_data.get('collection_method')
    if _cm not in VALID_COLLECTION_METHODS:
        warn(
            f'industry-intel.json: collection_method="{_cm}" is not valid — '
            f'must be one of: {", ".join(sorted(VALID_COLLECTION_METHODS))}'
        )

    # INFO: print counts of key arrays
    _trends = industry_intel_data.get('trends') or []
    _expert_quotes = industry_intel_data.get('expert_quotes') or []
    print(
        f'  ℹ️  industry-intel.json: {len(industry_benchmarks)} benchmark(s), '
        f'{len(_trends)} trend(s), {len(_expert_quotes)} expert_quote(s)'
    )

# ── CHECK 5: {slug}-audit-data.json — industry_context field ─────────────────
# Only runs when industry_context key is present AND non-null.
_ic = d.get('industry_context')
if _ic is not None:
    _key_benchmarks = _ic.get('key_benchmarks') or []
    if not _key_benchmarks:
        warn('audit-data.json industry_context: key_benchmarks is empty — required for SPA render')
    else:
        for _i, _kb in enumerate(_key_benchmarks):
            if not _kb.get('source_url'):
                warn(f'audit-data.json industry_context.key_benchmarks[{_i}] source_url is null — citation will not render')

    if not _ic.get('algolia_angle'):
        warn('audit-data.json industry_context: algolia_angle is null — required for SPA render')

    if not _ic.get('primary_market'):
        warn('audit-data.json industry_context: primary_market is null or missing')

# ── CHECK 6: Cross-file consistency — industry data lifted to audit-data.json ─
# If industry-intel.json has non-empty benchmarks[] but audit-data.json has no
# industry_context, generate-audit-data.py was not run after industry collection.
if industry_benchmarks and d.get('industry_context') is None:
    warn(
        f'{len(industry_benchmarks)} benchmark(s) exist in industry-intel.json '
        f'but industry_context in audit-data.json is null — run generate-audit-data.py to lift industry data'
    )

# ── CHECK 7: 01-company-context.json — portfolio_brands[] field validation ───
# Only runs when file is present AND portfolio_brands key exists.
# Absent key in older audits is acceptable (pre-v1.1) — all checks are WARNINGs.
company_ctx_path = os.path.join('..', 'research', '01-company-context.json')
company_ctx_data = None
if os.path.exists(company_ctx_path):
    try:
        with open(company_ctx_path, encoding='utf-8') as _f:
            company_ctx_data = json.load(_f)
    except (json.JSONDecodeError, OSError) as _e:
        warn(f'01-company-context.json could not be parsed: {_e}')

if company_ctx_data is not None and 'portfolio_brands' in company_ctx_data:
    _portfolio_brands = company_ctx_data.get('portfolio_brands') or []
    if _portfolio_brands:
        print(
            f'  ℹ️  01-company-context.json: portfolio_brands has {len(_portfolio_brands)} entr'
            f'{"y" if len(_portfolio_brands) == 1 else "ies"}'
        )
        _has_audit_target = False
        for _i, _brand in enumerate(_portfolio_brands):
            if not _brand.get('source'):
                warn(
                    f'portfolio_brands[{_i}] ({_brand.get("name","?")}) missing "source" field — '
                    f'every brand entry must cite where the portfolio data came from'
                )
            if not _brand.get('domain'):
                warn(
                    f'portfolio_brands[{_i}] ({_brand.get("name","?")}) missing "domain" field — '
                    f'required for SPA render and cross-reference with audit domain'
                )
            if _brand.get('is_audit_target'):
                _has_audit_target = True
        if not _has_audit_target:
            warn(
                'portfolio_brands has entries but no entry has is_audit_target=true — '
                'exactly one brand should match the audit domain'
            )

# ── CHECK 8: audit-data.json → company_snapshot.portfolio_brands ─────────────
# Validates portfolio fields lifted from 01-company-context.json by generate-audit-data.py.
_cs_portfolio = (d.get('company_snapshot') or {}).get('portfolio_brands')
if _cs_portfolio is not None and len(_cs_portfolio) > 0:
    print(
        f'  ℹ️  company_snapshot.portfolio_brands: {len(_cs_portfolio)} brand'
        f'{"s" if len(_cs_portfolio) != 1 else ""} — '
        + ', '.join(_b.get('name', '?') for _b in _cs_portfolio)
    )
    for _i, _brand in enumerate(_cs_portfolio):
        if not _brand.get('source'):
            warn(
                f'company_snapshot.portfolio_brands[{_i}] ({_brand.get("name","?")}) '
                f'missing "source" field — citation not verifiable'
            )

# ── CITATION BASELINE RULE (applies across all sections) — ALL BLOCKING ────────
# No citation = no data. These are BLOCKING failures, not warnings.
# An uncited claim in a client report is a liability, not an inconvenience.

# executives — every quote needs quote_source
for _i, _exec in enumerate(d.get('executives') or []):
    if _exec.get('quote') and not _exec.get('quote_source'):
        fail(f'executives[{_i}] ({_exec.get("name","?")}) has quote but no quote_source URL — citation required (BLOCKING)')

# intelligence_signals — every signal needs source_url
for _i, _sig in enumerate(d.get('intelligence_signals') or []):
    if (_sig.get('detail') or _sig.get('quote') or _sig.get('body')) and not _sig.get('source_url'):
        fail(f'intelligence_signals[{_i}] ("{(_sig.get("title") or _sig.get("badge_label","?"))[:40]}") has content but no source_url (BLOCKING)')

# strategic_angles — every angle needs source
for _i, _ang in enumerate(d.get('strategic_angles') or []):
    if not _ang.get('source'):
        fail(f'strategic_angles[{_i}] ("{_ang.get("label","?")[:40]}") missing source — citation required (BLOCKING)')
    if not _ang.get('algolia_proof'):
        fail(f'strategic_angles[{_i}] ("{_ang.get("label","?")[:40]}") missing algolia_proof — proof required (BLOCKING)')

# icp_mapping.priority_to_product — proof_url required when proof_company named
for _i, _p in enumerate((d.get('icp_mapping') or {}).get('priority_to_product') or []):
    if _p.get('proof_company') and not _p.get('proof_url'):
        fail(f'icp_mapping.priority_to_product[{_i}] has proof_company="{_p.get("proof_company")}" but no proof_url (BLOCKING)')
    if not _p.get('evidence') and not _p.get('exact_quote'):
        fail(f'icp_mapping.priority_to_product[{_i}] missing evidence/exact_quote — BDR cannot ask question without supporting citation (BLOCKING)')

# findings — case_study_url required when company named; impact_stat_source required
for _i, _f in enumerate(d.get('findings') or []):
    if _f.get('algolia_case_study_company') and not _f.get('algolia_case_study_url'):
        fail(f'findings[{_i}] ("{_f.get("title","?")[:40]}") has case_study_company but no case_study_url (BLOCKING)')
    if _f.get('impact_stat') and not _f.get('impact_stat_source'):
        fail(f'findings[{_i}] ("{_f.get("title","?")[:40]}") has impact_stat but no impact_stat_source — remove stat or cite it (BLOCKING)')

# ── finding enrichment — BLOCKING checks ─────────────────────────────────────
for _i, _f in enumerate(d.get('findings') or []):
    _ib = _f.get('industry_benchmark')
    if _ib is not None:
        if not _ib.get('source') or not str(_ib['source']).strip():
            fail(
                f'findings[{_i}] ("{_f.get("title","?")[:40]}") '
                f'industry_benchmark.source is empty — every benchmark must cite source URL (BLOCKING)'
            )
    _ad = _f.get('anxiety_driver')
    if _ad is not None:
        if not _ad.get('quantified_impact') or not str(_ad['quantified_impact']).strip():
            fail(
                f'findings[{_i}] ("{_f.get("title","?")[:40]}") '
                f'anxiety_driver.quantified_impact is empty — no naked anxiety claims (BLOCKING)'
            )

# case_studies — url and result required
for _i, _cs in enumerate(d.get('case_studies') or []):
    if not _cs.get('url'):
        fail(f'case_studies[{_i}] ({_cs.get("company","?")}) missing url — every case study must link to source (BLOCKING)')
    if not _cs.get('result'):
        fail(f'case_studies[{_i}] ({_cs.get("company","?")}) missing result metric — every case study must have measurable proof (BLOCKING)')

errors = [v for v in violations if v.startswith("  ❌")]
warnings = [v for v in violations if v.startswith("  ⚠️")]

if warnings:
    print(f'⚠️  {len(warnings)} warning(s) for {slug}:')
    for w in warnings:
        print(w)

if errors:
    print(f'\n❌ JSON SCHEMA VIOLATIONS ({len(errors)}) for {slug}\n')
    for e in errors:
        print(e)
    print('\nFix key names to match what the template reads. Wrong keys render as blank sections.')
    sys.exit(1)
else:
    print(f'✅ JSON schema valid — all template keys present for {slug}')
    sys.exit(0)
