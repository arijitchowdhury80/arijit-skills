const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());

const path = require('path');
const fs = require('fs');

const AUDIT_DIR = "/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit";
const COMPANY = "Torrid";
const URL = "https://www.torrid.com";
const SS_DIR = path.join(AUDIT_DIR, COMPANY, 'deliverables', 'screenshots');

fs.mkdirSync(SS_DIR, { recursive: true });

const SEARCH_SELECTORS = [
  '#SearchInput', 'input[type="search"]', 'input[name="q"]',
  'input[name="search"]', 'input[placeholder*="Search" i]',
  '[data-testid="search-input"]', '[data-testid*="search" i]',
  '.search-input', '.searchInput', '#search-input',
  'input[aria-label*="Search" i]', 'header input[type="text"]'
];

async function findSearchInput(page) {
  for (const sel of SEARCH_SELECTORS) {
    try {
      await page.waitForSelector(sel, { timeout: 3000 });
      return sel;
    } catch { continue; }
  }
  return null;
}

async function shot(page, filename, note) {
  const fp = path.join(SS_DIR, filename);
  await page.screenshot({ path: fp, fullPage: false });
  const sz = fs.statSync(fp).size;
  console.log(`📸 ${filename} — ${sz} bytes ${sz < 50000 ? '⚠️ SMALL' : '✓'}  ${note || ''}`);
  return fp;
}

async function checkWAF(page) {
  const title = await page.title().catch(() => '');
  const body = await page.content().catch(() => '');
  return title.includes('Access Denied') || title.includes('Just a moment') ||
    title.includes('403') || body.includes('ray ID') || body.includes('Checking your browser');
}

async function typeQuery(page, sel, q) {
  await page.click(sel);
  await page.waitForTimeout(500);
  await page.fill(sel, '');
  await page.type(sel, q, { delay: 80 });
  await page.waitForTimeout(1500);
}

(async () => {
  console.log('🚀 Torrid Browser Audit — Playwright Stealth');
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox','--disable-setuid-sandbox'] });
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'en-US',
  });
  const page = await ctx.newPage();
  page.setDefaultTimeout(60000);
  page.setDefaultNavigationTimeout(60000);

  const results = [];

  // ── 2a: Homepage ──
  console.log('\n[2a] Homepage...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(3000);
    const waf = await checkWAF(page);
    const title = await page.title();
    console.log(`  Title: ${title} | WAF: ${waf}`);
    await shot(page, '01-homepage.png', 'Homepage');
    results.push({ step: '2a', status: waf ? 'WAF' : 'OK', title });
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2a', status: 'ERROR', error: e.message }); }

  // ── Find search input ──
  const searchSel = await findSearchInput(page);
  console.log(`  Search input: ${searchSel || 'NOT FOUND'}`);

  // ── 2b: Empty state ──
  console.log('\n[2b] Empty state...');
  try {
    if (searchSel) {
      await page.click(searchSel);
      await page.waitForTimeout(1500);
    }
    await shot(page, '02-empty-state.png', 'Empty state');
    results.push({ step: '2b', status: 'OK', searchSel });
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2b', status: 'ERROR', error: e.message }); }

  // ── 2c: SAYT ──
  console.log('\n[2c] SAYT — "dress"...');
  try {
    if (searchSel) {
      await typeQuery(page, searchSel, 'dress');
      await shot(page, '03-sayt-dress.png', 'SAYT dress');
    } else { console.log('  No search input'); }
    results.push({ step: '2c', status: 'OK' });
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2c', status: 'ERROR', error: e.message }); }

  // ── 2a½: Network vendor verification + 2d: Full results ──
  console.log('\n[2d] Full results — "dress"...');
  try {
    if (searchSel) {
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      const resultUrl = page.url();
      console.log(`  URL: ${resultUrl}`);
      await shot(page, '04-results-dress.png', 'Full results dress');
      results.push({ step: '2d', status: 'OK', url: resultUrl });
    }
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2d', status: 'ERROR', error: e.message }); }

  // ── 2a½: Network vendor verification (check URL pattern on results page) ──
  console.log('\n[2a½] Vendor verification...');
  try {
    const networkVendors = [];
    // Intercept next navigation to see API calls
    const requests = [];
    page.on('request', req => {
      const u = req.url();
      if (u.includes('brsrvr.com') || u.includes('bloomreach.com') || u.includes('algolia') || u.includes('coveo') || u.includes('klevu') || u.includes('searchspring')) {
        requests.push(u);
      }
    });
    // Search again to capture network
    if (searchSel) {
      await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.waitForTimeout(2000);
      const s = await findSearchInput(page);
      if (s) {
        await typeQuery(page, s, 'jeans');
        await page.keyboard.press('Enter');
        await page.waitForLoadState('domcontentloaded');
        await page.waitForTimeout(2000);
      }
    }
    console.log(`  Vendor API calls: ${requests.length > 0 ? requests.join(', ') : 'none captured'}`);
    results.push({ step: '2a½', status: 'OK', vendors: requests });
  } catch(e) { console.log('  ❌', e.message); }

  // ── 2e: Typo tolerance ──
  console.log('\n[2e] Typo — "cardgan"...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'cardgan');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      const txt = await page.textContent('body').catch(() => '');
      const resultCount = txt.match(/(\d+)\s+results?/i)?.[0] || 'unknown';
      console.log(`  Result text: ${resultCount}`);
      await shot(page, '05-typo-cardgan.png', 'Typo cardgan');
      results.push({ step: '2e', status: 'OK', query: 'cardgan', resultCount });
    }
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2e', status: 'ERROR', error: e.message }); }

  // ── 2f: Synonym ──
  console.log('\n[2f] Synonym — "plus size jeans"...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'plus size jeans');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      await shot(page, '06-synonym-plus-size-jeans.png', 'Synonym plus size jeans');
      results.push({ step: '2f', status: 'OK' });
    }
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2f', status: 'ERROR', error: e.message }); }

  // ── 2g: No results ──
  console.log('\n[2g] No results — "qwerty"...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'qwerty');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      await shot(page, '07-no-results.png', 'No results qwerty');
      results.push({ step: '2g', status: 'OK' });
    }
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2g', status: 'ERROR', error: e.message }); }

  // ── 2h: Non-product content ──
  console.log('\n[2h] Non-product — "return policy"...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'return policy');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      await shot(page, '08-non-product-return-policy.png', 'Non-product return policy');
      results.push({ step: '2h', status: 'OK' });
    }
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2h', status: 'ERROR', error: e.message }); }

  // ── 2i: Intent detection ──
  console.log('\n[2i] Intent — "Lovesick"...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'Lovesick');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      await shot(page, '09-intent-lovesick.png', 'Intent Lovesick sub-brand');
      results.push({ step: '2i', status: 'OK' });
    }
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2i', status: 'ERROR', error: e.message }); }

  // ── 2j: Merchandising consistency ──
  console.log('\n[2j] Merchandising — search "jeans" vs browse...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'jeans');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      await shot(page, '10-merchandising.png', 'Merchandising jeans search');
    }
    results.push({ step: '2j', status: 'OK' });
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2j', status: 'ERROR', error: e.message }); }

  // ── 2k: Federated search ──
  console.log('\n[2k] Federated — SAYT content types...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'swim');
      await shot(page, '11-federated.png', 'Federated SAYT swim');
    }
    results.push({ step: '2k', status: 'OK' });
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2k', status: 'ERROR', error: e.message }); }

  // ── 2l: Mobile ──
  console.log('\n[2l] Mobile viewport...');
  try {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    await shot(page, '12-mobile-homepage.png', 'Mobile homepage');
    // Try mobile search
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'plus size swimwear');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      await shot(page, '12-mobile-swimwear.png', 'Mobile swimwear');
    }
    results.push({ step: '2l', status: 'OK' });
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2l', status: 'ERROR', error: e.message }); }

  // Reset to desktop
  await page.setViewportSize({ width: 1440, height: 900 });

  // ── 2m: Semantic NLP ──
  console.log('\n[2m] NLP — "gift for curvy woman under $100"...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'gift for curvy woman under $100');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      const txt = await page.textContent('body').catch(() => '');
      const rc = txt.match(/(\d+)\s+results?/i)?.[0] || 'unknown count';
      console.log(`  Result: ${rc}`);
      await shot(page, '13-nlp-gift-curvy.png', 'NLP gift curvy');
      results.push({ step: '2m', status: 'OK', query: 'gift for curvy woman under $100', resultCount: rc });
    }
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2m', status: 'ERROR', error: e.message }); }

  // ── 2m2: NLP "date night dress that hides tummy" ──
  console.log('\n[2m2] NLP — "date night dress that hides tummy"...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'date night dress that hides tummy');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      const txt = await page.textContent('body').catch(() => '');
      const rc = txt.match(/(\d+)\s+results?/i)?.[0] || 'unknown count';
      console.log(`  Result: ${rc}`);
      await shot(page, '13-nlp-date-night.png', 'NLP date night dress hides tummy');
      results.push({ step: '2m2', status: 'OK', query: 'date night dress that hides tummy', resultCount: rc });
    }
  } catch(e) { console.log('  ❌', e.message); }

  // ── 2n: Dynamic facets ──
  console.log('\n[2n] Dynamic facets — "swimwear"...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'swimwear');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      await shot(page, '14-dynamic-facets.png', 'Dynamic facets swimwear');
      results.push({ step: '2n', status: 'OK' });
    }
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2n', status: 'ERROR', error: e.message }); }

  // ── 2o: Popular/recent searches ──
  console.log('\n[2o] Popular searches...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await page.click(s);
      await page.waitForTimeout(1500);
      await shot(page, '15-popular-searches.png', 'Popular/recent searches');
    }
    results.push({ step: '2o', status: 'OK' });
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2o', status: 'ERROR', error: e.message }); }

  // ── 2p: Dynamic categories in SAYT ──
  console.log('\n[2p] Dynamic categories — SAYT "plus"...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'plus');
      await shot(page, '16-dynamic-categories.png', 'Dynamic categories SAYT plus');
    }
    results.push({ step: '2p', status: 'OK' });
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2p', status: 'ERROR', error: e.message }); }

  // ── 2q: Personalization ──
  console.log('\n[2q] Personalization...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    // Browse a few categories first
    const links = await page.$$eval('a[href*="/c/"]', els => els.slice(0,3).map(e => e.href));
    for (const l of links) {
      await page.goto(l, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {});
      await page.waitForTimeout(1000);
    }
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'dress');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
    }
    await shot(page, '17-personalization.png', 'Personalization test');
    results.push({ step: '2q', status: 'OK' });
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2q', status: 'ERROR', error: e.message }); }

  // ── 2r: Recommendations ──
  console.log('\n[2r] Recommendations on PDP...');
  try {
    // Navigate to a product page
    await page.goto('https://www.torrid.com/c/dresses', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    // Click first product
    const productLinks = await page.$$eval('a[href*="/p/"]', els => els.slice(0,1).map(e => e.href));
    if (productLinks.length) {
      await page.goto(productLinks[0], { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.waitForTimeout(2000);
      await shot(page, '18-recommendations.png', 'Product page recommendations');
      results.push({ step: '2r', status: 'OK', pdpUrl: productLinks[0] });
    } else {
      await shot(page, '18-recommendations.png', 'Category page (no PDP found)');
      results.push({ step: '2r', status: 'PARTIAL' });
    }
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2r', status: 'ERROR', error: e.message }); }

  // ── 2s: Banners & merchandising rules ──
  console.log('\n[2s] Banners — "sale"...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'sale');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      await shot(page, '19-banners.png', 'Banners sale search');
      results.push({ step: '2s', status: 'OK' });
    }
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2s', status: 'ERROR', error: e.message }); }

  // ── 2t: Analytics visibility (bestseller, trending) ──
  console.log('\n[2t] Analytics — trending/bestseller badges...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'denim');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      await shot(page, '20-analytics.png', 'Analytics denim');
      results.push({ step: '2t', status: 'OK' });
    }
  } catch(e) { console.log('  ❌', e.message); results.push({ step: '2t', status: 'ERROR', error: e.message }); }

  // ── Additional: Typo "legins" ──
  console.log('\n[2e2] Typo — "legins"...');
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(2000);
    const s = await findSearchInput(page);
    if (s) {
      await typeQuery(page, s, 'legins');
      await page.keyboard.press('Enter');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000);
      const txt = await page.textContent('body').catch(() => '');
      const rc = txt.match(/(\d+)\s+results?/i)?.[0] || 'unknown';
      await shot(page, '05-typo-legins.png', `Typo legins — ${rc}`);
    }
  } catch(e) { console.log('  ❌', e.message); }

  await browser.close();

  // ── Summary ──
  const files = fs.readdirSync(SS_DIR).filter(f => f.endsWith('.png'));
  console.log(`\n✅ Browser audit complete — ${files.length} screenshots`);
  console.log('Files:', files.join(', '));
  console.log('\nStep results:', JSON.stringify(results, null, 2));

})().catch(e => { console.error('FATAL:', e.message); process.exit(1); });
