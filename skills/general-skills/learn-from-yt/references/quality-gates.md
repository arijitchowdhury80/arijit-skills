# Quality Gates

Use these gates to prevent shallow summaries and premature synthesis.

## Source Recon Gate

Pass only when:

- Source metadata is captured.
- Transcript availability is known.
- Chapter or segmentation strategy is chosen.
- Visual requirements are known.
- Raw artifact location is recorded.
- Pilot segment is selected.

## Segment Gate

A segment is complete only when:

- Timestamp range is recorded.
- Summary separates fact, inference, and recommendation.
- Core concepts and business principles are extracted.
- Action steps are captured when present.
- Tools, metrics, examples, warnings, and decisions are captured when present.
- Claims to verify are listed.
- Visual gaps are marked.
- Downstream software, research, SOP, or agent requirements are captured when present.
- Confidence level is stated.
- Evidence anchors are included.

## Index Gate

Indexes are complete only when segment extractions have updated:

- Tools
- Tasks
- Metrics
- Pitfalls
- Decisions
- Claims to verify
- Evidence map
- Glossary
- Research backlog
- Software to build

## Synthesis Gate

Do not synthesize final methodology until:

- Required segments are extracted or explicitly skipped.
- Visual gaps are documented.
- High-impact claims are marked for verification.
- Contradictions are listed.
- Evidence map exists.
- Open questions are separated from confirmed method.
- Recommendations cite source segments.

## Final Deliverable Gate

Final outputs are complete only when they include:

- Full knowledge base
- Business plan
- SOP library
- Execution checklist
- Tool stack
- Metrics plan
- Research backlog
- Software/automation backlog
- Open questions
- Evidence map
