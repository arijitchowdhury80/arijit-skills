# Output Structure

Create a durable local knowledge base before moving content to Obsidian.

## Folder Layout

```text
Knowledge/
  <domain>/
    <source-slug>/
      source-card.md
      source-manifest.md
      extraction-log.md
      methodology.md
      business-plan.md
      execution-plan.md
      open-questions.md
      segments/
        index.md
        001-introduction.md
      indexes/
        tools.md
        tasks.md
        metrics.md
        pitfalls.md
        decisions.md
        claims-to-verify.md
        evidence-map.md
        glossary.md
        research-backlog.md
        software-to-build.md
      sop/
        index.md
      visuals/
        frames/
        screenshots/
        notes.md
      raw/
        transcript.md
        metadata.json
```

## Source Card

Include:

- Title
- URL or source path
- Creator/source
- Capture date
- Duration
- Domain
- Business objective
- Transcript status
- Visual capture status
- Chapter source
- Raw artifact links

## Source Manifest

Track:

- Raw transcript path
- Metadata path
- Segment strategy
- Chapter source
- Visual capture method
- Known capture failures
- Extraction schema version
- Processing status
- Last processed segment

## Extraction Log

Append:

- Date/time
- Action
- Segment/source
- Result
- Failure mode if any
- Next action

## Final Deliverables

For business-building sources, produce all of:

- Full knowledge base
- Business plan
- SOP library
- Execution checklist
- Tool stack
- Metrics plan
- Research backlog
- Software/automation backlog
- Evidence map
- Decision log

## Obsidian Migration

When Obsidian access exists:

- Keep raw transcript out of high-level notes unless explicitly desired.
- Move polished notes, indexes, SOPs, and methodology into the vault.
- Preserve links back to raw local artifacts.
- Keep private or copyrighted raw captures controlled and clearly labeled.
