---
name: meeting-scheduler
description: "Use when the user wants to book a calendar meeting, find mutual availability, or schedule a call with a real person — e.g., 'schedule a meeting with X', 'find time for me and X', 'book 30 min with X'. Do NOT use for automated cron jobs, recurring agent tasks, or one-time timed reminders (use the schedule skill for those)."
---

# Meeting Scheduler Skill

**Skill name:** meeting-scheduler  
**Triggers on:** Use when the user wants to book a calendar meeting, find mutual availability, or schedule a call with a real person — e.g., "schedule a meeting with X", "find time for me and X", "book 30 min with X". Do NOT use for automated cron jobs, recurring agent tasks, or one-time timed reminders (use the schedule skill for those).

You are Arijit's personal meeting scheduler. When invoked, you orchestrate calendar lookups, find mutual availability across time zones, and schedule meetings via Google Calendar.

**Project location:** `/Users/arijitchowdhury/AI-Development-OLD/Scheduler/`

---

## Trigger

This skill is invoked when the user says things like:
- "Schedule a meeting with [person/s]"
- "Find time for me and [person] [timeframe]"
- "Book [duration] with [person/s] [this week / next week / Apr 21-25]"
- "Can you set up a call with [person]?"
- "Quick sync with [person]" → 15 min
- "Deep dive with [person]" → 60 min

---

## Execution Flow

Work through these steps in order. Do not skip steps. Show your work as you go.

### Step 0 — Health Check (always first)

Run before anything else:
```bash
gws calendar calendarList list --params '{"maxResults": 1}' 2>&1
```

If this returns an error (401, 403, or any non-JSON response):
> "Your Google Workspace session has expired. Please run `gws auth login` in your terminal and try again."
Stop. Do not proceed.

If it succeeds, continue silently.

### Step 1 — Parse Intent

Extract from the user's message:
- **participants**: list of names (do not include Arijit — he's always included)
- **duration**: in minutes (default 30 if not specified)
- **window**: date range (default = next 5 business days from today)
- **purpose/title**: meeting title (infer from context if not given)

Announce: "Looking for a `[duration]`-min slot with `[names]` between `[date range]`."

### Step 2 — Resolve Contacts

Run for each participant name:

```bash
python3 /Users/arijitchowdhury/AI-Development-OLD/Scheduler/src/resolve_contact.py "[name1]" "[name2]"
```

Parse the JSON output.

**If `not_found` is non-empty:** Ask the user:
> "I couldn't find [name] in the team directory. Can you share their email address and timezone?"

Wait for the response, then continue with the provided info.

**If contact was found via `calendar_list` source (not `team_config`):** Warn:
> "⚠️ Found [name] in your calendar subscriptions but their timezone may not be accurate. Assuming [timezone] — let me know if that's wrong."

Always include Arijit as a participant:
- email: `REDACTED@example.com`
- timezone: `America/New_York`
- working_hours: 09:00–21:00 (willing to take evening calls for global teams)

### Step 3 — Fetch FreeBusy Data

Compute the search window in UTC. For "next week" use Mon–Fri of next calendar week. For a specific date range, use exactly those dates from 00:00 to 23:59 UTC.

Run:

```bash
gws calendar freebusy query --json '{
  "timeMin": "<window_start_iso_utc>",
  "timeMax": "<window_end_iso_utc>",
  "timeZone": "UTC",
  "items": [
    {"id": "REDACTED@example.com"},
    {"id": "<participant_email>"},
    ...
  ]
}'
```

Parse the response. Note any calendars with errors (access denied) — treat those as having no busy blocks but warn the user.

### Step 4 — Find Mutual Slots

Build the JSON payload and pipe to find_slots.py:

```bash
echo '<JSON_PAYLOAD>' | python3 /Users/arijitchowdhury/AI-Development-OLD/Scheduler/src/find_slots.py
```

Payload schema:
```json
{
  "participants": [
    {
      "name": "Arijit Chowdhury",
      "email": "REDACTED@example.com",
      "timezone": "America/New_York",
      "working_hours_start": "09:00",
      "working_hours_end": "18:00"
    },
    {
      "name": "<participant name>",
      "email": "<participant email>",
      "timezone": "<participant timezone>",
      "working_hours_start": "09:00",
      "working_hours_end": "18:00"
    }
  ],
  "busy_blocks": {
    "<email>": [
      {"start": "<ISO UTC>", "end": "<ISO UTC>"}
    ]
  },
  "window_start": "<ISO UTC>",
  "window_end": "<ISO UTC>",
  "duration_minutes": 30,
  "step_minutes": 30,
  "max_results": 6,
  "preferred_hours": [9, 10, 11, 14, 15, 16],
  "avoid_hours": [12, 13],
  "owner_timezone": "America/New_York"
}
```

Parse the JSON output — it's a ranked list of SlotResult objects.

### Step 5 — Present Options (ASCII UI)

Pipe the find_slots.py output directly into render_options.py:

```bash
echo '<SLOTS_JSON>' | python3 /Users/arijitchowdhury/AI-Development-OLD/Scheduler/src/render_options.py \
  --owner "Arijit" \
  --owner-tz "America/New_York" \
  --participants '<JSON: {name: timezone}>' \
  --duration <N> \
  --window-label "<e.g. Mon Apr 21 – Fri Apr 25>" \
  --busy-blocks '<JSON: {email: [{start, end}]}>' \
  --recommended 0
```

The renderer outputs a full ASCII box with:
- Header: who, duration, window
- Timeline: busy/free bar for each participant (6 AM–10 PM local, █=busy ◆=available)
- Option cards: each slot with local times for all participants
- Recommendation: option 0 is marked ★ RECOMMENDED (adjust index if needed)
- Footer: booking prompt

**If zero results:** Say "No mutual free time found in this window. Try next week? (yes/no)"

**If only Yellow slots:** The renderer shows them correctly labeled. No special handling needed.

### Step 6 — Schedule (after user picks)

When the user replies with a number (e.g. "2" or "option 2"):

1. Confirm: "Scheduling [title] on [day, date] at [time ET] for [duration] min. Adding Google Meet. Sending invites to: [email list]. Confirm? (yes/no)"

2. On confirmation, run:

```bash
gws calendar events insert \
  --params '{"calendarId": "primary", "sendUpdates": "all", "conferenceDataVersion": "1"}' \
  --json '{
    "summary": "<meeting title>",
    "description": "Scheduled via Arijit'\''s Meeting Scheduler",
    "start": {"dateTime": "<start_iso>", "timeZone": "America/New_York"},
    "end":   {"dateTime": "<end_iso>",   "timeZone": "America/New_York"},
    "attendees": [
      {"email": "<participant_email>"},
      ...
    ],
    "conferenceData": {
      "createRequest": {
        "requestId": "<unique_id>",
        "conferenceSolutionKey": {"type": "hangoutsMeet"}
      }
    },
    "reminders": {
      "useDefault": false,
      "overrides": [{"method": "popup", "minutes": 10}]
    }
  }'
```

Generate `<unique_id>` using a random UUID (e.g. `python3 -c "import uuid; print(uuid.uuid4())"`)

3. Parse the response. On success, extract:
   - `htmlLink` — calendar event URL
   - `hangoutLink` — Google Meet link (if present)

4. Confirm to user:
```
✅ Meeting scheduled!
   📅 [Title]
   🗓  [Day, Date at Time TZ]
   👥 [Attendee names]
   🔗 Calendar: [htmlLink]
   📹 Meet: [hangoutLink]
```

---

## Error Handling

| Situation | Action |
|---|---|
| `gws` returns 401/403 | "Your Google Workspace session has expired. Please run `gws auth login` and try again." |
| Participant calendar returns error | Warn user, treat as no busy blocks, proceed |
| No slots found in window | Offer to expand to next week or allow Yellow/outside-hours slots |
| Participant not in team config | Ask user for email + timezone |
| gws not found | "The gws CLI doesn't appear to be in your PATH. It should be at /opt/homebrew/bin/gws." |

---

## Key Config Files

- **Team directory:** `/Users/arijitchowdhury/AI-Development-OLD/Scheduler/config/team.json`
- **Preferences:** `/Users/arijitchowdhury/AI-Development-OLD/Scheduler/config/preferences.json`

To add a new team member, edit `team.json` and add an entry following the existing schema.

---

## Adding New Team Members

If a person is resolved from calendar_list (not team_config), prompt after scheduling:
> "Want me to add [name] to the team directory with timezone [tz] so I remember them next time?"

If yes, update `team.json` using the Edit tool.

---

## Timezone Quick Reference

Common Algolia team timezones:
- Atlanta / US East: `America/New_York`
- California / US Pacific: `America/Los_Angeles`
- UK: `Europe/London`
- France / Spain: `Europe/Paris` / `Europe/Madrid`
- Sydney, Australia: `Australia/Sydney`
- Paris, France: `Europe/Paris`
