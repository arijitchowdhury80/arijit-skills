#!/usr/bin/env python3
"""
generate-abx-json.py — Post-LLM JSON patcher for abx_sequence.touches[]

WHY THIS EXISTS:
  The LLM writes the campaign copy (email/LinkedIn/Loom — irreducibly creative) into
  the markdown files under deliverables/abx-campaign/. But the SPA renders the campaign
  from <slug>-audit-data.json's `abx_sequence.touches[].body`, NOT from the markdown.

  Previously the assembly of that JSON was PSEUDOCODE in campaign-abx/SKILL.md that the
  LLM hand-executed every run — exactly the failure class generate-audit-data.py was
  built to kill (wrong field names per channel, source notes leaking into sendable copy,
  video_script missing so the Loom panel renders blank).

  This script is the deterministic patcher: it reads each campaign .md file, extracts ONLY
  the sendable copy (no Source notes, no headers), maps it to the correct channel-specific
  fields, and writes abx_sequence.touches[] in a shape that satisfies audit_data_schema.ABXTouch.

  The LLM never touches the JSON. It writes prose; this script extracts structure.

USAGE:
  python3 generate-abx-json.py <slug> <workspace_dir>

  workspace_dir is the company folder, e.g. "$ALGOLIA_AUDIT_DIR/The North Face"
  Reads:   <workspace_dir>/deliverables/abx-campaign/*.md
  Patches: <workspace_dir>/deliverables/<slug>-audit-data.json   (abx_sequence only)

CONTRACT (mirrors audit_data_schema.ABXTouch — do not drift):
  every touch:   touch:int, day:str, channel:email|linkedin|video, target:str,
                 subject:str, body:str (sendable copy, NO source notes, >=50 chars),
                 message:str (preview)
  video touch:   ALSO video_script:str (the timed script, >=100 chars),
                 video_platform, video_duration_target, email_subject, email_body
                 (body holds the SHORT delivery email, NOT the script)
"""

import json
import os
import re
import sys

# ── Touch map: touch_num -> (filename, channel, day) ──────────────────────────
# Mirrors the touch_map documented in algolia-campaign-abx/SKILL.md.
TOUCH_MAP = {
    1: ("email-1-hook.md", "email", "Day 1"),
    2: ("linkedin-connect.md", "linkedin", "Day 1-2"),
    3: ("email-2-competitor.md", "email", "Day 3-4"),
    4: ("linkedin-followup-1.md", "linkedin", "Day 4-6"),
    5: ("email-3-business-case.md", "email", "Day 7"),
    6: ("loom-script.md", "video", "Day 7-14"),
    7: ("linkedin-followup-2.md", "linkedin", "Day 10-12"),
    8: ("email-4-social-proof.md", "email", "Day 14"),
    9: ("email-5-breakup.md", "email", "Day 21"),
}

# Placeholder markers the schema rejects — surface them at extraction time instead.
PLACEHOLDER_MARKERS = ["Pending —", "Pending—", "TBD", "[PLACEHOLDER]",
                       "will be generated", "not yet complete"]


def read_file(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return f.read()


def log(msg):
    print(f'  [generate-abx-json] {msg}', flush=True)


# ── Extraction helpers (deterministic — no LLM) ───────────────────────────────

def extract_subject(content):
    """Extract the Subject line from an email/loom file. Falls back to first heading."""
    m = re.search(r'\*\*Subject:\*\*\s*(.+)', content)
    if m:
        return m.group(1).strip()
    lines = [l for l in content.split('\n') if l.strip()]
    return lines[0].lstrip('#').strip() if lines else 'Untitled'


def strip_source_notes(text):
    """Remove the Source notes section and any trailing horizontal rule before it.

    Source notes are internal AE prep — they MUST NOT reach sendable copy.
    """
    # Cut everything from a Source notes marker onward (with or without leading rule).
    text = re.split(r'\n-{3,}\s*\n\s*\*\*Source notes:\*\*', text, flags=re.IGNORECASE)[0]
    text = re.split(r'\*\*Source notes:\*\*', text, flags=re.IGNORECASE)[0]
    text = re.split(r'\n#+\s*Source notes', text, flags=re.IGNORECASE)[0]
    return text


def extract_email_body(content):
    """Extract ONLY the sendable email text — strip headers, source notes, metadata.

    The body is the text after the **Body:** marker up to **Source notes:** (or EOF).
    """
    body_match = re.search(
        r'\*\*Body:\*\*\s*\n(.*?)(?=\n-{3,}\s*\n\s*\*\*Source notes:\*\*|\*\*Source notes:\*\*|\Z)',
        content, re.DOTALL | re.IGNORECASE)
    if body_match:
        return body_match.group(1).strip()

    # Fallback: drop source notes, then strip header lines (#, To:, Subject:, rules).
    cleaned = strip_source_notes(content)
    lines = cleaned.strip().split('\n')
    body_lines = []
    skip_header = True
    for line in lines:
        if skip_header and (line.startswith('#') or line.startswith('**To:') or
                            line.startswith('**Subject:') or line.strip() == '---' or
                            line.strip() == '**Body:**' or not line.strip()):
            continue
        skip_header = False
        body_lines.append(line)
    return '\n'.join(body_lines).strip()


def extract_linkedin_body(content):
    """Extract a plain-text LinkedIn message — first **Message...:** block, no metadata.

    LinkedIn files use `**Message (for X):**` rather than `**Body:**`, and carry
    Character count / Target metadata that must not ship.
    """
    cleaned = strip_source_notes(content)

    # Prefer the first **Message...:** block.
    m = re.search(
        r'\*\*Message[^*]*\*\*\s*\n(.*?)(?=\n-{3,}|\n\*\*Message|\n\*\*Character count|\Z)',
        cleaned, re.DOTALL | re.IGNORECASE)
    if m:
        body = m.group(1).strip()
    else:
        # Fallback to the generic body extractor.
        body = extract_email_body(content)

    # Strip residual metadata header lines the LLM may emit.
    body = re.sub(r'\*\*(?:Timing|Message|Goal|Angle|Target|Note|Character count|Alternate target)[^*]*\*\*[^\n]*\n?',
                  '', body, flags=re.IGNORECASE)
    body = re.sub(r'^-{3,}\s*$', '', body, flags=re.MULTILINE).strip()
    return body


def extract_loom_script(content):
    """Extract the full timed Loom script — everything except the title and source notes."""
    cleaned = strip_source_notes(content).strip()
    lines = cleaned.split('\n')
    # Drop a single leading H1 title line if present.
    if lines and lines[0].startswith('# '):
        lines = lines[1:]
    return '\n'.join(lines).strip()


def find_placeholders(text):
    """Return any schema-rejected placeholder markers present in text (case-insensitive)."""
    low = text.lower()
    return [m for m in PLACEHOLDER_MARKERS if m.lower() in low]


# ── Touch builders (one per channel, schema-shaped) ───────────────────────────

def build_email_touch(touch_num, day, raw):
    body = extract_email_body(raw)
    subject = extract_subject(raw)
    return {
        "touch": touch_num,
        "day": day,
        "channel": "email",
        "target": "all",
        "subject": subject,
        "body": body,                    # clean copy — no citations, no headers
        "message": body[:120].strip(),
    }, body


def build_linkedin_touch(touch_num, day, raw):
    body = extract_linkedin_body(raw)
    subject = extract_subject(raw)
    return {
        "touch": touch_num,
        "day": day,
        "channel": "linkedin",
        "target": "all",
        "subject": subject,
        "body": body,                    # plain message text only
        "message": body[:300].strip(),
    }, body


def build_video_touch(touch_num, day, raw):
    script = extract_loom_script(raw)
    subject = extract_subject(raw)
    if not subject or subject.lower().startswith('loom video script'):
        subject = "Loom Video: 2-minute audit walkthrough"
    delivery_email = ("Hi [Name] — I put together a 2-minute walkthrough of what we found "
                      "on your site. [Loom link] — worth 2 minutes.")
    touch = {
        "touch": touch_num,
        "day": day,
        "channel": "video",
        "target": "all",
        "video_platform": "Loom",
        "video_duration_target": "2 min / 120 sec",
        "video_script": script,          # template reads t.video_script for the script panel
        "subject": subject,
        "email_subject": subject,
        "email_body": delivery_email,
        "body": delivery_email,          # body = SHORT delivery email, NOT the script
        "message": "Loom ready — record, upload, replace [Loom link] before sending.",
    }
    # Validate against the field the schema enforces a length floor on.
    return touch, script


def patch_abx_sequence(data, abx_dir):
    """Build abx_sequence.touches[] from the campaign markdown files. Returns (data, warnings)."""
    warnings = []
    touches = []

    for touch_num, (filename, channel, day) in sorted(TOUCH_MAP.items()):
        path = os.path.join(abx_dir, filename)
        raw = read_file(path)
        if raw is None:
            warnings.append(f"touch {touch_num}: {filename} not found — skipped")
            log(f"touch {touch_num} ({channel}): {filename} MISSING — skipping")
            continue

        if channel == "email":
            touch, checked = build_email_touch(touch_num, day, raw)
        elif channel == "linkedin":
            touch, checked = build_linkedin_touch(touch_num, day, raw)
        elif channel == "video":
            touch, checked = build_video_touch(touch_num, day, raw)
        else:
            warnings.append(f"touch {touch_num}: unknown channel {channel}")
            continue

        # Schema guards surfaced at extraction time (fail loud, do not silently ship).
        ph = find_placeholders(checked)
        if ph:
            warnings.append(f"touch {touch_num} ({channel}): placeholder text {ph} in copy")
        if 'source notes' in checked.lower():
            warnings.append(f"touch {touch_num} ({channel}): Source notes leaked into body")
        floor = 100 if channel == "video" else 50
        if len(checked.strip()) < floor:
            warnings.append(
                f"touch {touch_num} ({channel}): copy is {len(checked.strip())} chars "
                f"(< {floor} floor) — extraction likely failed")

        touches.append(touch)
        log(f"touch {touch_num} ({channel}): extracted {len(checked)} chars from {filename}")

    abx = data.get("abx_sequence") or {}

    # Ensure every contact has an id (SPA contactMap lookup key).
    contacts = abx.get("contacts", []) or []
    for c in contacts:
        if not c.get("id"):
            c["id"] = (c.get("name", "") or "").lower().replace(" ", "_").replace("'", "")

    abx["contacts"] = contacts
    abx["touches"] = touches
    abx["total_touches"] = len(touches)
    abx.setdefault("duration_days", 21)
    abx.setdefault("channels", ["Email", "LinkedIn", "Video"])
    data["abx_sequence"] = abx
    return data, warnings


def main():
    if len(sys.argv) < 3:
        print('Usage: python3 generate-abx-json.py <slug> <workspace_dir>')
        print('  slug: company slug (e.g. thenorthface)')
        print('  workspace_dir: company folder (e.g. "$ALGOLIA_AUDIT_DIR/The North Face")')
        sys.exit(1)

    slug = sys.argv[1]
    workspace = sys.argv[2].rstrip('/')

    deliverables_dir = os.path.join(workspace, 'deliverables')
    abx_dir = os.path.join(deliverables_dir, 'abx-campaign')
    data_path = os.path.join(deliverables_dir, f'{slug}-audit-data.json')

    print(f'\n🔧 generate-abx-json.py — patching abx_sequence in {slug}-audit-data.json\n')

    if not os.path.isdir(abx_dir):
        print(f'ERROR: campaign dir not found: {abx_dir}')
        print('Run the algolia-campaign-abx skill to generate the campaign markdown first.')
        sys.exit(1)

    if os.path.exists(data_path):
        with open(data_path, encoding='utf-8') as f:
            data = json.load(f)
        log(f'Loaded existing {slug}-audit-data.json ({os.path.getsize(data_path):,} bytes)')
    else:
        data = {}
        log('No existing JSON found — creating abx_sequence from scratch')

    data, warnings = patch_abx_sequence(data, abx_dir)

    n_touches = len(data['abx_sequence']['touches'])
    if n_touches < 3:
        print(f'\nERROR: only {n_touches} touches extracted (schema minimum is 3). '
              f'Campaign markdown is incomplete.')
        for w in warnings:
            print(f'  ⚠️  {w}')
        sys.exit(1)

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f'\n✅ abx_sequence patched: {n_touches} touches written to {data_path}')
    if warnings:
        print('\n⚠️  Warnings (review before sending):')
        for w in warnings:
            print(f'  - {w}')
    else:
        print('   No warnings — all touches passed schema floors.')


if __name__ == '__main__':
    main()
