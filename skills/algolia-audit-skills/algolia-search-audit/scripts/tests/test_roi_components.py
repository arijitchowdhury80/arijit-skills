"""
Tests for the deterministic 6-component ROI model and the BUG-5 financial
overwrite guard (Cluster A — ROI & Scoring math).

Run: cd ~/.claude/skills/algolia-search-audit/scripts && python3 -m pytest tests/test_roi_components.py -v
"""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..')


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS_DIR, path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


roi = _load('calculate_roi', 'calculate-roi.py')
cf = _load('collect_financials', 'collect-financials.py')


# ── 6-component ROI math ──────────────────────────────────────────────────────

BASE = {
    'monthly_visits': 18_500_000,
    'aov': 62.50,
    'search_usage_rate': 0.15,
    'current_conversion': 0.03,
    'no_results_rate': 0.06,
    'nlp_fail_rate': 0.22,
}


class TestComponentMath:
    def test_all_six_components_present(self):
        out = roi.calculate_components(BASE)
        assert [c['component'] for c in out['components']] == [1, 2, 3, 4, 5, 6]

    def test_c1_exact_arithmetic(self):
        """C1 = visits × usage × conv_delta × AOV × 12 — hand-computed."""
        out = roi.calculate_components(BASE)
        c1 = next(c for c in out['components'] if c['component'] == 1)
        # 18.5M × 0.15 × 0.15 × 62.50 × 12
        assert c1['conservative_raw'] == pytest.approx(312_187_500.0)
        # moderate uses 0.20 delta
        assert c1['moderate_raw'] == pytest.approx(416_250_000.0)

    def test_totals_equal_sum_of_components(self):
        out = roi.calculate_components(BASE)
        active = [c for c in out['components'] if c['status'] != 'SKIPPED']
        assert out['totals']['conservative_raw'] == pytest.approx(
            sum(c['conservative_raw'] for c in active))
        assert out['totals']['moderate_raw'] == pytest.approx(
            sum(c['moderate_raw'] for c in active))

    def test_moderate_geq_conservative(self):
        out = roi.calculate_components(BASE)
        for c in out['components']:
            if c['status'] != 'SKIPPED':
                assert c['moderate_raw'] >= c['conservative_raw']

    def test_deterministic_repeat(self):
        a = roi.calculate_components(BASE)
        b = roi.calculate_components(BASE)
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

    def test_c2_skipped_without_current_conversion(self):
        a = dict(BASE)
        a.pop('current_conversion')
        out = roi.calculate_components(a)
        c2 = next(c for c in out['components'] if c['component'] == 2)
        assert c2['status'] == 'SKIPPED'
        assert c2['conservative_raw'] is None

    def test_no_fabrication_when_aov_missing(self):
        a = dict(BASE)
        a.pop('aov')
        out = roi.calculate_components(a)
        # every component that needs aov must be SKIPPED, none invents a number
        for c in out['components']:
            assert c['status'] == 'SKIPPED'
            assert c['conservative_raw'] is None

    def test_cli_components_mode_errors_without_required_inputs(self):
        res = subprocess.run(
            ['python3', os.path.join(SCRIPTS_DIR, 'calculate-roi.py'),
             '--components', '--monthly-visits', '1000000'],
            capture_output=True, text=True)
        assert res.returncode == 1
        assert 'requires at least monthly_visits and aov' in res.stdout

    def test_cli_components_mode_runs(self):
        res = subprocess.run(
            ['python3', os.path.join(SCRIPTS_DIR, 'calculate-roi.py'),
             '--components', '--monthly-visits', '18500000', '--aov', '62.5',
             '--current-conversion', '0.03'],
            capture_output=True, text=True)
        assert res.returncode == 0
        data = json.loads(res.stdout)
        assert data['mode'] == 'components'
        assert data['totals']['conservative_raw'] > 0


# ── BUG-5 overwrite guard ─────────────────────────────────────────────────────

class TestOverwriteGuard:
    def _write(self, p, content):
        with open(p, 'w', encoding='utf-8') as f:
            f.write(content)

    def test_marker_detection(self, tmp_path):
        p = tmp_path / '08-financial-profile.md'
        self._write(str(p), '<!-- company_type: private -->\n# Acme\n')
        assert cf.detect_existing_company_type(str(p)) == 'private'

    def test_legacy_public_inferred_from_ticker(self, tmp_path):
        p = tmp_path / '08-financial-profile.md'
        self._write(str(p), '# Acme\n**Ticker:** ACME\n')
        assert cf.detect_existing_company_type(str(p)) == 'public'

    def test_no_file_returns_none(self, tmp_path):
        p = tmp_path / '08-financial-profile.md'
        assert cf.detect_existing_company_type(str(p)) is None

    def test_guard_refuses_cross_path_without_force(self, tmp_path):
        p = tmp_path / '08-financial-profile.md'
        self._write(str(p), '<!-- company_type: private -->\n# Acme\n')
        with pytest.raises(SystemExit) as exc:
            cf.overwrite_guard(str(p), 'public', force=False)
        assert exc.value.code == 2
        # original file untouched
        assert 'private' in (tmp_path / '08-financial-profile.md').read_text()

    def test_guard_allows_same_type(self, tmp_path):
        p = tmp_path / '08-financial-profile.md'
        self._write(str(p), '<!-- company_type: public -->\n# Acme\n')
        # same type → returns None, no exit
        assert cf.overwrite_guard(str(p), 'public', force=False) is None

    def test_force_backs_up_then_allows(self, tmp_path):
        p = tmp_path / '08-financial-profile.md'
        self._write(str(p), '<!-- company_type: private -->\n# Acme private\n')
        assert cf.overwrite_guard(str(p), 'public', force=True) is None
        backup = tmp_path / '08-financial-profile.private.bak'
        assert backup.exists()
        assert 'private' in backup.read_text()
