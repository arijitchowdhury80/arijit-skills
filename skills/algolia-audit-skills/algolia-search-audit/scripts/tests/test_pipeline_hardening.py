"""
Pipeline hardening tests — verifies all 6 confirmed bugs are fixed.
Run: cd ~/.claude/skills/algolia-search-audit/scripts && python3 -m pytest tests/test_pipeline_hardening.py -v
"""
import json, os, subprocess, copy
import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..')
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'valid_audit_data.json')


def run_script(script_name, *args, cwd=None):
    result = subprocess.run(
        ['python3', os.path.join(SCRIPTS_DIR, script_name), *args],
        capture_output=True, text=True, cwd=cwd or SCRIPTS_DIR
    )
    return result.returncode, result.stdout, result.stderr


class TestFixtureIsValid:
    """Baseline: the test fixture must pass Pydantic schema."""

    def test_fixture_passes_pydantic_schema(self):
        import sys
        sys.path.insert(0, SCRIPTS_DIR)
        from audit_data_schema import validate_audit_data
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        ok, errors = validate_audit_data(data)
        assert ok, f"Fixture must pass Pydantic schema:\n" + "\n".join(errors)

    def test_fixture_has_channel_key_not_source(self):
        """Fixture top_channels must use 'channel' key — not 'source'."""
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        channels = (data.get('traffic') or {}).get('top_channels') or []
        assert len(channels) > 0, "Fixture must have top_channels"
        for ch in channels:
            assert 'channel' in ch, f"Fixture channel uses wrong key. Got: {list(ch.keys())}"
            assert 'source' not in ch, "Fixture must not use old 'source' key"

    def test_fixture_device_share_has_pct_symbol(self):
        """Fixture device_share values must include % symbol."""
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        ds = (data.get('traffic') or {}).get('device_share') or {}
        assert '%' in str(ds.get('mobile', '')), f"mobile should have %, got: {ds.get('mobile')}"
        assert '%' in str(ds.get('desktop', '')), f"desktop should have %, got: {ds.get('desktop')}"

    def test_fixture_has_real_benchmark_proof_not_generic(self):
        """Fixture must NOT contain the old hardcoded fallback text."""
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        bp = (data.get('ae_fields') or {}).get('benchmark_proof', '')
        assert bp, "ae_fields.benchmark_proof must be set"
        assert 'avg. +12% conversion uplift within 90 days' not in bp, (
            "Fixture contains old hardcoded fallback text. Must be prospect-specific."
        )

    def test_fixture_has_tab_subtitles(self):
        """Fixture must have tab_subtitles — now a blocking field."""
        with open(FIXTURE_PATH) as f:
            data = json.load(f)
        ts = data.get('tab_subtitles') or {}
        assert ts.get('summary'), "tab_subtitles.summary must be set"
        assert ts.get('account'), "tab_subtitles.account must be set"
        assert ts.get('findings'), "tab_subtitles.findings must be set"
        assert ts.get('case'), "tab_subtitles.case must be set"
        assert ts.get('playbook'), "tab_subtitles.playbook must be set"


class TestTopChannelsFieldName:
    """Bug fix: top_channels must use 'channel' key to match render-audit.ts:857."""

    def test_generate_audit_data_does_not_use_source_key(self):
        """Verify the fix is in generate-audit-data.py — 'source' key must be gone."""
        with open(os.path.join(SCRIPTS_DIR, 'generate-audit-data.py')) as f:
            content = f.read()
        assert "{'source': ch_name" not in content, (
            "generate-audit-data.py still uses 'source' key in top_channels. "
            "Must be 'channel' to match render-audit.ts:857. Fix line 247."
        )
        assert "{'channel': ch_name" in content, (
            "generate-audit-data.py must use 'channel' key (not 'source') in top_channels. "
            "render-audit.ts reads ch.channel at line 857."
        )


class TestDeviceShareFormat:
    """Bug fix: device_share must keep % symbol for rendering consistency."""

    def test_generate_audit_data_keeps_pct_symbol(self):
        """Verify the % is no longer stripped from device_share values."""
        with open(os.path.join(SCRIPTS_DIR, 'generate-audit-data.py')) as f:
            content = f.read()
        # The old buggy code stripped %
        assert "mob_match.group(1).replace('%', '')" not in content, (
            "generate-audit-data.py still strips % from device_share.mobile. "
            "Must keep % for rendering consistency."
        )
        assert "desk_match.group(1).replace('%', '')" not in content, (
            "generate-audit-data.py still strips % from device_share.desktop. "
            "Must keep % for rendering consistency."
        )


class TestNoFabricatedFallbacks:
    """Bug fix: render-audit.ts must not inject fabricated content when fields missing."""

    def test_render_audit_has_no_hardcoded_benchmark_proof(self):
        """render-audit.ts must not have the hardcoded +12% conversion fallback."""
        with open(os.path.join(SCRIPTS_DIR, 'render-audit.ts')) as f:
            content = f.read()
        assert 'avg. +12% conversion uplift within 90 days' not in content, (
            "render-audit.ts still contains hardcoded BENCHMARK_PROOF fallback. "
            "This fabricated stat gets rendered as if it were prospect-specific evidence."
        )

    def test_render_audit_has_no_hardcoded_opportunity_headline(self):
        """render-audit.ts must not have the hardcoded generic opportunity headline."""
        with open(os.path.join(SCRIPTS_DIR, 'render-audit.ts')) as f:
            content = f.read()
        # The old fallback was: `The ${s(cs.industry)} Search Opportunity`
        assert 'The ${s(cs.industry)} Search Opportunity' not in content, (
            "render-audit.ts still contains hardcoded OPPORTUNITY_HEADLINE fallback. "
            "Must use s(ae.opportunity_headline) with no fabricated default."
        )


class TestCitationBlockingRules:
    """Bug fix: citation violations must now block render (exit 1), not just warn."""

    @pytest.fixture
    def base_data(self):
        with open(FIXTURE_PATH) as f:
            return json.load(f)

    def run_validator(self, data, tmp_path):
        slug = 'testco'
        json_file = os.path.join(tmp_path, f'{slug}-audit-data.json')
        with open(json_file, 'w') as f:
            json.dump(data, f)
        rc, out, err = run_script('validate-json-schema.py', slug, cwd=tmp_path)
        return rc, out + err

    def test_valid_fixture_passes_validator(self, base_data, tmp_path):
        """Baseline: valid fixture exits 0."""
        rc, out = self.run_validator(base_data, str(tmp_path))
        assert rc == 0, f"Valid fixture should pass validator. rc={rc}\n{out}"

    def test_executive_missing_quote_source_is_blocking(self, base_data, tmp_path):
        """Executive with quote but no quote_source must exit 1."""
        data = copy.deepcopy(base_data)
        data['executives'][0]['quote_source'] = None
        # Remove from Pydantic-validated fields — schema auto-populates from source_url
        data['executives'][0]['source_url'] = None
        data['executives'][0]['source'] = None
        rc, out = self.run_validator(data, str(tmp_path))
        assert rc == 1, (
            f"Missing executive quote_source should block render. Got rc={rc}. "
            f"Citation checks must be fail() not warn().\n{out}"
        )

    def test_intelligence_signal_missing_source_url_is_blocking(self, base_data, tmp_path):
        """Intelligence signal with content but no source_url must exit 1."""
        data = copy.deepcopy(base_data)
        data['intelligence_signals'][0]['source_url'] = None
        rc, out = self.run_validator(data, str(tmp_path))
        assert rc == 1, (
            f"Missing intelligence_signal source_url should block render. Got rc={rc}.\n{out}"
        )

    def test_strategic_angle_missing_source_is_blocking(self, base_data, tmp_path):
        """Strategic angle without source must exit 1."""
        data = copy.deepcopy(base_data)
        data['strategic_angles'][0]['source'] = None
        rc, out = self.run_validator(data, str(tmp_path))
        assert rc == 1, (
            f"Missing strategic_angle source should block render. Got rc={rc}.\n{out}"
        )

    def test_strategic_angle_missing_proof_is_blocking(self, base_data, tmp_path):
        """Strategic angle without algolia_proof must exit 1."""
        data = copy.deepcopy(base_data)
        data['strategic_angles'][0]['algolia_proof'] = None
        rc, out = self.run_validator(data, str(tmp_path))
        assert rc == 1, (
            f"Missing strategic_angle algolia_proof should block render. Got rc={rc}.\n{out}"
        )

    def test_case_study_missing_url_is_blocking(self, base_data, tmp_path):
        """Case study without url must exit 1."""
        data = copy.deepcopy(base_data)
        data['case_studies'][0]['url'] = None
        rc, out = self.run_validator(data, str(tmp_path))
        assert rc == 1, (
            f"Case study missing url should block render. Got rc={rc}.\n{out}"
        )

    def test_missing_tab_subtitles_is_blocking(self, base_data, tmp_path):
        """Missing tab_subtitles must exit 1."""
        data = copy.deepcopy(base_data)
        data.pop('tab_subtitles', None)
        rc, out = self.run_validator(data, str(tmp_path))
        assert rc == 1, (
            f"Missing tab_subtitles should block render. Got rc={rc}. "
            f"tab_subtitles must be fail() not warn().\n{out}"
        )

    def test_wrong_top_channels_type_is_blocking(self, base_data, tmp_path):
        """top_channels as dict (not array) must exit 1."""
        data = copy.deepcopy(base_data)
        data['traffic']['top_channels'] = {'Direct': '45%', 'Organic': '32%'}
        rc, out = self.run_validator(data, str(tmp_path))
        assert rc == 1, (
            f"top_channels as dict should block render. Got rc={rc}.\n{out}"
        )

    def test_wrong_score_keys_blocked_by_pydantic(self, base_data, tmp_path):
        """Non-canonical score breakdown keys must fail Pydantic validation."""
        import sys
        sys.path.insert(0, SCRIPTS_DIR)
        from audit_data_schema import validate_audit_data
        data = copy.deepcopy(base_data)
        data['score']['breakdown']['Semantic / NLP Search'] = 3  # wrong key
        ok, errors = validate_audit_data(data)
        assert not ok, (
            "Non-canonical score breakdown key should fail Pydantic validation. "
            "AuditData.Score.validate_score_keys enforces CANONICAL_SCORE_KEYS."
        )
