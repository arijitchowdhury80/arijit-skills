"""Tests for platform_utils.gemini_search_results — the Tavily-replacement grounded
web/news search. Pure-logic + monkeypatched gemini client; no network.

Pins: tavily-shaped output, the no-fabrication grounded gate (ungrounded -> []),
prose-answer-as-content, and single-result emission (no per-citation stat dup).
"""

import os
import sys

import pytest

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import platform_utils as pu
import gemini_search as gs


def test_no_key_returns_empty(monkeypatch):
    monkeypatch.setattr(pu, "GEMINI_API_KEY", "")
    assert pu.gemini_search_results("anything") == []


def test_ungrounded_returns_empty(monkeypatch):
    # grounded:false (no citations) -> nothing, even with an answer (no fabrication).
    monkeypatch.setattr(pu, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(gs, "search", lambda *a, **k: {
        "answer": "Pet retail search converts at 2.3%.", "citations": [], "queries": [], "grounded": False,
    })
    assert pu.gemini_search_results("q") == []


def test_empty_answer_returns_empty(monkeypatch):
    monkeypatch.setattr(pu, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(gs, "search", lambda *a, **k: {
        "answer": "   ", "citations": ["https://c"], "queries": [], "grounded": True,
    })
    assert pu.gemini_search_results("q") == []


def test_grounded_returns_single_tavily_shaped_result(monkeypatch):
    monkeypatch.setattr(pu, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(gs, "search", lambda *a, **k: {
        "answer": "Site search converts at 2.32% in pet retail.",
        "citations": ["https://a", "https://b", "https://c"],
        "queries": ["q"], "grounded": True,
    })
    out = pu.gemini_search_results("pet retail search conversion")
    # SINGLE result (no per-citation duplication of the same stat).
    assert len(out) == 1
    r = out[0]
    assert {"title", "url", "content", "published_date", "score"} <= set(r.keys())
    assert r["content"] == "Site search converts at 2.32% in pet retail."
    assert r["url"] == "https://a"            # primary citation
    assert r["citations"] == ["https://a", "https://b", "https://c"]
    assert r["published_date"] == ""          # grounding gives no per-source date; never invented
    assert r["score"] == 1.0


def test_grounded_no_citation_urls_still_single_result(monkeypatch):
    # grounded True but citation list empty is a degenerate case; we already gate on
    # grounded, so this path only triggers if grounded is True with no URLs — emit one
    # result with empty url rather than crash.
    monkeypatch.setattr(pu, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(gs, "search", lambda *a, **k: {
        "answer": "fact", "citations": [], "queries": [], "grounded": True,
    })
    # grounded True + no citations: gate is `grounded and answer`, citations empty is allowed here.
    out = pu.gemini_search_results("q")
    assert len(out) == 1 and out[0]["url"] == ""


def test_gemini_available(monkeypatch):
    monkeypatch.setattr(pu, "GEMINI_API_KEY", "")
    assert pu.gemini_available() is False
    monkeypatch.setattr(pu, "GEMINI_API_KEY", "k")
    assert pu.gemini_available() is True
