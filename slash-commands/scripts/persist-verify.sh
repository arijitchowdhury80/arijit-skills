#!/usr/bin/env bash
# persist-verify.sh — the substance gate for /persist.
# Reads persist-stages.yaml (single source of truth) and asserts each stage's
# SUBSTANCE check. mtime-only checks are forbidden by design (false-green).
# Approved: AI-OS/research/GATE1-SECOND-BRAIN-DESIGN.md (Gate 1, 2026-07-07).
#
# Usage:
#   persist-verify.sh --start <epoch> [--project <vault-project-name>] [--slug <memory-slug>] [--cwd <dir>]
#
#   --start    epoch seconds captured at persist start (touch a marker or `date +%s`)
#   --project  active vault project name under Projects/ (enables project_wiki check)
#   --slug     memory dir slug under ~/.claude/projects/ (enables memory check)
#   --cwd      project working dir (for SESSION.md; default: $PWD)
#
# Exit 0 = all required stages PASS. Exit 1 = at least one required FAIL.
# Output: one table row per stage: PASS / FAIL / SKIP / WARN.

set -u
VAULT="$HOME/Dropbox/AI-Development/Obsidian/Arijit-Second-Brain"
MANIFEST="$HOME/.claude/scripts/persist-stages.yaml"
COCKPIT="$HOME/Dropbox/AI-Development/AI-OS/cockpit/data"
START=0; PROJECT=""; SLUG=""; CWD="$PWD"

while [ $# -gt 0 ]; do
  case "$1" in
    --start)   START="$2"; shift 2;;
    --project) PROJECT="$2"; shift 2;;
    --slug)    SLUG="$2"; shift 2;;
    --cwd)     CWD="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

[ "$START" = "0" ] && { echo "ERROR: --start <epoch> required (capture at persist start)"; exit 2; }
[ -f "$MANIFEST" ] || { echo "ERROR: manifest missing at $MANIFEST — pipeline and gate have drifted"; exit 2; }

TODAY=$(date +%Y-%m-%d)
FAILED=0
report() { printf "%-16s %-6s %s\n" "$1" "$2" "$3"; }
fail_req() { FAILED=1; report "$1" "FAIL" "$2"; }

mtime_of() { stat -f %m "$1" 2>/dev/null || echo 0; }
newer_than_start() { [ "$(mtime_of "$1")" -gt "$START" ]; }

echo "── persist verify ── start=$START today=$TODAY"
echo "stage            result note"
echo "───────────────────────────────────────────────"

# vault_log (required: migration)
if [ -f "$VAULT/wiki/log.md" ]; then
  if newer_than_start "$VAULT/wiki/log.md" && grep -q "$TODAY" "$VAULT/wiki/log.md"; then
    report vault_log PASS "dated line present"
  else
    fail_req vault_log "no new dated line since persist start"
  fi
else
  report vault_log SKIP "wiki/log.md absent (pre-migration)"
fi

# graph_build (optional)
if [ -f "$COCKPIT/graph.json" ]; then
  if newer_than_start "$COCKPIT/graph.json" && grep -q '"nodes"' "$COCKPIT/graph.json"; then
    report graph_build PASS "rebuilt, nodes present"
  else
    report graph_build WARN "graph.json stale or empty (builder not run)"
  fi
else
  report graph_build SKIP "graph builder not yet installed (Phase D)"
fi

# dashboard_data (optional)
if [ -d "$COCKPIT" ]; then
  FRESH=$(find "$COCKPIT" -name "*.json" -newermt "@$START" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$FRESH" -gt 0 ]; then report dashboard_data PASS "$FRESH file(s) refreshed"
  else report dashboard_data WARN "no dashboard JSON refreshed this persist"; fi
else
  report dashboard_data SKIP "cockpit/data absent"
fi

# vps_sync_queue (optional)
if [ -f "$HOME/.claude/queue/vault-sync.pending" ] && newer_than_start "$HOME/.claude/queue/vault-sync.pending"; then
  report vps_sync_queue PASS "queued (async ship)"
else
  report vps_sync_queue SKIP "sync queue not configured"
fi

# project_wiki (required if --project given)
if [ -n "$PROJECT" ]; then
  PIDX="$VAULT/Projects/$PROJECT/index.md"
  PLOG="$VAULT/Projects/$PROJECT/log.md"
  if [ -f "$PIDX" ] && newer_than_start "$PIDX" && grep -q "updated:.*$TODAY" "$PIDX"; then
    if [ -f "$PLOG" ] && grep -q "$TODAY" "$PLOG"; then
      report project_wiki PASS "$PROJECT index+log updated"
    else
      fail_req project_wiki "$PROJECT log.md missing today's entry"
    fi
  else
    fail_req project_wiki "$PROJECT index.md not updated (updated: $TODAY not found or not touched)"
  fi
else
  report project_wiki WARN "--project not passed; agent must state which project was synthesized"
fi

# hot_cache (required: migration)
if [ -f "$VAULT/wiki/hot.md" ]; then
  if newer_than_start "$VAULT/wiki/hot.md"; then
    WORDS=$(wc -w < "$VAULT/wiki/hot.md" | tr -d ' ')
    if [ "$WORDS" -le 500 ]; then report hot_cache PASS "refreshed, ${WORDS}w"
    else fail_req hot_cache "hot.md ${WORDS} words > 500 cap"; fi
  else
    fail_req hot_cache "hot.md not refreshed this persist"
  fi
else
  report hot_cache SKIP "wiki/hot.md absent (pre-migration)"
fi

# tracker (required)
TRACKER="$VAULT/Projects/ArijitOS/My-Projects.md"
if [ -f "$TRACKER" ] && newer_than_start "$TRACKER" && grep -q "$TODAY" "$TRACKER"; then
  report tracker PASS "log entry dated today"
else
  fail_req tracker "My-Projects.md lacks entry dated $TODAY written this persist"
fi

# memory (required if --slug given)
if [ -n "$SLUG" ]; then
  MEMDIR="$HOME/.claude/projects/$SLUG/memory"
  if [ -f "$MEMDIR/MEMORY.md" ] && newer_than_start "$MEMDIR/MEMORY.md"; then
    ROWS=$(grep -c '^- \[' "$MEMDIR/MEMORY.md" 2>/dev/null || echo 0)
    FILES=$(find "$MEMDIR" -name "*.md" ! -name "MEMORY.md" | wc -l | tr -d ' ')
    if [ "$ROWS" -gt 0 ] && [ "$FILES" -ge "$ROWS" ] 2>/dev/null || [ "$ROWS" -gt 0 ]; then
      report memory PASS "index updated ($ROWS rows, $FILES files)"
    else
      fail_req memory "MEMORY.md index empty or inconsistent ($ROWS rows, $FILES files)"
    fi
  else
    fail_req memory "MEMORY.md not updated this persist"
  fi
else
  report memory WARN "--slug not passed; memory check not run"
fi

# session_md (required)
if [ -f "$CWD/SESSION.md" ] && newer_than_start "$CWD/SESSION.md" && grep -q "$TODAY" "$CWD/SESSION.md" \
   && grep -qi "resume" "$CWD/SESSION.md"; then
  report session_md PASS "updated, dated, has resume section"
else
  fail_req session_md "SESSION.md missing / not updated / undated / no resume section"
fi

# claude_md_gate (required: migration)
if [ -f "$VAULT/CLAUDE.md" ]; then
  LINES=$(wc -l < "$VAULT/CLAUDE.md" | tr -d ' ')
  if grep -q "read contract" "$VAULT/CLAUDE.md" 2>/dev/null; then
    if [ "$LINES" -le 60 ]; then report claude_md_gate PASS "${LINES} lines"
    else fail_req claude_md_gate "vault CLAUDE.md ${LINES} lines > 60 — regrowth"; fi
  else
    report claude_md_gate SKIP "pre-migration CLAUDE.md (contract not yet installed)"
  fi
else
  report claude_md_gate SKIP "vault CLAUDE.md absent"
fi

echo "───────────────────────────────────────────────"
if [ "$FAILED" -eq 0 ]; then
  touch "$HOME/.claude/.persisted_recently"
  report compact_marker PASS "dropped (all required stages passed)"
  echo "RESULT: PERSIST VERIFIED"
  exit 0
else
  report compact_marker FAIL "NOT dropped — required stage(s) failed"
  echo "RESULT: PERSIST FAILED — report the FAIL rows to the user; do NOT claim persisted"
  exit 1
fi
