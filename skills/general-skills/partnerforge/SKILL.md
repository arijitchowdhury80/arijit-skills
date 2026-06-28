---
name: partnerforge
description: Partner Intelligence Platform for Algolia Sales - find displacement opportunities and enrich company data.
---

# PartnerForge

Partner Intelligence Platform for Algolia Sales. Finds companies using partner technologies (Adobe AEM, Shopify, etc.) who are NOT using Algolia for search - displacement opportunities with deep intelligence enrichment.

## Core Logic
```
Displacement Targets = Companies Using Partner Tech − Existing Algolia Customers
```

## Input

Accept a command as `$ARGUMENTS`:

| Command | Description | Example |
|---------|-------------|---------|
| `enrich <domain>` | Enrich a single company with full intelligence | `/partnerforge enrich costco.com` |
| `batch <N>` | Enrich top N hot leads by ICP score | `/partnerforge batch 20` |
| `intel <domain>` | Deep competitive intelligence for one company | `/partnerforge intel walmart.com` |
| `find <partner>` | Find displacement targets for a partner tech | `/partnerforge find "Adobe Experience Manager"` |
| `report <domain>` | Generate full intelligence report PDF | `/partnerforge report mercedes-benz.com` |
| `status` | Show enrichment status and stats | `/partnerforge status` |
| `dashboard` | Regenerate the dashboard HTML | `/partnerforge dashboard` |

### Command Combinations
- `/partnerforge enrich costco.com --force` - Force refresh even if data is fresh
- `/partnerforge batch 50 --tier 1` - Only Commerce tier targets
- `/partnerforge find Shopify --country US` - Filter by country

## MCP Servers Required

| Server | Purpose | Endpoints Used |
|--------|---------|----------------|
| **BuiltWith MCP** | Technology detection | `domain-lookup`, `relationships-api`, `recommendations-api`, `financial-api`, `social-api`, `trust-api`, `keywords-api` |
| **SimilarWeb MCP** | Traffic & competitors | `traffic`, `engagement`, `similar-sites`, `keywords-competitors`, `get-website-content-technologies-agg` |
| **Yahoo Finance MCP** | Financial data | `get_stock_info`, `get_financial_statement`, `get_recommendations`, `get_yahoo_finance_news` |
| **Chrome MCP** | Careers page scraping | For hiring signals when structured data unavailable |

## Process

### Phase 0: Workspace Setup

Create workspace for each enrichment session:
```
partnerforge-workspace/
├── _manifest.md              # Progress tracking
├── {domain}/
│   ├── 01-builtwith.json     # Raw BuiltWith response
│   ├── 02-similarweb.json    # Raw SimilarWeb response
│   ├── 03-yahoo-finance.json # Financial data
│   ├── 04-hiring.json        # Job postings
│   ├── 05-intelligence.md    # Synthesized intelligence
│   └── 06-report.pdf         # Final report (if requested)
└── batch-{date}/
    └── enrichment-log.csv    # Batch processing log
```

### Phase 1: Company Identification

**For `enrich` command:**
1. Validate domain exists in `displacement_targets` table
2. Check `enrichment_status` - skip if fresh (<7 days) unless `--force`
3. Proceed to Phase 2

**For `find` command:**
1. Query `displacement_targets` WHERE `partner_tech` LIKE '%{partner}%'
2. Filter by optional country/tier flags
3. Sort by `icp_score DESC`
4. Return paginated list

**For `batch` command:**
1. Query top N targets by `icp_score` WHERE `enrichment_level != 'full'`
2. Apply tier filter if specified
3. Queue for parallel enrichment (Agent Teams)

### Phase 2: Data Collection

**Step 1: BuiltWith Enrichment**
- `domain-lookup` - Current tech stack, spending estimate
- `relationships-api` - Sister sites, subsidiaries
- `recommendations-api` - Technology gaps
- `financial-api` - Revenue estimate, employee count
- `social-api` - Social profile URLs
- `trust-api` - Domain trust score

**CRITICAL**: Check for search vendor:
- If Algolia detected → Abort (already customer)
- If competitor detected (Coveo, Elasticsearch, Bloomreach, Constructor, Lucidworks, Searchspring, Klevu) → Flag as "displacement" opportunity

**Step 2: SimilarWeb Enrichment**
- `traffic` - Monthly visits, bounce rate, pages/visit
- `engagement` - Avg duration, search traffic %
- `similar-sites` - Competitor list
- `keywords-competitors` - Keyword overlap
- `get-website-content-technologies-agg` - Secondary tech stack verification

**Step 3: Yahoo Finance Enrichment** (public companies only)
1. Resolve ticker via WebSearch if not in `TICKER_MAP`
2. `get_stock_info` - Market cap, sector, employees
3. `get_financial_statement("income_stmt")` - 3-year revenue, net income, EBITDA
4. `get_financial_statement("balance_sheet")` - Assets, debt, cash
5. `get_recommendations` - Analyst consensus

**TICKER_MAP (54 verified):**
```python
TICKER_MAP = {
    'costco.com': 'COST', 'autozone.com': 'AZO', 'bestbuy.com': 'BBY',
    'walmart.com': 'WMT', 'target.com': 'TGT', 'homedepot.com': 'HD',
    'lowes.com': 'LOW', 'wayfair.com': 'W', 'etsy.com': 'ETSY',
    'ebay.com': 'EBAY', 'amazon.com': 'AMZN', 'kohls.com': 'KSS',
    'macys.com': 'M', 'nordstrom.com': 'JWN', 'gap.com': 'GPS',
    'williams-sonoma.com': 'WSM', 'dickssportinggoods.com': 'DKS',
    'ulta.com': 'ULTA', 'sephora.com': 'LVMUY', 'nike.com': 'NKE',
    'mercedes-benz.com': 'MBG.DE', 'bmw.com': 'BMW.DE', 'ford.com': 'F',
    'gm.com': 'GM', 'toyota.com': 'TM', 'cvs.com': 'CVS',
    'walgreens.com': 'WBA', 'kroger.com': 'KR', 'albertsons.com': 'ACI',
    'publix.com': None,  # Private
    'wegmans.com': None,  # Private
    'spglobal.com': 'SPGI', 'bloomberg.com': None,  # Private
    'reuters.com': 'TRI', 'wsj.com': 'NWS', 'nytimes.com': 'NYT',
    'washingtonpost.com': None,  # Private (Bezos)
    'cnn.com': 'WBD', 'foxnews.com': 'FOX', 'nbcnews.com': 'CMCSA',
    'microsoft.com': 'MSFT', 'apple.com': 'AAPL', 'google.com': 'GOOGL',
    'meta.com': 'META', 'salesforce.com': 'CRM', 'adobe.com': 'ADBE',
    'oracle.com': 'ORCL', 'sap.com': 'SAP', 'shopify.com': 'SHOP',
    'twilio.com': 'TWLO', 'datadog.com': 'DDOG', 'snowflake.com': 'SNOW',
    'tapestry.com': 'TPR', 'therealreal.com': 'REAL',
    # ... plus 8 more in database
}
```

**Step 4: Hiring Signals** (Chrome MCP if needed)
- Extract job postings from careers page
- Categorize by department (Search, AI/ML, Platform, Data, Ecommerce)
- Calculate hiring velocity (roles added in last 30/60/90 days)
- Identify budget signals (senior roles, team expansion)

### Phase 3: Signal Scoring

**ICP Score (0-100):**
| Component | Max | Logic |
|-----------|-----|-------|
| Vertical/Tier | 40 | Commerce=40, Content=25, Support=15 |
| Traffic | 30 | 50M+=30, 10M+=25, 1M+=15 |
| Tech Spend | 20 | $100K+=20, $50K+=15 |
| Partner Tech | 10 | Adobe=10, Shopify=7 |

**Signal Score (0-100):**
| Signal | Weight | Source |
|--------|--------|--------|
| Hiring search/AI roles | +25 | Careers page |
| Revenue growing >10% YoY | +15 | Yahoo Finance |
| Margin zone = Green (>20%) | +10 | Yahoo Finance |
| Search vendor REMOVED | +30 | BuiltWith |
| Using competitor search | +15 | BuiltWith |
| Executive quote re digital | +20 | Earnings call |
| New CTO/CDO (<12mo) | +25 | LinkedIn/News |
| Platform migration | +20 | 10-K/News |
| Competitor uses Algolia | +20 | BuiltWith + Case studies |
| Layoffs announced | -25 | News |
| Added competitor search | -40 | BuiltWith |

**Priority Classification:**
```
HOT = Score >= 150 OR (has Budget AND Pain AND Timing signals)
WARM = Score 100-149 OR (has 2 of 3 signal types)
COOL = Score 50-99
COLD = Score < 50 OR negative signals
```

### Phase 4: Database Persistence

Update `displacement_targets` table:
```sql
UPDATE displacement_targets SET
    enrichment_level = 'full',
    last_enriched = NOW(),
    revenue = ?,
    gross_margin = ?,
    traffic_growth = ?,
    current_search = ?,
    trigger_events = ?,
    exec_quote = ?,
    exec_name = ?,
    exec_title = ?,
    competitors_using_algolia = ?,
    displacement_angle = ?,
    financials_json = ?,
    hiring_signals = ?,
    tech_stack_json = ?
WHERE domain = ?
```

### Phase 5: Report Generation (for `report` command)

Generate PDF report with:
1. **Executive Summary** - Priority status, key signals, recommended actions
2. **Company Profile** - Overview, leadership, recent news
3. **Financial Analysis** - 3-year trends, margin zone, analyst ratings
4. **Technology Stack** - Current search, partner tech, gaps
5. **Competitive Landscape** - Who else is in market, who uses Algolia
6. **Hiring Signals** - Budget indicators, team growth
7. **Trigger Events** - Recent changes, strategic shifts
8. **Recommended Approach** - Personalized messaging angles
9. **Case Study Matches** - Relevant Algolia proof points

## Output Files

| Command | Output |
|---------|--------|
| `enrich <domain>` | Updates database + logs to console |
| `batch <N>` | `batch-{date}/enrichment-log.csv` |
| `intel <domain>` | `{domain}/05-intelligence.md` |
| `find <partner>` | Console table + optional CSV export |
| `report <domain>` | `{domain}/06-report.pdf` |
| `status` | Console output |
| `dashboard` | Regenerates `index.html` |

## Database Location

**SQLite:** `/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/PartnerForge/data/partnerforge.db`

**Tables:**
- `displacement_targets` - 2,687 AEM users not on Algolia
- `companies` - 400 existing Algolia customers
- `competitive_intel` - 25 SimilarWeb → BuiltWith analyses
- `case_studies` - 161 for matching to targets
- `verified_case_studies` - 16 verified Algolia case study URLs

## API Keys

Stored in `.env`:
```
BUILTWITH_API_KEY=<your-builtwith-key>
SIMILARWEB_API_KEY=<your-similarweb-key>
```

## FastAPI Backend (v2.1)

For on-demand enrichment via web UI:

**Location:** `api/main.py`

**Endpoints:**
- `GET /api/company/{domain}` - Get company data (cached or fresh)
- `POST /api/enrich/{domain}?force=true` - Trigger enrichment
- `GET /api/targets?page=1&per_page=50` - List paginated targets
- `GET /api/stats` - Get summary statistics

**Run locally:**
```bash
cd PartnerForge
pip3 install -r requirements.txt
uvicorn api.main:app --port 8000
```

**Cache TTL:** 7 days (data refreshed only when stale or `force=true`)

## Agent Teams Execution (for `batch` command)

When running batch enrichment, spawn parallel agents:

**Wave 1:** Up to 5 companies enriched in parallel
- Each agent handles one domain
- Uses BuiltWith → SimilarWeb → Yahoo Finance pipeline
- Writes to shared SQLite database (with row-level locking)

**Wave 2:** Continue with next 5 until batch complete

**Prerequisites:**
- Install `claude-sneakpeek`: `npx @realmikekelly/claude-sneakpeek quick --name claudesp`
- Run via `claudesp` (not `claude` or VS Code)

## Dashboard

**Live:** https://partnerforge.vercel.app

**Regenerate:**
```bash
cd PartnerForge
python3 scripts/generate_dashboard.py
git add index.html && git commit -m "Regenerate dashboard" && git push
```

## Current Stats (Feb 25, 2026)

- **2,687 displacement targets** (AEM users not on Algolia)
- **9 hot leads** (score 80+): Mercedes-Benz (95), Mark's (85), Infiniti (85), Allianz (85), Chevrolet Mexico (85), HOFER (85), Fiat (85), Bever (85), Sunstar (80)
- **49 warm leads** (score 60-79)
- **Estimated pipeline:** $63M

## Source Citation Requirements

Every data point must have a source:
- Financial figures → Yahoo Finance or SEC EDGAR URL
- Traffic stats → SimilarWeb URL
- Technology claims → BuiltWith URL
- Hiring signals → Careers page URL
- Executive quotes → Earnings transcript or press release URL

## Error Handling

| Error | Fallback |
|-------|----------|
| BuiltWith credits exhausted | Use SimilarWeb `get-website-content-technologies-agg` |
| Yahoo Finance ticker not found | Mark as "Private Company", skip financials |
| SimilarWeb API 403 | Use `country: "ww"` instead of `country: "us"` |
| Careers page blocked | Mark `hiring_status: "manual_required"` |

## Related Skills

- `/algolia-search-audit` - Full search audit on prospect website
- `/algolia-audit-factcheck` - Validate audit outputs
- `/market-research` - Competitive intelligence briefs
