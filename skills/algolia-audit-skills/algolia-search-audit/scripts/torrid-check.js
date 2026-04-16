const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
  });
  const page = await ctx.newPage();
  page.setDefaultNavigationTimeout(60000);
  
  await page.goto('https://www.torrid.com', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(3000);
  
  const title = await page.title();
  const url = page.url();
  const bodyText = await page.evaluate(() => document.body.innerText.slice(0, 500));
  const html = await page.content();
  
  console.log('Title:', title);
  console.log('URL:', url);
  console.log('Body text:', bodyText);
  console.log('Has challenge:', html.includes('challenge') || html.includes('blocked') || html.includes('Checking'));
  console.log('Has search input:', html.includes('SearchInput') || html.includes('search-input') || html.includes('type="search"'));
  console.log('HTML length:', html.length);
  
  await browser.close();
})().catch(e => console.error(e.message));
