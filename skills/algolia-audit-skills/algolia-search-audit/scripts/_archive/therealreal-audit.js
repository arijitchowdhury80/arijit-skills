/**
 * TheRealReal Browser Audit
 * Uses JS dispatch events to bypass modal overlay that blocks Playwright's pointer events
 * Key finding from run 1: homepage=143KB✓, empty-state=204KB✓ using jsClick
 * Modal: `data-block-page-scroll="true"` intercepts all pointer events
 */
const { chromium } = require('playwright-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const path = require('path');
const fs = require('fs');
chromium.use(StealthPlugin());

const AUDIT_DIR = '/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit';
const SHOTS = path.join(AUDIT_DIR, 'Therealreal/deliverables/screenshots');
const BASE = 'https://www.therealreal.com';
const SEARCH_SEL = '#search-bar-input';

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function shot(page, name) {
  const fp = path.join(SHOTS, name);
  await page.screenshot({ path: fp });
  const sz = fs.statSync(fp).size;
  console.log(`  📸 ${name} — ${sz.toLocaleString()} bytes ${sz > 100000 ? '✓' : sz > 50000 ? '~OK' : '⚠ small'}`);
  return sz;
}

// Focus search input via JS (bypasses modal overlay blocking)
async function focusSearch(page) {
  await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (el) { el.focus(); el.click(); }
  }, SEARCH_SEL);
  await sleep(400);
}

// Type a query character by character using keyboard events (triggers SAYT/autocomplete)
async function typeSearch(page, query) {
  await focusSearch(page);
  // Clear existing value
  await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (el) el.value = '';
  }, SEARCH_SEL);
  // Type char by char via keyboard
  for (const ch of query) {
    await page.keyboard.type(ch, { delay: 70 });
  }
  await sleep(1500);
}

// Submit search and wait for results
async function submitAndWait(page) {
  await page.keyboard.press('Enter');
  await sleep(5000); // SPA rendering time
}

// Dismiss modal/overlay
async function dismissModal(page) {
  try { await page.keyboard.press('Escape'); } catch(e) {}
  await sleep(500);
  // Remove the modal overlay DOM element to unblock clicks
  await page.evaluate(() => {
    const overlay = document.querySelector('[data-block-page-scroll="true"]');
    if (overlay) overlay.remove();
    // Also remove any modal backdrops
    document.querySelectorAll('[class*="Modal"], [class*="modal"], [class*="overlay"]').forEach(el => {
      if (el.style.position === 'fixed' || getComputedStyle(el).position === 'fixed') el.remove();
    });
  });
  await sleep(300);
}

async function loadPage(page) {
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(4000);
  await dismissModal(page);
}

async function main() {
  fs.mkdirSync(SHOTS, { recursive: true });
  const vendors = new Set();

  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    locale: 'en-US',
  });
  context.on('request', req => {
    const u = req.url();
    if (/algolia|cnstrc|constructor\.io|bloomreach|coveo|klevu|searchspring/i.test(u)) vendors.add(u);
  });

  const page = await context.newPage();

  // ─── 2a: Homepage ───────────────────────────────────────────────────────
  console.log('2a: Homepage');
  await loadPage(page);
  await shot(page, '01-homepage.png');

  // ─── 2b: Empty State ───────────────────────────────────────────────────
  console.log('2b: Empty state');
  await focusSearch(page);
  await sleep(2000);
  await shot(page, '02-empty-state.png');

  // ─── 2c: SAYT — 'chan' ─────────────────────────────────────────────────
  console.log('2c: SAYT chan');
  await typeSearch(page, 'chan');
  await sleep(500);
  await shot(page, '03-sayt-chan.png');

  // ─── 2d: Full Results — chanel ─────────────────────────────────────────
  console.log('2d: Full results chanel');
  // Clear and type full query  
  await page.evaluate((sel) => { const el = document.querySelector(sel); if(el) el.value=''; }, SEARCH_SEL);
  for (const ch of 'chanel') { await page.keyboard.type(ch, {delay:70}); }
  await sleep(500);
  await submitAndWait(page);
  await shot(page, '04-results-chanel.png');
  console.log('  URL:', page.url());

  // ─── 2e: Typo — loui vuitton ──────────────────────────────────────────
  console.log('2e: Typo loui vuitton');
  await loadPage(page);
  await typeSearch(page, 'loui vuitton');
  await submitAndWait(page);
  await shot(page, '05-typo-loui-vuitton.png');

  // ─── 2e: Typo — prade bag ─────────────────────────────────────────────
  console.log('2e: Typo prade');
  await loadPage(page);
  await typeSearch(page, 'prade bag');
  await submitAndWait(page);
  await shot(page, '05b-typo-prade.png');

  // ─── 2f: Synonym — purse ──────────────────────────────────────────────
  console.log('2f: Synonym purse');
  await loadPage(page);
  await typeSearch(page, 'purse');
  await submitAndWait(page);
  await shot(page, '06-synonym-purse.png');

  // ─── 2g: No Results ───────────────────────────────────────────────────
  console.log('2g: No results');
  await loadPage(page);
  await typeSearch(page, 'asdfghjkzxcvbnm');
  await submitAndWait(page);
  await shot(page, '07-no-results.png');

  // ─── 2h: Non-product — return policy ──────────────────────────────────
  console.log('2h: Return policy');
  await loadPage(page);
  await typeSearch(page, 'return policy');
  await submitAndWait(page);
  await shot(page, '08-non-product-return-policy.png');

  // ─── 2i: Intent — gucci dionysus ──────────────────────────────────────
  console.log('2i: Intent gucci dionysus');
  await loadPage(page);
  await typeSearch(page, 'gucci dionysus');
  await submitAndWait(page);
  await shot(page, '09-intent-gucci.png');

  // ─── 2j: Merchandising ────────────────────────────────────────────────
  console.log('2j: Merchandising — search gucci');
  await loadPage(page);
  await typeSearch(page, 'gucci');
  await submitAndWait(page);
  await shot(page, '10-merchandising-search-gucci.png');
  console.log('2j: Merchandising — nav women/bags');
  await page.goto(`${BASE}/women/bags`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(4000);
  await shot(page, '10b-merchandising-nav-bags.png');

  // ─── 2k: Federated — SAYT 'authentic' ────────────────────────────────
  console.log('2k: Federated');
  await loadPage(page);
  await typeSearch(page, 'authentic');
  await sleep(500);
  await shot(page, '11-federated-authentic.png');

  // ─── 2l: Mobile ───────────────────────────────────────────────────────
  console.log('2l: Mobile');
  await page.setViewportSize({ width: 390, height: 844 });
  await loadPage(page);
  await typeSearch(page, 'chanel bag');
  await submitAndWait(page);
  await shot(page, '12-mobile-chanel.png');
  await page.setViewportSize({ width: 1440, height: 900 });

  // ─── 2m: NLP — gift for wife under 500 ───────────────────────────────
  console.log('2m: NLP gift under 500');
  await loadPage(page);
  await typeSearch(page, 'gift for wife under 500');
  await submitAndWait(page);
  await shot(page, '13-nlp-gift-under-500.png');

  // ─── 2m: NLP — date night dress ──────────────────────────────────────
  console.log('2m: NLP date night');
  await loadPage(page);
  await typeSearch(page, 'date night dress under 300');
  await submitAndWait(page);
  await shot(page, '13b-nlp-date-night.png');

  // ─── 2m: NLP — investment piece handbag ──────────────────────────────
  console.log('2m: NLP investment handbag');
  await loadPage(page);
  await typeSearch(page, 'investment piece handbag');
  await submitAndWait(page);
  await shot(page, '13c-nlp-investment.png');

  // ─── 2n: Dynamic Facets ───────────────────────────────────────────────
  console.log('2n: Facets shoes');
  await loadPage(page);
  await typeSearch(page, 'shoes');
  await submitAndWait(page);
  await shot(page, '14-facets-shoes.png');
  console.log('2n: Facets watches');
  await loadPage(page);
  await typeSearch(page, 'watches');
  await submitAndWait(page);
  await shot(page, '14b-facets-watches.png');

  // ─── 2o: Popular Searches ─────────────────────────────────────────────
  console.log('2o: Popular searches');
  await loadPage(page);
  await focusSearch(page);
  await sleep(2000);
  await shot(page, '15-popular-searches.png');

  // ─── 2p: Dynamic Categories ───────────────────────────────────────────
  console.log('2p: Dynamic categories');
  await loadPage(page);
  await typeSearch(page, 'lv sp');
  await sleep(500);
  await shot(page, '16-dynamic-categories.png');

  // ─── 2q: Personalization ──────────────────────────────────────────────
  console.log('2q: Personalization');
  // Browse bags first
  await page.goto(`${BASE}/women/bags`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(3000);
  // Now search broadly
  await loadPage(page);
  await typeSearch(page, 'bag');
  await submitAndWait(page);
  await shot(page, '17-personalization-bag.png');

  // ─── 2r: PDP Recommendations ──────────────────────────────────────────
  console.log('2r: PDP');
  await page.goto(`${BASE}/women/bags`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(4000);
  try {
    const link = await page.$('a[href*="/product/"], a[href*="/p/"]');
    if (link) {
      const href = await link.getAttribute('href');
      const pdpUrl = href.startsWith('http') ? href : `${BASE}${href}`;
      await page.goto(pdpUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await sleep(4000);
      await page.evaluate(() => window.scrollBy(0, 1500));
      await sleep(2000);
      await shot(page, '18-recommendations-pdp.png');
    } else {
      await shot(page, '18-recommendations-no-pdp.png');
    }
  } catch(e) {
    console.log('  PDP error:', e.message.substring(0, 80));
    await shot(page, '18-recommendations-err.png');
  }

  // ─── 2s: Banners — sale ───────────────────────────────────────────────
  console.log('2s: Banners sale');
  await loadPage(page);
  await typeSearch(page, 'sale');
  await submitAndWait(page);
  await shot(page, '19-banners-sale.png');

  // ─── 2t: Analytics Badges ─────────────────────────────────────────────
  console.log('2t: Analytics');
  await loadPage(page);
  await typeSearch(page, 'chanel');
  await submitAndWait(page);
  await page.evaluate(() => window.scrollBy(0, 600));
  await sleep(800);
  await shot(page, '20-analytics-chanel.png');

  await browser.close();

  console.log('\n=== Vendor Detection ===');
  if (vendors.size > 0) vendors.forEach(u => console.log(' FOUND:', u));
  else console.log(' None detected');

  const files = fs.readdirSync(SHOTS).filter(f => f.endsWith('.png'));
  const sizes = files.map(f => fs.statSync(path.join(SHOTS, f)).size);
  const good = files.filter((f,i) => sizes[i] > 50000).length;
  const small = files.filter((f,i) => sizes[i] < 50000);
  console.log(`\n=== ${files.length} total | ${good} good (>50KB) | ${small.length} small ===`);
  if (small.length) console.log('Small:', small.join(', '));
}

main().catch(console.error);
