"""
calendar_client.py — Wrapper around the `gws` Google Workspace CLI.

Provides Python-friendly interfaces for:
  - Fetching freebusy data
  - Creating calendar events
  - Listing accessible calendars

All methods raise CalendarError on failure rather than returning None,
so callers can catch and handle gracefully.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class CalendarError(Exception):
    """Raised when a gws CLI call fails or returns an error."""
    pass


@dataclass
class BusyBlock:
    start: datetime  # UTC-aware
    end: datetime    # UTC-aware


# ---------------------------------------------------------------------------
# FreeBusy
# ---------------------------------------------------------------------------

def get_freebusy(
    emails: list[str],
    window_start: datetime,
    window_end: datetime,
) -> dict[str, list[BusyBlock]]:
    """
    Query Google Calendar freebusy for a list of emails over a time window.

    Returns: {email: [BusyBlock, ...], ...}
    Calendars with errors (e.g. access denied) are returned as empty lists
    with a warning printed to stderr.
    """
    body = {
        "timeMin": window_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timeMax": window_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timeZone": "UTC",
        "items": [{"id": email} for email in emails],
    }

    result = _gws_run(
        ["calendar", "freebusy", "query"],
        json_body=body,
    )

    busy_map: dict[str, list[BusyBlock]] = {}
    calendars = result.get("calendars", {})

    for email in emails:
        cal_data = calendars.get(email, {})
        errors = cal_data.get("errors", [])
        if errors:
            logger.warning(
                "get_freebusy | calendar_access_error | email=%s | errors=%s",
                email, errors
            )
            busy_map[email] = []
            continue

        busy_map[email] = [
            BusyBlock(
                start=datetime.fromisoformat(b["start"].replace("Z", "+00:00")),
                end=datetime.fromisoformat(b["end"].replace("Z", "+00:00")),
            )
            for b in cal_data.get("busy", [])
        ]

    return busy_map


# ---------------------------------------------------------------------------
# Event creation
# ---------------------------------------------------------------------------

def create_event(
    title: str,
    start_utc: str,     # ISO 8601, e.g. "2026-04-21T14:00:00Z"
    end_utc: str,
    attendee_emails: list[str],
    owner_timezone: str = "America/New_York",
    description: str = "",
    add_meet: bool = True,
) -> dict:
    """
    Create a Google Calendar event and send invites to all attendees.

    Returns the created event resource dict.
    """
    event_body: dict = {
        "summary": title,
        "description": description,
        "start": {
            "dateTime": start_utc.replace("Z", ":00Z") if not start_utc.endswith(":00Z") else start_utc,
            "timeZone": owner_timezone,
        },
        "end": {
            "dateTime": end_utc.replace("Z", ":00Z") if not end_utc.endswith(":00Z") else end_utc,
            "timeZone": owner_timezone,
        },
        "attendees": [{"email": email} for email in attendee_emails],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 10},
            ],
        },
    }

    if add_meet:
        event_body["conferenceData"] = {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }

    params = {
        "calendarId": "primary",
        "sendUpdates": "all",
    }
    if add_meet:
        params["conferenceDataVersion"] = "1"

    result = _gws_run(
        ["calendar", "events", "insert"],
        params=params,
        json_body=event_body,
    )

    return result


# ---------------------------------------------------------------------------
# Calendar list
# ---------------------------------------------------------------------------

def list_calendars() -> list[dict]:
    """
    Return all calendars accessible to the authenticated user.
    Each item has at minimum: id, summary, accessRole, timeZone.
    """
    result = _gws_run(
        ["calendar", "calendarList", "list"],
        params={"maxResults": 50},
    )
    return result.get("items", [])


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _gws_run(
    args: list[str],
    params: Optional[dict] = None,
    json_body: Optional[dict] = None,
) -> dict:
    """
    Run a gws command and return parsed JSON response.
    Raises CalendarError if the command fails or returns an API error.
    """
    cmd = ["gws"] + args

    if params:
        cmd += ["--params", json.dumps(params)]
    if json_body:
        cmd += ["--json", json.dumps(json_body)]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
    except subprocess.TimeoutExpired:
        logger.error("_gws_run | timeout | cmd=%s", " ".join(cmd))
        raise CalendarError(f"gws command timed out: {' '.join(cmd)}")
    except FileNotFoundError:
        logger.error("_gws_run | gws_not_found")
        raise CalendarError("gws not found. Is it installed at /opt/homebrew/bin/gws?")

    if result.returncode != 0:
        raise CalendarError(
            f"gws error (exit {result.returncode}): {result.stderr.strip() or result.stdout.strip()}"
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise CalendarError(f"Failed to parse gws output as JSON: {e}\nRaw: {result.stdout[:500]}")

    # Check for Google API error in response body
    if "error" in data:
        err = data["error"]
        raise CalendarError(
            f"Google API error {err.get('code', '?')}: {err.get('message', str(err))}"
        )

    return data


# ---------------------------------------------------------------------------
# CLI entry point — quick test / debug
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from datetime import timezone
    logging.basicConfig(level=logging.INFO)

    print("Testing calendar_client.py...")

    # Test: list calendars
    try:
        cals = list_calendars()
        print(f"✓ list_calendars: {len(cals)} calendars found")
        for c in cals[:3]:
            print(f"  - {c['id']} ({c.get('accessRole', '?')})")
    except CalendarError as e:
        print(f"✗ list_calendars failed: {e}")
        sys.exit(1)

    # Test: freebusy for today
    try:
        now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59)
        busy = get_freebusy(["REDACTED@example.com"], now, end)
        print(f"✓ get_freebusy: {sum(len(v) for v in busy.values())} busy blocks today")
        for email, blocks in busy.items():
            for b in blocks:
                print(f"  - {email}: {b.start.strftime('%H:%M')}–{b.end.strftime('%H:%M')} UTC")
    except CalendarError as e:
        print(f"✗ get_freebusy failed: {e}")
        sys.exit(1)

    print("\nAll checks passed.")
