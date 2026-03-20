#!/usr/bin/env python3
"""
Algolia Audit — Workspace Pre-Flight Validator
Checks every scratchpad file for completeness AND that output paths are canonical.
Exits 1 if critical gaps found or paths are wrong.

Usage: python3 validate-workspace.py $AUDIT_DIR/{CompanyName}/research/
         (also accepts legacy: python3 validate-workspace.py {slug}-audit-workspace/)
"""
import os, sys, glob, re

CANONICAL_BASE = os.path.expanduser(
    "~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com"
    "/My Drive/AI/MarketingProject/Algolia Search Audit"
)

ws = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
ws = os.path.realpath(ws)

# Derive company name/slug from workspace path
# New canonical: $AUDIT_DIR/{CompanyName}/research/
# Legacy: {slug}-audit-workspace/
is_canonical = os.path.basename(ws) == 'research'
company_name = os.path.basename(os.path.dirname(ws)) if is_canonical else None
slug = company_name.lower().replace(' ', '-') if company_name else os.path.basename(ws).replace('-audit-workspace','')

print(f"\n══════════════════════════════════════════════════")
print(f"  PRE-FLIGHT VALIDATION — {company_name or slug}")
print(f"══════════════════════════════════════════════════\n")

# ── Canonical path check ──────────────────────────────────────────────────────
print("── Canonical Path Check ──────────────────────────")
if is_canonical:
    expected = os.path.join(CANONICAL_BASE, company_name, 'research')
    if os.path.realpath(ws) == os.path.realpath(expected):
        print(f"  ✓ Workspace at canonical path")
        print(f"    {ws}")
    else:
        print(f"  ⚠️  Workspace is named 'research' but not at canonical base")
        print(f"    Current:  {ws}")
        print(f"    Expected: {expected}")
else:
    legacy_name = os.path.basename(ws)
    print(f"  ❌ WRONG PATH — workspace is at legacy location:")
    print(f"     {ws}")
    print(f"  → Move to canonical: $AUDIT_DIR/{{CompanyName}}/research/")
    print(f"     where AUDIT_DIR = {CANONICAL_BASE}")
    print(f"  ⚠️  Proceeding with validation but output will go to wrong location")

# ── Output paths check ────────────────────────────────────────────────────────
print("\n── Output Path Check ─────────────────────────────")
if is_canonical:
    parent = os.path.dirname(ws)  # $AUDIT_DIR/{CompanyName}/
    deliverables_dir = os.path.join(parent, 'deliverables')
    screenshots_dir  = os.path.join(deliverables_dir, 'screenshots')
    factcheck_dir    = os.path.join(parent, 'factcheck')
    scripts_dir      = os.path.join(parent, 'scripts')

    for label, path in [
        ('deliverables/', deliverables_dir),
        ('deliverables/screenshots/', screenshots_dir),
        ('factcheck/', factcheck_dir),
    ]:
        if os.path.exists(path):
            print(f"  ✓ {label} exists")
        else:
            print(f"  ⚠️  {label} missing — will be created on first write")
else:
    print(f"  ⚠️  Cannot verify output paths — workspace not at canonical location")
print()

PASS = True
missing_steps = []

# Minimum file size thresholds (bytes)
MIN_SIZE = {
    '01': 5000, '02': 5000, '03': 3000, '04': 5000,
    '05': 2000, '06': 4000, '07': 3000, '08': 5000,
    '09': 5000, '10': 3000, '11': 3000, '12': 4000,
}

# Required keywords per file
REQUIRED = {
    '01': [r'revenue|Revenue|employees|Employees'],
    '03': [r'monthly|traffic|visits'],
    '08': [r'ROI|roi|revenue|Revenue'],
    '09': [r'screenshot|Screenshot|query|Query|found|Found'],
    '10': [r'score|Score|severity|Severity'],
    '11': [r'quote|CEO|CFO|CTO|VP|Director|President'],
}

print("── Scratchpad Files ──────────────────────────────")
for i in ['01','02','03','04','05','06','07','08','09','10','11','12']:
    pattern = os.path.join(ws, f"{i}-*.md")
    matches = glob.glob(pattern)
    if not matches:
        print(f"  ❌ MISSING: {i}-*.md  ← Phase 1 step {i} not run")
        missing_steps.append(i)
        PASS = False
        continue

    filepath = matches[0]
    fname = os.path.basename(filepath)
    size = os.path.getsize(filepath)
    threshold = MIN_SIZE.get(i, 2000)

    if size < threshold:
        print(f"  ⚠️  SPARSE: {fname} ({size}b — expected >{threshold}b) — incomplete research")
        missing_steps.append(i)
        PASS = False
        continue

    # Check required keywords
    if i in REQUIRED:
        content = open(filepath, encoding='utf-8', errors='ignore').read()
        pattern_check = REQUIRED[i][0]
        if not re.search(pattern_check, content):
            print(f"  ⚠️  INCOMPLETE: {fname} — missing expected content")
            missing_steps.append(i)
            PASS = False
            continue

    print(f"  ✓ {fname} ({size}b)")

# Screenshots — check canonical deliverables/screenshots/ first, then legacy
print("\n── Screenshots ───────────────────────────────────")
if is_canonical:
    shot_dir = os.path.join(os.path.dirname(ws), 'deliverables', 'screenshots')
    print(f"  (checking canonical: deliverables/screenshots/)")
else:
    shot_dir = os.path.join(ws, 'screenshots')
    print(f"  (checking legacy: workspace/screenshots/)")
shots = glob.glob(os.path.join(shot_dir, '*.png')) if os.path.isdir(shot_dir) else []
if len(shots) < 10:
    print(f"  ❌ SCREENSHOTS: only {len(shots)} found (minimum 10 required)")
    print(f"     Phase 2 browser testing may be incomplete")
    PASS = False
else:
    print(f"  ✓ {len(shots)} screenshots")

# Placeholder text
print("\n── Placeholder Text Check ────────────────────────")
placeholder_pattern = re.compile(r'\[TO BE\]|\[RESEARCH NEEDED\]|\[PLACEHOLDER\]|\[TBD\]')
placeholder_files = []
for f in glob.glob(os.path.join(ws, '*.md')):
    content = open(f, encoding='utf-8', errors='ignore').read()
    if placeholder_pattern.search(content):
        placeholder_files.append(os.path.basename(f))
if placeholder_files:
    print(f"  ⚠️  {len(placeholder_files)} files contain placeholder text:")
    for f in placeholder_files:
        print(f"     → {f}")
    PASS = False
else:
    print(f"  ✓ No placeholder text found")

# Source URL count
print("\n── Source Citations ──────────────────────────────")
url_count = 0
for f in glob.glob(os.path.join(ws, '*.md')):
    content = open(f, encoding='utf-8', errors='ignore').read()
    url_count += len(re.findall(r'https://', content))
if url_count < 20:
    print(f"  ⚠️  Only {url_count} source URLs (expect 20+) — data may lack citations")
    PASS = False
else:
    print(f"  ✓ {url_count} source URLs found")

# Result
print(f"\n══════════════════════════════════════════════════")
if PASS:
    print(f"  ✅ VALIDATION PASSED — safe to proceed to Phase 3-5")
    print(f"══════════════════════════════════════════════════\n")
    sys.exit(0)
else:
    print(f"  ❌ VALIDATION FAILED — fix gaps before Phase 3-5")
    if missing_steps:
        steps_str = ' '.join(missing_steps)
        print(f"\n  Steps needing re-run: {steps_str}")
        print(f"  Fix with: /algolia-audit-research {{url}} --refresh {steps_str}")
    print(f"══════════════════════════════════════════════════\n")
    sys.exit(1)
