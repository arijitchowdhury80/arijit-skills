"""
find_slots.py — Core slot-finding algorithm for the Meeting Scheduler.

Pure function: no I/O, no side effects. Takes structured data, returns ranked slots.
Fully unit-testable in isolation.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, time
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Participant:
    name: str
    email: str
    timezone: str
    working_hours_start: str = "09:00"  # local time, HH:MM
    working_hours_end: str = "18:00"    # local time, HH:MM


@dataclass
class BusyBlock:
    start: datetime  # UTC-aware
    end: datetime    # UTC-aware


@dataclass
class SlotResult:
    start_utc: str       # ISO 8601, UTC
    end_utc: str         # ISO 8601, UTC
    tier: int            # 1=Green, 2=Yellow
    tier_label: str      # "🟢 Green" / "🟡 Yellow"
    tier_reason: str     # human-readable explanation
    local_times: dict    # {participant_name: "Mon Apr 21, 9:00 AM ET"}
    score: float         # higher = better


# ---------------------------------------------------------------------------
# Tier definitions
# ---------------------------------------------------------------------------

TIER_1 = (1, "🟢 Green",  "All free, within working hours for everyone")
TIER_2 = (2, "🟡 Yellow", "All free, but outside working hours for some")


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------

def find_slots(
    participants: list[Participant],
    busy_blocks: dict[str, list[BusyBlock]],  # keyed by email
    window_start: datetime,   # UTC-aware
    window_end: datetime,     # UTC-aware
    duration_minutes: int,
    step_minutes: int = 30,
    max_results: int = 6,
    preferred_hours: Optional[list[int]] = None,  # owner's local hours preference
    avoid_hours: Optional[list[int]] = None,
    owner_timezone: str = "America/New_York",
) -> list[SlotResult]:
    """
    Find available meeting slots within [window_start, window_end).

    Returns up to max_results SlotResult objects, sorted by tier then score.
    """
    if preferred_hours is None:
        preferred_hours = [9, 10, 11, 14, 15, 16]
    if avoid_hours is None:
        avoid_hours = [12, 13]

    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=step_minutes)

    results: list[SlotResult] = []
    candidate = _round_up_to_step(window_start, step_minutes)

    while candidate + duration <= window_end:
        slot_end = candidate + duration

        # Skip weekends (Saturday=5, Sunday=6)
        if candidate.weekday() >= 5:
            candidate += step
            continue

        # Check all participants
        has_conflict = False
        outside_hours: list[str] = []

        for p in participants:
            busy = busy_blocks.get(p.email, [])
            if _has_overlap(candidate, slot_end, busy):
                has_conflict = True
                break
            if not _within_working_hours(candidate, slot_end, p.timezone,
                                         p.working_hours_start, p.working_hours_end):
                outside_hours.append(p.name)

        if has_conflict:
            candidate += step
            continue

        # Determine tier
        if not outside_hours:
            tier_num, tier_label, tier_reason = TIER_1
        else:
            names = ", ".join(outside_hours)
            tier_num, tier_label, _ = TIER_2
            tier_reason = f"Outside working hours for: {names}"

        # Compute score: owner's preferred hours + counterparty hour quality
        owner_score = _score_slot(candidate, preferred_hours, avoid_hours, owner_timezone)
        counterparty_score = _score_counterparty_hours(candidate, participants, owner_timezone)
        # Weight: 50% owner preference, 50% counterparty quality
        # This surfaces 7 PM ET / 9 AM Sydney over 9 AM ET / 11 PM Sydney
        score = 0.5 * owner_score + 0.5 * counterparty_score

        local_times = {
            p.name: _format_local(candidate, slot_end, p.timezone)
            for p in participants
        }

        results.append(SlotResult(
            start_utc=candidate.strftime("%Y-%m-%dT%H:%M:%SZ"),
            end_utc=slot_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            tier=tier_num,
            tier_label=tier_label,
            tier_reason=tier_reason,
            local_times=local_times,
            score=score,
        ))

        candidate += step

    # Sort: tier ascending, then score descending
    results.sort(key=lambda s: (s.tier, -s.score))
    return results[:max_results]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _round_up_to_step(dt: datetime, step_minutes: int) -> datetime:
    """Round datetime up to the nearest step boundary."""
    minutes = dt.minute
    remainder = minutes % step_minutes
    if remainder == 0:
        return dt.replace(second=0, microsecond=0)
    delta = step_minutes - remainder
    return (dt + timedelta(minutes=delta)).replace(second=0, microsecond=0)


def _has_overlap(
    slot_start: datetime,
    slot_end: datetime,
    busy_blocks: list[BusyBlock],
) -> bool:
    """Return True if [slot_start, slot_end) overlaps any busy block."""
    for block in busy_blocks:
        if slot_start < block.end and slot_end > block.start:
            return True
    return False


def _within_working_hours(
    slot_start: datetime,
    slot_end: datetime,
    timezone: str,
    wh_start: str,
    wh_end: str,
) -> bool:
    """
    Return True if the entire slot falls within working hours in `timezone`.
    Both wh_start and wh_end are "HH:MM" strings (local time).
    """
    tz = ZoneInfo(timezone)
    local_start = slot_start.astimezone(tz)
    local_end = slot_end.astimezone(tz)

    # Parse working hours
    wh_s_h, wh_s_m = map(int, wh_start.split(":"))
    wh_e_h, wh_e_m = map(int, wh_end.split(":"))
    wh_s = time(wh_s_h, wh_s_m)
    wh_e = time(wh_e_h, wh_e_m)

    slot_s = local_start.time()
    slot_e = local_end.time()

    # Slot spans midnight in local timezone (e.g. 23:30–00:00) — outside working hours
    if slot_e <= slot_s:
        return False

    return slot_s >= wh_s and slot_e <= wh_e


def _score_counterparty_hours(
    slot_start: datetime,
    participants: list[Participant],
    owner_timezone: str,
) -> float:
    """
    Score a slot based on how reasonable it is for non-owner participants.
    Rewards slots where participants are in their core morning/afternoon hours.
    Penalises midnight/early-AM slots even if technically "within working hours."

    Returns average quality score across all non-owner participants. Range 0.0–1.0.
    """
    non_owners = [p for p in participants if p.timezone != owner_timezone]
    if not non_owners:
        return 1.0  # Only owner, no counterparty penalty

    scores = []
    for p in non_owners:
        tz = ZoneInfo(p.timezone)
        local_hour = slot_start.astimezone(tz).hour
        # Prime business hours → best
        if 9 <= local_hour <= 16:
            scores.append(1.0)
        # Early morning or late afternoon → acceptable
        elif 7 <= local_hour <= 8 or local_hour == 17:
            scores.append(0.6)
        # Very early or evening → poor
        elif 6 <= local_hour <= 18:
            scores.append(0.3)
        # Midnight / deep night → worst
        else:
            scores.append(0.0)

    return sum(scores) / len(scores)


def _score_slot(
    slot_start: datetime,
    preferred_hours: list[int],
    avoid_hours: list[int],
    owner_timezone: str,
) -> float:
    """
    Score a slot based on owner's time-of-day preferences.
    Higher = better. Range: 0.0–1.0
    """
    tz = ZoneInfo(owner_timezone)
    local_hour = slot_start.astimezone(tz).hour

    if local_hour in preferred_hours:
        return 1.0
    if local_hour in avoid_hours:
        return 0.1
    # Morning slightly preferred over afternoon
    if 8 <= local_hour < 12:
        return 0.7
    if 12 <= local_hour < 17:
        return 0.5
    return 0.3


def _format_local(start_utc: datetime, end_utc: datetime, timezone: str) -> str:
    """Format a UTC slot as a human-readable local time string."""
    tz = ZoneInfo(timezone)
    local_start = start_utc.astimezone(tz)
    local_end = end_utc.astimezone(tz)

    tz_abbr = local_start.strftime("%Z")
    date_str = local_start.strftime("%a %b %-d")
    time_range = f"{local_start.strftime('%-I:%M %p')}–{local_end.strftime('%-I:%M %p')}"

    return f"{date_str}, {time_range} {tz_abbr}"


# ---------------------------------------------------------------------------
# CLI entry point (used by the skill)
# ---------------------------------------------------------------------------

def main():
    """
    CLI interface: reads JSON from stdin, writes JSON to stdout.

    Input JSON schema:
    {
      "participants": [
        {
          "name": "...",
          "email": "...",
          "timezone": "...",
          "working_hours_start": "09:00",
          "working_hours_end": "18:00"
        }
      ],
      "busy_blocks": {
        "email@example.com": [
          {"start": "2026-04-21T13:00:00Z", "end": "2026-04-21T14:00:00Z"}
        ]
      },
      "window_start": "2026-04-21T00:00:00Z",
      "window_end":   "2026-04-25T23:59:59Z",
      "duration_minutes": 30,
      "step_minutes": 30,
      "max_results": 6,
      "preferred_hours": [9, 10, 11, 14, 15, 16],
      "avoid_hours": [12, 13],
      "owner_timezone": "America/New_York"
    }

    Output: JSON array of SlotResult objects.
    """
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        logger.error("main | invalid_json_input | error=%s", str(e))
        print(json.dumps({"error": f"Invalid JSON input: {e}"}))
        sys.exit(1)

    participants = [
        Participant(
            name=p["name"],
            email=p["email"],
            timezone=p["timezone"],
            working_hours_start=p.get("working_hours_start", "09:00"),
            working_hours_end=p.get("working_hours_end", "18:00"),
        )
        for p in payload["participants"]
    ]

    busy_blocks: dict[str, list[BusyBlock]] = {}
    for email, blocks in payload.get("busy_blocks", {}).items():
        busy_blocks[email] = [
            BusyBlock(
                start=datetime.fromisoformat(b["start"].replace("Z", "+00:00")),
                end=datetime.fromisoformat(b["end"].replace("Z", "+00:00")),
            )
            for b in blocks
        ]

    window_start = datetime.fromisoformat(
        payload["window_start"].replace("Z", "+00:00")
    )
    window_end = datetime.fromisoformat(
        payload["window_end"].replace("Z", "+00:00")
    )

    slots = find_slots(
        participants=participants,
        busy_blocks=busy_blocks,
        window_start=window_start,
        window_end=window_end,
        duration_minutes=payload.get("duration_minutes", 30),
        step_minutes=payload.get("step_minutes", 30),
        max_results=payload.get("max_results", 6),
        preferred_hours=payload.get("preferred_hours"),
        avoid_hours=payload.get("avoid_hours"),
        owner_timezone=payload.get("owner_timezone", "America/New_York"),
    )

    print(json.dumps([asdict(s) for s in slots], indent=2))


if __name__ == "__main__":
    main()
