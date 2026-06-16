#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def require(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"{name} is not available on PATH")
    return path


def run(cmd: list[str]) -> int:
    proc = subprocess.run(cmd, text=True)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture frames from a video URL or local media file.")
    parser.add_argument("source", help="YouTube URL or local media file")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--start", default="00:00:00")
    parser.add_argument("--end", default="")
    parser.add_argument("--every-seconds", type=int, default=30)
    parser.add_argument("--prefix", default="frame")
    parser.add_argument(
        "--youtube-client",
        choices=["auto", "default", "android"],
        default="auto",
        help="Client path to try for YouTube URL capture. auto tries android first, then default.",
    )
    args = parser.parse_args()

    ffmpeg = require("ffmpeg")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    source_path = Path(args.source)
    temp_dir_obj = None
    media = args.source

    if not source_path.exists() and args.source.startswith(("http://", "https://")):
        yt_dlp = require("yt-dlp") if shutil.which("yt-dlp") else None
        if yt_dlp is None:
            py = shutil.which("python3") or shutil.which("python")
            if not py:
                raise SystemExit("yt-dlp or python3 -m yt_dlp is required for URL capture")
            yt_dlp_cmd = [py, "-m", "yt_dlp"]
        else:
            yt_dlp_cmd = [yt_dlp]

        section = f"*{args.start}-{args.end}" if args.end else f"*{args.start}-"
        temp_dir_obj = tempfile.TemporaryDirectory()
        temp_dir = Path(temp_dir_obj.name)
        if args.youtube_client == "default":
            attempts = [("default", [])]
        elif args.youtube_client == "android":
            attempts = [("android", ["--extractor-args", "youtube:player_client=android"])]
        else:
            attempts = [
                ("android", ["--extractor-args", "youtube:player_client=android"]),
                ("default", []),
            ]

        failures: list[str] = []
        for label, extra in attempts:
            attempt_dir = temp_dir / label
            attempt_dir.mkdir(parents=True, exist_ok=True)
            media_pattern = str(attempt_dir / "source.%(ext)s")
            code = run(
                yt_dlp_cmd
                + extra
                + [
                    "--download-sections",
                    section,
                    "-f",
                    "bv*[height<=720]+ba/b[height<=720]/best[height<=720]/best",
                    "-o",
                    media_pattern,
                    args.source,
                ]
            )
            matches = [p for p in attempt_dir.iterdir() if p.is_file() and not p.name.endswith(".part")]
            if code == 0 and matches:
                media = str(matches[0])
                break
            failures.append(f"{label}: exit {code}, files {len(matches)}")
        else:
            raise SystemExit("yt-dlp did not produce a media file; attempts: " + "; ".join(failures))

    vf = f"fps=1/{max(args.every_seconds, 1)}"
    pattern = str(out_dir / f"{args.prefix}_%04d.jpg")
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error"]
    if source_path.exists():
        cmd += ["-ss", args.start]
    cmd += ["-i", media]
    if source_path.exists() and args.end:
        cmd += ["-to", args.end]
    cmd += ["-vf", vf, "-q:v", "2", pattern]
    code = run(cmd)
    if code != 0:
        raise SystemExit(code)

    if temp_dir_obj:
        temp_dir_obj.cleanup()

    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
