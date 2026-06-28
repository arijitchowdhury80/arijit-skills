---
name: algolia-synth-sales-plays
description: Use to generate AE/BDR sales playbooks for specific Algolia prospects. Invoke when the user wants to: build a playbook (AE playbook, BDR playbook, sales playbook), run synth-sales-plays or the sales plays generator, create pre-call talking points grounded in the prospect's own exec language from earnings calls, map MEDDPICC gaps, write SPIN-structured discovery Q&A trees, draft objection handling scripts, or prepare personalized cold outreach angles for a named company. All sections are grounded in audit research files and executive quotes — not templates. Output: {company}-playbook.md with BLUF header, top 5 talking points, discovery questions, MEDDPICC table, objection responses, and power map.
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Input
$ARGUMENTS — company slug.

Reads ALL of:
- `$AUDIT_DIR/{Company}/research/11-investor-intelligence.md` (exec language — quotes to mirror)
- `$AUDIT_DIR/{Company}/research/10-scoring-matrix.md` (what gaps exist — what to pitch)
- `$AUDIT_DIR/{Company}/research/04-competitors.md` (Golden Angle evidence)
- `$AUDIT_DIR/{Company}/research/09d-hiring-signals.md` (buying committee)
- `$AUDIT_DIR/{Company}/research/08-financial-profile.md` (financial context)
- `$AUDIT_DIR/{Company}/deliverables/{slug}-business-case.md` (if exists — ROI inputs)

## Output
`$AUDIT_DIR/{Company}/deliverables/{slug}-playbook.md`

## Path
```bash
if [ -z "$ALGOLIA_AUDIT_DIR" ]; then
  AUDIT_DIR="$(pwd)"
  echo "WARNING: ALGOLIA_AUDIT_DIR not set — using current directory: $AUDIT_DIR"
else
  AUDIT_DIR="$ALGOLIA_AUDIT_DIR"
fi
```

---

## STEP 0 — Read ALL input files BEFORE writing anything.

Context compaction corrupts data. Re-read all input files listed above before generating any section. If a file does not exist, note "NOT FOUND" and proceed with available data — do not skip sections.

Workspace declaration: "This writes to PRODUCTION: [{Company}] — generating playbook deliverable from verified research files."

---

## Playbook Structure

### BLUF HEADER (30-second pre-call read)
```
BOTTOM LINE: [Company] is [signal tier: HOT/WARM/COLD]. Lead with [specific angle].
Top angle: [Challenger insight in 1 sentence — what they don't know about their own search]
Key exec: [Name, Title] — contact via [route: see Partner Play below if available, else LinkedIn]
Partner Play: [If partner-intel.md exists and has HIGH-confidence SI partner: "Warm intro via [SI name] — [activation_strategy in 1 line]". Else: "No confirmed partner relationship — cold outbound with audit finding as hook"]
Signal: [Most urgent trigger signal with date — earnings call quote, hiring surge, replatform, etc.]
```

---

### SECTION 1: Top 5 Talking Points

Each talking point uses this structure — all personalized with the prospect's own language from earnings calls:

```
TALKING POINT #N: {Hook using prospect's own language from earnings calls}

WHY IT LANDS:
- What we found: {specific browser audit finding — exact query tested + exact result observed}
- Their words: "{verbatim exec quote}" — {Speaker}, {Title}, {Source: earnings call / 10-K / investor day}, {Date}
- Competitor proof: {named competitor} uses Algolia → {specific metric or outcome if available}

OPEN WITH (exact line):
"{The sentence an AE says to start the conversation — word-for-word}"

EXPECTED REACTION: {How a typical prospect in this situation responds — engaged / skeptical / curious}
```

Sourcing rule: Every talking point MUST cite an exec quote from `11-investor-intelligence.md`. If a talking point cannot be grounded in an exec quote, do not include it.

---

### SECTION 2: Discovery Questions (SPIN-structured)

Skip Situation questions we can already answer from the audit — use that knowledge to demonstrate credibility. Lead with Implication and Need-Payoff questions.

For each question:
```
QUESTION: "{Exact question, using their terminology from earnings calls — not generic 'search' language}"
Source of language: {where this phrasing came from — e.g., CFO Q3 2024 earnings call, job posting, 10-K}

IF THEY SAY [engaged / confirms the problem]:
  Follow-up: "{deeper diagnostic question}"
  Evidence: "We tested [exact query] and found [exact result] — does that match your experience?"

IF THEY SAY [skeptical / 'we don't have that problem']:
  Reframe: "{competitor evidence or specific audit finding that contradicts their assumption}"

IF THEY SAY [deflect / unaware]:
  Educate: "{specific data point — a number, a query result, an industry benchmark — that makes it real}"

QUALIFICATION SIGNAL: {what this answer reveals about deal readiness — budget, timeline, pain ownership}
```

Minimum 6 questions across: Implication (3), Need-Payoff (2), Problem confirmation (1).

---

### SECTION 3: MEDDPICC Gap Map

```
| Component | Status | Evidence | AE Action |
|-----------|--------|----------|-----------|
| Metrics (M) | [POPULATED / PARTIAL / UNKNOWN] | ROI: $[X]M from {slug}-business-case.md or estimated from audit scoring | — |
| Economic Buyer (E) | [POPULATED / PARTIAL / UNKNOWN] | [Name, Title from 09d-hiring-signals.md or 01-company-context.md] | — |
| Decision Criteria (D) | [POPULATED / PARTIAL / UNKNOWN] | [From tech stack + competitor intel — what they optimize for] | — |
| Decision Process (D) | [UNKNOWN] | — | Ask in discovery: "Walk me through how a decision like this typically moves forward at [Company]." |
| Paper Process (P) | [UNKNOWN] | — | Ask: "What does your procurement cycle look like for a platform investment?" |
| Implication of Pain (I) | [POPULATED] | Audit findings: [top 3 gaps by severity from 10-scoring-matrix.md] | Lead with this in every conversation |
| Champion (C) | [PARTIAL / UNKNOWN] | [From 09d-hiring-signals.md buying committee — most search-adjacent role] | Identify in first call — look for VP Search / Director of eComm / Head of Product |
| Competition (C) | [POPULATED] | [From 04-competitors.md — current vendor + Golden Angle status] | [Golden Angle: lead with competitor proof] or [Defensive: protect against displacement] |
```

---

### SECTION 4: Objection Handling

Anticipated objections are derived from: exec statements in earnings calls, financial profile constraints, current vendor relationships, and competitive scenario from `04-competitors.md`.

```
OBJECTION: "{Exact words they're likely to say — in their voice}"
Signal: {which audit finding or financial context predicts this objection}

RESPONSE: "{Specific, confident, evidence-backed response — reference the actual browser finding or exec quote}"

PIVOT: "{How to move from the objection back to the opportunity — redirect to their stated priority}"

FALLBACK: "{One more layer of proof if they push back again — a case study, a metric, a competitor proof point}"
```

Required objections (minimum 4):
1. "We built it in-house" — address with: what in-house cannot do (NLP, real-time relevance tuning, federated), and what it costs to maintain vs. Algolia
2. "Too expensive / budget isn't there" — address with: ROI from business-case.md, cost of current failure state (lost revenue from zero results, bounce)
3. "We're locked in with [current vendor]" — address with: Golden Angle competitor evidence, migration paths, and specific gap the current vendor cannot close
4. "Not a priority right now" — address with: most urgent trigger signal (hiring surge, replatform, exec quote about digital investment), and consequence of delay

Add additional objections based on exec language from `11-investor-intelligence.md` and financial profile from `08-financial-profile.md`.

---

### SECTION 5: Power Map

```
| Name | Title | Role in Deal | Relationship | Approach |
|------|-------|-------------|-------------|----------|
```

Sources: `09d-hiring-signals.md` (buying committee), `research/01-company-context.md` (C-suite executives).

Tier designations:
- **Tier 1 Champion**: Economic buyer — most senior exec with search/digital/revenue ownership. Approach first.
- **Technical Buyer**: Engineer or architect owning search infrastructure. Engage after champion is warmed.
- **Coach/Internal Advocate**: Director-level, closest to the pain. May surface independently from hiring signals.
- **Blocker**: Incumbent vendor relationship owner. Identify early, do not cold-approach.

Approach column: LinkedIn connection + content engagement / warm intro via [partner or mutual] / cold outbound with audit finding as hook.

---

### SECTION 6: Partner Angles

PRIORITY ORDER:
1. HIGH-confidence SI partner (Crossbeam-confirmed) → warm intro is ALWAYS first play, listed before any cold outreach
2. Algolia tech partner co-sell (SFCC, Adobe, etc.) → joint solution pitch
3. Competitor-based (Golden Angle) → "Your competitors chose Algolia"
4. Cold outbound with audit finding as hook → last resort only

If a HIGH-confidence SI partner exists in `partner-intel.md`, this MUST be listed as the #1 recommended
action in the BLUF, overriding any other approach. An AE who cold outbounds when a warm intro is
available is leaving significant deal velocity on the table.

Sources: `research/partner-intel.md` if exists; otherwise infer from `03-tech-stack.md` and `04-competitors.md`.

```
Tech partner: [partner name] — co-sell angle: [what joint story to tell]
SI partner: [partner name] — warm intro route: [how to activate the relationship]
GSI angle: [if enterprise deal — which GSI touches this account]
```

If `partner-intel.md` does not exist, note "No partner intel file found — infer from tech stack" and extract relevant partner relationships from `03-tech-stack.md`.

---

## Personalization Principle

EVERYTHING in this playbook uses the prospect's own language:
- Talking points reference their exact earnings call quotes — not paraphrased, verbatim
- Discovery questions use their terminology as it appears in transcripts, job postings, or public statements
- Objection responses reference their specific financial constraints or strategic commitments
- The MEDDPICC map is populated from their actual research files — no generic placeholders

This is what makes it a PLAYBOOK, not a template. A playbook without exec quotes is a template. Do not ship a template.

---

## Verification Gate

After writing the playbook, verify all of the following before declaring complete:

1. File size: `wc -c $AUDIT_DIR/{Company}/deliverables/{slug}-playbook.md` — must be ≥ 6000 bytes
2. All 6 sections present: BLUF, Talking Points, Discovery, MEDDPICC, Objections, Power Map
3. Exec quote sourcing: at least 3 talking points cite a verbatim quote with Speaker + Title + Source + Date
4. MEDDPICC table complete: all 8 rows present, no empty cells in Status or AE Action columns
5. Objection count: at least 4 objections handled with Response + Pivot + Fallback
6. No generic language: grep for "your company", "the prospect", "insert name" — if found, replace with actual names

7. **Claim traceability (mechanical — run the checker, don't self-attest):** every talking point
   must reference a real audit finding (`What we found:`) AND a verbatim exec quote (`Their words:`).
   A talking point with neither is an ungrounded claim and violates the Section 1 sourcing rule.

```bash
SCRIPTS="$HOME/.claude/skills/algolia-search-audit/scripts"   # adjust if running from repo
python3 "$SCRIPTS/check-claim-traceability.py" playbook \
  "$AUDIT_DIR/{Company}/deliverables/{slug}-playbook.md"
# Exit 0 = every talking point traces to a finding + quote. Exit 1 = ungrounded talking points listed.
```

This checks structure mechanically; it does NOT rewrite prose. If it reports a FAIL, add the missing
`What we found:` / `Their words:` line to that talking point (or remove the talking point) — do not
report completion while any talking point is ungrounded.

If any gate fails: fix before reporting complete. Do not report completion with a failing gate.
