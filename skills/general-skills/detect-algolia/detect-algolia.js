#!/usr/bin/env node
// detect-algolia.js — Deterministic search platform detector via Playwright network capture.
// No LLM calls. Pure pattern matching on network traffic + HTML source.

const { chromium } = require('playwright');

const PLATFORM_PATTERNS = [
  { id: 'algolia',              name: 'Algolia',                               urlPatterns: ['.algolia.net', '.algolia.com/1/', 'x-algolia-agent=', 'x-algolia-application-id=', '/1/indexes/*/queries'],     headerPatterns: ['x-algolia'] },
  { id: 'cars_commerce',        name: 'Cars Commerce Proprietary (Dealer Inspire)', urlPatterns: ['websites-search.api.carscommerce.inc'], headerPatterns: [] },
  { id: 'd2c_algolia',          name: 'D2C Media / Algolia',                   urlPatterns: ['VBAFQME90B'],                          headerPatterns: [] },
  { id: 'dealer_com',           name: 'Dealer.com (Cox Automotive)',           urlPatterns: ['dealer.com/api', 'ddc.com'],            headerPatterns: [] },
  { id: 'dealersocket',         name: 'DealerSocket',                          urlPatterns: ['dealersocket.com'],                     headerPatterns: [] },
  { id: 'ridemotive',           name: 'RideMotive',                            urlPatterns: ['ridemotive.com'],                       headerPatterns: [] },
  { id: 'dealer_inspire',       name: 'Dealer Inspire (Cars Commerce)',        urlPatterns: ['onlineshopper.dealerinspire.com'],      headerPatterns: [] },
  { id: 'coveo',                name: 'Coveo',                                 urlPatterns: ['coveo.com', 'cloud.coveo'],             headerPatterns: [] },
  { id: 'constructor_io',       name: 'Constructor.io',                        urlPatterns: ['cnstrc.com', 'constructor.io'],         headerPatterns: [] },
  { id: 'bloomreach',           name: 'Bloomreach',                            urlPatterns: ['bloomreach', 'brcloud'],                headerPatterns: [] },
  { id: 'searchspring',         name: 'Searchspring',                          urlPatterns: ['searchspring.net'],                     headerPatterns: [] },
  { id: 'yext',                 name: 'Yext',                                  urlPatterns: ['yext.com', 'liveapi.yext'],             headerPatterns: [] },
  { id: 'elasticsearch',        name: 'Elasticsearch',                         urlPatterns: ['elasticsearch.com', '/_search?', ':9200/'],  headerPatterns: [] },
  { id: 'dealereprocess',       name: 'DealerEProcess',                        urlPatterns: ['dealereprocess.org'],                    headerPatterns: [] },
  { id: 'klevu',                name: 'Klevu',                                 urlPatterns: ['klevu.com'],                            headerPatterns: [] },
  { id: 'unbxd',                name: 'Unbxd (Netcore)',                       urlPatterns: ['unbxd.io', 'unbxdapi.com'],             headerPatterns: [] },
  { id: 'hawksearch',           name: 'HawkSearch',                            urlPatterns: ['hawksearch.com'],                       headerPatterns: [] },
  { id: 'groupby',              name: 'GroupBy',                               urlPatterns: ['groupbycloud.com'],                     headerPatterns: [] },
  { id: 'swiftype',             name: 'Swiftype (Elastic)',                    urlPatterns: ['swiftype.com'],                         headerPatterns: [] },
  { id: 'doofinder',            name: 'Doofinder',                             urlPatterns: ['doofinder.com'],                        headerPatterns: [] },
  { id: 'typesense',            name: 'Typesense',                             urlPatterns: ['typesense.org', 'cloud.typesense'],     headerPatterns: [] },
  { id: 'meilisearch',          name: 'Meilisearch',                           urlPatterns: ['meilisearch.com'],                      headerPatterns: [] },
  { id: 'attraqt',              name: 'Attraqt (Crownpeak)',                   urlPatterns: ['attraqt.com', 'crownpeak.com'],         headerPatterns: [] },
  { id: 'empathy',              name: 'Empathy.co',                            urlPatterns: ['empathy.co', 'empathybroker'],          headerPatterns: [] },
  { id: 'nosto',                name: 'Nosto',                                 urlPatterns: ['nosto.com'],                            headerPatterns: [] },
  { id: 'syte',                 name: 'Syte',                                  urlPatterns: ['syte.ai'],                              headerPatterns: [] },
  { id: 'addsearch',            name: 'AddSearch',                             urlPatterns: ['addsearch.com'],                        headerPatterns: [] },
  { id: 'lucidworks',           name: 'Lucidworks',                            urlPatterns: ['lucidworks.com', 'app.lucidworks'],     headerPatterns: [] },
  { id: 'google_retail',        name: 'Google Retail Search',                  urlPatterns: ['retail.googleapis.com', 'discoveryengine.googleapis.com'], headerPatterns: [] },
];

const SEARCH_URL_SIGNALS = [
  '/search', '/inventory', '/listings', '/query',
  '/suggest', '/autocomplete', '/typeahead', '/facet',
  'api/search', 'api/v1/search', 'api/v1/listings',
];

const ANALYTICS_DOMAINS = [
  'google-analytics.com', 'analytics.google.com', 'googletagmanager.com',
  'facebook.com', 'doubleclick.net', 'googlesyndication.com',
  'google.com/measurement', 'google.com/pagead', 'bing.com/bat',
  'clarity.ms', 'hotjar.com', 'newrelic.com', 'nr-data.net',
  'sentry.io', 'segment.com', 'cdn.segment.com',
];

const DI_FINGERPRINTS = [
  'dealerinspire.com',
  'di-uploads-pod', 'di-shared-assets',
  'Advanced Automotive Dealer Websites by Dealer Inspire',
];

function identifyPlatform(url) {
  const lower = url.toLowerCase();
  for (const p of PLATFORM_PATTERNS) {
    if (p.urlPatterns.some(pat => lower.includes(pat.toLowerCase()))) {
      return p;
    }
  }
  return null;
}

function isSearchRelated(url) {
  const lower = url.toLowerCase();
  if (ANALYTICS_DOMAINS.some(d => lower.includes(d))) return false;
  return SEARCH_URL_SIGNALS.some(sig => lower.includes(sig));
}

function extractAlgoliaAppId(url) {
  const match = url.match(/https?:\/\/([A-Z0-9]{10,})-\d*\.?algolia(?:net)?\.net/i)
    || url.match(/https?:\/\/([A-Z0-9]{10,})-dsn\.algolia\.net/i);
  if (match) return match[1].toUpperCase();
  const paramMatch = url.match(/[?&]x-algolia-application-id=([A-Z0-9]+)/i);
  if (paramMatch) return paramMatch[1].toUpperCase();
  return null;
}

function safePostData(request) {
  try {
    const data = request.postData();
    if (!data) return null;
    try { return JSON.parse(data); } catch { return data.substring(0, 500); }
  } catch { return null; }
}

function safeQueryParams(url) {
  try {
    const u = new URL(url);
    const params = {};
    u.searchParams.forEach((v, k) => { params[k] = v; });
    return Object.keys(params).length > 0 ? params : null;
  } catch { return null; }
}

async function detectSearch(targetUrl, options = {}) {
  const { timeout = 30000, waitAfterLoad = 5000, typeQuery = 'test', noSearch = false } = options;
  const result = {
    url: targetUrl,
    algolia_detected: false,
    algolia_app_id: null,
    search_platform: 'Unknown',
    search_platforms_found: [],
    search_endpoint: null,
    sample_query: null,
    is_dealer_inspire: false,
    network_calls_total: 0,
    search_calls_count: 0,
    bot_blocked: false,
    error: null,
    timestamp: new Date().toISOString(),
  };

  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
      viewport: { width: 1440, height: 900 },
    });
    const page = await context.newPage();

    const allRequests = [];
    const searchRequests = [];
    const platformHits = new Map();

    let algoliaAppIdFromHeaders = null;
    page.on('request', req => {
      const url = req.url();
      allRequests.push(url);

      const headers = req.headers();
      if (headers['x-algolia-application-id'] && !algoliaAppIdFromHeaders) {
        algoliaAppIdFromHeaders = headers['x-algolia-application-id'].toUpperCase();
      }

      const platform = identifyPlatform(url);
      if (platform) {
        const key = platform.id;
        if (!platformHits.has(key)) {
          platformHits.set(key, { platform, urls: [], methods: [], queries: [] });
        }
        const entry = platformHits.get(key);
        entry.urls.push(url);
        entry.methods.push(req.method());
        const postBody = safePostData(req);
        const queryParams = safeQueryParams(url);
        if (postBody || queryParams) {
          entry.queries.push(postBody || queryParams);
        }
      }

      if (isSearchRelated(url) && (req.resourceType() === 'xhr' || req.resourceType() === 'fetch' || req.resourceType() === 'document')) {
        searchRequests.push({
          url, method: req.method(),
          postData: safePostData(req),
          queryParams: safeQueryParams(url),
        });
      }
    });

    await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout });
    await page.waitForTimeout(waitAfterLoad);

    if (typeQuery && !noSearch) {
      let typed = false;
      const log = (msg) => process.stderr.write(`  [search] ${msg}\n`);

      // Step 1: Try clicking search toggle icons/buttons to reveal the input
      const searchToggleSelectors = [
        'button[aria-label*="search" i]',
        'a[aria-label*="search" i]',
        '[data-testid*="search" i]',
        '.search-icon', '.search-toggle', '.search-button',
        'button.search', 'a.search',
        '[class*="SearchIcon"]', '[class*="search-icon"]',
        'svg[class*="search" i]',
        'header button:has(svg)',
      ];
      let toggleClicked = false;
      for (const sel of searchToggleSelectors) {
        try {
          const el = page.locator(sel).first();
          if (await el.isVisible({ timeout: 1000 })) {
            await el.click({ timeout: 2000 });
            await page.waitForTimeout(800);
            log(`toggle clicked: ${sel}`);
            toggleClicked = true;
            break;
          }
        } catch { /* next */ }
      }
      if (!toggleClicked) log('no toggle found');

      // Step 2: Try typing into visible search inputs
      const searchInputSelectors = [
        'input[type="search"]',
        'input[name*="search" i]',
        'input[placeholder*="search" i]',
        'input[id*="search" i]',
        'input[aria-label*="search" i]',
        'input[data-testid*="search" i]',
        '#searchInput', '.search-input',
        'input[role="searchbox"]', 'input[role="combobox"]',
      ];
      for (const sel of searchInputSelectors) {
        if (typed) break;
        try {
          const el = page.locator(sel).first();
          if (await el.isVisible({ timeout: 1500 })) {
            await el.click({ timeout: 2000 });
            await page.waitForTimeout(300);
            await el.fill(typeQuery);
            await page.waitForTimeout(3000);
            log(`typed "${typeQuery}" into: ${sel}`);
            typed = true;
          }
        } catch { /* next */ }
      }

      // Step 3: Fallback — navigate to /search?q= URL
      if (!typed) {
        log('no input found, falling back to /search?q= URL');
        try {
          const base = new URL(targetUrl);
          const searchUrl = `${base.origin}/search?q=${encodeURIComponent(typeQuery)}`;
          await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: timeout });
          await page.waitForTimeout(waitAfterLoad);
          log(`navigated to ${searchUrl}`);
        } catch (e) { log(`fallback nav failed: ${e.message}`); }
      }
    }

    const html = await page.content();
    const title = await page.title();

    const botBlocked = title === 'Access Denied'
      || (html.includes('Access Denied') && html.includes("don't have permission"))
      || html.includes('cf-challenge-running')
      || html.includes('cf_chl_opt')
      || html.includes('Please verify you are a human')
      || html.includes('Checking your browser before accessing');
    result.bot_blocked = botBlocked;

    const diDetected = DI_FINGERPRINTS.some(fp => html.includes(fp));
    result.is_dealer_inspire = diDetected;

    result.network_calls_total = allRequests.length;
    result.search_calls_count = searchRequests.length;

    const algoliaHit = platformHits.get('algolia') || platformHits.get('d2c_algolia');
    if (algoliaHit) {
      result.algolia_detected = true;
      result.search_platform = algoliaHit.platform.name;
      result.search_endpoint = algoliaHit.urls[0];
      result.sample_query = algoliaHit.queries[0] || null;
      const appId = algoliaHit.urls.map(extractAlgoliaAppId).find(Boolean) || algoliaAppIdFromHeaders;
      result.algolia_app_id = appId || null;
      if (appId === 'VBAFQME90B') {
        result.search_platform = 'D2C Media / Algolia';
      }
    } else {
      const htmlAlgolia = html.toLowerCase().includes('algolia.net') || html.toLowerCase().includes('algolianet');
      if (htmlAlgolia) {
        result.algolia_detected = true;
        result.search_platform = 'Algolia (HTML source only)';
      }
    }

    const allPlatforms = [];
    for (const [, val] of platformHits) {
      allPlatforms.push({
        id: val.platform.id,
        name: val.platform.name,
        hit_count: val.urls.length,
        sample_url: val.urls[0],
      });
    }
    result.search_platforms_found = allPlatforms;

    if (!result.algolia_detected && platformHits.size > 0) {
      const primary = [...platformHits.values()]
        .filter(v => v.platform.id !== 'dealer_inspire')
        .sort((a, b) => b.urls.length - a.urls.length)[0];
      if (primary) {
        result.search_platform = primary.platform.name;
        result.search_endpoint = primary.urls[0];
        result.sample_query = primary.queries[0] || null;
      }
    }

    if (!result.algolia_detected && platformHits.size === 0 && searchRequests.length > 0) {
      const primary = searchRequests[0];
      result.search_platform = 'Unknown (search traffic detected)';
      result.search_endpoint = primary.url;
      result.sample_query = primary.postData || primary.queryParams || null;
    }

    await browser.close();
  } catch (err) {
    result.error = err.message;
    if (browser) try { await browser.close(); } catch {}
  }

  return result;
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help')) {
    console.log(`
Usage:
  node detect-algolia.js <url>                    Detect search platform (searches "test" by default)
  node detect-algolia.js --file <path>            Bulk mode: one URL per line
  node detect-algolia.js --file <path> --csv      Bulk mode with CSV output
  node detect-algolia.js <url> --type-query "honda"  Use a specific search term

Options:
  --file <path>       File with one URL per line
  --csv               Output CSV instead of JSON (bulk mode only)
  --type-query <q>    Search term to type (default: "test")
  --no-search         Skip search interaction (only capture page-load traffic)
  --timeout <ms>      Navigation timeout in ms (default: 30000)
  --wait <ms>         Wait after load in ms (default: 5000)
  --help              Show this help
`);
    process.exit(0);
  }

  const fileIdx = args.indexOf('--file');
  const csvMode = args.includes('--csv');
  const typeIdx = args.indexOf('--type-query');
  const timeoutIdx = args.indexOf('--timeout');
  const waitIdx = args.indexOf('--wait');

  const noSearch = args.includes('--no-search');
  const typeQuery = typeIdx >= 0 ? args[typeIdx + 1] : 'test';
  const timeout = timeoutIdx >= 0 ? parseInt(args[timeoutIdx + 1], 10) : 30000;
  const waitAfterLoad = waitIdx >= 0 ? parseInt(args[waitIdx + 1], 10) : 5000;
  const options = { timeout, waitAfterLoad, typeQuery, noSearch };

  if (fileIdx >= 0) {
    const fs = require('fs');
    const filePath = args[fileIdx + 1];
    const urls = fs.readFileSync(filePath, 'utf8')
      .split('\n')
      .map(l => l.trim())
      .filter(l => l && !l.startsWith('#'));

    if (csvMode) {
      console.log('url,algolia_detected,algolia_app_id,search_platform,search_endpoint,is_dealer_inspire,search_calls_count,bot_blocked,error');
    }

    const results = [];
    for (let i = 0; i < urls.length; i++) {
      let url = urls[i];
      if (!url.startsWith('http')) url = 'https://' + url;
      process.stderr.write(`[${i + 1}/${urls.length}] ${url}\n`);

      const r = await detectSearch(url, options);
      results.push(r);

      if (csvMode) {
        const esc = (s) => '"' + (s || '').replace(/"/g, '""') + '"';
        console.log([
          esc(r.url), r.algolia_detected, esc(r.algolia_app_id),
          esc(r.search_platform), esc(r.search_endpoint),
          r.is_dealer_inspire, r.search_calls_count, r.bot_blocked, esc(r.error),
        ].join(','));
      }
    }

    if (!csvMode) {
      console.log(JSON.stringify(results, null, 2));
    }
  } else {
    let url = args[0];
    if (!url.startsWith('http')) url = 'https://' + url;
    const r = await detectSearch(url, options);
    console.log(JSON.stringify(r, null, 2));
  }
}

main().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
