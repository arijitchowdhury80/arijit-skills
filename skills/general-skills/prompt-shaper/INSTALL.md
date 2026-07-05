# Install: prompt-shaper

1. **Skill** — copy this directory (SKILL.md, reference.md, evals/) to `~/.claude/skills/prompt-shaper/`.

2. **Auto-trigger hook** (optional but recommended) — copy `hooks/prompt-shaper-detect.js` to `~/.claude/hooks/`, `chmod +x` it, then register in `~/.claude/settings.json`:

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

Fires on inputs ≥700 chars (or 3+ paragraphs ≥400 chars); silent on slash commands, code-dominated pastes, and system/task notifications.

3. **Prompt library** — approved prompts save to `~/.claude/prompt-library/` (skill creates it on first use).

## Eval status

Iteration-1 benchmark (2026-07-03, Fable 5): with-skill 35/35 assertions (100%) vs baseline 19/35 (55%). Cost: ~+13.5k tokens / +23s per shaping. Known improvement candidate: add light repo/memory recon before composing (baseline runs occasionally discovered existing code the shaped prompt missed).
