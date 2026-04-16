#!/usr/bin/env node
/**
 * audit-browser.js — Playwright + stealth browser audit for Algolia Search Audit
 * Replaces Chrome MCP for Phase 2 browser testing. Bypasses WAF (Akamai, Cloudflare).
 *
 * Usage:
 *   node audit-browser.js --company CostcoWholesale --url https://www.costco.com --audit-dir /path/to/audits
 *   node audit-browser.js --company Nike --url https://www.nike.com --step 2a --audit-dir /path
 *   node audit-browser.js --company DSW --url https://www.dsw.com --all-steps --audit-dir /path
 *   node audit-browser.js --test  (runs smoke test — navigates to example.com)
 */

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());

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
const allSteps = hasFlag('--all-steps');

// Canonical screenshots path
const screenshotsDir = path.join(auditDir, company, 'deliverables', 'screenshots');
const findingsPath = path.join(auditDir, company, 'research', '09-browser-findings.md');

// ── Search input selectors (try in order) ─────────────────────────────────────
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

// ── WAF check ─────────────────────────────────────────────────────────────────
async function checkWAF(page) {
  const title = await page.title().catch(() => '');
  const content = await page.content().catch(() => '');
  return title.includes('Access Denied') || title.includes('Just a moment') ||
         title.includes('403') || content.includes('ray ID') ||
         content.includes('Checking your browser');
}

// ── Individual step runners ───────────────────────────────────────────────────
const findings = [];

async function step2a(page) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(2000);
  if (await checkWAF(page)) { console.log('  ⛔ WAF detected on homepage'); return null; }
  const shot = await screenshot(page, '01-homepage.png', 'Initial observations');
  const searchSelector = await findSearchInput(page);
  findings.push({ step: '2a', screenshot: shot.filepath, observation: `Homepage loaded. Search input: ${searchSelector || 'NOT FOUND'}` });
  return searchSelector;
}

async function step2b(page, searchSel) {
  if (!searchSel) return;
  await page.click(searchSel);
  await page.waitForTimeout(1000);
  const shot = await screenshot(page, '02-empty-state.png', 'Empty state test');
  const html = await page.content();
  const hasSuggestions = html.includes('trending') || html.includes('popular') || html.includes('recent');
  findings.push({ step: '2b', screenshot: shot.filepath, observation: hasSuggestions ? 'Suggestions shown' : 'GAP: Blank empty state — no suggestions' });
}

async function step2c(page, searchSel, query) {
  if (!searchSel) return;
  await page.click(searchSel);
  await page.type(searchSel, query.slice(0, 4), { delay: 80 });
  await page.waitForTimeout(1500);
  const shot = await screenshot(page, `03-sayt-${query.slice(0,4)}.png`, `SAYT: "${query.slice(0,4)}"`);
  findings.push({ step: '2c', screenshot: shot.filepath, observation: `SAYT test for "${query}"`, query });
}

async function step2d(page, searchSel, query) {
  if (!searchSel) return;
  await page.fill(searchSel, query);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(3000);
  if (await checkWAF(page)) {
    const shot = await screenshot(page, '04-waf-block.png', 'WAF blocked full search');
    findings.push({ step: '2d', screenshot: shot.filepath, observation: `WAF BLOCKED: Full search for "${query}"`, waf_blocked: true });
    return;
  }
  const shot = await screenshot(page, `04-results-${query.replace(/\s+/g,'-').slice(0,15)}.png`, `Results: "${query}"`);
  const resultCount = await page.$eval('[data-count], .result-count, h1', el => el.textContent).catch(() => 'unknown');
  findings.push({ step: '2d', screenshot: shot.filepath, observation: `Results for "${query}": ${resultCount}`, query });
}

async function step2e(page, searchSel, typoQuery) {
  if (!searchSel) return;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(1500);
  const sel = await findSearchInput(page) || searchSel;
  await page.fill(sel, typoQuery);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  const shot = await screenshot(page, `05-typo-${typoQuery.replace(/\s+/g,'-')}.png`, `Typo: "${typoQuery}"`);
  findings.push({ step: '2e', screenshot: shot.filepath, observation: `Typo tolerance: "${typoQuery}"`, query: typoQuery });
}

async function step2g(page, searchSel) {
  if (!searchSel) return;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(1500);
  const sel = await findSearchInput(page) || searchSel;
  await page.fill(sel, 'asdfghjk');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  const shot = await screenshot(page, '07-no-results.png', 'No results test');
  findings.push({ step: '2g', screenshot: shot.filepath, observation: 'No results test with "asdfghjk"' });
}

async function step2h(page, searchSel) {
  if (!searchSel) return;
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(1500);
  const sel = await findSearchInput(page) || searchSel;
  await page.fill(sel, 'return policy');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  const shot = await screenshot(page, '08-non-product-return-policy.png', 'Non-product content');
  findings.push({ step: '2h', screenshot: shot.filepath, observation: 'Non-product content: "return policy"' });
}

async function step2l(page) {
  await page.setViewportSize({ width: 390, height: 844 }); // iPhone 14
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(1500);
  const shot = await screenshot(page, '12-mobile-viewport.png', 'Mobile viewport');
  findings.push({ step: '2l', screenshot: shot.filepath, observation: 'Mobile viewport (390×844)' });
  await page.setViewportSize({ width: 1440, height: 900 }); // Reset
}

// ── Network vendor detection ──────────────────────────────────────────────────
async function detectSearchVendor(page, searchSel, testQuery) {
  if (!searchSel) return 'unknown';
  const requests = [];
  page.on('request', req => { if (req.resourceType() === 'fetch' || req.resourceType() === 'xhr') requests.push(req.url()); });
  await page.click(searchSel);
  await page.type(searchSel, testQuery.slice(0,3), { delay: 60 });
  await page.waitForTimeout(1500);
  const VENDORS = { algolia: /algolia\.net|algolianet\.com/, coveo: /coveo\.com/, bloomreach: /brsrvr\.com|bloomreach\.com/, constructor: /cnstrc\.com/, searchspring: /searchspring\.io/, lucidworks: /lucidworks\.com|\/api\/apps\/.*\/query/ };
  for (const [name, regex] of Object.entries(VENDORS)) {
    if (requests.some(url => regex.test(url))) return `${name} ACTIVE`;
  }
  const vendorUrls = requests.filter(u => u.includes('search') || u.includes('query') || u.includes('suggest'));
  return vendorUrls.length > 0 ? `Unknown (${vendorUrls[0].split('/').slice(0,4).join('/')})` : 'Not detected';
}

// ── Main execution ─────────────────────────────────────────────────────────────
(async () => {
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
  console.log(`   Screenshots: ${screenshotsDir}`);
  console.log(`   Mode: ${isHeaded ? 'headed' : 'headless'} | Steps: ${stepFlag || (allSteps ? 'all' : 'core')}\n`);

  let browser;
  try {
    browser = await chromium.launch({ headless: !isHeaded, args: ['--no-sandbox', '--disable-setuid-sandbox'] });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' });
    const page = await context.newPage();

    // Step 2a — always first
    const searchSel = await step2a(page);

    // Detect search vendor
    if (searchSel) {
      console.log('  🔍 Detecting search vendor...');
      const vendor = await detectSearchVendor(page, searchSel, 'test');
      console.log(`  Vendor: ${vendor}`);
      findings.push({ step: '2a½', observation: `Search vendor: ${vendor}` });
      // Navigate back to homepage
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(1500);
    }

    if (stepFlag === '2a' || stepFlag === '2a½') { /* already done */ }
    else {
      // Core steps
      const freshSel = await findSearchInput(page) || searchSel;
      await step2b(page, freshSel);
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(1000);
      const sel2 = await findSearchInput(page) || freshSel;
      await step2c(page, sel2, 'television');
      await step2d(page, sel2, 'television');
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await page.waitForTimeout(1000);
      const sel3 = await findSearchInput(page) || freshSel;
      await step2e(page, sel3, 'samung tv');
      await step2g(page, sel3);
      await step2h(page, sel3);
      await step2l(page);
    }

    await browser.close();

    // Write findings
    const total = findings.length;
    const shots = findings.filter(f => f.screenshot).length;
    const wafBlocks = findings.filter(f => f.waf_blocked).length;

    console.log(`\n✅ Audit complete: ${total} steps, ${shots} screenshots, ${wafBlocks} WAF blocks\n`);

    // Append to 09-browser-findings.md
    const findingsText = findings.map(f => `### Step ${f.step}\n- Screenshot: ${f.screenshot || 'N/A'}\n- Observation: ${f.observation}\n`).join('\n');
    fs.mkdirSync(path.dirname(findingsPath), { recursive: true });
    fs.appendFileSync(findingsPath, `\n## Audit Run: ${new Date().toISOString()}\n${findingsText}`);
    console.log(`📝 Findings appended to: ${findingsPath}`);

    // Output JSON
    process.stdout.write(JSON.stringify({ company, url, steps_completed: total, screenshots: shots, waf_blocks: wafBlocks, findings }, null, 2));

  } catch (err) {
    console.error(`\n❌ Error: ${err.message}`);
    if (browser) await browser.close().catch(() => {});
    process.exit(1);
  }
})();
