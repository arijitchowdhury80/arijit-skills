# Failure Modes

## Planning Loop

Symptom: The agent keeps asking for schema and strategy before touching the source.

Fix: Run a pilot extraction from the intro or first 5 to 10 minutes, then refine schema from evidence.

## Fake Tool Invocation

Symptom: The agent says it has a skill, then tries to call it as a nonexistent tool.

Fix: Inspect the skill docs. Use the documented script or workflow.

## Context Flood

Symptom: The agent tries to summarize a long transcript in one prompt.

Fix: Segment first. Extract segment notes. Synthesize later.

## Shallow Summary

Symptom: Output is a generic summary with no tasks, metrics, decisions, or tools.

Fix: Re-run extraction using `references/extraction-schema.md`.

## Visual Blind Spot

Symptom: Transcript misses important screen demonstrations.

Fix: Capture frames/screenshots for the relevant timestamps and annotate what they show.

## YouTube Frame Capture 403

Symptom: `yt-dlp` metadata/transcript succeeds, but section download or ffmpeg frame capture fails with HTTP 403 from a YouTube media URL.

Fix: Record the visual gap instead of pretending screenshots exist. Use `capture_frames.py --youtube-client auto`, which tries the Android client first and then the default path. If that fails, use a browser screenshot workflow or capture frames from a successfully downloaded local segment.

## Premature Synthesis

Symptom: The methodology is written before segment evidence exists.

Fix: Stop synthesis. Build segment notes and indexes first.

## No Evidence Trail

Symptom: Final recommendations cannot be traced back to source segments.

Fix: Add segment IDs and timestamp references to notes, tasks, SOPs, and claims.
