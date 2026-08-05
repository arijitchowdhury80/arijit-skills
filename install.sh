#!/bin/bash
# Arijit Skills — Claude Code installer
#
# Installs every skill in skills/ to ~/.claude/skills/.
#
# This script does NOT hardcode a skill list or a skill count. It reads the
# filesystem. The previous version hardcoded both, drifted from reality, and
# ended up advertising four skills that did not exist while omitting five that
# did. Anything printed below is derived from what is actually on disk.

set -e

SKILLS_DIR="$HOME/.claude/skills"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/skills"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║        Arijit Skills — Claude Code install       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

if [ ! -d "$SOURCE_DIR" ]; then
  echo "ERROR: cannot find skills/ at $SOURCE_DIR"
  echo "Run this script from the repository root."
  exit 1
fi

mkdir -p "$SKILLS_DIR"
echo "Installing to $SKILLS_DIR"
echo ""

TOTAL=0

# A skill is any directory containing a SKILL.md. Claude Code requires a flat
# skills directory, so every skill installs to its own top-level folder
# regardless of which group folder it lives in here.
install_skill() {
  local skill_dir="$1"
  local skill_name
  skill_name=$(basename "$skill_dir")
  [ -f "$skill_dir/SKILL.md" ] || return 0
  rm -rf "$SKILLS_DIR/$skill_name"
  cp -R "$skill_dir" "$SKILLS_DIR/$skill_name"
  echo "  ✓ $skill_name"
  TOTAL=$((TOTAL + 1))
}

install_group() {
  local group_dir="$1" label="$2" count=0
  [ -d "$group_dir" ] || return 0
  echo "[$label]"
  for skill_dir in "$group_dir"/*/; do
    [ -d "$skill_dir" ] || continue
    [ -f "$skill_dir/SKILL.md" ] || continue
    install_skill "$skill_dir"
    count=$((count + 1))
  done
  echo "  → $count installed"
  echo ""
}

install_group "$SOURCE_DIR/algolia-audit-skills"    "Audit pipeline"
install_group "$SOURCE_DIR/algolia-branding-skills" "Brand & marketing"
install_group "$SOURCE_DIR/general-skills"          "General tools"

# Skills that sit directly under skills/ rather than in a group folder.
# The previous installer only walked the three group folders, so these were
# silently never installed.
STANDALONE=0
for skill_dir in "$SOURCE_DIR"/*/; do
  [ -f "$skill_dir/SKILL.md" ] || continue
  if [ $STANDALONE -eq 0 ]; then echo "[Standalone]"; STANDALONE=1; fi
  install_skill "$skill_dir"
done
[ $STANDALONE -eq 1 ] && echo ""

echo "────────────────────────────────────────────────────"
echo "  Total installed: $TOTAL"
echo "────────────────────────────────────────────────────"
echo ""
echo "  Type / in Claude Code to see the commands."
echo ""
echo "  Brand & marketing skills read their brand data from one place:"
echo "    $SKILLS_DIR/algolia-shared-reference/brand-core/"
echo "  Edit a value there and every branding skill picks it up."
echo "  That folder is also distributable on its own — see"
echo "  skills/algolia-branding-skills/README.md"
echo ""

# ── Audit pipeline prerequisites ──────────────────────
# Only relevant if you intend to run the audit pipeline. The brand and
# marketing skills need none of this.
SETTINGS_FILE="$HOME/.claude/settings.json"
MCP_MISSING=()
for mcp in chrome apify yahoo; do
  grep -q "$mcp" "$SETTINGS_FILE" 2>/dev/null || MCP_MISSING+=("$mcp")
done

if [ ${#MCP_MISSING[@]} -gt 0 ]; then
  echo "  Note: the audit pipeline expects these MCP servers, not found in settings.json:"
  printf '    - %s\n' "${MCP_MISSING[@]}"
  echo "  Ignore this if you only want the brand & marketing skills."
  echo ""
fi

# ── Audit workspace ───────────────────────────────────
if [ -z "$ALGOLIA_AUDIT_DIR" ]; then
  echo "  Optional: set ALGOLIA_AUDIT_DIR to choose where audit runs are stored."
  echo "    export ALGOLIA_AUDIT_DIR=\"\$HOME/Documents/Algolia Search Audits\""
  echo "  Not needed for the brand & marketing skills."
  echo ""
fi

echo "Done."
echo ""
