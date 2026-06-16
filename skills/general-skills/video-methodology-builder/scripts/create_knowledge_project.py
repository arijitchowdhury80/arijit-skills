#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    value = re.sub(r"-{2,}", "-", value)
    return value[:90].strip("-") or "source"


def write_if_missing(path: Path, text: str) -> None:
    if not path.exists():
        path.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a video methodology knowledge-base scaffold.")
    parser.add_argument("--root", default="./Knowledge")
    parser.add_argument("--title", required=True)
    parser.add_argument("--domain", default="business-building")
    parser.add_argument("--url", default="")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    source = root / slugify(args.domain) / slugify(args.title)
    for sub in [
        "segments",
        "indexes",
        "sop",
        "visuals/frames",
        "visuals/screenshots",
        "raw",
    ]:
        (source / sub).mkdir(parents=True, exist_ok=True)

    today = datetime.now().date().isoformat()
    write_if_missing(source / "source-card.md", f"""# {args.title}

- URL: {args.url or "TODO"}
- Domain: {args.domain}
- Capture date: {today}
- Transcript status: TODO
- Visual capture status: TODO
- Business objective: TODO
- Raw transcript: `raw/transcript.md`
- Metadata: `raw/metadata.json`
""")
    write_if_missing(source / "methodology.md", f"# {args.title} - Methodology\n\nStatus: draft\n")
    write_if_missing(source / "business-plan.md", f"# {args.title} - Business Plan\n\nStatus: draft\n")
    write_if_missing(source / "execution-plan.md", f"# {args.title} - Execution Plan\n\nStatus: draft\n")
    write_if_missing(source / "open-questions.md", "# Open Questions\n\n")
    write_if_missing(source / "segments/index.md", "# Segment Index\n\n")
    for name in [
        "tools",
        "tasks",
        "metrics",
        "pitfalls",
        "decisions",
        "claims-to-verify",
        "evidence-map",
        "glossary",
        "research-backlog",
        "software-to-build",
    ]:
        write_if_missing(source / "indexes" / f"{name}.md", f"# {name.replace('-', ' ').title()}\n\n")
    write_if_missing(source / "sop/index.md", "# SOP Library\n\n")
    write_if_missing(source / "visuals/notes.md", "# Visual Notes\n\n")
    write_if_missing(source / "raw/transcript.md", "# Raw Transcript\n\nTODO\n")
    write_if_missing(source / "raw/metadata.json", "{}\n")
    write_if_missing(source / "source-manifest.md", f"""# Source Manifest

- Title: {args.title}
- Domain: {args.domain}
- URL: {args.url or "TODO"}
- Raw transcript: `raw/transcript.md`
- Metadata: `raw/metadata.json`
- Segment strategy: TODO
- Chapter source: TODO
- Visual capture method: TODO
- Known capture failures: TODO
- Extraction schema version: v1
- Processing status: scaffolded
- Last processed segment: none
""")
    write_if_missing(source / "extraction-log.md", f"""# Extraction Log

- {today}: Created knowledge project scaffold.
""")

    print(source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
