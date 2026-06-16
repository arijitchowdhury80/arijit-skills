#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


STAMP_RE = re.compile(r"\[(?:(\d{1,2}):)?(\d{1,2}):(\d{2})\]")


def stamp_to_seconds(match: re.Match[str]) -> int:
    h = int(match.group(1) or 0)
    m = int(match.group(2))
    s = int(match.group(3))
    return h * 3600 + m * 60 + s


def fmt(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Split a timestamped transcript into fixed-size markdown segments.")
    parser.add_argument("transcript")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--minutes", type=int, default=10)
    args = parser.parse_args()

    transcript = Path(args.transcript)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    window = args.minutes * 60

    buckets: dict[int, list[str]] = {}
    untimestamped: list[str] = []
    for line in transcript.read_text(errors="ignore").splitlines():
        match = STAMP_RE.search(line)
        if not match:
            if line.strip():
                untimestamped.append(line)
            continue
        seconds = stamp_to_seconds(match)
        bucket = seconds // window
        buckets.setdefault(bucket, []).append(line)

    index_lines = ["# Segment Index", ""]
    for bucket in sorted(buckets):
        start = bucket * window
        end = start + window
        name = f"{bucket + 1:03d}-{fmt(start).replace(':', '-')}-{fmt(end).replace(':', '-')}.md"
        path = out_dir / name
        path.write_text(
            f"# Segment {bucket + 1:03d}\n\n"
            f"- Timestamp range: {fmt(start)} to {fmt(end)}\n"
            f"- Extraction status: TODO\n"
            f"- Visual capture status: TODO\n\n"
            "## Transcript\n\n"
            + "\n".join(buckets[bucket])
            + "\n"
        )
        index_lines.append(f"- [{fmt(start)} to {fmt(end)}]({name})")

    if untimestamped and not buckets:
        (out_dir / "001-untimestamped.md").write_text("# Segment 001\n\n## Transcript\n\n" + "\n".join(untimestamped) + "\n")
        index_lines.append("- [Untimestamped](001-untimestamped.md)")

    (out_dir / "index.md").write_text("\n".join(index_lines) + "\n")
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
