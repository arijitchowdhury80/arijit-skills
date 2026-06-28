#!/usr/bin/env python3
"""
industry_fallback_filter.py — deterministic guards for the algolia-intel-industry
WebSearch FALLBACK path and for Scout-based benchmark-page fetching.

Why this exists (survey D, bugs BUG-2 + Scout-embed §2.5 / F-evidence F1/F3):

  * BUG-2 — the 24-month staleness rule is enforced only inside collect-industry.py
    (the Tavily path). The WebSearch fallback (SKILL Step 2b, LLM-executed) had NO age
    gate, so stale benchmarks (2020-2022 articles dressed as "2025 trends") leaked into
    the deliverable whenever TAVILY_API_KEY was unset. This module applies the SAME
    `age_months > 24` exclusion to fallback results so the freshness guarantee holds on
    BOTH paths.

  * SCOUT EMBED — benchmark pages (Baymard / Forrester / NRF) are the ONE proven Scout
    win (F3: 11.6K chars clean structured markdown vs WebFetch's summary). This module
    fetches a benchmark page via Scout, but per Scout bug F1 (Scout returns empty/below-
    threshold markdown on some CMSes, e.g. Squarespace) it GUARDS the result: if the
    returned markdown is empty or below threshold, it FLAGS the degradation and signals
    the caller to FALL BACK to WebFetch — it NEVER silently accepts empty markdown.

This is a deterministic helper. The LLM still curates which stats/quotes matter and
writes the narrative; this module only enforces the mechanical age gate and the Scout
empty-markdown guard so those decisions are reproducible and not "judged in prose".

Two entry points:

  1. filter_fallback_results(results, today=None) -> (kept, dropped)
       Applies the 24-month age gate to a list of WebSearch fallback result dicts.
       Each result: {"url", "title", "source_date" (YYYY-MM-DD or None), ...}.
       Mirrors collect-industry.py's compute_age_months/is_stale semantics EXACTLY
       (age_months = floor(days/30); excluded when age_months > 24; unknown age kept
       but flagged stale_unknown=True so the LLM downgrades the label).

  2. scout_benchmark_fetch(url, min_markdown_chars=500) -> dict
       Fetches a benchmark page via Scout with the F1 empty-markdown guard. Returns a
       dict with `degraded` + `fallback_to_webfetch` flags so the caller knows whether
       to trust the markdown or fall back to WebFetch.

CLI usage:
  # Age-gate a fallback results JSON file (list of {url,title,source_date}):
  python3 industry_fallback_filter.py filter <results.json>

  # Scout-fetch a benchmark page (prints guarded result JSON to stdout):
  python3 industry_fallback_filter.py scout <benchmark_url> [--min-chars 500]
"""

import sys
import os
import json
import math
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

# Staleness cutoff — MUST match collect-industry.py STALE_MONTHS (24).
STALE_MONTHS = 24

# F1 guard: Scout markdown shorter than this is treated as empty/degraded.
# Baymard via Scout returned 11,608 chars (F3); the Squarespace failures returned
# 1-4 chars (F1). 500 is a conservative floor well above the failure mode and well
# below a real benchmark page.
DEFAULT_MIN_MARKDOWN_CHARS = 500


# ── Age gate (BUG-2 fix) ──────────────────────────────────────────────────────

def compute_age_months(source_date_str, today=None):
    """Age in months = floor((today - source_date).days / 30).

    Returns None when the date is missing or unparseable. Matches
    collect-industry.py compute_age_months EXACTLY so both paths agree.
    """
    if not source_date_str:
        return None
    today = today or date.today()
    try:
        src = date.fromisoformat(str(source_date_str)[:10])
        delta_days = (today - src).days
        return math.floor(delta_days / 30)
    except Exception:
        return None


def is_stale(age_months):
    """True when age_months exceeds STALE_MONTHS (24). Unknown age (None) is NOT
    stale here — it is kept but flagged by the caller. Matches collect-industry.py."""
    if age_months is None:
        return False
    return age_months > STALE_MONTHS


def filter_fallback_results(results, today=None):
    """Apply the 24-month age gate to WebSearch fallback results.

    This is the SAME gate collect-industry.py applies on the Tavily path, now applied
    on the fallback path too (BUG-2). Stale results (> 24 months) are DROPPED. Results
    with an unknown/unparseable date are KEPT but tagged `stale_unknown: True` and
    `collection_method: "websearch_fallback"` so the LLM downgrades their label to
    [ESTIMATE] and never presents an unverified-age stat as a fresh [FACT].

    Args:
        results: list of dicts, each with at least {"url", "title", "source_date"}.
        today:   optional date override for testing.

    Returns:
        (kept, dropped): two lists. `kept` entries are annotated with `age_months`,
        `stale_unknown`, and `collection_method`. `dropped` entries carry a
        `dropped_reason` of "stale_gt_24mo".
    """
    if not isinstance(results, list):
        raise TypeError("results must be a list of result dicts")

    kept, dropped = [], []
    for r in results:
        if not isinstance(r, dict):
            continue
        entry = dict(r)
        age = compute_age_months(entry.get("source_date"), today=today)
        entry["age_months"] = age
        entry["collection_method"] = "websearch_fallback"

        if is_stale(age):
            entry["dropped_reason"] = "stale_gt_24mo"
            dropped.append(entry)
            continue

        entry["stale_unknown"] = age is None
        kept.append(entry)

    return kept, dropped


# ── Scout benchmark fetch with F1 guard (SCOUT EMBED) ─────────────────────────

def _scout_config():
    base = os.environ.get("SCOUT_URL", "http://localhost:8421")
    key = os.environ.get("SCOUT_API_KEY", "dev-key")
    return base, key


def scout_available(timeout=5):
    """True if Scout's /health endpoint responds 200. Network-isolated by import-time
    lazy requests so the module imports even where requests/Scout is unavailable."""
    try:
        import requests
    except ImportError:
        return False
    base, _ = _scout_config()
    try:
        r = requests.get(f"{base}/health", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def evaluate_scout_markdown(markdown, min_chars=DEFAULT_MIN_MARKDOWN_CHARS):
    """F1 guard decision, isolated and pure so it is unit-testable without network.

    Returns (degraded, fallback_to_webfetch, reason).
      - degraded=True when markdown is empty or below the min-chars threshold
        (the reproducible Scout-on-Squarespace failure mode, F1).
      - fallback_to_webfetch mirrors degraded — the caller must WebFetch instead of
        silently accepting empty markdown.
    """
    md = markdown or ""
    n = len(md.strip())
    if n == 0:
        return True, True, "scout_markdown_empty"
    if n < min_chars:
        return True, True, f"scout_markdown_below_threshold ({n} < {min_chars})"
    return False, False, "ok"


def scout_benchmark_fetch(url, min_markdown_chars=DEFAULT_MIN_MARKDOWN_CHARS,
                          timeout=30):
    """Fetch a benchmark page via Scout, GUARDED per F1.

    On a clean fetch (markdown >= threshold) returns the markdown with degraded=False.
    On empty/below-threshold markdown (F1) returns degraded=True and
    fallback_to_webfetch=True — the caller MUST then WebFetch the same URL and label
    the result accordingly. The degradation is FLAGGED, never silently swallowed.

    Returns a dict:
      {url, scout_available, success, markdown, markdown_chars,
       degraded, fallback_to_webfetch, reason}
    """
    base, key = _scout_config()
    result = {
        "url": url,
        "scout_available": False,
        "success": False,
        "markdown": "",
        "markdown_chars": 0,
        "degraded": True,
        "fallback_to_webfetch": True,
        "reason": "scout_unavailable",
    }

    try:
        import requests
    except ImportError:
        return result

    if not scout_available():
        return result

    result["scout_available"] = True
    headers = {"Content-Type": "application/json", "X-API-Key": key}
    try:
        r = requests.post(
            f"{base}/scrape",
            headers=headers,
            json={
                "url": url,
                "formats": ["markdown"],
                "use_js": True,        # benchmark pages (Baymard) are JS-heavy
                "stealth": True,
                "timeout_ms": timeout * 1000,
            },
            timeout=timeout + 5,
        )
    except Exception as e:
        result["reason"] = f"scout_request_error: {e}"
        return result

    if r.status_code != 200:
        result["reason"] = f"scout_http_{r.status_code}"
        return result

    data = r.json()
    md = data.get("markdown", "") or ""
    result["success"] = bool(data.get("success", False))
    result["markdown"] = md
    result["markdown_chars"] = len(md.strip())

    degraded, fallback, reason = evaluate_scout_markdown(md, min_markdown_chars)
    result["degraded"] = degraded
    result["fallback_to_webfetch"] = fallback
    result["reason"] = reason
    return result


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cli_filter(path):
    with open(path) as f:
        results = json.load(f)
    kept, dropped = filter_fallback_results(results)
    print(json.dumps({
        "kept": kept,
        "dropped": dropped,
        "kept_count": len(kept),
        "dropped_count": len(dropped),
        "stale_months_threshold": STALE_MONTHS,
    }, indent=2))


def _cli_scout(url, min_chars):
    out = scout_benchmark_fetch(url, min_markdown_chars=min_chars)
    # Do not dump the full markdown to stdout (can be huge) — show a preview.
    preview = out.pop("markdown", "")
    out["markdown_preview"] = preview[:500]
    print(json.dumps(out, indent=2))


def main():
    if len(sys.argv) < 3:
        print(
            "Usage:\n"
            "  python3 industry_fallback_filter.py filter <results.json>\n"
            "  python3 industry_fallback_filter.py scout <benchmark_url> [--min-chars N]",
            file=sys.stderr,
        )
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "filter":
        _cli_filter(sys.argv[2])
    elif mode == "scout":
        url = sys.argv[2]
        min_chars = DEFAULT_MIN_MARKDOWN_CHARS
        if "--min-chars" in sys.argv:
            i = sys.argv.index("--min-chars")
            if i + 1 < len(sys.argv):
                min_chars = int(sys.argv[i + 1])
        _cli_scout(url, min_chars)
    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
