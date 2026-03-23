#!/bin/bash
# Algolia Search Audit — PDF Generator
# Version: 2.0
#
# Usage:
#   ./generate-pdf.sh <company-slug> <template>
#   ./generate-pdf.sh <company-slug> all
#
# Templates:
#   binder       → {slug}-book.html       → {slug}-book.pdf
#   ae-report    → {slug}-ae-report.html  → {slug}-ae-report.pdf
#   battle-card  → {slug}-battle-card.html → {slug}-battle-card.pdf  (landscape)
#   leave-behind → {slug}-leave-behind.html → {slug}-leave-behind.pdf
#   all          → all four above
#
# Examples:
#   ./generate-pdf.sh costco binder
#   ./generate-pdf.sh costco all
#
# Requirements:
#   - Google Chrome (macOS: /Applications/Google Chrome.app)
#   - python3 (for local HTTP server — ensures assets load correctly)
#
# IMPORTANT: Always serve via HTTP (not file://) so images and CSS resolve correctly.

set -euo pipefail

SLUG="${1:-}"
TEMPLATE="${2:-binder}"
PORT=8766

if [ -z "$SLUG" ]; then
  echo "Usage: $0 <company-slug> <template|all>"
  echo "Templates: binder | ae-report | battle-card | leave-behind | all"
  exit 1
fi

# ─── Resolve Chrome path ─────────────────────────────────────────────────────

find_chrome() {
  local candidates=(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
    "$(which google-chrome 2>/dev/null || true)"
    "$(which chromium 2>/dev/null || true)"
    "$(which chromium-browser 2>/dev/null || true)"
  )
  for c in "${candidates[@]}"; do
    if [ -n "$c" ] && [ -x "$c" ]; then
      echo "$c"
      return 0
    fi
  done
  # macOS: try mdfind
  local found
  found=$(mdfind "kMDItemCFBundleIdentifier == 'com.google.Chrome'" 2>/dev/null | head -1)
  if [ -n "$found" ]; then
    echo "${found}/Contents/MacOS/Google Chrome"
    return 0
  fi
  echo ""
}

CHROME=$(find_chrome)
if [ -z "$CHROME" ]; then
  echo "✗ Google Chrome not found. Install from https://www.google.com/chrome/"
  exit 1
fi
echo "Chrome: $CHROME"

# ─── Template config ─────────────────────────────────────────────────────────

# Template config (bash 3 compatible — no associative arrays)
get_html_file() {
  case "$1" in
    binder)      echo "${SLUG}-book.html" ;;
    ae-report)   echo "${SLUG}-ae-report.html" ;;
    battle-card) echo "${SLUG}-battle-card.html" ;;
    leave-behind) echo "${SLUG}-leave-behind.html" ;;
    *) echo "" ;;
  esac
}
get_pdf_file() {
  case "$1" in
    binder)      echo "${SLUG}-book.pdf" ;;
    ae-report)   echo "${SLUG}-ae-report.pdf" ;;
    battle-card) echo "${SLUG}-battle-card.pdf" ;;
    leave-behind) echo "${SLUG}-leave-behind.pdf" ;;
    *) echo "" ;;
  esac
}
get_paper_size() {
  case "$1" in
    battle-card) echo "landscape" ;;
    *) echo "portrait" ;;
  esac
}

# ─── Start local HTTP server ──────────────────────────────────────────────────

# Kill any leftover server on our port
lsof -ti tcp:$PORT | xargs kill -9 2>/dev/null || true
sleep 0.3

python3 -m http.server $PORT --directory "$(pwd)" --bind 127.0.0.1 &>/dev/null &
SERVER_PID=$!
sleep 1.2  # wait for server to be ready

cleanup() {
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "HTTP server: http://localhost:${PORT} (pid ${SERVER_PID})"

# ─── PDF generation function ─────────────────────────────────────────────────

generate_pdf() {
  local tmpl="$1"
  local html_file; html_file="$(get_html_file "$tmpl")"
  local pdf_file; pdf_file="$(get_pdf_file "$tmpl")"
  local orientation; orientation="$(get_paper_size "$tmpl")"

  if [ ! -f "$html_file" ]; then
    echo "✗ [$tmpl] $html_file not found. Run render-audit.ts first."
    return 1
  fi

  echo -n "  Generating [$tmpl] $pdf_file ... "

  # Build paper size flags
  local paper_flags=""
  if [ "$orientation" = "landscape" ]; then
    paper_flags="--print-to-pdf-paper-width=11 --print-to-pdf-paper-height=8.5"
  fi
  # Portrait: Chrome default is letter (8.5x11) — no flags needed

  "$CHROME" \
    --headless=new \
    --disable-gpu \
    --no-sandbox \
    --disable-software-rasterizer \
    --disable-dev-shm-usage \
    --run-all-compositor-stages-before-draw \
    --virtual-time-budget=10000 \
    --no-pdf-header-footer \
    --print-to-pdf="$(pwd)/$pdf_file" \
    $paper_flags \
    "http://localhost:${PORT}/${html_file}" \
    2>/dev/null

  if [ -f "$pdf_file" ]; then
    local size
    size=$(du -h "$pdf_file" | cut -f1)
    echo "✓ ($size)"
    return 0
  else
    echo "✗ FAILED"
    return 1
  fi
}

# ─── Main ─────────────────────────────────────────────────────────────────────

echo ""
echo "Algolia Search Audit — PDF Generator"
echo "Company: $SLUG"
echo ""

SUCCESS=0
FAIL=0

if [ "$TEMPLATE" = "all" ]; then
  for tmpl in binder ae-report battle-card leave-behind; do
    if generate_pdf "$tmpl"; then
      ((SUCCESS++))
    else
      ((FAIL++))
    fi
  done
else
  if [ -z "$(get_html_file "$TEMPLATE")" ]; then
    echo "✗ Unknown template: $TEMPLATE"
    echo "Valid: binder | ae-report | battle-card | leave-behind | all"
    exit 1
  fi
  if generate_pdf "$TEMPLATE"; then
    ((SUCCESS++))
  else
    ((FAIL++))
  fi
fi

echo ""
echo "Done: $SUCCESS succeeded, $FAIL failed."

# ─── Quality hints ───────────────────────────────────────────────────────────

if [ "$TEMPLATE" = "binder" ] || [ "$TEMPLATE" = "all" ]; then
  PDF="${SLUG}-book.pdf"
  if [ -f "$PDF" ]; then
    SIZE_KB=$(du -k "$PDF" | cut -f1)
    if [ "$SIZE_KB" -lt 500 ]; then
      echo "⚠  ${PDF} is small (${SIZE_KB}KB). Expected >2MB for a full binder with screenshots."
      echo "   Check that screenshots/ directory is present and screenshot_file paths are correct."
    fi
  fi
fi

[ "$FAIL" -gt 0 ] && exit 1
exit 0
