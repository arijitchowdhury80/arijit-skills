#!/usr/bin/env python3
"""
JSON Schema Validator — checks audit-data.json keys match exactly what the template reads.
Blocks render if critical fields are missing or use wrong key names.
Run before render-audit.ts. Exits 1 if violations found.
Usage: python3 validate-json-schema.py {slug}
"""
import json, sys, os

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

def fail(msg): violations.append(f'  ❌ {msg}')
def warn(msg): violations.append(f'  ⚠️  {msg}')

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

# ── executives — must have source_url for citations to render ─────────────────
for i, e in enumerate(d.get('executives') or []):
    if not e.get('source_url'):
        fail(f'executives[{i}] ({e.get("name","?")}) missing source_url — citation will not render')
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

# ── hiring ────────────────────────────────────────────────────────────────────
hir = d.get('hiring') or {}
if not hir.get('buying_committee'):
    fail('hiring.buying_committee missing — buying committee section empty')

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
