"""
resolve_contact.py — Resolve a person's name to their email and timezone.

Resolution order:
  1. config/team.json — name/alias match (case-insensitive)
  2. gws calendar calendarList — check subscribed calendars
  3. Return None → caller should ask user for email

CLI: python resolve_contact.py "david"
     Returns JSON: {"name": "Jordan Kim", "email": "...", "timezone": "...", ...}
     Or: {"error": "not_found", "query": "david"}
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "config" / "team.json"


# ---------------------------------------------------------------------------
# Main resolver
# ---------------------------------------------------------------------------

def resolve(query: str, team_config_path: Path = CONFIG_PATH) -> Optional[dict]:
    """
    Resolve a name query to a contact dict.

    Returns dict with keys: name, email, timezone, working_hours_start,
    working_hours_end, location (all optional except name + email + timezone).
    Returns None if not found.
    """
    query_clean = query.strip().lower()

    # Step 1: team.json lookup
    contact = _lookup_team_json(query_clean, team_config_path)
    if contact:
        return contact

    # Step 2: gws calendar list
    contact = _lookup_calendar_list(query_clean)
    if contact:
        return contact

    return None


def resolve_multiple(queries: list[str], team_config_path: Path = CONFIG_PATH) -> tuple[list[dict], list[str]]:
    """
    Resolve multiple names. Returns (found, not_found) where:
    - found: list of contact dicts
    - not_found: list of original query strings that couldn't be resolved
    """
    found = []
    not_found = []
    for q in queries:
        result = resolve(q, team_config_path)
        if result:
            found.append(result)
        else:
            not_found.append(q)
    return found, not_found


# ---------------------------------------------------------------------------
# Lookup strategies
# ---------------------------------------------------------------------------

def _lookup_team_json(query: str, config_path: Path) -> Optional[dict]:
    """Search team.json by name, alias, or email fragment."""
    if not config_path.exists():
        return None

    with open(config_path) as f:
        team = json.load(f)

    query = query.strip().lower()

    for member in team.get("members", []):
        # Skip owner entry when resolving (owner is always included separately)
        name_lower = member["name"].lower()
        email_lower = member["email"].lower()
        aliases = [a.lower() for a in member.get("aliases", [])]

        if (
            query == name_lower
            or query in name_lower
            or query in email_lower
            or query in aliases
            or any(query in alias for alias in aliases)
        ):
            return {
                "name": member["name"],
                "email": member["email"],
                "timezone": member.get("timezone", "UTC"),
                "working_hours_start": member.get("working_hours", {}).get("start", "09:00"),
                "working_hours_end": member.get("working_hours", {}).get("end", "18:00"),
                "location": member.get("location", ""),
                "source": "team_config",
            }

    return None


def get_owner(team_config_path: Path = CONFIG_PATH) -> Optional[dict]:
    """
    Return the team.json member flagged `"owner": true` — the person this
    scheduler is running on behalf of. Used so the skill never has to
    hardcode a specific person's email/timezone.
    Returns None if team.json is missing or has no owner flagged.
    """
    if not team_config_path.exists():
        return None

    with open(team_config_path) as f:
        team = json.load(f)

    for member in team.get("members", []):
        if member.get("owner"):
            return {
                "name": member["name"],
                "email": member["email"],
                "timezone": member.get("timezone", "UTC"),
                "working_hours_start": member.get("working_hours", {}).get("start", "09:00"),
                "working_hours_end": member.get("working_hours", {}).get("end", "18:00"),
                "location": member.get("location", ""),
            }

    return None


def _lookup_calendar_list(query: str) -> Optional[dict]:
    """Check subscribed calendars via gws for a matching email."""
    try:
        result = subprocess.run(
            ["gws", "calendar", "calendarList", "list",
             "--params", '{"maxResults": 50}'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        for item in data.get("items", []):
            cal_id = item.get("id", "").lower()
            summary = item.get("summary", "").lower()
            # Extract name from email: jordan.kim@example.com → "jordan kim"
            name_from_email = re.sub(r"@.*", "", cal_id).replace(".", " ").replace("-", " ")

            if (
                query in cal_id
                or query in summary
                or query in name_from_email
                or any(part in name_from_email for part in query.split())
            ):
                # Best effort: we know their email but not their timezone
                return {
                    "name": _humanize_email(item["id"]),
                    "email": item["id"],
                    "timezone": item.get("timeZone", "UTC"),
                    "working_hours_start": "09:00",
                    "working_hours_end": "18:00",
                    "location": "",
                    "source": "calendar_list",
                    "warning": "Timezone may be incorrect — not in team config. Please verify.",
                }

    except subprocess.TimeoutExpired:
        logger.warning("_lookup_calendar_list | gws_timeout | query=%s", query)
    except json.JSONDecodeError as e:
        logger.warning("_lookup_calendar_list | bad_json | query=%s | error=%s", query, str(e))
    except FileNotFoundError:
        logger.error("_lookup_calendar_list | gws_not_found | query=%s", query)

    return None


def _humanize_email(email: str) -> str:
    """Convert jordan.kim@example.com → Jordan Kim."""
    local = email.split("@")[0]
    parts = re.split(r"[.\-_]", local)
    return " ".join(p.capitalize() for p in parts if p)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """
    Usage: python resolve_contact.py "david"
           python resolve_contact.py "david" "sarah" "metin"
           python resolve_contact.py --owner

    Outputs JSON: list of resolved contacts + list of not-found names.
    `--owner` returns the team.json member flagged owner:true instead.
    """
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: resolve_contact.py <name> [name2 ...] | --owner"}))
        sys.exit(1)

    if sys.argv[1] == "--owner":
        owner = get_owner()
        if owner is None:
            print(json.dumps({"error": "owner_not_found", "hint": "No member with \"owner\": true in config/team.json"}))
            sys.exit(1)
        print(json.dumps({"owner": owner}, indent=2))
        return

    queries = sys.argv[1:]
    found, not_found = resolve_multiple(queries)

    print(json.dumps({
        "found": found,
        "not_found": not_found,
    }, indent=2))


if __name__ == "__main__":
    main()
