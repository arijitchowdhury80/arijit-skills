---
name: video-methodology-builder
description: Turn long videos, podcasts, courses, talks, calls, or lectures into structured knowledge bases, business methodologies, SOPs, execution plans, and downstream software or research requirements. Use when Codex is asked to transcribe, ingest, learn from, summarize deeply, process chapter-by-chapter, extract a business method from, or build an LLM/wiki knowledge base from video or audio content, especially business-building content such as POD, SaaS, marketing, sales, operations, product, strategy, or founder education.
---

# Video Methodology Builder

Use this skill to convert long-form media into reusable operating knowledge. This skill is a layer above `youtube-knowledge`: use `youtube-knowledge` for capture/transcripts, then use this skill for segmentation, extraction, screenshots, methodology, SOPs, execution checklists, and downstream build requirements.

When running helper scripts, resolve paths relative to this installed skill directory. In examples below, replace `<skill-root>` with the folder that contains this `SKILL.md`.

## Core Rules

- Define the operating contract before extraction: outcome, deliverables, evidence standard, visual requirements, raw storage, and done criteria.
- Start with a pilot segment before processing the full source.
- Do not process a long transcript in one context window.
- Do not synthesize the final methodology before segment extraction exists.
- Do not assume a skill is a callable tool. Inspect the skill and use its script or documented workflow.
- Preserve raw source artifacts locally. Do not paste full copyrighted transcripts into chat.
- Mark visual-only demonstrations as a gap unless screenshots or frames are captured.
- Every extracted claim, task, SOP, or recommendation must be traceable to a segment or timestamp when possible.
- Separate fact, inference, recommendation, and open question.
- Optimize for business-building knowledge, but keep the method general enough for software, research, operations, and strategy topics.

## Workflow

1. Define the mission: topic, source URL/file, final outputs, audience, and business goal.
2. Capture source artifacts with `youtube-knowledge` or an equivalent transcript workflow.
3. Create a knowledge project scaffold:

```bash
python3 <skill-root>/scripts/create_knowledge_project.py \
  --root ./Knowledge \
  --title "The ONLY Print on Demand Guide You Need for 2026" \
  --domain "print-on-demand business"
```

4. Run a pilot extraction on the first 5 to 10 minutes or first chapter.
5. Refine the extraction schema using `references/extraction-schema.md`.
6. Segment the transcript by official chapters, timestamps, topic breaks, or fixed windows.
7. Extract every segment into the standard structure.
8. Run the segment quality gate in `references/quality-gates.md`.
9. Capture screenshots/frames for visual demonstrations when visuals matter.
10. Build indexes: tasks, tools, metrics, pitfalls, decisions, claims, evidence map, glossary, software to build, and research backlog.
11. Run the synthesis gate in `references/quality-gates.md`.
12. Synthesize final outputs: full knowledge base, business plan, SOP library, execution checklist, and downstream software/research requirements.
13. Record skill improvements after each source.

## Output Location

Default to a local `Knowledge/` folder unless the user specifies another destination. Treat Obsidian as the ultimate destination when available, but do not assume vault access. Use local markdown first, then later migrate or mirror into Obsidian.

## Capture With youtube-knowledge

Use the existing YouTube skill when the source is YouTube:

```bash
python3 <youtube-knowledge-skill-root>/scripts/youtube_to_wiki.py \
  "YOUTUBE_URL" \
  --wiki-root "./Knowledge/raw-captures"
```

Then inspect the generated `metadata.json`, `source.md`, and `raw/transcript.md`.

## Screenshots And Frames

If the content relies on visual demonstrations, capture frames or screenshots. For YouTube, use `yt-dlp` and `ffmpeg` when available. Store frames under:

```text
visuals/
  frames/
  screenshots/
  notes.md
```

Name each visual with timestamp and segment ID where possible. Add a short note explaining what the frame demonstrates.

Helper:

```bash
python3 <skill-root>/scripts/capture_frames.py \
  "YOUTUBE_URL" \
  --out-dir "./Knowledge/<domain>/<source>/visuals/frames" \
  --start "00:00:00" \
  --end "00:10:00" \
  --every-seconds 30
```

## References

- Read `references/extraction-schema.md` when defining or applying the segment extraction schema.
- Read `references/output-structure.md` when creating the knowledge base folder or final deliverables.
- Read `references/failure-modes.md` when a run gets stuck, loops, over-plans, or produces shallow summaries.
- Read `references/quality-gates.md` before marking segment extraction or final synthesis complete.

## Interview The User When Needed

Ask only questions that materially change the output. Prioritize:

- What is the business objective for this source?
- What final deliverables are required?
- Where should the knowledge base live?
- Is transcript-only acceptable, or are visuals required?
- Should the extraction optimize for strategy, execution, software requirements, or all of them?
