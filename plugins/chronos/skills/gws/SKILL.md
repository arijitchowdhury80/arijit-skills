---
name: gws
description: "Use when any task involves Google Workspace: reading/sending/drafting email, searching Gmail threads, reading/writing Google Docs, uploading/listing Drive files, reading/writing Sheets, managing Calendar events, creating Slides, or running cross-service workflows (standup, meeting prep, weekly digest). Triggers on: 'send email', 'draft an email', 'read that doc', 'upload to Drive', 'check my calendar', 'search Gmail', 'create a spreadsheet', 'forward this email', 'what meetings do I have', 'triage my inbox', 'reply to that thread', 'append to the sheet', 'create a Google Doc', 'find files in Drive'. Do NOT use for scheduling meetings with specific people (use meeting-scheduler). Do NOT use for calendar event CRUD with MCP tools already connected."
---

# Google Workspace CLI (`gws`) Skill

**Skill name:** gws
**Tool:** `gws` CLI v0.22.5+ (installed via Homebrew at `/opt/homebrew/bin/gws`)
**Auth:** OAuth2, encrypted credentials at `~/.config/gws/credentials.enc`
**Account:** whichever Google Workspace account you authenticate with via `gws auth login`
**GCP Project:** your own Google Cloud project, registered with its own OAuth client (see First-time setup in the `meeting-scheduler` skill)

---

## Voice — read before drafting any email body

Before composing, drafting, replying to, or forwarding any email with body text (`+send`, `+reply`, `+reply-all`, `+forward`), load the `tone-of-voice` skill and apply it to the copy. That skill holds Arijit's signature, tone, and structure rules — this skill only handles the mechanics of getting it into Gmail. Raw API calls that don't touch body text (search, triage, list, read) don't need it.

## When to Use

Any task touching Google Workspace services:
- **Gmail** — search, read, triage, send, draft, reply, reply-all, forward, watch
- **Drive** — list, search, upload, download, create folders, manage permissions
- **Docs** — create, read, append text, batch update (rich formatting)
- **Sheets** — read ranges, append rows, bulk insert
- **Slides** — read/create presentations
- **Calendar** — list events, create/update events
- **Workflows** — standup report, meeting prep, weekly digest, email-to-task

**Do NOT use this skill when:**
- Scheduling meetings with specific people → use `meeting-scheduler` (it calls gws internally)
- Calendar MCP tools are connected and sufficient for the task

---

## Step 0 — Health Check (always run first)

**Never hardcode the OAuth client ID/secret in this file or in any command you run.** They live in `~/.config/gws/.env` (0600 permissions, local-only, never committed to git). Source that file, don't inline the values.

```bash
source ~/.config/gws/.env
gws auth status 2>&1 | grep -E '"token_valid"|"user"'
```

If `token_valid: false` → tell the user to run `gws auth login` in their terminal.

**CRITICAL:** Every `gws` command in this skill needs those two env vars in scope. The CLI requires them for OAuth token refresh. Without them, commands fail silently or with auth errors.

Template for all commands:
```bash
source ~/.config/gws/.env && gws <command>
```

If `~/.config/gws/.env` doesn't exist on a machine, tell the user to create it (mode 600) with:
```
export GOOGLE_WORKSPACE_CLI_CLIENT_ID="<from Google Cloud Console, your own GCP project>"
export GOOGLE_WORKSPACE_CLI_CLIENT_SECRET="<from Google Cloud Console, your own GCP project>"
```
Never ask the user to paste the actual secret value into chat — point them to Google Cloud Console → APIs & Services → Credentials.

---

## Gmail Operations

### Search threads
```bash
gws gmail users threads list --params '{"userId":"me","q":"subject:(Weekly Report) newer_than:7d","maxResults":10}'
```

### Triage inbox (unread summary)
```bash
gws gmail +triage --max 20
gws gmail +triage --query 'from:boss is:unread' --format table
gws gmail +triage --query 'label:INBOX is:unread newer_than:1d' --labels
```

### Read a message
```bash
gws gmail +read --id MESSAGE_ID
gws gmail +read --id MESSAGE_ID --headers --format json
gws gmail +read --id MESSAGE_ID --html
```

### Send email
```bash
gws gmail +send --to alice@example.com --subject 'Subject' --body 'Plain text body'
gws gmail +send --to alice@example.com --subject 'Report' --body '<h1>HTML</h1>' --html
gws gmail +send --to alice@example.com --subject 'Report' --body 'See attached' -a report.pdf -a data.csv
```

### Create draft (NOT send)
```bash
gws gmail +send --to alice@example.com --subject 'Subject' --body 'Body' --draft
gws gmail +send --to alice@example.com --subject 'Report' --body '<b>HTML</b>' --html --draft -a file.pdf
```

### Reply to a message
```bash
gws gmail +reply --message-id MSG_ID --body 'Reply text'
gws gmail +reply --message-id MSG_ID --body '<p>HTML reply</p>' --html
gws gmail +reply --message-id MSG_ID --body 'Reply' --draft  # draft reply, don't send
```

### Reply-all
```bash
gws gmail +reply-all --message-id MSG_ID --body 'Reply to all'
```

### Forward
```bash
gws gmail +forward --message-id MSG_ID --to recipient@example.com
gws gmail +forward --message-id MSG_ID --to recipient@example.com --body 'FYI' --draft
```

### Watch for new emails (streaming)
```bash
gws gmail +watch --project <your-gcp-project> --label-ids INBOX --once
```

### List messages (raw API)
```bash
gws gmail users messages list --params '{"userId":"me","q":"from:alice newer_than:30d","maxResults":20}'
```

### Get full message (raw API)
```bash
gws gmail users messages get --params '{"userId":"me","id":"MESSAGE_ID","format":"full"}'
```

### List labels
```bash
gws gmail users labels list --params '{"userId":"me"}'
```

---

## Drive Operations

### List files
```bash
gws drive files list --params '{"pageSize":20,"orderBy":"modifiedTime desc"}'
gws drive files list --params '{"q":"name contains '\''report'\'' and mimeType != '\''application/vnd.google-apps.folder'\''","pageSize":10}'
```

### Search files
```bash
gws drive files list --params '{"q":"fullText contains '\''quarterly review'\'' and trashed=false","pageSize":10}'
```

### List folder contents
```bash
gws drive files list --params '{"q":"'\''FOLDER_ID'\'' in parents","pageSize":50}'
```

### Upload file
```bash
gws drive +upload ./report.pdf
gws drive +upload ./report.pdf --parent FOLDER_ID
gws drive +upload ./data.csv --name 'Sales Data Q4.csv' --parent FOLDER_ID
```

### Download file
```bash
gws drive files get --params '{"fileId":"FILE_ID","alt":"media"}' --output ./downloaded_file.pdf
```

### Create folder
```bash
gws drive files create --json '{"name":"New Folder","mimeType":"application/vnd.google-apps.folder"}'
gws drive files create --json '{"name":"Subfolder","mimeType":"application/vnd.google-apps.folder","parents":["PARENT_FOLDER_ID"]}'
```

### Get file metadata
```bash
gws drive files get --params '{"fileId":"FILE_ID","fields":"id,name,mimeType,modifiedTime,size,webViewLink"}'
```

### Rename/move file
```bash
gws drive files update --params '{"fileId":"FILE_ID"}' --json '{"name":"New Name"}'
gws drive files update --params '{"fileId":"FILE_ID","addParents":"NEW_FOLDER","removeParents":"OLD_FOLDER"}' --json '{}'
```

---

## Docs Operations

### Create document
```bash
gws docs documents create --json '{"title":"My Document"}'
```

### Read document
```bash
gws docs documents get --params '{"documentId":"DOC_ID"}'
```

### Append text
```bash
gws docs +write --document DOC_ID --text 'Text to append at end of document'
```

### Rich formatting (batchUpdate)
```bash
gws docs documents batchUpdate --params '{"documentId":"DOC_ID"}' --json '{
  "requests": [
    {
      "insertText": {
        "location": {"index": 1},
        "text": "Bold Header\n"
      }
    },
    {
      "updateTextStyle": {
        "range": {"startIndex": 1, "endIndex": 12},
        "textStyle": {"bold": true, "fontSize": {"magnitude": 18, "unit": "PT"}},
        "fields": "bold,fontSize"
      }
    }
  ]
}'
```

---

## Sheets Operations

### Read values
```bash
gws sheets +read --spreadsheet SPREADSHEET_ID --range "Sheet1!A1:D10"
gws sheets +read --spreadsheet SPREADSHEET_ID --range "Sheet1" --format table
```

### Append row
```bash
gws sheets +append --spreadsheet SPREADSHEET_ID --values 'Alice,100,true'
```

### Bulk append
```bash
gws sheets +append --spreadsheet SPREADSHEET_ID --json-values '[["Alice","100"],["Bob","200"]]'
```

### Create spreadsheet
```bash
gws sheets spreadsheets create --json '{"properties":{"title":"My Spreadsheet"}}'
```

---

## Slides Operations

### Create presentation
```bash
gws slides presentations create --json '{"title":"My Presentation"}'
```

### Read presentation
```bash
gws slides presentations get --params '{"presentationId":"PRES_ID"}'
```

---

## Calendar Operations

### List today's events
```bash
gws calendar events list --params '{"calendarId":"primary","timeMin":"2026-07-01T00:00:00Z","timeMax":"2026-07-01T23:59:59Z","singleEvents":true,"orderBy":"startTime"}'
```

### List this week's events
```bash
gws calendar events list --params '{"calendarId":"primary","timeMin":"2026-06-30T00:00:00Z","timeMax":"2026-07-04T23:59:59Z","singleEvents":true,"orderBy":"startTime","maxResults":50}'
```

### Create event
```bash
gws calendar events insert --params '{"calendarId":"primary"}' --json '{
  "summary": "Team Standup",
  "start": {"dateTime": "2026-07-02T10:00:00-04:00"},
  "end": {"dateTime": "2026-07-02T10:30:00-04:00"},
  "attendees": [{"email": "colleague@example.com"}]
}'
```

---

## Cross-Service Workflows

### Standup report (today's meetings + open tasks)
```bash
gws workflow +standup-report
gws workflow +standup-report --format table
```

### Meeting prep (next meeting: agenda, attendees, docs)
```bash
gws workflow +meeting-prep
```

### Weekly digest (week's meetings + unread count)
```bash
gws workflow +weekly-digest
gws workflow +weekly-digest --format table
```

### Email to task
```bash
gws workflow +email-to-task --message-id MSG_ID
```

---

## Pagination

For large result sets, use `--page-all`:
```bash
gws drive files list --params '{"pageSize":100}' --page-all --page-limit 5
gws gmail users messages list --params '{"userId":"me","q":"newer_than:30d"}' --page-all --page-limit 3
```

---

## Output Formats

All commands support `--format`:
- `json` (default) — pipe to `jq` for filtering
- `table` — human-readable
- `yaml` — structured but readable
- `csv` — for spreadsheet import

---

## Safety Rules

1. **NEVER auto-send emails without explicit user confirmation.** Default to `--draft` when composing. Only use send when user explicitly says "send it."
2. **NEVER delete files/emails** without user confirmation. Surface what will be deleted first.
3. **Attachments with secrets** — warn if attaching .env, credentials, or key files.
4. **Large operations** — warn before bulk operations (>50 items).
5. **The `--dry-run` flag** is available on every command. Use it when uncertain.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `401 Unauthorized` | Env vars missing. Export CLIENT_ID and CLIENT_SECRET. |
| `403 Forbidden` | Scope not granted. Run `gws auth login --scopes gmail,drive,docs,sheets,calendar,slides,tasks` |
| `Token expired` | `gws auth login` (re-authenticates, refreshes token) |
| Command hangs | Check network. `gws auth status` to verify. |
| `encrypted credentials not found` | Run `gws auth setup` then `gws auth login` |

---

## Schema Discovery

To explore any API method's parameters:
```bash
gws schema gmail.users.messages.list
gws schema drive.files.list --resolve-refs
gws schema docs.documents.batchUpdate --resolve-refs
```
