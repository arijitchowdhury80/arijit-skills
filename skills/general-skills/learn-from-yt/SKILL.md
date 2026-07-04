---
name: learn-from-yt
description: Turn long videos, podcasts, courses, talks, calls, or lectures into structured knowledge bases, business methodologies, SOPs, execution plans, and downstream software or research requirements. Self-contained — captures the source (metadata, chapters, transcript, frames) and then segments, extracts, and synthesizes. Use when asked to transcribe, ingest, learn from, summarize deeply, process chapter-by-chapter, extract a business method from, or build an LLM/wiki knowledge base from video or audio content, especially business-building content such as POD, SaaS, marketing, sales, operations, product, strategy, or founder education.
---

# Learn From YT

Convert long-form media into reusable operating knowledge. This skill is **self-contained**: it captures the source and then does segmentation, extraction, screenshots, methodology, SOPs, execution checklists, and downstream build requirements — one pipeline, one chain.

When running helper scripts, resolve paths relative to this installed skill directory. Replace `<skill-root>` with the folder that contains this `SKILL.md`.

## One-Command Run (the execution chain)

```bash
python3 <skill-root>/scripts/run.py "YOUTUBE_URL" \
  --root ./Knowledge --domain "print-on-demand business" --minutes 10 --frame-interval 30
```

`run.py` chains the mechanical stages and leaves a ready-to-extract workspace:

1. **capture** (`capture.py`) — yt-dlp metadata + chapters + timestamped transcript → `raw-captures/<slug>/{metadata.json, source.md, raw/transcript.md}`.
2. **scaffold** (`create_knowledge_project.py`) — the knowledge-base folder structure.
3. **segment** (`segment_transcript.py`) — split the transcript into fixed-window markdown segments.
4. **frames** (`capture_frames.py`) — visual frames for demonstration-heavy sections.

Useful flags: `--capture-only` (grab source artifacts, nothing else), `--no-frames` (skip visuals), `--from-transcript PATH` (reuse an already-captured transcript and skip live fetch — use this when YouTube is rate-limiting / returns HTTP 429).

After `run.py`, YOU (the agent) do the judgment stages below: extract each segment, build indexes, run quality gates, and synthesize.

## Core Rules

- Define the operating contract before extraction: outcome, deliverables, evidence standard, visual requirements, raw storage, and done criteria.
- Start with a pilot segment before processing the full source.
- Do not process a long transcript in one context window.
- Do not synthesize the final methodology before segment extraction exists.
- Preserve raw source artifacts locally. Do not paste full copyrighted transcripts into chat.
- Mark visual-only demonstrations as a gap unless screenshots or frames are captured.
- Every extracted claim, task, SOP, or recommendation must be traceable to a segment or timestamp when possible.
- Separate fact, inference, recommendation, and open question.
- Optimize for business-building knowledge, but keep the method general enough for software, research, operations, and strategy topics.

## Workflow

1. Define the mission: topic, source URL/file, final outputs, audience, and business goal.
2. Run `run.py` (above) to capture + scaffold + segment + frames in one chain. For rate-limited or pre-captured sources, pass `--from-transcript`.
3. Inspect the generated `metadata.json`, `source.md`, and `raw/transcript.md`.
4. Run a pilot extraction on the first chapter/segment.
5. Refine the extraction schema using `references/extraction-schema.md`.
6. Extract every segment into the standard structure.
7. Run the segment quality gate in `references/quality-gates.md`.
8. Capture/annotate frames for visual demonstrations where visuals matter.
9. Build indexes: tasks, tools, metrics, pitfalls, decisions, claims, evidence map, glossary, software to build, research backlog.
10. Run the synthesis gate in `references/quality-gates.md`.
11. Synthesize final outputs: full knowledge base, business plan, SOP library, execution checklist, and downstream software/research requirements.
12. Record skill improvements after each source.

## Output Location

Default to a local `Knowledge/` folder unless the user specifies another destination. Treat the Obsidian vault as the ultimate single source of truth when available, but do not assume vault access — capture to local markdown first, then mirror into Obsidian.

## Screenshots And Frames

Capture frames only where visuals carry the meaning (UI demos, diagrams, dashboards). `run.py` calls `capture_frames.py`; to target a window:

```bash
python3 <skill-root>/scripts/capture_frames.py "YOUTUBE_URL" \
  --out-dir "./Knowledge/<domain>/<source>/visuals/frames" \
  --start "00:00:00" --end "00:10:00" --every-seconds 30
```

Name each visual with timestamp and segment ID; add a note explaining what it demonstrates. Requires `yt-dlp` + `ffmpeg`.

## References

- `references/extraction-schema.md` — defining/applying the segment extraction schema.
- `references/output-structure.md` — knowledge-base folders and final deliverables.
- `references/failure-modes.md` — when a run stalls, loops, over-plans, or goes shallow.
- `references/quality-gates.md` — before marking segment extraction or synthesis complete.

## Interview The User When Needed

Ask only questions that materially change the output: business objective, required deliverables, where the knowledge base lives, transcript-only vs visuals required, and whether to optimize for strategy, execution, software requirements, or all.
