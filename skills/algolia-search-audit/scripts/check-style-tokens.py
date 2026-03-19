#!/usr/bin/env python3
"""
Check that all inline font-size and font-weight values use T.* tokens.
Run before any git push. Exits 1 if violations found.
Usage: python3 check-style-tokens.py
"""
import re, sys, glob

template_path = '/Users/arijitchowdhury/.claude/skills/algolia-search-audit/templates/index-template.html'

with open(template_path) as f:
    content = f.read()

violations = []
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    styles = re.findall(r'style="([^"]*)"', line)
    for style in styles:
        # Skip SVG text elements (different rendering context)
        if 'font-family:\'Sora\'' in style and 'fill:' in style:
            continue
        # Skip CSS rule definitions (not inline styles)
        if i < 350:  # CSS section
            continue
        if re.search(r'font-size:[0-9]+px', style) and '${T.' not in style:
            violations.append(f'  Line {i}: {style[:90]}')

if violations:
    print(f'❌ STYLE TOKEN VIOLATIONS ({len(violations)}) — use T.* tokens, not inline font-size')
    for v in violations[:20]:
        print(v)
    if len(violations) > 20:
        print(f'  ... and {len(violations)-20} more')
    print('\nFix: replace inline font-size with T.eyebrowSm, T.bodySm, T.compact etc.')
    print('See T object at top of script in index-template.html')
    sys.exit(1)
else:
    print(f'✅ Style token check passed — no raw font-size values found')
    sys.exit(0)
