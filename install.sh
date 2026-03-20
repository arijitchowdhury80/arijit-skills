#!/bin/bash
# Algolia Claude Code Skills — Unified Installer v2.8
# Installs 16 skills (13 brand + 1 search audit + 1 factcheck + 1 project-governance) to ~/.claude/skills/

set -e

SKILLS_DIR="$HOME/.claude/skills"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/skills"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   Algolia Skills for Claude Code — Install v2.8  ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Verify source exists
if [ ! -d "$SOURCE_DIR" ]; then
  echo "ERROR: Cannot find skills/ directory at $SOURCE_DIR"
  echo "Make sure you run this script from the algolia-claude-skills/ directory."
  exit 1
fi

# Create ~/.claude/skills/ if it doesn't exist
if [ ! -d "$SKILLS_DIR" ]; then
  echo "Creating $SKILLS_DIR ..."
  mkdir -p "$SKILLS_DIR"
fi

# Copy all skill directories
echo "Installing skills to $SKILLS_DIR ..."
echo ""

SKILL_COUNT=0
BRAND_COUNT=0
AUDIT_COUNT=0
FACTCHECK_COUNT=0
REF_COUNT=0

for skill_dir in "$SOURCE_DIR"/algolia-* "$SOURCE_DIR"/project-governance; do
  if [ -d "$skill_dir" ]; then
    skill_name=$(basename "$skill_dir")
    echo "  -> $skill_name"
    cp -R "$skill_dir" "$SKILLS_DIR/"

    if [ "$skill_name" = "algolia-shared-reference" ]; then
      REF_COUNT=1
    elif [ "$skill_name" = "algolia-search-audit" ]; then
      AUDIT_COUNT=1
    elif [ "$skill_name" = "algolia-audit-factcheck" ]; then
      FACTCHECK_COUNT=1
    else
      BRAND_COUNT=$((BRAND_COUNT + 1))
    fi
    SKILL_COUNT=$((SKILL_COUNT + 1))
  fi
done

echo ""
echo "────────────────────────────────────────────────────"
echo "  Installed: $BRAND_COUNT brand skills"
echo "             $AUDIT_COUNT search audit skill (v2.7)"
echo "             $FACTCHECK_COUNT audit fact-check skill"
echo "             $REF_COUNT shared brand reference directory"
echo "────────────────────────────────────────────────────"
echo ""
echo "Brand Content Skills:"
echo "  /algolia-brand-check   — Check content for brand compliance"
echo "  /algolia-algolialize   — Transform any content to Algolia brand"
echo "  /algolia-blog          — Generate a branded blog post"
echo "  /algolia-boilerplate   — Get approved company descriptions"
echo "  /algolia-brief         — Generate a campaign brief"
echo "  /algolia-case-study    — Create a customer case study"
echo "  /algolia-deck          — Create a branded presentation"
echo "  /algolia-email         — Write branded email copy"
echo "  /algolia-landing       — Generate landing page copy"
echo "  /algolia-one-pager     — Create a product one-pager"
echo "  /algolia-partner       — Create co-marketing content"
echo "  /algolia-social        — Write social media posts"
echo "  /algolia-ui-copy       — Write UI microcopy"
echo ""
echo "Search Audit Skills:"
echo "  /algolia-search-audit       — Run a full search audit on a prospect website"
echo "  /algolia-audit-factcheck    — Validate audit deliverables (run after audit)"
echo ""
echo "────────────────────────────────────────────────────"
echo ""

# Check for MCP servers needed by search audit
SETTINGS_FILE="$HOME/.claude/settings.json"
MCP_MISSING=()

if [ -f "$SETTINGS_FILE" ]; then
  # Check for Chrome MCP
  if ! grep -q "127.0.0.1:21405" "$SETTINGS_FILE" 2>/dev/null; then
    MCP_MISSING+=("Chrome MCP")
  fi
  # Check for SimilarWeb
  if ! grep -q "similarweb" "$SETTINGS_FILE" 2>/dev/null; then
    MCP_MISSING+=("SimilarWeb MCP")
  fi
  # Check for BuiltWith
  if ! grep -q "builtwith" "$SETTINGS_FILE" 2>/dev/null; then
    MCP_MISSING+=("BuiltWith MCP")
  fi
else
  MCP_MISSING=("Chrome MCP" "SimilarWeb MCP" "BuiltWith MCP")
fi

if [ ${#MCP_MISSING[@]} -gt 0 ]; then
  echo "⚠  SEARCH AUDIT SETUP REQUIRED"
  echo ""
  echo "  The /algolia-search-audit skill needs these MCP servers:"
  for mcp in "${MCP_MISSING[@]}"; do
    echo "    ✗ $mcp — not detected"
  done
  echo ""
  echo "  See README.md for setup instructions (API keys & configuration)."
  echo "  The 13 brand skills work immediately — no extra setup needed."
  echo ""
else
  echo "✓ All MCP servers detected. Search audit is ready to use."
  echo ""
fi

# Offer to copy CLAUDE.md template
if [ -f "$SCRIPT_DIR/CLAUDE-template.md" ]; then
  if [ ! -f "$HOME/.claude/CLAUDE.md" ]; then
    echo "TIP: A CLAUDE.md project memory template is available."
    echo "     Run: cp CLAUDE-template.md ~/.claude/CLAUDE.md"
    echo "     This gives Claude Code context about the audit methodology."
    echo ""
  fi
fi

echo "Project Governance Skill:"
echo "  /project-governance    — Bootstrap complete governance for any project"
echo "    Creates: STATUS.md, CHECKPOINT.md, SESSION.md, CLAUDE.md, get-up-to-speed.md,"
echo "             5 project commands, git hook, PRD + test plan templates."
echo "    Run once per project. Then: /get-up-to-speed at every session start."
echo ""
echo "────────────────────────────────────────────────────"
echo ""

# ── ALGOLIA_AUDIT_DIR setup ───────────────────────────────────────────────────
if grep -q "algolia-search-audit" "$SKILLS_DIR" 2>/dev/null || [ -d "$SKILLS_DIR/algolia-search-audit" ]; then

  echo "────────────────────────────────────────────────────"
  echo ""
  echo "SEARCH AUDIT WORKSPACE SETUP"
  echo ""
  echo "  The search audit skill needs a directory to store:"
  echo "    • Company research files (scratchpads)"
  echo "    • Browser screenshots"
  echo "    • Deliverables (reports, HTML files, PDFs)"
  echo ""

  # Check if already set
  if [ -n "$ALGOLIA_AUDIT_DIR" ]; then
    echo "  ✓ ALGOLIA_AUDIT_DIR already set: $ALGOLIA_AUDIT_DIR"
    AUDIT_DIR="$ALGOLIA_AUDIT_DIR"
  else
    DEFAULT_AUDIT_DIR="$HOME/Documents/Algolia Search Audits"
    echo -n "  Enter audit workspace path [${DEFAULT_AUDIT_DIR}]: "
    read -r USER_AUDIT_DIR
    AUDIT_DIR="${USER_AUDIT_DIR:-$DEFAULT_AUDIT_DIR}"
  fi

  # Create the directory
  mkdir -p "$AUDIT_DIR"
  echo "  ✓ Audit workspace: $AUDIT_DIR"

  # Add to shell profile if not already there
  SHELL_RC=""
  if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
  elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
  elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_RC="$HOME/.bash_profile"
  fi

  if [ -n "$SHELL_RC" ]; then
    if ! grep -q "ALGOLIA_AUDIT_DIR" "$SHELL_RC"; then
      echo "" >> "$SHELL_RC"
      echo "# Algolia Search Audit — workspace directory" >> "$SHELL_RC"
      echo "export ALGOLIA_AUDIT_DIR="$AUDIT_DIR"" >> "$SHELL_RC"
      echo "  ✓ Added to $SHELL_RC"
      echo "  ✓ Run: source $SHELL_RC  (or restart terminal)"
    else
      echo "  ✓ ALGOLIA_AUDIT_DIR already in $SHELL_RC"
    fi
  else
    echo "  ⚠  Could not detect shell profile. Add manually:"
    echo "     export ALGOLIA_AUDIT_DIR=\"$AUDIT_DIR\""
  fi
  echo ""
fi

echo "Open any project in Claude Code and type / to see all commands."
echo ""
echo "Done!"
