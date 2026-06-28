const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const context = await browser.newContext({ 
    viewport: { width: 1440, height: 900 }, 
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' 
  });
  const page = await context.newPage();
  
  await page.goto('https://www.thenorthface.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);
  
  const title = await page.title();
  console.log('Page title:', title);
  
  // Find ALL input elements
  const inputs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('input')).map(el => ({
      type: el.type,
      name: el.name,
      id: el.id,
      placeholder: el.placeholder,
      className: el.className.substring(0,80),
      ariaLabel: el.getAttribute('aria-label'),
      dataTestId: el.getAttribute('data-testid'),
      visible: window.getComputedStyle(el).display !== 'none'
    }));
  });
  console.log('All inputs:', JSON.stringify(inputs, null, 2));
  
  // Check for search-related elements
  const searchEls = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll('button, [role="button"]'));
    return els.filter(el => {
      const text = ((el.textContent || '') + (el.getAttribute('aria-label') || '') + (el.className || '')).toLowerCase();
      return text.includes('search');
    }).slice(0,8).map(el => ({
      tag: el.tagName,
      text: el.textContent.trim().substring(0,60),
      ariaLabel: el.getAttribute('aria-label'),
      className: el.className.substring(0,80),
      id: el.id
    }));
  });
  console.log('Search buttons:', JSON.stringify(searchEls, null, 2));
  
  await browser.close();
})();
