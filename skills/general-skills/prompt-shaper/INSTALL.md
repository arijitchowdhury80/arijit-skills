# Install: prompt-shaper

This directory is the single source. `~/.claude/skills/prompt-shaper/` and `~/.agents/skills/prompt-shaper/` are installed copies and must stay byte-identical to it. Do not edit the installed copies; edit here, then re-copy.

1. **Skill:** copy this directory (SKILL.md, reference/, evals/) to `~/.claude/skills/prompt-shaper/`. For Codex, copy the same files to `~/.agents/skills/prompt-shaper/`. Step 3 of the skill already covers Codex as an executor via `reference/codex-gpt.md`.

2. **Auto-trigger hook** (recommended): copy `hooks/prompt-shaper-detect.js` to `~/.claude/hooks/`, `chmod +x` it, then register in `~/.claude/settings.json`:

```json
"UserPromptSubmit": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "\"/opt/homebrew/bin/node\" \"/Users/<you>/.claude/hooks/prompt-shaper-detect.js\"",
        "timeout": 5,
        "statusMessage": "Checking input shape..."
      }
    ]
  }
]
```

Fires on inputs of 700+ chars (or 3+ paragraphs at 400+ chars); silent on slash commands, code-dominated pastes, and system/task notifications. The hook text is deliberately strict ("You MUST invoke... Do NOT skip because the input looks already structured"). That wording was added 2026-08-19 after the model repeatedly rationalized skipping the skill on structured-looking blobs. Keep it.

3. **Prompt library:** approved prompts save to `~/.claude/prompt-library/` (skill creates it on first use). One library for both Claude and Codex.

## Reference layout

`reference/general.md` is read on every run. One target file is read per run: `claude-haiku.md`, `claude-sonnet.md`, `claude-opus.md`, `claude-fable.md`, `codex-gpt.md`. Each file names its source page and read date in its header. When a new model family ships, re-read the vendor page and update that one file; the old monolithic `reference.md` (2026-07-03, Opus 4.8 and Fable 5 era) is retired to `evals/runs/_retired-reference-2026-07-03.md` for comparison.

## Eval status

- 2026-07-03, iteration 1 (Fable 5): with-skill 35/35 assertions vs baseline 19/35.
- 2026-10-12, reference rebuilt on the 5.5-series pages. Eval 2 (haiku-dispatch) re-baselined: old skill applied "haiku gets explicit numbered steps" and a fixed `low` effort, neither of which the Haiku 5.5 page supports. New cases: 4 (fable target with a show-your-reasoning ask), 5 to 7 (negative triggers). GREEN runs recorded in `evals/runs/`.
- Known improvement candidate: light repo/memory recon before composing (baseline runs occasionally discovered existing code the shaped prompt missed).
