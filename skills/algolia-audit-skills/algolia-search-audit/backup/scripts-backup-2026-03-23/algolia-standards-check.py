#!/usr/bin/env python3
"""
algolia-standards-check.py — Platform Standards Compliance Checker
Part of the Algolia Search Audit quality pipeline.

Runs against a complete audit workspace and checks ALL outputs against
the canonical rules defined in AGENT-CONTEXT.md. Deterministic — no LLM.

Checks:
  1. JSON field names in audit-data.json (against AGENT-CONTEXT.md canonical list)
  2. CSS classes in HTML outputs (only approved classes permitted)
  3. Inline styles in HTML outputs (no raw font-size/color/font-weight)
  4. File naming in research/ directory ({nn}-{slug}.md pattern)
  5. Path convention (no hardcoded Google Drive paths)
  6. Source labels in research .md files ([FACT]/[ESTIMATE] coverage)

Exit codes:
  0 — all checks pass (or WARN only)
  1 — one or more FAIL violations found

Usage: python3 algolia-standards-check.py <workspace-dir>
  e.g.: python3 algolia-standards-check.py ~/algolia-audits/Costco/
"""

import sys, os, json, re
from pathlib import Path

# ── Canonical lists from AGENT-CONTEXT.md ─────────────────────────────────────

CANONICAL_TOP_LEVEL = {
    'meta','cover','score','company_snapshot','executives','intelligence_signals',
    'competitors','findings','gap_pairs','toc','financials','traffic','tech_stack',
    'ae_fields','next_steps','methodology','bibliography'
}

CANONICAL_FINDING_FIELDS = {
    'id','title','severity','category','tested_query','expected_behavior',
    'actual_behavior','impact_stat','impact_stat_source','screenshot_file',
    'prospect_description','algolia_solution','algolia_case_study_url',
    'algolia_case_study_company','algolia_case_study_result'
}

CANONICAL_SCORE_FIELDS = {
    'overall','verdict','breakdown','breakdown_labels','breakdown_severity',
    'critical_count','moderate_count','low_count','formula_shown','source'
}

CANONICAL_SCORE_KEYS = {
    'latency','typo_tolerance','query_suggestions_empty_state','intent_detection',
    'merchandising_consistency','content_commerce_ux','semantic_nlp_search',
    'dynamic_facets_personalization','recommendations_merchandising','search_intelligence'
}

APPROVED_CSS_CLASSES = {
    'dp-tile','card-3d','feature-grid','feature-card','feature-card--urgent',
    'feature-card--warning','glow-card','inline-src','src-tag',
    'severity--high','severity--medium','severity--low',
    'annotated-screenshot','annotation-circle','annotation-callout',
    'ab-container','finding-card-gradient__title','finding-card-gradient__desc'
}

CANONICAL_RESEARCH_FILES = {
    '01-company-context','02-tech-stack','03-traffic-data','04-competitors',
    '05-test-queries','06-strategic-context','07-hiring-signals','08-financial-profile',
    '09-browser-findings','09b-social-signals','09c-news-signals','09d-hiring-signals',
    '10-scoring-matrix','11-investor-intelligence','12-icp-priority-mapping',
}

ALLOWED_NON_NUMBERED = {
    'CHECKPOINT','_workspace-manifest','FACTCHECK_GATE','partner-intel',
    'industry-intel','test-queries',
}

HARDCODED_PATH_PATTERNS = [
    r'/Users/[a-z]+/Library/CloudStorage/GoogleDrive',
    r'arijit\.chowdhury@algolia\.com',
    r'My Drive/AI/MarketingProject',
    r'My Drive/AI/Claude',
]

# ── Check functions ────────────────────────────────────────────────────────────

def check_json_fields(workspace):
    """Check audit-data.json for canonical field compliance."""
    fails = []
    warns = []

    audit_json = None
    for pattern in ['deliverables/*-audit-data.json', 'deliverables/audit-data.json', '*-audit-data.json']:
        matches = list(Path(workspace).glob(pattern))
        if matches:
            audit_json = matches[0]
            break

    if not audit_json:
        warns.append('audit-data.json not found — skip JSON field check (run after Phase 3)')
        return fails, warns

    try:
        data = json.loads(audit_json.read_text())
    except Exception as e:
        fails.append(f'audit-data.json parse error: {e}')
        return fails, warns

    # Top-level fields
    for key in data.keys():
        if key not in CANONICAL_TOP_LEVEL:
            fails.append(f'audit-data.json: invented top-level field "{key}" — not in canonical list')

    # Finding fields
    for i, finding in enumerate(data.get('findings', [])):
        for key in finding.keys():
            if key not in CANONICAL_FINDING_FIELDS:
                fails.append(f'findings[{i}]: invented field "{key}"')

    # Score keys
    score = data.get('score', {})
    breakdown = score.get('breakdown', {})
    for key in breakdown.keys():
        if key not in CANONICAL_SCORE_KEYS:
            fails.append(f'score.breakdown: invalid key "{key}" — must be one of the 10 canonical scoring areas')

    return fails, warns


def check_css_classes(workspace):
    """Check HTML outputs for unapproved CSS classes."""
    fails = []
    warns = []

    html_files = list(Path(workspace).glob('deliverables/**/*.html'))
    html_files += list(Path(workspace).glob('deliverables/*.html'))

    for html_file in html_files:
        try:
            content = html_file.read_text(errors='ignore')
            classes_found = re.findall(r'class=["\']([^"\']+)', content)
            for class_str in classes_found:
                for cls in class_str.split():
                    # Skip Tailwind-style utilities and template classes
                    if cls.startswith('algolia-') or cls.startswith('tw-') or len(cls) > 50:
                        continue
                    if cls not in APPROVED_CSS_CLASSES and not cls.startswith('js-') and not cls.startswith('is-'):
                        warns.append(f'{html_file.name}: class="{cls}" — verify it is in approved list or a template utility')
        except Exception as e:
            warns.append(f'{html_file.name}: could not read — {e}')

    return fails, warns


def check_inline_styles(workspace):
    """Check HTML/JS for raw font-size, color hex, font-weight violations."""
    fails = []
    warns = []

    files = list(Path(workspace).glob('deliverables/**/*.html')) + \
            list(Path(workspace).glob('deliverables/*.html'))

    skip_line_patterns = [
        'SIGNAL_COLORS', 'DONUT_COLORS', 'const chColor', 'const triggerUrgency',
        ':root', 'CSS variable', '/* ', '//',
    ]

    for f in files:
        try:
            lines = f.read_text(errors='ignore').splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines[350:], start=350):  # Skip CSS :root block
            stripped = line.strip()
            # Skip known safe patterns
            if any(p in stripped for p in skip_line_patterns): continue
            if stripped.startswith('<path') or stripped.startswith('<svg'): continue

            # Rule 1: raw font-size
            styles = re.findall(r'style=["\']([^"\']*)["\']', line)
            for style in styles:
                if re.search(r'font-size:\s*[\d.]+(?:px|rem|em)', style) and '${T.' not in style:
                    fails.append(f'{f.name}:{i+1}: raw font-size in style attr — use T.* token')
                if re.search(r'font-weight:\s*\d{3}', style) and '${T.' not in style:
                    fails.append(f'{f.name}:{i+1}: raw font-weight in style attr — use T.* token')

            # Rule 2: raw hex colors
            hex_matches = re.findall(r'(?:style=["\'][^"\']*|["\`])#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(?![0-9A-Fa-f])', line)
            if hex_matches:
                for h in hex_matches:
                    fails.append(f'{f.name}:{i+1}: raw hex color #{h} — use var(--name)')

    return fails, warns


def check_file_naming(workspace):
    """Check research/ directory for naming convention compliance."""
    fails = []
    warns = []

    research_dir = Path(workspace) / 'research'
    if not research_dir.exists():
        warns.append('research/ directory not found — skip naming check')
        return fails, warns

    for f in research_dir.glob('*.md'):
        stem = f.stem
        # Check numbered pattern
        if re.match(r'^\d{2}-.+', stem):
            num = int(stem[:2])
            if num < 1 or num > 12:
                warns.append(f'research/{f.name}: file number {num:02d} outside expected range 01-12')
        elif stem not in ALLOWED_NON_NUMBERED:
            warns.append(f'research/{f.name}: does not match {{nn}}-{{slug}}.md pattern and is not a known special file')

    return fails, warns


def check_path_convention(workspace):
    """Check all files for hardcoded Google Drive or personal paths."""
    fails = []

    all_files = list(Path(workspace).glob('**/*.py')) + \
                list(Path(workspace).glob('**/*.md')) + \
                list(Path(workspace).glob('**/*.sh'))

    # Also check skills directory scripts
    skills_scripts = Path.home() / '.claude/skills/algolia-search-audit/scripts'
    if skills_scripts.exists():
        all_files += list(skills_scripts.glob('*.py'))

    for f in all_files:
        try:
            content = f.read_text(errors='ignore')
            for pattern in HARDCODED_PATH_PATTERNS:
                if re.search(pattern, content):
                    fails.append(f'{f}: contains hardcoded path matching "{pattern}" — use $ALGOLIA_AUDIT_DIR')
        except Exception:
            continue

    return fails, []


def check_source_labels(workspace):
    """Check research .md files for [FACT]/[ESTIMATE] label coverage."""
    fails = []
    warns = []

    research_dir = Path(workspace) / 'research'
    if not research_dir.exists():
        return fails, warns

    for f in research_dir.glob('*.md'):
        try:
            content = f.read_text(errors='ignore')
        except Exception:
            continue

        # Count numeric stats (e.g., "$1.2B", "83.4M", "32%", "4.1 million")
        numerics = re.findall(r'\$[\d,.]+[BMK]?|\d+\.?\d*[%BMK]|\d[\d,]+ million', content)
        labels = re.findall(r'\[(?:FACT|ESTIMATE|WEBSEARCH|WEBFETCH|OBSERVED|WEBSEARCH)\b', content, re.I)

        if len(numerics) >= 5 and len(labels) < 2:
            warns.append(f'research/{f.name}: {len(numerics)} numeric values, only {len(labels)} source labels — possible unlabeled claims')

        # Check for [COLLECT_VIA_SKILL] — these are expected stubs, not violations
        stubs = len(re.findall(r'\[COLLECT_VIA_SKILL\]', content))
        if stubs > 0:
            warns.append(f'research/{f.name}: {stubs} [COLLECT_VIA_SKILL] stubs — skill orchestrator enrichment required')

    return fails, warns

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print('Usage: algolia-standards-check.py <workspace-dir>', file=sys.stderr)
        sys.exit(1)

    workspace = os.path.expanduser(sys.argv[1])
    if not os.path.isdir(workspace):
        print(f'ERROR: {workspace} is not a directory', file=sys.stderr)
        sys.exit(1)

    print(f'\nALGOLIA STANDARDS CHECK — {workspace}')
    print('━' * 60)

    all_fails = []
    all_warns = []

    checks = [
        ('JSON field names',    check_json_fields),
        ('CSS classes',         check_css_classes),
        ('Inline styles',       check_inline_styles),
        ('File naming',         check_file_naming),
        ('Path convention',     check_path_convention),
        ('Source labels',       check_source_labels),
    ]

    for name, fn in checks:
        fails, warns = fn(workspace)
        all_fails.extend(fails)
        all_warns.extend(warns)

        if fails:
            print(f'\n❌ {name}: FAIL ({len(fails)} violations)')
            for v in fails[:5]:
                print(f'   {v}')
            if len(fails) > 5:
                print(f'   ... and {len(fails)-5} more')
        elif warns:
            print(f'\n⚠️  {name}: WARN ({len(warns)} warnings)')
            for w in warns[:3]:
                print(f'   {w}')
        else:
            print(f'\n✅ {name}: PASS')

    print(f'\n{"━"*60}')
    print(f'SUMMARY: {len(all_fails)} FAIL, {len(all_warns)} WARN')
    if all_fails:
        print('\nFix guide:')
        print('  JSON fields   → check AGENT-CONTEXT.md canonical list')
        print('  CSS classes   → use only approved classes from AGENT-CONTEXT.md Section 2')
        print('  Inline styles → use T.* tokens from AGENT-CONTEXT.md Section 3')
        print('  File naming   → use {nn}-{slug}.md (01-12) in research/')
        print('  Path conv     → use $ALGOLIA_AUDIT_DIR, never hardcoded paths')
        print('  Source labels → add [FACT]/[ESTIMATE] to every numeric claim')
        sys.exit(1)
    else:
        print('\n✅ All checks passed — workspace meets platform standards')
        sys.exit(0)

if __name__ == '__main__':
    main()
