---
name: algolia-campaign-abx
version: 2.0.0
description: ABX campaign package for Algolia Search Audit. Creates complete multi-touch outreach package: 5-email sequence, LinkedIn connection + follow-up messages, Loom video script, and collateral schedule. All personalized using audit findings, investor quotes, competitor evidence. Calls algolia-email, algolia-brief, algolia-social for brand-validated output. Output: abx-campaign/ folder.
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Overview

This skill generates a complete Account-Based Experience (ABX) outreach package for a prospect who has received an Algolia Search Audit. The package is fully personalized using live audit data: search gap findings, executive quotes from investor calls, competitor intelligence, and financial context. It produces 10 campaign files plus a collateral schedule.

---

## Path Convention

```bash
# At start of skill execution:
if [ -z "$ALGOLIA_AUDIT_DIR" ]; then
  AUDIT_DIR="$(pwd)"
  echo "⚠️ ALGOLIA_AUDIT_DIR not set — using current directory: $AUDIT_DIR"
else
  AUDIT_DIR="$ALGOLIA_AUDIT_DIR"
fi
```

Never hardcode the Google Drive path. Always use `$ALGOLIA_AUDIT_DIR`.

---

## Input

`$ARGUMENTS` — company slug (e.g., `costco`, `tapestry`, `therealreal`).

### STEP 0 — Re-read all source files before writing any campaign content

Read the following files in full before writing a single campaign file:

| File | Purpose |
|------|---------|
| `$AUDIT_DIR/{CompanyName}/deliverables/{slug}-playbook.md` | Talking points, MEDDPICC, objection handling (written by algolia-audit-report Phase 5d) |
| `$AUDIT_DIR/{CompanyName}/research/11-investor-intelligence.md` | Executive quotes for personalization |
| `$AUDIT_DIR/{CompanyName}/research/04-competitors.md` | Golden Angle evidence + competitor search providers |
| `$AUDIT_DIR/{CompanyName}/research/08-financial-profile.md` | Financial context for Email 3 |
| `$AUDIT_DIR/{CompanyName}/research/09-browser-findings.md` | Specific audit findings + screenshot file references |
| `$AUDIT_DIR/{CompanyName}/deliverables/screenshots/` | Screenshot inventory (list all .png files) |

If any of these files is missing, halt and alert the user. Do not proceed with incomplete source data.

---

## Output

All files written to:

```
$AUDIT_DIR/{CompanyName}/deliverables/abx-campaign/
├── email-1-hook.md
├── email-2-competitor.md
├── email-3-business-case.md
├── email-4-social-proof.md
├── email-5-breakup.md
├── linkedin-connect.md
├── linkedin-followup-1.md
├── linkedin-followup-2.md
├── loom-script.md
└── collateral-schedule.md
```

This writes to PRODUCTION: `{CompanyName}` — campaign files are additive, no existing audit data is overwritten.

---

## Signal Tier → Campaign Selection

Read `deliverables/{slug}-playbook.md` for the Signal Tier classification. Select the campaign type accordingly:

| Tier | Campaign | Initiator | Timing |
|------|----------|-----------|--------|
| Tier 1 (ACT NOW) | Full 5-email + LinkedIn + Loom | AE-led | Within 48 hours |
| Tier 2 (MONITOR) | 3-email + LinkedIn | BDR-led | 1-2 weeks |
| Tier 3 (WATCH) | Email 1 only + content nurture | Marketing | Monthly |

State the detected tier at the top of `collateral-schedule.md`.

---

## Email Sequence Specs

All emails must be written in plain Markdown. No HTML. No tables inside email body copy. Include:
- `Subject:` line
- `Body:` (full email text)
- `Source notes:` (citations for every claim — scratchpad file or URL)

---

### email-1-hook.md — HOOK (search gap finding)

**Structure (SCR):** Situation → Complication → Resolution

- **Situation:** {prospect's digital context — 1 line, use their language from the playbook or investor quotes}
- **Complication:** {specific finding from `09-browser-findings.md` — include the exact query tested and what actually happened}
- **Resolution:** {low-friction CTA — "worth a 15-min conversation?"}

**Subject:** Personalized — uses their product/category language. NOT generic "your search" or "search experience".

**Length:** 4-6 sentences max. No attachments referenced.

**Rules:**
- Use a SPECIFIC audit finding with the exact query tested. Never use a generic search problem.
- The complication must reference a screenshot file from `deliverables/screenshots/` that documents the finding.
- Source note must cite `09-browser-findings.md` line reference.

---

### email-2-competitor.md — COMPETITOR (Golden Angle or Defensive)

**Structure:** {Competitor} made this change → got this result → here's what that means for you

**Subject:** Include competitor name if confirmed. Do not fabricate.

**Two plays — choose based on `04-competitors.md`:**

**Golden Angle play** (use ONLY if detect-search confirmed a named competitor uses Algolia):
- Competitor name + what they changed
- The measurable result (cite source)
- The implication for the prospect

**Defensive play** (use if no Golden Angle confirmed):
- Industry leader doing X
- The risk to the prospect if they fall behind
- Algolia as the solution

**Rules:**
- NEVER speculate about competitor technology. Only cite what detect-search confirmed.
- If `04-competitors.md` shows no Golden Angle, use the Defensive play without mentioning Golden Angle.
- Source notes must identify which competitor and which detect-search network inspection confirmed the finding.

---

### email-3-business-case.md — BUSINESS CASE

**Structure:** Your revenue → the gap → the math

**Subject:** Revenue-specific, using their actual figures from `08-financial-profile.md`.

**Body:**
- Open with one financial figure (annual revenue or digital revenue) sourced from `08-financial-profile.md`
- Connect the audit gap to a revenue leakage estimate — show ONE formula component from the business case, not the full model
- Enough math to intrigue, not overwhelm (1-2 lines of calculation shown)
- CTA: offer to walk through the full model in 15 minutes

**Attach / reference:** Link to the published leave-behind HTML if it exists at `deliverables/{slug}-leave-behind.html`, or note "I can send the full business case model as a follow-up."

**Rules:**
- All financial figures must be sourced to Yahoo Finance, SEC, or the scratchpad file they came from.
- Show one calculation component, not the full ROI. The goal is to intrigue.
- Do not fabricate revenue figures. If `08-financial-profile.md` lacks specifics, use the available range.

---

### email-4-social-proof.md — SOCIAL PROOF

**Structure:** Company similar to yours → their gap → what Algolia did → result

**Subject:** Name the case study company — prospects recognize peers, not abstractions.

**Body:**
- Case study company (vertical-matched)
- Their search gap (analogous to the prospect's)
- What Algolia did (specific feature/capability, not generic)
- The measurable result

**Rules:**
- Only cite case studies where the URL has been WebFetch-verified in the audit. Use the `[FACT]` label.
- Prefer vertical-matched case studies. Check `deliverables/{slug}-playbook.md` for the ICP vertical.
- If no verified vertical-matched case study exists, use the closest match and note "adjacent vertical."
- Source note must include the case study URL and the scratchpad file that recorded it.

---

### email-5-breakup.md — BREAK-UP

**Structure:** Honest, human, leaves the door open.

**Subject:** Honest — not aggressive. Example: "Closing the loop on {Company}" not "Last chance."

**Body:**
- Acknowledge they've been busy (no guilt)
- Leave behind one resource as a parting gift (link to microsite or leave-behind)
- Signal that the door stays open

**Rules:**
- Never aggressive. The goal is to keep the relationship warm, not burn it.
- The parting resource must be a real file that exists in `deliverables/`.
- No "last chance" language. No urgency fabrication.

---

## LinkedIn Sequence

All LinkedIn messages written in plain text (no Markdown formatting — LinkedIn does not render it).
Include character count after each message. Hard limits enforced.

---

### linkedin-connect.md — Connection Request (300 characters max)

Template:
```
Hi [Name] — [one specific finding from the audit that relates to their role]. Thought you'd find it interesting. Happy to share the full analysis.
```

**Rules:**
- Specific to THEIR role — if they're VP of eCommerce, reference the revenue leakage finding; if they're CTO, reference the tech stack gap.
- Do not use generic "we do search" language.
- Must be under 300 characters. Count and confirm.
- Source note: which finding from `09-browser-findings.md` this references.

---

### linkedin-followup-1.md — Follow-up 1 (if accepted, no reply — 3-5 days after connect)

**Goal:** Build credibility. Share the specific finding. No ask.

**Structure:**
- Reference the finding mentioned in the connection request
- Add one more data point (screenshot description, metric, or investor quote)
- No CTA. Just signal.

**Rules:**
- No sales ask in Follow-up 1. Credibility building only.
- Under 300 characters recommended. Up to 500 acceptable.

---

### linkedin-followup-2.md — Follow-up 2 (1 week after Follow-up 1)

**Goal:** Move toward a meeting.

**Structure:**
- Competitor angle (from Email 2) OR business case component (from Email 3)
- Soft ask: "Would a 15-minute call make sense?"

**Rules:**
- One angle only — competitor OR business case, not both.
- Soft ask, not hard close. "Would it make sense" not "Book a time here."

---

## loom-script.md — Loom Video Script

**Format:** Timed sections. 2-minute max (120 seconds).

```
HOOK (0-10 sec):
"I spent 30 minutes on {company}.com and found three things that surprised me..."

DEMO (10-90 sec):
[Screenshot 1 — reference actual file from deliverables/screenshots/]
"When your [customer/member/user] clicks search, this is what they see..."
[Describe what the screenshot shows — exact query, exact result]

[Screenshot 2 — reference actual file from deliverables/screenshots/]
"This is what happens when they type naturally..."
[Describe the NLP or semantic failure]

[Screenshot 3 — reference actual file OR note if not available]
"Here's what [competitor] shows for the same search..."
[Competitor comparison if screenshot exists, otherwise skip to CTA]

"Three gaps. Here's what they mean for your $[X] digital business..."
[Pull revenue figure from 08-financial-profile.md]

CTA (90-120 sec):
"I put together a full analysis. Happy to walk you through it in 15 minutes.
[your name], [title], Algolia"
```

**Rules:**
- Every screenshot referenced MUST be an actual file in `deliverables/screenshots/`. No fictional filenames.
- Revenue figure must be sourced to `08-financial-profile.md`.
- Script must include speaker notes for transitions between screenshots.
- Total word count should be 200-280 words (comfortable 2-minute delivery at 120-140 wpm).

---

## collateral-schedule.md — Collateral Schedule

**Format:** Table + Signal Tier declaration at top.

```
Signal Tier: [Tier 1 / 2 / 3] — [ACT NOW / MONITOR / WATCH]
Campaign Type: [Full 5-email + LinkedIn + Loom / 3-email + LinkedIn / Email 1 only]
Initiator: [AE-led / BDR-led / Marketing]
Timing: [Within 48 hours / 1-2 weeks / Monthly]

| Touch | Channel | What to send | Why | Timing |
|-------|---------|-------------|-----|--------|
| Email 1 | Email | Hook email — no attachments | Keep it human, build curiosity | Day 1 |
| LinkedIn Connect | LinkedIn | linkedin-connect.md | Parallel track, executive access | Day 1-2 |
| Email 2 | Email | Competitor angle | Urgency without pressure | Day 3-4 |
| LinkedIn Follow-up 1 | LinkedIn | linkedin-followup-1.md (if accepted) | Share finding, no ask | Day 4-6 |
| Email 3 | Email | Business case + leave-behind link | Substantiate the revenue story | Day 7 |
| LinkedIn Follow-up 2 | LinkedIn | linkedin-followup-2.md | Soft meeting ask | Day 10-12 |
| Email 4 | Email | Social proof — case study | Peer validation | Day 14 |
| Loom | Email/LinkedIn | loom-script.md (recorded by AE) | Personal, visual, differentiated | Day 7 or Day 14 |
| Meeting | Live | {slug}/index.html SPA | Full audit walkthrough | TBD |
| Email 5 | Email | Break-up email + parting resource | Keep relationship warm | Day 21 |
| Post-meeting follow-up | Email | {slug}-business-case.md | Leave them with the math | Within 24h of meeting |
```

Notes section: List any files that could not be created due to missing source data, with the specific missing file referenced.

---

## Calling Sub-Skills

After writing all 10 campaign files, call brand validation:

```
Use the Skill tool: skill="algolia-brand-check", args="{path to abx-campaign folder}"
Wait for the skill to complete.
```

If `algolia-brand-check` is not installed, note in the output: "Brand check skipped — algolia-brand-check skill not found. Manual review recommended before sending to AE."

---

## Update audit-data.json abx_sequence (MANDATORY after writing files)

After writing all 10 campaign files, populate `deliverables/{slug}-audit-data.json`'s
`abx_sequence.touches[]` with the **full content** of each touch. The SPA renders directly
from this JSON; the markdown files are NOT read by the SPA. If `body` is empty, the SPA shows
a blank or one-line summary.

**Do NOT hand-assemble this JSON.** Assembling it by hand is the failure class that leaks
Source notes into sendable copy, drops `video_script` (blanking the Loom panel), and mislabels
channel fields. A deterministic patcher does it correctly every time:

```bash
# Mirror of generate-audit-data.py — extracts sendable copy from the campaign .md files
# and writes schema-valid abx_sequence.touches[] (no Source notes, correct per-channel fields).
SCRIPTS="$HOME/.claude/skills/algolia-search-audit/scripts"   # adjust if running from repo
python3 "$SCRIPTS/generate-abx-json.py" {slug} "$AUDIT_DIR/{CompanyName}"
```

What the script guarantees (so you don't have to verify it by hand):
- **Email touches:** `body` = the text between `**Body:**` and `**Source notes:**` only. Source
  notes never reach the body (stripped even if the `**Body:**` delimiter is missing).
- **LinkedIn touches:** `body` = the first `**Message...:**` block, plain text, with `Character count`,
  `Target`, and other metadata headers removed.
- **Video (Loom) touch:** the timed script goes to `video_script` (the field the SPA template reads);
  `body` holds the SHORT delivery email, NOT the script. (Hand-built JSON routinely got this wrong —
  putting the script in `body` and leaving `video_script` empty, which blanks the Loom panel per
  `template_contract.py`.)
- **Contacts:** every contact gets a snake_case `id` for the SPA contactMap lookup.
- **Schema floors:** warns loudly if any copy is too short, contains a placeholder (`TBD`,
  `Pending —`, …), or leaked Source notes. The output validates against `audit_data_schema.ABXSequence`.

The script exits non-zero if fewer than 3 touches could be extracted (campaign incomplete). Review
any warnings it prints before sending — they flag real copy problems, not script failures.

**Email-3 financials traceability:** the revenue figure and the single ROI formula shown in
`email-3-business-case.md` must come from the deterministic calculator, not in-LLM arithmetic. Before
writing Email 3, run `calculate-roi.py` and quote ONE of its component figures:

```bash
python3 "$SCRIPTS/calculate-roi.py" "$AUDIT_DIR/{CompanyName}/research" | python3 -m json.tool
# Use a single component figure from this JSON in Email 3. Do NOT re-multiply by hand.
# Cite it in Source notes as: "{slug}-business-case.md / calculate-roi.py — Component N: <figure>".
```

---

## Verification Gate

After writing all files AND updating the JSON:

```bash
# Verify all 10 files exist and are non-trivial
ls "$AUDIT_DIR/{CompanyName}/deliverables/abx-campaign/"
```

Pass conditions:
- Exactly 10 files present (email-1 through email-5, linkedin-connect, linkedin-followup-1, linkedin-followup-2, loom-script, collateral-schedule)
- Each file ≥ 200 bytes
- `loom-script.md` references at least 2 actual screenshot filenames from `deliverables/screenshots/`
- `collateral-schedule.md` contains Signal Tier declaration
- Every email file contains a `Source notes:` section with at least one citation
- `{slug}-audit-data.json` `abx_sequence.touches[]` has `body` field populated (not empty)
- `generate-abx-json.py` exited 0 (>=3 touches) and printed no warnings — or you reviewed each warning
- The video touch has a non-empty `video_script` (the script panel) AND a short `body` (delivery email)

If any check fails: halt and report which file and which condition failed. Do not silently deliver incomplete output.

---

## Quality Rules — Non-Negotiable

| Rule | Detail |
|------|--------|
| Specificity mandate | Every email must reference a specific audit finding (query + result), not a generic search problem |
| Source citation mandate | Every factual claim across all 10 files must cite its scratchpad file or external URL |
| Screenshot existence check | Every screenshot referenced in the Loom script must exist in `deliverables/screenshots/` before being named |
| No fabricated competitors | Golden Angle only used when detect-search confirmed. Defensive play used otherwise. |
| No fabricated financials | Only figures sourced from `08-financial-profile.md`, Yahoo Finance, or SEC |
| No fabricated case studies | Only verified case studies with WebFetch-confirmed URLs |
| LinkedIn character limits | Connection request ≤ 300 chars. Character count included in file. |
| Loom word count | 200-280 words for 2-minute delivery |
| Signal Tier compliance | Campaign scope matches the tier from `deliverables/{slug}-playbook.md` |
| No HTML in campaign files | All 10 output files are plain Markdown |

---

## Error Handling

| Condition | Action |
|-----------|--------|
| `deliverables/{slug}-playbook.md` missing | Halt. Alert user. Cannot determine Signal Tier or talking points without playbook. |
| `09-browser-findings.md` missing | Halt. Cannot write personalized emails without browser audit findings. |
| `11-investor-intelligence.md` missing | Proceed, but note all executive quotes are unavailable. Use company narrative from `01-company-context.md` instead. |
| `04-competitors.md` missing | Proceed with Defensive play in Email 2. Note Golden Angle could not be verified. |
| `08-financial-profile.md` missing | Proceed without revenue figures in Email 3. Flag missing financial context in collateral-schedule.md notes. |
| No screenshots in `deliverables/screenshots/` | Write Loom script without screenshot references. Flag in verification gate output. |
| Brand check skill not found | Continue. Note manual brand review needed. |
