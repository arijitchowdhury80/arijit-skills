const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());
const path = require('path');
const fs = require('fs');

const SCREENSHOTS_DIR = '/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit/The North Face/deliverables/screenshots';

(async () => {
  const b = await chromium.launch({ headless: false, args: ['--no-sandbox', '--disable-blink-features=AutomationControlled'] });
  const ctx = await b.newContext({ 
    viewport: {width:1440,height:900},
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'en-US'
  });
  await ctx.addInitScript(() => { Object.defineProperty(navigator,'webdriver',{get:()=>undefined}); });
  const page = await ctx.newPage();
  
  const tests = [
    { url: 'https://www.thenorthface.com/search?q=jackets', file: 'check-search.png', name: '/search' },
    { url: 'https://www.thenorthface.com/en-us/search?q=jackets', file: 'check-enus-search.png', name: '/en-us/search' }
  ];
  
  for (const t of tests) {
    await page.goto(t.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(4000);
    const title = await page.title();
    const hasCaptcha = await page.$('#px-captcha-modal') !== null;
    const content = await page.content();
    const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 300));
    const filepath = path.join(SCREENSHOTS_DIR, t.file);
    await page.screenshot({ path: filepath });
    const size = fs.statSync(filepath).size;
    console.log(`\n${t.name}:`);
    console.log(`  URL: ${t.url}`);
    console.log(`  Title: ${title}`);
    console.log(`  CAPTCHA: ${hasCaptcha}`);
    console.log(`  Size: ${size} bytes`);
    console.log(`  Text: ${bodyText.replace(/\n/g,' ').substring(0,200)}`);
  }
  
  await b.close();
})();
