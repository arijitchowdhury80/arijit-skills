const { addExtra } = require('../node_modules/playwright-extra');
const StealthPlugin = require('../node_modules/puppeteer-extra-plugin-stealth');
const { chromium } = require('../node_modules/playwright');
const path = require('path');
const fs = require('fs');

const pChromium = addExtra(chromium);
pChromium.use(StealthPlugin());

const AUDIT_DIR = process.env.AUDIT_DIR;
const screenshotsDir = path.join(AUDIT_DIR, 'Torrid/deliverables/screenshots');

const pages = [
  { url: 'https://www.torrid.com/category/dresses', filename: '04-results-dresses.png' },
  { url: 'https://www.torrid.com/search?q=plus+size+jeans', filename: '05-plus-size-jeans.png' },
  { url: 'https://www.torrid.com/search?q=cardigan', filename: '06-search-cardigan.png' },
  { url: 'https://www.torrid.com/search?q=qwerty12345nonsense', filename: '07-no-results.png' },
  { url: 'https://www.torrid.com/search?q=return+policy', filename: '08-non-product.png' },
  { url: 'https://www.torrid.com/search?q=date+night+dress+that+hides+tummy', filename: '13-nlp-hides-tummy.png' },
  { url: 'https://www.torrid.com/search?q=gift+for+curvy+woman+under+100', filename: '13-nlp-gift.png' },
];

async function run() {
  const browser = await pChromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'en-US',
  });
  const page = await context.newPage();
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    delete navigator.__proto__.webdriver;
  });

  for (const p of pages) {
    try {
      console.log(`Testing: ${p.url}`);
      await page.goto(p.url, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForTimeout(4000);
      const title = await page.title();
      const filepath = path.join(screenshotsDir, p.filename);
      await page.screenshot({ path: filepath, fullPage: false });
      const size = fs.statSync(filepath).size;
      console.log(`📸 ${p.filename} — ${size} bytes | ${title.slice(0, 60)}`);
    } catch (e) {
      console.log(`⚠️  ${p.filename}: ${e.message.slice(0, 80)}`);
    }
    await page.waitForTimeout(3000);
  }
  await browser.close();
  console.log('Complete');
}

run().catch(e => console.error('Fatal:', e.message));
