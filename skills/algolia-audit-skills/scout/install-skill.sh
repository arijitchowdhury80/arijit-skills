#!/usr/bin/env bash
# Installs the Scout Claude Code skill to ~/.claude/commands/scout.md
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMANDS_DIR="$HOME/.claude/commands"
SKILL_SRC="$SCRIPT_DIR/SKILL.md"
SKILL_DST="$COMMANDS_DIR/scout.md"

if [ ! -f "$SKILL_SRC" ]; then
  echo "Error: skill file not found at $SKILL_SRC" >&2
  exit 1
fi

mkdir -p "$COMMANDS_DIR"
cp "$SKILL_SRC" "$SKILL_DST"

echo "Done. Restart Claude Code or open a new session to load Scout."
echo "Install Scout runtime from: https://github.com/arijitchowdhury80/scout"
