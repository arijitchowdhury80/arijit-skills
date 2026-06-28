---
name: detect-search
description: >
  Use when asked to identify, detect, or check what search platform a website uses — 'what search does X.com use', 'is this site on Algolia', 'detect their search vendor', 'scan these URLs for search tech', 'run detect-search on X', 'what search API does this site call', 'check if they use Constructor/Coveo/Bloomreach', or any request to discover a website's search stack by inspecting network traffic. Runs a Playwright browser, loads the target URL, triggers a search interaction, and pattern-matches network requests against 30+ platform signatures (Algolia, Constructor.io, Coveo, Bloomreach, Yext, Typesense, Elasticsearch, Searchspring, Klevu, and 20+ more). Extracts deep details: API keys, app IDs, index names, client versions, queries. Catches proxied setups where search API calls go through first-party domains. Supports single URL or bulk file input. Do NOT use for setting up or configuring search (use docs), running full Algolia audits (use algolia-audit-research), checking tech stacks broadly via BuiltWith, or comparing search platforms conceptually.
---

# Detect-Search — Universal Search Platform Detector

Sniffs network traffic to identify which search API a website calls. Platform-agnostic — detects whatever search technology is in use and extracts as much detail as the network traffic reveals.

## When to Use

- "What search platform does this website use?"
- "Is this site running Algolia / Coveo / Constructor / etc.?"
- "Scan these sites and tell me their search stack"
- "Run detect-search on [url or file]"
- Before or during a search audit to identify the incumbent

## How It Works

1. Opens headless Chromium via Playwright
2. Loads target URL, waits for page render
3. **Triggers search by default**: clicks search toggle → types query → captures API calls
4. Pattern-matches network URLs + request headers against 30+ platform signatures
5. Runs deep extraction per platform: API keys, app IDs, index names, client versions, queries
6. Checks HTML source for platform JS bundles (fallback detection)
7. Reports bot-blocking (Akamai, Cloudflare)

## Platforms Detected (30+)

### Full deep extraction (API keys, IDs, indexes, versions):
| Platform | Extracts |
|---|---|
| **Algolia** | app_id, api_key, agent (JS version), indexes, query |
| **Constructor.io** | api_key, client version, section, endpoint_type, query |
| **Coveo** | org_id, access_token, search_hub, query |
| **Bloomreach** | account_id, domain_key, auth_key, query |
| **Yext** | api_key, experience_key, locale, api_version, query |
| **Searchspring** | site_id, query |
| **Klevu** | api_key (ticket), query |
| **Typesense** | api_key, collection, query |
| **Elasticsearch** | index, query_dsl |
| **Meilisearch** | api_key, index, query |
| **Doofinder** | hash_id, query |
| **Swiftype** | engine, query |
| **Google Retail** | project_id, query |

### Pattern detection (endpoint + query extraction):
Unbxd, HawkSearch, GroupBy, Attraqt, Empathy.co, Nosto, Syte, AddSearch, Lucidworks, Loop54, Sajari, Bonsai/Orama, Cludo, Fast Simon, DealerSocket, DealerEProcess, RideMotive, Cars Commerce, Dealer.com

## Usage

### Single URL (searches "test" by default)
```
node ~/.claude/skills/detect-search/detect-search.js https://www.example.com
```

### With specific search term
```
node ~/.claude/skills/detect-search/detect-search.js https://www.example.com --type-query "shoes"
```

### Skip search interaction (page-load only)
```
node ~/.claude/skills/detect-search/detect-search.js https://www.example.com --no-search
```

### Bulk mode
```
node ~/.claude/skills/detect-search/detect-search.js --file urls.txt --csv
```

## Output Schema

```json
{
  "url": "https://www.petsmart.com",
  "search_detected": true,
  "search_platform": "Algolia",
  "platform_id": "algolia",
  "platform_details": {
    "app_id": "97P6EWKR25",
    "api_key": "89538b14986f30460d07967cc3717153",
    "agent": "Algolia for JavaScript (4.24.0); Browser; autocomplete-core (1.12.1)",
    "indexes": ["p-US_products_query_suggestions", "p-US_products"]
  },
  "all_platforms_found": [...],
  "search_requests": [...],
  "is_dealer_inspire": false,
  "network_calls_total": 245,
  "search_calls_count": 4,
  "bot_blocked": false,
  "error": null
}
```

## Validated Results (2026-06-21)

| Site | Platform | Key Details |
|---|---|---|
| Gymshark | Algolia | `2DEAES0CUO`, JS 4.19.1, index `production_us_products_v2` |
| Breville | Algolia | `VBT275CJRZ`, JS 4.25.3, 4 indexes including query suggestions |
| Arc'teryx | Algolia | `R5KI4B59T0`, autocomplete-core 1.19.4, 2 indexes |
| edX | Algolia | `IGSYV1Z1XI`, InstantSearch 4.78.1, Next.js 15.2.9 |
| PetSmart | Algolia | `97P6EWKR25`, **proxied through petsmart.com** (no algolia.net calls) |
| Stripe Docs | Algolia | `Y4PFTTJ91H` |
| Under Armour | Constructor.io | key `key_Gz4VzKsXbR7b7fSh`, client 2.65.0 |
| Slack | Yext | key `985ff...`, experience `answers-starter` |
| Walgreens | Proprietary | `/retailsearch/typeahead` |

## Checklist

When invoked:

1. Determine input: single URL, URL list, or file
2. Run: `node ~/.claude/skills/detect-search/detect-search.js <args>`
3. Parse JSON, present findings. For each platform found show the deep details.
4. For bulk: table with platform breakdown + detail column

## Prerequisites

```bash
cd ~/.claude/skills/detect-search && npm install && npx playwright install chromium
```

## Constraints

- **No LLM calls** — deterministic pattern matching + extraction
- **Search by default** — always types a query unless `--no-search`
- **Proxied detection** — catches Algolia/others routed through first-party domains via headers + URL params
- **~10-15s per site**
