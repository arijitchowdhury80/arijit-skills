"""Tests for gemini_search.py — Gemini Google-Search grounded research backend.

Pure-logic only — no network. The HTTP call in main() is not exercised here;
build_payload() and parse_response() are the load-bearing pure functions and
carry the verified request/response contract (mirrors prism_platform gemini_api).
"""

import os
import sys

import pytest

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import gemini_search as gs

# A representative generateContent grounding response (shape per the read receipt).
SAMPLE = {
    "candidates": [
        {
            "content": {"parts": [{"text": "PetSmart CEO is J.K. Symancyk."}]},
            "groundingMetadata": {
                "groundingChunks": [
                    {"web": {"uri": "https://example.com/a", "title": "A"}},
                    {"web": {"uri": "https://example.com/b"}},
                ],
                "webSearchQueries": ["petsmart ceo"],
            },
        }
    ],
    "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5},
}


def test_build_payload_has_google_search_tool():
    p = gs.build_payload("sys", "q", 0.1, 1024)
    assert p["tools"] == [{"google_search": {}}]
    assert p["system_instruction"]["parts"][0]["text"] == "sys"
    assert p["contents"][0]["parts"][0]["text"] == "q"
    assert p["generationConfig"]["temperature"] == 0.1
    assert p["generationConfig"]["maxOutputTokens"] == 1024


def test_parse_extracts_answer_citations_queries():
    out = gs.parse_response(SAMPLE)
    assert "Symancyk" in out["answer"]
    assert out["citations"] == ["https://example.com/a", "https://example.com/b"]
    assert out["queries"] == ["petsmart ceo"]
    assert out["grounded"] is True


def test_parse_no_citations_means_ungrounded():
    data = {"candidates": [{"content": {"parts": [{"text": "x"}]}, "groundingMetadata": {}}]}
    out = gs.parse_response(data)
    assert out["grounded"] is False
    assert out["citations"] == []


def test_parse_no_candidates_raises():
    with pytest.raises(ValueError):
        gs.parse_response({"candidates": []})


def test_parse_strips_code_fences():
    data = {
        "candidates": [
            {
                "content": {"parts": [{"text": "```json\n{\"a\":1}\n```"}]},
                "groundingMetadata": {"groundingChunks": [{"web": {"uri": "u"}}]},
            }
        ]
    }
    out = gs.parse_response(data)
    assert out["answer"].strip() == '{"a":1}'


def test_parse_skips_chunks_without_web_uri():
    data = {
        "candidates": [
            {
                "content": {"parts": [{"text": "ok"}]},
                "groundingMetadata": {
                    "groundingChunks": [
                        {"web": {"uri": "https://good"}},
                        {"web": {}},
                        {"retrievedContext": {"uri": "https://ignored"}},
                    ]
                },
            }
        ]
    }
    out = gs.parse_response(data)
    assert out["citations"] == ["https://good"]
