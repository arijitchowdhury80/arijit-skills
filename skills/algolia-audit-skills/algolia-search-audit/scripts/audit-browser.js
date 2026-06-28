#!/usr/bin/env node
/**
 * audit-browser.js — Playwright + stealth browser audit for Algolia Search Audit
 * Replaces Chrome MCP for Phase 2 browser testing. Bypasses WAF (Akamai, Cloudflare).
 *
 * GENERAL-PURPOSE: the per-site bits (search selector, the URL pattern a site uses for a
 * search-results page, the query set, cookie/modal dismissal) are all PARAMETERS — not
 * hand-forked scripts. This is what killed the ~20 abandoned per-company forks
 * (tnf-audit-v3.js, jbl-audit-stealth.js, hd-mx-audit-full.js, …); see _archive/.
 *
 * Two search modes, auto-selected (or forced via --mode):
 *   - "input": type into the on-page search box (default; works on most sites)
 *   - "url":   navigate directly to a results URL built from a template, e.g.
 *              "/search?q={q}" or "/en-us/search?q={q}". This is the WAF/CAPTCHA-robust
 *              path the forks all converged on (PerimeterX/Akamai trip on keystrokes,
 *              not on navigation). Pass --search-url-template to enable.
 *
 * Usage:
 *   node audit-browser.js --company Costco --url https://www.costco.com --audit-dir /path
 *   node audit-browser.js --company TheNorthFace --url https://www.thenorthface.com \
 *        --search-url-template "/en-us/search?q={q}" --mode url --audit-dir /path
 *   node audit-browser.js --company HomeDepotMx --url https://www.homedepot.com.mx \
 *        --search-selector "#type-ahead-site-search-desktop" --audit-dir /path
 *   node audit-browser.js --company X --url https://x.com --config ./site-config.json
 *   node audit-browser.js --test        (smoke test — navigates to example.com)
 *   node audit-browser.js --self-test   (no network: validates config/template plumbing)
 *
 * --config <path>  JSON with any of:
 *   {
 *     "searchSelector": "#type-ahead-site-search-desktop",
 *     "searchUrlTemplate": "/en-us/search?q={q}",
 *     "mode": "url",
 *     "queries": { "main": "television", "typo": "samung tv", "nlp": "warm jacket under 300",
 *                  "noResults": "asdfghjk", "nonProduct": "return policy" },
 *     "dismissSelectors": ["#px-captcha-modal-close", ".custom-modal-close"]
 *   }
 * CLI flags override config; config overrides defaults.
 */

const path = require('path');
const fs = require('fs');

// ── Argument parsing ──────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const getArg = (flag) => { const i = args.indexOf(flag); return i >= 0 ? args[i + 1] : null; };
const hasFlag = (flag) => args.includes(flag);

const company = getArg('--company') || 'Unknown';
const url = getArg('--url') || 'https://example.com';
const stepFlag = getArg('--step');
const auditDir = getArg('--audit-dir') || process.env.ALGOLIA_AUDIT_DIR || process.cwd();
const isHeaded = hasFlag('--headed');
const isTest = hasFlag('--test');
const isSelfTest = hasFlag('--self-test');
const allSteps = hasFlag('--all-steps');
const configPath = getArg('--config');

// ── Per-site config (file → CLI override → default) ────────────────────────────
const DEFAULT_QUERIES = {
  main: 'television',
  typo: 'samung tv',
  nlp: 'warm jacket for skiing under 300',
  noResults: 'asdfghjk',
  nonProduct: 'return policy',
};

const DEFAULT_DISMISS = [
  '#onetrust-accept-btn-handler',
  'button[aria-label*="accept" i]',
  'button[data-tracking*="cookie" i]',
  '.cookie-accept',
  '[data-block-page-scroll="true"] button[aria-label*="close" i]',
  'button[aria-label*="close" i]',
];

function loadConfig(p) {
  if (!p) return {};
  try {
    const raw = fs.readFileSync(p, 'utf8');
    return JSON.parse(raw);
  } catch (e) {
    console.error(`⚠️  Could not read --config ${p}: ${e.message}. Using defaults.`);
    return {};
  }
}

const fileConfig = loadConfig(configPath);

// Resolve effective config: CLI flag > config file > default.
const cfg = {
  searchSelector: getArg('--search-selector') || fileConfig.searchSelector || null,
  searchUrlTemplate: getArg('--search-url-template') || fileConfig.searchUrlTemplate || null,
  mode: getArg('--mode') || fileConfig.mode || null,  // "input" | "url" | null(auto)
  queries: Object.assign({}, DEFAULT_QUERIES, fileConfig.queries || {}),
  dismissSelectors: (fileConfig.dismissSelectors || []).concat(DEFAULT_DISMISS),
};
// Allow --queries-file to supply a JSON object of queries.
const queriesFile = getArg('--queries-file');
if (queriesFile) {
  try { Object.assign(cfg.queries, JSON.parse(fs.readFileSync(queriesFile, 'utf8'))); }
  catch (e) { console.error(`⚠️  Could not read --queries-file ${queriesFile}: ${e.message}`); }
}

// Effective mode: explicit, else "url" if a template was given, else "input".
const searchMode = cfg.mode || (cfg.searchUrlTemplate ? 'url' : 'input');

// Canonical screenshots path
const screenshotsDir = path.join(auditDir, company, 'deliverables', 'screenshots');
const findingsPath = path.join(auditDir, company, 'research', '09-browser-findings.md');

// ── Search input selectors (try in order; site override prepended) ─────────────
const SEARCH_SELECTORS = [
  '#SearchInput', 'input[type="search"]', 'input[name="q"]',
  'input[name="search"]', 'input[placeholder*="Search" i]',
  '[data-testid="search-input"]', '[data-testid*="search" i]',
  '.search-input', '.searchInput', '#search-input',
  'input[aria-label*="Search" i]', 'header input[type="text"]'
];
// A site-specific selector (from config/CLI) wins — tried first.
const EFFECTIVE_SELECTORS = cfg.searchSelector
  ? [cfg.searchSelector, ...SEARCH_SELECTORS]
  : SEARCH_SELECTORS;

// ── URL helpers ────────────────────────────────────────────────────────────────
// Build a results-page URL from the per-site template. {q} is replaced with the
// URL-encoded query (spaces → "+" to match the forks' observed pattern).
function buildSearchUrl(baseUrl, template, query) {
  const enc = encodeURIComponent(query).replace(/%20/g, '+');
  // Template may be absolute or a path; resolve against base origin.
  if (/^https?:\/\//i.test(template)) return template.replace('{q}', enc);
  const origin = baseUrl.replace(/\/+$/, '');
  const pathPart = template.startsWith('/') ? template : '/' + template;
  return origin + pathPart.replace('{q}', enc);
}

// ── Screenshot helper ──────────────────────────────────────────────────────────
async function screenshot(page, filename, context = '') {
  fs.mkdirSync(screenshotsDir, { recursive: true });
  const filepath = path.join(screenshotsDir, filename);
  await page.screenshot({ path: filepath, fullPage: false });
  const size = fs.statSync(filepath).size;
  const quality = size < 50000 ? '⚠️ SMALL (<50KB — possible WAF block)' : '✓';
  console.log(`  📸 ${filename} — ${size} bytes ${quality}${context ? ' | ' + context : ''}`);
  return { filepath, size, waf_suspected: size < 50000 };
}

// ── Dismiss cookie banners / modals / overlays (per-site + defaults) ───────────
async function dismissOverlays(page) {
  for (const sel of cfg.dismissSelectors) {
    try {
      const el = await page.$(sel);
      if (el) { await el.click({ timeout: 1500 }).catch(() => {}); await page.waitForTimeout(300); }
    } catch { /* ignore */ }
  }
}

// ── WAF check ─────────────────────────────────────────────────────────────────
async function checkWAF(page) {
  const title = await page.title().catch(() => '');
  const content = await page.content().catch(() => '');
  return title.includes('Access Denied') || title.includes('Just a moment') ||
         title.includes('403') || content.includes('ray ID') ||
         content.includes('Checking your browser');
}

async function findSearchInput(page) {
  for (const sel of EFFECTIVE_SELECTORS) {
    try {
      await page.waitForSelector(sel, { timeout: 3000 });
      return sel;
    } catch { continue; }
  }
  return null;
}

// ── Search executor — abstracts input-mode vs url-mode ─────────────────────────
// Returns true if a results page was reached without a WAF block.
async function runQuery(page, searchSel, query, { fresh = true } = {}) {
  if (searchMode === 'url' && cfg.searchUrlTemplate) {
    const target = buildSearchUrl(url, cfg.searchUrlTemplate, query);
    await page.goto(target, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2500);
    await dismissOverlays(page);
    return !(await checkWAF(page));
  }
  // input mode
  if (fresh) {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(1200);
    await dismissOverlays(page);
  }
  const sel = await findSearchInput(page) || searchSel;
  if (!sel) return false;
  await page.fill(sel, query).catch(async () => { await page.click(sel); await page.type(sel, query, { delay: 60 }); });
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2800);
  return !(await checkWAF(page));
}

// ── Individual step runners ───────────────────────────────────────────────────
const findings = [];

async function step2a(page) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(2000);
  await dismissOverlays(page);
  if (await checkWAF(page)) { console.log('  ⛔ WAF detected on homepage'); return null; }
  const shot = await screenshot(page, '01-homepage.png', 'Initial observations');
  const searchSelector = await findSearchInput(page);
  findings.push({ step: '2a', screenshot: shot.filepath, observation: `Homepage loaded. Search input: ${searchSelector || 'NOT FOUND'}. Mode: ${searchMode}` });
  return searchSelector;
}

async function step2b(page, searchSel) {
  // Empty-state test only meaningful in input mode (focus the box, observe suggestions).
  if (searchMode === 'url' || !searchSel) {
    findings.push({ step: '2b', observation: searchMode === 'url' ? 'Empty-state skipped (url mode)' : 'No search input — empty state untestable' });
    return;
  }
  await page.click(searchSel);
  await page.waitForTimeout(1000);
  const shot = await screenshot(page, '02-empty-state.png', 'Empty state test');
  const html = await page.content();
  const hasSuggestions = html.includes('trending') || html.includes('popular') || html.includes('recent');
  findings.push({ step: '2b', screenshot: shot.filepath, observation: hasSuggestions ? 'Suggestions shown' : 'GAP: Blank empty state — no suggestions' });
}

async function step2c(page, searchSel, query) {
  // SAYT (type-ahead) — only observable in input mode.
  if (searchMode === 'url' || !searchSel) {
    findings.push({ step: '2c', observation: searchMode === 'url' ? `SAYT skipped (url mode) for "${query}"` : 'No search input — SAYT untestable' });
    return;
  }
  await page.click(searchSel);
  await page.type(searchSel, query.slice(0, 4), { delay: 80 });
  await page.waitForTimeout(1500);
  const shot = await screenshot(page, `03-sayt-${query.slice(0,4)}.png`, `SAYT: "${query.slice(0,4)}"`);
  findings.push({ step: '2c', screenshot: shot.filepath, observation: `SAYT test for "${query}"`, query });
}

async function step2d(page, searchSel, query) {
  const ok = await runQuery(page, searchSel, query, { fresh: true });
  if (!ok) {
    const shot = await screenshot(page, '04-waf-block.png', 'WAF blocked full search');
    findings.push({ step: '2d', screenshot: shot.filepath, observation: `WAF BLOCKED: Full search for "${query}"`, waf_blocked: true });
    return;
  }
  const shot = await screenshot(page, `04-results-${query.replace(/\s+/g,'-').slice(0,15)}.png`, `Results: "${query}"`);
  const resultCount = await page.$eval('[data-count], .result-count, h1', el => el.textContent).catch(() => 'unknown');
  findings.push({ step: '2d', screenshot: shot.filepath, observation: `Results for "${query}": ${resultCount}`, query });
}

async function step2e(page, searchSel, typoQuery) {
  const ok = await runQuery(page, searchSel, typoQuery, { fresh: true });
  const shot = await screenshot(page, `05-typo-${typoQuery.replace(/\s+/g,'-')}.png`, `Typo: "${typoQuery}"`);
  findings.push({ step: '2e', screenshot: shot.filepath, observation: `Typo tolerance: "${typoQuery}"${ok ? '' : ' (WAF suspected)'}`, query: typoQuery });
}

async function step2f(page, searchSel, nlpQuery) {
  // NLP / conversational query (the forks all tested an "under $X" phrase).
  const ok = await runQuery(page, searchSel, nlpQuery, { fresh: true });
  const shot = await screenshot(page, `06-nlp-${nlpQuery.replace(/\s+/g,'-').slice(0,20)}.png`, `NLP: "${nlpQuery}"`);
  findings.push({ step: '2f', screenshot: shot.filepath, observation: `NLP/semantic: "${nlpQuery}"${ok ? '' : ' (WAF suspected)'}`, query: nlpQuery });
}

async function step2g(page, searchSel, noResultsQuery) {
  await runQuery(page, searchSel, noResultsQuery, { fresh: true });
  const shot = await screenshot(page, '07-no-results.png', 'No results test');
  findings.push({ step: '2g', screenshot: shot.filepath, observation: `No results test with "${noResultsQuery}"` });
}

async function step2h(page, searchSel, nonProductQuery) {
  await runQuery(page, searchSel, nonProductQuery, { fresh: true });
  const shot = await screenshot(page, '08-non-product-return-policy.png', 'Non-product content');
  findings.push({ step: '2h', screenshot: shot.filepath, observation: `Non-product content: "${nonProductQuery}"` });
}

async function step2l(page) {
  await page.setViewportSize({ width: 390, height: 844 }); // iPhone 14
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(1500);
  await dismissOverlays(page);
  const shot = await screenshot(page, '12-mobile-viewport.png', 'Mobile viewport');
  findings.push({ step: '2l', screenshot: shot.filepath, observation: 'Mobile viewport (390×844)' });
  await page.setViewportSize({ width: 1440, height: 900 }); // Reset
}

// ── Network vendor detection ──────────────────────────────────────────────────
async function detectSearchVendor(page, searchSel, testQuery) {
  const requests = [];
  page.on('request', req => { if (req.resourceType() === 'fetch' || req.resourceType() === 'xhr') requests.push(req.url()); });
  if (searchMode === 'url' && cfg.searchUrlTemplate) {
    await page.goto(buildSearchUrl(url, cfg.searchUrlTemplate, testQuery), { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(1800);
  } else if (searchSel) {
    await page.click(searchSel);
    await page.type(searchSel, testQuery.slice(0,3), { delay: 60 });
    await page.waitForTimeout(1500);
  } else {
    return 'unknown';
  }
  const VENDORS = { algolia: /algolia\.net|algolianet\.com/, coveo: /coveo\.com/, bloomreach: /brsrvr\.com|bloomreach\.com/, constructor: /cnstrc\.com/, searchspring: /searchspring\.io/, lucidworks: /lucidworks\.com|\/api\/apps\/.*\/query/ };
  for (const [name, regex] of Object.entries(VENDORS)) {
    if (requests.some(u => regex.test(u))) return `${name} ACTIVE`;
  }
  const vendorUrls = requests.filter(u => u.includes('search') || u.includes('query') || u.includes('suggest'));
  return vendorUrls.length > 0 ? `Unknown (${vendorUrls[0].split('/').slice(0,4).join('/')})` : 'Not detected';
}

// ── Self-test (no network) — validates the parameterization plumbing ───────────
function selfTest() {
  const assert = (label, cond) => { if (!cond) { console.error(`  FAIL: ${label}`); process.exitCode = 1; } else console.log(`  ✓ ${label}`); };
  // URL template building
  assert('relative template resolves against origin',
    buildSearchUrl('https://www.thenorthface.com', '/en-us/search?q={q}', 'rain gear') === 'https://www.thenorthface.com/en-us/search?q=rain+gear');
  assert('trailing slash on base is stripped',
    buildSearchUrl('https://www.jbl.com/', '/search?q={q}', 'speakers') === 'https://www.jbl.com/search?q=speakers');
  assert('absolute template used verbatim',
    buildSearchUrl('https://x.com', 'https://search.x.com/?q={q}', 'a b') === 'https://search.x.com/?q=a+b');
  assert('path without leading slash is normalized',
    buildSearchUrl('https://x.com', 'find?q={q}', 'q') === 'https://x.com/find?q=q');
  // selector precedence
  assert('site selector is tried first', EFFECTIVE_SELECTORS[0] === (cfg.searchSelector || '#SearchInput'));
  // mode inference
  assert('mode auto-infers url when template present', (cfg.searchUrlTemplate ? searchMode === 'url' : true));
  // query defaults present
  assert('default queries are populated', cfg.queries.main && cfg.queries.typo && cfg.queries.noResults);
  console.log(process.exitCode ? '\n✗ self-test FAILED' : '\n✓ self-test passed (no network)');
}

// ── Main execution ─────────────────────────────────────────────────────────────
(async () => {
  if (isSelfTest) { selfTest(); process.exit(process.exitCode || 0); }

  // Playwright only required for real runs (keeps --self-test dependency-free).
  const { chromium } = require('playwright-extra');
  const stealth = require('puppeteer-extra-plugin-stealth');
  chromium.use(stealth());

  if (isTest) {
    console.log('🧪 Smoke test mode — navigating to example.com');
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.goto('https://example.com');
    const title = await page.title();
    console.log(`✓ Playwright + stealth working. Page title: "${title}"`);
    await browser.close();
    process.exit(0);
  }

  console.log(`\n🔍 Algolia Browser Audit — ${company}`);
  console.log(`   URL: ${url}`);
  console.log(`   Mode: ${searchMode}${cfg.searchUrlTemplate ? ` (template: ${cfg.searchUrlTemplate})` : ''}`);
  console.log(`   Search selector: ${cfg.searchSelector || 'auto-detect'}`);
  console.log(`   Screenshots: ${screenshotsDir}`);
  console.log(`   ${isHeaded ? 'headed' : 'headless'} | Steps: ${stepFlag || (allSteps ? 'all' : 'core')}\n`);

  let browser;
  try {
    browser = await chromium.launch({ headless: !isHeaded, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' });
    const page = await context.newPage();

    // Step 2a — always first
    const searchSel = await step2a(page);

    // Detect search vendor (works in both modes)
    console.log('  🔍 Detecting search vendor...');
    const vendor = await detectSearchVendor(page, searchSel, cfg.queries.main);
    console.log(`  Vendor: ${vendor}`);
    findings.push({ step: '2a½', observation: `Search vendor: ${vendor}` });

    if (stepFlag === '2a' || stepFlag === '2a½') { /* already done */ }
    else {
      await step2b(page, searchSel);
      await step2c(page, searchSel, cfg.queries.main);
      await step2d(page, searchSel, cfg.queries.main);
      await step2e(page, searchSel, cfg.queries.typo);
      await step2f(page, searchSel, cfg.queries.nlp);
      await step2g(page, searchSel, cfg.queries.noResults);
      await step2h(page, searchSel, cfg.queries.nonProduct);
      await step2l(page);
    }

    await browser.close();

    // Write findings
    const total = findings.length;
    const shots = findings.filter(f => f.screenshot).length;
    const wafBlocks = findings.filter(f => f.waf_blocked).length;

    console.log(`\n✅ Audit complete: ${total} steps, ${shots} screenshots, ${wafBlocks} WAF blocks\n`);

    const findingsText = findings.map(f => `### Step ${f.step}\n- Screenshot: ${f.screenshot || 'N/A'}\n- Observation: ${f.observation}\n`).join('\n');
    fs.mkdirSync(path.dirname(findingsPath), { recursive: true });
    fs.appendFileSync(findingsPath, `\n## Audit Run: ${new Date().toISOString()} (mode: ${searchMode})\n${findingsText}`);
    console.log(`📝 Findings appended to: ${findingsPath}`);

    process.stdout.write(JSON.stringify({ company, url, mode: searchMode, steps_completed: total, screenshots: shots, waf_blocks: wafBlocks, findings }, null, 2));

  } catch (err) {
    console.error(`\n❌ Error: ${err.message}`);
    if (browser) await browser.close().catch(() => {});
    process.exit(1);
  }
})();
