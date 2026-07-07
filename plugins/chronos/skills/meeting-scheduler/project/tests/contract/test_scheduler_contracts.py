"""
tests/contract/test_scheduler_contracts.py

Layer 3 — Contract tests for the Scheduler module.
Validates that:
  1. find_slots() output satisfies the SlotResult schema
  2. SlotResult fields are all present, correctly typed, and within valid ranges
  3. The JSON output from find_slots CLI is parseable by the skill (downstream consumer)
  4. resolve_contact output satisfies the contact dict schema expected by the skill

These tests catch breaking changes at module boundaries before they propagate.
"""

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from find_slots import BusyBlock, Participant, SlotResult, find_slots

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


ARIJIT = Participant(
    name="Arijit Chowdhury",
    email="arijit.chowdhury@algolia.com",
    timezone="America/New_York",
    working_hours_start="09:00",
    working_hours_end="21:00",
)

DAVID = Participant(
    name="Jordan Kim",
    email="jordan.kim@example.com",
    timezone="Australia/Sydney",
    working_hours_start="09:00",
    working_hours_end="18:00",
)


# ---------------------------------------------------------------------------
# Contract: SlotResult schema
# ---------------------------------------------------------------------------

class TestSlotResultContract:
    """Validates the SlotResult output contract that the skill consumes."""

    def _get_slots(self) -> list[SlotResult]:
        return find_slots(
            participants=[ARIJIT, DAVID],
            busy_blocks={},
            window_start=_utc("2026-04-21T00:00:00Z"),
            window_end=_utc("2026-04-25T23:59:59Z"),
            duration_minutes=30,
            max_results=6,
            owner_timezone="America/New_York",
        )

    def test_slot_result_has_all_required_fields(self):
        """Every SlotResult must have all fields the skill reads."""
        required_fields = {
            "start_utc", "end_utc", "tier", "tier_label",
            "tier_reason", "local_times", "score"
        }
        slots = self._get_slots()
        assert len(slots) > 0, "Need at least one slot to validate contract"
        for slot in slots:
            d = asdict(slot)
            for field in required_fields:
                assert field in d, f"Missing required field: {field}"

    def test_start_utc_is_valid_iso_format(self):
        """start_utc and end_utc must be parseable ISO 8601 strings."""
        for slot in self._get_slots():
            # Must parse without error
            start = datetime.fromisoformat(slot.start_utc.replace("Z", "+00:00"))
            end = datetime.fromisoformat(slot.end_utc.replace("Z", "+00:00"))
            assert start < end, f"start_utc must be before end_utc: {slot.start_utc}"

    def test_tier_is_1_or_2(self):
        """Tier must be 1 (Green) or 2 (Yellow) in v1."""
        for slot in self._get_slots():
            assert slot.tier in (1, 2), f"Invalid tier: {slot.tier}"

    def test_tier_label_matches_tier_number(self):
        """tier_label must be consistent with tier number."""
        for slot in self._get_slots():
            if slot.tier == 1:
                assert "Green" in slot.tier_label
            elif slot.tier == 2:
                assert "Yellow" in slot.tier_label

    def test_score_is_between_0_and_1(self):
        """Score must be a float in [0.0, 1.0]."""
        for slot in self._get_slots():
            assert 0.0 <= slot.score <= 1.0, f"Score out of range: {slot.score}"

    def test_local_times_has_all_participants(self):
        """local_times must contain an entry for every participant."""
        slots = self._get_slots()
        for slot in slots:
            assert ARIJIT.name in slot.local_times
            assert DAVID.name in slot.local_times

    def test_local_times_are_non_empty_strings(self):
        """All local time strings must be non-empty."""
        for slot in self._get_slots():
            for name, time_str in slot.local_times.items():
                assert isinstance(time_str, str) and len(time_str) > 0, \
                    f"Empty local time for {name}"

    def test_slots_sorted_by_tier_then_score(self):
        """Output must be sorted: tier ascending, score descending within tier."""
        slots = self._get_slots()
        for i in range(len(slots) - 1):
            a, b = slots[i], slots[i + 1]
            if a.tier == b.tier:
                assert a.score >= b.score, \
                    f"Within same tier, score must be descending: {a.score} < {b.score}"
            else:
                assert a.tier <= b.tier, \
                    f"Tiers must be ascending: {a.tier} > {b.tier}"

    def test_no_weekend_slots_in_output(self):
        """Contract: output must never contain Saturday or Sunday slots."""
        for slot in self._get_slots():
            start = datetime.fromisoformat(slot.start_utc.replace("Z", "+00:00"))
            assert start.weekday() < 5, \
                f"Weekend slot found: {slot.start_utc} (weekday={start.weekday()})"

    def test_output_is_json_serializable(self):
        """Contract: output must serialize to JSON (skill uses json.dumps)."""
        slots = self._get_slots()
        serialized = json.dumps([asdict(s) for s in slots])
        reparsed = json.loads(serialized)
        assert len(reparsed) == len(slots)
        assert all("start_utc" in s for s in reparsed)


# ---------------------------------------------------------------------------
# Contract: resolve_contact output schema
# ---------------------------------------------------------------------------

class TestResolveContactContract:
    """Validates the contact dict schema that the skill and find_slots consume."""

    def _get_contact(self) -> dict:
        import tempfile
        import json as _json
        from resolve_contact import _lookup_team_json

        team = {"members": [{
            "name": "Jordan Kim",
            "aliases": ["jordan"],
            "email": "jordan.kim@example.com",
            "timezone": "Australia/Sydney",
            "working_hours": {"start": "09:00", "end": "18:00"},
            "location": "Sydney, Australia",
        }]}
        tmp = Path(tempfile.mkdtemp()) / "team.json"
        tmp.write_text(_json.dumps(team))
        return _lookup_team_json("jordan", tmp)

    def test_contact_has_required_fields(self):
        """Contact dict must have all fields the skill and find_slots require."""
        required = {"name", "email", "timezone", "working_hours_start", "working_hours_end"}
        contact = self._get_contact()
        assert contact is not None
        for field in required:
            assert field in contact, f"Missing required contact field: {field}"

    def test_contact_timezone_is_valid_iana(self):
        """Timezone must be a valid IANA string (zoneinfo can load it)."""
        from zoneinfo import ZoneInfo
        contact = self._get_contact()
        tz = ZoneInfo(contact["timezone"])  # raises if invalid
        assert tz is not None

    def test_contact_working_hours_parseable(self):
        """working_hours_start and end must be HH:MM strings."""
        contact = self._get_contact()
        for field in ("working_hours_start", "working_hours_end"):
            parts = contact[field].split(":")
            assert len(parts) == 2
            assert all(p.isdigit() for p in parts)

    def test_contact_email_has_at_sign(self):
        """Email must be a valid-looking email address."""
        contact = self._get_contact()
        assert "@" in contact["email"]
