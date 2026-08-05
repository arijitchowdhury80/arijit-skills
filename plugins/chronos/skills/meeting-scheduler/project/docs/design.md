# Meeting Scheduler — Design Spec
**Date:** 2026-04-15  
**Author:** Arijit Chowdhury + Claude (co-architect)  
**Status:** v1.0 — Approved for implementation

---

## 1. Purpose

A Claude Code skill (`/scheduler`) that acts as a personal meeting scheduling assistant. Given a natural-language request ("Schedule 30 min with David next week"), it:

1. Resolves who the people are (email + timezone)
2. Fetches their calendar availability via Google Workspace CLI (`gws`)
3. Finds mutual free slots, ranked by a tier system
4. Presents options and creates the event on confirmation

**This is Module 1 of a broader personal assistant.** It handles the scheduling domain only.

---

## 2. Architecture

```
User: "Schedule 30 min with David and Sarah, Apr 21–25"
         │
         ▼
  [scheduler.md skill]
  Claude parses intent:
  - participants: ["David", "Sarah"]
  - duration: 30 min
  - window: Apr 21–25 2026
         │
         ├─► resolve_contact.py ──► team.json / gws calendar list
         │   Returns: [{name, email, timezone, working_hours}, ...]
         │
         ├─► calendar_client.py ──► gws calendar freebusy query
         │   Returns: {email: [{start, end}, ...], ...}  (busy blocks)
         │
         ├─► find_slots.py
         │   Input:  participants, busy_blocks, window, duration
         │   Output: [{start_utc, local_times, tier, score}, ...]  ranked
         │
         └─► Claude formats and presents options
                  │
                  └─► User picks → calendar_client.py creates event via gws
```

### Components

| Component | Responsibility | Type |
|---|---|---|
| `scheduler.md` | Skill entry point. Orchestrates flow, talks to user | Claude skill |
| `src/find_slots.py` | Pure slot-finding algorithm. No I/O. | Python module |
| `src/resolve_contact.py` | Name → email + timezone. Checks config, then gws | Python module |
| `src/calendar_client.py` | `gws` CLI wrapper: freebusy, create event | Python module |
| `config/team.json` | Known team members: email, timezone, working hours | JSON config |
| `config/preferences.json` | Arijit's defaults: timezone, working hours, meeting prefs | JSON config |

---

## 3. Availability Tier System

| Tier | Color | Meaning |
|---|---|---|
| 1 | 🟢 Green | All attendees free, all within their working hours |
| 2 | 🟡 Yellow | All free, but outside working hours for ≥1 person |
| 3 | 🟠 Orange | Conflicts: ≥1 person has a soft conflict (movable meeting) |
| 4 | 🔴 Red | Hard conflicts: ≥1 person has unmovable blocks |

> Note: In v1, we only compute Green and Yellow. Orange/Red requires knowing which meetings are "movable" — needs calendar event detail access, deferred to v2.

---

## 4. Data Flow Details

### 4a. Contact Resolution

Priority order:
1. `config/team.json` — name match (case-insensitive, partial match ok)
2. `gws calendar calendarList list` — check subscribed calendars
3. **Manual fallback**: Ask user "I couldn't find David's email. Can you provide it?"

Known limitation: `gws people searchContacts` requires additional OAuth scope (403 currently). Tracked as a gap.

### 4b. FreeBusy Query

```bash
gws calendar freebusy query --json '{
  "timeMin": "<window_start_utc>",
  "timeMax": "<window_end_utc>",
  "timeZone": "UTC",
  "items": [{"id": "email1"}, {"id": "email2"}, ...]
}'
```

Returns busy blocks per calendar. Free = everything not busy.

### 4c. Slot Finding Algorithm

```
for each candidate_slot in window (step = duration, step = 30 min):
    for each participant:
        check if slot overlaps any busy block
        check if slot is within working hours (in their timezone)
    
    if no overlaps AND all within working hours → Tier 1 (Green)
    if no overlaps BUT some outside working hours → Tier 2 (Yellow)
    skip if any overlaps (Tier 3/4 deferred to v2)
    
return top N slots, sorted by:
    - Tier (1 before 2)
    - Score: working-hours coverage score
    - Time-of-day preference (mid-morning preferred over late afternoon)
```

### 4d. Output Format

```
I found 5 possible times for your 30-min meeting with David (Sydney) and Sarah (London):

🟢 Green — All free, within working hours for everyone:
  1. Monday Apr 21 — 9:00 AM ET | 2:00 PM BST | 11:00 PM AEST
  2. Tuesday Apr 22 — 10:00 AM ET | 3:00 PM BST | 12:00 AM AEST+1

🟡 Yellow — All free, but outside working hours for some:
  3. Wednesday Apr 23 — 7:00 AM ET | 12:00 PM BST | 9:00 PM AEST  [early for you]
  4. Thursday Apr 24 — 4:00 PM ET | 9:00 PM BST | 6:00 AM AEST+1  [late for Sarah]

Reply with the option number (1–4) to schedule, or say "none of these" to try a different week.
```

### 4e. Event Creation

```bash
gws calendar events insert --params '{"calendarId": "primary", "sendUpdates": "all"}' \
  --json '{
    "summary": "<title>",
    "start": {"dateTime": "<iso>", "timeZone": "America/New_York"},
    "end":   {"dateTime": "<iso>", "timeZone": "America/New_York"},
    "attendees": [{"email": "..."}, ...],
    "conferenceData": {"createRequest": {"requestId": "<uuid>", "conferenceSolutionKey": {"type": "hangoutsMeet"}}}
  }'
```

---

## 5. Configuration Schema

### `config/team.json`
```json
{
  "members": [
    {
      "name": "Arijit Chowdhury",
      "aliases": ["arijit", "me"],
      "email": "REDACTED@example.com",
      "timezone": "America/New_York",
      "working_hours": {"start": "09:00", "end": "18:00"},
      "owner": true
    }
  ]
}
```

### `config/preferences.json`
```json
{
  "owner_email": "REDACTED@example.com",
  "owner_timezone": "America/New_York",
  "default_duration_minutes": 30,
  "preferred_slot_times": ["09:00", "10:00", "11:00", "14:00", "15:00"],
  "avoid_times": ["12:00", "13:00"],
  "max_slots_to_show": 6,
  "slot_step_minutes": 30,
  "default_search_days": 5
}
```

---

## 6. Assumptions & Constraints

| # | Assumption | Impact if Wrong |
|---|---|---|
| A1 | `gws` is authenticated and token is valid | Nothing works. Manual re-auth needed. |
| A2 | Attendees' calendars are accessible via freebusy (shared in Algolia workspace) | Will get 404/empty for inaccessible calendars. Graceful error needed. |
| A3 | People API scope is blocked (403) | Contact lookup falls back to team.json |
| A4 | v1 only handles Tier 1 + Tier 2 (no conflict resolution) | Cannot suggest "move this meeting to fit" |
| A5 | Google Meet is created automatically with event | Hardcoded to Meet; no Zoom support in v1 |

---

## 7. Known Gaps (Framework Test Log)

These are areas where one-shot execution hit a wall — require human input or future work:

- **GAP-01**: `gws people` returns 403. Cannot search contacts by name via API. Mitigation: `team.json` pre-population. Permanent fix: re-authenticate `gws` with People API scope.
- **GAP-02**: Timezone for subscribed calendar members is unknown unless in `team.json`. Need to either ask user or use admin directory API.
- **GAP-03**: Tier 3/4 (conflict resolution — "can we move X?") requires reading full event details + attendee status. Deferred to v2.
- **GAP-04**: Slack integration (find people via Slack) mentioned in brief. Not scoped in v1. Would need Slack MCP or Slack API.

---

## 8. Out of Scope (v1)

- Slack-based contact lookup
- Recurring meeting scheduling
- Room/resource booking
- Zoom/Teams conference links
- Mobile/web UI
- Proactive rescheduling suggestions
