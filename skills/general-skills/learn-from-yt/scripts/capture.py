#!/usr/bin/env python3
"""Capture a YouTube video -> metadata.json, source.md, raw/transcript.md.
Capture layer beneath learn-from-yt. Deps: yt-dlp, youtube-transcript-api."""
import argparse, json, re, subprocess, sys
from pathlib import Path

def vid_id(url):
    m = re.search(r'(?:v=|youtu\.be/|/watch\?v=|embed/)([A-Za-z0-9_-]{11})', url)
    return m.group(1) if m else url

def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', (s or '').lower()).strip('-')[:60] or 'video'

def meta(url):
    out = subprocess.run(["yt-dlp", "-J", "--skip-download", url],
                         capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise SystemExit(f"yt-dlp failed: {out.stderr[:200]}")
    j = json.loads(out.stdout)
    return {"id": j.get("id"), "title": j.get("title"), "channel": j.get("uploader") or j.get("channel"),
            "duration_s": j.get("duration"), "upload_date": j.get("upload_date"),
            "view_count": j.get("view_count"), "url": j.get("webpage_url"),
            "chapters": [{"start": c.get("start_time"), "title": c.get("title")} for c in (j.get("chapters") or [])],
            "description": (j.get("description") or "")[:4000]}

def transcript(vid, url):
    """Primary: yt-dlp auto-subs (json3) — robust against transcript-API IP blocks.
    Fallback: youtube-transcript-api."""
    import tempfile, glob, os
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["yt-dlp", "--write-auto-subs", "--write-subs", "--sub-langs", "en.*",
                        "--sub-format", "json3", "--skip-download", "-o", f"{td}/%(id)s.%(ext)s", url],
                       capture_output=True, text=True, timeout=120)
        files = glob.glob(f"{td}/*.json3")
        if files:
            j = json.load(open(files[0]))
            out = []
            for e in j.get("events", []):
                txt = "".join(s.get("utf8", "") for s in (e.get("segs") or [])).strip()
                if txt:
                    out.append({"t": (e.get("tStartMs", 0) or 0) / 1000.0, "text": txt})
            if out:
                return out
    # fallback
    from youtube_transcript_api import YouTubeTranscriptApi as A
    return [{"t": s.start, "text": s.text} for s in list(A().fetch(vid))]

def hhmmss(t):
    t = int(t or 0); return f"{t//3600:02d}:{t%3600//60:02d}:{t%60:02d}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url"); ap.add_argument("--wiki-root", default="./Knowledge/raw-captures")
    a = ap.parse_args()
    vid = vid_id(a.url)
    m = meta(a.url)
    d = Path(a.wiki_root) / f"{slug(m['title'])}-{vid}"; (d / "raw").mkdir(parents=True, exist_ok=True)
    json.dump(m, open(d / "metadata.json", "w"), indent=2)
    ch = "\n".join(f"- {hhmmss(c['start'])} {c['title']}" for c in m["chapters"]) or "(no chapters)"
    open(d / "source.md", "w").write(
        f"# {m['title']}\n\n- Channel: {m['channel']}\n- Duration: {hhmmss(m['duration_s'])}\n"
        f"- Uploaded: {m['upload_date']}\n- Views: {m['view_count']}\n- URL: {m['url']}\n\n"
        f"## Chapters\n{ch}\n\n## Description\n\n{m['description']}\n")
    try:
        segs = transcript(vid, a.url)
        body = "\n".join(f"[{hhmmss(s['t'])}] {s['text']}" for s in segs)
        open(d / "raw" / "transcript.md", "w").write(f"# Transcript — {m['title']}\n\n{body}\n")
        tw = sum(len(s['text'].split()) for s in segs)
    except Exception as e:
        open(d / "raw" / "transcript.md", "w").write(f"# Transcript unavailable: {e}\n"); tw = 0
    print(json.dumps({"dir": str(d), "title": m["title"], "chapters": len(m["chapters"]),
                      "transcript_words": tw}, indent=2))

if __name__ == "__main__":
    main()
