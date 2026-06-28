#!/usr/bin/env python3
"""
reconcile_financials.py — deterministic 6-source revenue reconciliation for
algolia-intel-financial-private (Layer 1F).

Why this exists (survey D, accuracy risk #2 + BUG-5):

  The financial-private SKILL says "HIGH = 3+ sources agree within 20% | MEDIUM = 2
  sources | LOW = single mention", but that comparison was JUDGED IN PROSE by the LLM —
  a prime fabrication surface (a confident wrong revenue propagates straight into the
  ROI model). This module computes the tier DETERMINISTICALLY from the structured
  candidate estimates the LLM collects, so the number and its confidence are reproducible.

  It also emits a RANGE (min/median/max), never collapsing conflicting sources to a
  single point — the survey's explicit fix for accuracy risk #2 ("range, not point;
  never collapse to a single number without showing the spread").

  BUG-5 guard: 1E (public) and 1F (private) both write 08-financial-profile.json and are
  "mutually exclusive" by the orchestrator's public/private routing. If routing
  misclassifies, or both run on a re-run, one silently overwrites the other. This module
  provides `assert_no_overwrite()` which REFUSES to let a private write clobber an
  existing public profile (or vice versa) unless explicitly forced.

The LLM still COLLECTS the candidate estimates (ecdb, LinkedIn headcount, trade press,
Inc 5000, etc. — those are irreducible web reads). This module only does the arithmetic:
parse each candidate to a number, compute the cluster of sources agreeing within 20% of
the median, and assign the tier. No revenue number is "judged" — it is computed.

Confidence tier rule (deterministic, matches SKILL Step 2 line 64):
  HIGH   — 3+ sources within ±20% of the cluster median
  MEDIUM — exactly 2 sources within ±20%
  LOW    — 0-1 corroborating sources (single mention or all sources disagree)

Usage (library):
  from reconcile_financials import reconcile, parse_money
  result = reconcile([
    {"source": "ecdb",            "value": "$1.2B"},
    {"source": "linkedin",        "value": 1100000000},
    {"source": "trade_press",     "value": "$1.15 billion"},
    {"source": "inc5000",         "value": "$900M"},
  ])
  # result["revenue_confidence"] == "HIGH", result["revenue_estimate_range"] == {...}

Usage (CLI):
  python3 reconcile_financials.py <candidates.json>
    candidates.json = [{"source": "...", "value": "..."}, ...]
"""

import sys
import os
import re
import json
import statistics

# Agreement window: a source "agrees" if within ±20% of the cluster median.
AGREEMENT_PCT = 0.20

# Multiplier suffixes for money parsing.
_MULT = {
    "K": 1e3, "THOUSAND": 1e3,
    "M": 1e6, "MM": 1e6, "MILLION": 1e6, "MN": 1e6,
    "B": 1e9, "BN": 1e9, "BILLION": 1e9,
    "T": 1e12, "TRILLION": 1e12,
}

_NUM_RE = re.compile(
    r"""
    \$?\s*
    (?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?  # 1,200,000(.5)
          | \d+(?:\.\d+)?)                # or 1200000 / 1.2
    \s*
    (?P<suffix>thousand|million|billion|trillion|[kmbt]n?|mm)?   # optional unit
    """,
    re.IGNORECASE | re.VERBOSE,
)


def parse_money(raw):
    """Parse a money string/number to a float in absolute dollars.

    Handles '$1.2B', '1.2 billion', '$1,150,000,000', '900M', plain ints/floats.
    Returns None if no number is parseable. Normalizes number+unit together — it does
    NOT strip-then-parseFloat (which is unit-blind; see the audit-financials chart bug
    lesson `strip+parseFloat is unit-blind`).
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip()
    if not s:
        return None
    m = _NUM_RE.search(s)
    if not m:
        return None
    num = float(m.group("num").replace(",", ""))
    suffix = (m.group("suffix") or "").upper()
    if suffix:
        num *= _MULT.get(suffix, 1.0)
    return num


def _agreeing_cluster(values):
    """Return the subset of values within ±AGREEMENT_PCT of the median of `values`.

    Deterministic: the median anchor is computed on ALL parsed values, then each value
    is tested against it. This is order-independent and reproducible.
    """
    if not values:
        return []
    anchor = statistics.median(values)
    if anchor == 0:
        return [v for v in values if v == 0]
    lo, hi = anchor * (1 - AGREEMENT_PCT), anchor * (1 + AGREEMENT_PCT)
    return [v for v in values if lo <= v <= hi]


def reconcile(candidates):
    """Deterministically reconcile revenue estimates from the 6-source waterfall.

    Args:
        candidates: list of {"source": str, "value": <money str|number>}.
                    `value` may be None/unparseable — those are recorded as failed.

    Returns a dict:
      {
        "revenue_confidence": "HIGH|MEDIUM|LOW",
        "revenue_estimate_range": {"min", "median", "max"} | None,
        "agreeing_sources": [source names within ±20% of median],
        "agreeing_count": int,
        "revenue_sources": [all sources that parsed to a number],
        "sources_failed": [sources whose value was unparseable],
        "parsed": [{"source","value_raw","value_usd"}],
        "agreement_pct": 0.20,
        "note": "human-readable spread summary",
      }
    """
    if not isinstance(candidates, list):
        raise TypeError("candidates must be a list of {source, value} dicts")

    parsed = []
    sources_failed = []
    for c in candidates:
        if not isinstance(c, dict):
            continue
        src = c.get("source", "unknown")
        val_usd = parse_money(c.get("value"))
        if val_usd is None:
            sources_failed.append(src)
            continue
        parsed.append({
            "source": src,
            "value_raw": c.get("value"),
            "value_usd": val_usd,
        })

    values = [p["value_usd"] for p in parsed]

    if not values:
        return {
            "revenue_confidence": "LOW",
            "revenue_estimate_range": None,
            "agreeing_sources": [],
            "agreeing_count": 0,
            "revenue_sources": [],
            "sources_failed": sources_failed,
            "parsed": parsed,
            "agreement_pct": AGREEMENT_PCT,
            "note": "no parseable revenue estimates",
        }

    cluster = _agreeing_cluster(values)
    # Map cluster values back to their source names (preserve duplicates correctly).
    agreeing_sources = []
    remaining = list(cluster)
    for p in parsed:
        if p["value_usd"] in remaining:
            agreeing_sources.append(p["source"])
            remaining.remove(p["value_usd"])

    n_agree = len(cluster)
    if n_agree >= 3:
        confidence = "HIGH"
    elif n_agree == 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    rng = {
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }

    spread_pct = ((rng["max"] - rng["min"]) / rng["median"] * 100) if rng["median"] else 0
    note = (
        f"{len(values)} sources parsed; {n_agree} agree within "
        f"±{int(AGREEMENT_PCT*100)}% of median; spread {spread_pct:.0f}% of median"
    )

    return {
        "revenue_confidence": confidence,
        "revenue_estimate_range": rng,
        "agreeing_sources": agreeing_sources,
        "agreeing_count": n_agree,
        "revenue_sources": [p["source"] for p in parsed],
        "sources_failed": sources_failed,
        "parsed": parsed,
        "agreement_pct": AGREEMENT_PCT,
        "note": note,
    }


# ── BUG-5 overwrite guard ─────────────────────────────────────────────────────

class OverwriteError(RuntimeError):
    """Raised when a financial-profile write would clobber the other company_type."""


def assert_no_overwrite(output_path, writing_company_type, force=False):
    """Refuse to let 1E (public) and 1F (private) silently overwrite each other.

    08-financial-profile.json is written by BOTH the public (1E) and private (1F)
    skills, "mutually exclusive" only by the orchestrator's routing. If routing
    misclassifies — or both run on a re-run — one silently clobbers the other (BUG-5).
    This guard reads any existing file, inspects its company_type (supports both `meta`
    and `_meta`), and raises OverwriteError if it differs from the type about to write.

    Args:
        output_path:          path to 08-financial-profile.json being written.
        writing_company_type: "public" or "private" — the type about to write.
        force:                if True, bypass the guard (explicit re-classification).

    Returns:
        existing_company_type (str) or None if no/typeless existing file.

    Raises:
        OverwriteError when an existing file's company_type differs and not forced.
    """
    wt = (writing_company_type or "").lower()
    if wt not in ("public", "private"):
        raise ValueError("writing_company_type must be 'public' or 'private'")

    if not os.path.exists(output_path):
        return None

    try:
        with open(output_path) as f:
            existing = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None  # unreadable/corrupt — let the write proceed

    meta = existing.get("meta") or existing.get("_meta") or {}
    existing_type = (meta.get("company_type") or existing.get("company_type") or "").lower()

    if not existing_type:
        return None  # legacy file with no type — cannot guard, allow

    if existing_type != wt and not force:
        raise OverwriteError(
            f"Refusing to overwrite {output_path}: existing company_type="
            f"'{existing_type}' but writing '{wt}'. This is BUG-5 — the public/private "
            f"routing likely misclassified, or both financial skills ran. Re-check the "
            f"orchestrator's public/private decision, or pass force=True to override."
        )
    return existing_type


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python3 reconcile_financials.py <candidates.json>\n"
            '  candidates.json = [{"source": "ecdb", "value": "$1.2B"}, ...]',
            file=sys.stderr,
        )
        sys.exit(1)

    with open(sys.argv[1]) as f:
        candidates = json.load(f)
    print(json.dumps(reconcile(candidates), indent=2))


if __name__ == "__main__":
    main()
