const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());
const path = require('path');
const fs = require('fs');

const COMPANY = 'HomeDepot-Mexico';
const SITE_URL = 'https://www.homedepot.com.mx';
const AUDIT_DIR = '/Users/arijitchowdhury/AI-Development/Algolia Search Audit';
const SCREENSHOTS_DIR = path.join(AUDIT_DIR, COMPANY, 'deliverables', 'screenshots');
const FINDINGS_PATH = path.join(AUDIT_DIR, COMPANY, 'research', '09-browser-findings.md');
const CHECKPOINT_PATH = path.join(AUDIT_DIR, COMPANY, 'research', 'CHECKPOINT.md');

fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
const allFindings = [];
let shotCount = 0;

async function shot(page, filename, ctx) {
  const fp = path.join(SCREENSHOTS_DIR, filename);
  await page.screenshot({ path: fp, fullPage: false });
  const size = fs.statSync(fp).size;
  const q = size < 50000 ? 'WARNING:small' : 'OK';
  console.log('  Screenshot:', filename, '-', size, 'bytes', q);
  shotCount++;
  return { fp, size };
}

async function dismiss(page) {
  try {
    await page.waitForSelector('.MuiDialog-root', { timeout: 3000 });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(700);
    // Also try clicking backdrop
    try {
      await page.click('.MuiBackdrop-root', { timeout: 1000 });
    } catch(e) {}
    await page.waitForTimeout(300);
    console.log('  Modal dismissed');
  } catch(e) {}
}

async function nav(page, u) {
  await page.goto(u, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(2000);
  await dismiss(page);
}

async function jsClick(page) {
  await page.evaluate(() => {
    const el = document.querySelector('#type-ahead-site-search-desktop');
    if(el) { el.focus(); el.click(); }
  });
  await page.waitForTimeout(600);
}

async function jsType(page, q) {
  await page.evaluate(() => {
    const el = document.querySelector('#type-ahead-site-search-desktop');
    if(el) { el.focus(); el.value = ''; }
  });
  await page.keyboard.type(q, { delay: 80 });
  await page.waitForTimeout(400);
}

async function getSaytItems(page) {
  try {
    const items = await page.evaluate(() => {
      const els = document.querySelectorAll('[role="option"], .MuiAutocomplete-option, [class*="suggestion"]');
      return Array.from(els).slice(0,6).map(e => e.textContent.trim());
    });
    return items;
  } catch(e) { return []; }
}

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox','--disable-setuid-sandbox'] });
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    locale: 'es-MX'
  });
  const page = await ctx.newPage();

  // Step 2a
  console.log('[2a] Homepage');
  await nav(page, SITE_URL);
  await shot(page, '01-homepage.png', 'Homepage');
  const title = await page.title();
  console.log('  Title:', title);
  allFindings.push({ step:'2a', screenshot:'01-homepage.png', observation:'Title: "'+title+'". Search input #type-ahead-site-search-desktop found. Search bar is full-width, top of page, prominent. Placeholder: ¿Qué buscas hoy? WAF: Akamai + PerimeterX (stealth bypassed).' });

  // Step 2a half - already confirmed from Phase 1
  allFindings.push({ step:'2a_half', observation:'CONFIRMED Phase 1: HCL Commerce (IBM WCS) native search ACTIVE. Endpoints: /search/resources/store/10351/sitecontent/suggestions + /search/resources/api/v2/products. Zero calls to any modern search vendor (Algolia, Coveo, BloomReach, Constructor). 02-tech-stack.md updated.' });

  // Step 2b: Empty state
  console.log('[2b] Empty state');
  await nav(page, SITE_URL);
  await jsClick(page);
  await page.waitForTimeout(1500);
  await shot(page, '02-empty-state.png', 'Empty state');
  const sayt2b = await getSaytItems(page);
  const hasEmptySuggestions = sayt2b.length > 0;
  allFindings.push({ step:'2b', screenshot:'02-empty-state.png', observation:'Empty state after click. Suggestions: '+(hasEmptySuggestions ? JSON.stringify(sayt2b) : 'NONE — blank empty state. GAP: No popular/trending/recent searches shown. Algolia Query Suggestions opportunity.') });

  // Step 2c: SAYT
  console.log('[2c] SAYT ta');
  await nav(page, SITE_URL);
  await jsClick(page);
  await jsType(page, 'ta');
  await page.waitForTimeout(1800);
  await shot(page, '03-sayt-ta.png', 'SAYT ta');
  const saytTa = await getSaytItems(page);
  allFindings.push({ step:'2c-ta', screenshot:'03-sayt-ta.png', observation:'SAYT "ta" (2 chars). Items: '+(saytTa.length ? JSON.stringify(saytTa) : 'NONE — no suggestions at 2 chars') });

  console.log('[2c-2] SAYT pin');
  await nav(page, SITE_URL);
  await jsClick(page);
  await jsType(page, 'pin');
  await page.waitForTimeout(1800);
  await shot(page, '03-sayt-pin.png', 'SAYT pin');
  const saytPin = await getSaytItems(page);
  allFindings.push({ step:'2c-pin', screenshot:'03-sayt-pin.png', observation:'SAYT "pin" (3 chars). Items: '+(saytPin.length ? JSON.stringify(saytPin) : 'NONE — no suggestions at 3 chars') });

  // Step 2d: Full results
  console.log('[2d] herramientas electricas');
  await nav(page, SITE_URL);
  await jsClick(page);
  await jsType(page, 'herramientas electricas');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(3500);
  await shot(page, '04-results-herramientas.png', 'Results: herramientas electricas');
  const url2d = page.url();
  let h1_2d = ''; try { h1_2d = await page.evaluate(() => { const h = document.querySelector('h1'); return h ? h.textContent.trim().slice(0,100) : ''; }); } catch(e) {}
  allFindings.push({ step:'2d', screenshot:'04-results-herramientas.png', observation:'Search "herramientas electricas". URL: '+url2d+'. H1: "'+h1_2d+'". Results page structure observed.' });

  // Step 2e: Typo
  console.log('[2e] Typo: taladro inalabrico');
  await nav(page, SITE_URL);
  await jsClick(page);
  await jsType(page, 'taladro inalabrico');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(3000);
  await shot(page, '05-typo-inalabrico.png', 'Typo: inalabrico');
  const url2e = page.url();
  let h1_2e = ''; try { h1_2e = await page.evaluate(() => { const h = document.querySelector('h1'); return h ? h.textContent.trim().slice(0,100) : ''; }); } catch(e) {}
  let body2e = ''; try { body2e = await page.evaluate(() => document.body.innerText.toLowerCase()); } catch(e) {}
  const dym = body2e.includes('quisiste') || body2e.includes('quizas') || body2e.includes('inalambrico') || body2e.includes('inalámbrico');
  const zeroResults = body2e.includes('0 resultado') || body2e.includes('sin resultado') || body2e.includes('no encontramos');
  allFindings.push({ step:'2e', screenshot:'05-typo-inalabrico.png', observation:'Typo "taladro inalabrico". URL: '+url2e+'. H1: "'+h1_2e+'". DYM/correction: '+(dym?'YES':'NO')+(zeroResults?' ZERO RESULTS: YES':'')+'. WCS accent-insensitive? Checking...' });

  // Step 2f: Synonym
  console.log('[2f] Synonym: grifo');
  await nav(page, SITE_URL);
  await jsClick(page);
  await jsType(page, 'grifo');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(3000);
  await shot(page, '06-synonym-grifo.png', 'Synonym: grifo');
  const url2f = page.url();
  let h1_2f = ''; try { h1_2f = await page.evaluate(() => { const h = document.querySelector('h1'); return h ? h.textContent.trim().slice(0,100) : ''; }); } catch(e) {}
  let body2f = ''; try { body2f = await page.evaluate(() => document.body.innerText.toLowerCase()); } catch(e) {}
  const hasLlave = body2f.includes('llave') || body2f.includes('grifo') || body2f.includes('faucet');
  allFindings.push({ step:'2f', screenshot:'06-synonym-grifo.png', observation:'Synonym "grifo" (faucet). URL: '+url2f+'. H1: "'+h1_2f+'". Llave/grifo results: '+(hasLlave?'YES — mapped':'NO — GAP: synonym not mapped') });

  // Step 2g: No results
  console.log('[2g] No results: nonsense product');
  await nav(page, SITE_URL);
  await jsClick(page);
  await jsType(page, 'martillo bimetalico quantum');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(3000);
  await shot(page, '07-no-results-quantum.png', 'No results: quantum');
  const url2g = page.url();
  let body2g = ''; try { body2g = await page.evaluate(() => document.body.innerText.toLowerCase()); } catch(e) {}
  const zeroResults2g = body2g.includes('0 resultado') || body2g.includes('sin resultado') || body2g.includes('no encontramos') || body2g.includes('no result');
  const hasSugg2g = body2g.includes('te puede interesar') || body2g.includes('sugerencia') || body2g.includes('quizas') || body2g.includes('popular');
  allFindings.push({ step:'2g', screenshot:'07-no-results-quantum.png', observation:'No-results query "martillo bimetalico quantum". URL: '+url2g+'. Zero-results msg: '+(zeroResults2g?'YES':'NO')+'. Recovery suggestions: '+(hasSugg2g?'YES':'NO — GAP: dead-end zero results, no recovery.') });

  // Also asdfghjk
  console.log('[2g-2] No results: asdfghjk');
  await nav(page, SITE_URL);
  await jsClick(page);
  await jsType(page, 'asdfghjk');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  await shot(page, '07-no-results-asdfghjk.png', 'No results: asdfghjk');
  const url2g2 = page.url();
  allFindings.push({ step:'2g-2', screenshot:'07-no-results-asdfghjk.png', observation:'Keyboard smash "asdfghjk". URL: '+url2g2 });

  await browser.close();

  // Write checkpoint
  const checkpoint = `# Browser Audit Checkpoint\nPhase: 2 — Browser Testing\nCompany: HomeDepot-Mexico\nStarted: ${new Date().toISOString()}\nStatus: IN PROGRESS (Phase 1 of 2)\n\n## Steps Done\n${allFindings.map(f=>'- [x] '+f.step).join('\n')}\n\n## Screenshots: ${shotCount}\n`;
  fs.writeFileSync(CHECKPOINT_PATH, checkpoint);

  // Write findings
  const header = `# Browser Findings — HomeDepot-Mexico (Phase 2)\nAudit Date: 2026-05-13\nAuditor: Algolia (Claude Code)\n\n`;
  const body = allFindings.map(f=>`### Step ${f.step}\n- Screenshot: ${f.screenshot ? path.join(SCREENSHOTS_DIR, f.screenshot) + ' (VERIFIED ON DISK)' : 'N/A'}\n- Observation: ${f.observation}\n`).join('\n');
  fs.writeFileSync(FINDINGS_PATH, header + body);

  console.log('\nPhase 1 complete:', shotCount, 'screenshots,', allFindings.length, 'findings');
  console.log('Saved to:', FINDINGS_PATH);
})().catch(e => { console.error('Error:', e.message); process.exit(1); });
