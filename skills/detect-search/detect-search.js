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

// === FULL TECH STACK SIGNATURES ===
// Hand-curated high-precision signatures for ~60 audit-relevant technologies.
// match_type: 'url'            → matches against any request URL
//             'response_header'→ matches response header key (+ optional value_pattern)
//             'html'           → matches page HTML source
//             'cookie'         → matches cookie name pattern
// confidence: 'confirmed' = network/header/cookie hit; 'likely' = HTML-only reference
const TECH_SIGNATURES = {
  ecommerce_platform: [
    {
      id: 'shopify', name: 'Shopify',
      rules: [
        { match_type: 'url', pattern: /cdn\.shopify\.com/i, evidence_hint: 'Shopify CDN URL' },
        { match_type: 'url', pattern: /myshopify\.com/i, evidence_hint: 'Shopify storefront domain' },
        { match_type: 'url', pattern: /\.shopifycdn\.com/i, evidence_hint: 'Shopify CDN alias' },
        { match_type: 'html', pattern: /Shopify\.theme\b/i, evidence_hint: 'Shopify.theme global in HTML' },
        { match_type: 'html', pattern: /cdn\.shopify\.com/i, evidence_hint: 'Shopify CDN in HTML source' },
      ],
    },
    {
      id: 'sfcc', name: 'Salesforce Commerce Cloud (SFCC)',
      rules: [
        { match_type: 'url', pattern: /\.demandware\.net/i, evidence_hint: 'Demandware/SFCC CDN' },
        { match_type: 'url', pattern: /dx\.commercecloud\.salesforce\.com/i, evidence_hint: 'SFCC API URL' },
        { match_type: 'url', pattern: /\/on\/demandware\./i, evidence_hint: 'Demandware request path' },
        { match_type: 'html', pattern: /demandware\.static\b/i, evidence_hint: 'Demandware static in HTML' },
        { match_type: 'html', pattern: /salesforcecommerce/i, evidence_hint: 'SFCC reference in HTML' },
      ],
    },
    {
      id: 'magento', name: 'Adobe Commerce / Magento',
      rules: [
        { match_type: 'url', pattern: /\/static\/version\d+\//i, evidence_hint: 'Magento versioned static path' },
        { match_type: 'url', pattern: /\/mage\/cookies\.js/i, evidence_hint: 'Magento cookie JS' },
        { match_type: 'html', pattern: /"Magento_[A-Za-z]+"/i, evidence_hint: 'Magento module ref in HTML' },
        { match_type: 'html', pattern: /\bMage\.Cookies\b/i, evidence_hint: 'Mage.Cookies global in HTML' },
      ],
    },
    {
      id: 'bigcommerce', name: 'BigCommerce',
      rules: [
        { match_type: 'url', pattern: /cdn\.bigcommerce\.com/i, evidence_hint: 'BigCommerce CDN URL' },
        { match_type: 'url', pattern: /\.bigcommerce\.com\/api\//i, evidence_hint: 'BigCommerce API URL' },
        { match_type: 'html', pattern: /window\.BCData\b/i, evidence_hint: 'BigCommerce BCData global in HTML' },
        { match_type: 'html', pattern: /cdn\.bigcommerce\.com/i, evidence_hint: 'BigCommerce CDN in HTML' },
      ],
    },
    {
      id: 'commercetools', name: 'commercetools',
      rules: [
        { match_type: 'url', pattern: /api\.commercetools\.(com|io)/i, evidence_hint: 'commercetools API URL' },
        { match_type: 'url', pattern: /\.commercetools\.(com|io)\//i, evidence_hint: 'commercetools endpoint' },
      ],
    },
    {
      id: 'shopware', name: 'Shopware',
      rules: [
        { match_type: 'url', pattern: /shopware\.js/i, evidence_hint: 'Shopware JS bundle URL' },
        { match_type: 'url', pattern: /shopware-storefront/i, evidence_hint: 'Shopware storefront URL' },
        { match_type: 'html', pattern: /shopware-storefront/i, evidence_hint: 'Shopware storefront class in HTML' },
        { match_type: 'html', pattern: /window\.shopware\b/i, evidence_hint: 'Shopware global in HTML' },
        { match_type: 'cookie', pattern: /^sw-cache-hash$/i, evidence_hint: 'Shopware sw-cache-hash cookie' },
      ],
    },
    {
      id: 'sap_commerce', name: 'SAP Commerce Cloud',
      rules: [
        { match_type: 'url', pattern: /hybris\.com/i, evidence_hint: 'SAP Hybris URL' },
        { match_type: 'url', pattern: /\/occ\/v\d+\//i, evidence_hint: 'SAP OCC REST API path' },
        { match_type: 'html', pattern: /hybrisDataLayer/i, evidence_hint: 'SAP Hybris dataLayer in HTML' },
        { match_type: 'html', pattern: /sap-ui-bootstrap/i, evidence_hint: 'SAP UI5 bootstrap in HTML' },
      ],
    },
    {
      id: 'oracle_commerce', name: 'Oracle Commerce Cloud',
      rules: [
        { match_type: 'url', pattern: /\.oraclecloud\.com.*\/ccstore\//i, evidence_hint: 'Oracle Commerce Cloud API' },
        { match_type: 'url', pattern: /\/ccstorex?\//i, evidence_hint: 'Oracle CCStore URL path' },
        { match_type: 'html', pattern: /OracleCommerceCloud\b/i, evidence_hint: 'Oracle Commerce global in HTML' },
      ],
    },
  ],
  analytics: [
    {
      id: 'ga4', name: 'Google Analytics 4 (GA4)',
      rules: [
        { match_type: 'url', pattern: /google-analytics\.com\/g\/collect/i, evidence_hint: 'GA4 collect endpoint' },
        { match_type: 'url', pattern: /analytics\.google\.com\/g\/collect/i, evidence_hint: 'GA4 via analytics.google.com' },
        { match_type: 'url', pattern: /googletagmanager\.com\/gtag\/js\?id=G-/i, evidence_hint: 'gtag.js with GA4 G- measurement ID' },
        { match_type: 'html', pattern: /gtag\('config',\s*'G-/i, evidence_hint: "GA4 gtag('config','G-...) in HTML" },
      ],
    },
    {
      id: 'adobe_analytics', name: 'Adobe Analytics',
      rules: [
        { match_type: 'url', pattern: /\.omtrdc\.net/i, evidence_hint: 'Adobe Analytics omtrdc.net beacon' },
        { match_type: 'url', pattern: /\.2o7\.net/i, evidence_hint: 'Adobe Analytics 2o7.net beacon' },
        { match_type: 'url', pattern: /adobedtm\.com.*satelliteLib/i, evidence_hint: 'Adobe DTM satelliteLib URL' },
        { match_type: 'html', pattern: /AppMeasurement\b/i, evidence_hint: 'Adobe AppMeasurement in HTML' },
      ],
    },
    {
      id: 'segment', name: 'Segment',
      rules: [
        { match_type: 'url', pattern: /cdn\.segment\.com/i, evidence_hint: 'Segment CDN URL' },
        { match_type: 'url', pattern: /api\.segment\.io/i, evidence_hint: 'Segment events API URL' },
        { match_type: 'url', pattern: /evs\.segment\.com/i, evidence_hint: 'Segment event server URL' },
        { match_type: 'html', pattern: /analytics\.js.*segment\.com/i, evidence_hint: 'Segment analytics.js in HTML' },
      ],
    },
    {
      id: 'amplitude', name: 'Amplitude',
      rules: [
        { match_type: 'url', pattern: /api\.amplitude\.com/i, evidence_hint: 'Amplitude API URL' },
        { match_type: 'url', pattern: /cdn\.amplitude\.com/i, evidence_hint: 'Amplitude CDN URL' },
        { match_type: 'html', pattern: /amplitude\.getInstance\b/i, evidence_hint: 'Amplitude getInstance() in HTML' },
        { match_type: 'html', pattern: /amplitude\.init\b/i, evidence_hint: 'amplitude.init() in HTML' },
      ],
    },
    {
      id: 'mixpanel', name: 'Mixpanel',
      rules: [
        { match_type: 'url', pattern: /api\.mixpanel\.com/i, evidence_hint: 'Mixpanel API URL' },
        { match_type: 'url', pattern: /cdn\.mxpnl\.com/i, evidence_hint: 'Mixpanel CDN URL' },
        { match_type: 'html', pattern: /mixpanel\.init\(/i, evidence_hint: 'mixpanel.init() call in HTML' },
      ],
    },
    {
      id: 'heap', name: 'Heap Analytics',
      rules: [
        { match_type: 'url', pattern: /cdn\.heapanalytics\.com/i, evidence_hint: 'Heap CDN URL' },
        { match_type: 'url', pattern: /heapanalytics\.com\/h\b/i, evidence_hint: 'Heap capture endpoint' },
        { match_type: 'html', pattern: /heap\.load\(/i, evidence_hint: 'heap.load() call in HTML' },
      ],
    },
  ],
  tag_manager: [
    {
      id: 'gtm', name: 'Google Tag Manager',
      rules: [
        { match_type: 'url', pattern: /googletagmanager\.com\/gtm\.js/i, evidence_hint: 'GTM script URL' },
        { match_type: 'url', pattern: /googletagmanager\.com\/ns\.html/i, evidence_hint: 'GTM no-script iframe URL' },
        { match_type: 'html', pattern: /googletagmanager\.com\/gtm\.js/i, evidence_hint: 'GTM script tag in HTML' },
      ],
    },
    {
      id: 'tealium', name: 'Tealium',
      rules: [
        { match_type: 'url', pattern: /tags\.tiqcdn\.com/i, evidence_hint: 'Tealium TIQ CDN URL' },
        { match_type: 'url', pattern: /collect\.tealiumiq\.com/i, evidence_hint: 'Tealium Collect API URL' },
        { match_type: 'html', pattern: /utag\.js\b/i, evidence_hint: 'Tealium utag.js in HTML' },
        { match_type: 'html', pattern: /tealiumiq\.com/i, evidence_hint: 'Tealium TIQ reference in HTML' },
      ],
    },
    {
      id: 'adobe_launch', name: 'Adobe Launch / Experience Platform Tags',
      rules: [
        { match_type: 'url', pattern: /assets\.adobedtm\.com/i, evidence_hint: 'Adobe DTM/Launch CDN URL' },
        { match_type: 'url', pattern: /launch-[a-f0-9]{20,}\.min\.js/i, evidence_hint: 'Adobe Launch bundle URL' },
        { match_type: 'html', pattern: /assets\.adobedtm\.com/i, evidence_hint: 'Adobe DTM CDN in HTML' },
      ],
    },
  ],
  cdn_waf: [
    {
      id: 'cloudflare', name: 'Cloudflare',
      rules: [
        { match_type: 'response_header', header: 'cf-ray', evidence_hint: 'Cloudflare cf-ray header' },
        { match_type: 'response_header', header: 'cf-cache-status', evidence_hint: 'Cloudflare cf-cache-status header' },
        { match_type: 'response_header', header: 'server', value_pattern: /^cloudflare$/i, evidence_hint: 'Server: cloudflare header' },
        { match_type: 'url', pattern: /\.cloudflare\.com\//i, evidence_hint: 'Cloudflare asset URL' },
      ],
    },
    {
      id: 'akamai', name: 'Akamai',
      rules: [
        { match_type: 'url', pattern: /\.akamaized\.net/i, evidence_hint: 'Akamai CDN URL (akamaized.net)' },
        { match_type: 'url', pattern: /\.akamai\.net/i, evidence_hint: 'Akamai CDN URL (akamai.net)' },
        { match_type: 'url', pattern: /\.akamaihd\.net/i, evidence_hint: 'Akamai HD CDN URL' },
        { match_type: 'response_header', header: 'x-check-cacheable', evidence_hint: 'Akamai x-check-cacheable header' },
        { match_type: 'response_header', header: 'x-akamai-transformed', evidence_hint: 'Akamai x-akamai-transformed header' },
        { match_type: 'response_header', header: 'x-akamai-request-id', evidence_hint: 'Akamai x-akamai-request-id header' },
      ],
    },
    {
      id: 'fastly', name: 'Fastly',
      rules: [
        { match_type: 'response_header', header: 'x-fastly-request-id', evidence_hint: 'Fastly x-fastly-request-id header' },
        { match_type: 'response_header', header: 'x-served-by', value_pattern: /cache-/i, evidence_hint: 'Fastly x-served-by cache- header' },
        { match_type: 'response_header', header: 'fastly-restarts', evidence_hint: 'Fastly fastly-restarts header' },
        { match_type: 'url', pattern: /\.fastly\.net\//i, evidence_hint: 'Fastly CDN URL' },
      ],
    },
    {
      id: 'imperva', name: 'Imperva / Incapsula',
      rules: [
        { match_type: 'response_header', header: 'x-iinfo', evidence_hint: 'Imperva x-iinfo header' },
        { match_type: 'cookie', pattern: /^incap_ses_/i, evidence_hint: 'Imperva incap_ses session cookie' },
        { match_type: 'cookie', pattern: /^visid_incap_/i, evidence_hint: 'Imperva visid_incap visitor cookie' },
        { match_type: 'url', pattern: /\.imperva\.com\//i, evidence_hint: 'Imperva resource URL' },
        { match_type: 'url', pattern: /\.incapsula\.com\//i, evidence_hint: 'Incapsula resource URL' },
      ],
    },
  ],
  personalization: [
    {
      id: 'dynamic_yield', name: 'Dynamic Yield',
      rules: [
        { match_type: 'url', pattern: /cdn\.dynamicyield\.com/i, evidence_hint: 'Dynamic Yield CDN URL' },
        { match_type: 'url', pattern: /dy-api\.com/i, evidence_hint: 'Dynamic Yield API URL' },
        { match_type: 'url', pattern: /\.dynamicyield\.com/i, evidence_hint: 'Dynamic Yield URL' },
        { match_type: 'html', pattern: /DYO\.init\b/i, evidence_hint: 'Dynamic Yield DYO.init in HTML' },
      ],
    },
    {
      id: 'monetate', name: 'Monetate',
      rules: [
        { match_type: 'url', pattern: /\.monetate\.net/i, evidence_hint: 'Monetate CDN/API URL' },
        { match_type: 'url', pattern: /monetate-engine\.com/i, evidence_hint: 'Monetate engine URL' },
        { match_type: 'html', pattern: /monetateConstants\b/i, evidence_hint: 'Monetate constants in HTML' },
      ],
    },
    {
      id: 'nosto', name: 'Nosto',
      rules: [
        { match_type: 'url', pattern: /connect\.nosto\.com/i, evidence_hint: 'Nosto connect API URL' },
        { match_type: 'url', pattern: /nosto\.com\/include\//i, evidence_hint: 'Nosto include URL' },
        { match_type: 'html', pattern: /nostojs\(/i, evidence_hint: 'nostojs() call in HTML' },
      ],
    },
    {
      id: 'algolia_recommend', name: 'Algolia Recommend',
      rules: [
        { match_type: 'url', pattern: /algolia(?:net)?\.(?:net|com).*\/1\/recommend/i, evidence_hint: 'Algolia Recommend API endpoint' },
        { match_type: 'url', pattern: /algolia(?:net)?\.(?:net|com).*\/recommendations/i, evidence_hint: 'Algolia Recommend recommendations endpoint' },
        { match_type: 'html', pattern: /@algolia\/recommend\b/i, evidence_hint: '@algolia/recommend npm ref in HTML' },
      ],
    },
    {
      id: 'richrelevance', name: 'RichRelevance / Salsify',
      rules: [
        { match_type: 'url', pattern: /recs\.richrelevance\.com/i, evidence_hint: 'RichRelevance recs API URL' },
        { match_type: 'url', pattern: /richrelevance\.com/i, evidence_hint: 'RichRelevance URL' },
        { match_type: 'html', pattern: /R3_COMMON\b/i, evidence_hint: 'RichRelevance R3_COMMON global in HTML' },
      ],
    },
  ],
  reviews_ugc: [
    {
      id: 'bazaarvoice', name: 'Bazaarvoice',
      rules: [
        { match_type: 'url', pattern: /api\.bazaarvoice\.com/i, evidence_hint: 'Bazaarvoice API URL' },
        { match_type: 'url', pattern: /\.bazaarvoice\.com/i, evidence_hint: 'Bazaarvoice CDN/API URL' },
        { match_type: 'url', pattern: /bvapi\.com/i, evidence_hint: 'Bazaarvoice bvapi.com URL' },
        { match_type: 'html', pattern: /BVRRContainer\b/i, evidence_hint: 'Bazaarvoice BVRRContainer in HTML' },
      ],
    },
    {
      id: 'yotpo', name: 'Yotpo',
      rules: [
        { match_type: 'url', pattern: /staticw2\.yotpo\.com/i, evidence_hint: 'Yotpo static widget CDN URL' },
        { match_type: 'url', pattern: /api\.yotpo\.com/i, evidence_hint: 'Yotpo API URL' },
        { match_type: 'html', pattern: /yotpo\.com/i, evidence_hint: 'Yotpo reference in HTML' },
      ],
    },
    {
      id: 'powerreviews', name: 'PowerReviews',
      rules: [
        { match_type: 'url', pattern: /powerreviews\.com/i, evidence_hint: 'PowerReviews URL' },
        { match_type: 'html', pattern: /POWERREVIEWS\b/i, evidence_hint: 'POWERREVIEWS global in HTML' },
        { match_type: 'html', pattern: /powerreviews/i, evidence_hint: 'PowerReviews reference in HTML' },
      ],
    },
    {
      id: 'trustpilot', name: 'Trustpilot',
      rules: [
        { match_type: 'url', pattern: /widget\.trustpilot\.com/i, evidence_hint: 'Trustpilot widget URL' },
        { match_type: 'url', pattern: /invitations\.trustpilot\.com/i, evidence_hint: 'Trustpilot invitations API URL' },
        { match_type: 'html', pattern: /trustpilot\.com/i, evidence_hint: 'Trustpilot reference in HTML' },
      ],
    },
  ],
  consent_cmp: [
    {
      id: 'onetrust', name: 'OneTrust',
      rules: [
        { match_type: 'url', pattern: /cdn\.cookielaw\.org/i, evidence_hint: 'OneTrust cookielaw CDN URL' },
        { match_type: 'url', pattern: /onetrust\.com/i, evidence_hint: 'OneTrust URL' },
        { match_type: 'cookie', pattern: /^OptanonConsent$/i, evidence_hint: 'OneTrust OptanonConsent cookie' },
        { match_type: 'cookie', pattern: /^OptanonAlertBoxClosed$/i, evidence_hint: 'OneTrust alert-closed cookie' },
        { match_type: 'html', pattern: /OneTrust\.Init\b/i, evidence_hint: 'OneTrust.Init() in HTML' },
      ],
    },
    {
      id: 'trustarc', name: 'TrustArc',
      rules: [
        { match_type: 'url', pattern: /consent\.trustarc\.com/i, evidence_hint: 'TrustArc consent URL' },
        { match_type: 'url', pattern: /trustarc\.com/i, evidence_hint: 'TrustArc URL' },
        { match_type: 'html', pattern: /truste\.com/i, evidence_hint: 'TRUSTe (TrustArc) reference in HTML' },
      ],
    },
    {
      id: 'cookiebot', name: 'Cookiebot',
      rules: [
        { match_type: 'url', pattern: /consent\.cookiebot\.com/i, evidence_hint: 'Cookiebot consent URL' },
        { match_type: 'url', pattern: /cookiebot\.com/i, evidence_hint: 'Cookiebot URL' },
        { match_type: 'cookie', pattern: /^CookieConsent$/i, evidence_hint: 'Cookiebot CookieConsent cookie' },
      ],
    },
  ],
  ad_pixels: [
    {
      id: 'meta_pixel', name: 'Meta Pixel (Facebook)',
      rules: [
        { match_type: 'url', pattern: /connect\.facebook\.net.*fbevents\.js/i, evidence_hint: 'Facebook fbevents.js loader URL' },
        { match_type: 'url', pattern: /facebook\.com\/tr\b/i, evidence_hint: 'Facebook Pixel tracking pixel URL' },
        { match_type: 'html', pattern: /fbq\('init'/i, evidence_hint: "fbq('init',...) Pixel init in HTML" },
      ],
    },
    {
      id: 'google_ads', name: 'Google Ads',
      rules: [
        { match_type: 'url', pattern: /googletagmanager\.com\/gtag\/js\?id=AW-/i, evidence_hint: 'Google Ads gtag AW- measurement ID' },
        { match_type: 'url', pattern: /google\.com\/pagead\/conversion/i, evidence_hint: 'Google Ads conversion URL' },
        { match_type: 'html', pattern: /gtag\('config',\s*'AW-/i, evidence_hint: "Google Ads gtag('config','AW-...) in HTML" },
      ],
    },
    {
      id: 'criteo', name: 'Criteo',
      rules: [
        { match_type: 'url', pattern: /static\.criteo\.net/i, evidence_hint: 'Criteo static CDN URL' },
        { match_type: 'url', pattern: /dis\.criteo\.com/i, evidence_hint: 'Criteo display network URL' },
        { match_type: 'html', pattern: /criteo_q\.push/i, evidence_hint: 'Criteo queue push in HTML' },
      ],
    },
    {
      id: 'tiktok_pixel', name: 'TikTok Pixel',
      rules: [
        { match_type: 'url', pattern: /analytics\.tiktok\.com/i, evidence_hint: 'TikTok Analytics URL' },
        { match_type: 'url', pattern: /business-api\.tiktok\.com/i, evidence_hint: 'TikTok Business API URL' },
        { match_type: 'html', pattern: /ttq\.load\(/i, evidence_hint: 'ttq.load() TikTok Pixel in HTML' },
      ],
    },
    {
      id: 'pinterest_tag', name: 'Pinterest Tag',
      rules: [
        { match_type: 'url', pattern: /ct\.pinterest\.com/i, evidence_hint: 'Pinterest conversion tracker URL' },
        { match_type: 'url', pattern: /pinimg\.com\/ct\//i, evidence_hint: 'Pinterest CT image URL' },
        { match_type: 'html', pattern: /pintrk\('load'/i, evidence_hint: "Pinterest pintrk('load',...) in HTML" },
      ],
    },
  ],
  payment_processors: [
    {
      id: 'stripe', name: 'Stripe',
      rules: [
        { match_type: 'url', pattern: /js\.stripe\.com/i, evidence_hint: 'Stripe.js CDN URL' },
        { match_type: 'url', pattern: /api\.stripe\.com/i, evidence_hint: 'Stripe API URL' },
        { match_type: 'html', pattern: /stripe\.createToken\b|stripe\.confirmCardPayment\b|StripeElement/i, evidence_hint: 'Stripe element or method in HTML' },
      ],
    },
    {
      id: 'braintree', name: 'Braintree (PayPal)',
      rules: [
        { match_type: 'url', pattern: /js\.braintreegateway\.com/i, evidence_hint: 'Braintree JS CDN URL' },
        { match_type: 'url', pattern: /api\.braintreegateway\.com/i, evidence_hint: 'Braintree API URL' },
        { match_type: 'html', pattern: /braintree\.client\.create|braintree-web/i, evidence_hint: 'Braintree client.create or braintree-web in HTML' },
      ],
    },
    {
      id: 'adyen', name: 'Adyen',
      rules: [
        { match_type: 'url', pattern: /checkoutshopper-(?:live|test)\.adyen\.com/i, evidence_hint: 'Adyen Checkout Shopper CDN URL' },
        { match_type: 'url', pattern: /\.adyen\.com\//i, evidence_hint: 'Adyen API/CDN URL' },
        { match_type: 'html', pattern: /AdyenCheckout\b|window\.AdyenCheckout/i, evidence_hint: 'Adyen AdyenCheckout global in HTML' },
      ],
    },
    {
      id: 'paypal', name: 'PayPal',
      rules: [
        { match_type: 'url', pattern: /\.paypal\.com\/sdk\/js/i, evidence_hint: 'PayPal JS SDK URL' },
        { match_type: 'url', pattern: /www\.paypal\.com\/webapps\/hermes/i, evidence_hint: 'PayPal Hermes checkout URL' },
        { match_type: 'html', pattern: /paypal\.Buttons\b|paypal-button-container/i, evidence_hint: 'PayPal Buttons or container in HTML' },
      ],
    },
    {
      id: 'checkout_com', name: 'Checkout.com',
      rules: [
        { match_type: 'url', pattern: /cdn\.checkout\.com/i, evidence_hint: 'Checkout.com CDN URL' },
        { match_type: 'url', pattern: /api\.checkout\.com/i, evidence_hint: 'Checkout.com API URL' },
        { match_type: 'html', pattern: /Frames\.init\b|checkout-frames/i, evidence_hint: 'Checkout.com Frames.init in HTML' },
      ],
    },
    {
      id: 'bolt', name: 'Bolt',
      rules: [
        { match_type: 'url', pattern: /connect\.bolt\.com/i, evidence_hint: 'Bolt connect CDN URL' },
        { match_type: 'url', pattern: /api\.bolt\.com/i, evidence_hint: 'Bolt API URL' },
        { match_type: 'html', pattern: /BoltCheckout\b|bolt-checkout/i, evidence_hint: 'Bolt checkout reference in HTML' },
      ],
    },
  ],
  cdp: [
    {
      id: 'mparticle', name: 'mParticle',
      rules: [
        { match_type: 'url', pattern: /jssdks?\.mparticle\.com/i, evidence_hint: 'mParticle JS SDK CDN URL' },
        { match_type: 'url', pattern: /nativesdks?\.mparticle\.com/i, evidence_hint: 'mParticle native SDK URL' },
        { match_type: 'html', pattern: /mParticle\.init\b/i, evidence_hint: 'mParticle.init() call in HTML' },
      ],
    },
    {
      id: 'rudderstack', name: 'RudderStack',
      rules: [
        { match_type: 'url', pattern: /cdn\.rudderlabs\.com/i, evidence_hint: 'RudderStack CDN URL' },
        { match_type: 'url', pattern: /rudderlabs\.com/i, evidence_hint: 'RudderStack URL' },
        { match_type: 'html', pattern: /rudderanalytics\.load\b|RudderAnalytics/i, evidence_hint: 'RudderStack analytics init in HTML' },
      ],
    },
    {
      id: 'blueconic', name: 'BlueConic',
      rules: [
        { match_type: 'url', pattern: /blueconic\.net/i, evidence_hint: 'BlueConic CDN/API URL' },
        { match_type: 'cookie', pattern: /^bc_/i, evidence_hint: 'BlueConic bc_ prefixed cookie' },
        { match_type: 'html', pattern: /blueConicClient\b|BlueConic\b/i, evidence_hint: 'BlueConic client reference in HTML' },
      ],
    },
    {
      id: 'tealium_audiencestream', name: 'Tealium AudienceStream',
      rules: [
        { match_type: 'url', pattern: /visitor-service\.tealiumiq\.com/i, evidence_hint: 'Tealium AudienceStream visitor service URL' },
        { match_type: 'url', pattern: /audience-store\.tealiumiq\.com/i, evidence_hint: 'Tealium AudienceStream audience-store URL' },
        { match_type: 'html', pattern: /utag\.link\b|AudienceStream/i, evidence_hint: 'Tealium AudienceStream reference in HTML' },
      ],
    },
  ],
  frontend_framework: [
    {
      id: 'nextjs', name: 'Next.js',
      rules: [
        { match_type: 'html', pattern: /__NEXT_DATA__/i, evidence_hint: '__NEXT_DATA__ global in HTML (Next.js)' },
        { match_type: 'url', pattern: /\/_next\/static\//i, evidence_hint: 'Next.js /_next/static/ asset path' },
        { match_type: 'html', pattern: /__next_[a-z]/i, evidence_hint: '__next_ prefixed variable in HTML' },
      ],
    },
    {
      id: 'react', name: 'React',
      rules: [
        { match_type: 'html', pattern: /data-reactroot\b/i, evidence_hint: 'data-reactroot attribute (React SSR) in HTML' },
        { match_type: 'html', pattern: /__REACT[_A-Z]|_reactRootContainer\b/i, evidence_hint: 'React internal global in HTML' },
        { match_type: 'url', pattern: /react(?:\.production\.min|\.development)\.js/i, evidence_hint: 'React bundle URL' },
      ],
    },
    {
      id: 'vue_nuxt', name: 'Vue / Nuxt',
      rules: [
        { match_type: 'html', pattern: /__NUXT__\s*=/i, evidence_hint: '__NUXT__ payload in HTML (Nuxt)' },
        { match_type: 'html', pattern: /data-v-[0-9a-f]{7}/i, evidence_hint: 'Vue scoped attribute (data-v-*) in HTML' },
        { match_type: 'url', pattern: /\/_nuxt\//i, evidence_hint: 'Nuxt /_nuxt/ asset path' },
      ],
    },
    {
      id: 'angular', name: 'Angular',
      rules: [
        { match_type: 'html', pattern: /ng-version=["']\d/i, evidence_hint: 'Angular ng-version attribute in HTML' },
        { match_type: 'html', pattern: /<app-root\b/i, evidence_hint: 'Angular <app-root> element in HTML' },
        { match_type: 'url', pattern: /(?:main|polyfills|runtime)\.[a-f0-9]{8,}\.js$/i, evidence_hint: 'Angular hashed bundle URL pattern' },
      ],
    },
    {
      id: 'svelte', name: 'Svelte / SvelteKit',
      rules: [
        { match_type: 'html', pattern: /__svelte\b|svelte-[a-z0-9]+/i, evidence_hint: 'Svelte class or global in HTML' },
        { match_type: 'url', pattern: /\/_app\/immutable\//i, evidence_hint: 'SvelteKit /_app/immutable/ asset path' },
        { match_type: 'html', pattern: /\bSvelteKit\b/i, evidence_hint: 'SvelteKit reference in HTML' },
      ],
    },
  ],
  marketing_automation: [
    {
      id: 'klaviyo', name: 'Klaviyo',
      rules: [
        { match_type: 'url', pattern: /static\.klaviyo\.com/i, evidence_hint: 'Klaviyo static CDN URL' },
        { match_type: 'url', pattern: /a\.klaviyo\.com/i, evidence_hint: 'Klaviyo events endpoint URL' },
        { match_type: 'html', pattern: /klaviyo\.init\b|_klOnsite\b/i, evidence_hint: 'Klaviyo init or _klOnsite in HTML' },
      ],
    },
    {
      id: 'braze', name: 'Braze',
      rules: [
        { match_type: 'url', pattern: /js\.appboycdn\.com/i, evidence_hint: 'Braze (Appboy) CDN URL' },
        { match_type: 'url', pattern: /sdk\.(?:fra-01\.braze\.eu|iad-\d+\.braze\.com)/i, evidence_hint: 'Braze SDK endpoint URL' },
        { match_type: 'html', pattern: /braze\.initialize\b|appboy\.initialize\b/i, evidence_hint: 'Braze initialize call in HTML' },
      ],
    },
    {
      id: 'iterable', name: 'Iterable',
      rules: [
        { match_type: 'url', pattern: /links\.iterable\.com/i, evidence_hint: 'Iterable link-tracking URL' },
        { match_type: 'url', pattern: /api\.iterable\.com/i, evidence_hint: 'Iterable API URL' },
        { match_type: 'html', pattern: /iterable\.identify\b|IterableWebSDK/i, evidence_hint: 'Iterable SDK reference in HTML' },
      ],
    },
    {
      id: 'hubspot', name: 'HubSpot',
      rules: [
        { match_type: 'url', pattern: /js\.hsforms\.net|js\.hscta\.net/i, evidence_hint: 'HubSpot forms/CTA CDN URL' },
        { match_type: 'url', pattern: /track\.hubspot\.com/i, evidence_hint: 'HubSpot tracking URL' },
        { match_type: 'html', pattern: /hsq\.push\b|_hsq\b/i, evidence_hint: 'HubSpot _hsq queue in HTML' },
      ],
    },
    {
      id: 'sfmc', name: 'Salesforce Marketing Cloud',
      rules: [
        { match_type: 'url', pattern: /exacttarget\.com/i, evidence_hint: 'ExactTarget (SFMC) URL' },
        { match_type: 'url', pattern: /salesforce-mktg\.com/i, evidence_hint: 'Salesforce Marketing Cloud URL' },
        { match_type: 'html', pattern: /ET_WriteEmail\b|SalesforceInteractions\.init\b/i, evidence_hint: 'SFMC ET_WriteEmail or SalesforceInteractions in HTML' },
      ],
    },
  ],
  hosting: [
    {
      id: 'vercel', name: 'Vercel',
      rules: [
        { match_type: 'response_header', header: 'x-vercel-id', evidence_hint: 'Vercel x-vercel-id response header' },
        { match_type: 'response_header', header: 'x-vercel-cache', evidence_hint: 'Vercel x-vercel-cache response header' },
        { match_type: 'response_header', header: 'server', value_pattern: /^vercel$/i, evidence_hint: 'Server: vercel response header' },
      ],
    },
    {
      id: 'netlify', name: 'Netlify',
      rules: [
        { match_type: 'response_header', header: 'x-nf-request-id', evidence_hint: 'Netlify x-nf-request-id response header' },
        { match_type: 'response_header', header: 'server', value_pattern: /^netlify$/i, evidence_hint: 'Server: netlify response header' },
        { match_type: 'url', pattern: /\.netlify\.app\//i, evidence_hint: 'Netlify .netlify.app subdomain URL' },
      ],
    },
    {
      id: 'aws_cloudfront', name: 'AWS CloudFront',
      rules: [
        { match_type: 'response_header', header: 'x-amz-cf-id', evidence_hint: 'CloudFront x-amz-cf-id response header' },
        { match_type: 'response_header', header: 'x-amz-cf-pop', evidence_hint: 'CloudFront x-amz-cf-pop PoP header' },
        { match_type: 'url', pattern: /\.cloudfront\.net\//i, evidence_hint: 'CloudFront .cloudfront.net CDN URL' },
      ],
    },
    {
      id: 'fastly_cdn', name: 'Fastly',
      // Also appears in cdn_waf; hosting entry confirms delivery infrastructure role
      rules: [
        { match_type: 'response_header', header: 'x-fastly-request-id', evidence_hint: 'Fastly x-fastly-request-id response header' },
        { match_type: 'url', pattern: /\.fastly\.net\//i, evidence_hint: 'Fastly .fastly.net CDN URL' },
      ],
    },
  ],
};

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

// --- Full tech stack detection (--full-tech mode) ---
// Multi-page capture: home → PLP → PDP → /search?q=test → /cart, all in the same browser context.
// Accumulates signals (request URLs, response headers, HTML, cookies) across every page visited.
// Each detected item carries a (page: <label>) suffix in its evidence string.
// Folds search detection result under 'search' key; does not run interactive search typing.
async function detectTechStack(targetUrl, options = {}) {
  const { timeout = 30000, waitAfterLoad = 5000, pages: customPageUrls = null } = options;

  const result = {
    url: targetUrl,
    pages_visited: [],
    detected: [],
    search: null,
    categories_covered: Object.keys(TECH_SIGNATURES).concat(['search']),
    not_detectable_note: [
      'Client-side detection only.',
      'Invisible to this detector: server-side technology (backend framework, database, server rendering),',
      'self-hosted or reverse-proxied third-party tools (network calls through first-party domain with no',
      'distinctive header/param), and any tech that emits no client-side network request, response header,',
      'HTML reference, or cookie during a cold page load.',
      'No fabrication: every detected technology is backed by a concrete matched evidence string.',
    ].join(' '),
    network_calls_total: 0,
    bot_blocked: false,
    error: null,
    timestamp: new Date().toISOString(),
  };

  // Accumulated signals across all pages visited.
  // Each entry records the page that produced it so evidence strings can cite it.
  const signals = {
    requestEntries: [],   // { url, pageLabel, method, headers, body }
    responseEntries: [],  // { url, pageLabel, headers }
    htmlEntries: [],      // { html, pageLabel }
    cookieEntries: [],    // { name, pageLabel }
  };

  const allRequestCount = { n: 0 };
  // platformHits: id -> { platform, hits: [...], firstPageLabel }
  const platformHits = new Map();
  const searchRequests = [];

  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
      viewport: { width: 1440, height: 900 },
    });

    // ---- loadPageSignals: open one tab, attach listeners, navigate, close tab ----
    // Returns { html, botBlocked, finalUrl }. Never throws — errors are logged to stderr.
    async function loadPageSignals(pageUrl, pageLabel) {
      let page;
      let html = '';
      let botBlocked = false;
      let finalUrl = pageUrl;
      try {
        page = await context.newPage();

        page.on('request', req => {
          allRequestCount.n++;
          const url = req.url();
          const headers = safeHeaders(req);
          const body = safePostData(req);
          const method = req.method();

          signals.requestEntries.push({ url, pageLabel, method, headers, body });

          // Search platform detection (identical logic to detectSearch)
          const platform = identifyPlatform(url);
          if (platform) {
            const key = platform.id;
            if (!platformHits.has(key)) platformHits.set(key, { platform, hits: [], firstPageLabel: pageLabel });
            platformHits.get(key).hits.push({ url, method, headers, body });
          }
          for (const p of PLATFORMS) {
            if (p.headerKeys && !platformHits.has(p.id)) {
              for (const hk of p.headerKeys) {
                if (headers[hk]) {
                  if (!platformHits.has(p.id)) platformHits.set(p.id, { platform: p, hits: [], firstPageLabel: pageLabel });
                  platformHits.get(p.id).hits.push({ url, method, headers, body });
                  break;
                }
              }
            }
          }

          if (isSearchRelated(url) && ['xhr', 'fetch', 'document'].includes(req.resourceType())) {
            searchRequests.push({ url: url.substring(0, 300), method, body_preview: body ? JSON.stringify(body).substring(0, 200) : null });
          }
        });

        page.on('response', resp => {
          try {
            const url = resp.url();
            const headers = resp.headers();
            if (Object.keys(headers).length > 0) {
              signals.responseEntries.push({ url, pageLabel, headers });
            }
          } catch { /* ignore failed responses */ }
        });

        await page.goto(pageUrl, { waitUntil: 'domcontentloaded', timeout });
        await page.waitForTimeout(waitAfterLoad);

        html = await page.content();
        finalUrl = page.url();
        const title = await page.title();
        botBlocked = title === 'Access Denied'
          || (html.includes('Access Denied') && html.includes("don't have permission"))
          || html.includes('cf-challenge-running') || html.includes('cf_chl_opt')
          || html.includes('Please verify you are a human')
          || html.includes('Checking your browser before accessing');
      } catch (e) {
        process.stderr.write(`  [full-tech] page "${pageLabel}" (${pageUrl}) skipped: ${e.message}\n`);
        html = '';
      }

      signals.htmlEntries.push({ html, pageLabel });

      // Snapshot cookies into signals; first page that sets a cookie wins the label
      try {
        const cookies = await context.cookies();
        const seen = new Set(signals.cookieEntries.map(c => c.name));
        for (const c of cookies) {
          if (!seen.has(c.name)) {
            signals.cookieEntries.push({ name: c.name, pageLabel });
            seen.add(c.name);
          }
        }
      } catch { /* ignore */ }

      try { await page.close(); } catch { /* ignore */ }
      return { html, botBlocked, finalUrl };
    }

    // ---- Determine the sequence of pages to visit ----
    // If --pages was supplied, use those exact URLs (first = home, rest = custom).
    // Otherwise: home → auto-discovered PLP/PDP → /search?q=test → /cart.
    let pageQueue; // [{ url, label }]

    if (customPageUrls && customPageUrls.length > 0) {
      pageQueue = customPageUrls.map((u, i) => ({ url: u, label: i === 0 ? 'home' : `custom_${i}` }));
    } else {
      pageQueue = null; // will build dynamically after home load
    }

    // ---- Page 1: home (always first) ----
    const homeTarget = pageQueue ? pageQueue[0].url : targetUrl;
    const homeLabel = 'home';
    const { html: homeHtml, botBlocked: homeBlocked, finalUrl: homeFinalUrl } =
      await loadPageSignals(homeTarget, homeLabel);
    result.pages_visited.push(homeFinalUrl || homeTarget);
    if (homeBlocked) result.bot_blocked = true;

    // ---- Pages 2+: custom override OR auto-discovery ----
    if (pageQueue) {
      // Custom pages: load index 1..n
      for (let i = 1; i < pageQueue.length; i++) {
        const { finalUrl, botBlocked } = await loadPageSignals(pageQueue[i].url, pageQueue[i].label);
        result.pages_visited.push(finalUrl || pageQueue[i].url);
        if (botBlocked) result.bot_blocked = true;
      }
    } else {
      // Auto-discover PLP and PDP from homepage HTML
      let plpUrl = null;
      let pdpUrl = null;
      try {
        const base = new URL(targetUrl);
        const plpPatterns = [/\/category\//i, /\/categories\//i, /\/collections\//i, /\/shop\/[^"'/?#]+\//i, /\/c\/[^"'/?#]+\//i, /\/department\//i, /\/browse\//i];
        const pdpPatterns = [/\/product\//i, /\/products\//i, /\/p\/[^"'/?#]+/i, /\/item\//i, /\/dp\/[A-Z0-9]{5,}/i, /\/sku\//i];

        for (const m of homeHtml.matchAll(/href=["']([^"'#][^"']*?)["']/g)) {
          if (plpUrl && pdpUrl) break;
          try {
            const resolved = new URL(m[1], base.href);
            if (resolved.hostname === base.hostname && resolved.pathname.length > 1) {
              const full = resolved.href;
              if (!plpUrl && plpPatterns.some(p => p.test(full))) plpUrl = full;
              if (!pdpUrl && pdpPatterns.some(p => p.test(full))) pdpUrl = full;
            }
          } catch { /* skip bad hrefs */ }
        }
      } catch (e) {
        process.stderr.write(`  [full-tech] link discovery failed: ${e.message}\n`);
      }

      const autoPages = [];
      if (plpUrl) autoPages.push({ url: plpUrl, label: 'plp' });
      if (pdpUrl) autoPages.push({ url: pdpUrl, label: 'pdp' });
      try {
        const base = new URL(targetUrl);
        autoPages.push({ url: `${base.origin}/search?q=test`, label: 'search' });
        autoPages.push({ url: `${base.origin}/cart`, label: 'cart' });
      } catch { /* ignore URL parse error */ }

      for (const { url, label } of autoPages) {
        const { finalUrl, botBlocked } = await loadPageSignals(url, label);
        result.pages_visited.push(finalUrl || url);
        if (botBlocked) result.bot_blocked = true;
      }
    }

    result.network_calls_total = allRequestCount.n;

    // ======= Tech signature matching over accumulated multi-page signals =======
    for (const [category, techs] of Object.entries(TECH_SIGNATURES)) {
      for (const tech of techs) {
        let matched = null;

        for (const rule of tech.rules) {
          if (matched) break;

          if (rule.match_type === 'url') {
            for (const entry of signals.requestEntries) {
              if (rule.pattern.test(entry.url)) {
                matched = {
                  confidence: 'confirmed',
                  evidence: `Network URL: ${entry.url.substring(0, 200)} [${rule.evidence_hint}] (page: ${entry.pageLabel})`,
                };
                break;
              }
            }
          } else if (rule.match_type === 'response_header') {
            for (const entry of signals.responseEntries) {
              const headerVal = entry.headers[rule.header.toLowerCase()];
              if (headerVal !== undefined) {
                if (!rule.value_pattern || rule.value_pattern.test(headerVal)) {
                  matched = {
                    confidence: 'confirmed',
                    evidence: `Response header ${rule.header}: "${headerVal.substring(0, 80)}" on ${entry.url.substring(0, 100)} [${rule.evidence_hint}] (page: ${entry.pageLabel})`,
                  };
                  break;
                }
              }
            }
          } else if (rule.match_type === 'html') {
            for (const entry of signals.htmlEntries) {
              if (entry.html && rule.pattern.test(entry.html)) {
                matched = {
                  confidence: 'likely',
                  evidence: `HTML source match: ${rule.evidence_hint} (page: ${entry.pageLabel})`,
                };
                break;
              }
            }
          } else if (rule.match_type === 'cookie') {
            for (const entry of signals.cookieEntries) {
              if (rule.pattern.test(entry.name)) {
                matched = {
                  confidence: 'confirmed',
                  evidence: `Cookie: ${entry.name} [${rule.evidence_hint}] (page: ${entry.pageLabel})`,
                };
                break;
              }
            }
          }
        }

        if (matched) {
          result.detected.push({
            category,
            technology: tech.name,
            confidence: matched.confidence,
            evidence: matched.evidence,
            source: 'detect-search',
          });
        }
      }
    }

    // ======= Open-DB fallback matching (non-fatal; skipped if module absent) =======
    try {
      const { matchOpenDb } = require('./tech-fingerprint-db');
      const responseHeaderMap = {};
      for (const e of signals.responseEntries) {
        if (!responseHeaderMap[e.url]) responseHeaderMap[e.url] = e.headers;
      }
      const capturedSignals = {
        requestUrls: signals.requestEntries.map(e => e.url),
        responseHeaders: responseHeaderMap,
        htmlSources: signals.htmlEntries.map(e => e.html).filter(Boolean),
        cookieNames: [...new Set(signals.cookieEntries.map(e => e.name))],
      };
      const openDbResults = matchOpenDb(capturedSignals);
      const curatedTechLower = new Set(result.detected.map(d => d.technology.toLowerCase()));
      for (const od of openDbResults) {
        if (!curatedTechLower.has(od.technology.toLowerCase())) {
          result.detected.push({
            category: od.category,
            technology: od.technology,
            confidence: 'likely-opendb',
            evidence: od.evidence,
            source: 'opendb',
          });
        }
      }
    } catch (e) {
      process.stderr.write(`  [full-tech] open-db matcher skipped: ${e.message}\n`);
    }

    // ======= Search detection (fold existing logic; uses combined signals) =======
    const combinedHtml = signals.htmlEntries.map(e => e.html).join(' ');
    const htmlLower = combinedHtml.toLowerCase();
    const searchResult = {
      search_detected: false,
      search_platform: null,
      platform_id: null,
      platform_details: {},
      all_platforms_found: [],
      is_dealer_inspire: DI_FINGERPRINTS.some(fp => combinedHtml.includes(fp)),
      search_calls_count: searchRequests.length,
    };

    const allSearchPlatforms = [];
    for (const [id, val] of platformHits) {
      if (id === 'dealer_inspire') continue;
      const extracted = val.platform.extract(val.hits);
      allSearchPlatforms.push({
        id,
        name: val.platform.name,
        hit_count: val.hits.length,
        sample_endpoint: val.hits[0].url.substring(0, 300),
        details: extracted,
        firstPageLabel: val.firstPageLabel,
      });
    }

    // HTML fallback for search platform detection (checks combined HTML from all pages)
    const htmlSearchChecks = [
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
    for (const check of htmlSearchChecks) {
      if (!allSearchPlatforms.find(p => p.id === check.id) && check.patterns.some(pat => htmlLower.includes(pat))) {
        allSearchPlatforms.push({
          id: check.id,
          name: PLATFORMS.find(p => p.id === check.id)?.name || check.id,
          hit_count: 0,
          sample_endpoint: null,
          details: { detection_method: 'html_source_only' },
          firstPageLabel: 'home',
        });
      }
    }

    searchResult.all_platforms_found = allSearchPlatforms.map(({ firstPageLabel: _, ...rest }) => rest);

    if (allSearchPlatforms.length > 0) {
      const primary = allSearchPlatforms.sort((a, b) => b.hit_count - a.hit_count)[0];
      searchResult.search_detected = true;
      searchResult.search_platform = primary.name;
      searchResult.platform_id = primary.id;
      searchResult.platform_details = primary.details;
    }

    if (searchRequests.length > 0 && !searchResult.search_detected) {
      searchResult.search_detected = true;
      searchResult.search_platform = 'Proprietary / Unidentified';
      searchResult.platform_id = 'unknown';
      searchResult.platform_details = { first_endpoint: searchRequests[0].url };
    }

    // Add confirmed search hit into the unified detected list
    if (searchResult.search_detected && searchResult.platform_id !== 'unknown') {
      const primaryPlatform = allSearchPlatforms.find(p => p.id === searchResult.platform_id);
      const pg = primaryPlatform?.firstPageLabel || 'home';
      result.detected.push({
        category: 'search',
        technology: searchResult.search_platform,
        confidence: primaryPlatform?.hit_count > 0 ? 'confirmed' : 'likely',
        evidence: primaryPlatform?.sample_endpoint
          ? `Network URL: ${primaryPlatform.sample_endpoint} (page: ${pg})`
          : `HTML source reference (page: ${pg})`,
        source: 'detect-search',
      });
    }

    result.search = searchResult;

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
detect-search — Identify search platform OR full client-side tech stack by sniffing network traffic.

Usage (search-only mode — default):
  node detect-search.js <url>                        Detect search platform (types "test" by default)
  node detect-search.js <url> --type-query "shoes"   Use specific search term
  node detect-search.js <url> --no-search            Page-load traffic only
  node detect-search.js --file <path>                Bulk mode, one URL per line
  node detect-search.js --file <path> --csv          Bulk CSV output

Usage (full tech stack mode):
  node detect-search.js <url> --full-tech            Detect full stack: ecommerce, search, analytics,
                                                     tag manager, CDN/WAF, personalization, reviews/UGC,
                                                     consent/CMP, ad pixels, payment processors, CDP,
                                                     frontend frameworks, marketing automation, hosting
  node detect-search.js <url> --full-tech --pages "url1,url2,url3"
                                                     Override auto-discovered pages with exact URLs

Options:
  --type-query <q>    Search term for search-only mode (default: "test")
  --no-search         Skip search interaction (search-only mode)
  --full-tech         Full tech stack detection mode (multi-page; no search typing)
  --pages "u1,u2..."  Override page list for --full-tech (comma-separated URLs)
  --file <path>       Bulk mode (search-only)
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
  const pagesIdx = args.indexOf('--pages');
  const noSearch = args.includes('--no-search');
  const fullTech = args.includes('--full-tech');

  const typeQuery = typeIdx >= 0 ? args[typeIdx + 1] : 'test';
  const timeout = timeoutIdx >= 0 ? parseInt(args[timeoutIdx + 1], 10) : 30000;
  const waitAfterLoad = waitIdx >= 0 ? parseInt(args[waitIdx + 1], 10) : 5000;
  const pagesOverride = pagesIdx >= 0
    ? args[pagesIdx + 1].split(',').map(u => u.trim()).filter(Boolean)
    : null;
  const options = { timeout, waitAfterLoad, typeQuery, noSearch };

  // --full-tech: multi-page tech stack mode; runs detectTechStack (no search typing)
  if (fullTech) {
    if (fileIdx >= 0) {
      console.error('--full-tech does not support --file bulk mode (run URLs one at a time)');
      process.exit(1);
    }
    let url = args.find(a => a.startsWith('http') || (!a.startsWith('-') && !a.includes('=')));
    if (!url) { console.error('No URL provided'); process.exit(1); }
    if (!url.startsWith('http')) url = 'https://' + url;
    process.stderr.write(`[full-tech] ${url}${pagesOverride ? ` (${pagesOverride.length} custom pages)` : ' (auto-discover pages)'}\n`);
    const r = await detectTechStack(url, { timeout, waitAfterLoad, pages: pagesOverride });
    console.log(JSON.stringify(r, null, 2));
    return;
  }

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
