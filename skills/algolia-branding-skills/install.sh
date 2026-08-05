#!/bin/bash
# Algolia Branding Skills — installer for Claude Code
#
# Installs the 13 branding skills plus their shared reference library into
# ~/.claude/skills/. Self-contained: no MCP servers, no API keys, no workspace
# setup. Run it from this directory.

set -e

SKILLS_DIR="$HOME/.claude/skills"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   Algolia Branding Skills — Claude Code install  ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

if [ ! -d "$SOURCE_DIR/algolia-brand-check" ]; then
  echo "ERROR: run this script from inside skills/algolia-branding-skills/"
  echo "       (could not find algolia-brand-check/ next to $0)"
  exit 1
fi

mkdir -p "$SKILLS_DIR"
echo "Installing to $SKILLS_DIR"
echo ""

COUNT=0
for skill_dir in "$SOURCE_DIR"/*/; do
  [ -d "$skill_dir" ] || continue
  skill_name=$(basename "$skill_dir")

  # Claude Code requires a flat skills directory, so each skill installs to its
  # own top-level folder. algolia-shared-reference goes alongside them, which is
  # what makes ../algolia-shared-reference/ resolve from every skill.
  rm -rf "$SKILLS_DIR/$skill_name"
  cp -R "$skill_dir" "$SKILLS_DIR/$skill_name"

  if [ "$skill_name" = "algolia-shared-reference" ]; then
    echo "  ✓ $skill_name  (shared reference — not directly invocable)"
  else
    echo "  ✓ $skill_name"
  fi
  COUNT=$((COUNT + 1))
done

echo ""
echo "────────────────────────────────────────────────────"
echo "  Installed: $COUNT"
echo "────────────────────────────────────────────────────"
echo ""
echo "  /algolia-brand-check    Audit content for brand compliance"
echo "  /algolia-algolialize    Transform any content into Algolia brand"
echo "  /algolia-boilerplate    Approved company descriptions"
echo ""
echo "  /algolia-blog  /algolia-email  /algolia-landing  /algolia-social"
echo "  /algolia-deck  /algolia-one-pager  /algolia-case-study"
echo "  /algolia-brief  /algolia-partner  /algolia-ui-copy"
echo ""
echo "  Brand data lives in one place:"
echo "    $SKILLS_DIR/algolia-shared-reference/brand-core/"
echo "  Edit approved-stats.md there and every skill picks it up."
echo ""
echo "  Logos are NOT bundled. Pull them from Frontify:"
echo "    https://algolia.frontify.com"
echo ""
echo "Restart Claude Code, then type / to see the commands."
echo ""
