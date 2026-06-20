#!/bin/bash
# Arijit Skills — Unified Claude Code Installer v3.1
# 42 skills organized in three folders:
#   skills/algolia-audit-skills/     — 23 audit pipeline skills
#   skills/algolia-branding-skills/ — 13 brand & marketing skills
#   skills/general-skills/           — 6 general tools

set -e

SKILLS_DIR="$HOME/.claude/skills"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/skills"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   Arijit Skills for Claude Code — Install v3.1   ║"
echo "║   42 skills · Modular pipeline architecture      ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Verify source exists
if [ ! -d "$SOURCE_DIR" ]; then
  echo "ERROR: Cannot find skills/ directory at $SOURCE_DIR"
  echo "Make sure you run this script from the algolia-claude-skills/ directory."
  exit 1
fi

# Create ~/.claude/skills/ if needed
mkdir -p "$SKILLS_DIR"

echo "Installing skills to $SKILLS_DIR ..."
echo ""

TOTAL=0

install_group() {
  local group_dir="$1"
  local group_label="$2"
  local count=0

  if [ ! -d "$group_dir" ]; then
    echo "  ⚠  $group_label not found at $group_dir"
    return
  fi

  echo "[$group_label]"
  for skill_dir in "$group_dir"/*/; do
    if [ -d "$skill_dir" ]; then
      skill_name=$(basename "$skill_dir")
      # Install flat to ~/.claude/skills/ (Claude Code requires flat structure)
      rm -rf "$SKILLS_DIR/$skill_name"
      cp -R "$skill_dir" "$SKILLS_DIR/$skill_name"
      echo "  ✓ $skill_name"
      count=$((count + 1))
      TOTAL=$((TOTAL + 1))
    fi
  done
  echo "  → $count skills installed"
  echo ""
}

install_group "$SOURCE_DIR/algolia-audit-skills"     "Audit Pipeline (23 skills)"
install_group "$SOURCE_DIR/algolia-branding-skills" "Marketing & Brand (13 skills)"
install_group "$SOURCE_DIR/general-skills"           "General Tools (6 skills)"

echo "────────────────────────────────────────────────────"
echo "  Total installed: $TOTAL skills"
echo "────────────────────────────────────────────────────"
echo ""
echo "AUDIT PIPELINE  (algolia-audit/)"
echo "  /algolia-search-audit       — Full pipeline orchestrator (v3.0)"
echo "  /algolia-intel-company      — 1A: Company context"
echo "  /algolia-intel-techstack    — 1B: Tech stack detection"
echo "  /algolia-intel-traffic      — 1C: SimilarWeb traffic"
echo "  /algolia-intel-competitors  — 1D: Competitor analysis"
echo "  /algolia-intel-financial-*  — 1E/F: Financial intelligence"
echo "  /algolia-intel-investor     — 1G: Investor quotes"
echo "  /algolia-intel-hiring       — 1H: Hiring signals"
echo "  /algolia-intel-social       — 1I: Social signals"
echo "  /algolia-intel-news         — 1J: News signals"
echo "  /algolia-intel-partner      — 1K: Partner intelligence"
echo "  /algolia-intel-industry     — 1L: Industry benchmarks"
echo "  /algolia-intel-queries      — 1M: Test query generation"
echo "  /algolia-audit-browser      — Phase 2: Browser testing"
echo "  /algolia-audit-report       — Phase 3-5: Scoring + deliverables"
echo "  /algolia-synth-business-case — ROI model"
echo "  /algolia-synth-sales-plays  — AE/BDR playbook"
echo "  /algolia-campaign-abx       — ABX campaign package"
echo "  /algolia-audit-factcheck    — Quality gate"
echo "  /algolia-audit-eval         — Module quality scorer"
echo ""
echo "MARKETING & BRAND  (algolia-marketing/)"
echo "  /algolia-blog /algolia-email /algolia-deck /algolia-brief"
echo "  /algolia-case-study /algolia-landing /algolia-one-pager"
echo "  /algolia-social /algolia-partner /algolia-ui-copy"
echo "  /algolia-algolialize /algolia-brand-check"
echo ""
echo "GENERAL TOOLS  (general/)"
echo "  /market-research /partnerforge /project-governance"
echo "  /learn-from-yt /sketch-explainer /agent-knowledge-capture"
echo ""
echo "────────────────────────────────────────────────────"
echo ""

# ── MCP server check ──────────────────────────────────
SETTINGS_FILE="$HOME/.claude/settings.json"
MCP_MISSING=()

if [ -f "$SETTINGS_FILE" ]; then
  grep -q "127.0.0.1:21405\|chrome" "$SETTINGS_FILE" 2>/dev/null || MCP_MISSING+=("Chrome MCP")
  grep -q "similarweb" "$SETTINGS_FILE" 2>/dev/null || MCP_MISSING+=("SimilarWeb MCP")
  grep -q "builtwith" "$SETTINGS_FILE" 2>/dev/null || MCP_MISSING+=("BuiltWith MCP")
  grep -q "apify" "$SETTINGS_FILE" 2>/dev/null || MCP_MISSING+=("Apify MCP")
  grep -q "yahoo" "$SETTINGS_FILE" 2>/dev/null || MCP_MISSING+=("Yahoo Finance MCP")
else
  MCP_MISSING=("Chrome MCP" "SimilarWeb MCP" "BuiltWith MCP" "Apify MCP" "Yahoo Finance MCP")
fi

if [ ${#MCP_MISSING[@]} -gt 0 ]; then
  echo "⚠  AUDIT PIPELINE SETUP REQUIRED"
  echo "   Missing MCP servers:"
  for mcp in "${MCP_MISSING[@]}"; do
    echo "     ✗ $mcp"
  done
  echo "   See skills/algolia-audit-skills/README.md for setup instructions."
  echo ""
else
  echo "✓ All MCP servers detected. Audit pipeline is ready."
  echo ""
fi

# ── ALGOLIA_AUDIT_DIR setup ───────────────────────────
echo "────────────────────────────────────────────────────"
echo "SEARCH AUDIT WORKSPACE SETUP"
echo ""
echo "  The audit pipeline stores research, screenshots, and"
echo "  deliverables in a directory you choose."
echo ""

if [ -n "$ALGOLIA_AUDIT_DIR" ]; then
  echo "  ✓ ALGOLIA_AUDIT_DIR already set: $ALGOLIA_AUDIT_DIR"
  AUDIT_DIR="$ALGOLIA_AUDIT_DIR"
else
  DEFAULT_AUDIT_DIR="$HOME/Documents/Algolia Search Audits"
  echo -n "  Enter audit workspace path [${DEFAULT_AUDIT_DIR}]: "
  read -r USER_AUDIT_DIR
  AUDIT_DIR="${USER_AUDIT_DIR:-$DEFAULT_AUDIT_DIR}"
fi

mkdir -p "$AUDIT_DIR"
echo "  ✓ Audit workspace: $AUDIT_DIR"

SHELL_RC=""
[ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"
[ -z "$SHELL_RC" ] && [ -f "$HOME/.bashrc" ] && SHELL_RC="$HOME/.bashrc"
[ -z "$SHELL_RC" ] && [ -f "$HOME/.bash_profile" ] && SHELL_RC="$HOME/.bash_profile"

if [ -n "$SHELL_RC" ]; then
  if ! grep -q "ALGOLIA_AUDIT_DIR" "$SHELL_RC"; then
    echo "" >> "$SHELL_RC"
    echo "# Algolia Search Audit — workspace directory" >> "$SHELL_RC"
    echo "export ALGOLIA_AUDIT_DIR=\"$AUDIT_DIR\"" >> "$SHELL_RC"
    echo "  ✓ Added to $SHELL_RC — run: source $SHELL_RC"
  else
    echo "  ✓ ALGOLIA_AUDIT_DIR already in $SHELL_RC"
  fi
else
  echo "  ⚠  Add manually: export ALGOLIA_AUDIT_DIR=\"$AUDIT_DIR\""
fi

echo ""
echo "Open any project in Claude Code and type / to see all commands."
echo "Full documentation: skills/algolia-audit-skills/README.md"
echo ""
echo "Done! ✓"
