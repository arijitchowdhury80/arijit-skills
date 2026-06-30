#!/usr/bin/env python3
"""gemini_search.py — Gemini + Google-Search grounded research for audit skills.

Replaces claude-cli WebSearch in the algolia-intel-* skills with a GROUNDED
backend: every answer carries citation URIs from Google Search grounding, so a
claim with no citation is visibly ungrounded. This is the no-fabrication rule
made mechanical — the model must label ungrounded answers, never ship them as
[FACT].

Read receipt (Google docs, ai.google.dev/gemini-api/docs/generate-content/
google-search; mirrors prism_platform/v2/gemini_api.py, verified 2026-06-29):
  POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={KEY}
  body: {"system_instruction": {"parts":[{"text": ...}]},
         "contents": [{"role":"user","parts":[{"text": ...}]}],
         "tools": [{"google_search": {}}],            # snake_case, verbatim
         "generationConfig": {"temperature": ..., "maxOutputTokens": ...}}
  resp: candidates[0].content.parts[].text                         -> answer
        candidates[0].groundingMetadata.groundingChunks[].web.uri  -> citations
        candidates[0].groundingMetadata.webSearchQueries           -> queries

Env:
  GEMINI_API_KEY   (required)  — the paid key (same one Cass/Hermes uses)
  GEMINI_MODEL     (optional)  — default gemini-2.5-flash
  GEMINI_API_BASE  (optional)  — default the public generativelanguage endpoint

Usage (CLI):
  python3 gemini_search.py "who is the CEO of PetSmart and when was it founded"
  python3 gemini_search.py --system "Answer only with grounded facts; cite sources." "<query>"
  python3 gemini_search.py --max-tokens 4096 --temperature 0.0 "<query>"

Returns JSON to stdout:
  {"answer": "...", "citations": ["https://..."], "queries": ["..."],
   "grounded": true, "model": "gemini-2.5-flash"}

A query that returns NO grounding citations sets "grounded": false. The caller
MUST treat an ungrounded answer as unverified — label it [OBSERVED]/[UNVERIFIED],
never [FACT]. Exit codes: 0 success (grounded or not); 2 hard error (missing key,
HTTP error, or no candidates).
"""

import argparse
import json
import os
import sys

import requests

GEMINI_API_BASE = os.environ.get(
    "GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta/models"
)
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
TIMEOUT = 120


def _log(msg):
    print(msg, file=sys.stderr)


def build_payload(system_prompt, user_prompt, temperature, max_tokens):
    """Build the generateContent request body with Google-Search grounding.

    Pure — same input always yields the same payload. The ``google_search`` tool
    key is snake_case per the verified read receipt; do not camelCase it.
    """
    return {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }


def _strip_code_fences(content):
    """Strip ```json ... ``` fences Gemini sometimes wraps output in."""
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        return "\n".join(lines)
    return content


def parse_response(data):
    """Map a generateContent grounding response to the gemini_search output dict.

    Returns {answer, citations, queries, grounded}. ``grounded`` is True iff at
    least one Google-Search citation URI is present — an answer with no citation
    is, by this gate, ungrounded.

    Raises:
        ValueError: when the response carries no candidates.
    """
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("No candidates returned from Gemini API")

    candidate = candidates[0]
    parts = candidate.get("content", {}).get("parts", []) or []
    answer = "".join(p.get("text", "") for p in parts)
    answer = _strip_code_fences(answer)

    grounding = candidate.get("groundingMetadata", {}) or {}
    chunks = grounding.get("groundingChunks", []) or []
    citations = [
        c["web"]["uri"]
        for c in chunks
        if isinstance(c.get("web"), dict) and c["web"].get("uri")
    ]
    queries = grounding.get("webSearchQueries", []) or []

    return {
        "answer": answer,
        "citations": citations,
        "queries": queries,
        "grounded": bool(citations),
    }


def search(query, system_prompt, temperature, max_tokens, model, api_key):
    """Execute one grounded search call. Raises requests.HTTPError / ValueError."""
    url = f"{GEMINI_API_BASE}/{model}:generateContent?key={api_key}"
    payload = build_payload(system_prompt, query, temperature, max_tokens)
    resp = requests.post(
        url, json=payload, headers={"Content-Type": "application/json"}, timeout=TIMEOUT
    )
    resp.raise_for_status()
    out = parse_response(resp.json())
    out["model"] = model
    return out


DEFAULT_SYSTEM = (
    "You are a research backend. Answer the query using Google Search grounding. "
    "State only facts supported by the search results. If the search does not "
    "support a claim, say so explicitly rather than guessing."
)


def main():
    parser = argparse.ArgumentParser(description="Gemini Google-Search grounded research.")
    parser.add_argument("query", help="The research query.")
    parser.add_argument("--system", default=DEFAULT_SYSTEM, help="System instruction.")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        _log("ERROR: GEMINI_API_KEY environment variable not set.")
        sys.exit(2)

    try:
        out = search(
            args.query, args.system, args.temperature, args.max_tokens, args.model, api_key
        )
    except requests.HTTPError as exc:
        _log(f"ERROR: Gemini API HTTP error: {exc} — body: {exc.response.text[:500]}")
        sys.exit(2)
    except ValueError as exc:
        _log(f"ERROR: {exc}")
        sys.exit(2)

    if not out["grounded"]:
        _log("WARN: response has no Google-Search citations — treat as UNVERIFIED.")

    print(json.dumps(out, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
