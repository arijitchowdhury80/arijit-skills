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

  // Track ALL network requests
  const allRequests = [];
  const searchAPIRequests = [];
  context.on('request', req => {
    const url = req.url();
    allRequests.push(url);
    if (url.includes('api') || url.includes('search') || url.includes('query') || url.includes('suggest')) {
      searchAPIRequests.push({ url, method: req.method(), resourceType: req.resourceType() });
    }
  });

  const page = await context.newPage();

  // Navigate to homepage first
  console.log('=== Warming session on homepage ===');
  await page.goto('https://www.jbl.com/', { waitUntil: 'networkidle', timeout: 45000 });
  await sleep(3000);
  
  // Now click search icon and perform a real search
  console.log('=== Clicking search icon ===');
  try {
    await page.click('button[aria-label="Toggle Site Search"]', { timeout: 5000 });
    await sleep(2000);
    console.log('Search toggled');
    
    // Check if search input is now visible
    const inp = await page.waitForSelector('input[name="q"]', { state: 'visible', timeout: 5000 });
    console.log('Search input visible');
    await inp.click();
    await sleep(300);
    
    // Type "headphones" slowly
    await page.keyboard.type('headphones', { delay: 100 });
    await sleep(2500);
    
    // Screenshot SAYT
    const sspath = `${SCREENSHOTS_DIR}/03-sayt-speakers-v2.png`;
    await page.screenshot({ path: sspath });
    console.log(`SAYT screenshot: ${fs.statSync(sspath).size} bytes`);
    
    // Get SAYT HTML
    const saytContent = await page.evaluate(() => {
      const dropdown = document.querySelector('[class*="autocomplete"], [class*="suggestions"], [class*="typeahead"], [class*="search-dropdown"], [class*="sayt"], [role="listbox"], [class*="search-results-dropdown"]');
      return dropdown ? { found: true, html: dropdown.innerHTML.substring(0, 500), tagName: dropdown.tagName, className: dropdown.className } : { found: false };
    });
    console.log('SAYT dropdown:', JSON.stringify(saytContent, null, 2));
    
    // Submit search
    await page.keyboard.press('Enter');
    await sleep(5000);
    
    const resultsTitle = await page.title();
    const resultsUrl = page.url();
    console.log(`After submit — title: ${resultsTitle}, url: ${resultsUrl}`);
    
    const resultsHTML = await page.evaluate(() => {
      return {
        bodyText: document.body?.innerText?.substring(0, 800) || '',
        productCount: document.querySelectorAll('[class*="product-tile"], [class*="product-card"], [class*="result-item"]').length,
        searchInput: document.querySelector('input[name="q"]')?.value || 'none',
        noResults: document.querySelector('[class*="no-results"], [class*="zero-results"]') ? 'YES' : 'NO',
        facets: [...document.querySelectorAll('[class*="facet"], [class*="filter"]')].slice(0,3).map(el => el.className.substring(0,60)),
      };
    });
    console.log('Results page:', JSON.stringify(resultsHTML, null, 2));
    
    const ss = `${SCREENSHOTS_DIR}/04-results-headphones-v2.png`;
    await page.screenshot({ path: ss, fullPage: false });
    console.log(`Results screenshot: ${fs.statSync(ss).size} bytes`);
    
  } catch(e) {
    console.log('Search flow error:', e.message);
  }

  // Check the search API calls
  console.log('\n=== Search-related API calls ===');
  searchAPIRequests.forEach(r => console.log(`${r.method} [${r.resourceType}] ${r.url.substring(0, 150)}`));
  
  // Check for specific vendor signatures
  const hasAlgolia = allRequests.some(u => u.includes('algolia'));
  const hasCoveo = allRequests.some(u => u.includes('coveo'));
  const hasBazaarvoice = allRequests.some(u => u.includes('bazaarvoice'));
  const hasYottaa = allRequests.some(u => u.includes('yottaa'));
  const hasConstructor = allRequests.some(u => u.includes('constructor.io') || u.includes('cnstrc'));
  const hasBloomreach = allRequests.some(u => u.includes('bloomreach') || u.includes('brsrvr'));
  
  console.log('\n=== Vendor detection ===');
  console.log('Algolia:', hasAlgolia);
  console.log('Coveo:', hasCoveo);
  console.log('Bazaarvoice:', hasBazaarvoice);
  console.log('Yottaa CDN:', hasYottaa);
  console.log('Constructor.io:', hasConstructor);
  console.log('Bloomreach:', hasBloomreach);

  await browser.close();
}

main().catch(console.error);
