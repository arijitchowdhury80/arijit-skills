The shaper's tier-choice logic holds for this ask. The work is mechanical and report-only, so Haiku fits. Four things in the request would change the work, so I list them as gap questions, and I'm not executing the task.
I did a short read-only check of the environment. The audit workspaces are scattered across at least four roots: `Algolia Search Audit/<Company>/research/` and `Previous-Audits/`, `PIP/temp/audits/`, `PRISM-Research-Docs/Current Audit SPA`, and `prism/backend/…`. The module JSONs follow a `NN-name.json` naming pattern. The only schema-like files I saw were `audit_data_schema.py` and `audit-health-check.py` under `algolia-search-audit/scripts`. I did not open them.
## (1) Numbered inventory
1. Scope: a sweep across all of the user's Algolia intel skill outputs, meaning all the JSON files in the audit workspaces.
2. Check A: every JSON file is valid JSON.
3. Check B: every file has the required fields for its module type. The module type comes from the producing skill, e.g. company, competitors, techstack, financial, hiring, investor, news, social, traffic.
4. Motivation or constraint: the work is "totally mechanical", so use a cheap model. The user names Haiku, "or whatever", so the tier is the user's call and any cheap tier qualifies.
5. Deliverable: a table of what is broken and where.
6. Context: "probably a lot of files", so volume is high and completeness matters.
7. Constraint: do not fix anything, report only.
8. Constraint: do not read the `.md` files, JSON only.
No self-corrections or retractions in the message.
## (2) Gap questions I would ask (one AskUserQuestion call, 4 max)
1. **Which roots count as "the audit workspaces"?** Options: (a) only `~/Dropbox/AI-Development/Algolia Search Audit/*/research*` including `Previous-Audits`; (b) also `PIP/temp/audits/` and `PIP/audit-skill-improvement` copies; (c) also `PRISM-Research-Docs` and `prism/backend`; (d) everything under AI-Development matching `NN-*.json`. This changes the file set, and the user said "all", so the answer decides whether the PIP and PRISM copies and `research-rerun/` folders are in.
2. **What defines "required fields for its module type"?** Options: (a) take the schema from `algolia-search-audit/scripts/audit_data_schema.py` and `audit-health-check.py`; (b) derive required keys from each `algolia-intel-*` SKILL.md output spec (this conflicts with the "don't read md" rule, since that is a different file set from the audit outputs, so it needs an explicit yes); (c) the user supplies a list. There is no stated source of truth, and the whole sweep depends on it.
3. **Which files are in scope for the field check?** Should the sweep include non-module JSONs such as `audit-data.json`, `screenshots` manifests, `package.json`, and eval outputs, or only `NN-*.json` module outputs? For files without a known module type, the options are to skip them, to check validity only, or to flag them as "unknown type".
4. **Table granularity and output location.** Options: one row per broken file (path, module type, failure kind, missing fields), or one row per missing field. Print inline only, or also write a CSV to the scratchpad? The default I would assume is one row per broken file, inline plus a scratchpad CSV.
## (3) The shaped prompt (target: Claude Haiku 5.5)
```
<context>
Arijit Chowdhury maintains Algolia Search Audit workspaces. Each workspace holds module output files produced by the algolia-intel-* skills (company, competitors, techstack, traffic, financial, hiring, investor, news, social, industry, partner, queries). Each module writes a markdown file and a JSON file named like NN-name.json, for example 01-company-context.json. The JSON files feed downstream modules, so a broken or incomplete file silently corrupts later audit steps. This task is a health sweep to find those files. It is a read-only report; no file is changed.
Audit workspace roots: {{ROOTS_FROM_Q1}}
Required-field source of truth: {{SCHEMA_SOURCE_FROM_Q2}}
The current date is 2026-10-12.
</context>
<task>
Find every JSON file inside the audit workspace roots. For each file, determine two things: whether it parses as valid JSON, and whether it contains the required fields for its module type. Then report every file that fails either check.
</task>
<requirements>
1. Cover every JSON file in scope. Enumerate the full file set first and report the total count, so completeness can be checked. Apply the same checks to every workspace, including rerun and previous-audit folders.
2. Validity check: a file fails if it does not parse as JSON, is empty, or is truncated. Record the parser error text.
3. Required-field check: infer the module type from the filename prefix and name, e.g. 01-company-context.json is the company module. Look up that type's required fields in the schema source named in context. A file fails if any required field is missing, null, or an empty string or empty collection where the schema expects content. Record the exact missing field names.
4. A JSON file whose module type has no schema entry is reported as "unknown module type" with its validity result, not skipped silently.
5. Use a script (Python with the standard json module is fine) to do the checking, so results are exact across a large file count. Run any Python with -I.
6. Keep working until every file in scope has been checked. Only stop to ask if you cannot continue without the user or before a risky step. When the work is done and checked, stop and report. Don't add anything that wasn't asked for.
</requirements>
<constraints>
- Read only the .json files, and the schema source named in context. Do not open any .md file, because the user asked for JSON only and the markdown twins are out of scope for this sweep.
- Report only. Make no edits to any file, and do not repair, reformat, delete, or move anything. Fixing is a separate decision for the user.
- Do not run any audit skill or regenerate any output.
- Scratch files go in the session scratchpad directory only.
</constraints>
<deliverables>
A single markdown table of broken files, one row per file, with these exact columns: workspace | file path (absolute) | module type | failure (invalid JSON / missing fields / empty / unknown type) | detail (parser error or the exact missing field names).
Above the table, one summary line: total files checked, total passing, total failing, counts per failure type.
Below the table, a one-line note listing any file paths that could not be read.
If nothing is broken, say so and show the counts.
Verification of completion: the checked count in the summary line equals the enumerated file count from requirement 1.
</deliverables>
<out_of_scope>
- Fixing, regenerating, or rewriting any file
- Reading or validating any .md file
- Judging the quality or accuracy of the content inside the JSON
- Checking screenshots, PDFs, HTML, or any non-JSON deliverable
</out_of_scope>
<assumptions>
- "Audit workspaces" means the roots confirmed in the interview; if the user did not answer, default to ~/Dropbox/AI-Development/Algolia Search Audit/** only.
- "Required fields" come from audit_data_schema.py and audit-health-check.py unless the user named another source.
- Module type is derived from the NN-name filename convention.
- Non-module JSONs (package.json, manifests) are checked for validity only and listed as "unknown module type" if invalid.
- One row per broken file; output printed inline plus a CSV in the scratchpad.
</assumptions>
The sections above are the authoritative reading of the input below. Where they differ (retracted options, resolved ambiguities), the sections win. The original is kept so you can check nothing was lost.
<original_input>
i need a sweep across all my algolia intel skill outputs, basically all the json files sitting in the audit workspaces, check every one of them is valid json and has the required fields for its module type, this is totally mechanical work so use a cheap model for it, haiku or whatever, and give me back a table of what is broken and where. there are probably a lot of files. dont fix anything, just report. dont go reading the md files, just the json.
</original_input>
```
Notes on lint: the prompt has no reasoning-echo wording and no MUST-shouting. It gives the definition of done and the output shape, not a step script. The only procedural line is "use a script", and that is a means constraint that protects exactness at high volume. The "report-only" rule is stated once, positively, per Haiku rule 8. The early-stop guard is the Haiku rule 3 wording, included because the file set is long. The user's mention of "haiku or whatever" is honoured, and the current date is included.
## (4) Coverage map
| # | Inventory item | Landed in |
|---|---|---|
| 1 | Sweep all JSON in audit workspaces | `<task>`, `<requirements>` 1, `<context>` roots |
| 2 | Valid JSON check | `<requirements>` 2 |
| 3 | Required fields per module type | `<requirements>` 3 and 4, `<context>` schema source |
| 4 | Cheap model, Haiku | Routing (5); stated in the preamble above. Not in the prompt body, since the executor does not need it |
| 5 | Table of what is broken and where | `<deliverables>` |
| 6 | Probably a lot of files | `<requirements>` 1 (enumerate and count), 5 (script), 6 (keep working); `<deliverables>` completeness check |
| 7 | Don't fix, just report | `<constraints>`, `<out_of_scope>` |
| 8 | Don't read md files | `<constraints>`, `<out_of_scope>` |
Nothing was dropped.
## (5) Routing recommendation
- **Model tier:** T1, `haiku` (Claude Haiku 5.5, `claude-haiku-5-5`). It is the user's stated preference and matches the table: schema checks, validation runs and file ops. Severity does not escalate, because the sweep is read-only and cheap to redo.
- **Effort wording:** "Start at `medium` (default). `low` for simple high-volume work if early-stopping and skipped checks are acceptable or guarded." Here `low` is guarded by the enumerated-count check in the deliverables, so `low` is a reasonable second try. Measure whether the checked count equals the enumerated count. If it stops short or skips files, go back to `medium`.
- **Skill:** none of the build skills. This is a one-off validation script plus report, not a code change, so `development-loop` is not needed. If the sweep is meant to become a recurring check, route to `code-validator` or `algolia-audit-eval` as a follow-up.
- **Budget-guard note (CLAUDE.md #6):** one agent, T1, small token estimate. The gating cost is the file enumeration, not model reasoning. Most of the work is a script, so the cost is low. Dispatching it as a subagent is justified because the output (a table) is much smaller than the input (hundreds of JSON files).
- **Next step if this were live:** show items (3) to (5) to the user, ask the four gap questions, wait for approval, then save to `~/.claude/prompt-library/2026-10-12-audit-json-sweep.md` and dispatch. I skipped the questions, the save and the dispatch as instructed.
