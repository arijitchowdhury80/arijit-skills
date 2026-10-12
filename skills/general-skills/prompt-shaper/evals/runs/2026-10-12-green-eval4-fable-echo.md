I'll start by reading the skill file.
**Not executed.** I read SKILL.md, `general.md` and `claude-fable.md`, and applied them to your message. I skipped AskUserQuestion and saved no file.
## (1) Inventory
1. Hand the whole explore-algolia case study pipeline refactor to Fable.
2. Reason for Fable: it is the hardest thing on your plate.
3. Symptom: the ingest is flaky.
4. Symptom: matches are wrong about 10% of the time.
5. Symptom: the badge projection step sometimes writes to the wrong record.
6. Wants it to "really think hard".
7. Wants to see its reasoning as it goes, so you can follow along.
8. "Super thorough, go beyond the basics."
9. "Don't stop until everything is green."
10. Subagents are allowed.
11. The index schema stays as is. It is locked.
12. Nothing is pushed to the live index unless you say so.
Items 7, 8 and 9 need rewriting for Fable, not copying over. Item 7 would trigger the reasoning-echo refusal. Item 8 is a quality modifier that makes Fable overshoot. Item 9 has no definition of "green".
## (2) Gap questions I would ask
These would go in one AskUserQuestion call, max 4.
1. **What does "green" mean?** Which checks must pass? I'd offer options: (a) existing tests plus a new regression test per bug, (b) also a re-run of the match set against a labelled sample with a target error rate, (c) a dry-run of badge projection showing zero wrong-record writes. The 10% figure has no target, so "fixed" is undefined without this.
2. **Is this a refactor or a bug fix first?** You named three concrete defects, plus "refactor". Options: (a) root-cause and fix the three defects, restructuring only what they require; (b) full restructure of the pipeline, with the fixes as part of it; (c) assess first and bring you a plan before any change. This decides the scope of the deliverable.
3. **What counts as the live index, and where can it write?** Options: (a) a staging or scratch index is allowed, only `algolia_case_studies` and the implementation records are off-limits; (b) local files and dry-runs only; (c) it can write to the live index in a read-only verification mode. This sets the line for "no push without me saying so".
4. **Git and where it runs.** Options: (a) commit locally on a branch, never push; (b) no commits, leave a diff; (c) commit and push to GitHub when green. This also tells me whether to use the unattended autonomy clause or the watching-human clause. You said you want to follow along, so I assumed you are watching.
## (3) Shaped prompt
Target is Fable 5.1, which you chose. I assumed you are watching and set a progress cadence. Answers to the gap questions would replace the matching items under `<assumptions>`.
```
<context>
Arijit Chowdhury owns the Explore Algolia project: a grounded index of Algolia customer case studies (index algolia_case_studies, built from algolia.com/customers) that feeds teasers and badges onto customer implementation records. The existing `algolia-casestudies` skill covers fetching, re-indexing, reviewing and locking customer matches, and projecting badges onto implementation records. Read it and the pipeline code first, because it defines the current workflow. The implementation data is confidential and NDA-gated.
The pipeline has three known defects: (a) the ingest is flaky, (b) roughly 10% of case-study-to-customer matches are wrong, (c) the badge projection step sometimes writes to the wrong record. This is the hardest item on Arijit's plate and he wants it handled end to end. He is watching and wants to follow progress.
</context>
<task>
Refactor the explore-algolia case study pipeline so that ingest is reliable, matches are correct, and badge projection only ever writes to the record it was meant for. Find the root cause of each defect and fix the class, not the one instance. Restructure only as much as the root causes require.
</task>
<requirements>
1. Ingest: identify why it is flaky and make it deterministic and re-runnable, with failures surfaced instead of swallowed.
2. Matching: measure the current error rate on a sample you label from the data, find why about 10% are wrong, and fix it. Report before and after rates.
3. Badge projection: find every path that can write to the wrong record. Make writes keyed by an unambiguous record identity, and add a check that rejects a write whose target does not match its source.
4. Each fix ships with a regression test that fails on the old behavior and passes on the new.
5. Done means every item in the deliverables section is met and you can point to evidence for each from this session.
</requirements>
<constraints>
1. The index schema is locked. Do not add, remove, rename or retype any field or setting. If a fix seems to need a schema change, stop and report it as a proposal.
2. Do not write to, push to, or re-index the live index (algolia_case_studies and the implementation records) without Arijit's explicit yes in chat. Use dry-runs, local fixtures or a scratch index for verification. The reason: a wrong write to live data is hard to undo.
3. Never commit secrets. Read credentials from the project's existing env files.
4. Use subagents for independent subtasks and keep working while they run. Use a fresh-context subagent as verifier rather than reviewing your own work. Before dispatching more than two subagents, state the count, the tier for each, and a rough token estimate. Give mechanical work (running tests, grepping, schema checks) to the cheapest tier.
5. You are working with Arijit watching. Say in a line what you are about to do, give brief updates as milestones land (root cause found, fix landed, check run), and close with a recap that stands on its own. When you have enough information to act, act. Do not re-derive facts already established. Give recommendations, not exhaustive surveys.
6. Before reporting progress, audit each claim against a tool result from this session. Report only work you can point to evidence for, and say what is not yet verified.
7. When it will not affect the result, edit files surgically instead of rewriting them.
</constraints>
<deliverables>
1. Code changes on a local branch, with a diff Arijit can read.
2. A short root-cause note per defect: what caused it, where, and which other places had the same class of bug, found by searching the whole repo.
3. Green means all of these, shown with command output: the existing test suite passes; the new regression tests pass; match error rate on the labelled sample is measured before and after; a dry-run of badge projection shows zero writes to a non-matching record; a re-run of ingest twice gives identical results.
4. A final report listing each item as done, deferred or blocked, with the evidence for each.
</deliverables>
<out_of_scope>
1. Any change to the index schema.
2. Any write, push or re-index to the live index.
3. Pre-existing bugs or improvements unrelated to the three defects: report them as follow-ups, do not fix them.
4. Writing new case studies (the algolia-case-study skill's job).
</out_of_scope>
<assumptions>
1. Green is defined as in deliverable 3, until Arijit says otherwise.
2. Scope is root-cause fixes plus the restructuring they require, not a full rewrite.
3. Verification runs against local data, fixtures or a scratch index. Git work stays on a local branch, with no push unless Arijit says so.
4. The "about 10%" match error rate is Arijit's estimate. Measure it before trusting it.
5. Arijit is watching, so progress updates and a closing recap are expected.
6. Arijit asked to see reasoning as it goes. This prompt delivers that through short milestone updates and a closing recap, because reasoning echo is not requested of this model.
</assumptions>
The sections above are the authoritative reading of the input below. Where they differ (retracted options, resolved ambiguities), the sections win. The original is kept so you can check nothing was lost.
<original_input>
ok big one. i want to hand the whole explore-algolia case study pipeline refactor to fable since its the hardest thing on my plate, the ingest is flaky, matches are wrong like 10% of the time, and the badge projection step sometimes writes to the wrong record. i want it to really think hard, show me its reasoning as it goes so i can follow, be super thorough, go beyond the basics, and dont stop until everything is green. it can use subagents. keep the index schema as is, thats locked. and dont let it push anything to the live index without me saying so.
</original_input>
```
## (4) Coverage map
| # | Inventory item | Landed in |
|---|---|---|
| 1 | Hand whole refactor to Fable | `<task>`, routing |
| 2 | Hardest thing on plate | `<context>` |
| 3 | Ingest flaky | `<context>`, `<requirements>` 1, `<deliverables>` 3 |
| 4 | Matches wrong about 10% | `<context>`, `<requirements>` 2, `<assumptions>` 4 |
| 5 | Badge projection writes to the wrong record | `<context>`, `<requirements>` 3, `<deliverables>` 3 |
| 6 | Think really hard | Dropped as wording. Fable's thinking is always on and adaptive, and the effort setting is the lever, so it goes in routing. |
| 7 | Show reasoning as it goes | Converted, not copied. Reasoning echo can trigger a `reasoning_extraction` refusal. `<constraints>` 5 asks for milestone updates and a recap, and `<assumptions>` 6 records why. |
| 8 | Super thorough, go beyond the basics | Dropped as a quality modifier, because it makes Fable overshoot. Replaced by a concrete deliverable list, root-cause plus class search (`<deliverables>` 2), `<constraints>` 5 ("act, don't re-derive, recommend") and `<out_of_scope>` 3. |
| 9 | Don't stop until everything is green | `<requirements>` 5, `<deliverables>` 3 (green defined), `<assumptions>` 1 |
| 10 | Subagents allowed | `<constraints>` 4 (tiers and counts declared, fresh-context verifier) |
| 11 | Schema locked | `<constraints>` 1, `<out_of_scope>` 1 |
| 12 | No live-index push without your say | `<constraints>` 2, `<out_of_scope>` 2, `<assumptions>` 3 |
Added by me, not in your message:
- The scope guard in `<out_of_scope>` 3 and `<constraints>` 7 (Fable rules 4 and 10).
- The grounded-claims rule in `<constraints>` 6 (Fable rule 7).
- No secrets in commits (`<constraints>` 3).
- The pointer to the `algolia-casestudies` skill.
## (5) Routing recommendation
- **Model:** T4 `fable` (Fable 5.1, `claude-fable-5-1`). You chose it explicitly, which the routing table requires for T4. The severity override also supports it, since live-index writes are costly to reverse. The main session stays at its own tier for orchestration. Fable's subagents should run at the cheapest tier that fits, with mechanical checks at `haiku`.
- **Effort wording:** "Start at `high` (default). Step down to `medium` or `low` if evals hold; step up to `xhigh` only for a measured gain." I'd keep `high` and not use `xhigh` or `max`, because this is a long multi-step build and not one long document. If you do pick `xhigh` or `max`, add the one-limit note: "everything in one reply counts toward one limit, don't draft the deliverable twice."
- **Skill:** `development-loop`, because this is a refactor with tests and a rollback story. Pair it with `root-cause-sweep` before any "fixed" claim, since the prompt asks for class-level fixes. Use `algolia-casestudies` as the domain reference for the pipeline's existing steps.
- **Flag on your request:** "Show me its reasoning" and "think really hard" are the two lines most likely to cause trouble on Fable. The shaped prompt gives you what you want through milestone updates and a recap, and effort handles the depth.
