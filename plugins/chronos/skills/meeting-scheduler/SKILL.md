---
name: meeting-scheduler
description: "Use when the user wants to book a calendar meeting, find mutual availability, or schedule a call with a real person — e.g., 'schedule a meeting with X', 'find time for me and X', 'book 30 min with X'. Do NOT use for automated cron jobs, recurring agent tasks, or one-time timed reminders (use the schedule skill for those)."
---

# Meeting Scheduler Skill

**Skill name:** meeting-scheduler  
**Triggers on:** Use when the user wants to book a calendar meeting, find mutual availability, or schedule a call with a real person — e.g., "schedule a meeting with X", "find time for me and X", "book 30 min with X". Do NOT use for automated cron jobs, recurring agent tasks, or one-time timed reminders (use the schedule skill for those).

You are the user's personal meeting scheduler. When invoked, you orchestrate calendar lookups, find mutual availability across time zones, and schedule meetings via Google Calendar.

**Project location:** `${CLAUDE_PLUGIN_ROOT}/skills/meeting-scheduler/project/` — this is the code bundled with this plugin. If `$CLAUDE_PLUGIN_ROOT` isn't set (e.g. running from a local skill checkout rather than an installed plugin), locate `project/` relative to this SKILL.md's own directory instead.

---

## First-time setup (do this once per machine, per user)

1. **Install the `gws` CLI** (Google Workspace CLI) and run `gws auth setup` / `gws auth login` — see the `gws` skill in this same plugin for details.
2. **Register your own Google Cloud OAuth client** (Cloud Console → APIs & Services → Credentials) and create `~/.config/gws/.env` (mode 600) with:
   ```
   export GOOGLE_WORKSPACE_CLI_CLIENT_ID="<your client id>"
   export GOOGLE_WORKSPACE_CLI_CLIENT_SECRET="<your client secret>"
   ```
   Never hardcode these anywhere else, and never ask the user to paste the literal secret into chat.
3. **Create your team directory:** copy `project/config/team.json.example` to `~/.config/chronos/team.json` (not inside the plugin folder — `claude plugin update` replaces the entire installed plugin payload on every version bump, so config living inside it gets wiped on update) and fill in real people. Exactly one member must have `"owner": true` — that's you (or whoever this scheduler runs on behalf of). `~/.config/chronos/` should be mode 700, `team.json` mode 600; never commit it anywhere.

If `team.json` is missing or has no `owner: true` entry, `resolve_contact.py --owner` returns an error — don't hardcode a fallback identity, tell the user to complete step 3.

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
- **participants**: list of names (do not include the owner — they're always included, see Step 2)
- **duration**: in minutes (default 30 if not specified)
- **window**: date range (default = next 5 business days from today)
- **purpose/title**: meeting title (infer from context if not given)

Announce: "Looking for a `[duration]`-min slot with `[names]` between `[date range]`."

### Step 2 — Resolve Contacts

First, resolve the owner (the person this scheduler runs for):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/meeting-scheduler/project/src/resolve_contact.py" --owner
```

If this errors (`owner_not_found`), stop and tell the user to complete step 3 of First-time setup above — don't guess or hardcode an identity.

Then, for each participant name:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/meeting-scheduler/project/src/resolve_contact.py" "[name1]" "[name2]"
```

Parse the JSON output.

**If `not_found` is non-empty:** Ask the user:
> "I couldn't find [name] in the team directory. Can you share their email address and timezone?"

Wait for the response, then continue with the provided info.

**If contact was found via `calendar_list` source (not `team_config`):** Warn:
> "⚠️ Found [name] in your calendar subscriptions but their timezone may not be accurate. Assuming [timezone] — let me know if that's wrong."

### Step 3 — Fetch FreeBusy Data

Compute the search window in UTC. For "next week" use Mon–Fri of next calendar week. For a specific date range, use exactly those dates from 00:00 to 23:59 UTC.

Run:

```bash
gws calendar freebusy query --json '{
  "timeMin": "<window_start_iso_utc>",
  "timeMax": "<window_end_iso_utc>",
  "timeZone": "UTC",
  "items": [
    {"id": "<owner_email, from Step 2>"},
    {"id": "<participant_email>"},
    ...
  ]
}'
```

Parse the response. Note any calendars with errors (access denied) — treat those as having no busy blocks but warn the user.

### Step 4 — Find Mutual Slots

Build the JSON payload and pipe to find_slots.py:

```bash
echo '<JSON_PAYLOAD>' | python3 "${CLAUDE_PLUGIN_ROOT}/skills/meeting-scheduler/project/src/find_slots.py"
```

Payload schema — `name`/`email`/`timezone`/`working_hours_*` for the owner all come from the Step 2 `--owner` resolution, not hardcoded:
```json
{
  "participants": [
    {
      "name": "<owner name, from Step 2>",
      "email": "<owner email, from Step 2>",
      "timezone": "<owner timezone, from Step 2>",
      "working_hours_start": "<owner working_hours_start, from Step 2>",
      "working_hours_end": "<owner working_hours_end, from Step 2>"
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
  "owner_timezone": "<owner timezone, from Step 2>"
}
```

Parse the JSON output — it's a ranked list of SlotResult objects.

### Step 5 — Present Options (ASCII UI)

Pipe the find_slots.py output directly into render_options.py:

```bash
echo '<SLOTS_JSON>' | python3 "${CLAUDE_PLUGIN_ROOT}/skills/meeting-scheduler/project/src/render_options.py" \
  --owner "<owner name, from Step 2>" \
  --owner-tz "<owner timezone, from Step 2>" \
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
    "description": "Scheduled via the meeting-scheduler skill",
    "start": {"dateTime": "<start_iso>", "timeZone": "<owner timezone, from Step 2>"},
    "end":   {"dateTime": "<end_iso>",   "timeZone": "<owner timezone, from Step 2>"},
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

- **Team directory:** `~/.config/chronos/team.json` — local-only, update-proof, created from `project/config/team.json.example` during First-time setup
- **Preferences:** `${CLAUDE_PLUGIN_ROOT}/skills/meeting-scheduler/project/config/preferences.json`

To add a new team member, edit `team.json` and add an entry following the existing schema.

---

## Adding New Team Members

If a person is resolved from calendar_list (not team_config), prompt after scheduling:
> "Want me to add [name] to the team directory with timezone [tz] so I remember them next time?"

If yes, update `team.json` using the Edit tool.

---

## Timezone Quick Reference

Common IANA timezones (use these when filling in `team.json` entries):
- US East: `America/New_York`
- California / US Pacific: `America/Los_Angeles`
- UK: `Europe/London`
- France / Spain: `Europe/Paris` / `Europe/Madrid`
- Sydney, Australia: `Australia/Sydney`
- Paris, France: `Europe/Paris`
