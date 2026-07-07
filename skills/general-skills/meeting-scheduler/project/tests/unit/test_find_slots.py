"""
tests/test_find_slots.py — Unit tests for the core slot-finding algorithm.

Tests are pure: no I/O, no network, no gws calls.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from find_slots import (
    BusyBlock,
    Participant,
    SlotResult,
    _has_overlap,
    _round_up_to_step,
    _within_working_hours,
    find_slots,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _utc(iso: str) -> datetime:
    """Parse ISO UTC string to aware datetime."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


ARIJIT = Participant(
    name="Arijit Chowdhury",
    email="arijit.chowdhury@algolia.com",
    timezone="America/New_York",
    working_hours_start="09:00",
    working_hours_end="18:00",
)

DAVID = Participant(
    name="Jordan Kim",
    email="jordan.kim@example.com",
    timezone="Australia/Sydney",
    working_hours_start="09:00",
    working_hours_end="18:00",
)

SARAH = Participant(
    name="Sarah",
    email="sarah@example.com",
    timezone="Europe/London",
    working_hours_start="09:00",
    working_hours_end="18:00",
)


# ---------------------------------------------------------------------------
# _round_up_to_step
# ---------------------------------------------------------------------------

class TestRoundUpToStep:
    def test_already_on_boundary(self):
        dt = _utc("2026-04-21T09:00:00Z")
        result = _round_up_to_step(dt, 30)
        assert result == dt.replace(second=0, microsecond=0)

    def test_rounds_up_to_next_30(self):
        dt = _utc("2026-04-21T09:10:00Z")
        result = _round_up_to_step(dt, 30)
        assert result == _utc("2026-04-21T09:30:00Z")

    def test_rounds_up_to_next_hour(self):
        dt = _utc("2026-04-21T09:45:00Z")
        result = _round_up_to_step(dt, 30)
        assert result == _utc("2026-04-21T10:00:00Z")

    def test_60_min_step(self):
        dt = _utc("2026-04-21T09:20:00Z")
        result = _round_up_to_step(dt, 60)
        assert result == _utc("2026-04-21T10:00:00Z")


# ---------------------------------------------------------------------------
# _has_overlap
# ---------------------------------------------------------------------------

class TestHasOverlap:
    def test_no_busy_blocks(self):
        assert not _has_overlap(_utc("2026-04-21T09:00:00Z"), _utc("2026-04-21T09:30:00Z"), [])

    def test_slot_inside_busy(self):
        busy = [BusyBlock(start=_utc("2026-04-21T09:00:00Z"), end=_utc("2026-04-21T10:00:00Z"))]
        assert _has_overlap(_utc("2026-04-21T09:15:00Z"), _utc("2026-04-21T09:45:00Z"), busy)

    def test_slot_before_busy(self):
        busy = [BusyBlock(start=_utc("2026-04-21T10:00:00Z"), end=_utc("2026-04-21T11:00:00Z"))]
        assert not _has_overlap(_utc("2026-04-21T09:00:00Z"), _utc("2026-04-21T09:30:00Z"), busy)

    def test_slot_after_busy(self):
        busy = [BusyBlock(start=_utc("2026-04-21T08:00:00Z"), end=_utc("2026-04-21T09:00:00Z"))]
        assert not _has_overlap(_utc("2026-04-21T09:00:00Z"), _utc("2026-04-21T09:30:00Z"), busy)

    def test_slot_partially_overlaps_start(self):
        busy = [BusyBlock(start=_utc("2026-04-21T09:15:00Z"), end=_utc("2026-04-21T10:00:00Z"))]
        assert _has_overlap(_utc("2026-04-21T09:00:00Z"), _utc("2026-04-21T09:30:00Z"), busy)

    def test_slot_partially_overlaps_end(self):
        busy = [BusyBlock(start=_utc("2026-04-21T09:00:00Z"), end=_utc("2026-04-21T09:15:00Z"))]
        assert _has_overlap(_utc("2026-04-21T09:00:00Z"), _utc("2026-04-21T09:30:00Z"), busy)

    def test_adjacent_slots_no_overlap(self):
        # Slot ends exactly when busy starts — should NOT overlap
        busy = [BusyBlock(start=_utc("2026-04-21T09:30:00Z"), end=_utc("2026-04-21T10:00:00Z"))]
        assert not _has_overlap(_utc("2026-04-21T09:00:00Z"), _utc("2026-04-21T09:30:00Z"), busy)


# ---------------------------------------------------------------------------
# _within_working_hours
# ---------------------------------------------------------------------------

class TestWithinWorkingHours:
    def test_slot_within_hours_new_york(self):
        # 9 AM ET = 13:00 UTC (EST+4 in April = EDT)
        assert _within_working_hours(
            _utc("2026-04-21T13:00:00Z"), _utc("2026-04-21T13:30:00Z"),
            "America/New_York", "09:00", "18:00"
        )

    def test_slot_before_working_hours(self):
        # 7 AM ET = 11:00 UTC
        assert not _within_working_hours(
            _utc("2026-04-21T11:00:00Z"), _utc("2026-04-21T11:30:00Z"),
            "America/New_York", "09:00", "18:00"
        )

    def test_slot_after_working_hours(self):
        # 7 PM ET = 23:00 UTC
        assert not _within_working_hours(
            _utc("2026-04-21T23:00:00Z"), _utc("2026-04-21T23:30:00Z"),
            "America/New_York", "09:00", "18:00"
        )

    def test_slot_spanning_midnight_local(self):
        # 23:30–00:00 local time spans midnight — should be outside working hours
        # 2026-04-22 03:30 UTC = 2026-04-21 23:30 EDT
        assert not _within_working_hours(
            _utc("2026-04-22T03:30:00Z"), _utc("2026-04-22T04:00:00Z"),
            "America/New_York", "09:00", "18:00"
        )

    def test_slot_spanning_midnight_sydney(self):
        # 2026-04-22 13:30 UTC = 2026-04-22 23:30 AEST — spans midnight
        assert not _within_working_hours(
            _utc("2026-04-22T13:30:00Z"), _utc("2026-04-22T14:00:00Z"),
            "Australia/Sydney", "09:00", "18:00"
        )

    def test_sydney_timezone(self):
        # Sydney is UTC+10 in April (AEST, no DST)
        # 9 AM Sydney = 23:00 UTC previous day
        assert _within_working_hours(
            _utc("2026-04-20T23:00:00Z"), _utc("2026-04-20T23:30:00Z"),
            "Australia/Sydney", "09:00", "18:00"
        )

    def test_paris_timezone(self):
        # Paris is UTC+2 in April (CEST)
        # 9 AM Paris = 07:00 UTC
        assert _within_working_hours(
            _utc("2026-04-21T07:00:00Z"), _utc("2026-04-21T07:30:00Z"),
            "Europe/Paris", "09:00", "18:00"
        )


# ---------------------------------------------------------------------------
# find_slots — integration-style unit tests
# ---------------------------------------------------------------------------

class TestFindSlots:
    """Test the full slot-finding function with controlled inputs."""

    def _week_window(self):
        """Monday Apr 21 to Friday Apr 25, 2026 (UTC)."""
        return (
            _utc("2026-04-21T00:00:00Z"),
            _utc("2026-04-25T23:59:59Z"),
        )

    def test_finds_slots_when_everyone_free(self):
        """With no busy blocks, should find many Tier 1 green slots."""
        window_start, window_end = self._week_window()
        slots = find_slots(
            participants=[ARIJIT],
            busy_blocks={},
            window_start=window_start,
            window_end=window_end,
            duration_minutes=30,
            max_results=6,
            owner_timezone="America/New_York",
        )
        assert len(slots) == 6
        assert all(s.tier == 1 for s in slots)

    def test_skips_busy_blocks(self):
        """Slots conflicting with busy blocks should be excluded."""
        # Block the entire morning of Monday (9–12 ET = 13:00–16:00 UTC)
        busy = {
            ARIJIT.email: [
                BusyBlock(_utc("2026-04-21T13:00:00Z"), _utc("2026-04-21T16:00:00Z"))
            ]
        }
        window_start, window_end = self._week_window()
        slots = find_slots(
            participants=[ARIJIT],
            busy_blocks=busy,
            window_start=window_start,
            window_end=window_end,
            duration_minutes=30,
            max_results=10,
            owner_timezone="America/New_York",
        )
        # Ensure no slot overlaps the busy block
        for slot in slots:
            start = _utc(slot.start_utc)
            end = _utc(slot.end_utc)
            assert not (start < _utc("2026-04-21T16:00:00Z") and end > _utc("2026-04-21T13:00:00Z")), \
                f"Slot {slot.start_utc} should not overlap busy block"

    def test_tier_1_when_both_in_working_hours(self):
        """Slot within working hours for both ET and London → Tier 1."""
        # 14:00 UTC = 10 AM ET, 3 PM London — both in working hours
        window_start = _utc("2026-04-21T14:00:00Z")
        window_end = _utc("2026-04-21T15:00:00Z")
        slots = find_slots(
            participants=[ARIJIT, SARAH],
            busy_blocks={},
            window_start=window_start,
            window_end=window_end,
            duration_minutes=30,
            owner_timezone="America/New_York",
        )
        assert len(slots) >= 1
        assert slots[0].tier == 1

    def test_tier_2_when_one_outside_working_hours(self):
        """
        14:00 UTC = 10 AM ET (in hours), midnight AEST (out of hours).
        Meeting with Sydney person → Tier 2.
        """
        window_start = _utc("2026-04-21T14:00:00Z")
        window_end = _utc("2026-04-21T14:31:00Z")
        slots = find_slots(
            participants=[ARIJIT, DAVID],
            busy_blocks={},
            window_start=window_start,
            window_end=window_end,
            duration_minutes=30,
            owner_timezone="America/New_York",
        )
        assert len(slots) >= 1
        assert slots[0].tier == 2
        assert "Jordan Kim" in slots[0].tier_reason

    def test_no_slots_on_weekend(self):
        """Weekend slots should be skipped entirely."""
        # April 18–19, 2026 = Saturday–Sunday (weekdays 5 and 6)
        window_start = _utc("2026-04-18T00:00:00Z")
        window_end = _utc("2026-04-19T23:59:59Z")
        slots = find_slots(
            participants=[ARIJIT],
            busy_blocks={},
            window_start=window_start,
            window_end=window_end,
            duration_minutes=30,
        )
        assert len(slots) == 0

    def test_results_sorted_tier_then_score(self):
        """Tier 1 slots should always appear before Tier 2 slots."""
        window_start, window_end = self._week_window()
        slots = find_slots(
            participants=[ARIJIT, DAVID],
            busy_blocks={},
            window_start=window_start,
            window_end=window_end,
            duration_minutes=30,
            max_results=10,
            owner_timezone="America/New_York",
        )
        tiers = [s.tier for s in slots]
        assert tiers == sorted(tiers), f"Tiers not sorted: {tiers}"

    def test_max_results_respected(self):
        """Should never return more than max_results slots."""
        window_start, window_end = self._week_window()
        slots = find_slots(
            participants=[ARIJIT],
            busy_blocks={},
            window_start=window_start,
            window_end=window_end,
            duration_minutes=30,
            max_results=3,
        )
        assert len(slots) <= 3

    def test_local_times_included(self):
        """Each slot should include local time string for each participant."""
        window_start = _utc("2026-04-21T14:00:00Z")
        window_end = _utc("2026-04-21T14:31:00Z")
        slots = find_slots(
            participants=[ARIJIT, SARAH],
            busy_blocks={},
            window_start=window_start,
            window_end=window_end,
            duration_minutes=30,
        )
        assert len(slots) >= 1
        slot = slots[0]
        assert ARIJIT.name in slot.local_times
        assert SARAH.name in slot.local_times
        assert "AM" in slot.local_times[ARIJIT.name] or "PM" in slot.local_times[ARIJIT.name]


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
