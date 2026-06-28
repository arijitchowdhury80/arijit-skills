const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());
const path = require('path');
const fs = require('fs');

const SITE_URL = 'https://www.homedepot.com.mx';
const SCREENSHOTS_DIR = '/Users/arijitchowdhury/AI-Development/Algolia Search Audit/HomeDepot-Mexico/deliverables/screenshots';

async function dismiss(page) {
  try {
    await page.waitForSelector('.MuiDialog-root', { timeout: 3000 });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(700);
    console.log('  Modal dismissed');
  } catch(e) {}
}

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox','--disable-setuid-sandbox'] });
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    locale: 'es-MX'
  });
  const page = await ctx.newPage();

  await page.goto(SITE_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(2000);
  await dismiss(page);

  // Focus search
  await page.evaluate(() => {
    const el = document.querySelector('#type-ahead-site-search-desktop');
    if(el) { el.focus(); }
  });
  await page.keyboard.type('herramientas electricas', { delay: 80 });
  await page.waitForTimeout(400);
  await page.keyboard.press('Enter');
  
  // Wait for navigation
  await page.waitForTimeout(5000);
  
  const finalUrl = page.url();
  const title = await page.title();
  const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 500));
  const waf = title.includes('Access') || title.includes('Denied') || title.includes('403') || bodyText.toLowerCase().includes('ray id') || bodyText.toLowerCase().includes('perimeter');
  
  console.log('Final URL:', finalUrl);
  console.log('Title:', title);
  console.log('WAF blocked:', waf);
  console.log('Body preview:', bodyText.slice(0, 300));
  
  // Take screenshot with wait
  await page.waitForTimeout(2000);
  const fp = path.join(SCREENSHOTS_DIR, '04-results-herramientas-v2.png');
  await page.screenshot({ path: fp, fullPage: false });
  const size = fs.statSync(fp).size;
  console.log('Screenshot size:', size, 'bytes');
  
  await browser.close();
})().catch(e => { console.error('Error:', e.message); process.exit(1); });
