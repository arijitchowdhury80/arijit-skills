"""
tests/test_resolve_contact.py — Unit tests for contact resolution.

Uses a test fixture team.json to avoid depending on live gws calls.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from resolve_contact import (
    _humanize_email,
    _lookup_team_json,
    get_owner,
    resolve,
    resolve_multiple,
)


# ---------------------------------------------------------------------------
# Fixture: minimal team config
# ---------------------------------------------------------------------------

TEST_TEAM = {
    "members": [
        {
            "name": "Arijit Chowdhury",
            "aliases": ["arijit", "me"],
            "email": "arijit.chowdhury@algolia.com",
            "timezone": "America/New_York",
            "working_hours": {"start": "09:00", "end": "18:00"},
            "location": "Atlanta, GA",
            "owner": True,
        },
        {
            "name": "Jordan Kim",
            "aliases": ["jordan kim", "jordan k"],
            "email": "jordan.kim@example.com",
            "timezone": "Australia/Sydney",
            "working_hours": {"start": "09:00", "end": "18:00"},
            "location": "Sydney, Australia",
        },
        {
            "name": "Sarah Dupont",
            "aliases": ["sarah"],
            "email": "sarah.dupont@example.com",
            "timezone": "Europe/Paris",
            "working_hours": {"start": "09:00", "end": "18:00"},
            "location": "Paris, France",
        },
    ]
}


def _make_config(tmp_path: Path) -> Path:
    config = tmp_path / "team.json"
    config.write_text(json.dumps(TEST_TEAM))
    return config


# ---------------------------------------------------------------------------
# _humanize_email
# ---------------------------------------------------------------------------

class TestHumanizeEmail:
    def test_dot_separated(self):
        assert _humanize_email("jordan.kim@example.com") == "Jordan Kim"

    def test_single_name(self):
        assert _humanize_email("arijit@algolia.com") == "Arijit"

    def test_hyphenated(self):
        assert _humanize_email("casey.doe-smith@example.com") == "Casey Doe Smith"


# ---------------------------------------------------------------------------
# _lookup_team_json
# ---------------------------------------------------------------------------

class TestLookupTeamJson:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.config = _make_config(Path(self.tmp))

    def test_full_name_match(self):
        result = _lookup_team_json("jordan kim", self.config)
        assert result is not None
        assert result["email"] == "jordan.kim@example.com"
        assert result["timezone"] == "Australia/Sydney"

    def test_partial_first_name(self):
        result = _lookup_team_json("jordan", self.config)
        assert result is not None
        # Should match Jordan Kim (first match)

    def test_alias_match(self):
        result = _lookup_team_json("sarah", self.config)
        assert result is not None
        assert result["email"] == "sarah.dupont@example.com"

    def test_owner_alias(self):
        result = _lookup_team_json("me", self.config)
        assert result is not None
        assert result["email"] == "arijit.chowdhury@algolia.com"

    def test_case_insensitive(self):
        result = _lookup_team_json("JORDAN KIM", self.config)
        assert result is not None
        assert result["email"] == "jordan.kim@example.com"

    def test_not_found(self):
        result = _lookup_team_json("batman", self.config)
        assert result is None

    def test_missing_config(self):
        result = _lookup_team_json("david", Path("/nonexistent/team.json"))
        assert result is None

    def test_working_hours_extracted(self):
        result = _lookup_team_json("arijit", self.config)
        assert result is not None
        assert result["working_hours_start"] == "09:00"
        assert result["working_hours_end"] == "18:00"

    def test_source_is_team_config(self):
        result = _lookup_team_json("jordan", self.config)
        assert result["source"] == "team_config"


# ---------------------------------------------------------------------------
# get_owner
# ---------------------------------------------------------------------------

class TestGetOwner:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.config = _make_config(Path(self.tmp))

    def test_returns_owner_entry(self):
        owner = get_owner(self.config)
        assert owner is not None
        assert owner["email"] == "arijit.chowdhury@algolia.com"
        assert owner["timezone"] == "America/New_York"

    def test_missing_config_returns_none(self):
        owner = get_owner(Path("/nonexistent/team.json"))
        assert owner is None

    def test_no_owner_flagged_returns_none(self):
        tmp = tempfile.mkdtemp()
        config = Path(tmp) / "team.json"
        config.write_text(json.dumps({"members": [
            {"name": "Nobody", "email": "nobody@example.com", "timezone": "UTC"}
        ]}))
        owner = get_owner(config)
        assert owner is None


# ---------------------------------------------------------------------------
# resolve_multiple
# ---------------------------------------------------------------------------

@patch("resolve_contact._lookup_calendar_list", return_value=None)
class TestResolveMultiple:
    """
    _lookup_calendar_list is mocked out here: without it, an unresolved
    team.json query falls through to a live `gws` subprocess call against
    whatever calendars the machine running the test happens to have
    subscribed to — non-deterministic and not portable to another install.
    These tests are specifically about the team.json resolution path.
    """

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.config = _make_config(Path(self.tmp))

    def test_all_found(self, _mock_cal):
        found, not_found = resolve_multiple(["jordan", "sarah"], self.config)
        assert len(found) == 2
        assert not_found == []

    def test_some_not_found(self, _mock_cal):
        found, not_found = resolve_multiple(["jordan", "batman"], self.config)
        assert len(found) == 1
        assert "batman" in not_found

    def test_all_not_found(self, _mock_cal):
        found, not_found = resolve_multiple(["batman", "joker"], self.config)
        assert found == []
        assert len(not_found) == 2

    def test_empty_query_list(self, _mock_cal):
        found, not_found = resolve_multiple([], self.config)
        assert found == []
        assert not_found == []


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
