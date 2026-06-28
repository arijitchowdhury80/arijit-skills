const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());

const SCREENSHOTS_DIR = '/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit/The North Face/deliverables/screenshots';
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--no-sandbox', '--disable-blink-features=AutomationControlled']
  });
  
  const context = await browser.newContext({ 
    viewport: { width: 1440, height: 900 }, 
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'en-US'
  });
  
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  });
  
  const page = await context.newPage();
  
  await page.goto('https://www.thenorthface.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(4000);
  
  console.log('Title:', await page.title());
  
  // Get ALL input elements with full details
  const inputs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('input')).map(el => {
      const rect = el.getBoundingClientRect();
      return {
        type: el.type,
        name: el.name,
        id: el.id,
        placeholder: el.placeholder,
        className: el.className.substring(0,100),
        ariaLabel: el.getAttribute('aria-label'),
        dataTestId: el.getAttribute('data-testid'),
        role: el.getAttribute('role'),
        visible: rect.width > 0 && rect.height > 0,
        width: rect.width,
        height: rect.height,
        parentTag: el.parentElement ? el.parentElement.tagName : 'none',
        parentClass: el.parentElement ? el.parentElement.className.substring(0,60) : ''
      };
    });
  });
  console.log('\nAll inputs (' + inputs.length + '):');
  inputs.forEach(i => console.log(JSON.stringify(i)));
  
  // Get search-related buttons
  const searchBtns = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('*')).filter(el => {
      const attrs = (el.getAttribute('aria-label') || '') + (el.getAttribute('data-testid') || '') + (el.className || '') + (el.id || '');
      return attrs.toLowerCase().includes('search');
    }).slice(0,15).map(el => {
      const rect = el.getBoundingClientRect();
      return {
        tag: el.tagName,
        id: el.id,
        className: el.className.substring(0,80),
        ariaLabel: el.getAttribute('aria-label'),
        dataTestId: el.getAttribute('data-testid'),
        role: el.getAttribute('role'),
        text: el.textContent.trim().substring(0,40),
        visible: rect.width > 0 && rect.height > 0,
        width: rect.width,
        height: rect.height
      };
    });
  });
  console.log('\nSearch-related elements (' + searchBtns.length + '):');
  searchBtns.forEach(b => console.log(JSON.stringify(b)));
  
  // Take a screenshot
  await page.screenshot({ path: path.join(SCREENSHOTS_DIR, '01-homepage-inspect.png') });
  console.log('\nScreenshot saved.');
  
  await browser.close();
})();
