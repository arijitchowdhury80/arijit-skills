---
name: algolia-intel-partner
description: Use when the user asks to run partner intelligence, partner discovery, or find co-sell/ecosystem partners for an Algolia audit prospect. Triggers when: mapping which platforms in Algolia's tech partner network a prospect uses (Adobe, Salesforce, Shopify, SAP, commercetools), identifying SI or consulting firms with existing C-suite relationships at the target company (Accenture, EPAM, Deloitte Digital, Publicis Sapient, Slalom, etc.), querying Crossbeam for account overlap, or generating a missing partner-intel.md audit file. Use for any Algolia Search Audit prospect where you need to map the partner landscape for co-sell or relationship-based sales motions.
---

## MANDATORY FIRST ACTION
Read `~/.claude/skills/algolia-search-audit/AGENT-CONTEXT.md`

---

## Input
$ARGUMENTS — company slug. Reads: $ALGOLIA_AUDIT_DIR/{CompanyName}/research/02-tech-stack.md

## Output
$ALGOLIA_AUDIT_DIR/{CompanyName}/research/partner-intel.md

## Path
```bash
# At start of skill execution:
if [ -z "$ALGOLIA_AUDIT_DIR" ]; then
  AUDIT_DIR="$(pwd)"
  echo "WARNING: ALGOLIA_AUDIT_DIR not set — using current directory: $AUDIT_DIR"
else
  AUDIT_DIR="$ALGOLIA_AUDIT_DIR"
fi
```

---

## The Two Partner Types

### Tech Partners (co-sell motion)
Companies whose technology the prospect uses where Algolia has a co-sell/referral partnership.

Algolia tech partner examples:
- Adobe Experience Manager / Adobe Commerce (Magento)
- Salesforce Commerce Cloud
- Shopify Plus
- SAP Commerce Cloud
- commercetools
- BigCommerce
- HCL Commerce
- Contentful
- Contentstack
- Amplience
- Bloomreach (CMS/DXP)
- Akeneo (PIM)
- Bazaarvoice
- Stripe (checkout/payments context)

Detect via:
1. Crossbeam MCP — account overlap data
2. `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/02-tech-stack.md` — what was already detected in their stack

Sales motion: "You already use [Partner] — we have a co-sell agreement. Let me introduce you to our joint solution team."

---

### SI / Implementation Partners (relationship/influencer motion)
Systems integrators and consulting firms with existing C-suite relationships at the prospect. These know the CTO/CDO/VP Digital by name. They are deal INFLUENCERS and ACCELERATORS.

SI/agency partners are discovered DYNAMICALLY via Crossbeam MCP — never from a fixed list.
Do NOT iterate through a predetermined list of SI names. Crossbeam tells you which ones actually have overlap at this account.

**Why dynamic matters:** Algolia's SI partner ecosystem includes dozens of firms — Slalom, Grid Dynamics, Intellias, EPAM, Publicis Sapient, Deloitte Digital, Accenture, IBM iX, Merkle, Capgemini, ThoughtWorks, Perficient, Valtech, and many more. The relevant one for THIS deal is whichever firm Crossbeam shows has an existing relationship at THIS account. That changes per prospect.

Detect via:
1. Crossbeam MCP — pull ALL SI partners with overlap at this account (primary source)
2. WebSearch: "[company] implementation partner" — broad search, not SI-name-specific
3. WebSearch: "[company] digital transformation partner 2024 2025"
4. WebSearch: "[company] [technology] implementation" — using tech stack as the bridge (e.g., "[company] Salesforce Commerce Cloud implementation partner")
5. "[company] annual report" — sometimes lists strategic implementation partners by name

Sales motion (fill in from Crossbeam result): "[SI partner from Crossbeam] already has a relationship at [Company] — engage them to co-sell and get a warm introduction to the decision-maker."

---

## Execution Steps

### Step 1: Read tech stack (required input)
Read `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/02-tech-stack.md`.
Extract: all detected platforms, CMS/DXP, commerce engine, CDN/WAF, analytics, personalization, search provider.
Cross-reference against Algolia tech partner list above — identify which detected platforms have Algolia co-sell agreements.

### Step 2: Crossbeam MCP — tech partner overlap
Query Crossbeam for account overlap data on the prospect domain.
Capture: which Algolia tech partners show account overlap.
Label all data: [FACT — Crossbeam MCP, {date}]

If Crossbeam MCP is unavailable or returns no data: note "No Crossbeam data available — relying on tech stack + WebSearch" and proceed.

### Step 3: Crossbeam MCP — SI partner overlap
Query Crossbeam for SI/implementation partner overlap on the prospect domain.
Capture: which SI/agency partners show account overlap.
Label all data: [FACT — Crossbeam MCP, {date}]

### Step 4: WebSearch — SI partner relationships
Run the following searches (all required, not optional):
1. `"{company}" EPAM OR "Publicis Sapient" implementation OR "digital transformation"`
2. `"{company}" Deloitte OR Accenture OR IBM implementation OR consulting`
3. `"{company}" Merkle OR Perficient OR Valtech OR Capgemini digital`
4. `"{company}" Adobe OR Salesforce implementation partner agency`

For each search result that shows evidence of an SI relationship:
- Record: SI name, evidence summary, source URL, recency of article/announcement
- Label: [WEBSEARCH — {source URL}, {date}]

### Step 5: WebSearch — tech partner confirmation
If a tech partner was detected in the stack but not confirmed via Crossbeam, run:
`"{company}" {partner name} implementation OR integration OR "powered by"`
Record confirmation evidence with source URL.

### Step 6: Write partner-intel.md
Write the full output file to: `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/partner-intel.md`
Use the exact output format specified below.

### Step 7: Verification gate
After writing, run:
```bash
ls -la "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/partner-intel.md"
```
Pass condition: file exists AND size ≥ 2000 bytes.
If file is missing or under 2000 bytes: STOP and alert user. Do not proceed.

---

## Output Format

```markdown
# Partner Intelligence — {Company}
*Generated: {date} | Sources: Crossbeam MCP + tech-stack analysis + WebSearch*

---

## SECTION A: Tech Partners (Co-Sell Motions)

### A1. Confirmed in Stack
Partners detected in 02-tech-stack.md that have Algolia co-sell/referral agreements.

| Partner Tech | Version/SKU | Algolia Partnership Type | Co-Sell Angle | Source |
|---|---|---|---|---|
| [platform] | [version if known] | [co-sell / referral / joint-GTM] | [specific joint-solution pitch] | [FACT — source, date] |

*If none detected: "No Algolia tech partners detected in current stack."*

### A2. Crossbeam Overlap
Partners showing account overlap in Crossbeam for this prospect.

| Partner | Overlap Type | Account Match | Source |
|---|---|---|---|
| [partner] | [Customer / Prospect / Partner] | [match confidence] | [FACT — Crossbeam MCP, date] |

*If Crossbeam unavailable: "Crossbeam data unavailable — relying on tech stack analysis and WebSearch."*

### A3. Not in Stack (Future Opportunity)
Algolia tech partners NOT currently detected — relevant if prospect migrates or adds this platform.

| Partner Tech | Why Relevant | Co-Sell Angle |
|---|---|---|
| [platform] | [why this prospect might adopt it] | [future pitch] |

---

## SECTION B: SI / Implementation Partners (Relationship Access)

### B1. High-Confidence SI Relationships
Confirmed via Crossbeam MCP data or corroborated WebSearch evidence (≥1 source URL).

| SI Partner | Evidence | Likely C-Suite Access | Sales Action | Source |
|---|---|---|---|---|
| [firm] | [what evidence: press release, case study, RFP award, etc.] | [CTO / CDO / VP Digital / CMO] | [specific action: "Request warm intro via EPAM account team"] | [WEBFETCH/WEBSEARCH — URL, date] |

*If none found: "No high-confidence SI relationships identified via available sources."*

### B2. Potential SI Partners (Investigate)
SIs worth investigating — no confirmed evidence but high likelihood based on company size, vertical, or tech stack.

| SI Partner | Why Likely | How to Confirm |
|---|---|---|
| [firm] | [reason: company size / vertical / shared Adobe relationship / geography] | [action: "Check Crossbeam → ask AE → search LinkedIn for [firm] employees at [company]"] |

---

## SECTION C: Sales Action Plan

### Immediate (within 1 week)
[Single highest-confidence action using the strongest partner signal found above. Be specific: name the partner, name the Algolia contact who owns that relationship, and name the ask.]

Example format:
> **Action**: Contact [Algolia Partner Manager name] at Algolia's [Adobe/Salesforce/etc.] partner team. Prospect uses [platform] and has a live co-sell agreement. Request joint intro call to [company] [title].

### Secondary (within 1 month)
[1-3 supporting partner actions, in priority order]

1. [action with SI partner: who to contact, what to ask]
2. [action with second tech partner or second SI]
3. [outreach to confirm potential SI relationship]

---

## SECTION D: Data Quality Notes
[Note any gaps: Crossbeam unavailable, no WebSearch evidence found for specific SIs, tech-stack data incomplete, etc.]

---

## Sources
| # | URL | Type | Date | Used In |
|---|---|---|---|---|
| 1 | [URL] | [Crossbeam / WebSearch / WebFetch / BuiltWith] | [date] | [Section A/B/C] |
```

---

## Label Reference
All data in partner-intel.md MUST carry one of these labels:
- `[FACT — Crossbeam MCP, {date}]` — direct Crossbeam account overlap data
- `[FACT — 02-tech-stack.md, {date}]` — derived from tech stack scratchpad
- `[WEBSEARCH — {source URL}, {date}]` — found via WebSearch, not yet fetched
- `[WEBFETCH — {source URL}, {date}]` — primary source URL fetched and verified
- `[ESTIMATE]` — inferred/logical conclusion, no direct evidence (use sparingly, must explain basis)

Do NOT write any claim without a label. An unlabeled data point is an unverified data point.

---

## Verification Gate

After writing partner-intel.md, confirm:

```bash
ls -la "$ALGOLIA_AUDIT_DIR/{CompanyName}/research/partner-intel.md"
```

Pass conditions:
1. File exists at expected path
2. File size ≥ 2000 bytes
3. SECTION A is present (search for "Tech Partners")
4. SECTION B is present (search for "SI / Implementation Partners")
5. Sources section is present with at least 1 URL

If any condition fails: STOP. Do not report completion. Alert user with specific failure reason.
