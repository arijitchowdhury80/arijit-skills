#!/usr/bin/env python3
"""learn-from-yt — ONE execution chain. Capture -> scaffold -> segment -> frames,
leaving a ready-to-extract knowledge workspace. The extraction + synthesis steps
(judgment) are then done by the agent following SKILL.md.

Usage:
  python3 run.py "YOUTUBE_URL" [--root ./Knowledge] [--domain "print-on-demand"]
      [--minutes 10] [--frame-interval 30] [--no-frames] [--capture-only]
      [--from-transcript PATH]   # reuse an already-captured transcript, skip live fetch
"""
from __future__ import annotations
import argparse, json, subprocess, sys, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable

def sh(cmd, capture=False):
    print("  →", " ".join(str(c) for c in cmd))
    r = subprocess.run(cmd, text=True, capture_output=capture)
    if capture and r.returncode != 0:
        print(r.stderr[:300], file=sys.stderr)
    return r

def slug(s): return re.sub(r'[^a-z0-9]+', '-', (s or '').lower()).strip('-')[:60] or 'video'

def main():
    ap = argparse.ArgumentParser(description="learn-from-yt one-chain runner")
    ap.add_argument("url")
    ap.add_argument("--root", default="./Knowledge")
    ap.add_argument("--domain", default="business-building")
    ap.add_argument("--minutes", type=int, default=10)
    ap.add_argument("--frame-interval", type=int, default=30)
    ap.add_argument("--no-frames", action="store_true")
    ap.add_argument("--capture-only", action="store_true")
    ap.add_argument("--from-transcript", default="")
    a = ap.parse_args()

    print("[1/4] capture")
    if a.from_transcript:
        tpath = Path(a.from_transcript)
        title = tpath.stem
        proj = Path(a.root) / "raw-captures" / f"{slug(title)}"
        (proj / "raw").mkdir(parents=True, exist_ok=True)
        (proj / "raw" / "transcript.md").write_text(tpath.read_text(errors="replace"))
        print(f"    reused transcript -> {proj}/raw/transcript.md")
    else:
        r = sh([PY, str(HERE / "capture.py"), a.url, "--wiki-root", str(Path(a.root) / "raw-captures")], capture=True)
        try:
            info = json.loads(r.stdout.strip().splitlines()[-1])
            proj = Path(info["dir"]); title = info["title"]
            print(f"    captured '{title}' ({info.get('chapters',0)} chapters, {info.get('transcript_words',0)} words)")
        except Exception:
            print("    capture failed (likely YouTube 429 IP-throttle). Retry later or pass --from-transcript.", file=sys.stderr)
            sys.exit(2)

    if a.capture_only:
        print(f"done (capture-only): {proj}"); return

    print("[2/4] scaffold knowledge project")
    sh([PY, str(HERE / "create_knowledge_project.py"), "--root", str(Path(a.root) / "projects"),
        "--title", title, "--domain", a.domain, "--url", a.url])

    print("[3/4] segment transcript")
    tfile = proj / "raw" / "transcript.md"
    if tfile.exists():
        sh([PY, str(HERE / "segment_transcript.py"), str(tfile), "--out-dir", str(proj / "segments"), "--minutes", str(a.minutes)])

    if not a.no_frames:
        print("[4/4] capture frames (visual layer)")
        r = sh([PY, str(HERE / "capture_frames.py"), a.url, "--out-dir", str(proj / "visuals" / "frames"),
                "--every-seconds", str(a.frame_interval)], capture=True)
        if r.returncode != 0:
            print("    frames skipped (429 / unavailable) — transcript path still complete.", file=sys.stderr)
    else:
        print("[4/4] frames skipped (--no-frames)")

    print(f"\nWorkspace ready: {proj}")
    print("Next (agent, per SKILL.md): extract each segment -> build indexes -> run quality gates -> synthesize methodology/SOPs/requirements.")

if __name__ == "__main__":
    main()
