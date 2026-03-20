#!/usr/bin/env python3
"""
Algolia Audit — Workspace Pre-Flight Validator
Checks every scratchpad file for completeness before Phase 3-5 runs.
Exits 1 if critical gaps found.
Usage: python3 validate-workspace.py $AUDIT_DIR/{CompanyName}/research/
         (also accepts legacy: python3 validate-workspace.py {slug}-audit-workspace/)
"""
import os, sys, glob, re

ws = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
# Derive company slug from workspace path
# New canonical: $AUDIT_DIR/{CompanyName}/research/
# Legacy: {slug}-audit-workspace/
slug = os.path.basename(os.path.dirname(ws)) if os.path.basename(ws) == 'research' else os.path.basename(ws).replace('-audit-workspace','')
print(f"\n══════════════════════════════════════════════════")
print(f"  PRE-FLIGHT VALIDATION — {slug}")
print(f"══════════════════════════════════════════════════\n")

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

# Screenshots
print("\n── Screenshots ───────────────────────────────────")
shot_dir = os.path.join(ws, 'screenshots')
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
