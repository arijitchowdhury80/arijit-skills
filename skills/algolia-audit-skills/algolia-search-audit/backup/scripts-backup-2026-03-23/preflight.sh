#!/usr/bin/env bash
# Algolia Audit — Pre-Renderer Dependency Check
# Validates all dependencies required for Phase 3-5 (renderer + PDF generation)
# Run before any render-audit.ts invocation
# Exits 0 if all checks pass. Exits 1 if any check fails.

set -euo pipefail

PASS=true
SKILL_DIR="$(dirname "$0")/.."

echo "══════════════════════════════════════════════════"
echo "  PRE-FLIGHT DEPENDENCY CHECK"
echo "══════════════════════════════════════════════════"
echo ""

# ── Deno ──────────────────────────────────────────────────────────────────────
if deno --version &>/dev/null; then
  echo "  ✓ Deno: $(deno --version | head -1)"
else
  echo "  ❌ Deno not installed — required for render-audit.ts"
  echo "     Install: curl -fsSL https://deno.land/install.sh | sh"
  PASS=false
fi

# ── Node.js ───────────────────────────────────────────────────────────────────
if node --version &>/dev/null; then
  echo "  ✓ Node.js: $(node --version)"
else
  echo "  ❌ Node.js not installed — required for Playwright"
  echo "     Install: https://nodejs.org"
  PASS=false
fi

# ── Playwright + stealth ─────────────────────────────────────────────────────
# Check in the skill's own node_modules (where npm install was run)
PLAYWRIGHT_CHECK="require('$SKILL_DIR/node_modules/playwright-extra')"
if node -e "$PLAYWRIGHT_CHECK" &>/dev/null 2>&1; then
  echo "  ✓ Playwright + stealth: installed"
else
  echo "  ❌ Playwright not installed"
  echo "     Fix: cd ~/.claude/skills/algolia-search-audit && npm install"
  PASS=false
fi

# ── Playwright Chromium binary ────────────────────────────────────────────────
CHROMIUM=$(find ~/Library/Caches/ms-playwright -name "Chromium" -type f 2>/dev/null | head -1)
if [ -n "$CHROMIUM" ]; then
  echo "  ✓ Playwright Chromium: found at $CHROMIUM"
else
  echo "  ❌ Playwright Chromium not installed"
  echo "     Fix: cd ~/.claude/skills/algolia-search-audit && npx playwright install chromium"
  PASS=false
fi

# ── Python 3 ──────────────────────────────────────────────────────────────────
if python3 --version &>/dev/null; then
  echo "  ✓ Python 3: $(python3 --version)"
else
  echo "  ❌ Python 3 not installed — required for validation scripts"
  PASS=false
fi

# ── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES="$SKILL_DIR/templates"
for tmpl in "index-template.html" "ae-action-report-template.html" "strategic-battle-card-template.html" "prospect-leave-behind-template.html" "algolia-brand.css" "audit-data.schema.json"; do
  if [ -f "$TEMPLATES/$tmpl" ]; then
    echo "  ✓ Template: $tmpl"
  else
    echo "  ❌ Template missing: $tmpl"
    echo "     Expected at: $TEMPLATES/$tmpl"
    PASS=false
  fi
done

# ── render-audit.ts ───────────────────────────────────────────────────────────
if [ -f "$SKILL_DIR/scripts/render-audit.ts" ]; then
  echo "  ✓ render-audit.ts: present"
else
  echo "  ❌ render-audit.ts missing"
  PASS=false
fi

# ── Hub directory (for publishing) ────────────────────────────────────────────
HUB_DIR=""
for p in "$HOME/algolia-arian-v2" "/tmp/algolia-arian-v2"; do
  if [ -d "$p/.git" ]; then HUB_DIR="$p"; break; fi
done
if [ -n "$HUB_DIR" ]; then
  echo "  ✓ Hub directory: $HUB_DIR"
else
  echo "  ⚠️  Hub directory not found (~/algolia-arian-v2)"
  echo "     Fix: git clone https://github.com/arijitchowdhury80/algolia-arian-v2.git ~/algolia-arian-v2"
  echo "     (Only needed for publishing — not blocking for local render)"
fi

# ── ALGOLIA_AUDIT_DIR ─────────────────────────────────────────────────────────
if [ -n "${ALGOLIA_AUDIT_DIR:-}" ]; then
  echo "  ✓ ALGOLIA_AUDIT_DIR: $ALGOLIA_AUDIT_DIR"
else
  echo "  ⚠️  ALGOLIA_AUDIT_DIR not set — will use current directory"
  echo "     Fix: export ALGOLIA_AUDIT_DIR=\"\$HOME/algolia-audits\""
fi

echo ""
echo "══════════════════════════════════════════════════"
if [ "$PASS" = true ]; then
  echo "  ✅ ALL CHECKS PASSED — safe to run renderer"
  echo "══════════════════════════════════════════════════"
  exit 0
else
  echo "  ❌ PREFLIGHT FAILED — fix issues above before rendering"
  echo "══════════════════════════════════════════════════"
  exit 1
fi
