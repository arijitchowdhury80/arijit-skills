#!/usr/bin/env python3
"""
calculate-score.py — Deterministic scoring calculator for Algolia Search Audit
Reads 10-scoring-matrix.md, extracts all 10 area scores + severities,
applies the weighted formula, and outputs verified results.

Usage: python3 calculate-score.py <workspace-dir>
Output: JSON with overall_score, formula, breakdown

Formula: sum(score × weight) / sum(weights)
  HIGH severity = 2.0×
  MEDIUM severity = 1.0×
  LOW severity = 0.5×
"""

import sys, os, re, json

def get_weight(severity):
    return {'HIGH': 2.0, 'MEDIUM': 1.0, 'LOW': 0.5}.get(severity.upper(), 1.0)

def parse_scoring_matrix(filepath):
    """Parse 10-scoring-matrix.md and extract scores + severities."""
    with open(filepath) as f:
        content = f.read()

    # Match table rows: | N | **Area** | Score/10 | SEVERITY | ...
    # Pattern handles both "7/10" and "7" formats, with optional bold (**) around area name
    pattern = r'^\|\s*\d+\s*\|\s*\*{0,2}([^|*]+)\*{0,2}\s*\|\s*(\d+)(?:/10)?\s*\|\s*(HIGH|MEDIUM|LOW)\s*\|'
    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)

    if not matches:
        # Try alternate format without ** bold
        pattern2 = r'^\|\s*\d+\s*\|\s*([^|]+)\s*\|\s*(\d+)(?:/10)?\s*\|\s*(HIGH|MEDIUM|LOW)\s*\|'
        matches = re.findall(pattern2, content, re.IGNORECASE | re.MULTILINE)

    areas = []
    for area_name, score_str, severity in matches:
        areas.append({
            'area': area_name.strip(),
            'score': int(score_str),
            'severity': severity.upper(),
            'weight': get_weight(severity)
        })

    return areas

def calculate_weighted_score(areas):
    """Apply weighted formula. Returns (weighted_sum, total_weight, overall_score)."""
    weighted_sum = sum(a['score'] * a['weight'] for a in areas)
    total_weight = sum(a['weight'] for a in areas)
    overall = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0
    return weighted_sum, total_weight, overall

def count_severities(areas):
    counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for a in areas:
        counts[a['severity']] = counts.get(a['severity'], 0) + 1
    return counts

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: calculate-score.py <workspace-dir>'}))
        sys.exit(1)

    workspace = sys.argv[1]
    matrix_path = os.path.join(workspace, '10-scoring-matrix.md')

    if not os.path.exists(matrix_path):
        print(json.dumps({'error': f'10-scoring-matrix.md not found at {matrix_path}'}))
        sys.exit(1)

    areas = parse_scoring_matrix(matrix_path)

    if len(areas) < 10:
        print(json.dumps({
            'error': f'Only {len(areas)} scoring areas found (expected 10). Check 10-scoring-matrix.md format.',
            'areas_found': [a['area'] for a in areas]
        }))
        sys.exit(1)

    weighted_sum, total_weight, overall = calculate_weighted_score(areas)
    severity_counts = count_severities(areas)

    result = {
        'overall_score': overall,
        'formula': f'{weighted_sum:.1f} / {total_weight:.1f} = {overall}',
        'weighted_sum': weighted_sum,
        'total_weight': total_weight,
        'severity_counts': severity_counts,
        'area_count': len(areas),
        'breakdown': [
            {
                'area': a['area'],
                'score': a['score'],
                'severity': a['severity'],
                'weight': a['weight'],
                'weighted': round(a['score'] * a['weight'], 1)
            }
            for a in areas
        ],
        'verdict': (
            'Critical Gaps Found' if overall < 4.0 else
            'Significant Issues' if overall < 6.0 else
            'Moderate Issues' if overall < 8.0 else
            'Strong Baseline'
        )
    }

    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
