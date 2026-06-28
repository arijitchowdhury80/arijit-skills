const { chromium } = require('playwright');
const fs = require('fs');

const AUDIT_DIR = "/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit";
const SCREENSHOTS_DIR = `${AUDIT_DIR}/JBL/deliverables/screenshots`;

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function typeSlowly(page, text) {
  for (const char of text) {
    await page.keyboard.type(char, { delay: 80 + Math.random() * 80 });
  }
}

async function saveScreenshot(page, filename, label) {
  const fpath = `${SCREENSHOTS_DIR}/${filename}`;
  await page.screenshot({ path: fpath, fullPage: false });
  const size = fs.statSync(fpath).size;
  const status = size < 50000 ? '⚠️ SMALL' : size < 100000 ? '⚠️ MED' : '✅';
  console.log(`${status} ${filename}: ${size.toLocaleString()} bytes — ${label}`);
  return fpath;
}

async function openSearch(page) {
  // Try clicking search icon/button to reveal input
  const iconSelectors = [
    '[aria-label*="search" i]',
    'button[class*="search" i]',
    '[class*="search-icon"]',
    '[class*="search-toggle"]',
    '[class*="searchIcon"]',
    'button[title*="search" i]',
    '.header__search',
    'a[href="/search"]',
    'a[href*="search"]',
  ];

  for (const sel of iconSelectors) {
    try {
      const el = await page.$(sel);
      if (el) {
        const visible = await el.isVisible();
        if (visible) {
          console.log(`Clicking search trigger: ${sel}`);
          await el.click();
          await sleep(1500);
          break;
        }
      }
    } catch(e) {}
  }

  // Now find visible search input
  const inputSelectors = [
    'input[name="q"]:visible',
    'input[type="search"]:visible',
    'input[placeholder*="search" i]:visible',
    '#search-input',
    '.search-field',
    '[data-testid*="search"] input',
  ];

  for (const sel of inputSelectors) {
    try {
      await page.waitForSelector(sel, { state: 'visible', timeout: 5000 });
      console.log(`Search input ready: ${sel}`);
      return sel;
    } catch(e) {}
  }

  // Fallback: just try clicking any input[name="q"] using JS focus
  try {
    await page.evaluate(() => {
      const inp = document.querySelector('input[name="q"]');
      if (inp) { inp.style.display = 'block'; inp.style.visibility = 'visible'; inp.focus(); }
    });
    await sleep(500);
    console.log('Used JS focus fallback on input[name="q"]');
    return 'input[name="q"]';
  } catch(e) {}

  console.log('WARNING: Could not find visible search input');
  return null;
}

async function main() {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });

  const browser = await chromium.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-blink-features=AutomationControlled',
      '--disable-dev-shm-usage',
      '--window-size=1440,900',
    ]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'en-US',
    timezoneId: 'America/New_York',
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9',
      'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"macOS"',
    }
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    window.chrome = { runtime: {} };
    Object.defineProperty(navigator, 'platform', { get: () => 'MacIntel' });
  });

  // Track network requests for search vendor detection
  const networkRequests = [];
  context.on('request', req => {
    const url = req.url();
    if (url.includes('algolia') || url.includes('coveo') || url.includes('bloomreach') || 
        url.includes('klevu') || url.includes('searchspring') || url.includes('constructor') ||
        url.includes('elasticsearch') || url.includes('api') || url.includes('search')) {
      networkRequests.push({ url, method: req.method() });
    }
  });

  const page = await context.newPage();
  const findings = [];

  try {
    // ===== STEP 2a: Homepage =====
    console.log('\n=== STEP 2a: Homepage ===');
    await page.goto('https://www.jbl.com/', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await sleep(4000);
    const title = await page.title();
    console.log(`Title: ${title}`);
    await saveScreenshot(page, '01-homepage.png', 'Homepage initial state');

    // Inspect search area
    const searchIconCount = await page.evaluate(() => {
      return document.querySelectorAll('[aria-label*="search" i], button[class*="search" i], [class*="search-icon"]').length;
    });
    console.log(`Search icons/buttons found in DOM: ${searchIconCount}`);

    const allButtons = await page.evaluate(() => {
      return [...document.querySelectorAll('button, a')].filter(el => 
        el.textContent.toLowerCase().includes('search') || 
        el.getAttribute('aria-label')?.toLowerCase().includes('search') ||
        el.className.toLowerCase().includes('search')
      ).map(el => ({ tag: el.tagName, text: el.textContent.trim().substring(0,50), class: el.className.substring(0,80), ariaLabel: el.getAttribute('aria-label') }));
    });
    console.log('Search-related buttons:', JSON.stringify(allButtons.slice(0,5), null, 2));

    findings.push({
      step: '2a',
      screenshot: '01-homepage.png',
      observation: `Homepage loaded. Title: "${title}". Search buttons found: ${searchIconCount}`
    });

    // ===== STEP 2a½: Search vendor detection =====
    console.log('\n=== STEP 2a½: Search vendor network detection ===');

    // ===== STEP 2b: Empty state — click search =====
    console.log('\n=== STEP 2b: Empty State ===');

    // Try various search openers
    const searchOpeners = [
      '[aria-label="Search"]',
      '[aria-label="search"]',
      'button[aria-label*="earch"]',
      '.header-search',
      '.search-icon',
      'button.search',
      '[class*="header"] button',
      '[data-nav-item="search"]',
      'a[aria-label*="search" i]',
    ];

    let searchOpened = false;
    for (const sel of searchOpeners) {
      try {
        const el = await page.$(sel);
        if (el && await el.isVisible()) {
          await el.click({ force: true });
          await sleep(2000);
          console.log(`Opened search via: ${sel}`);
          searchOpened = true;
          break;
        }
      } catch(e) {}
    }

    // Check if there's a visible input now
    let searchInput = null;
    const inputCandidates = ['input[name="q"]', 'input[type="search"]', 'input[placeholder*="search" i]'];
    for (const sel of inputCandidates) {
      try {
        await page.waitForSelector(sel, { state: 'visible', timeout: 3000 });
        searchInput = sel;
        console.log(`Visible search input: ${sel}`);
        break;
      } catch(e) {}
    }

    if (!searchInput) {
      // Try navigating to search page directly
      console.log('Trying direct navigation to /search');
      await page.goto('https://www.jbl.com/search', { waitUntil: 'domcontentloaded', timeout: 30000 });
      await sleep(3000);
      for (const sel of inputCandidates) {
        try {
          await page.waitForSelector(sel, { state: 'visible', timeout: 3000 });
          searchInput = sel;
          console.log(`Visible search input on /search: ${sel}`);
          break;
        } catch(e) {}
      }
    }

    await saveScreenshot(page, '02-empty-state.png', 'Search bar open / empty state');
    findings.push({ step: '2b', screenshot: '02-empty-state.png', observation: `Search input: ${searchInput || 'not found'}, Search opened: ${searchOpened}` });

    // ===== STEP 2c: SAYT =====
    console.log('\n=== STEP 2c: SAYT ===');
    if (searchInput) {
      const inp = await page.$(searchInput);
      if (inp) {
        await inp.click({ force: true });
        await sleep(500);
        await page.keyboard.type('speak', { delay: 100 });
        await sleep(2000);
        await saveScreenshot(page, '03-sayt-speakers.png', 'SAYT after typing "speak"');
        findings.push({ step: '2c', screenshot: '03-sayt-speakers.png', observation: 'Typed "speak" - checking SAYT dropdown' });

        // Step 2d: Full results
        console.log('\n=== STEP 2d: Full Results ===');
        await page.keyboard.type('ers', { delay: 100 });
        await sleep(500);
        await page.keyboard.press('Enter');
        await sleep(4000);
        await saveScreenshot(page, '04-results-speakers.png', 'Search results for "speakers"');
        const resultCount = await page.evaluate(() => {
          const countEl = document.querySelector('[class*="result-count"], [class*="results-count"], [data-count]');
          return countEl ? countEl.textContent.trim() : 'unknown';
        });
        findings.push({ step: '2d', screenshot: '04-results-speakers.png', observation: `Results for "speakers". Count: ${resultCount}` });
      }
    } else {
      // Navigate to search results directly
      console.log('Using direct URL for search results');
      await page.goto('https://www.jbl.com/search?q=speakers', { waitUntil: 'domcontentloaded', timeout: 30000 });
      await sleep(4000);
      await saveScreenshot(page, '03-sayt-speakers.png', 'Direct search URL - speakers');
      await saveScreenshot(page, '04-results-speakers.png', 'Search results - speakers');
      findings.push({ step: '2c', screenshot: '03-sayt-speakers.png', observation: 'Direct URL navigation (SAYT not accessible)' });
      findings.push({ step: '2d', screenshot: '04-results-speakers.png', observation: 'Search results via direct URL' });
    }

    // ===== STEP 2e: Typo Tolerance =====
    console.log('\n=== STEP 2e: Typo Tolerance ===');
    await page.goto('https://www.jbl.com/search?q=bluetoth+speaker', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '05-typo-bluetoth-speaker.png', 'Typo test: "bluetoth speaker"');
    const typoPageTitle = await page.title();
    const typoBodySnippet = await page.evaluate(() => document.body?.innerText?.substring(0, 300) || '');
    console.log(`Typo result page: ${typoPageTitle}`);
    console.log(`Body snippet: ${typoBodySnippet.substring(0,200)}`);
    findings.push({ step: '2e', screenshot: '05-typo-bluetoth-speaker.png', observation: `Typo "bluetoth speaker" — title: ${typoPageTitle}` });

    // ===== STEP 2f: Synonym =====
    console.log('\n=== STEP 2f: Synonym ===');
    await page.goto('https://www.jbl.com/search?q=earphones', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '06-synonym-earphones.png', 'Synonym test: "earphones"');
    findings.push({ step: '2f', screenshot: '06-synonym-earphones.png', observation: 'Testing "earphones" vs "earbuds" synonym handling' });

    // ===== STEP 2g: No Results =====
    console.log('\n=== STEP 2g: No Results ===');
    await page.goto('https://www.jbl.com/search?q=xkcd+speaker+zzz', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '07-no-results.png', 'No results test: gibberish query');
    findings.push({ step: '2g', screenshot: '07-no-results.png', observation: 'Testing zero-results handling' });

    // ===== STEP 2h: Non-Product Content =====
    console.log('\n=== STEP 2h: Non-Product Content ===');
    await page.goto('https://www.jbl.com/search?q=return+policy', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '08-non-product-return-policy.png', 'Non-product: "return policy"');
    findings.push({ step: '2h', screenshot: '08-non-product-return-policy.png', observation: 'Testing content federation for "return policy"' });

    // ===== STEP 2i: Intent Detection =====
    console.log('\n=== STEP 2i: Intent Detection ===');
    await page.goto('https://www.jbl.com/search?q=JBL+Flip', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '09-intent-jbl-flip.png', 'Intent: "JBL Flip" sub-brand');
    findings.push({ step: '2i', screenshot: '09-intent-jbl-flip.png', observation: 'Testing sub-brand intent detection for "JBL Flip"' });

    // ===== STEP 2j: Merchandising Consistency =====
    console.log('\n=== STEP 2j: Merchandising Consistency ===');
    await page.goto('https://www.jbl.com/PORTABLE-BLUETOOTH-SPEAKERS/', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '10-merchandising-portable-speakers.png', 'Category page: portable speakers');
    findings.push({ step: '2j', screenshot: '10-merchandising-portable-speakers.png', observation: 'Category browse vs search comparison' });

    // ===== STEP 2k: Federated Search =====
    console.log('\n=== STEP 2k: Federated Search ===');
    await page.goto('https://www.jbl.com/search?q=warranty', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '11-federated-warranty.png', 'Federated: "warranty" - products or help content?');
    findings.push({ step: '2k', screenshot: '11-federated-warranty.png', observation: 'Testing federated search across products + content' });

    // ===== STEP 2l: Mobile =====
    console.log('\n=== STEP 2l: Mobile ===');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('https://www.jbl.com/', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '12-mobile-homepage.png', 'Mobile viewport: homepage');
    await page.goto('https://www.jbl.com/search?q=headphones', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '12b-mobile-headphones.png', 'Mobile search results: headphones');
    findings.push({ step: '2l', screenshot: '12-mobile-homepage.png', observation: 'Mobile experience - 390px viewport' });

    // Reset to desktop
    await page.setViewportSize({ width: 1440, height: 900 });

    // ===== STEP 2m: Semantic/NLP =====
    console.log('\n=== STEP 2m: Semantic/NLP ===');
    await page.goto('https://www.jbl.com/search?q=workout+headphones+under+100', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '13-nlp-workout-headphones.png', 'NLP: "workout headphones under 100"');
    const nlpBodySnippet = await page.evaluate(() => document.body?.innerText?.substring(0, 400) || '');
    console.log(`NLP result snippet: ${nlpBodySnippet.substring(0,300)}`);
    findings.push({ step: '2m', screenshot: '13-nlp-workout-headphones.png', observation: 'NLP test: "workout headphones under 100"' });

    // ===== STEP 2n: Dynamic Facets =====
    console.log('\n=== STEP 2n: Dynamic Facets ===');
    await page.goto('https://www.jbl.com/search?q=headphones', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '14-dynamic-facets-headphones.png', 'Facets for headphones search');
    findings.push({ step: '2n', screenshot: '14-dynamic-facets-headphones.png', observation: 'Dynamic facets for headphones category' });

    // ===== STEP 2o: Popular/Recent Searches =====
    console.log('\n=== STEP 2o: Popular Searches ===');
    // Go back to homepage and try opening search
    await page.goto('https://www.jbl.com/', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    // Try to open search bar
    try {
      await page.click('[aria-label*="search" i], button[class*="search" i], .search-icon', { force: true, timeout: 5000 });
      await sleep(2000);
    } catch(e) {}
    await saveScreenshot(page, '15-popular-searches.png', 'Popular searches / empty state after search history');
    findings.push({ step: '2o', screenshot: '15-popular-searches.png', observation: 'Popular/recent searches check' });

    // ===== STEP 2p: Dynamic Categories =====
    console.log('\n=== STEP 2p: Dynamic Categories ===');
    await page.goto('https://www.jbl.com/search?q=JBL+Charge', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '16-dynamic-categories-jbl-charge.png', 'Dynamic categories for "JBL Charge"');
    findings.push({ step: '2p', screenshot: '16-dynamic-categories-jbl-charge.png', observation: 'Dynamic category suggestions for sub-brand query' });

    // ===== STEP 2q: Personalization =====
    console.log('\n=== STEP 2q: Personalization ===');
    // Browse headphones then search broad
    await page.goto('https://www.jbl.com/HEADPHONES/', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(2000);
    await page.goto('https://www.jbl.com/search?q=audio', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '17-personalization-audio.png', 'Personalization signals after category browse');
    findings.push({ step: '2q', screenshot: '17-personalization-audio.png', observation: 'Personalization test: browse headphones then search "audio"' });

    // ===== STEP 2r: Recommendations =====
    console.log('\n=== STEP 2r: Recommendations ===');
    await page.goto('https://www.jbl.com/FLIP6.html', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(4000);
    await saveScreenshot(page, '18-recommendations-pdp.png', 'PDP recommendations: JBL Flip 6');
    findings.push({ step: '2r', screenshot: '18-recommendations-pdp.png', observation: 'PDP recommendations check on JBL Flip 6' });

    // ===== STEP 2s: Banners & Rules =====
    console.log('\n=== STEP 2s: Banners ===');
    await page.goto('https://www.jbl.com/search?q=sale', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '19-banners-sale.png', 'Banners/rules: "sale" search');
    findings.push({ step: '2s', screenshot: '19-banners-sale.png', observation: 'Merchandising rules/banners for "sale" query' });

    // ===== STEP 2t: Analytics Visibility =====
    console.log('\n=== STEP 2t: Analytics ===');
    await page.goto('https://www.jbl.com/HEADPHONES/', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    await saveScreenshot(page, '20-analytics-category.png', 'Analytics badges on category page');
    findings.push({ step: '2t', screenshot: '20-analytics-category.png', observation: 'Analytics visibility: bestseller/trending badges on category page' });

    // ===== Network summary =====
    console.log('\n=== Network requests (search/API) ===');
    const searchVendorRequests = networkRequests.filter(r => 
      r.url.includes('algolia') || r.url.includes('coveo') || r.url.includes('bloomreach') || 
      r.url.includes('klevu') || r.url.includes('constructor') || r.url.includes('searchspring')
    );
    console.log(`Search vendor API calls: ${searchVendorRequests.length}`);
    if (searchVendorRequests.length > 0) {
      searchVendorRequests.forEach(r => console.log(`  ${r.method} ${r.url.substring(0,100)}`));
    }

    // Sample all API calls
    const apiCalls = networkRequests.filter(r => r.url.includes('/api/') || r.url.includes('query') || r.url.includes('search?'));
    console.log(`Total API calls captured: ${apiCalls.length}`);
    apiCalls.slice(0, 10).forEach(r => console.log(`  ${r.url.substring(0, 120)}`));

  } catch (err) {
    console.error('Fatal error:', err.message);
  } finally {
    await browser.close();
  }

  // Print summary
  console.log('\n=== AUDIT COMPLETE ===');
  const files = fs.readdirSync(SCREENSHOTS_DIR).filter(f => f.endsWith('.png'));
  console.log(`Screenshots on disk: ${files.length}`);
  files.forEach(f => {
    const size = fs.statSync(`${SCREENSHOTS_DIR}/${f}`).size;
    console.log(`  ${f}: ${size.toLocaleString()} bytes`);
  });
}

main().catch(console.error);
