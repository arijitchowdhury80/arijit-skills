const { chromium } = require('playwright-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
chromium.use(StealthPlugin());
const fs = require('fs');

const SCREENSHOTS_DIR = process.argv[2];

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function takeShot(page, name) {
  const path = `${SCREENSHOTS_DIR}/${name}.png`;
  await page.screenshot({ path, fullPage: false });
  const size = fs.statSync(path).size;
  console.log(`  📸 ${name}.png — ${size} bytes ✓`);
  return path;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const BASE = 'https://www.footlocker.com/';
  
  // Step 2d: running shoes full results
  console.log('Step 2d: running shoes results');
  try {
    await page.goto(BASE + 'search?query=running+shoes', { waitUntil: 'domcontentloaded', timeout: 25000 });
    await sleep(2500);
    await takeShot(page, '04-results-running-shoes');
  } catch(e) { console.log(`  FAIL: ${e.message}`); }

  // Step 2e: nikee air max typo
  console.log('Step 2e: nikee air max typo');
  try {
    await page.goto(BASE + 'search?query=nikee+air+max', { waitUntil: 'domcontentloaded', timeout: 25000 });
    await sleep(2500);
    await takeShot(page, '05-typo-nikee-air-max');
  } catch(e) { console.log(`  FAIL: ${e.message}`); }

  // Step 2f: synonym kicks
  console.log('Step 2f: kicks synonym');
  try {
    await page.goto(BASE + 'search?query=kicks', { waitUntil: 'domcontentloaded', timeout: 25000 });
    await sleep(2500);
    await takeShot(page, '06-synonym-kicks');
  } catch(e) { console.log(`  FAIL: ${e.message}`); }

  // Step 2i: intent Jordan
  console.log('Step 2i: Jordan intent');
  try {
    await page.goto(BASE + 'search?query=Jordan', { waitUntil: 'domcontentloaded', timeout: 25000 });
    await sleep(2500);
    await takeShot(page, '09-intent-jordan');
  } catch(e) { console.log(`  FAIL: ${e.message}`); }

  // Step 2m: NLP comfortable sneakers under 100
  console.log('Step 2m: NLP query');
  try {
    await page.goto(BASE + 'search?query=comfortable+sneakers+under+100', { waitUntil: 'domcontentloaded', timeout: 25000 });
    await sleep(2500);
    await takeShot(page, '13-nlp-sneakers-under-100');
  } catch(e) { console.log(`  FAIL: ${e.message}`); }

  // Step 2n: dynamic facets basketball shoes
  console.log('Step 2n: basketball shoes facets');
  try {
    await page.goto(BASE + 'search?query=basketball+shoes', { waitUntil: 'domcontentloaded', timeout: 25000 });
    await sleep(2500);
    await takeShot(page, '14-dynamic-facets-basketball');
  } catch(e) { console.log(`  FAIL: ${e.message}`); }

  // Step 2r: recommendations PDP
  console.log('Step 2r: recommendations');
  try {
    await page.goto(BASE + 'search?query=Nike+Air+Force+1+white', { waitUntil: 'domcontentloaded', timeout: 25000 });
    await sleep(2500);
    await takeShot(page, '18-recommendations-af1');
  } catch(e) { console.log(`  FAIL: ${e.message}`); }

  // Step 2s: banners sale
  console.log('Step 2s: sale banners');
  try {
    await page.goto(BASE + 'search?query=sale', { waitUntil: 'domcontentloaded', timeout: 25000 });
    await sleep(2500);
    await takeShot(page, '19-banners-sale');
  } catch(e) { console.log(`  FAIL: ${e.message}`); }

  // Step 2t: analytics — best sellers
  console.log('Step 2t: analytics bestsellers');
  try {
    await page.goto(BASE + 'search?query=best+sellers', { waitUntil: 'domcontentloaded', timeout: 25000 });
    await sleep(2500);
    await takeShot(page, '20-analytics-bestsellers');
  } catch(e) { console.log(`  FAIL: ${e.message}`); }

  await browser.close();
  console.log('All extra steps done.');
})().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
