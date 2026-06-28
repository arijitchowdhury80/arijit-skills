#!/usr/bin/env python3
"""
ground_quotes.py — deterministic grounding gate for algolia-intel-investor quotes.

Why this exists (survey D, accuracy risk #3; same lesson as the report-QA verifier
`feedback-injection-insufficient-need-hard-gate`):

  The investor SKILL says quotes must be VERBATIM and dated >= Jan 2025, but enforcement
  was LLM-side. Mis-dated or paraphrased "verbatim" quotes are the classic hallucination:
  injecting the source + "quote exactly" still fabricated in the report-QA spike, which is
  precisely why a POST-GEN verifier is mandatory. This module is that verifier for quotes.

  Two hard gates, both deterministic:
    1. GROUNDING — the quote must appear as an exact substring of the fetched source text
       (after light normalization of whitespace and smart-quotes). No substring match ->
       REJECT. This catches paraphrases dressed as verbatim quotes.
    2. RECENCY  — the quote's source date must be >= 2025-01-01. Older -> REJECT. (SKILL
       line 124: "Reject any quote dated before January 2025. No exceptions.")

  The LLM still CHOOSES which quote matters and extracts the candidate; this module only
  decides whether a candidate is allowed to ship. A quote that fails either gate is
  rejected with a machine-readable reason, never silently downgraded.

Normalization (substring match only — does NOT alter what ships):
  - collapse all runs of whitespace (incl. newlines) to a single space
  - map curly quotes/apostrophes -> straight, en/em dashes -> hyphen
  - casefold (case-insensitive match; transcripts vary capitalization of speaker tags)
  This is grounding-by-presence, not fuzzy matching — a real verbatim quote survives
  these transforms; a paraphrase does not.

Usage (library):
  from ground_quotes import check_quote, RECENCY_FLOOR
  verdict = check_quote(quote="...", source_text="<fetched transcript/10-K text>",
                        source_date="2025-03-14")
  if verdict["accepted"]: ...   # else verdict["reasons"] explains why

Usage (CLI):
  python3 ground_quotes.py <quotes.json> <source_text_file>
    quotes.json = [{"quote": "...", "source_date": "2025-..", "speaker": "..."}]
    source_text_file = plaintext of the fetched source (transcript / 10-K / article)
"""

import sys
import json
import re
from datetime import date

# Recency floor — quotes dated before this are rejected (SKILL line 124).
RECENCY_FLOOR = date(2025, 1, 1)

_QUOTE_MAP = {
    "‘": "'", "’": "'", "‛": "'",       # curly single / apostrophes
    "“": '"', "”": '"', "„": '"',       # curly double
    "–": "-", "—": "-", "−": "-",        # en/em/minus dashes
    " ": " ",                                       # non-breaking space
    "…": "...",                                     # ellipsis
}


def normalize(text):
    """Normalize text for substring matching: unify quotes/dashes, collapse
    whitespace, casefold. Pure and reproducible — same input always same output."""
    if not text:
        return ""
    for src, dst in _QUOTE_MAP.items():
        text = text.replace(src, dst)
    text = re.sub(r"\s+", " ", text)
    return text.strip().casefold()


def is_grounded(quote, source_text):
    """True iff the normalized quote is an exact substring of the normalized source.

    This is the grounding hard-gate: a paraphrase will not survive as a contiguous
    substring, so it is rejected. An empty quote or empty source is NOT grounded.
    """
    nq = normalize(quote)
    ns = normalize(source_text)
    if not nq or not ns:
        return False
    return nq in ns


def parse_date(raw):
    """Parse a YYYY-MM-DD (or longer ISO) date string to a date. None if unparseable."""
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except Exception:
        return None


def is_recent(source_date, floor=RECENCY_FLOOR):
    """True iff source_date >= floor (default 2025-01-01).

    Unknown/unparseable date -> NOT recent (fail closed): an undated 'verbatim' quote
    cannot be proven fresh, and the SKILL forbids unverified-age quotes shipping as fresh.
    """
    d = parse_date(source_date)
    if d is None:
        return False
    return d >= floor


def check_quote(quote, source_text, source_date, floor=RECENCY_FLOOR):
    """Run both hard gates on a single quote candidate.

    Returns a verdict dict:
      {
        "accepted": bool,            # True only if BOTH gates pass
        "grounded": bool,            # exact-substring presence in source_text
        "recent": bool,              # source_date >= floor
        "source_date": <normalized or None>,
        "reasons": [ ... ],          # machine-readable rejection reasons (empty if accepted)
      }
    """
    grounded = is_grounded(quote, source_text)
    recent = is_recent(source_date, floor=floor)

    reasons = []
    if not grounded:
        reasons.append("not_grounded: quote is not an exact substring of the fetched source")
    if not recent:
        d = parse_date(source_date)
        if d is None:
            reasons.append("recency_unverified: source_date missing or unparseable")
        else:
            reasons.append(f"too_old: source_date {d.isoformat()} < {floor.isoformat()}")

    parsed = parse_date(source_date)
    return {
        "accepted": grounded and recent,
        "grounded": grounded,
        "recent": recent,
        "source_date": parsed.isoformat() if parsed else None,
        "reasons": reasons,
    }


def filter_quotes(quotes, source_text, floor=RECENCY_FLOOR):
    """Apply check_quote to a list of candidates against a single source text.

    Each quote dict needs at least {"quote", "source_date"}; other fields pass through.
    Returns (accepted, rejected): accepted entries get a `_grounding` verdict block;
    rejected entries get `_grounding` with the failure reasons.
    """
    accepted, rejected = [], []
    for q in quotes:
        if not isinstance(q, dict):
            continue
        verdict = check_quote(
            q.get("quote", ""), source_text, q.get("source_date"), floor=floor
        )
        entry = dict(q)
        entry["_grounding"] = verdict
        (accepted if verdict["accepted"] else rejected).append(entry)
    return accepted, rejected


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python3 ground_quotes.py <quotes.json> <source_text_file>\n"
            '  quotes.json = [{"quote": "...", "source_date": "2025-..", ...}]',
            file=sys.stderr,
        )
        sys.exit(1)

    with open(sys.argv[1]) as f:
        quotes = json.load(f)
    with open(sys.argv[2]) as f:
        source_text = f.read()

    accepted, rejected = filter_quotes(quotes, source_text)
    print(json.dumps({
        "accepted": accepted,
        "rejected": rejected,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "recency_floor": RECENCY_FLOOR.isoformat(),
    }, indent=2))
    # Non-zero exit if anything was rejected — lets a Bash gate branch on it.
    sys.exit(1 if rejected else 0)


if __name__ == "__main__":
    main()
