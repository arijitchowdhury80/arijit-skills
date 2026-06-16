# Learn From YT

Portable AI skill for turning long videos, podcasts, calls, courses, or lectures into structured knowledge bases, business methodologies, SOP libraries, execution checklists, and downstream software or research requirements.

This is the first WorkOS knowledge-extraction skill. It is optimized for business-building content such as POD, SaaS, marketing, sales, operations, product strategy, and founder education, while remaining general enough for technical lectures, product demos, and research talks.

## What It Does

- Captures raw source artifacts before synthesis.
- Segments long transcripts by chapter, timestamp, topic, or fixed windows.
- Extracts claims, tactics, SOP steps, tools, metrics, risks, open questions, and evidence.
- Captures frames or screenshots when visual demonstrations matter.
- Produces a reusable knowledge base, business plan, SOP library, execution checklist, and downstream software/research backlog.
- Preserves traceability from final recommendations back to segments and timestamps.

## Skill Layout

```text
learn-from-yt/
├── SKILL.md
├── README.md
├── install-skill.sh
├── agents/
│   └── openai.yaml
├── references/
│   ├── extraction-schema.md
│   ├── failure-modes.md
│   ├── output-structure.md
│   └── quality-gates.md
└── scripts/
    ├── capture_frames.py
    ├── create_knowledge_project.py
    └── segment_transcript.py
```

## Install

From a fresh checkout:

```bash
git clone https://github.com/arijitchowdhury80/arijit-skills.git
cd arijit-skills/skills/general-skills/learn-from-yt
chmod +x install-skill.sh
```

Install everywhere on the current machine:

```bash
./install-skill.sh --all
```

Install only for Codex:

```bash
./install-skill.sh --codex
```

Install only for Claude Code:

```bash
./install-skill.sh --claude
```

Install into a Hermes skills directory:

```bash
./install-skill.sh --hermes-dir /opt/data/skills
```

For Hermes/chowmes, run the install as the runtime user or fix ownership after installation so the Hermes process can read and update runtime files safely.

## Default Install Locations

| Runtime | Location |
|---------|----------|
| Codex | `$CODEX_HOME/skills/learn-from-yt` or `~/.codex/skills/learn-from-yt` |
| Claude Code | `$CLAUDE_HOME/skills/learn-from-yt` or `~/.claude/skills/learn-from-yt` |
| Hermes | Path passed with `--hermes-dir`, usually `/opt/data/skills/learn-from-yt` on the server |

## Dependencies

The skill itself is markdown and Python. For full YouTube capture and visual extraction, the environment should have:

- Python 3
- `yt-dlp`
- `ffmpeg`
- `youtube-transcript-api` as a fallback transcript provider

The helper scripts fail with clear messages when optional media dependencies are missing.

## Usage

Ask the agent to use the skill on a video or transcript:

```text
Use learn-from-yt on this YouTube video and build the knowledge base, SOPs, execution checklist, and downstream software requirements.
```

Claude Code users can invoke it from the slash command list after installation:

```text
/learn-from-yt
```

Codex and Hermes should load the skill by name when the task involves video ingestion, methodology extraction, business-building knowledge capture, or chapter-by-chapter synthesis.

## Operating Standard

Do not jump straight to summary. The skill is designed around a durable pipeline:

1. Preserve raw capture.
2. Create a knowledge project scaffold.
3. Run a pilot segment.
4. Segment the source.
5. Extract each segment with evidence.
6. Capture visuals where they matter.
7. Build indexes and backlog artifacts.
8. Synthesize final methodology and execution assets.
9. Record failure modes and skill improvements.

## Download For Other Agents

Other Codex, Claude Code, or Hermes agents can pull the skill from:

```text
https://github.com/arijitchowdhury80/arijit-skills/tree/main/skills/general-skills/learn-from-yt
```

For automated setup, clone the repo and run `install-skill.sh` with the appropriate target flags.
