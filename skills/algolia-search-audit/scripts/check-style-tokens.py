#!/usr/bin/env python3
"""
Design System Compliance Checker — blocks render on ANY violation.

Rules enforced:
  1. No raw font-size in any unit (px/rem/em) — must use T.* token
  2. No raw hex color (#RRGGBB) in inline styles or JS strings — must use var(--)
  3. No <pre> tags in template body — use <div style="white-space:pre-wrap"> + explicit font-family

Run before any render. Exits 1 if violations found.
Usage: python3 check-style-tokens.py
"""
import re, sys

template_path = '/Users/arijitchowdhury/.claude/skills/algolia-search-audit/templates/index-template.html'

with open(template_path) as f:
    lines = f.readlines()

violations = []

for i, line in enumerate(lines, 1):
    # Skip CSS :root definitions and CSS rule blocks (lines 1-349)
    if i < 350:
        continue

    # Skip SVG icon definitions (fill= inside <path> or <svg> tags)
    stripped = line.strip()
    if stripped.startswith('<path') or stripped.startswith('<svg') or stripped.startswith('<polygon') or stripped.startswith('<rect') or stripped.startswith('<circle'):
        continue

    # ── Rule 1: No raw font-size in any unit ──────────────────────────────
    styles = re.findall(r'style="([^"]*)"', line)
    for style in styles:
        # Skip SVG text elements (fill: + font-family: Sora = SVG rendering context)
        if "font-family:'Sora'" in style and 'fill:' in style:
            continue
        if re.search(r'font-size:\s*[\d.]+(?:px|rem|em)', style) and '${T.' not in style:
            violations.append(f'  [FONT-SIZE] Line {i}: {style[:90]}')

    # ── Rule 2: No raw hex colors anywhere (inline styles OR JS strings) ──
    # Matches #RRGGBB or #RGB in style attributes and JS template literals
    hex_matches = re.findall(r"(?:style=\"[^\"]*|['\`])#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(?![0-9A-Fa-f])", line)
    if hex_matches:
        # Skip lines that are inside the SIGNAL_COLORS or chColor JS object definitions
        # (those are looked up dynamically and are expected)
        if 'SIGNAL_COLORS' in line or 'const chColor' in line or 'const triggerUrgency' in line:
            continue
        # Skip the donut chart color definitions
        if 'DONUT_COLORS' in line or 'demographics.map' in line:
            continue
        for h in hex_matches:
            violations.append(f'  [RAW-COLOR] Line {i}: #{h} — use var(--name) instead')

    # ── Rule 3: No <pre> tags ─────────────────────────────────────────────
    if re.search(r'<pre[\s>]', line) and 'font-family:' not in line:
        violations.append(f'  [PRE-TAG]   Line {i}: <pre> causes monospace — use <div style="white-space:pre-wrap;font-family:\'Sora\',sans-serif">')

if violations:
    # Deduplicate
    seen = set()
    deduped = []
    for v in violations:
        key = v[:60]
        if key not in seen:
            seen.add(key)
            deduped.append(v)

    print(f'❌ DESIGN SYSTEM VIOLATIONS ({len(deduped)}) — fix before rendering\n')
    for v in deduped[:25]:
        print(v)
    if len(deduped) > 25:
        print(f'  ... and {len(deduped)-25} more')
    print('\nFix guide:')
    print('  Font sizes  → use T.bodySm, T.compact, T.h5, T.eyebrow etc.')
    print('  Colors      → use var(--blue), var(--red-tint), var(--violet) etc.')
    print('  <pre> tags  → use <div style="white-space:pre-wrap;font-family:\'Sora\',sans-serif">')
    print('  See :root{} for all available CSS vars')
    print('  See T object in template for all available font tokens')
    sys.exit(1)
else:
    print(f'✅ Design system check passed — fonts, colors, and markup all compliant')
    sys.exit(0)
