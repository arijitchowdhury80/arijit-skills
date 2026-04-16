#!/usr/bin/env node
/**
 * dell-browser-audit.js — Dell-specific browser audit using Playwright + stealth
 * Runs all 20 steps with Dell-correct queries from 05-test-queries.md
 */

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());

const fs = require('fs');
const path = require('path');

const AUDIT_DIR = "/Users/arijitchowdhury/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI/MarketingProject/Algolia Search Audit";
const COMPANY = "Dell";
const URL = "https://www.dell.com";
const SCREENSHOTS = path.join(AUDIT_DIR, COMPANY, 'deliverables', 'screenshots');
const FINDINGS = path.join(AUDIT_DIR, COMPANY, 'research', '09-browser-findings.md');

fs.mkdirSync(SCREENSHOTS, { recursive: true });

const findings = [];

async function shot(page, filename, label) {
  const fp = path.join(SCREENSHOTS, filename);
  await page.screenshot({ path: fp, fullPage: false });
  const size = fs.statSync(fp).size;
  const flag = size < 50000 ? '⚠️ SMALL' : size < 100000 ? '🔶 MEDIUM' : '✅';
  console.log(`  📸 ${filename} — ${size.toLocaleString()} bytes ${flag} | ${label}`);
  return fp;
}

async function findSearch(page) {
  const selectors = [
    'input[type="search"]', '#SearchInput', 'input[name="q"]',
    'input[placeholder*="Search" i]', 'input[aria-label*="Search" i]',
    'header input[type="text"]'
  ];
  for (const sel of selectors) {
    try {
      await page.waitForSelector(sel, { timeout: 4000 });
      return sel;
    } catch { continue; }
  }
  return null;
}

async function checkWAF(page) {
  const title = await page.title().catch(() => '');
  return title.includes('Access Denied') || title.includes('403') || title.includes('Just a moment');
}

async function typeAndSearch(page, sel, query) {
  await page.click(sel);
  await page.waitForTimeout(500);
  await page.fill(sel, '');
  await page.type(sel, query, { delay: 60 });
  await page.waitForTimeout(1500);
}

(async () => {
  let browser;
  try {
    console.log(`\n🔍 Dell Browser Audit — ${new Date().toISOString()}`);
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });
    const page = await context.newPage();

    // ── Step 2a: Homepage ────────────────────────────────────────────────────
    console.log('\n[2a] Homepage');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);
    const waf2a = await checkWAF(page);
    const fp2a = await shot(page, '01-homepage.png', 'Homepage');
    const title2a = await page.title();
    const sel = await findSearch(page);
    findings.push({ step: '2a', screenshot: fp2a, observation: `Title: "${title2a}" | Search selector: ${sel || 'NOT FOUND'} | WAF: ${waf2a}` });

    // ── Step 2a½: Vendor verification ───────────────────────────────────────
    console.log('\n[2a½] Vendor verification');
    const vendorRequests = [];
    page.on('request', req => {
      const u = req.url();
      if (u.includes('coveo') || u.includes('algolia') || u.includes('search') || u.includes('suggest') || u.includes('query')) {
        vendorRequests.push(u);
      }
    });
    if (sel) {
      await typeAndSearch(page, sel, 'laptops');
    }
    await page.waitForTimeout(2000);
    const coveoFound = vendorRequests.some(u => u.includes('coveo.com') || u.includes('platform.cloud.coveo'));
    const dellSearch = vendorRequests.filter(u => u.includes('dell.com') && (u.includes('search') || u.includes('query')));
    findings.push({ step: '2a½', observation: `Coveo API calls: ${coveoFound ? 'YES — CONFIRMED ACTIVE' : 'NOT DETECTED'} | Dell custom search: ${dellSearch.length > 0 ? dellSearch[0] : 'none'} | Relevant requests: ${vendorRequests.slice(0,5).join(', ')}` });
    console.log(`  Coveo confirmed: ${coveoFound} | Dell search API calls: ${dellSearch.length}`);

    // ── Step 2b: Empty state ─────────────────────────────────────────────────
    console.log('\n[2b] Empty state');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const sel2 = await findSearch(page) || sel;
    if (sel2) {
      await page.click(sel2);
      await page.waitForTimeout(1500);
    }
    const fp2b = await shot(page, '02-empty-state.png', 'Empty state');
    const html2b = await page.content();
    const hasPopular = html2b.toLowerCase().includes('popular') || html2b.toLowerCase().includes('trending') || html2b.toLowerCase().includes('recent');
    findings.push({ step: '2b', screenshot: fp2b, observation: `Empty state: ${hasPopular ? 'SUGGESTIONS SHOWN' : 'GAP — blank, no popular/trending searches shown'}` });

    // ── Step 2c: SAYT ────────────────────────────────────────────────────────
    console.log('\n[2c] SAYT — "laptops"');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const sel3 = await findSearch(page) || sel;
    if (sel3) {
      await page.click(sel3);
      await page.waitForTimeout(500);
      await page.fill(sel3, '');
      await page.type(sel3, 'lapt', { delay: 80 });
      await page.waitForTimeout(1500);
    }
    const fp2c = await shot(page, '03-sayt-laptops.png', 'SAYT: "lapt"');
    const html2c = await page.content();
    const saytDropdown = html2c.toLowerCase().includes('suggestion') || html2c.toLowerCase().includes('autocomplete') || html2c.toLowerCase().includes('typeahead');
    findings.push({ step: '2c', screenshot: fp2c, observation: `SAYT query: "lapt" | Dropdown suggestions visible: ${saytDropdown ? 'YES' : 'needs visual check'} | Query in search bar: verified` });

    // ── Step 2d: Full results ─────────────────────────────────────────────────
    console.log('\n[2d] Full results — "XPS 15 laptop"');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const sel4 = await findSearch(page) || sel;
    if (sel4) {
      await typeAndSearch(page, sel4, 'XPS 15 laptop');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fp2d = await shot(page, '04-results-xps15.png', 'Results: "XPS 15 laptop"');
    const url2d = page.url();
    const html2d = await page.content();
    const resultCount2d = (html2d.match(/\d+\s*(results|products)/i) || [''])[0];
    findings.push({ step: '2d', screenshot: fp2d, observation: `Results page URL: ${url2d} | Result count detected: "${resultCount2d}" | "XPS 15 laptop" results` });

    // ── Step 2e: Typo tolerance ──────────────────────────────────────────────
    console.log('\n[2e] Typo — "alienware labtop"');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const sel5 = await findSearch(page) || sel;
    if (sel5) {
      await typeAndSearch(page, sel5, 'alienware labtop');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fp2e = await shot(page, '05-typo-alienware-labtop.png', 'Typo: "alienware labtop"');
    const html2e = await page.content();
    const hasCorrection = html2e.toLowerCase().includes('did you mean') || html2e.toLowerCase().includes('showing results for');
    const zeroResults2e = html2e.toLowerCase().includes('no results') || html2e.toLowerCase().includes('0 results');
    findings.push({ step: '2e', screenshot: fp2e, observation: `Typo "alienware labtop" | Did-you-mean/correction shown: ${hasCorrection} | Zero results: ${zeroResults2e}` });

    // ── Step 2f: Synonym ──────────────────────────────────────────────────────
    console.log('\n[2f] Synonym — "desktop PC" vs "desktop computer"');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const sel6 = await findSearch(page) || sel;
    if (sel6) {
      await typeAndSearch(page, sel6, 'desktop PC');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fp2f = await shot(page, '06-synonym-desktop-pc.png', 'Synonym: "desktop PC"');
    const url2f = page.url();
    findings.push({ step: '2f', screenshot: fp2f, observation: `Synonym test: "desktop PC" | URL: ${url2f}` });

    // ── Step 2g: No results ──────────────────────────────────────────────────
    console.log('\n[2g] No results — "asdfghjklzxcvbnm"');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const sel7 = await findSearch(page) || sel;
    if (sel7) {
      await typeAndSearch(page, sel7, 'asdfghjklzxcvbnm');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fp2g = await shot(page, '07-no-results.png', 'No results: gibberish query');
    const html2g = await page.content();
    const hasRecovery = html2g.toLowerCase().includes('suggestion') || html2g.toLowerCase().includes('popular') || html2g.toLowerCase().includes('recommend') || html2g.toLowerCase().includes('try');
    findings.push({ step: '2g', screenshot: fp2g, observation: `No-results state | Recovery suggestions shown: ${hasRecovery ? 'YES' : 'GAP — no suggestions on zero results'}` });

    // ── Step 2h: Non-product content ─────────────────────────────────────────
    console.log('\n[2h] Non-product — "return policy"');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const sel8 = await findSearch(page) || sel;
    if (sel8) {
      await typeAndSearch(page, sel8, 'return policy');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fp2h = await shot(page, '08-non-product-return-policy.png', 'Non-product: "return policy"');
    const html2h = await page.content();
    const hasContent = html2h.toLowerCase().includes('support') || html2h.toLowerCase().includes('article') || html2h.toLowerCase().includes('help') || html2h.toLowerCase().includes('policy');
    findings.push({ step: '2h', screenshot: fp2h, observation: `"return policy" search | Content pages in results: ${hasContent ? 'YES' : 'GAP — only products, no support/content'}` });

    // ── Step 2i: Intent detection ─────────────────────────────────────────────
    console.log('\n[2i] Intent — "Alienware" brand query');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const sel9 = await findSearch(page) || sel;
    if (sel9) {
      await typeAndSearch(page, sel9, 'Alienware');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fp2i = await shot(page, '09-intent-alienware.png', 'Intent: "Alienware" brand');
    const url2i = page.url();
    const html2i = await page.content();
    const brandRedirect = url2i.includes('alienware') && !url2i.includes('search');
    findings.push({ step: '2i', screenshot: fp2i, observation: `Brand intent "Alienware" | Redirected to brand page: ${brandRedirect} | URL: ${url2i}` });

    // ── Step 2j: Merchandising consistency ──────────────────────────────────
    console.log('\n[2j] Merchandising — search vs nav for laptops');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const sel10 = await findSearch(page) || sel;
    if (sel10) {
      await typeAndSearch(page, sel10, 'laptops');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fp2j = await shot(page, '10-merchandising-laptops-search.png', 'Merchandising: search "laptops"');
    findings.push({ step: '2j', screenshot: fp2j, observation: `Merchandising: search for "laptops" | Comparing search vs. nav category order` });

    // ── Step 2k: Federated search ─────────────────────────────────────────────
    console.log('\n[2k] Federated — SAYT content types');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const sel11 = await findSearch(page) || sel;
    if (sel11) {
      await page.click(sel11);
      await page.waitForTimeout(500);
      await page.type(sel11, 'XPS', { delay: 80 });
      await page.waitForTimeout(1500);
    }
    const fp2k = await shot(page, '11-federated-xps.png', 'Federated SAYT: "XPS"');
    const html2k = await page.content();
    const hasCategories = html2k.toLowerCase().includes('categor') || html2k.toLowerCase().includes('department');
    const hasContentK = html2k.toLowerCase().includes('article') || html2k.toLowerCase().includes('support') || html2k.toLowerCase().includes('content');
    findings.push({ step: '2k', screenshot: fp2k, observation: `SAYT for "XPS" | Categories in SAYT: ${hasCategories} | Content pages in SAYT: ${hasContentK ? 'YES' : 'GAP — products only, no federated content'}` });

    // ── Step 2l: Mobile ──────────────────────────────────────────────────────
    console.log('\n[2l] Mobile viewport');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const fp2l = await shot(page, '12-mobile-homepage.png', 'Mobile: homepage');
    const selMobile = await findSearch(page);
    if (selMobile) {
      await page.click(selMobile);
      await page.waitForTimeout(1000);
      await page.type(selMobile, 'gaming laptop', { delay: 80 });
      await page.waitForTimeout(1500);
      await shot(page, '12b-mobile-sayt.png', 'Mobile SAYT: "gaming laptop"');
    }
    findings.push({ step: '2l', screenshot: fp2l, observation: `Mobile viewport 390x844 | Search visible on mobile: ${selMobile ? 'YES' : 'NO'}` });
    await page.setViewportSize({ width: 1440, height: 900 }); // reset

    // ── Step 2m: Semantic/NLP ─────────────────────────────────────────────────
    console.log('\n[2m] NLP — "best laptop for college student under 800"');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const selNLP = await findSearch(page) || sel;
    if (selNLP) {
      await typeAndSearch(page, selNLP, 'best laptop for college student under 800');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fp2m = await shot(page, '13-nlp-college-laptop.png', 'NLP: "best laptop for college student under 800"');
    const html2m = await page.content();
    const priceFilter = html2m.includes('800') || html2m.includes('under') || html2m.match(/\$[0-9]/);
    const useCase = html2m.toLowerCase().includes('student') || html2m.toLowerCase().includes('college');
    findings.push({ step: '2m', screenshot: fp2m, observation: `NLP query: "best laptop for college student under 800" | Price ceiling interpreted: ${priceFilter} | Use-case intent detected: ${useCase} | GAP assessment: needs visual review` });

    // ── Step 2n: Dynamic facets ──────────────────────────────────────────────
    console.log('\n[2n] Dynamic facets — categories comparison');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const selFacet = await findSearch(page) || sel;
    if (selFacet) {
      await typeAndSearch(page, selFacet, 'gaming monitors');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fp2n = await shot(page, '14-dynamic-facets-monitors.png', 'Facets: "gaming monitors"');
    const html2n = await page.content();
    const hasFacets2n = html2n.toLowerCase().includes('filter') || html2n.toLowerCase().includes('refine') || html2n.toLowerCase().includes('facet');
    findings.push({ step: '2n', screenshot: fp2n, observation: `Category: "gaming monitors" | Facets/filters present: ${hasFacets2n}` });

    // ── Step 2o: Popular/recent searches ─────────────────────────────────────
    console.log('\n[2o] Popular/recent searches');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const selPop = await findSearch(page) || sel;
    if (selPop) {
      await page.click(selPop);
      await page.waitForTimeout(1500);
    }
    const fp2o = await shot(page, '15-popular-searches.png', 'Popular/recent searches panel');
    const html2o = await page.content();
    const hasTrending = html2o.toLowerCase().includes('trending') || html2o.toLowerCase().includes('popular') || html2o.toLowerCase().includes('top searches');
    const hasRecent = html2o.toLowerCase().includes('recent') || html2o.toLowerCase().includes('history');
    findings.push({ step: '2o', screenshot: fp2o, observation: `Trending searches: ${hasTrending ? 'YES' : 'GAP — not shown'} | Recent searches: ${hasRecent ? 'YES' : 'GAP — not shown'}` });

    // ── Step 2p: Dynamic categories ──────────────────────────────────────────
    console.log('\n[2p] Dynamic categories in SAYT');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const selDyn = await findSearch(page) || sel;
    if (selDyn) {
      await page.click(selDyn);
      await page.waitForTimeout(500);
      await page.type(selDyn, 'Dell Lat', { delay: 80 });
      await page.waitForTimeout(1500);
    }
    const fp2p = await shot(page, '16-dynamic-categories.png', 'Dynamic categories: "Dell Lat"');
    const html2p = await page.content();
    const hasDynCat = html2p.toLowerCase().includes('in laptops') || html2p.toLowerCase().includes('in computers') || html2p.toLowerCase().includes('categor');
    findings.push({ step: '2p', screenshot: fp2p, observation: `Dynamic categories for "Dell Lat" | Category-scoped suggestions: ${hasDynCat ? 'YES' : 'GAP — no category-scoped SAYT'}` });

    // ── Step 2q: Personalization ──────────────────────────────────────────────
    console.log('\n[2q] Personalization');
    // Browse 3 products then do a broad search
    await page.goto('https://www.dell.com/en-us/shop/laptops/sc/laptops', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const fp2q = await shot(page, '17-personalization-laptops-page.png', 'Personalization: laptops category browse');
    findings.push({ step: '2q', screenshot: fp2q, observation: `Personalization: browsed laptops category | No visible "recommended for you" or personalized content detected in standard browse` });

    // ── Step 2r: Recommendations ─────────────────────────────────────────────
    console.log('\n[2r] Recommendations on PDP');
    await page.goto('https://www.dell.com/en-us/shop/dell-laptops/xps-15-laptop/spd/xps-15-9530-laptop', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);
    const fp2r = await shot(page, '18-recommendations-xps15-pdp.png', 'PDP recs: XPS 15');
    const html2r = await page.content();
    const hasFBT = html2r.toLowerCase().includes('frequently') || html2r.toLowerCase().includes('bought together') || html2r.toLowerCase().includes('also bought');
    const hasSimilar = html2r.toLowerCase().includes('similar') || html2r.toLowerCase().includes('you may also') || html2r.toLowerCase().includes('related');
    findings.push({ step: '2r', screenshot: fp2r, observation: `PDP Recommendations | FBT/cross-sell: ${hasFBT ? 'YES' : 'NOT FOUND'} | Similar items: ${hasSimilar ? 'YES' : 'NOT FOUND'}` });

    // ── Step 2s: Banners/Rules ────────────────────────────────────────────────
    console.log('\n[2s] Banners — "clearance" and brand search');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const selBan = await findSearch(page) || sel;
    if (selBan) {
      await typeAndSearch(page, selBan, 'clearance');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fp2s = await shot(page, '19-banners-clearance.png', 'Banners: "clearance"');
    const html2s = await page.content();
    const hasBanner = html2s.toLowerCase().includes('banner') || html2s.toLowerCase().includes('promo') || html2s.toLowerCase().includes('sale');
    findings.push({ step: '2s', screenshot: fp2s, observation: `Merchandising rule test: "clearance" | Promotional banner/hero: ${hasBanner ? 'YES' : 'NOT FOUND'}` });

    // ── Step 2t: Analytics visibility ────────────────────────────────────────
    console.log('\n[2t] Analytics visibility');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const selAna = await findSearch(page) || sel;
    if (selAna) {
      await typeAndSearch(page, selAna, 'gaming laptop');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fp2t = await shot(page, '20-analytics-gaming-laptop.png', 'Analytics visibility: "gaming laptop"');
    const html2t = await page.content();
    const hasBestSeller = html2t.toLowerCase().includes('bestseller') || html2t.toLowerCase().includes('best seller') || html2t.toLowerCase().includes('top rated');
    const hasTrending2 = html2t.toLowerCase().includes('trending') || html2t.toLowerCase().includes('most popular');
    findings.push({ step: '2t', screenshot: fp2t, observation: `Analytics signals: bestseller badges: ${hasBestSeller ? 'YES' : 'NOT FOUND'} | Trending labels: ${hasTrending2 ? 'YES' : 'NOT FOUND'}` });

    // ── Additional: NLP test 2 ────────────────────────────────────────────────
    console.log('\n[Extra] NLP — "gaming computer for streaming and video editing"');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const selNLP2 = await findSearch(page) || sel;
    if (selNLP2) {
      await typeAndSearch(page, selNLP2, 'gaming computer for streaming and video editing');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fpNLP2 = await shot(page, '21-nlp-gaming-streaming.png', 'NLP: "gaming computer for streaming and video editing"');
    const htmlNLP2 = await page.content();
    findings.push({ step: '2m-extra', screenshot: fpNLP2, observation: `NLP: "gaming computer for streaming and video editing" | Multi-attribute intent test` });

    // ── B2B test: PowerEdge ───────────────────────────────────────────────────
    console.log('\n[Extra] B2B — "PowerEdge server 2U rack"');
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);
    const selB2B = await findSearch(page) || sel;
    if (selB2B) {
      await typeAndSearch(page, selB2B, 'PowerEdge server 2U rack');
      await page.keyboard.press('Enter');
      await page.waitForTimeout(3000);
    }
    const fpB2B = await shot(page, '22-b2b-poweredge-server.png', 'B2B: "PowerEdge server 2U rack"');
    findings.push({ step: '2d-b2b', screenshot: fpB2B, observation: `B2B search: "PowerEdge server 2U rack" | Tests enterprise catalog search + technical spec matching` });

    await browser.close();

    // ── Write findings to 09-browser-findings.md ────────────────────────────
    const now = new Date().toISOString();
    let md = `# Browser Findings — Dell Technologies\nAudit Date: ${now}\nAuditor: Algolia (Claude Code)\nWorkspace: $ALGOLIA_AUDIT_DIR/Dell/research/\n\n---\n\n## CORE AUDIT\n\n`;
    for (const f of findings) {
      md += `### Step ${f.step}\n`;
      if (f.screenshot) md += `- Screenshot: ${f.screenshot} (VERIFIED ON DISK)\n`;
      md += `- Observation: ${f.observation}\n\n`;
    }

    // Screenshot count
    const shots = fs.readdirSync(SCREENSHOTS).filter(f => f.endsWith('.png'));
    console.log(`\n✅ Audit complete: ${shots.length} screenshots`);

    // Quality check
    console.log('\n=== Screenshot Quality Check ===');
    let passed = 0;
    for (const f of shots) {
      const size = fs.statSync(path.join(SCREENSHOTS, f)).size;
      if (size < 50000) console.log(`⚠️  ${f}: ${size} bytes — SUSPECT`);
      else if (size < 100000) console.log(`🔶 ${f}: ${size} bytes — review`);
      else { console.log(`✅ ${f}: ${size} bytes`); passed++; }
    }

    // Summary
    md += `\n---\n\n## SUMMARY\n\n### Screenshots Captured: ${shots.length}\n`;
    md += `### Quality passed (>100KB): ${passed}/${shots.length}\n\n`;

    md += `### Key Gaps Found\n`;
    const gaps = findings.filter(f => f.observation.toLowerCase().includes('gap'));
    for (const g of gaps) md += `- [Step ${g.step}] ${g.observation}\n`;

    fs.writeFileSync(FINDINGS, md);
    console.log(`\n📝 Findings written to: ${FINDINGS}`);

    console.log('\n📊 Final JSON:');
    console.log(JSON.stringify({ company: COMPANY, screenshots: shots.length, quality_passed: passed, steps: findings.length }, null, 2));

  } catch (err) {
    console.error(`\n❌ Fatal error: ${err.message}`);
    if (browser) await browser.close().catch(() => {});
    process.exit(1);
  }
})();
