#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="agent-knowledge-capture"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INSTALL_CODEX=0
INSTALL_CLAUDE=0
HERMES_SKILLS_DIR=""

usage() {
  cat <<'EOF'
Install agent-knowledge-capture for Codex, Claude Code, and/or Hermes.

Usage:
  ./install-skill.sh --all
  ./install-skill.sh --codex
  ./install-skill.sh --claude
  ./install-skill.sh --hermes-dir /opt/data/skills

Flags:
  --all                 Install to Codex and Claude Code on this machine.
  --codex               Install to $CODEX_HOME/skills or ~/.codex/skills.
  --claude              Install to $CLAUDE_HOME/skills or ~/.claude/skills and add /record.
  --hermes-dir PATH     Install under PATH/agent-knowledge-capture.
  -h, --help            Show this help.
EOF
}

copy_skill() {
  local destination="$1"

  rm -rf "$destination"
  mkdir -p "$destination"

  cp "$SCRIPT_DIR/SKILL.md" "$destination/SKILL.md"

  if [ -d "$SCRIPT_DIR/agents" ]; then
    cp -R "$SCRIPT_DIR/agents" "$destination/agents"
  fi

  if [ -d "$SCRIPT_DIR/references" ]; then
    cp -R "$SCRIPT_DIR/references" "$destination/references"
  fi
}

install_claude_command() {
  local claude_home="$1"
  local commands_dir="$claude_home/commands"
  local command_file="$commands_dir/record.md"

  mkdir -p "$commands_dir"
  cat > "$command_file" <<'EOF'
# /record — Agent Knowledge Capture

Use the Agent Knowledge Capture skill at:

```text
~/.claude/skills/agent-knowledge-capture/SKILL.md
```

Read the skill, then capture the current session into durable knowledge.

Follow the universal method:

1. Identify the project or workspace.
2. Preserve concise raw/session evidence when useful.
3. Extract durable decisions, process changes, project state, reusable lessons, and open questions.
4. Route each item to the right project, vault, or shared-knowledge layer.
5. Update indexes or backlinks when appropriate.
6. Return a compact receipt with created/updated paths.

Do not dump the whole transcript. Do not record secrets. Do not create a decision record unless a real decision was made.
EOF
}

if [ "$#" -eq 0 ]; then
  usage
  exit 1
fi

while [ "$#" -gt 0 ]; do
  case "$1" in
    --all)
      INSTALL_CODEX=1
      INSTALL_CLAUDE=1
      shift
      ;;
    --codex)
      INSTALL_CODEX=1
      shift
      ;;
    --claude)
      INSTALL_CLAUDE=1
      shift
      ;;
    --hermes-dir)
      if [ "$#" -lt 2 ]; then
        echo "ERROR: --hermes-dir requires a path" >&2
        exit 1
      fi
      HERMES_SKILLS_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

echo "Installing $SKILL_NAME..."

if [ "$INSTALL_CODEX" -eq 1 ]; then
  CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
  CODEX_DEST="$CODEX_HOME_DIR/skills/$SKILL_NAME"
  copy_skill "$CODEX_DEST"
  echo "  Codex: $CODEX_DEST"
fi

if [ "$INSTALL_CLAUDE" -eq 1 ]; then
  CLAUDE_HOME_DIR="${CLAUDE_HOME:-$HOME/.claude}"
  CLAUDE_DEST="$CLAUDE_HOME_DIR/skills/$SKILL_NAME"
  copy_skill "$CLAUDE_DEST"
  install_claude_command "$CLAUDE_HOME_DIR"
  echo "  Claude Code: $CLAUDE_DEST"
  echo "  Claude command: $CLAUDE_HOME_DIR/commands/record.md"
fi

if [ -n "$HERMES_SKILLS_DIR" ]; then
  HERMES_DEST="$HERMES_SKILLS_DIR/$SKILL_NAME"
  copy_skill "$HERMES_DEST"
  echo "  Hermes: $HERMES_DEST"
fi

echo "Done."
