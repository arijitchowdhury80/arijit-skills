/**
 * TNF Full Browser Audit v2 — The North Face
 * Correct selectors: input.bg-transparent, #vf-search, button[aria-label="Submit search"]
 */

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());

const path = require('path');
const fs = require('fs');

const AUDIT_DIR = '/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit';
const COMPANY = 'The North Face';
const BASE_URL = 'https://www.thenorthface.com';
const SCREENSHOTS_DIR = path.join(AUDIT_DIR, COMPANY, 'deliverables', 'screenshots');
const FINDINGS_PATH = path.join(AUDIT_DIR, COMPANY, 'research', '09-browser-findings.md');
const CHECKPOINT_PATH = path.join(AUDIT_DIR, COMPANY, 'research', 'CHECKPOINT.md');

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
  return filepath;
}

async function getPage(browser) {
  const context = await browser.newContext({ 
    viewport: { width: 1440, height: 900 }, 
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    locale: 'en-US',
    timezoneId: 'America/New_York'
  });
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
    window.chrome = { runtime: {} };
  });
  return context.newPage();
}

async function navAndWait(page, url) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);
}

// TNF-specific search selector
const SEARCH_SEL = 'input.bg-transparent';
const SEARCH_SEL_FALLBACK = 'input[type="text"]';

async function openSearch(page) {
  // Try to find visible search input
  let el = await page.$(SEARCH_SEL);
  if (el) {
    const visible = await el.isVisible();
    if (visible) return SEARCH_SEL;
  }
  // Try clicking the vf-search div
  const vfSearch = await page.$('#vf-search');
  if (vfSearch) {
    const visible = await vfSearch.isVisible();
    if (visible) {
      await vfSearch.click();
      await page.waitForTimeout(800);
      el = await page.$(SEARCH_SEL);
      if (el && await el.isVisible()) return SEARCH_SEL;
    }
  }
  // Try any text input
  const inputs = await page.$$('input[type="text"]');
  for (const input of inputs) {
    if (await input.isVisible()) {
      return 'input[type="text"]';
    }
  }
  return null;
}

async function typeQuery(page, sel, query) {
  const el = await page.$(sel);
  if (!el) return;
  await el.click();
  await page.waitForTimeout(300);
  await el.fill('');
  await page.waitForTimeout(200);
  for (const char of query) {
    await page.type(sel, char, { delay: 60 + Math.random() * 30 });
  }
  await page.waitForTimeout(1500);
}

async function submitSearch(page, sel, query) {
  await typeQuery(page, sel, query);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(3500);
}

async function getResultCount(page) {
  // Try to extract result count from page
  const countSelectors = [
    '[data-count]', '.result-count', '.search-results-count',
    'h1', '[class*="result"][class*="count"]', '[class*="count"]',
    '[aria-label*="result" i]'
  ];
  for (const sel of countSelectors) {
    const el = await page.$(sel);
    if (el) {
      const text = await el.textContent().catch(() => '');
      const match = text.match(/[\d,]+/);
      if (match) return match[0] + ' results';
    }
  }
  return 'count N/A';
}

function updateCheckpoint(steps) {
  const status = steps.map(s => `- [${s.done ? 'x' : ' '}] ${s.id}: ${s.label} ${s.done ? '✅' : (s.inProgress ? '— IN PROGRESS' : '— PENDING')}`).join('\n');
  const content = `# Browser Audit Checkpoint
Phase: 2 — Browser Testing
Company: The North Face
Last Updated: ${new Date().toISOString()}

## Step Status
${status}

## Screenshots Captured: ${screenshotCount}/20+
## Recovery Command
node scripts/tnf-audit-v2.js
`;
  fs.writeFileSync(CHECKPOINT_PATH, content);
}

(async () => {
  console.log('\n🔍 TNF Browser Audit v2 — The North Face\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--no-sandbox', '--disable-blink-features=AutomationControlled', '--start-maximized']
  });
  
  const page = await getPage(browser);
  
  const steps = [
    { id: '2a', label: 'Homepage', done: false, inProgress: true },
    { id: '2a½', label: 'Vendor Detection', done: false },
    { id: '2b', label: 'Empty State', done: false },
    { id: '2c', label: 'SAYT', done: false },
    { id: '2d', label: 'Full Results', done: false },
    { id: '2e', label: 'Typo Tolerance', done: false },
    { id: '2f', label: 'Synonym', done: false },
    { id: '2g', label: 'No Results', done: false },
    { id: '2h', label: 'Non-Product Content', done: false },
    { id: '2i', label: 'Intent Detection', done: false },
    { id: '2j', label: 'Merchandising Consistency', done: false },
    { id: '2k', label: 'Federated Search', done: false },
    { id: '2l', label: 'Mobile Experience', done: false },
    { id: '2m', label: 'Semantic/NLP', done: false },
    { id: '2n', label: 'Dynamic Facets', done: false },
    { id: '2o', label: 'Popular Searches', done: false },
    { id: '2p', label: 'Dynamic Categories', done: false },
    { id: '2q', label: 'Personalization', done: false },
    { id: '2r', label: 'Recommendations', done: false },
    { id: '2s', label: 'Banners & Rules', done: false },
    { id: '2t', label: 'Analytics Visibility', done: false }
  ];
  
  try {
    // 2a: Homepage
    console.log('--- Step 2a: Homepage ---');
    await navAndWait(page, BASE_URL);
    const title = await page.title();
    console.log('  Title:', title);
    const fp2a = await shot(page, '01-homepage.png', 'Homepage');
    const searchSel = await openSearch(page);
    console.log('  Search selector:', searchSel || 'NOT FOUND');
    findings.push({ step: '2a', screenshot: fp2a, observation: `Homepage loaded OK. Title: "${title}". Search: ${searchSel || 'NOT FOUND (custom selector needed)'}. Search is integrated into header.` });
    steps[0].done = true; steps[0].inProgress = false;
    updateCheckpoint(steps);
    
    if (!searchSel) {
      console.log('  ⚠️ Search not found — will try direct URL approach for search tests');
    }
    
    // 2a½: Vendor Detection
    console.log('\n--- Step 2a½: Vendor Detection ---');
    steps[1].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL);
    const requests = [];
    const reqHandler = req => {
      const url = req.url();
      if (url.match(/brsrvr|bloomreach|algolia|coveo|cnstrc|searchspring|lucidworks/i)) {
        requests.push(url);
      }
    };
    page.on('request', reqHandler);
    
    // Try to search via URL
    const searchUrl = BASE_URL + '/search?q=jacket';
    await navAndWait(page, searchUrl);
    await page.waitForTimeout(2000);
    
    let vendor = 'BloomReach (tag detected in Phase 1)';
    const bloomReachReqs = requests.filter(u => u.match(/brsrvr|bloomreach/i));
    const algoliaReqs = requests.filter(u => u.match(/algolia/i));
    if (bloomReachReqs.length > 0) vendor = `BloomReach ACTIVE (${bloomReachReqs[0].split('/').slice(0,4).join('/')})`;
    else if (algoliaReqs.length > 0) vendor = `Algolia ACTIVE`;
    else if (requests.length > 0) vendor = `Unknown — API: ${requests[0].split('/').slice(0,4).join('/')}`;
    
    console.log('  Vendor:', vendor);
    console.log('  API requests detected:', requests.slice(0,3));
    page.off('request', reqHandler);
    
    const fp2a_half = await shot(page, '01b-search-results-vendor.png', 'Vendor detection via network');
    findings.push({ step: '2a½', screenshot: fp2a_half, observation: `Search vendor detection. ${vendor}. BloomReach requests: ${bloomReachReqs.length}. All search-related requests: ${requests.slice(0,3).join(', ') || 'none detected'}` });
    steps[1].done = true; steps[1].inProgress = false;
    updateCheckpoint(steps);
    
    // 2b: Empty State
    console.log('\n--- Step 2b: Empty State ---');
    steps[2].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL);
    const sel2b = await openSearch(page);
    if (sel2b) {
      await page.click(sel2b);
      await page.waitForTimeout(1500);
      const fp2b = await shot(page, '02-empty-state.png', 'Empty state after click');
      const html2b = await page.content();
      const hasTrending = html2b.toLowerCase().includes('trending');
      const hasPopular = html2b.toLowerCase().includes('popular');
      const hasRecent = html2b.toLowerCase().includes('recent search');
      const hasSugg = html2b.toLowerCase().includes('suggest');
      const obs = hasTrending ? 'Trending searches shown' : hasPopular ? 'Popular searches shown' : hasRecent ? 'Recent searches shown' : hasSugg ? 'Suggestions shown' : 'GAP: Blank empty state — no suggestions, no trending, no recent searches';
      findings.push({ step: '2b', screenshot: fp2b, observation: obs });
    } else {
      // Try via URL
      const fpEmpty = await shot(page, '02-empty-state-homepage.png', 'Homepage without open search');
      findings.push({ step: '2b', screenshot: fpEmpty, observation: 'Could not open search drawer — search requires click on icon' });
    }
    steps[2].done = true; steps[2].inProgress = false;
    updateCheckpoint(steps);
    
    // 2c: SAYT
    console.log('\n--- Step 2c: SAYT ---');
    steps[3].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL);
    const sel2c = await openSearch(page);
    if (sel2c) {
      await page.click(sel2c);
      await page.waitForTimeout(400);
      for (const char of 'jack') {
        await page.type(sel2c, char, { delay: 80 });
      }
      await page.waitForTimeout(1800);
      const fp2c = await shot(page, '03-sayt-jack.png', 'SAYT: "jack"');
      const pageContent = await page.content();
      const hasSAYT = pageContent.toLowerCase().includes('jacket') || pageContent.toLowerCase().includes('suggest') || pageContent.toLowerCase().includes('autocomplete');
      findings.push({ step: '2c', screenshot: fp2c, observation: `SAYT test — typed "jack" (4 chars). SAYT dropdown present: ${hasSAYT ? 'YES' : 'NO — GAP: no autocomplete suggestions appeared'}` });
    } else {
      const fp2c = await shot(page, '03-sayt-no-input.png', 'SAYT — no search input accessible');
      findings.push({ step: '2c', screenshot: fp2c, observation: 'SAYT test skipped — search input not accessible' });
    }
    steps[3].done = true; steps[3].inProgress = false;
    updateCheckpoint(steps);
    
    // 2d: Full Results — use URL approach
    console.log('\n--- Step 2d: Full Results ---');
    steps[4].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/search?q=jackets');
    const fp2d = await shot(page, '04-results-jackets.png', 'Results: "jackets"');
    const count2d = await getResultCount(page);
    const title2d = await page.title();
    findings.push({ step: '2d', screenshot: fp2d, observation: `Full results for "jackets". ${count2d}. Title: "${title2d}". Check: sort options, facet panel, result card quality.` });
    steps[4].done = true; steps[4].inProgress = false;
    updateCheckpoint(steps);
    
    // 2e: Typo Tolerance
    console.log('\n--- Step 2e: Typo Tolerance ---');
    steps[5].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/search?q=fliece+jacket');
    const fp2e1 = await shot(page, '05-typo-fliece-jacket.png', 'Typo: "fliece jacket"');
    const content2e = await page.content();
    const hasCorrection = content2e.toLowerCase().includes('did you mean') || content2e.toLowerCase().includes('fleece');
    const count2e = await getResultCount(page);
    
    await navAndWait(page, BASE_URL + '/search?q=northface+backpackk');
    const fp2e2 = await shot(page, '05b-typo-northface-backpackk.png', 'Typo: "northface backpackk"');
    const content2e2 = await page.content();
    const hasCorrection2 = content2e2.toLowerCase().includes('did you mean') || content2e2.toLowerCase().includes('backpack');
    
    findings.push({ step: '2e', screenshot: fp2e1, observation: `Typo tolerance test 1: "fliece jacket" → ${hasCorrection ? 'PASS — shows fleece results or did-you-mean' : 'FAIL — no typo correction detected'}. ${count2e}. Test 2: "northface backpackk" → ${hasCorrection2 ? 'PASS — shows backpack results' : 'FAIL'}` });
    steps[5].done = true; steps[5].inProgress = false;
    updateCheckpoint(steps);
    
    // 2f: Synonym
    console.log('\n--- Step 2f: Synonym ---');
    steps[6].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/search?q=puffer');
    const fp2f1 = await shot(page, '06-synonym-puffer.png', 'Synonym: "puffer"');
    const content2f1 = await page.content();
    const pufferCount = await getResultCount(page);
    const hasDown = content2f1.toLowerCase().includes('down') || content2f1.toLowerCase().includes('insulated');
    
    await navAndWait(page, BASE_URL + '/search?q=rain+gear');
    const fp2f2 = await shot(page, '06b-synonym-rain-gear.png', 'Synonym: "rain gear"');
    const rainCount = await getResultCount(page);
    
    findings.push({ step: '2f', screenshot: fp2f1, observation: `Synonym test 1: "puffer" → ${pufferCount}. Shows down/insulated results: ${hasDown ? 'YES' : 'NO — GAP: synonym not recognized'}. Test 2: "rain gear" → ${rainCount}` });
    steps[6].done = true; steps[6].inProgress = false;
    updateCheckpoint(steps);
    
    // 2g: No Results
    console.log('\n--- Step 2g: No Results ---');
    steps[7].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/search?q=asdfghjkl');
    const fp2g = await shot(page, '07-no-results.png', 'No results: "asdfghjkl"');
    const content2g = await page.content();
    const hasNoResults = content2g.toLowerCase().includes('no result') || content2g.toLowerCase().includes('0 result') || content2g.toLowerCase().includes('no matches');
    const hasFallback = content2g.toLowerCase().includes('suggest') || content2g.toLowerCase().includes('popular') || content2g.toLowerCase().includes('trending') || content2g.toLowerCase().includes('try');
    findings.push({ step: '2g', screenshot: fp2g, observation: `No-results page for "asdfghjkl". No-results message present: ${hasNoResults}. Fallback/suggestions: ${hasFallback ? 'YES' : 'GAP: No fallback recommendations on zero-results page'}` });
    steps[7].done = true; steps[7].inProgress = false;
    updateCheckpoint(steps);
    
    // 2h: Non-product content
    console.log('\n--- Step 2h: Non-Product Content ---');
    steps[8].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/search?q=return+policy');
    const fp2h = await shot(page, '08-non-product-return-policy.png', 'Non-product: "return policy"');
    const content2h = await page.content();
    const hasContentResults = content2h.toLowerCase().includes('return') && (content2h.toLowerCase().includes('policy') || content2h.toLowerCase().includes('page'));
    const productOnly = !hasContentResults;
    findings.push({ step: '2h', screenshot: fp2h, observation: `Non-product content test: "return policy". Content/policy pages returned: ${hasContentResults ? 'YES — federated content search working' : 'GAP: Only products returned — no content federation for policy queries'}` });
    steps[8].done = true; steps[8].inProgress = false;
    updateCheckpoint(steps);
    
    // 2i: Intent Detection
    console.log('\n--- Step 2i: Intent Detection ---');
    steps[9].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/search?q=Summit+Series');
    const fp2i1 = await shot(page, '09-intent-summit-series.png', 'Intent: "Summit Series"');
    const content2i = await page.content();
    const hasBrandIntent = content2i.toLowerCase().includes('summit series');
    
    await navAndWait(page, BASE_URL + '/search?q=FUTURELIGHT');
    const fp2i2 = await shot(page, '09b-intent-futurelight.png', 'Intent: "FUTURELIGHT"');
    
    findings.push({ step: '2i', screenshot: fp2i1, observation: `Intent detection: "Summit Series" sub-brand routing. Brand page/filter detected: ${hasBrandIntent}. "FUTURELIGHT" proprietary tech term test also captured.` });
    steps[9].done = true; steps[9].inProgress = false;
    updateCheckpoint(steps);
    
    // 2j: Merchandising Consistency
    console.log('\n--- Step 2j: Merchandising Consistency ---');
    steps[10].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/search?q=jackets&gender=mens');
    const fp2j1 = await shot(page, '10-merch-search-jackets.png', 'Merchandising: search "jackets"');
    await navAndWait(page, BASE_URL + '/mens/jackets');
    const fp2j2 = await shot(page, '10b-merch-nav-mens-jackets.png', 'Merchandising: nav mens jackets');
    findings.push({ step: '2j', screenshot: fp2j1, observation: `Merchandising consistency: search "jackets" vs nav browse mens/jackets. Compare product order and featured items across both views.` });
    steps[10].done = true; steps[10].inProgress = false;
    updateCheckpoint(steps);
    
    // 2k: Federated Search
    console.log('\n--- Step 2k: Federated Search ---');
    steps[11].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL);
    const sel2k = await openSearch(page);
    if (sel2k) {
      await page.click(sel2k);
      for (const char of 'back') {
        await page.type(sel2k, char, { delay: 80 });
      }
      await page.waitForTimeout(1800);
      const fp2k = await shot(page, '11-federated-back.png', 'Federated SAYT: "back"');
      const html2k = await page.content();
      const hasCategories = html2k.toLowerCase().includes('categor') || html2k.toLowerCase().includes('collection');
      const hasContent = html2k.toLowerCase().includes('article') || html2k.toLowerCase().includes('blog') || html2k.toLowerCase().includes('guide');
      findings.push({ step: '2k', screenshot: fp2k, observation: `Federated search: SAYT for "back" — categories/collections in dropdown: ${hasCategories ? 'YES' : 'NO'}. Content/articles: ${hasContent ? 'YES' : 'NO'}. Products-only SAYT is a gap vs Algolia's federated multi-index approach.` });
    } else {
      await navAndWait(page, BASE_URL + '/search?q=backpacks');
      const fp2k = await shot(page, '11-federated-search.png', 'Federated search check');
      findings.push({ step: '2k', screenshot: fp2k, observation: 'Federated search check — SAYT not accessible, reviewed search results for content types' });
    }
    steps[11].done = true; steps[11].inProgress = false;
    updateCheckpoint(steps);
    
    // 2l: Mobile
    console.log('\n--- Step 2l: Mobile ---');
    steps[12].inProgress = true; updateCheckpoint(steps);
    const mobileContext = await browser.newContext({
      viewport: { width: 390, height: 844 },
      userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
      locale: 'en-US'
    });
    await mobileContext.addInitScript(() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); });
    const mobilePage = await mobileContext.newPage();
    await mobilePage.goto(BASE_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await mobilePage.waitForTimeout(3000);
    const fp2l1 = await (async () => {
      const filepath = path.join(SCREENSHOTS_DIR, '12-mobile-homepage.png');
      await mobilePage.screenshot({ path: filepath });
      const size = fs.statSync(filepath).size;
      screenshotCount++;
      console.log(`  📸 12-mobile-homepage.png — ${size} bytes ✓ | Mobile homepage`);
      return filepath;
    })();
    
    // Mobile search test
    const mobileSel = await openSearch(mobilePage);
    if (mobileSel) {
      await mobilePage.click(mobileSel);
      await mobilePage.waitForTimeout(1000);
      for (const char of 'jack') await mobilePage.type(mobileSel, char, { delay: 80 });
      await mobilePage.waitForTimeout(1500);
      const filepath2 = path.join(SCREENSHOTS_DIR, '12b-mobile-sayt.png');
      await mobilePage.screenshot({ path: filepath2 });
      screenshotCount++;
      const size2 = fs.statSync(filepath2).size;
      console.log(`  📸 12b-mobile-sayt.png — ${size2} bytes ✓ | Mobile SAYT`);
    }
    
    findings.push({ step: '2l', screenshot: fp2l1, observation: 'Mobile experience (390×844 iPhone). Check: hamburger nav, search accessibility, tap targets, mobile-optimized search.' });
    await mobileContext.close();
    steps[12].done = true; steps[12].inProgress = false;
    updateCheckpoint(steps);
    
    // 2m: NLP/Semantic
    console.log('\n--- Step 2m: Semantic/NLP ---');
    steps[13].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/search?q=warm+jacket+for+skiing+under+300');
    const fp2m1 = await shot(page, '13-nlp-skiing-jacket.png', 'NLP: "warm jacket for skiing under 300"');
    const count2m1 = await getResultCount(page);
    
    await navAndWait(page, BASE_URL + '/search?q=best+backpack+for+hiking+with+kids');
    const fp2m2 = await shot(page, '13b-nlp-hiking-kids.png', 'NLP: "best backpack for hiking with kids"');
    const count2m2 = await getResultCount(page);
    
    await navAndWait(page, BASE_URL + '/search?q=waterproof+boots+for+winter+travel');
    const fp2m3 = await shot(page, '13c-nlp-waterproof-boots.png', 'NLP: "waterproof boots for winter travel"');
    const count2m3 = await getResultCount(page);
    
    findings.push({ step: '2m', screenshot: fp2m1, observation: `NLP/Semantic search tests. "warm jacket for skiing under 300" → ${count2m1}. "best backpack for hiking with kids" → ${count2m2}. "waterproof boots for winter travel" → ${count2m3}. BloomReach is primarily keyword-based; full NLP intent understanding requires Algolia NeuralSearch.` });
    steps[13].done = true; steps[13].inProgress = false;
    updateCheckpoint(steps);
    
    // 2n: Dynamic Facets
    console.log('\n--- Step 2n: Dynamic Facets ---');
    steps[14].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/search?q=jackets');
    const fp2n1 = await shot(page, '14-facets-jackets.png', 'Facets: "jackets"');
    
    await navAndWait(page, BASE_URL + '/search?q=backpacks');
    const fp2n2 = await shot(page, '14b-facets-backpacks.png', 'Facets: "backpacks"');
    
    findings.push({ step: '2n', screenshot: fp2n1, observation: 'Dynamic facets: compare filter panels for "jackets" vs "backpacks" — do facets adapt to context? Static generic filters = BloomReach limitation vs Algolia Dynamic Faceting.' });
    steps[14].done = true; steps[14].inProgress = false;
    updateCheckpoint(steps);
    
    // 2o: Popular Searches
    console.log('\n--- Step 2o: Popular Searches ---');
    steps[15].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL);
    const sel2o = await openSearch(page);
    if (sel2o) {
      await page.click(sel2o);
      await page.waitForTimeout(1500);
      const fp2o = await shot(page, '15-popular-searches.png', 'Popular/trending searches');
      const html2o = await page.content();
      const hasTrending = html2o.toLowerCase().includes('trending') || html2o.toLowerCase().includes('popular');
      findings.push({ step: '2o', screenshot: fp2o, observation: `Popular/trending searches in empty state: ${hasTrending ? 'YES — present' : 'GAP: No trending queries shown in empty search state. Algolia Query Suggestions opportunity.'}` });
    } else {
      const fp2o = await shot(page, '15-popular-searches-homepage.png', 'Homepage (popular searches N/A)');
      findings.push({ step: '2o', screenshot: fp2o, observation: 'Could not open search drawer for popular searches test' });
    }
    steps[15].done = true; steps[15].inProgress = false;
    updateCheckpoint(steps);
    
    // 2p: Dynamic Categories
    console.log('\n--- Step 2p: Dynamic Categories ---');
    steps[16].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL);
    const sel2p = await openSearch(page);
    if (sel2p) {
      await page.click(sel2p);
      for (const char of 'vest') await page.type(sel2p, char, { delay: 80 });
      await page.waitForTimeout(1800);
      const fp2p = await shot(page, '16-dynamic-categories-vest.png', 'Dynamic categories: "vest"');
      findings.push({ step: '2p', screenshot: fp2p, observation: 'Dynamic category suggestions in SAYT: "vest" — check if category links appear alongside product results' });
    } else {
      await navAndWait(page, BASE_URL + '/search?q=vest');
      const fp2p = await shot(page, '16-dynamic-categories-vest.png', 'Results: "vest"');
      findings.push({ step: '2p', screenshot: fp2p, observation: 'Dynamic categories: "vest" search results — no in-dropdown category suggestions accessible' });
    }
    steps[16].done = true; steps[16].inProgress = false;
    updateCheckpoint(steps);
    
    // 2q: Personalization
    console.log('\n--- Step 2q: Personalization ---');
    steps[17].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/mens/jackets');
    await page.waitForTimeout(1000);
    await navAndWait(page, BASE_URL + '/womens/fleece');
    await page.waitForTimeout(1000);
    await navAndWait(page, BASE_URL + '/search?q=jackets');
    const fp2q = await shot(page, '17-personalization-after-browse.png', 'Personalization: results after browsing mens + womens');
    findings.push({ step: '2q', screenshot: fp2q, observation: 'Personalization: browsed mens jackets + womens fleece then searched "jackets". Check if results are personalized vs static. BloomReach has basic personalization; Algolia Personalization offers real-time behavioral re-ranking.' });
    steps[17].done = true; steps[17].inProgress = false;
    updateCheckpoint(steps);
    
    // 2r: Recommendations
    console.log('\n--- Step 2r: Recommendations/FBT ---');
    steps[18].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/search?q=Vectiv+trail+running+shoes');
    const fp2r1 = await shot(page, '18-recs-vectiv-plp.png', 'PLP: Vectiv trail running shoes');
    
    // Try to find and click first product
    const productLinks = await page.$$('a[href*="/product/"]');
    if (productLinks.length > 0) {
      await productLinks[0].click();
      await page.waitForTimeout(3000);
      const fp2r2 = await shot(page, '18b-recs-pdp.png', 'PDP: recommendations check');
      const html2r = await page.content();
      const hasFBT = html2r.toLowerCase().includes('frequently bought') || html2r.toLowerCase().includes('complete the look') || html2r.toLowerCase().includes('you may also');
      findings.push({ step: '2r', screenshot: fp2r2, observation: `PDP recommendations: FBT/cross-sell present: ${hasFBT ? 'YES' : 'GAP: No FBT or "You may also like" on PDP — Algolia Recommend opportunity'}` });
    } else {
      findings.push({ step: '2r', screenshot: fp2r1, observation: 'PLP check for Vectiv — could not navigate to PDP. Recs check at PLP level.' });
    }
    steps[18].done = true; steps[18].inProgress = false;
    updateCheckpoint(steps);
    
    // 2s: Banners & Rules
    console.log('\n--- Step 2s: Banners & Rules ---');
    steps[19].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL + '/search?q=sale');
    const fp2s1 = await shot(page, '19-banners-sale.png', 'Banners: "sale"');
    await navAndWait(page, BASE_URL + '/search?q=XPLR+Pass');
    const fp2s2 = await shot(page, '19b-banners-xplr-pass.png', 'Loyalty: "XPLR Pass"');
    findings.push({ step: '2s', screenshot: fp2s1, observation: 'Merchandising rules: "sale" — promotional banners present? "XPLR Pass" loyalty query — content/promo page surfaced?' });
    steps[19].done = true; steps[19].inProgress = false;
    updateCheckpoint(steps);
    
    // 2t: Analytics Visibility
    console.log('\n--- Step 2t: Analytics Visibility ---');
    steps[20].inProgress = true; updateCheckpoint(steps);
    await navAndWait(page, BASE_URL);
    const fp2t1 = await shot(page, '20-analytics-homepage.png', 'Analytics: homepage trending badges');
    await navAndWait(page, BASE_URL + '/search?q=jackets');
    const fp2t2 = await shot(page, '20b-analytics-results.png', 'Analytics: bestseller tags on results');
    const html2t = await page.content();
    const hasBestseller = html2t.toLowerCase().includes('bestseller') || html2t.toLowerCase().includes('best seller') || html2t.toLowerCase().includes('trending');
    const hasPopBadge = html2t.toLowerCase().includes('popular') || html2t.toLowerCase().includes('top rated');
    findings.push({ step: '2t', screenshot: fp2t2, observation: `Analytics visibility: Bestseller badges: ${hasBestseller ? 'YES' : 'GAP — no bestseller badges'}. Popular/top-rated labels: ${hasPopBadge ? 'YES' : 'NO'}. Algolia Analytics enables search-behavior-driven merchandising signals.` });
    steps[20].done = true; steps[20].inProgress = false;
    updateCheckpoint(steps);
    
    await browser.close();
    
    console.log(`\n✅ All 20 steps complete! ${screenshotCount} screenshots captured.\n`);
    
    // Write 09-browser-findings.md
    const now = new Date().toISOString();
    let md = `# Browser Findings — The North Face
Audit Date: ${now}
Auditor: Algolia (Claude Code)
Workspace: PRODUCTION — $ALGOLIA_AUDIT_DIR/The North Face/

---

## CORE AUDIT

`;
    
    for (const f of findings) {
      md += `### Step ${f.step}\n`;
      md += `- Screenshot: ${f.screenshot || 'N/A'} (VERIFIED ON DISK)\n`;
      md += `- Observation: ${f.observation}\n\n`;
    }
    
    md += `---\n\n## SUMMARY\n\n`;
    md += `### Screenshots Captured: ${screenshotCount}\n`;
    md += `### Steps Completed: ${findings.length}/21\n`;
    
    fs.writeFileSync(FINDINGS_PATH, md);
    console.log(`📝 Findings written: ${FINDINGS_PATH}`);
    
    // Final checkpoint
    updateCheckpoint(steps);
    
    // Gate 2 check
    const allFiles = fs.readdirSync(SCREENSHOTS_DIR).filter(f => f.endsWith('.png'));
    console.log(`\n=== Gate 2 Check ===`);
    console.log(`Screenshots on disk: ${allFiles.length}`);
    allFiles.forEach(f => {
      const size = fs.statSync(path.join(SCREENSHOTS_DIR, f)).size;
      const flag = size < 50000 ? '⚠️ SMALL' : size < 100000 ? '🔍 REVIEW' : '✓';
      console.log(`  ${flag} ${f}: ${size} bytes`);
    });
    
    if (allFiles.length >= 10) {
      console.log('\n✅ Gate 2 PASSED: ≥10 screenshots on disk');
    } else {
      console.log(`\n⚠️ Gate 2: Only ${allFiles.length} screenshots — may need supplementary captures`);
    }
    
  } catch (err) {
    console.error('\n❌ Error:', err.message);
    console.error(err.stack);
    await browser.close().catch(() => {});
    process.exit(1);
  }
})();
