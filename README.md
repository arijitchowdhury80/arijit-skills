# Algolia Claude Skills

A suite of Claude Code skills for Algolia Account Executives and Sales Engineers. Automates search audits, sales intelligence, content generation, and prospect research.

---

## Quick Install

```bash
git clone https://github.com/arijitchowdhury80/algolia-claude-skills.git
cd algolia-claude-skills
chmod +x install.sh && ./install.sh
```

---

## Required MCP Servers & API Keys

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "apify": {
      "command": "npx",
      "args": ["@apify/actors-mcp-server"],
      "env": { "APIFY_TOKEN": "YOUR_APIFY_TOKEN" }
    },
    "chrome": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp"]
    },
    "similarweb-mcp": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://mcp.similarweb.com/",
               "--header", "api-key: YOUR_SIMILARWEB_KEY"]
    },
    "builtwith": {
      "command": "node",
      "args": ["PATH_TO/bw-mcp-v1.js"],
      "env": { "BUILTWITH_API_KEY": "YOUR_BUILTWITH_KEY" }
    },
    "yahoo-finance-mcp": {
      "command": "uv",
      "args": ["--directory", "PATH_TO/yahoo-finance-mcp", "run", "python", "server.py"]
    }
  }
}
```

| Service | Used For | Get Key |
|---------|---------|---------|
| **Apify** | LinkedIn Jobs, Twitter/X, Google News scraping | [apify.com](https://apify.com) → Settings → API token |
| **SimilarWeb** | Traffic analytics | [similarweb.com/corp/developer](https://www.similarweb.com/corp/developer/) |
| **BuiltWith** | Tech stack detection | [api.builtwith.com](https://api.builtwith.com) |
| **Yahoo Finance MCP** | Financial data (open source) | No key needed |
| **Chrome DevTools MCP** | Browser automation | No key needed |

---

## Skill Architecture

### The Algolia Search Audit System

```
/algolia-search-audit {url}           ← PARENT ORCHESTRATOR
├── /algolia-audit-research {slug}    ← Phase 1: Research (14 steps, ~15 min)
│   └── /algolia-live-signals {slug}  ← Phase 1b: Apify live intel (~3 min, $0.14)
├── /algolia-audit-browser {slug}     ← Phase 2: Browser testing (~25 min)
├── /algolia-audit-report {slug}      ← Phase 3-5: Scoring + deliverables (~20 min)
└── /algolia-audit-factcheck {slug}   ← Optional: Quality verification
```

---

## All Skills

### 🔍 Search Audit (Parent + Sub-Skills)

#### `/algolia-search-audit` — Orchestrator
Runs the full audit pipeline end-to-end.

```bash
/algolia-search-audit https://brooksrunning.com
/algolia-search-audit https://brooksrunning.com --phase research
/algolia-search-audit https://brooksrunning.com --phase searchaudit
/algolia-search-audit https://brooksrunning.com --phase deliverables
/algolia-search-audit https://brooksrunning.com --deliverable site
/algolia-search-audit https://brooksrunning.com --skip-pdf
```

**MCP required:** Chrome, SimilarWeb, BuiltWith, Yahoo Finance, Apify  
**Output:** Complete workspace with all 12 scratchpads + all deliverables

---

#### `/algolia-audit-research` — Phase 1: Research
Collects company context, tech stack, traffic, competitors, financials, hiring, and investor intelligence.

```bash
/algolia-audit-research brooks-running
/algolia-audit-research brooks-running --refresh hiring
/algolia-audit-research brooks-running --no-browser
```

**Parent:** `/algolia-search-audit`  
**Calls:** `/algolia-live-signals` at Step 8  
**MCP required:** SimilarWeb, BuiltWith, Yahoo Finance, Apify  
**Output:** `{slug}-audit-workspace/` with 12 scratchpad .md files

---

#### `/algolia-live-signals` — Phase 1b: Live Intelligence (Apify)
Scrapes LinkedIn Jobs, company social posts, and Google News in real-time. Replaces Chrome MCP for hiring data.

```bash
/algolia-live-signals brooks-running
```

**Parent:** `/algolia-audit-research` (Step 8)  
**MCP required:** Apify (`APIFY_TOKEN`)  
**Actors used:**
- `curious_coder/linkedin-jobs-scraper` — 50 jobs, 90-day lookback, $0.05
- `harvestapi/linkedin-company-posts` — 30 posts, 30-day lookback, $0.06
- `apidojo/tweet-scraper` — 30 tweets, 90-day lookback, $0.01
- `data_xplorer/google-news-scraper-fast` — 20 articles, 60-day lookback, $0.02

**ICP roles detected:** VP/Director Digital, Senior Engineers (eCommerce/Platform), Performance Marketing, Merchandising, CRO, Analytics  
**Cost:** ~$0.14/audit  
**Output:** `07-hiring-signals.md`, `09b-social-signals.md`, `09c-news-signals.md`

---

#### `/algolia-audit-browser` — Phase 2: Browser Testing
Runs 20 browser-based search tests using real Chrome. Tests NLP, typo tolerance, personalization, recommendations, facets, and 14 more.

```bash
/algolia-audit-browser brooks-running
```

**Parent:** `/algolia-search-audit`  
**MCP required:** Chrome DevTools MCP  
**Output:** `09-browser-findings.md` + `screenshots/` (20+ PNG files)

---

#### `/algolia-audit-report` — Phase 3-5: Scoring & Deliverables
Scores 10 search areas, generates the full JSON schema, renders the SPA and all HTML deliverables.

```bash
/algolia-audit-report brooks-running
/algolia-audit-report brooks-running --deliverable site
/algolia-audit-report brooks-running --skip-pdf
```

**Parent:** `/algolia-search-audit`  
**Requires:** All 12 scratchpad files + screenshots  
**Output:**
- `{slug}-audit-data.json` — 22-section master data
- `{slug}/index.html` — 5-tab SPA (primary deliverable)
- `{slug}-ae-report.html` — AE action card
- `{slug}-battle-card.html` — Feature comparison
- `{slug}-leave-behind.html/pdf` — Prospect-facing
- `{slug}-ae-precall-brief.md` — AE brief
- `{slug}-strategic-signal-brief.md` — Signal brief

---

#### `/algolia-audit-factcheck` — Quality Verification
Verifies all factual claims across deliverables. 7-dimension scoring.

```bash
/algolia-audit-factcheck brooks-running-audit-workspace/
```

**Output:** Factcheck report (0-10 score), correction manifest, skill feedback

---

### 📊 Intelligence & Research

| Skill | Command | Description | MCP |
|-------|---------|-------------|-----|
| **market-research** | `/market-research` | Competitive intelligence briefs | SimilarWeb, BuiltWith |
| **partnerforge** | `/partnerforge enrich {domain}` | Partner displacement opportunities | BuiltWith |
| **persona-research** | `/persona-research` | B2B buyer persona creation | None |

---

### 📝 Content & Collateral

| Skill | Command | Description |
|-------|---------|-------------|
| algolia-brief | `/algolia-brief` | Campaign briefs for Marketing/ABX |
| algolia-blog | `/algolia-blog` | SEO blog posts |
| algolia-case-study | `/algolia-case-study` | Customer case studies |
| algolia-deck | `/algolia-deck` | Presentation decks with speaker notes |
| algolia-email | `/algolia-email` | Email templates |
| algolia-landing | `/algolia-landing` | Landing page content + HTML |
| algolia-one-pager | `/algolia-one-pager` | Executive one-pagers |
| algolia-partner | `/algolia-partner` | Co-branded partner materials |
| algolia-social | `/algolia-social` | LinkedIn + Twitter/X posts |
| algolia-ui-copy | `/algolia-ui-copy` | UI microcopy |
| algolia-algolialize | `/algolia-algolialize` | Transform any content to Algolia brand voice |
| algolia-brand-check | `/algolia-brand-check` | Brand compliance audit (1-10 score) |

---

### 🏗️ Engineering & Architecture

| Skill | Command | Description |
|-------|---------|-------------|
| architect | `/architect` | System architecture + ADRs |
| ui-architect | `/ui-architect` | Frontend architecture + wireframes |
| frontend-design | `/frontend-design` | Production frontend interfaces |
| prd | `/prd` | Product Requirements Documents |
| project-plan | `/project-plan` | Project plans with RACI |
| brainstorm | `/brainstorm` | Structured brainstorming |
| supabase | `/supabase` | Supabase Edge Functions + migrations |
| vercel-deploy | `/vercel-deploy` | Vercel deployment |

---

## Audit Web App

The audit system outputs a deployable webapp:

```
workspace/
├── index.html              ← Hub listing all audits (auto-generated)
├── {company}/
│   └── index.html          ← 5-tab SPA per company
└── {company}-audit-data.json
```

**Generate index page (after each new audit):**
```bash
deno run --allow-read --allow-write \
  ~/.claude/skills/algolia-search-audit/scripts/generate-index.ts
```

**Serve locally:**
```bash
python3 -m http.server 8766
# Open: http://127.0.0.1:8766
```

**Deploy to Vercel:**
```bash
vercel --prod
# Each audit available at: your-url.vercel.app/{company}/
```

---

## SPA Tab Structure

| Tab | Contents |
|-----|---------|
| **Overview** | Score card (4.4/10), G1–G3 critical gaps, M1–M4 moderate gaps, Revenue at risk ($4.85M–$14.55M), Golden angle (Nike + Asics use Algolia), Timing signals, Section nav cards |
| **Company Intel** | Company bento (name/HQ/founded/execs), Financial profile, Tech stack, Hiring intelligence (buying committee), Intelligence signals (news/social/competitive) |
| **Search Audit** | Score heatmap (10 areas), Critical findings (G1–G3 with screenshots), Moderate findings (M1–M4), Positive findings, Test query log |
| **Business Case** | Said vs Found (exec gap pairs), Competitive landscape (4-tier matrix + capability table), Revenue at risk (3 scenarios), Vertical case studies, Why Act Now, Strategic angles |
| **Sales Play** | ICP anchor lines + talk track, Buying committee map, Battle card (SFCC vs Algolia), Discovery questions (in their language), Objection counters, 4-week outreach sequence |

**Features:** Draggable pill navbar, Cmd+K search, ← back breadcrumbs, clickable source links on every data point

---

## Design System

Centralized in `skills/algolia-search-audit/templates/algolia-brand.css`.  
Edit once → all deliverables update automatically on next render.

| Token | Value |
|-------|-------|
| Font | Sora (300/400/600) |
| Primary text | `#23263B` |
| Algolia Blue | `#003DFF` |
| Min font size | 14px |
| Link style | Blue, underline on hover only (no arrows/icons) |

---

## Prerequisites for Full Installation

```bash
# Required runtimes
node --version    # 18+
deno --version    # 1.4+

# CLI tools
npm install -g vercel
brew install gh

# Apify MCP server
npm install -g @apify/actors-mcp-server
```

---

## License

Internal Algolia tool. Not for external distribution.  
Built with Claude Code (claude-sonnet-4-6).
