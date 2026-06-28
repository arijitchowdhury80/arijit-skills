const { chromium } = require('playwright');
const fs = require('fs');

const AUDIT_DIR = "/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit";
const SCREENSHOTS_DIR = `${AUDIT_DIR}/JBL/deliverables/screenshots`;

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled', '--window-size=1440,900']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'en-US',
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    window.chrome = { runtime: {} };
  });

  const page = await context.newPage();

  console.log('Loading homepage with domcontentloaded...');
  await page.goto('https://www.jbl.com/', { waitUntil: 'domcontentloaded', timeout: 45000 });
  await sleep(8000); // Wait longer for Vue to hydrate

  const htmlSummary = await page.evaluate(() => {
    return {
      title: document.title,
      totalElements: document.querySelectorAll('*').length,
      buttons: document.querySelectorAll('button').length,
      inputs: document.querySelectorAll('input').length,
      links: document.querySelectorAll('a').length,
      images: document.querySelectorAll('img').length,
      bodyText: document.body?.innerText?.substring(0, 500) || 'NO BODY',
      htmlPreview: document.documentElement.innerHTML.substring(0, 1000),
      isAkamaiBlock: document.title.includes('Access') || document.body?.innerText?.includes('Access Denied') || false,
    };
  });
  
  console.log('HTML summary:', JSON.stringify({
    title: htmlSummary.title,
    totalElements: htmlSummary.totalElements,
    buttons: htmlSummary.buttons,
    inputs: htmlSummary.inputs,
    links: htmlSummary.links,
    images: htmlSummary.images,
    isAkamaiBlock: htmlSummary.isAkamaiBlock,
    bodyText: htmlSummary.bodyText.substring(0, 300),
  }, null, 2));

  // Search specifically for search-related elements
  const searchElements = await page.evaluate(() => {
    const elements = [];
    document.querySelectorAll('*').forEach(el => {
      const cls = (el.className || '').toString().toLowerCase();
      const id = (el.id || '').toLowerCase();
      const label = (el.getAttribute('aria-label') || '').toLowerCase();
      if (cls.includes('search') || id.includes('search') || label.includes('search')) {
        elements.push({
          tag: el.tagName,
          className: el.className.toString().substring(0, 60),
          id: el.id,
          ariaLabel: el.getAttribute('aria-label'),
          visible: el.offsetParent !== null,
          display: window.getComputedStyle(el).display
        });
      }
    });
    return elements;
  });
  console.log('Search elements found:', JSON.stringify(searchElements.slice(0,10), null, 2));

  await browser.close();
}

main().catch(console.error);
