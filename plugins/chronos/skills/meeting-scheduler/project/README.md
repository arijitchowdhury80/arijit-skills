# Meeting Scheduler — Personal Assistant Module 1

Schedule meetings across time zones using natural language. Checks live Google Calendar availability and books with Google Meet.

---

## Prerequisites

1. **`gws` CLI** — Google Workspace CLI, installed at `/opt/homebrew/bin/gws`
   - Already installed and authenticated on this machine
   - If token expires: run `gws auth login` in your terminal

2. **Python 3.11+** — already installed

3. **The skill file** — already installed at `~/.claude/skills/scheduler.md`

---

## How to Use (the only thing you need to know)

Open any Claude Code session and say:

```
Schedule 30 min with David next week
```

```
Quick sync with Metin this week
```

```
Book a deep dive with the France team for next Thursday
```

Claude will:
1. Check your Google Calendar (live)
2. Check David's calendar (live)
3. Find mutual free slots
4. Show you options with a timeline
5. Book it when you pick a number

That's it. No commands to run. No app to open.

---

## Duration shortcuts

| You say | Duration |
|---|---|
| "quick sync" | 15 min |
| (nothing) | 30 min (default) |
| "deep dive" / "an hour" | 60 min |

## Search window

Scheduler always looks at **current week + next 2 weeks**, preferring sooner. No need to specify a date range unless you want to.

## External (customer) meetings

```
Schedule a call with customer John Smith (john@acme.com, US Pacific).
He's available Mon 2-4 PM PT or Tue 10 AM PT.
Internal attendees: me, Metin, Sarah.
```

For external meetings, provide the customer's preferred times. The scheduler checks internal availability against those times.

---

## Time zones — known team members

The scheduler knows these people automatically:

| Name | Location | Timezone |
|---|---|---|
| Arijit Chowdhury | Atlanta, GA | America/New_York |
| Jordan Kim | Sydney, AU | Australia/Sydney |
| David Barth | Paris, FR | Europe/Paris |
| Metin Ergener | USA | America/New_York |
| Casey Doe-Smith | UK | Europe/London |
| Debanshi Bheda | USA | America/New_York |
| Matthew Eisnor | USA | America/New_York |
| Piyush Patel | USA | America/New_York |
| Brian Weitz | USA | America/New_York |
| Jillian Lellis | USA | America/New_York |
| Massis Buyukkalender | Turkey | Europe/Istanbul |

**To add someone:** Edit `config/team.json`. Copy any existing entry as a template.

---

## Project structure

```
Scheduler/
├── src/
│   ├── find_slots.py        # Core algorithm: freebusy + timezone math → ranked slots
│   ├── resolve_contact.py   # Name → email + timezone lookup
│   ├── calendar_client.py   # Google Calendar API wrapper (via gws CLI)
│   └── render_options.py    # ASCII UI renderer
├── config/
│   ├── team.json            # Known team members + timezones
│   └── preferences.json     # Your defaults (timezone, preferred hours, duration)
├── tests/
│   ├── unit/                # 42 unit tests — run fast, no network
│   ├── integration/         # 9 live tests — hit real Google Calendar API
│   └── contract/            # 14 schema tests — validate output contracts
└── docs/
    ├── design.md            # Architecture spec
    └── workspace/scheduler/ # PRD, assumptions, pre-mortem
```

---

## Run the tests

```bash
# Fast — unit + contract (no network needed)
python3 -m pytest tests/unit/ tests/contract/ -v

# Full — includes live Google Calendar API calls
python3 -m pytest tests/ -v

# Expected: 65 passed
```

---

## Run the scripts directly (optional)

You don't need to do this — the skill handles it. But if you want to test manually:

```bash
# Resolve a contact by name
python3 src/resolve_contact.py "david"

# Check calendar client is working
python3 src/calendar_client.py

# Full pipeline: find slots for next week
echo '{
  "participants": [
    {"name": "Arijit", "email": "REDACTED@example.com",
     "timezone": "America/New_York", "working_hours_start": "09:00", "working_hours_end": "21:00"},
    {"name": "Jordan Kim", "email": "jordan.kim@example.com",
     "timezone": "Australia/Sydney", "working_hours_start": "09:00", "working_hours_end": "18:00"}
  ],
  "busy_blocks": {},
  "window_start": "2026-04-21T00:00:00Z",
  "window_end":   "2026-04-25T23:59:59Z",
  "duration_minutes": 30,
  "max_results": 6,
  "owner_timezone": "America/New_York"
}' | python3 src/find_slots.py
```

---

## Troubleshooting

**"Your Google Workspace session has expired"**
```bash
gws auth login
```

**"I couldn't find [name] in the team directory"**
Add them to `config/team.json` — copy any existing entry, fill in their email and timezone.

**Wrong timezone for someone**
Tell Claude: "David is actually in Melbourne, Australia/Melbourne" — it will update `team.json` automatically.

---

## What's next (v2)

- Tier 3/4: conflict resolution ("can we move this to fit?")
- Slack lookup: find people by Slack handle
- Group scheduling: 4+ people across 4+ timezones (works now, not battle-tested at scale)
- `gws people` API: full contact search by name (needs OAuth scope re-auth)
- Morning briefing module: next personal assistant agent after this one
