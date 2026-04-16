#!/usr/bin/env bash
# Algolia Audit — Workspace Pre-Flight Validator
# Checks every scratchpad file for completeness before Phase 3-5 runs.
# bash 3.2 compatible (macOS default) — no declare -A
# Usage: bash validate-workspace.sh <workspace-dir>

set -euo pipefail

WS="${1:-$(pwd)}"
SLUG=$(basename "$WS" | sed 's/-audit-workspace//' | sed 's|.*/research$||' | sed 's|/$||')
[ -z "$SLUG" ] && SLUG=$(basename "$(dirname "$WS")")
PASS=true

echo "══════════════════════════════════════════════════"
echo "  PRE-FLIGHT VALIDATION — $(basename "$WS")"
echo "══════════════════════════════════════════════════"
echo ""

# Minimum size thresholds — bash 3.2 compatible function
get_min_size() {
  case "$1" in
    01) echo 5000 ;;  02) echo 500 ;;   03) echo 1500 ;;
    04) echo 1000 ;;  05) echo 2000 ;;  06) echo 4000 ;;
    07) echo 3000 ;;  08) echo 3000 ;;  09) echo 5000 ;;
    10) echo 3000 ;;  11) echo 3000 ;;  12) echo 4000 ;;
    # Note: 02 threshold 500b (script-filtered output is intentionally small ~1KB)
    # Note: 03 threshold 1500b (partial SimilarWeb coverage acceptable if ≥1500b)
    # Note: 04 threshold 1000b (competitor list, minimal content)
    *) echo 2000 ;;
  esac
}

# Required keyword checks — bash 3.2 compatible function
get_required_keyword() {
  case "$1" in
    01) echo "revenue" ;;
    03) echo "monthly" ;;
    08) echo "ROI\|roi\|revenue\|Revenue" ;;
    09) echo "screenshot\|Screenshot\|query\|Query" ;;
    10) echo "score\|Score\|severity\|Severity" ;;
    11) echo "quote\|Quote\|executive\|Executive\|CEO\|CFO\|CTO\|VP" ;;
    *) echo "" ;;
  esac
}

echo "── Scratchpad Files ──────────────────────────────"
MISSING_PHASES=""
for i in 01 02 03 04 05 06 07 08 09 10 11 12; do
  FILE=$(ls "$WS/${i}-"*.md 2>/dev/null | head -1 || true)
  if [ -z "$FILE" ]; then
    echo "  ❌ MISSING: ${i}-*.md — Phase 1 step ${i} not run"
    MISSING_PHASES="$MISSING_PHASES $i"
    PASS=false
    continue
  fi

  SIZE=$(wc -c < "$FILE" | tr -d ' ')
  BASENAME=$(basename "$FILE")
  THRESHOLD=$(get_min_size "$i")

  if [ "$SIZE" -lt "$THRESHOLD" ]; then
    echo "  ⚠️  SPARSE: $BASENAME (${SIZE}b — expected >${THRESHOLD}b) — likely incomplete research"
    MISSING_PHASES="$MISSING_PHASES $i"
    PASS=false
  else
    KW=$(get_required_keyword "$i")
    if [ -n "$KW" ] && ! grep -qi "$KW" "$FILE" 2>/dev/null; then
      echo "  ⚠️  INCOMPLETE: $BASENAME — missing expected content (keyword: $KW)"
      MISSING_PHASES="$MISSING_PHASES $i"
      PASS=false
    else
      echo "  ✓ $BASENAME (${SIZE}b)"
    fi
  fi
done

echo ""
echo "── Screenshots ───────────────────────────────────"
# Canonical path: {CompanyName}/deliverables/screenshots/
# WS = research/ dir, so deliverables/ is its sibling
SHOTS_DIR="$(dirname "$WS")/deliverables/screenshots"
if [ -d "$SHOTS_DIR" ]; then
  SHOTS=$(ls "$SHOTS_DIR/"*.png 2>/dev/null | wc -l | tr -d ' ')
else
  SHOTS=0
  echo "  ⚠️  Expected screenshots at: $SHOTS_DIR"
fi
if [ "$SHOTS" -lt 10 ]; then
  echo "  ❌ SCREENSHOTS: only $SHOTS found (minimum 10 required)"
  PASS=false
else
  echo "  ✓ $SHOTS screenshots found"
fi

echo ""
echo "── Placeholder Text Check ────────────────────────"
PLACEHOLDER_FILES=$(grep -rl "\[TO BE\]\|\[RESEARCH NEEDED\]\|\[PLACEHOLDER\]\|\[TBD\]\|TODO\|FIXME" "$WS"/*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$PLACEHOLDER_FILES" -gt 0 ]; then
  echo "  ⚠️  $PLACEHOLDER_FILES files contain placeholder text"
  PASS=false
else
  echo "  ✓ No placeholder text found"
fi

echo ""
echo "── Source URL Check ──────────────────────────────"
URL_COUNT=$(grep -h "https://" "$WS"/*.md 2>/dev/null | wc -l | tr -d ' ')
if [ "$URL_COUNT" -lt 20 ]; then
  echo "  ⚠️  Only $URL_COUNT source URLs (expect 20+) — data may lack citations"
  PASS=false
else
  echo "  ✓ $URL_COUNT source URLs found"
fi

echo ""
echo "══════════════════════════════════════════════════"
if [ "$PASS" = true ]; then
  echo "  ✅ VALIDATION PASSED — safe to proceed"
  echo "══════════════════════════════════════════════════"
  exit 0
else
  echo "  ❌ VALIDATION FAILED — fix gaps before proceeding"
  [ -n "$MISSING_PHASES" ] && echo "  Steps needing re-run:${MISSING_PHASES}"
  echo "  Run: /algolia-audit-research {url} --refresh {step}"
  echo "══════════════════════════════════════════════════"
  exit 1
fi
