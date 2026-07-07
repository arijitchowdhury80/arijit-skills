"""
render_options.py — Plain ASCII scheduler UI.
No Unicode box drawing. Works in every terminal.

Usage:
    python3 render_options.py \
        --slots '<json>' \
        --owner "Arijit" --owner-tz "America/New_York" \
        --participants '{"Jordan Kim": "Australia/Sydney"}' \
        --busy-blocks '<json>' \
        --duration 30 \
        --window-label "Thu Apr 16 + Fri Apr 17"
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

W = 66


def div(char="="):
    return char * W


def row(text="", pad=" "):
    return text


def timeline_bar(
    tz_str: str,
    busy_blocks_for_person: list[dict],
    highlight_slots: list[dict],
    day_label: str,
) -> list[str]:
    """
    Render a 14-hour ASCII timeline bar for one person (8 AM to 10 PM local).
    Each character = 30 min. Total = 28 chars wide.
    Symbols: . = free, # = busy, * = available meeting slot
    """
    tz = ZoneInfo(tz_str)
    HOURS = 14      # 8 AM to 10 PM
    BLOCKS = HOURS * 2  # 28 half-hour blocks

    grid = list("." * BLOCKS)

    # Mark busy
    for b in busy_blocks_for_person:
        bs = datetime.fromisoformat(b["start"].replace("Z", "+00:00")).astimezone(tz)
        be = datetime.fromisoformat(b["end"].replace("Z", "+00:00")).astimezone(tz)
        for i in range(BLOCKS):
            block_hour = 8 + i * 0.5
            bs_h = bs.hour + bs.minute / 60
            be_h = be.hour + be.minute / 60
            if bs_h <= block_hour < be_h:
                grid[i] = "#"

    # Mark available slots
    for slot in highlight_slots:
        ss = datetime.fromisoformat(slot["start_utc"].replace("Z", "+00:00")).astimezone(tz)
        se = datetime.fromisoformat(slot["end_utc"].replace("Z", "+00:00")).astimezone(tz)
        for i in range(BLOCKS):
            block_hour = 8 + i * 0.5
            ss_h = ss.hour + ss.minute / 60
            se_h = se.hour + se.minute / 60
            if ss_h <= block_hour < se_h and grid[i] == ".":
                grid[i] = "*"

    bar = "".join(grid)

    lines = []
    lines.append(f"  {day_label}")
    lines.append(f"   8a  9a  10  11  12p  1p  2p  3p  4p  5p  6p  7p  8p  9p")
    lines.append(f"   |{bar}|")
    lines.append(f"   . = free   # = busy   * = open slot")
    return lines


def render(
    slots: list[dict],
    owner_name: str,
    owner_tz: str,
    participants: dict[str, str],
    duration: int,
    window_label: str,
    busy_blocks: dict[str, list[dict]],
) -> str:
    lines = []

    all_names = [owner_name] + list(participants.keys())
    all_tzs = {owner_name: owner_tz, **participants}

    # -------------------------------------------------------------------------
    # HEADER
    # -------------------------------------------------------------------------
    lines.append(div("="))
    lines.append(f" SCHEDULER  |  {duration} min with {' + '.join(p for p in participants)}")
    lines.append(f" {window_label}  |  Live calendar data")
    lines.append(div("="))
    lines.append("")

    # -------------------------------------------------------------------------
    # AVAILABILITY TIMELINE
    # -------------------------------------------------------------------------
    lines.append(" AVAILABILITY")
    lines.append(div("-"))
    lines.append("")

    for name in all_names:
        tz_str = all_tzs[name]

        # Find this person's busy blocks
        person_busy = []
        for k, v in busy_blocks.items():
            if name.lower().split()[0] in k.lower() or k.lower().split("@")[0].replace(".", " ") in name.lower():
                person_busy = v
                break

        # Get local date label for first slot
        if slots:
            first_utc = datetime.fromisoformat(slots[0]["start_utc"].replace("Z", "+00:00"))
            local_dt = first_utc.astimezone(ZoneInfo(tz_str))
            local_time_str = local_times_for_person(slots[0], name, tz_str)
            day_label = f"{name}  ({local_dt.strftime('%a %b %-d')}  {local_dt.strftime('%Z')})"
        else:
            day_label = name

        tl = timeline_bar(tz_str, person_busy, slots, day_label)
        lines.extend(["  " + l for l in tl])
        lines.append("")

    # -------------------------------------------------------------------------
    # OPTIONS
    # -------------------------------------------------------------------------
    lines.append(div("-"))
    lines.append(" OPTIONS")
    lines.append(div("-"))
    lines.append("")

    if not slots:
        lines.append("  No mutual free time found in this window.")
        lines.append("  Type 'more' to search next week.")
    else:
        option_notes = [
            "RECOMMENDED  -- his prime morning, reasonable for you",
            "Good -- his late morning",
            "OK   -- getting late for you",
            "Late -- but available",
        ]
        for i, slot in enumerate(slots):
            tag = f"  [{i + 1}]"
            note = option_notes[i] if i < len(option_notes) else ""
            rec = "  <-- PICK THIS" if i == 0 else ""
            lines.append(f"{tag}  {note}{rec}")
            for pname in all_names:
                local = local_times_for_person(slot, pname, all_tzs[pname])
                lines.append(f"       {pname:<20} {local}")
            lines.append("")

    # -------------------------------------------------------------------------
    # FOOTER
    # -------------------------------------------------------------------------
    lines.append(div("-"))
    lines.append("  Type a number to book  |  'none' to try next week")
    lines.append(div("="))

    return "\n".join(lines)


def local_times_for_person(slot: dict, name: str, tz_str: str) -> str:
    """Get local time string for a participant, fallback to computing it."""
    # Try to find in local_times by name
    for k, v in slot.get("local_times", {}).items():
        if name.lower() in k.lower() or k.lower() in name.lower():
            return v
    # Compute it
    tz = ZoneInfo(tz_str)
    start = datetime.fromisoformat(slot["start_utc"].replace("Z", "+00:00")).astimezone(tz)
    end = datetime.fromisoformat(slot["end_utc"].replace("Z", "+00:00")).astimezone(tz)
    return f"{start.strftime('%a %b %-d, %-I:%M %p')} - {end.strftime('%-I:%M %p')} {start.strftime('%Z')}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slots", required=True)
    parser.add_argument("--owner", default="Arijit")
    parser.add_argument("--owner-tz", default="America/New_York")
    parser.add_argument("--participants", default="{}")
    parser.add_argument("--duration", type=int, default=30)
    parser.add_argument("--window-label", default="This week")
    parser.add_argument("--busy-blocks", default="{}")
    args = parser.parse_args()

    print(render(
        slots=json.loads(args.slots),
        owner_name=args.owner,
        owner_tz=args.owner_tz,
        participants=json.loads(args.participants),
        duration=args.duration,
        window_label=args.window_label,
        busy_blocks=json.loads(args.busy_blocks),
    ))


if __name__ == "__main__":
    main()
