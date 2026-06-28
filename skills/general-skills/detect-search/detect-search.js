#!/usr/bin/env node
// detect-search.js — Deterministic search platform detector via Playwright network capture.
// Sniffs network traffic, identifies which search API a website calls, extracts deep platform details.
// No LLM calls. Pure pattern matching.

const { chromium } = require('playwright');

// --- Platform registry: URL patterns + deep extraction logic per platform ---
const PLATFORMS = [
  {
    id: 'algolia', name: 'Algolia',
    urlPatterns: ['.algolia.net', '.algolia.com/1/', 'x-algolia-agent=', 'x-algolia-application-id=', '/1/indexes/*/queries'],
    headerKeys: ['x-algolia-application-id', 'x-algolia-api-key'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        if (!details.app_id) {
          const m = h.url.match(/https?:\/\/([A-Z0-9]{10,})-(?:\d+\.)?(?:dsn\.)?algolia(?:net)?\.(?:net|com)/i);
          if (m) details.app_id = m[1].toUpperCase();
        }
        if (!details.app_id) {
          const p = h.url.match(/[?&]x-algolia-application-id=([A-Z0-9]+)/i);
          if (p) details.app_id = p[1].toUpperCase();
        }
        if (!details.app_id && h.headers['x-algolia-application-id']) {
          details.app_id = h.headers['x-algolia-application-id'].toUpperCase();
        }
        if (!details.api_key && h.headers['x-algolia-api-key']) {
          details.api_key = h.headers['x-algolia-api-key'];
        }
        if (!details.api_key) {
          const k = h.url.match(/[?&]x-algolia-api-key=([a-f0-9]+)/i);
          if (k) details.api_key = k[1];
        }
        const agent = h.url.match(/[?&]x-algolia-agent=([^&]+)/i);
        if (agent && !details.agent) details.agent = decodeURIComponent(agent[1]);
        if (h.body && typeof h.body === 'object') {
          if (h.body.requests) {
            details.indexes = [...new Set(h.body.requests.map(r => r.indexName).filter(Boolean))];
            const q = h.body.requests.find(r => r.params && r.params.includes('query='));
            if (q) {
              const qm = q.params.match(/query=([^&]*)/);
              if (qm) details.query = decodeURIComponent(qm[1]);
            }
          }
          if (h.body.query !== undefined) details.query = h.body.query;
        }
      }
      return details;
    },
  },
  {
    id: 'constructor_io', name: 'Constructor.io',
    urlPatterns: ['cnstrc.com', 'constructor.io'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        const key = h.url.match(/[?&]key=([^&]+)/);
        if (key && !details.api_key) details.api_key = key[1];
        const section = h.url.match(/[?&]section=([^&]+)/i);
        if (section && !details.section) details.section = decodeURIComponent(section[1]);
        const q = h.url.match(/[?&]q(?:uery)?=([^&]+)/i);
        if (q && !details.query) details.query = decodeURIComponent(q[1]);
        const c = h.url.match(/[?&]c=([^&]+)/);
        if (c && !details.client) details.client = decodeURIComponent(c[1]);
        if (h.url.includes('/autocomplete/')) details.endpoint_type = 'autocomplete';
        if (h.url.includes('/search')) details.endpoint_type = 'search';
        if (h.url.includes('/recommendations/')) details.endpoint_type = 'recommendations';
        if (h.url.includes('/browse/')) details.endpoint_type = 'browse';
      }
      return details;
    },
  },
  {
    id: 'coveo', name: 'Coveo',
    urlPatterns: ['coveo.com', 'cloud.coveo', 'platform.cloud.coveo'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        const org = h.url.match(/https?:\/\/([^.]+)\.org\.coveo\.com/i);
        if (org && !details.org_id) details.org_id = org[1];
        if (h.headers['authorization'] && !details.access_token) {
          details.access_token = h.headers['authorization'].replace(/^Bearer\s+/i, '').substring(0, 20) + '...';
        }
        const hub = h.url.match(/[?&]searchHub=([^&]+)/i);
        if (hub && !details.search_hub) details.search_hub = decodeURIComponent(hub[1]);
        if (h.body && h.body.q !== undefined) details.query = h.body.q;
      }
      return details;
    },
  },
  {
    id: 'bloomreach', name: 'Bloomreach',
    urlPatterns: ['bloomreach', 'brcloud', 'brapi.com'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        const acct = h.url.match(/[?&]account_id=([^&]+)/i);
        if (acct && !details.account_id) details.account_id = acct[1];
        const dk = h.url.match(/[?&]domain_key=([^&]+)/i);
        if (dk && !details.domain_key) details.domain_key = dk[1];
        const q = h.url.match(/[?&]q=([^&]+)/i);
        if (q && !details.query) details.query = decodeURIComponent(q[1]);
        const auth = h.url.match(/[?&]auth_key=([^&]+)/i);
        if (auth && !details.auth_key) details.auth_key = auth[1];
      }
      return details;
    },
  },
  {
    id: 'yext', name: 'Yext',
    urlPatterns: ['yext.com', 'liveapi.yext'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        const key = h.url.match(/[?&]api_key=([^&]+)/i);
        if (key && !details.api_key) details.api_key = key[1];
        const exp = h.url.match(/[?&]experienceKey=([^&]+)/i);
        if (exp && !details.experience_key) details.experience_key = exp[1];
        const locale = h.url.match(/[?&]locale=([^&]+)/i);
        if (locale && !details.locale) details.locale = locale[1];
        const q = h.url.match(/[?&]input=([^&]+)/i);
        if (q && !details.query) details.query = decodeURIComponent(q[1]);
        const v = h.url.match(/[?&]v=([^&]+)/i);
        if (v && !details.api_version) details.api_version = v[1];
      }
      return details;
    },
  },
  {
    id: 'searchspring', name: 'Searchspring',
    urlPatterns: ['searchspring.net'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        const site = h.url.match(/[?&]siteId=([^&]+)/i);
        if (site && !details.site_id) details.site_id = site[1];
        const q = h.url.match(/[?&]q=([^&]+)/i);
        if (q && !details.query) details.query = decodeURIComponent(q[1]);
      }
      return details;
    },
  },
  {
    id: 'klevu', name: 'Klevu',
    urlPatterns: ['klevu.com'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        const key = h.url.match(/[?&]ticket=([^&]+)/i);
        if (key && !details.api_key) details.api_key = key[1];
        if (h.body && h.body.term) details.query = h.body.term;
      }
      return details;
    },
  },
  {
    id: 'typesense', name: 'Typesense',
    urlPatterns: ['typesense.org', 'cloud.typesense'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        if (h.headers['x-typesense-api-key'] && !details.api_key) details.api_key = h.headers['x-typesense-api-key'];
        const coll = h.url.match(/\/collections\/([^/]+)/);
        if (coll && !details.collection) details.collection = coll[1];
        const q = h.url.match(/[?&]q=([^&]+)/i);
        if (q && !details.query) details.query = decodeURIComponent(q[1]);
      }
      return details;
    },
  },
  {
    id: 'elasticsearch', name: 'Elasticsearch',
    urlPatterns: ['elasticsearch.com', '/_search?', ':9200/', 'elastic-cloud.com'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        const idx = h.url.match(/\/([^/]+)\/_search/);
        if (idx && !details.index) details.index = idx[1];
        if (h.body && h.body.query) details.query_dsl = JSON.stringify(h.body.query).substring(0, 200);
      }
      return details;
    },
  },
  {
    id: 'meilisearch', name: 'Meilisearch',
    urlPatterns: ['meilisearch.com', '/indexes/', 'meilisearch'],
    headerKeys: ['x-meili-api-key'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        if (h.headers['x-meili-api-key'] && !details.api_key) details.api_key = h.headers['x-meili-api-key'];
        const idx = h.url.match(/\/indexes\/([^/]+)/);
        if (idx && !details.index) details.index = idx[1];
        if (h.body && h.body.q !== undefined) details.query = h.body.q;
      }
      return details;
    },
  },
  {
    id: 'unbxd', name: 'Unbxd (Netcore)',
    urlPatterns: ['unbxd.io', 'unbxdapi.com'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        const q = h.url.match(/[?&]q=([^&]+)/i);
        if (q && !details.query) details.query = decodeURIComponent(q[1]);
      }
      return details;
    },
  },
  {
    id: 'doofinder', name: 'Doofinder',
    urlPatterns: ['doofinder.com'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        const hash = h.url.match(/\/5\/search\/([a-f0-9]+)/);
        if (hash && !details.hash_id) details.hash_id = hash[1];
        const q = h.url.match(/[?&]query=([^&]+)/i);
        if (q && !details.query) details.query = decodeURIComponent(q[1]);
      }
      return details;
    },
  },
  {
    id: 'swiftype', name: 'Swiftype (Elastic)',
    urlPatterns: ['swiftype.com'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        const eng = h.url.match(/\/engines\/([^/]+)/);
        if (eng && !details.engine) details.engine = eng[1];
        if (h.body && h.body.query) details.query = h.body.query;
      }
      return details;
    },
  },
  {
    id: 'google_retail', name: 'Google Retail Search',
    urlPatterns: ['retail.googleapis.com', 'discoveryengine.googleapis.com'],
    extract: (hits) => {
      const details = {};
      for (const h of hits) {
        const proj = h.url.match(/projects\/([^/]+)/);
        if (proj && !details.project_id) details.project_id = proj[1];
        if (h.body && h.body.query) details.query = h.body.query;
      }
      return details;
    },
  },
  // Automotive-specific
  { id: 'cars_commerce', name: 'Cars Commerce Proprietary', urlPatterns: ['websites-search.api.carscommerce.inc'], extract: defaultExtract },
  { id: 'dealer_com', name: 'Dealer.com (Cox Automotive)', urlPatterns: ['dealer.com/api', 'ddc.com'], extract: defaultExtract },
  { id: 'dealersocket', name: 'DealerSocket', urlPatterns: ['dealersocket.com'], extract: defaultExtract },
  { id: 'ridemotive', name: 'RideMotive', urlPatterns: ['ridemotive.com'], extract: defaultExtract },
  { id: 'dealer_inspire', name: 'Dealer Inspire (Cars Commerce)', urlPatterns: ['onlineshopper.dealerinspire.com'], extract: defaultExtract },
  { id: 'dealereprocess', name: 'DealerEProcess', urlPatterns: ['dealereprocess.org'], extract: defaultExtract },
  // Additional platforms
  { id: 'hawksearch', name: 'HawkSearch', urlPatterns: ['hawksearch.com'], extract: defaultExtract },
  { id: 'groupby', name: 'GroupBy', urlPatterns: ['groupbycloud.com'], extract: defaultExtract },
  { id: 'attraqt', name: 'Attraqt (Crownpeak)', urlPatterns: ['attraqt.com', 'crownpeak.com'], extract: defaultExtract },
  { id: 'empathy', name: 'Empathy.co', urlPatterns: ['empathy.co', 'empathybroker'], extract: defaultExtract },
  { id: 'nosto', name: 'Nosto', urlPatterns: ['nosto.com'], extract: defaultExtract },
  { id: 'syte', name: 'Syte', urlPatterns: ['syte.ai'], extract: defaultExtract },
  { id: 'addsearch', name: 'AddSearch', urlPatterns: ['addsearch.com'], extract: defaultExtract },
  { id: 'lucidworks', name: 'Lucidworks', urlPatterns: ['lucidworks.com', 'app.lucidworks'], extract: defaultExtract },
  { id: 'loop54', name: 'Loop54', urlPatterns: ['loop54.com'], extract: defaultExtract },
  { id: 'sajari', name: 'Sajari (Search.io)', urlPatterns: ['sajari.com', 'search.io'], extract: defaultExtract },
  { id: 'bonsai', name: 'Bonsai (Oramasearch)', urlPatterns: ['bonsai.io', 'orama.run'], extract: defaultExtract },
  { id: 'cludo', name: 'Cludo', urlPatterns: ['cludo.com'], extract: defaultExtract },
  { id: 'fastsimon', name: 'Fast Simon', urlPatterns: ['fast.co/search', 'fastsimon.com'], extract: defaultExtract },
];

function defaultExtract(hits) {
  const details = {};
  for (const h of hits) {
    const q = h.url.match(/[?&]q(?:uery)?=([^&]+)/i);
    if (q && !details.query) details.query = decodeURIComponent(q[1]);
    if (h.body && typeof h.body === 'object') {
      if (h.body.query && !details.query) details.query = h.body.query;
      if (h.body.q && !details.query) details.query = h.body.q;
    }
  }
  return details;
}

const SEARCH_URL_SIGNALS = [
  '/search', '/inventory', '/listings', '/query',
  '/suggest', '/autocomplete', '/typeahead', '/facet',
  'api/search', 'api/v1/search', 'api/v1/listings',
  '/instant-search', '/site-search', '/recommendations',
];

const NOISE_DOMAINS = [
  'google-analytics.com', 'analytics.google.com', 'googletagmanager.com',
  'facebook.com', 'doubleclick.net', 'googlesyndication.com',
  'google.com/measurement', 'google.com/pagead', 'bing.com/bat',
  'clarity.ms', 'hotjar.com', 'newrelic.com', 'nr-data.net',
  'sentry.io', 'segment.com', 'cdn.segment.com',
  'fonts.googleapis.com', 'fonts.gstatic.com',
];

const DI_FINGERPRINTS = [
  'dealerinspire.com', 'di-uploads-pod', 'di-shared-assets',
  'Advanced Automotive Dealer Websites by Dealer Inspire',
];

function identifyPlatform(url) {
  const lower = url.toLowerCase();
  for (const p of PLATFORMS) {
    if (p.urlPatterns.some(pat => lower.includes(pat.toLowerCase()))) return p;
  }
  return null;
}

function isSearchRelated(url) {
  const lower = url.toLowerCase();
  if (NOISE_DOMAINS.some(d => lower.includes(d))) return false;
  return SEARCH_URL_SIGNALS.some(sig => lower.includes(sig));
}

function safePostData(request) {
  try {
    const data = request.postData();
    if (!data) return null;
    try { return JSON.parse(data); } catch { return data.substring(0, 1000); }
  } catch { return null; }
}

function safeHeaders(request) {
  try { return request.headers(); } catch { return {}; }
}

// --- Main detection function ---
async function detectSearch(targetUrl, options = {}) {
  const { timeout = 30000, waitAfterLoad = 5000, typeQuery = 'test', noSearch = false } = options;

  const result = {
    url: targetUrl,
    search_detected: false,
    search_platform: null,
    platform_id: null,
    platform_details: {},
    all_platforms_found: [],
    search_requests: [],
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

    const allRequestCount = { n: 0 };
    const platformHits = new Map(); // id -> { platform, hits: [{ url, method, headers, body }] }
    const searchRequests = [];

    page.on('request', req => {
      allRequestCount.n++;
      const url = req.url();
      const headers = safeHeaders(req);
      const body = safePostData(req);
      const method = req.method();

      const platform = identifyPlatform(url);
      if (platform) {
        const key = platform.id;
        if (!platformHits.has(key)) platformHits.set(key, { platform, hits: [] });
        platformHits.get(key).hits.push({ url, method, headers, body });
      }

      // Also check headers for platform-specific keys (catches proxied setups)
      for (const p of PLATFORMS) {
        if (p.headerKeys && !platformHits.has(p.id)) {
          for (const hk of p.headerKeys) {
            if (headers[hk]) {
              if (!platformHits.has(p.id)) platformHits.set(p.id, { platform: p, hits: [] });
              platformHits.get(p.id).hits.push({ url, method, headers, body });
              break;
            }
          }
        }
      }

      if (isSearchRelated(url) && (req.resourceType() === 'xhr' || req.resourceType() === 'fetch' || req.resourceType() === 'document')) {
        searchRequests.push({ url: url.substring(0, 300), method, body_preview: body ? JSON.stringify(body).substring(0, 200) : null });
      }
    });

    await page.goto(targetUrl, { waitUntil: 'domcontentloaded', timeout });
    await page.waitForTimeout(waitAfterLoad);

    // --- Search interaction (always on unless --no-search) ---
    if (typeQuery && !noSearch) {
      let typed = false;
      const log = (msg) => process.stderr.write(`  [search] ${msg}\n`);

      const searchToggleSelectors = [
        'button[aria-label*="search" i]', 'a[aria-label*="search" i]',
        '[data-testid*="search" i]',
        '.search-icon', '.search-toggle', '.search-button',
        'button.search', 'a.search',
        '[class*="SearchIcon"]', '[class*="search-icon"]',
        'svg[class*="search" i]', 'header button:has(svg)',
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

      const searchInputSelectors = [
        'input[type="search"]', 'input[name*="search" i]',
        'input[placeholder*="search" i]', 'input[id*="search" i]',
        'input[aria-label*="search" i]', 'input[data-testid*="search" i]',
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

      if (!typed) {
        log('no input found, falling back to /search?q= URL');
        try {
          const base = new URL(targetUrl);
          const searchUrl = `${base.origin}/search?q=${encodeURIComponent(typeQuery)}`;
          await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout });
          await page.waitForTimeout(waitAfterLoad);
          log(`navigated to ${searchUrl}`);
        } catch (e) { log(`fallback nav failed: ${e.message}`); }
      }
    }

    // --- Post-scan analysis ---
    const html = await page.content();
    const title = await page.title();

    result.bot_blocked = title === 'Access Denied'
      || (html.includes('Access Denied') && html.includes("don't have permission"))
      || html.includes('cf-challenge-running') || html.includes('cf_chl_opt')
      || html.includes('Please verify you are a human')
      || html.includes('Checking your browser before accessing');

    result.is_dealer_inspire = DI_FINGERPRINTS.some(fp => html.includes(fp));
    result.network_calls_total = allRequestCount.n;
    result.search_calls_count = searchRequests.length;

    // Build all_platforms_found with deep extraction
    const allPlatforms = [];
    for (const [id, val] of platformHits) {
      if (id === 'dealer_inspire') continue; // DI is a site fingerprint, not a search platform
      const extracted = val.platform.extract(val.hits);
      allPlatforms.push({
        id,
        name: val.platform.name,
        hit_count: val.hits.length,
        sample_endpoint: val.hits[0].url.substring(0, 300),
        details: extracted,
      });
    }

    // Also check HTML source for platform JS bundles
    const htmlLower = html.toLowerCase();
    const htmlPlatformChecks = [
      { id: 'algolia', patterns: ['algolia.net', 'algoliasearch', 'algolianet'] },
      { id: 'constructor_io', patterns: ['cnstrc.com', 'constructor.io'] },
      { id: 'coveo', patterns: ['coveo.com', 'coveo/headless'] },
      { id: 'bloomreach', patterns: ['bloomreach', 'pathfora'] },
      { id: 'searchspring', patterns: ['searchspring'] },
      { id: 'klevu', patterns: ['klevu.com'] },
      { id: 'typesense', patterns: ['typesense'] },
      { id: 'doofinder', patterns: ['doofinder'] },
      { id: 'yext', patterns: ['yext.com', 'yextpages'] },
    ];
    for (const check of htmlPlatformChecks) {
      if (!allPlatforms.find(p => p.id === check.id) && check.patterns.some(pat => htmlLower.includes(pat))) {
        allPlatforms.push({
          id: check.id,
          name: PLATFORMS.find(p => p.id === check.id)?.name || check.id,
          hit_count: 0,
          sample_endpoint: null,
          details: { detection_method: 'html_source_only' },
        });
      }
    }

    result.all_platforms_found = allPlatforms;

    // Pick primary platform (most network hits, exclude DI fingerprints)
    if (allPlatforms.length > 0) {
      const primary = allPlatforms.sort((a, b) => b.hit_count - a.hit_count)[0];
      result.search_detected = true;
      result.search_platform = primary.name;
      result.platform_id = primary.id;
      result.platform_details = primary.details;
    }

    // Capture unidentified search traffic
    if (searchRequests.length > 0) {
      result.search_requests = searchRequests.slice(0, 10);
      if (!result.search_detected) {
        result.search_detected = true;
        result.search_platform = 'Proprietary / Unidentified';
        result.platform_id = 'unknown';
        result.platform_details = { first_endpoint: searchRequests[0].url };
      }
    }

    await browser.close();
  } catch (err) {
    result.error = err.message;
    if (browser) try { await browser.close(); } catch {}
  }

  return result;
}

// --- CLI ---
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help')) {
    console.log(`
detect-search — Identify which search platform a website uses by sniffing network traffic.

Usage:
  node detect-search.js <url>                        Detect search platform (types "test" by default)
  node detect-search.js <url> --type-query "shoes"   Use specific search term
  node detect-search.js <url> --no-search            Page-load traffic only
  node detect-search.js --file <path>                Bulk mode, one URL per line
  node detect-search.js --file <path> --csv          Bulk CSV output

Options:
  --type-query <q>    Search term (default: "test")
  --no-search         Skip search interaction
  --file <path>       Bulk mode
  --csv               CSV output (bulk only)
  --timeout <ms>      Nav timeout (default: 30000)
  --wait <ms>         Post-load wait (default: 5000)
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
      .split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('#'));

    if (csvMode) {
      console.log('url,search_detected,platform_id,search_platform,platform_details,search_calls_count,bot_blocked,is_dealer_inspire,error');
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
          esc(r.url), r.search_detected, esc(r.platform_id),
          esc(r.search_platform), esc(JSON.stringify(r.platform_details)),
          r.search_calls_count, r.bot_blocked, r.is_dealer_inspire, esc(r.error),
        ].join(','));
      }
    }

    if (!csvMode) console.log(JSON.stringify(results, null, 2));
  } else {
    let url = args[0];
    if (!url.startsWith('http')) url = 'https://' + url;
    const r = await detectSearch(url, options);
    console.log(JSON.stringify(r, null, 2));
  }
}

main().catch(err => { console.error('Fatal:', err.message); process.exit(1); });
