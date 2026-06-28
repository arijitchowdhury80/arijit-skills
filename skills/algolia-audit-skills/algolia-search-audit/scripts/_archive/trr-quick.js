const { chromium } = require('playwright-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const path = require('path');
const fs = require('fs');
chromium.use(StealthPlugin());

const SHOTS = '/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit/Therealreal/deliverables/screenshots';
const BASE = 'https://www.therealreal.com';

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
async function shot(page, name) {
  const fp = path.join(SHOTS, name);
  await page.screenshot({ path: fp });
  const sz = fs.statSync(fp).size;
  console.log(`📸 ${name} — ${sz.toLocaleString()} bytes ${sz > 100000 ? '✓' : '⚠'}`);
  return sz;
}

async function jsClick(page, sel) {
  await page.evaluate((s) => { const el = document.querySelector(s); if (el) { el.dispatchEvent(new MouseEvent('click', {bubbles:true})); el.focus(); }}, sel);
  await sleep(500);
}

async function main() {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
  });
  const vendors = new Set();
  context.on('request', req => {
    const u = req.url();
    if (/algolia|cnstrc|constructor\.io|bloomreach|coveo|klevu|searchspring/i.test(u)) vendors.add(u);
  });
  
  const page = await context.newPage();
  
  // Homepage
  console.log('Loading homepage...');
  await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await sleep(4000);
  // Dismiss modal via keyboard
  await page.keyboard.press('Escape'); await sleep(500);
  // Remove blocking overlays
  await page.evaluate(() => {
    document.querySelectorAll('[data-block-page-scroll]').forEach(el => el.remove());
  });
  await shot(page, '01-homepage.png');
  
  // Empty state — click search using jsClick
  await jsClick(page, '#search-bar-input');
  await sleep(2000);
  await shot(page, '02-empty-state.png');
  
  // SAYT — type without pressing enter
  await page.evaluate(() => { const el = document.querySelector('#search-bar-input'); if(el) el.value=''; });
  for (const ch of 'chan') { await page.keyboard.type(ch, {delay: 80}); }
  await sleep(2000);
  await shot(page, '03-sayt-chan.png');
  
  // Full results — press Enter after typing more
  for (const ch of 'el') { await page.keyboard.type(ch, {delay: 80}); }
  await page.keyboard.press('Enter');
  await sleep(5000);
  console.log('After chanel search URL:', page.url());
  await shot(page, '04-results-chanel.png');
  
  console.log('\nVendors:', vendors.size > 0 ? [...vendors].join('\n') : 'none');
  await browser.close();
}
main().catch(console.error);
