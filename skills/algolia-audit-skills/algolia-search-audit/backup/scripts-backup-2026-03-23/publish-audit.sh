#!/bin/bash
# Algolia Audit Publisher
#
# Copies a rendered audit SPA + deliverables into the algolia-arian-v2 hub,
# regenerates the index page, and optionally pushes to GitHub.
#
# CANONICAL PATHS:
#   Source SPA:       ~/algolia-arian-v2/{slug}/index.html
#   Source extras:    ~/algolia-arian-v2/{slug}/ae-report.html, battle-card.html, leave-behind.html
#   Source JSON:      ~/algolia-arian-v2/{slug}-audit-data.json
#   Source screenshots: ~/algolia-arian-v2/{slug}/screenshots/
#   Destination:      ~/algolia-arian-v2/{slug}/ (same repo — staging then push)
#
# Usage:
#   ./publish-audit.sh <slug> [hub-dir] [--stage-only | --push-only]
#
# Modes:
#   (default)      Copy + regenerate index + git commit + git push
#   --stage-only   Copy + regenerate index + git commit ONLY (no push — waits for review)
#   --push-only    git push ONLY (use after --stage-only + review approval)
#
# Examples:
#   ./publish-audit.sh brooks-running                          # full publish
#   ./publish-audit.sh brooks-running ~/algolia-arian-v2 --stage-only   # stage for review
#   ./publish-audit.sh brooks-running ~/algolia-arian-v2 --push-only    # push after approval

set -euo pipefail

SLUG="${1:-}"
HUB_DIR="${2:-}"
MODE="${3:-}"

if [ -z "$SLUG" ]; then
  echo "Usage: $0 <company-slug> [hub-directory] [--stage-only|--push-only]"
  exit 1
fi

# ── Locate hub directory ──────────────────────────────────────────────────────
if [ -z "$HUB_DIR" ] || [ "$HUB_DIR" = "--stage-only" ] || [ "$HUB_DIR" = "--push-only" ]; then
  [ "$HUB_DIR" = "--stage-only" ] && MODE="--stage-only"
  [ "$HUB_DIR" = "--push-only" ]  && MODE="--push-only"
  HUB_DIR=""
  for p in "$HOME/algolia-arian-v2" "/tmp/algolia-arian-v2" "$HOME/Desktop/algolia-arian-v2"; do
    if [ -d "$p/.git" ]; then HUB_DIR="$p"; break; fi
  done
fi

if [ -z "$HUB_DIR" ] || [ ! -d "$HUB_DIR" ]; then
  echo "✗ Hub not found. Clone first:"
  echo "  git clone https://github.com/arijitchowdhury80/algolia-arian-v2.git ~/algolia-arian-v2"
  exit 1
fi

# ── Push-only mode ────────────────────────────────────────────────────────────
if [ "$MODE" = "--push-only" ]; then
  echo "Pushing staged changes to GitHub..."
  cd "$HUB_DIR"
  git push origin main
  echo ""
  echo "✓ Published. Vercel will auto-deploy in ~60 seconds."
  REMOTE=$(git remote get-url origin)
  REPO=$(echo "$REMOTE" | sed 's/.*github.com\///' | sed 's/\.git//')
  echo "  GitHub: https://github.com/$REPO"
  exit 0
fi

# ── Check source files ────────────────────────────────────────────────────────
CWD="$(pwd)"
SPA_DIR="$CWD/$SLUG"
JSON_FILE="$CWD/$SLUG-audit-data.json"

if [ ! -f "$SPA_DIR/index.html" ]; then
  echo "✗ $SPA_DIR/index.html not found."
  echo "  Run: deno run render-audit.ts $SLUG site"
  exit 1
fi
if [ ! -f "$JSON_FILE" ]; then
  echo "✗ $JSON_FILE not found."
  exit 1
fi

# ── Copy SPA + JSON to hub ────────────────────────────────────────────────────
echo "Staging $SLUG → hub..."
mkdir -p "$HUB_DIR/$SLUG"
cp -r "$SPA_DIR/." "$HUB_DIR/$SLUG/"
cp "$JSON_FILE" "$HUB_DIR/"

if [ -d "$CWD/screenshots" ]; then
  # Copy ONLY into the company subfolder — never to a shared location.
  # Shared screenshot folders cause cross-contamination when multiple audits
  # have files with identical names (e.g. 02-empty-state.png).
  mkdir -p "$HUB_DIR/$SLUG/screenshots"
  cp -n "$CWD/screenshots/"*.png "$HUB_DIR/$SLUG/screenshots/" 2>/dev/null || true
fi

echo "  ✓ $SLUG/index.html"
echo "  ✓ $SLUG-audit-data.json"

# ── Regenerate hub index ──────────────────────────────────────────────────────
GENERATE=~/.claude/skills/algolia-search-audit/scripts/generate-index.ts
if [ -f "$GENERATE" ]; then
  cd "$HUB_DIR"
  deno run --allow-read --allow-write "$GENERATE" 2>/dev/null
  echo "  ✓ index.html regenerated"
fi

# ── Git commit ────────────────────────────────────────────────────────────────
cd "$HUB_DIR"
git add -A

COMPANY=$(python3 -c "
import json, sys
try:
    d = json.load(open('$SLUG-audit-data.json'))
    print(d['meta']['company'])
except: print('$SLUG')
" 2>/dev/null || echo "$SLUG")

git commit -m "$(cat <<COMMITMSG
${MODE:+[STAGED] }Add $COMPANY audit

- $SLUG/index.html: 5-tab SPA
- Updated hub index

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
COMMITMSG
)"

# ── Push or stage ─────────────────────────────────────────────────────────────
if [ "$MODE" = "--stage-only" ]; then
  echo ""
  echo "✓ $COMPANY staged for review (NOT yet published)"
  echo ""
  echo "  Review at: http://127.0.0.1:8766/$SLUG/"
  echo ""
  echo "  When approved, run:"
  echo "  bash publish-audit.sh $SLUG $HUB_DIR --push-only"
else
  git push origin main
  echo ""
  echo "✓ $COMPANY published."
  echo "  Vercel auto-deploys in ~60 seconds."
fi
