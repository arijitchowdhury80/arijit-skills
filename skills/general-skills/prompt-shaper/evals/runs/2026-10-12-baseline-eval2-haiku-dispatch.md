## (1) Inventory
1. Scope: sweep all JSON outputs produced by the Algolia intel skills, sitting in the audit workspaces. "Every one" means full coverage, not a sample.
2. Check A: each file is valid JSON (parses).
3. Check B: each file has the required fields for its module type (company, techstack, competitors, financial, hiring, news, social, investor, and so on).
4. Execution tier: "totally mechanical", so use a cheap model, "haiku or whatever". Haiku is a preference, not a hard lock.
5. Deliverable: a table of what is broken and where.
6. Volume: "probably a lot of files" (count unknown, so the plan must scale).
7. Constraint: do not fix anything, report only (read-only).
8. Constraint: do not read the .md files, only the .json. Each module writes an .md and a .json pair, so the .md files must be skipped.
No self-corrections in the message. Item 6 is a belief, not a fact, so the executor must count the files itself.
## (2) Gap questions I would ask
I would ask these in a single AskUserQuestion call, capped at 4.
1. **Where are the audit workspaces, and which ones count?** I have not verified the location. Options: every workspace under one root, only the ones from the last N days, or a specific list. This decides the glob and whether "every one" includes stale or test workspaces.
2. **Where is the "required fields per module type" definition?** Candidates: the Output Contract in each `algolia-intel-*` SKILL.md, a schema file, or the checks in `algolia-search-audit/scripts`. Options: (a) use the existing definition, (b) infer fields from the majority of files per module (weaker, and it hides a field missing from every file), (c) you give me the list. This one changes the work the most.
3. **Do you want a failure severity split?** For example: unparseable JSON versus parses but missing a required field versus field present but empty or null. Or is any of these simply "broken"?
4. **Is the report a chat table, or a saved file too?** If it is saved, where? The default would be a CSV or markdown table under the scratchpad.
Two points the blob already answers, so I would not ask about them. The task is read-only. The .md files are off limits.
I would also note two things the user did not ask about but should hear:
- **Reading JSON with an LLM does not scale.** An agent opening hundreds of files is the work the model-economics rule warns against. The right shape is a small deterministic script that haiku writes or runs and then reports on. I would record this as an assumption, not ask about it.
- **The .md ban conflicts with one source.** If the required fields live in a SKILL.md, the executor must read that one definition. I would ask to carve that out as an explicit exception.
## (3) Shaped prompt
Target is haiku, so it gets explicit numbered steps and a fixed output format. It gets no show-your-thinking language, and no fable-style one-line steering.
```xml
<context>
Arijit runs Algolia Search Audits. Each audit has a workspace folder. The algolia-intel-* modules
write paired outputs into it: a human-readable .md and a machine-readable .json (for example
01-company-context.json, 02-tech-stack.json, 04-competitors.json, 08-financial-profile.json,
09b-social-signals.json, 09c-news-signals.json, 09d-hiring-signals.json, 11-investor-intelligence.json).
Downstream modules read these JSON files, so a malformed or incomplete one breaks later steps.
This is a read-only health check. The result is a table Arijit will read to decide what to
re-run. A wrong or missing row means a broken file goes unnoticed, so completeness matters more
than speed.
</context>
<task>
Find every .json output produced by the algolia-intel-* modules across all audit workspaces under
[WORKSPACE_ROOT]. For each file, check (A) it is valid JSON and (B) it contains the required fields
for its module type. Return one table of every file that fails either check. Change nothing.
</task>
<requirements>
1. Discover first. Run one find command for *.json under [WORKSPACE_ROOT] and report the total count
   and the count per workspace before checking anything.
2. Do the checking with a single small script (Python, `python3 -I`), not by opening files one at a
   time in chat. The script loops over every discovered file.
3. Check A: attempt json.load on each file. Record the exact parse error and line/column on failure.
4. Check B: identify the module type from the filename prefix (for example 01- company, 02- tech
   stack, 04- competitors, 08- financial, 09b- social, 09c- news, 09d- hiring, 11- investor). Compare
   against the required-field list in [SCHEMA_SOURCE]. List each missing field by name. Also flag a
   required field that is present but null or empty, in a separate column.
5. Files whose module type has no known field list go in a separate "unclassified" list. Do not
   guess fields for them and do not drop them silently.
6. Coverage proof: the number of rows checked must equal the discovered count. Print
   checked = N of N, passing = X, failing = Y, unclassified = Z. If the numbers do not reconcile,
   say so and stop.
7. Report format: a markdown table with columns
   workspace | file path | module type | failure (INVALID_JSON / MISSING_FIELDS / EMPTY_FIELDS) | detail.
   Sort by workspace, then filename. Put the totals line above the table.
</requirements>
<constraints>
- Read-only. Do not edit, rename, move, delete, repair, or reformat any file. Do not write into the workspaces.
- Do not read any .md file. Match on *.json only. The single exception is the schema source below,
  if it is a SKILL.md.
- Write any script or intermediate output to the scratchpad directory, not into the workspaces.
- Do not run `python3` from inside a workspace directory. Pass paths as arguments and use `-I`.
- Do not call any network service or any Algolia API. Everything is local disk.
- No em-dashes in the report.
</constraints>
<deliverables>
- The totals line and the failure table, in chat.
- The script path in the scratchpad, so the check can be re-run.
- Completion is verified by the reconciliation line in requirement 6. The claim "all files checked"
  is only allowed if checked equals discovered. Otherwise the report must say "partial" and name
  what was skipped.
</deliverables>
<out_of_scope>
Fixing or regenerating any file. Reading or validating .md files. Judging whether the content is
accurate or good (that belongs to algolia-audit-eval and algolia-audit-factcheck). Any file outside
the audit workspaces.
</out_of_scope>
<assumptions>
- [WORKSPACE_ROOT] and [SCHEMA_SOURCE] are filled from the answers to questions 1 and 2. Until then
  they stay unresolved placeholders, and the prompt must not be dispatched.
- Haiku is used as requested. The run is read-only and cheap to redo, so no tier escalation. Haiku
  is told to use a script, because haiku evals that read many files by hand tend to stall.
- "Broken" covers both unparseable JSON and missing required fields, per the blob. Null or empty
  required fields are reported separately.
- The workspace .json set may include files that are not intel-module outputs (config, caches).
  Those go to "unclassified", not to failures.
</assumptions>
<original_input>
i need a sweep across all my algolia intel skill outputs, basically all the json files sitting in the audit workspaces, check every one of them is valid json and has the required fields for its module type, this is totally mechanical work so use a cheap model for it, haiku or whatever, and give me back a table of what is broken and where. there are probably a lot of files. dont fix anything, just report. dont go reading the md files, just the json.
</original_input>
```
## (4) Coverage map
| # | Inventory item | Landed in |
|---|---|---|
| 1 | Sweep all intel JSON in audit workspaces | `<task>`, requirements 1 and 7, `<assumptions>` |
| 2 | Check valid JSON | requirement 3 |
| 3 | Check required fields per module type | requirement 4, requirement 5 (unclassified) |
| 4 | Cheap model, haiku | `<assumptions>`, plus the routing in section 5 |
| 5 | Table of what is broken and where | requirement 7, `<deliverables>` |
| 6 | "Probably a lot of files" | requirements 1, 2 and 6 (count first, script, reconciliation) |
| 7 | Don't fix, report only | `<constraints>`, `<out_of_scope>` |
| 8 | Don't read .md, only .json | `<constraints>` (with the SKILL.md exception) |
Nothing was dropped. The `<original_input>` section carries the verbatim text.
## (5) Routing recommendation
- **Model tier:** T1, haiku, as the user asked. The work is deterministic and read-only, so it is cheap to redo. Opus or fable would be wasted.
- **Effort:** low. It is a script run with a fixed report format.
- **Shape:** one single haiku agent, not a fan-out. A single script handles volume better than several agents. Do not split by workspace, because the cross-workspace reconciliation count is the control.
- **Skill:** none needed. This is not a build. `algolia-audit-eval` is the nearest existing skill, but it scores quality, so it is not a fit. Reuse check before dispatch: look at `~/.claude/skills/algolia-search-audit/scripts` and its tests. A JSON or field validator may already exist there, and reusing it is better than a new script.
- **Verify the result.** Under Guardrail #1, a haiku report is not evidence. After it returns, spot-check 2 or 3 of the failing rows on disk, and confirm the `checked = N of N` line against an independent `find ... | wc -l`. Do not use `grep -c` for the count, because of the double-zero false-green issue in memory.
- **Blocker before dispatch:** the two unresolved placeholders, workspace root and schema source. If the answer to question 2 is "infer from the files", I would push back. That makes the check circular and hides any field missing from every file.
I produced no file and ran no command, so my earlier reply rests on no new artifact. Here is what it actually rested on.
- **Files I read:** `/Users/arijitchowdhury/.claude/skills/prompt-shaper/SKILL.md` and `/Users/arijitchowdhury/.claude/skills/prompt-shaper/reference.md`. I applied their steps to your message.
- **Nothing saved:** The shaped prompt exists only in my previous reply. You told me not to save a file, so there is no file at `~/.claude/prompt-library/`. The task itself was not executed.
- **"Nothing was dropped" is a claim from my own mapping.** It comes from the coverage table in that reply. I did not check it against any other source.
- **Unverified:**
  - I did not look at the disk for the audit workspaces, so `[WORKSPACE_ROOT]` is still a placeholder.
  - I did not confirm where the required-fields definition lives.
  - I did not open `/Users/arijitchowdhury/.claude/skills/algolia-search-audit/scripts`. My suggestion that a validator might already exist there is a guess.
  - The filename-to-module mapping (01-, 02-, 04-, 08-, 09b-, 09c-, 09d-, 11-) comes from the skill descriptions in my context, not from files on disk.
The status is "shaped prompt drafted, not yet verified against the disk, not executed."
