"""
Validator gate tests — confirms validate-json-schema.py exit codes are correct.
These are the same tests as TestCitationBlockingRules but as a standalone file
for clarity that these specifically test the validator gate behaviour.
Run: cd ~/.claude/skills/algolia-search-audit/scripts && python3 -m pytest tests/test_validator_gates.py -v
"""
import json, os, subprocess, copy
import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..')
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'valid_audit_data.json')
VALIDATOR = os.path.join(SCRIPTS_DIR, 'validate-json-schema.py')


def run_validator(data: dict, tmp_dir: str) -> tuple[int, str]:
    slug = 'testco'
    json_path = os.path.join(tmp_dir, f'{slug}-audit-data.json')
    with open(json_path, 'w') as f:
        json.dump(data, f)
    result = subprocess.run(
        ['python3', VALIDATOR, slug],
        capture_output=True, text=True, cwd=tmp_dir
    )
    return result.returncode, result.stdout + result.stderr


class TestValidatorExitCodes:
    """validate-json-schema.py must exit 1 on all blocking violations."""

    @pytest.fixture
    def base(self):
        with open(FIXTURE_PATH) as f:
            return json.load(f)

    def test_valid_fixture_exits_0(self, base, tmp_path):
        rc, out = run_validator(base, str(tmp_path))
        assert rc == 0, f"Valid fixture must exit 0.\n{out}"
        assert 'schema valid' in out.lower() or '✅' in out

    def test_missing_tab_subtitles_exits_1(self, base, tmp_path):
        data = copy.deepcopy(base)
        data.pop('tab_subtitles', None)
        rc, out = run_validator(data, str(tmp_path))
        assert rc == 1, f"Missing tab_subtitles must exit 1. Got {rc}.\n{out}"

    def test_missing_exec_quote_source_exits_1(self, base, tmp_path):
        data = copy.deepcopy(base)
        data['executives'][0]['quote_source'] = None
        data['executives'][0]['source_url'] = None
        data['executives'][0]['source'] = None
        rc, out = run_validator(data, str(tmp_path))
        assert rc == 1, f"Missing exec quote_source must exit 1. Got {rc}.\n{out}"

    def test_missing_signal_source_url_exits_1(self, base, tmp_path):
        data = copy.deepcopy(base)
        data['intelligence_signals'][0]['source_url'] = None
        rc, out = run_validator(data, str(tmp_path))
        assert rc == 1, f"Missing signal source_url must exit 1. Got {rc}.\n{out}"

    def test_missing_angle_source_exits_1(self, base, tmp_path):
        data = copy.deepcopy(base)
        data['strategic_angles'][0]['source'] = None
        rc, out = run_validator(data, str(tmp_path))
        assert rc == 1, f"Missing angle source must exit 1. Got {rc}.\n{out}"

    def test_missing_case_study_url_exits_1(self, base, tmp_path):
        data = copy.deepcopy(base)
        data['case_studies'][0]['url'] = None
        rc, out = run_validator(data, str(tmp_path))
        assert rc == 1, f"Missing case_study url must exit 1. Got {rc}.\n{out}"

    def test_top_channels_dict_exits_1(self, base, tmp_path):
        data = copy.deepcopy(base)
        data['traffic']['top_channels'] = {'Direct': '45%'}  # dict not array
        rc, out = run_validator(data, str(tmp_path))
        assert rc == 1, f"top_channels as dict must exit 1. Got {rc}.\n{out}"

    def test_missing_tech_stack_exits_1(self, base, tmp_path):
        data = copy.deepcopy(base)
        data['tech_stack']['full_list'] = None
        rc, out = run_validator(data, str(tmp_path))
        assert rc == 1, f"Missing tech_stack.full_list must exit 1. Got {rc}.\n{out}"
