#!/usr/bin/env python3
"""Tests for generate-abx-json.py — the post-LLM abx_sequence patcher (Cluster E)."""
import importlib.util
import json
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

spec = importlib.util.spec_from_file_location(
    "generate_abx_json", os.path.join(parent_dir, "generate-abx-json.py"))
gaj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gaj)


# ── Source-note stripping (must NOT leak into sendable copy) ───────────────────

def test_email_body_strips_source_notes():
    raw = (
        "# Email 1 — Hook\n\n**Subject:** Test subject\n\n**Body:**\n\n"
        "Hi [Name], this is the real sendable email copy and it is clearly long enough.\n\n"
        "---\n\n**Source notes:**\n- secret citation that must never ship\n")
    body = gaj.extract_email_body(raw)
    assert "secret citation" not in body
    assert "Source notes" not in body
    assert "real sendable email copy" in body


def test_email_body_strips_source_notes_without_body_marker():
    # LLM forgot the **Body:** delimiter — fallback path must still strip source notes.
    raw = (
        "# Email\n\n**Subject:** Test\n\n"
        "Hello there, this is the body copy that is definitely over fifty characters long.\n\n"
        "**Source notes:**\n- internal citation\n")
    body = gaj.extract_email_body(raw)
    assert "internal citation" not in body
    assert "this is the body copy" in body


# ── Subject extraction ────────────────────────────────────────────────────────

def test_subject_extraction():
    raw = "# Email\n\n**Subject:** What happened when I searched X\n\n**Body:**\nbody\n"
    assert gaj.extract_subject(raw) == "What happened when I searched X"


# ── LinkedIn body uses **Message...:**, not **Body:** ─────────────────────────

def test_linkedin_body_extraction():
    raw = (
        "# LinkedIn — Connection Request\n\n**Target:** Jane Doe, VP\n\n---\n\n"
        "**Message (for Jane):**\n\n"
        "Hi Jane — ran an audit on yoursite.com, found a measurable search gap. Happy to share.\n\n"
        "**Character count:** 90 characters\n\n---\n\n**Source notes:**\n- finding ref\n")
    body = gaj.extract_linkedin_body(raw)
    assert "Hi Jane" in body
    assert "Character count" not in body
    assert "Source notes" not in body
    assert "finding ref" not in body


# ── Video: script goes to video_script, short delivery email goes to body ─────

def test_video_touch_separates_script_from_body():
    raw = (
        "# Loom Video Script — Demo\n\n## HOOK (0-10 sec)\n"
        '"I spent 30 minutes on demo.com and found three things..."\n\n'
        "## DEMO (10-90 sec)\n[Screen: screenshots/1.png] explanation here that runs reasonably long "
        "so the script clears the one-hundred character floor required by the schema validator.\n\n"
        "## CTA (90-120 sec)\nHappy to walk through it.\n")
    touch, script = gaj.build_video_touch(6, "Day 7-14", raw)
    assert touch["channel"] == "video"
    assert touch["video_script"] == script
    assert len(touch["video_script"]) >= 100
    # body is the SHORT delivery email — NOT the script
    assert touch["video_script"] != touch["body"]
    assert "[Loom link]" in touch["body"]


# ── Placeholder detection ─────────────────────────────────────────────────────

def test_find_placeholders():
    assert gaj.find_placeholders("This is TBD for now") == ["TBD"]
    assert gaj.find_placeholders("clean copy") == []


# ── End-to-end patch builds a schema-valid sequence ───────────────────────────

def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def test_patch_abx_sequence_end_to_end(tmp_path):
    abx_dir = os.path.join(str(tmp_path), "deliverables", "abx-campaign")
    long = "x" * 200
    for fn, channel in [
        ("email-1-hook.md", "email"), ("email-2-competitor.md", "email"),
        ("email-3-business-case.md", "email"), ("email-4-social-proof.md", "email"),
        ("email-5-breakup.md", "email"),
    ]:
        _write(os.path.join(abx_dir, fn),
               f"# {fn}\n\n**Subject:** S\n\n**Body:**\nReal copy {long}\n\n**Source notes:**\n- cite\n")
    for fn in ["linkedin-connect.md", "linkedin-followup-1.md", "linkedin-followup-2.md"]:
        _write(os.path.join(abx_dir, fn),
               f"# {fn}\n\n**Message (for X):**\nReal message {long}\n\n**Source notes:**\n- cite\n")
    _write(os.path.join(abx_dir, "loom-script.md"),
           "# Loom Video Script\n\n## HOOK\nLine one. " + long + "\n\n## CTA\nClose.\n")

    data = {"abx_sequence": {"contacts": [{"name": "Jane Doe"}], "touches": []}}
    data, warnings = gaj.patch_abx_sequence(data, abx_dir)

    touches = data["abx_sequence"]["touches"]
    assert len(touches) == 9
    # contacts get an id auto-populated
    assert data["abx_sequence"]["contacts"][0]["id"] == "jane_doe"
    # no source notes leaked anywhere
    for t in touches:
        assert "Source notes" not in t["body"]
        if t["channel"] == "video":
            assert t.get("video_script")
            assert len(t["video_script"]) >= 100

    # The produced sequence must validate against the real schema contract.
    from audit_data_schema import ABXSequence
    ABXSequence(**data["abx_sequence"])  # raises on any contract violation


def test_patch_warns_on_missing_files(tmp_path):
    abx_dir = os.path.join(str(tmp_path), "deliverables", "abx-campaign")
    long = "x" * 200
    # Only 3 emails present — enough to meet the >=3 floor but missing files warned.
    for fn in ["email-1-hook.md", "email-2-competitor.md", "email-3-business-case.md"]:
        _write(os.path.join(abx_dir, fn), f"# {fn}\n\n**Subject:** S\n\n**Body:**\nCopy {long}\n")
    data = {"abx_sequence": {"contacts": [{"name": "A B"}], "touches": []}}
    data, warnings = gaj.patch_abx_sequence(data, abx_dir)
    assert any("not found" in w for w in warnings)
    assert len(data["abx_sequence"]["touches"]) == 3


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([__file__, "-v"]))
