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
  console.log(`  📸 ${name}.png — ${size} bytes`);
  return path;
}

const QUERIES = [
  ['nikee-air-max', 'nikee+air+max', '05-typo-nikee-air-max'],
  ['kicks', 'kicks', '06-synonym-kicks'],
  ['Jordan', 'Jordan', '09-intent-jordan'],
  ['basketball-shoes', 'basketball+shoes', '14-dynamic-facets-basketball'],
  ['nlp-sneakers', 'comfortable+sneakers+under+100', '13-nlp-sneakers-under-100'],
  ['sale', 'sale', '19-banners-sale'],
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const BASE = 'https://www.footlocker.com/';

  for (const [label, query, filename] of QUERIES) {
    // Skip if already exists
    if (fs.existsSync(`${SCREENSHOTS_DIR}/${filename}.png`)) {
      console.log(`  SKIP: ${filename}.png already exists`);
      continue;
    }
    console.log(`Trying: ${label}`);
    try {
      await page.goto(`${BASE}search?query=${query}`, { waitUntil: 'domcontentloaded', timeout: 40000 });
      await sleep(3000);
      await takeShot(page, filename);
    } catch(e) {
      console.log(`  FAIL ${label}: ${e.message.slice(0,60)}`);
      // try with networkidle
      try {
        await page.goto(`${BASE}search?query=${query}`, { waitUntil: 'load', timeout: 40000 });
        await sleep(3000);
        await takeShot(page, filename);
      } catch(e2) {
        console.log(`  RETRY FAIL: ${e2.message.slice(0,60)}`);
      }
    }
    await sleep(2000);
  }

  await browser.close();
  console.log('Done.');
})().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
