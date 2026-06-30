# Algolia Search Audit Skills

A suite of Claude skills that produces a full **Algolia search audit** for a prospect company —
from raw web research through browser testing, scoring, and sales activation deliverables.

These skills are the execution engine behind **PRISM** — a [Hermes](https://github.com/) agent
instance running on a VPS. PRISM orchestrates this suite via the claude-cli executor and answers
questions grounded **only** in the resulting audit report. PRISM is becoming the *executioner*: it
runs the pipeline end-to-end, not just chats over the output.

**Suite version: `2.0.0` (Gemini-grounded release).** Per-skill versions live in each `SKILL.md`
frontmatter; `algolia-intel-hiring` is ahead at `3.0.0` (full source redesign). `algolia-intel-techstack`
was rebuilt on keyless `detect-search --full-tech` multi-page fingerprinting (BuiltWith fully retired).

---

## Data-source architecture (v2.0.0)

The defining change in this release: **the right tool for each job**, and no fabrication — a field
with no grounded source stays blank.

Sources are **not uniform** across skills — each module's collector script is the source of truth.
The table below is the suite-wide map; per-skill READMEs give the exact source each module uses.

| Source | Role | Used for |
|--------|------|----------|
| **Scout** (`localhost:8421`) | Acquire the **target's own** data | Executive team, careers/jobs page, investor relations, PDF decks; field-level enrichment of the company profile. JS-rendered + stealth + PDF extraction. |
| **Gemini-grounded Google search** (`scripts/gemini_search.py`) | **Open-web** research | Industry benchmarks (`collect-industry.py`), exec-media quotes (`collect-exec-media.py`), private-company estimates. Returns `{answer, citations, queries, grounded}`; ungrounded → empty. |
| **detect-search** | Search-vendor / platform detection | Network packet inspection (`map-detect-search.py`) — live search stack + ecommerce platform; competitor search tech. |
| **SimilarWeb REST API** (`SIMILARWEB_API_KEY`) + **browser session** | Traffic + competitor discovery | Direct HTTPS calls (`collect-traffic.py`, v1/v4 endpoints); competitor discovery runs a browser subprocess (`collect-similarweb-browser.js`). **Not an MCP.** |
| **yfinance library** (`collect-financials.py`) | Public-company financials | 3-year revenue, EBITDA margin, analyst consensus. Python lib, not an MCP. |
| **Yahoo Finance MCP** | Investor news feed | `get_yahoo_finance_news` via the `algolia-intel-investor` orchestrator. |
| **Apify** (`APIFY_TOKEN`) | Live social + news signals | LinkedIn posts + Twitter/X (`collect-social.py`); Google News in the research live-signals step. REST API, not an MCP. |
| **Tavily** (`TAVILY_API_KEY`) + **Google News RSS** | Company news | `algolia-intel-news` primary = Tavily news search; keyless Google News RSS is the fallback. |
| **WebFetch** | Direct known-URL fetch | Earnings-call / interview transcripts, SEC EDGAR, company LinkedIn. |

**Retired:** ~~BuiltWith~~ (→ detect-search + SimilarWeb), ~~WebSearch~~ (→ Gemini-grounded Google
search). **Tavily** was intended to be retired but is still the primary source in `algolia-intel-news`
(`collect-news.py`) — a known migration gap, not yet reconciled.

---

## Pipeline

```
algolia-search-audit  ── full-pipeline orchestrator (entry point)
│
├─ Phase 1 · Research        algolia-audit-research  (kicks off Wave 1)
│   └─ Wave 1 intel modules (read 01-company-context first):
│      algolia-intel-company    (1A · run first, all downstream read it)
│      algolia-intel-techstack   (1B · search vendor / full tech stack)
│      algolia-intel-traffic     (1C · SimilarWeb traffic)
│      algolia-intel-competitors (1D · competitor search tech)
│      algolia-intel-financial-public / -private (1E/1F · revenue)
│      algolia-intel-investor    (1G · exec quotes, 10-K, news)
│      algolia-intel-hiring       (1H · Scout careers + Gemini job boards)
│      algolia-intel-social       (1I · LinkedIn/X via Apify)
│      algolia-intel-news         (1J · Google News + RSS)
│      algolia-intel-partner      (partner / co-sell mapping)
│      algolia-intel-industry     (vertical benchmarks)
│      algolia-intel-queries      (test-query set for browser phase)
│
├─ Phase 2 · Browser         algolia-audit-browser   (live search testing; needs Phase 1)
│
├─ Phase 3 · Report          algolia-audit-report    (deck + landing + PDF + playbook)
│                            algolia-audit-factcheck (gate: PROCEED / WARN / BLOCKED)
│                            algolia-audit-eval      (score vs 5 quality dimensions)
│
└─ Phase 4 · Activation      algolia-synth-business-case (ROI model)
                             algolia-synth-sales-plays   (AE/BDR playbook)
                             algolia-campaign-abx        (5-email + LinkedIn + Loom)
```

Run phases in order. Do not run Phase 3 without Phase 2 browser screenshots.

---

## Skills

Each skill has its own `README.md` with inputs, outputs, data sources, and how PRISM invokes it.

### Orchestration
- **algolia-search-audit** — full-pipeline orchestrator and entry point.
- **algolia-audit-research** — Phase 1 research orchestrator; runs all Wave 1 intel modules.

### Wave 1 intel modules
- **algolia-intel-company** — company context, vertical, execs, key URLs (run first).
- **algolia-intel-techstack** — full tech stack + search vendor via keyless `detect-search --full-tech` (multi-page network fingerprint); optional SimilarWeb REST cross-check.
- **algolia-intel-traffic** — full SimilarWeb traffic profile.
- **algolia-intel-competitors** — competitor set + each one's search tech (Golden Angle: any on Algolia).
- **algolia-intel-financial-public** — public-company financials (Yahoo Finance).
- **algolia-intel-financial-private** — private-company revenue estimate (6-source waterfall).
- **algolia-intel-investor** — verbatim exec quotes, 10-K MD&A, news feed.
- **algolia-intel-hiring** — ICP roles via Scout (own careers page) + Gemini (third-party boards). No Apify/LinkedIn.
- **algolia-intel-social** — LinkedIn + Twitter/X strategic signals (Apify).
- **algolia-intel-news** — Google News + RSS, last 60 days (Apify).
- **algolia-intel-partner** — tech-partner + SI/consulting overlap (Crossbeam).
- **algolia-intel-industry** — vertical benchmarks + analyst quotes (Gemini-grounded).
- **algolia-intel-queries** — builds the browser-test query set.

### Phase 2–4
- **algolia-audit-browser** — live browser search testing (Playwright stealth vs WAF).
- **algolia-audit-report** — McKinsey deck, dual-view landing page, PDF book, AE playbook.
- **algolia-audit-factcheck** — cross-file quality gate before sharing.
- **algolia-audit-eval** — scores module/output across 5 quality dimensions.
- **algolia-synth-business-case** — 6-component search ROI model.
- **algolia-synth-sales-plays** — grounded AE/BDR playbook (MEDDPICC, SPIN, objections).
- **algolia-campaign-abx** — multi-touch ABX outreach package.

`scout` (in this directory) is the shared web-intelligence platform the intel modules call; see its
own README.

---

## Platform rules

`algolia-search-audit/AGENT-CONTEXT.md` defines the platform contract every skill obeys — JSON field
names, CSS classes, design tokens, function names, the `$ALGOLIA_AUDIT_DIR` path convention, and the
sub-skill invocation pattern. Read it before modifying any skill.

## Conventions

- Outputs land under `$ALGOLIA_AUDIT_DIR/{CompanyName}/research/`; intel modules emit a paired
  `NN-name.md` + `NN-name.json`.
- **Evidence on every data point.** Citations required; ungrounded → blank, never fabricated.
- Research **aborts** if the prospect is already on Algolia (`algolia_detected=true`).
