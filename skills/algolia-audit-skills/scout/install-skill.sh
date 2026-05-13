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

if [ -f "$SKILL_DST" ]; then
  echo "Updating existing skill: $SKILL_DST"
else
  echo "Installing skill: $SKILL_DST"
fi

cp "$SKILL_SRC" "$SKILL_DST"
echo "Done. Restart Claude Code (or open a new session) to load the scout skill."
echo ""
echo "Quick start:"
echo "  1. cp .env.example .env && edit .env   # set SCOUT_API_KEY"
echo "  2. scout serve                          # start the server"
echo "  3. curl http://localhost:8421/health    # verify"
