/**
 * TNF Full Browser Audit — The North Face
 * Uses Playwright with stealth + headed mode + additional fingerprint evasion
 */

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());

const path = require('path');
const fs = require('fs');

const AUDIT_DIR = '/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit';
const COMPANY = 'The North Face';
const URL = 'https://www.thenorthface.com';
const SCREENSHOTS_DIR = path.join(AUDIT_DIR, COMPANY, 'deliverables', 'screenshots');
const FINDINGS_PATH = path.join(AUDIT_DIR, COMPANY, 'research', '09-browser-findings.md');

fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });

const findings = [];
let screenshotCount = 0;

async function shot(page, filename, label) {
  const filepath = path.join(SCREENSHOTS_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: false });
  const size = fs.statSync(filepath).size;
  screenshotCount++;
  const quality = size < 50000 ? '⚠️ SMALL' : '✓';
  console.log(`  📸 ${filename} — ${size} bytes ${quality} | ${label}`);
  return { filepath, size };
}

async function checkWAF(page) {
  const title = await page.title().catch(() => '');
  return title.includes('Access Denied') || title.includes('Just a moment') || title.includes('403');
}

async function findSearch(page) {
  const selectors = [
    'input[name="q"]',
    'input[type="search"]',
    '#SearchInput',
    'input[placeholder*="Search" i]',
    'input[placeholder*="search" i]',
    'input[aria-label*="Search" i]',
    '.search-input',
    '.searchInput',
    '[data-testid="search-input"]',
    '[data-testid*="search" i]',
    'header input',
    '.header-search input',
    '#search input',
    '.site-search input'
  ];
  for (const sel of selectors) {
    try {
      const el = await page.$(sel);
      if (el) {
        const visible = await el.isVisible();
        if (visible) {
          console.log(`  ✓ Search found: ${sel}`);
          return sel;
        }
      }
    } catch {}
  }
  // Try clicking a search icon to reveal search bar
  const searchIcons = [
    '[aria-label*="search" i]',
    '[aria-label*="Search" i]',
    '.search-icon',
    '.header-search-icon',
    'button.search',
    '[data-testid*="search"]'
  ];
  for (const iconSel of searchIcons) {
    try {
      const btn = await page.$(iconSel);
      if (btn) {
        console.log(`  🖱️ Clicking search icon: ${iconSel}`);
        await btn.click();
        await page.waitForTimeout(1000);
        for (const inputSel of selectors) {
          const el = await page.$(inputSel);
          if (el) {
            const visible = await el.isVisible();
            if (visible) {
              console.log(`  ✓ Search revealed: ${inputSel}`);
              return inputSel;
            }
          }
        }
      }
    } catch {}
  }
  console.log('  ⚠️ No search input found');
  return null;
}

async function typeSearch(page, sel, query) {
  await page.click(sel);
  await page.waitForTimeout(300);
  await page.fill(sel, '');
  await page.waitForTimeout(200);
  for (const char of query) {
    await page.type(sel, char, { delay: 60 + Math.random() * 40 });
  }
  await page.waitForTimeout(1500);
}

(async () => {
  console.log(`\n🔍 TNF Browser Audit — headed mode with extra stealth\n`);
  
  const browser = await chromium.launch({ 
    headless: false,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-blink-features=AutomationControlled',
      '--disable-infobars',
      '--start-maximized'
    ]
  });
  
  const context = await browser.newContext({ 
    viewport: { width: 1440, height: 900 }, 
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'en-US',
    timezoneId: 'America/New_York',
    permissions: ['geolocation'],
    geolocation: { latitude: 40.7128, longitude: -74.0060 }
  });
  
  // Extra stealth: override navigator properties
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    window.chrome = { runtime: {} };
  });
  
  const page = await context.newPage();
  
  try {
    // Step 2a: Homepage
    console.log('\n--- Step 2a: Homepage ---');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(4000);
    
    const isWAF = await checkWAF(page);
    if (isWAF) {
      console.log('  ⛔ WAF on homepage. Title:', await page.title());
      const s = await shot(page, '01-homepage-waf.png', 'WAF blocked');
      findings.push({ step: '2a', screenshot: s.filepath, observation: 'WAF BLOCKED — Access Denied on homepage' });
    } else {
      console.log('  ✅ Homepage loaded. Title:', await page.title());
      const s = await shot(page, '01-homepage.png', 'Homepage');
      const searchSel = await findSearch(page);
      findings.push({ step: '2a', screenshot: s.filepath, observation: `Homepage OK. Search: ${searchSel || 'NOT FOUND'}` });
      
      let netVendor = 'unknown';
      
      if (searchSel) {
        // Step 2a½: Vendor detection
        console.log('\n--- Step 2a½: Vendor Detection ---');
        const requests = [];
        page.on('request', req => {
          const url = req.url();
          if (url.includes('brsrvr') || url.includes('bloomreach') || url.includes('algolia') || 
              url.includes('coveo') || url.includes('cnstrc') || url.includes('searchspring')) {
            requests.push(url);
          }
        });
        await typeSearch(page, searchSel, 'jack');
        if (requests.length > 0) {
          console.log('  Search vendor requests:', requests.slice(0,3));
          netVendor = requests[0].includes('brsrvr') || requests[0].includes('bloomreach') ? 'BloomReach ACTIVE' :
                      requests[0].includes('algolia') ? 'Algolia ACTIVE' :
                      requests[0].includes('coveo') ? 'Coveo ACTIVE' :
                      requests[0].includes('cnstrc') ? 'Constructor.io ACTIVE' : 'Unknown';
        } else {
          netVendor = 'No search vendor API detected';
        }
        console.log('  Vendor:', netVendor);
        findings.push({ step: '2a½', observation: `Vendor detection: ${netVendor}. Requests: ${requests.slice(0,2).join(', ')}` });
        
        // Step 2b: Empty State
        console.log('\n--- Step 2b: Empty State ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2b = await findSearch(page);
        if (sel2b) {
          await page.click(sel2b);
          await page.waitForTimeout(1200);
          const s2b = await shot(page, '02-empty-state.png', 'Empty state');
          const html2b = await page.content();
          const hasSugg = html2b.toLowerCase().includes('trending') || html2b.toLowerCase().includes('popular') || html2b.toLowerCase().includes('recent');
          findings.push({ step: '2b', screenshot: s2b.filepath, observation: hasSugg ? 'Has suggestions/trending' : 'GAP: No suggestions in empty state' });
        }
        
        // Step 2c: SAYT
        console.log('\n--- Step 2c: SAYT ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2c = await findSearch(page);
        if (sel2c) {
          await page.click(sel2c);
          await page.waitForTimeout(300);
          for (const char of 'jack') {
            await page.type(sel2c, char, { delay: 80 });
          }
          await page.waitForTimeout(1500);
          const s2c = await shot(page, '03-sayt-jack.png', 'SAYT: "jack"');
          findings.push({ step: '2c', screenshot: s2c.filepath, observation: 'SAYT test for "jack"' });
          
          // Step 2d: Full Results
          console.log('\n--- Step 2d: Full Results ---');
          await page.fill(sel2c, 'jackets');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3500);
          if (await checkWAF(page)) {
            console.log('  ⛔ WAF on results page');
            const s2d = await shot(page, '04-results-waf.png', 'WAF on results');
            findings.push({ step: '2d', screenshot: s2d.filepath, observation: 'WAF BLOCKED on search results' });
          } else {
            const s2d = await shot(page, '04-results-jackets.png', 'Results: "jackets"');
            const titleText = await page.title();
            findings.push({ step: '2d', screenshot: s2d.filepath, observation: `Results page for "jackets". Title: ${titleText}` });
          }
        }
        
        // Step 2e: Typo Tolerance
        console.log('\n--- Step 2e: Typo Tolerance ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2e = await findSearch(page);
        if (sel2e) {
          await page.fill(sel2e, 'fliece jacket');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3000);
          const s2e = await shot(page, '05-typo-fliece-jacket.png', 'Typo: "fliece jacket"');
          findings.push({ step: '2e', screenshot: s2e.filepath, observation: 'Typo test: "fliece jacket" → should correct to "fleece jacket"' });
        }
        
        // Step 2f: Synonym
        console.log('\n--- Step 2f: Synonym ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2f = await findSearch(page);
        if (sel2f) {
          await page.fill(sel2f, 'puffer');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3000);
          const s2f = await shot(page, '06-synonym-puffer.png', 'Synonym: "puffer"');
          findings.push({ step: '2f', screenshot: s2f.filepath, observation: 'Synonym test: "puffer" → should match down/insulated jackets' });
        }
        
        // Step 2g: No Results
        console.log('\n--- Step 2g: No Results ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2g = await findSearch(page);
        if (sel2g) {
          await page.fill(sel2g, 'asdfghjkl');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3000);
          const s2g = await shot(page, '07-no-results.png', 'No results: "asdfghjkl"');
          findings.push({ step: '2g', screenshot: s2g.filepath, observation: 'No-results test with gibberish query' });
        }
        
        // Step 2h: Non-product content
        console.log('\n--- Step 2h: Non-Product Content ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2h = await findSearch(page);
        if (sel2h) {
          await page.fill(sel2h, 'return policy');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3000);
          const s2h = await shot(page, '08-non-product-return-policy.png', 'Non-product: "return policy"');
          findings.push({ step: '2h', screenshot: s2h.filepath, observation: 'Non-product test: "return policy"' });
        }
        
        // Step 2i: Intent Detection
        console.log('\n--- Step 2i: Intent Detection ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2i = await findSearch(page);
        if (sel2i) {
          await page.fill(sel2i, 'Summit Series');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3000);
          const s2i = await shot(page, '09-intent-summit-series.png', 'Intent: "Summit Series"');
          findings.push({ step: '2i', screenshot: s2i.filepath, observation: 'Intent: sub-brand "Summit Series" — should route to curated brand page' });
        }
        
        // Step 2j: Merchandising Consistency
        console.log('\n--- Step 2j: Merchandising Consistency ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2j = await findSearch(page);
        if (sel2j) {
          await page.fill(sel2j, 'jackets');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3000);
          const s2j = await shot(page, '10-merchandising-search.png', 'Merchandising: search "jackets"');
          findings.push({ step: '2j', screenshot: s2j.filepath, observation: 'Merchandising: search "jackets" vs nav browse comparison' });
        }
        
        // Step 2k: Federated Search
        console.log('\n--- Step 2k: Federated Search ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2k = await findSearch(page);
        if (sel2k) {
          await page.click(sel2k);
          for (const char of 'back') {
            await page.type(sel2k, char, { delay: 80 });
          }
          await page.waitForTimeout(1500);
          const s2k = await shot(page, '11-federated-back.png', 'Federated SAYT: "back"');
          findings.push({ step: '2k', screenshot: s2k.filepath, observation: 'Federated search check: SAYT dropdown content types' });
        }
        
        // Step 2l: Mobile
        console.log('\n--- Step 2l: Mobile ---');
        await page.setViewportSize({ width: 390, height: 844 });
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const s2l = await shot(page, '12-mobile-homepage.png', 'Mobile homepage');
        const sel2l = await findSearch(page);
        if (sel2l) {
          await page.click(sel2l);
          await page.waitForTimeout(1000);
          const s2lSearch = await shot(page, '12b-mobile-search.png', 'Mobile search open');
          findings.push({ step: '2l', screenshot: s2l.filepath, observation: `Mobile (390×844) — search: ${sel2l || 'not found'}` });
        } else {
          findings.push({ step: '2l', screenshot: s2l.filepath, observation: 'Mobile (390×844) — search input not found on mobile' });
        }
        await page.setViewportSize({ width: 1440, height: 900 });
        
        // Step 2m: NLP/Semantic
        console.log('\n--- Step 2m: NLP/Semantic ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2m = await findSearch(page);
        if (sel2m) {
          await page.fill(sel2m, 'warm jacket for skiing under 300');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3000);
          const s2m = await shot(page, '13-nlp-skiing-jacket.png', 'NLP: "warm jacket for skiing under 300"');
          findings.push({ step: '2m', screenshot: s2m.filepath, observation: 'NLP test: conversational query with activity + price constraint' });
        }
        
        // Step 2n: Dynamic Facets
        console.log('\n--- Step 2n: Dynamic Facets ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2n = await findSearch(page);
        if (sel2n) {
          await page.fill(sel2n, 'backpacks');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3000);
          const s2n = await shot(page, '14-dynamic-facets-backpacks.png', 'Facets: "backpacks"');
          findings.push({ step: '2n', screenshot: s2n.filepath, observation: 'Dynamic facets test: "backpacks" — facet panels' });
        }
        
        // Step 2o: Popular Searches
        console.log('\n--- Step 2o: Popular Searches ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2o = await findSearch(page);
        if (sel2o) {
          await page.click(sel2o);
          await page.waitForTimeout(1200);
          const s2o = await shot(page, '15-popular-searches.png', 'Popular searches in empty state');
          findings.push({ step: '2o', screenshot: s2o.filepath, observation: 'Popular/trending searches in empty state' });
        }
        
        // Step 2p: Dynamic Categories
        console.log('\n--- Step 2p: Dynamic Categories ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2p = await findSearch(page);
        if (sel2p) {
          for (const char of 'vest') {
            await page.type(sel2p, char, { delay: 80 });
          }
          await page.waitForTimeout(1500);
          const s2p = await shot(page, '16-dynamic-categories-vest.png', 'Dynamic categories: "vest"');
          findings.push({ step: '2p', screenshot: s2p.filepath, observation: 'Dynamic category suggestions in SAYT: "vest"' });
        }
        
        // Step 2q: Personalization
        console.log('\n--- Step 2q: Personalization ---');
        await page.goto(URL + '/mens/jackets', { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const s2q = await shot(page, '17-personalization-mens-jackets.png', 'Browse: mens jackets');
        findings.push({ step: '2q', screenshot: s2q.filepath, observation: 'Personalization signals: browsed mens jackets' });
        
        // Step 2r: Recommendations
        console.log('\n--- Step 2r: Recommendations ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2r = await findSearch(page);
        if (sel2r) {
          await page.fill(sel2r, 'Vectiv trail running shoes');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3000);
          const s2r = await shot(page, '18-recommendations-vectiv.png', 'PLP: Vectiv shoes');
          findings.push({ step: '2r', screenshot: s2r.filepath, observation: 'Recommendations/FBT check on Vectiv PLP' });
        }
        
        // Step 2s: Banners/Rules
        console.log('\n--- Step 2s: Banners & Rules ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const sel2s = await findSearch(page);
        if (sel2s) {
          await page.fill(sel2s, 'sale');
          await page.keyboard.press('Enter');
          await page.waitForTimeout(3000);
          const s2s = await shot(page, '19-banners-sale.png', 'Banners: "sale"');
          findings.push({ step: '2s', screenshot: s2s.filepath, observation: 'Merchandising rules/banners: "sale" query' });
        }
        
        // Step 2t: Analytics Visibility
        console.log('\n--- Step 2t: Analytics Visibility ---');
        await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000);
        const s2t = await shot(page, '20-analytics-homepage.png', 'Analytics signals on homepage');
        findings.push({ step: '2t', screenshot: s2t.filepath, observation: 'Analytics visibility: bestseller/trending badges check' });
      }
    }
    
    await browser.close();
    
    console.log(`\n✅ Audit complete: ${findings.length} steps, ${screenshotCount} screenshots\n`);
    
    // Write 09-browser-findings.md
    const now = new Date().toISOString();
    let md = `# Browser Findings — The North Face\nAudit Date: ${now}\nAuditor: Algolia (Claude Code)\nWorkspace: PRODUCTION\n\n---\n\n`;
    
    for (const f of findings) {
      md += `### Step ${f.step}\n`;
      md += `- Screenshot: ${f.screenshot || 'N/A'}\n`;
      md += `- Observation: ${f.observation}\n\n`;
    }
    
    fs.writeFileSync(FINDINGS_PATH, md);
    console.log(`📝 Findings written to: ${FINDINGS_PATH}`);
    console.log(`\nScreenshot count: ${screenshotCount}`);
    
    // Output JSON summary
    const result = {
      screenshots: screenshotCount,
      findings: findings.length,
      waf_blocked: findings.filter(f => f.observation && f.observation.includes('WAF')).length > 0,
      steps: findings.map(f => f.step)
    };
    console.log('\nJSON:', JSON.stringify(result, null, 2));
    
  } catch (err) {
    console.error('\n❌ Error:', err.message);
    console.error(err.stack);
    if (browser) await browser.close().catch(() => {});
    process.exit(1);
  }
})();
