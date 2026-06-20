# Agent Knowledge Capture

Portable `/record` methodology for Codex, Claude Code, Hermes, MyOS, and future coding-agent workflows.

This skill turns an agent session into durable knowledge without dumping the whole chat. It preserves useful raw evidence, distills decisions and reusable lessons, routes updates to the right project or vault layer, and returns a compact receipt.

## What It Does

- Captures concise session logs and evidence.
- Extracts decisions, process changes, project state, reusable lessons, and open questions.
- Routes knowledge into project docs, ADRs, wiki pages, Obsidian notes, or agent memory proposals.
- Keeps one consistent method across runtimes while allowing different destination paths.

## Install

```bash
git clone https://github.com/arijitchowdhury80/arijit-skills.git
cd arijit-skills/skills/general-skills/agent-knowledge-capture
./install-skill.sh --all
```

Install only one runtime:

```bash
./install-skill.sh --codex
./install-skill.sh --claude
```

Hermes install target:

```bash
./install-skill.sh --hermes-dir /opt/data/skills
```

## Usage

In Claude Code, use:

```text
/record
```

In Codex or another agent, ask:

```text
record this
capture what we learned
save the decision
update the vault/wiki/docs
```

## Method

```text
agent session
  -> identify project/workspace
  -> preserve raw evidence if useful
  -> classify durable knowledge
  -> route to project, shared, or memory layer
  -> patch files/indexes/links
  -> return compact receipt
```

See `SKILL.md` for the executable agent instructions and `references/` for the full methodology and destination rules.
