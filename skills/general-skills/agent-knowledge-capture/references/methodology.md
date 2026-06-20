# Agent Knowledge Capture Methodology

## Intent

Every serious agent session should leave the project easier to resume.

The goal is not to save everything. The goal is to preserve enough evidence and distilled knowledge that a future agent can recover the state, respect decisions, and avoid repeating investigation.

## Capture Modes

| Mode | Use when | Output |
|---|---|---|
| `record` | General session produced durable knowledge | log + distilled updates |
| `decision` | A concrete choice was made | decision/ADR |
| `process` | A repeatable workflow changed | SOP/process note |
| `state` | Project status changed | status/handoff file |
| `raw-only` | Evidence must be preserved but not promoted yet | raw/session log |
| `distill-only` | Raw already exists | wiki/spec/decision updates |

## Classification

Classify every candidate item before writing:

- **Fact**: stable project or system information.
- **Decision**: accepted choice with alternatives or rationale.
- **Rationale**: why a decision was made.
- **Procedure**: repeatable steps.
- **Preference**: user or organization preference.
- **Failure mode**: what went wrong and how to detect/fix it.
- **Open question**: unresolved uncertainty.
- **Artifact**: file, report, build, output, source, or evidence path.
- **Task**: future action with owner or trigger.

## Routing

Prefer existing project conventions. If none exist, use this default:

```text
project/
  docs/
    decisions/ or adr/
    wiki/
    specs/
    processes/
    logs/
    handoffs/
```

For an Obsidian-style vault:

```text
Projects/{Project}/
  index.md
  raw/
  logs/
  wiki/
  decisions/
  workspace-state.md

Knowledge/wiki/
  concepts/
  syntheses/
  entities/

Standards/
Architecture/
```

## Promotion Test

Promote an item from raw log to durable docs only when one of these is true:

- Future work depends on it.
- A decision was made.
- A repeated process was discovered.
- A failure mode should not be rediscovered.
- The user corrected an assumption.
- The knowledge applies across projects.

If none are true, keep it only in the log.

## Receipt

End with a receipt:

```text
Recorded:
- Log: path
- Decision: path, if any
- Updated: path(s)
- Open questions: count
- Skipped: secrets/noise/duplicates, if relevant
```

Keep the receipt short. The files are the durable output.
