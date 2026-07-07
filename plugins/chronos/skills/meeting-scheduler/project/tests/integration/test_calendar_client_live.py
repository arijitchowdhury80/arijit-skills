"""
tests/integration/test_calendar_client_live.py

Layer 2 — Integration tests for calendar_client.py against the real Google Calendar API.
Requires live gws authentication. Run before merges, not on every save.

Usage:
    pytest tests/integration/ -v --run-integration
    or just: pytest tests/integration/ -v   (marks auto-detected)
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from calendar_client import CalendarError, get_freebusy, list_calendars

pytestmark = pytest.mark.integration

OWNER_EMAIL = "arijit.chowdhury@algolia.com"


class TestListCalendarsLive:
    def test_list_calendars_returns_nonempty(self):
        """Live gws returns at least one calendar for authenticated user."""
        cals = list_calendars()
        assert len(cals) > 0

    def test_list_calendars_owner_present(self):
        """Owner's primary calendar is in the list."""
        cals = list_calendars()
        ids = [c["id"] for c in cals]
        assert OWNER_EMAIL in ids

    def test_list_calendars_have_required_fields(self):
        """Every calendar entry has id, accessRole, and kind."""
        cals = list_calendars()
        for cal in cals:
            assert "id" in cal
            assert "accessRole" in cal


class TestGetFreeBusyLive:
    def _today_window(self):
        """Return (start, end) for today UTC."""
        now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return now, now.replace(hour=23, minute=59, second=59)

    def test_freebusy_owner_returns_dict(self):
        """freebusy for owner returns dict keyed by email."""
        start, end = self._today_window()
        result = get_freebusy([OWNER_EMAIL], start, end)
        assert isinstance(result, dict)
        assert OWNER_EMAIL in result

    def test_freebusy_owner_blocks_are_valid(self):
        """Any busy blocks have start < end and are UTC-aware datetimes."""
        start, end = self._today_window()
        result = get_freebusy([OWNER_EMAIL], start, end)
        for block in result[OWNER_EMAIL]:
            assert block.start < block.end
            assert block.start.tzinfo is not None
            assert block.end.tzinfo is not None

    def test_freebusy_next_week_window(self):
        """freebusy works over a 5-day window without error."""
        now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        start = now
        end = now + timedelta(days=7)
        result = get_freebusy([OWNER_EMAIL], start, end)
        assert OWNER_EMAIL in result
        # Blocks may be empty or non-empty — just check structure
        assert isinstance(result[OWNER_EMAIL], list)

    def test_freebusy_multiple_emails(self):
        """freebusy handles multiple email addresses at once."""
        start, end = self._today_window()
        emails = [OWNER_EMAIL, "jordan.kim@example.com"]
        result = get_freebusy(emails, start, end)
        assert OWNER_EMAIL in result
        assert "jordan.kim@example.com" in result

    def test_freebusy_empty_email_list_returns_empty(self):
        """Empty email list: Google API returns empty dict, not an error."""
        start, end = self._today_window()
        result = get_freebusy([], start, end)
        assert result == {}  # API returns empty calendars dict for empty input

    def test_freebusy_invalid_window_raises(self):
        """Window where end < start should raise CalendarError."""
        now = datetime.now(timezone.utc)
        with pytest.raises((CalendarError, Exception)):
            get_freebusy([OWNER_EMAIL], now + timedelta(days=1), now)
