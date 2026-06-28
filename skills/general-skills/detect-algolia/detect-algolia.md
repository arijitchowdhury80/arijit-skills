---
name: detect-algolia
description: Detect whether a website uses Algolia search (including proxied/first-party domain setups) by capturing network traffic via Playwright. Identifies 25+ search platforms. Always triggers a search interaction by default. Reports bot-blocked sites honestly. Works on single URLs or bulk file input. Deterministic — no LLM calls.
---

# Detect-Algolia — Search Platform Detection Skill

Detects search platform on any website by headless browsing + network capture. Always performs a search interaction (types "test" into search box by default) to trigger search API calls. Catches both direct Algolia (`*.algolia.net`) and proxied setups (`x-algolia-agent` in query params, `x-algolia-application-id` in headers).

## When to Use

- "What search does this website use?"
- "Is this site running Algolia?"
- "Scan these dealer sites for search platform"
- "Run detect-algolia on [url or file]"
- Before or during an Algolia search audit

## How It Works

1. Opens Chromium headless via Playwright
2. Navigates to target URL, waits for page load
3. **Searches by default**: clicks search toggle → types query → captures API calls. Falls back to `/search?q=` URL if no input found
4. Pattern-matches network URLs against 25+ search platform signatures
5. Checks request headers for `x-algolia-application-id` (catches proxied setups like PetSmart)
6. Detects bot-blocking (Akamai "Access Denied", Cloudflare challenges)
7. Returns structured JSON

## Search Interaction (3-Step)

Always runs unless `--no-search` flag is set:

1. **Click toggle** — tries `button[aria-label*="search"]`, `.search-icon`, `header button:has(svg)`, etc.
2. **Type query** — fills `input[type="search"]`, `input[placeholder*="search"]`, `input[role="combobox"]`, etc.
3. **Fallback** — navigates to `/search?q={term}` if no input found

## Platforms Detected (25+)

| Platform | Signal |
|---|---|
| **Algolia** | `*.algolia.net`, `x-algolia-agent=`, `x-algolia-application-id=`, `/1/indexes/*/queries` |
| Cars Commerce Proprietary | `websites-search.api.carscommerce.inc` |
| D2C Media / Algolia | App ID `VBAFQME90B` |
| Constructor.io | `cnstrc.com` |
| Coveo | `coveo.com` |
| Bloomreach | `bloomreach`, `brcloud` |
| Yext | `yext.com`, `liveapi.yext` |
| Searchspring | `searchspring.net` |
| Klevu | `klevu.com` |
| Unbxd (Netcore) | `unbxd.io`, `unbxdapi.com` |
| HawkSearch | `hawksearch.com` |
| GroupBy | `groupbycloud.com` |
| Swiftype (Elastic) | `swiftype.com` |
| Doofinder | `doofinder.com` |
| Typesense | `typesense.org` |
| Meilisearch | `meilisearch.com` |
| Attraqt (Crownpeak) | `attraqt.com` |
| Empathy.co | `empathy.co` |
| Nosto | `nosto.com` |
| Syte | `syte.ai` |
| AddSearch | `addsearch.com` |
| Lucidworks | `lucidworks.com` |
| Google Retail Search | `retail.googleapis.com` |
| Elasticsearch | `/_search?`, `elasticsearch.com` |
| Dealer.com (Cox) | `dealer.com/api` |
| DealerSocket | `dealersocket.com` |
| RideMotive | `ridemotive.com` |

## Usage

### Single URL (searches "test" by default)

```
node ~/.claude/skills/detect-algolia/detect-algolia.js https://www.example.com
```

### Custom search term

```
node ~/.claude/skills/detect-algolia/detect-algolia.js https://www.example.com --type-query "honda civic"
```

### Page-load only (skip search interaction)

```
node ~/.claude/skills/detect-algolia/detect-algolia.js https://www.example.com --no-search
```

### Bulk mode

```
node ~/.claude/skills/detect-algolia/detect-algolia.js --file urls.txt --csv
```

### Options

- `--type-query <q>` — Search term (default: "test")
- `--no-search` — Skip search interaction, only capture page-load traffic
- `--file <path>` — Bulk mode, one URL per line
- `--csv` — CSV output (bulk mode)
- `--timeout <ms>` — Nav timeout (default: 30000)
- `--wait <ms>` — Wait after load (default: 5000)

## Output Schema

```json
{
  "url": "https://...",
  "algolia_detected": true,
  "algolia_app_id": "97P6EWKR25",
  "search_platform": "Algolia",
  "search_platforms_found": [{ "id": "algolia", "name": "Algolia", "hit_count": 3 }],
  "search_endpoint": "https://...",
  "sample_query": { ... },
  "is_dealer_inspire": false,
  "network_calls_total": 208,
  "search_calls_count": 4,
  "bot_blocked": false,
  "error": null,
  "timestamp": "2026-06-21T..."
}
```

## Validated Results (2026-06-21)

| Brand | Result | App ID | Notes |
|---|---|---|---|
| Gymshark | Algolia | `2DEAES0CUO` | JS 4.19.1 + Recommend |
| Breville | Algolia | `VBT275CJRZ` | Toggle click required |
| Arc'teryx | Algolia | `R5KI4B59T0` | Toggle click required |
| edX | Algolia | `IGSYV1Z1XI` | InstantSearch 7.15.5 |
| PetSmart | Algolia | `97P6EWKR25` | **Proxied** through petsmart.com, detected via headers |
| Stripe Docs | Algolia | `Y4PFTTJ91H` | Direct algolia.net calls |
| Under Armour | Constructor.io | — | |
| Slack | Yext | — | |
| Walgreens | Proprietary | — | `/retailsearch/typeahead` |
| EyeBuyDirect | Bot Blocked | — | Akamai WAF |
| Lacoste | Bot Blocked | — | Akamai WAF |

## Checklist

When invoked:

1. Determine input: single URL, URL list, or file path
2. Run: `node ~/.claude/skills/detect-algolia/detect-algolia.js <args>`
3. Parse JSON, present findings as table
4. For bulk: summarize totals (Algolia count, platform breakdown, bot-blocked count, errors)

## Prerequisites

```bash
cd ~/.claude/skills/detect-algolia && npm install && npx playwright install chromium
```

## Constraints

- **No LLM calls** — deterministic pattern matching only
- **Search by default** — always triggers search unless `--no-search`
- **Proxied Algolia detection** — catches sites routing through first-party domains
- **Bot-blocked reporting** — distinguishes "didn't find Algolia" from "couldn't load page"
- ~10-15 seconds per site
