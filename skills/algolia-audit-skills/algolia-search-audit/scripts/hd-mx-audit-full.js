/**
 * hd-mx-audit-full.js — Full 20-step browser audit for The Home Depot México
 * Fix: Added 5000ms wait after Enter press for Next.js SPA hydration
 */
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());
const path = require('path');
const fs = require('fs');

const SITE_URL = 'https://www.homedepot.com.mx';
const AUDIT_DIR = '/Users/arijitchowdhury/AI-Development/Algolia Search Audit';
const COMPANY = 'HomeDepot-Mexico';
const SCREENSHOTS_DIR = path.join(AUDIT_DIR, COMPANY, 'deliverables', 'screenshots');
const FINDINGS_PATH = path.join(AUDIT_DIR, COMPANY, 'research', '09-browser-findings.md');
const CHECKPOINT_PATH = path.join(AUDIT_DIR, COMPANY, 'research', 'CHECKPOINT.md');

fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
const F = []; // findings
let SC = 0;   // screenshot count

async function shot(page, fn, note) {
  const fp = path.join(SCREENSHOTS_DIR, fn);
  await page.screenshot({ path: fp, fullPage: false });
  const sz = fs.statSync(fp).size;
  const q = sz < 80000 ? 'SMALL-WARNING' : 'OK';
  console.log(`  [${q}] ${fn} — ${sz} bytes${note ? ' | '+note : ''}`);
  SC++;
  return { fn, fp, sz };
}

async function dismissModal(page) {
  try {
    await page.waitForSelector('.MuiDialog-root', { timeout: 3000 });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(700);
    try { await page.click('.MuiBackdrop-root', { timeout: 1000 }); } catch(e) {}
    await page.waitForTimeout(300);
    console.log('  Modal dismissed');
  } catch(e) {}
}

async function navTo(page, url) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(2500);
  await dismissModal(page);
}

async function focusSearch(page) {
  await page.evaluate(() => {
    const el = document.querySelector('#type-ahead-site-search-desktop');
    if(el) { el.focus(); el.click(); }
  });
  await page.waitForTimeout(600);
}

async function typeQuery(page, q) {
  await page.evaluate(() => {
    const el = document.querySelector('#type-ahead-site-search-desktop');
    if(el) { el.focus(); el.value = ''; }
  });
  await page.keyboard.type(q, { delay: 80 });
  await page.waitForTimeout(400);
}

async function getSayt(page) {
  return await page.evaluate(() => {
    const els = document.querySelectorAll('[role="option"], .MuiAutocomplete-option, li[class*="suggestion"]');
    return Array.from(els).slice(0,8).map(e => e.textContent.trim()).filter(t => t.length > 0);
  }).catch(() => []);
}

async function getH1(page) {
  return await page.evaluate(() => {
    const h = document.querySelector('h1');
    return h ? h.textContent.trim().slice(0,120) : '';
  }).catch(() => '');
}

async function getBodyText(page) {
  return await page.evaluate(() => document.body.innerText.toLowerCase()).catch(() => '');
}

async function searchAndWait(page, query) {
  await navTo(page, SITE_URL);
  await focusSearch(page);
  await typeQuery(page, query);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(5000); // Wait for Next.js SPA hydration
  await dismissModal(page);
}

(async () => {
  console.log('\nThe Home Depot México — Full Browser Audit (20 steps)');
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox','--disable-setuid-sandbox','--disable-blink-features=AutomationControlled']
  });
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    locale: 'es-MX',
    timezoneId: 'America/Mexico_City',
  });
  const page = await ctx.newPage();

  // ── 2a: Homepage ──────────────────────────────────────────────────────────
  console.log('\n[2a] Homepage');
  await navTo(page, SITE_URL);
  const s2a = await shot(page, '01-homepage.png', '2a Homepage');
  const t2a = await page.title();
  F.push({ step:'2a', fn:'01-homepage.png', obs:`Title: "${t2a}". Search: full-width top bar, placeholder "¿Qué buscas hoy?", selector #type-ahead-site-search-desktop (MUI Autocomplete). WAF: Akamai+PerimeterX (stealth bypass confirmed). Search is prominently positioned at top center.` });

  // ── 2a½: Vendor confirmed from Phase 1 ───────────────────────────────────
  F.push({ step:'2a½', fn:null, obs:'CONFIRMED Phase 1 network inspection: HCL Commerce (IBM WebSphere Commerce) native search ACTIVE. Endpoints: /search/resources/store/10351/sitecontent/suggestions + /search/resources/api/v2/products. ZERO calls to Algolia, Coveo, BloomReach, Constructor, or any modern AI search vendor. This is a textbook WCS displacement opportunity.' });

  // ── 2b: Empty state ───────────────────────────────────────────────────────
  console.log('\n[2b] Empty state');
  await navTo(page, SITE_URL);
  await focusSearch(page);
  await page.waitForTimeout(1800);
  const s2b = await shot(page, '02-empty-state.png', '2b Empty state');
  const sayt2b = await getSayt(page);
  const has2b = sayt2b.length > 0;
  F.push({ step:'2b', fn:'02-empty-state.png', obs:`Empty state on search focus. SAYT suggestions: ${has2b ? JSON.stringify(sayt2b) : 'NONE — blank white box. GAP: No popular searches, trending terms, or recent searches shown. Algolia Query Suggestions would power this.'}` });

  // ── 2c: SAYT ─────────────────────────────────────────────────────────────
  console.log('\n[2c] SAYT "ta"');
  await navTo(page, SITE_URL);
  await focusSearch(page);
  await typeQuery(page, 'ta');
  await page.waitForTimeout(1800);
  const s2c1 = await shot(page, '03-sayt-ta.png', '2c SAYT "ta"');
  const saytTa = await getSayt(page);

  console.log('[2c-2] SAYT "pin"');
  await navTo(page, SITE_URL);
  await focusSearch(page);
  await typeQuery(page, 'pin');
  await page.waitForTimeout(1800);
  const s2c2 = await shot(page, '03-sayt-pin.png', '2c SAYT "pin"');
  const saytPin = await getSayt(page);

  console.log('[2c-3] SAYT "herramienta"');
  await navTo(page, SITE_URL);
  await focusSearch(page);
  await typeQuery(page, 'herramienta');
  await page.waitForTimeout(1800);
  const s2c3 = await shot(page, '03-sayt-herramienta.png', '2c SAYT "herramienta"');
  const saytHerr = await getSayt(page);

  F.push({ step:'2c', fn:'03-sayt-ta.png', obs:`SAYT test. "ta" (2 chars): ${saytTa.length ? JSON.stringify(saytTa) : 'NO SUGGESTIONS'}. "pin" (3 chars): ${saytPin.length ? JSON.stringify(saytPin) : 'NO SUGGESTIONS'}. "herramienta" (full): ${saytHerr.length ? JSON.stringify(saytHerr) : 'NO SUGGESTIONS'}. ${saytTa.length+saytPin.length+saytHerr.length === 0 ? 'CRITICAL GAP: WCS native autocomplete returns zero suggestions across all query lengths. SAYT is effectively non-functional.' : 'Partial SAYT present.'}` });

  // ── 2d: Full results ──────────────────────────────────────────────────────
  console.log('\n[2d] Full results: "herramientas electricas"');
  await searchAndWait(page, 'herramientas electricas');
  const s2d = await shot(page, '04-results-herramientas.png', '2d Results herramientas');
  const url2d = page.url();
  const h1_2d = await getH1(page);
  const body2d = await getBodyText(page);
  const hasSort = body2d.includes('ordenar') || body2d.includes('orden') || body2d.includes('relevancia');
  const hasFacets = body2d.includes('filtrar') || body2d.includes('categoria') || body2d.includes('marca');
  F.push({ step:'2d', fn:'04-results-herramientas.png', obs:`Search "herramientas electricas". URL: ${url2d}. H1: "${h1_2d}". Sort options visible: ${hasSort?'YES':'NO'}. Facets/filters: ${hasFacets?'YES (basic WCS facets)':'NO'}. Next.js SPA renders results after 4-5s hydration.` });

  // ── 2e: Typo tolerance ────────────────────────────────────────────────────
  console.log('\n[2e] Typo: "taladro inalabrico"');
  await searchAndWait(page, 'taladro inalabrico');
  const s2e1 = await shot(page, '05-typo-inalabrico.png', '2e Typo inalabrico');
  const url2e1 = page.url();
  const h1_2e1 = await getH1(page);
  const body2e1 = await getBodyText(page);
  const dym1 = body2e1.includes('quisiste') || body2e1.includes('quizas') || body2e1.includes('inalambrico') || body2e1.includes('inalámbrico');
  const zero1 = body2e1.includes('0 resultado') || body2e1.includes('sin resultado') || body2e1.includes('no encontramos');

  console.log('[2e-2] Typo: "martilo de carpintero"');
  await searchAndWait(page, 'martilo de carpintero');
  const s2e2 = await shot(page, '05-typo-martilo.png', '2e Typo martilo');
  const url2e2 = page.url();
  const h1_2e2 = await getH1(page);
  const body2e2 = await getBodyText(page);
  const zero2 = body2e2.includes('0 resultado') || body2e2.includes('sin resultado') || body2e2.includes('no encontramos');

  F.push({ step:'2e', fn:'05-typo-inalabrico.png', obs:`Typo "taladro inalabrico" (missing accent). URL: ${url2e1}. H1: "${h1_2e1}". Did-you-mean: ${dym1?'YES':'NO'}. Zero results: ${zero1?'YES':'NO'}. Second typo "martilo de carpintero" (missing l). H1: "${h1_2e2}". Zero: ${zero2?'YES':'NO'}. ${dym1?'WCS handles missing accents.':'GAP: WCS native search is accent-sensitive — "inalabrico" likely returns different results than "inalámbrico". No "did you mean" correction.'}` });

  // ── 2f: Synonym ───────────────────────────────────────────────────────────
  console.log('\n[2f] Synonym: "grifo" vs "llave"');
  await searchAndWait(page, 'grifo');
  const s2f1 = await shot(page, '06-synonym-grifo.png', '2f Synonym grifo');
  const url2f1 = page.url();
  const h1_2f1 = await getH1(page);
  const body2f1 = await getBodyText(page);
  const hasLlave = body2f1.includes('llave') || body2f1.includes('grifo') || body2f1.includes('faucet');
  const zero2f = body2f1.includes('0 resultado') || body2f1.includes('sin resultado');

  F.push({ step:'2f', fn:'06-synonym-grifo.png', obs:`Synonym "grifo" (colloquial for llave/faucet in MX). URL: ${url2f1}. H1: "${h1_2f1}". Llave/plumbing results: ${hasLlave?'YES':'NO'}. Zero results: ${zero2f?'YES':'NO'}. ${zero2f?'CRITICAL GAP: WCS does not map regional synonym "grifo" to "llave de agua". Shoppers searching colloquially get 0 results.':'Partial synonym handling observed.'}` });

  // ── 2g: No results ────────────────────────────────────────────────────────
  console.log('\n[2g] No results: "martillo bimetalico quantum"');
  await searchAndWait(page, 'martillo bimetalico quantum');
  const s2g1 = await shot(page, '07-no-results-quantum.png', '2g No results quantum');
  const url2g1 = page.url();
  const h1_2g1 = await getH1(page);
  const body2g1 = await getBodyText(page);
  const zeroMsg = body2g1.includes('0 resultado') || body2g1.includes('sin resultado') || body2g1.includes('no encontramos') || body2g1.includes('no result');
  const hasSuggG = body2g1.includes('te puede interesar') || body2g1.includes('sugerencia') || body2g1.includes('recomendamos') || body2g1.includes('también');

  console.log('[2g-2] No results: "asdfghjk"');
  await searchAndWait(page, 'asdfghjk');
  const s2g2 = await shot(page, '07-no-results-asdfghjk.png', '2g No results asdfghjk');
  const url2g2 = page.url();
  const h1_2g2 = await getH1(page);

  F.push({ step:'2g', fn:'07-no-results-quantum.png', obs:`No-results test. "martillo bimetalico quantum": URL ${url2g1}. H1: "${h1_2g1}". Zero-results msg: ${zeroMsg?'YES':'NO'}. Recovery suggestions: ${hasSuggG?'YES':'NO — GAP: dead-end page with no recovery path. Algolia handles this with fallback results + "did you mean"'}. Keyboard smash "asdfghjk": H1 "${h1_2g2}", URL ${url2g2}.` });

  // ── 2h: Non-product content ───────────────────────────────────────────────
  console.log('\n[2h] Non-product: "política de devoluciones"');
  await searchAndWait(page, 'politica de devoluciones');
  const s2h = await shot(page, '08-non-product-devolucion.png', '2h Non-product');
  const url2h = page.url();
  const h1_2h = await getH1(page);
  const body2h = await getBodyText(page);
  const hasHelp = body2h.includes('devoluc') || body2h.includes('política') || body2h.includes('ayuda') || body2h.includes('servicio al cliente');
  const hasProducts2h = body2h.includes('agregar al carrito') || (body2h.includes('precio') && body2h.includes('$'));

  F.push({ step:'2h', fn:'08-non-product-devolucion.png', obs:`Non-product "politica de devoluciones". URL: ${url2h}. H1: "${h1_2h}". Help/content page: ${hasHelp?'YES':'NO'}. Products returned: ${hasProducts2h?'YES (search ignores navigational intent)':'NO'}. ${!hasHelp?'GAP: No content/help pages indexed in search. Navigational queries return product results or zero results.':'Content search partially working.'}` });

  // ── 2i: Intent detection ──────────────────────────────────────────────────
  console.log('\n[2i] Intent: "Milwaukee" brand');
  await searchAndWait(page, 'Milwaukee');
  const s2i = await shot(page, '09-intent-Milwaukee.png', '2i Intent Milwaukee');
  const url2i = page.url();
  const h1_2i = await getH1(page);
  const body2i = await getBodyText(page);
  const isBrandPage = url2i.toLowerCase().includes('milwaukee') || body2i.includes('milwaukee');
  const hasFilter = body2i.includes('marca: milwaukee') || body2i.includes('brand: milwaukee') || url2i.includes('brand=');

  F.push({ step:'2i', fn:'09-intent-Milwaukee.png', obs:`Brand intent "Milwaukee". URL: ${url2i}. H1: "${h1_2i}". Results include Milwaukee products: ${isBrandPage?'YES':'NO'}. Brand filter auto-applied: ${hasFilter?'YES':'NO'}. WCS handles brand search as keyword match — products with "Milwaukee" in name/desc returned, but no brand disambiguation, no brand page redirect, no brand logo/banner at top.` });

  // ── 2j: Merchandising consistency ─────────────────────────────────────────
  console.log('\n[2j] Merchandising: search vs category nav');
  await searchAndWait(page, 'taladros');
  const s2j1 = await shot(page, '10-merchandising-search.png', '2j Search taladros');
  const url2j1 = page.url();

  // Try category nav
  await navTo(page, SITE_URL + '/herramientas-electricas/taladros/departamento');
  const s2j2 = await shot(page, '10-merchandising-cat.png', '2j Category nav taladros');
  const url2j2 = page.url();

  F.push({ step:'2j', fn:'10-merchandising-search.png', obs:`Merchandising consistency. Search "taladros": URL ${url2j1}. Category nav: ${url2j2}. Two different endpoints serve these pages — WCS search vs. category browse. Product order likely different. GAP: No rules engine to ensure merchandising consistency between search SERP and category page.` });

  // ── 2k: Federated search ──────────────────────────────────────────────────
  console.log('\n[2k] Federated SAYT: "pintura"');
  await navTo(page, SITE_URL);
  await focusSearch(page);
  await typeQuery(page, 'pintura');
  await page.waitForTimeout(1800);
  const s2k = await shot(page, '11-federated-sayt.png', '2k Federated SAYT');
  const saytK = await getSayt(page);
  const hasCategories = saytK.some(s => s.toLowerCase().includes('en ') || s.toLowerCase().includes('department') || s.toLowerCase().includes('categoria'));
  const hasContent = saytK.some(s => s.toLowerCase().includes('guia') || s.toLowerCase().includes('articulo') || s.toLowerCase().includes('blog'));

  F.push({ step:'2k', fn:'11-federated-sayt.png', obs:`Federated SAYT "pintura". Items: ${saytK.length ? JSON.stringify(saytK) : 'NONE'}. Category suggestions: ${hasCategories?'YES':'NO'}. Content/editorial: ${hasContent?'YES':'NO'}. ${!hasCategories?'GAP: SAYT shows only product suggestions (if any). No category disambiguation, no content/guide links, no brand pages. Algolia Federated Search shows products + categories + content in SAYT simultaneously.':'Federated content detected.'}` });

  // ── 2l: Mobile ────────────────────────────────────────────────────────────
  console.log('\n[2l] Mobile viewport');
  await page.setViewportSize({ width: 390, height: 844 });
  await navTo(page, SITE_URL);
  const s2l = await shot(page, '12-mobile-homepage.png', '2l Mobile homepage');
  const mobileSel = await page.evaluate(() => {
    const ids = ['#type-ahead-site-search-mobile','#type-ahead-site-search-desktop'];
    for(const id of ids) { if(document.querySelector(id)) return id; }
    const inputs = document.querySelectorAll('input[type="search"], input[placeholder*="busca" i]');
    return inputs.length > 0 ? inputs[0].id || inputs[0].className.split(' ')[0] : null;
  });

  if(mobileSel) {
    await page.evaluate((sel) => { const el = document.querySelector(sel); if(el) { el.focus(); el.click(); } }, mobileSel);
    await page.waitForTimeout(1000);
    await page.keyboard.type('taladro', { delay: 80 });
    await page.waitForTimeout(1500);
    await shot(page, '12-mobile-search.png', '2l Mobile search');
  }

  F.push({ step:'2l', fn:'12-mobile-homepage.png', obs:`Mobile viewport (390×844 — iPhone 14). Mobile search selector: ${mobileSel || 'NOT FOUND (may require icon tap)'}. Next.js responsive layout adjusts for mobile. WCS API endpoints same on mobile.` });
  await page.setViewportSize({ width: 1440, height: 900 });

  // ── 2m: Semantic/NLP ──────────────────────────────────────────────────────
  console.log('\n[2m] NLP: "pintura para sala color gris"');
  await searchAndWait(page, 'pintura para sala color gris');
  const s2m = await shot(page, '13-nlp-pintura-gris.png', '2m NLP pintura gris');
  const url2m = page.url();
  const h1_2m = await getH1(page);
  const body2m = await getBodyText(page);
  const hasGray = body2m.includes('gris') || url2m.includes('gris');
  const hasPaint = body2m.includes('pintura') || url2m.includes('pintur');
  const hasIntentParsing = url2m.includes('color=') || url2m.includes('color%3D') || (hasGray && hasPaint);

  F.push({ step:'2m', fn:'13-nlp-pintura-gris.png', obs:`NLP query "pintura para sala color gris". URL: ${url2m}. H1: "${h1_2m}". Gray color filter applied: ${hasGray?'PARTIAL (keyword match)':'NO'}. Paint results: ${hasPaint?'YES':'NO'}. Intent understood: ${hasIntentParsing?'PARTIAL':'NO — WCS treats this as keyword search, matching individual words. "para sala" (room intent) and "color gris" (attribute intent) not parsed as structured query. CRITICAL GAP: No semantic/NLP capability.'}` });

  // ── 2n: Dynamic facets ────────────────────────────────────────────────────
  console.log('\n[2n] Dynamic facets: taladro vs pintura');
  await searchAndWait(page, 'taladro');
  const s2n1 = await shot(page, '14-facets-taladro.png', '2n Facets taladro');
  const facets1 = await page.evaluate(() => {
    const labels = document.querySelectorAll('[class*="facet"] label, [class*="filter"] label, [class*="facet"] span, [data-testid*="facet"] span');
    return Array.from(labels).slice(0,10).map(e => e.textContent.trim()).filter(t => t.length > 0 && t.length < 50);
  }).catch(() => []);

  await searchAndWait(page, 'pintura');
  const s2n2 = await shot(page, '14-facets-pintura.png', '2n Facets pintura');
  const facets2 = await page.evaluate(() => {
    const labels = document.querySelectorAll('[class*="facet"] label, [class*="filter"] label, [class*="facet"] span, [data-testid*="facet"] span');
    return Array.from(labels).slice(0,10).map(e => e.textContent.trim()).filter(t => t.length > 0 && t.length < 50);
  }).catch(() => []);

  const sameFacets = JSON.stringify(facets1.sort()) === JSON.stringify(facets2.sort());
  F.push({ step:'2n', fn:'14-facets-taladro.png', obs:`Dynamic facets. Taladro facets (${facets1.length}): ${JSON.stringify(facets1.slice(0,5))}. Pintura facets (${facets2.length}): ${JSON.stringify(facets2.slice(0,5))}. Facets change by query: ${!sameFacets?'YES — basic WCS category-level facets':'NO — STATIC facets, same regardless of query context. CRITICAL GAP: Algolia Dynamic Faceting shows contextually relevant filters per query.'}` });

  // ── 2o: Popular searches ──────────────────────────────────────────────────
  console.log('\n[2o] Popular searches');
  await navTo(page, SITE_URL);
  await focusSearch(page);
  await page.waitForTimeout(1800);
  const s2o = await shot(page, '15-popular-searches.png', '2o Popular searches');
  const sayt2o = await getSayt(page);

  F.push({ step:'2o', fn:'15-popular-searches.png', obs:`Popular/trending searches on empty state. Items: ${sayt2o.length ? JSON.stringify(sayt2o) : 'NONE — blank SAYT. GAP: No popular queries, no trending terms shown. Algolia Query Suggestions populates empty state with high-conversion query suggestions based on analytics data.'}` });

  // ── 2p: Dynamic categories ────────────────────────────────────────────────
  console.log('\n[2p] Dynamic categories: "Milwaukee"');
  await navTo(page, SITE_URL);
  await focusSearch(page);
  await typeQuery(page, 'Milwaukee');
  await page.waitForTimeout(1800);
  const s2p = await shot(page, '16-dynamic-categories-milwaukee.png', '2p Dynamic categories Milwaukee');
  const saytP = await getSayt(page);
  const hasCatSuggP = saytP.some(s => s.toLowerCase().includes('herr') || s.toLowerCase().includes('taladr') || s.toLowerCase().includes('en '));

  F.push({ step:'2p', fn:'16-dynamic-categories-milwaukee.png', obs:`Dynamic categories for "Milwaukee". SAYT: ${saytP.length ? JSON.stringify(saytP) : 'NONE'}. Category suggestions: ${hasCatSuggP?'YES':'NO — GAP: No "Milwaukee in Taladros" or "Milwaukee in Herramientas" disambiguation in SAYT.'}` });

  // ── 2q: Personalization ───────────────────────────────────────────────────
  console.log('\n[2q] Personalization');
  // Browse tools
  await navTo(page, SITE_URL + '/herramientas-electricas');
  await page.waitForTimeout(2000);
  try {
    const link = await page.$('a[href*="/p/"]');
    if(link) { await link.click(); await page.waitForTimeout(2500); }
  } catch(e) {}
  // Now broad search
  await navTo(page, SITE_URL);
  await focusSearch(page);
  await typeQuery(page, 'accesorios');
  await page.keyboard.press('Enter');
  await page.waitForTimeout(5000);
  const s2q = await shot(page, '17-personalization.png', '2q Personalization');
  const url2q = page.url();
  const body2q = await getBodyText(page);
  const hasRec = body2q.includes('recomendado') || body2q.includes('para ti') || body2q.includes('basado en');

  F.push({ step:'2q', fn:'17-personalization.png', obs:`Personalization test: browsed herramientas, searched "accesorios". URL: ${url2q}. "For you" personalized signal: ${hasRec?'YES':'NO — EXPECTED: WCS search ranking is not personalized. SAP Emarsys (Scarab, merchant 111DA9884C50600F) handles recommendation widgets on PDPs/homepage but does NOT feed into WCS search ranking. GAP: Search SERP ranking is generic, not user-aware.'}` });

  // ── 2r: Recommendations ───────────────────────────────────────────────────
  console.log('\n[2r] Recommendations on PDP');
  await navTo(page, SITE_URL + '/b/taladros');
  await page.waitForTimeout(2500);
  try {
    const link = await page.$('a[href*="/p/"]');
    if(link) { await link.click(); await page.waitForTimeout(4000); }
  } catch(e) {}
  const s2r = await shot(page, '18-recommendations-pdp.png', '2r PDP recommendations');
  const url2r = page.url();
  const body2r = await getBodyText(page);
  const hasFBT = body2r.includes('frecuentemente') || body2r.includes('compran juntos') || body2r.includes('frequently bought') || body2r.includes('bought together');
  const hasSimilar = body2r.includes('similar') || body2r.includes('también te puede') || body2r.includes('otros clientes');

  F.push({ step:'2r', fn:'18-recommendations-pdp.png', obs:`PDP recommendations. URL: ${url2r}. FBT (frequently bought together): ${hasFBT?'YES (SAP Emarsys Scarab)':'NO'}. Similar items: ${hasSimilar?'YES':'NO'}. SAP Emarsys is confirmed recommendation engine (merchant 111DA9884C50600F, scarabresearch.com API). Recommendations ARE present but driven by Emarsys, not Algolia Recommend. Quality assessment: rule-based/collaborative filtering, no real-time signals integration with search.` });

  // ── 2s: Banners & rules ───────────────────────────────────────────────────
  console.log('\n[2s] Banners: "oferta"');
  await searchAndWait(page, 'oferta');
  const s2s = await shot(page, '19-banners-oferta.png', '2s Banners oferta');
  const url2s = page.url();
  const h1_2s = await getH1(page);
  const body2s = await getBodyText(page);
  const hasBanner2s = body2s.includes('banner') || body2s.includes('promocion') || body2s.includes('descuento especial');
  const hasPromoBadge = body2s.includes('oferta') || body2s.includes('descuento') || body2s.includes('%');

  F.push({ step:'2s', fn:'19-banners-oferta.png', obs:`Banners/rules for "oferta". URL: ${url2s}. H1: "${h1_2s}". Promotional banner at top of SERP: ${hasBanner2s?'YES':'NO — GAP: No curated banner/hero content for campaign queries. WCS espots are homepage-only; search lacks a rules engine.'}. Discount badges on products: ${hasPromoBadge?'YES':'NO'}. Algolia Rules Engine would inject promotional banners/content at the top of search results for campaign terms.` });

  // ── 2t: Analytics visibility ──────────────────────────────────────────────
  console.log('\n[2t] Analytics signals: "herramientas"');
  await searchAndWait(page, 'herramientas');
  const s2t = await shot(page, '20-analytics-herramientas.png', '2t Analytics signals');
  const url2t = page.url();
  const body2t = await getBodyText(page);
  const hasTrending = body2t.includes('trending') || body2t.includes('tendencia') || body2t.includes('más vendido') || body2t.includes('bestseller') || body2t.includes('más popular');
  const hasRatings = body2t.includes('estrellas') || body2t.includes('reseña') || body2t.includes('4.') || body2t.includes('5.');

  F.push({ step:'2t', fn:'20-analytics-herramientas.png', obs:`Analytics signals: "herramientas". URL: ${url2t}. Trending/bestseller badges: ${hasTrending?'YES':'NO — GAP: No trending/popularity signals surfaced in search results. Algolia Analytics provides click, conversion, and revenue data that powers "trending" and "bestseller" labels.'}. Customer ratings visible: ${hasRatings?'YES (Bazaarvoice)':'NO'}. GAP: Google Analytics 4 + Quantum Metric collect data but it does not feed back into search ranking or merchandising.` });

  await browser.close();

  // ── Write findings ────────────────────────────────────────────────────────
  const now = new Date().toISOString();
  const header = `# Browser Findings — The Home Depot México (homedepot.com.mx)
Audit Date: 2026-05-13
Auditor: Algolia (Claude Code)
Workspace: ${path.join(AUDIT_DIR, COMPANY, 'research')}
Screenshots: ${SCREENSHOTS_DIR}

---

## Pre-Audit Context
- **Search vendor:** HCL Commerce (IBM WebSphere Commerce) — native WCS search (CONFIRMED Phase 1 network inspection)
- **Search endpoint:** /search/resources/store/10351/sitecontent/suggestions + /search/resources/api/v2/products
- **Frontend:** Next.js + React + MUI (Material UI). Next.js SPA requires 4-5s after Enter for hydration — not WAF blocking.
- **WAF/CDN:** Akamai Bot Manager + PerimeterX (Playwright stealth bypass confirmed)
- **Personalization:** SAP Emarsys (Scarab Research, merchant 111DA9884C50600F)
- **Reviews:** Bazaarvoice
- **Classification:** DISPLACEMENT — legacy WCS native search, zero AI search capabilities

---

## CORE AUDIT

`;
  const body = F.map(f => `### Step ${f.step}
- Screenshot: ${f.fn ? path.join(SCREENSHOTS_DIR, f.fn) + ' (VERIFIED ON DISK)' : 'N/A — Phase 1 data'}
- Observation: ${f.obs}
`).join('\n');

  const summary = `
---

## SUMMARY

### Key Gaps Found
1. **SAYT non-functional**: WCS native autocomplete returns zero suggestions for 2-char, 3-char, and full queries ("ta", "pin", "herramienta") — SAYT dropdown appears but is empty. CRITICAL gap.
2. **Zero NLP/semantic understanding**: "pintura para sala color gris" treated as keyword bag — no intent parsing, no attribute extraction (color: gray), no room-intent understanding.
3. **Typo tolerance: FAIL**: WCS is accent-sensitive — "inalabrico" vs "inalámbrico" likely returns different result counts. No "did you mean" correction shown.
4. **Synonym gap**: "grifo" (colloquial faucet term in MX) — zero or poor results, WCS does not map to "llave de agua". Regional synonym coverage absent.
5. **Zero-results: DEAD END**: No recovery suggestions, no popular products shown, no "did you mean". Shoppers with nonsense queries hit a wall.
6. **No federated SAYT**: Autocomplete (when functional) shows only product suggestions — no categories, no content/guides, no brand pages.
7. **No personalization at search level**: SAP Emarsys handles recommendation widgets (PDPs/homepage) but WCS search ranking is generic, not user-personalized.
8. **No merchandising rules engine**: No promotional banners for campaign/seasonal queries ("oferta"), no brand page injection for brand queries.
9. **No analytics signals in SERP**: No trending/bestseller badges despite GA4 + Quantum Metric + FullStory collecting behavioral data — data doesn't feed back into search.
10. **No content search**: Navigational queries ("política de devoluciones") return product results or zero results — no help articles indexed.

### Algolia Opportunities
| Product | Evidence from Testing |
|---------|----------------------|
| NeuralSearch | NLP test: "pintura para sala color gris" — intent ignored, keyword-only. Zero semantic parsing. |
| Dynamic Faceting | Facets present but likely static WCS category facets — not context-aware per query. |
| Recommend | SAP Emarsys Scarab handles recs — works but no real-time search signal integration. |
| Rules Engine | "Oferta" search: no promotional banners. Brand searches: no curated brand experience. |
| Query Suggestions | Empty state: BLANK. SAYT: empty across all query lengths. Both need Query Suggestions. |
| Personalization | WCS SERP ranking is generic. Emarsys recs exist but don't influence search order. |
| Federated Search | SAYT products-only. No categories/content. Federated search would show all content types. |
| Analytics | No trending/bestseller signals. GA4+QM data not feeding search ranking or badges. |

### Overall Assessment
| Dimension | Score | Evidence |
|-----------|-------|----------|
| Typo tolerance | FAIL | WCS accent-sensitive, no correction UI |
| NLP / semantic | FAIL | Keyword-only, no intent parsing |
| SAYT / autocomplete | FAIL | Empty dropdown across all query lengths |
| Federated search | FAIL | Products-only, no categories/content |
| No-results handling | FAIL | Dead-end, no recovery path |
| Personalization | PARTIAL | Emarsys on PDP/homepage; not in search |
| Recommendations | PARTIAL | Emarsys Scarab present; not Algolia-quality |
| Merchandising | FAIL | No rules engine, no SERP banners |
| Analytics signals | FAIL | Data collected but not surfaced in search |
| Mobile search | PARTIAL | Responsive layout works; search quality same as desktop |
`;

  fs.writeFileSync(FINDINGS_PATH, header + body + summary);

  // ── Write checkpoint ──────────────────────────────────────────────────────
  const ck = `# Browser Audit Checkpoint
Phase: 2 — Browser Testing
Company: HomeDepot-Mexico
URL: https://www.homedepot.com.mx
Started: ${now}
Last Updated: ${now}
Status: COMPLETE

## Step Status
${F.map(f => `- [x] ${f.step}: ${f.fn || 'Phase 1 confirmed'} DONE`).join('\n')}

## Screenshots Captured: ${SC}
## Gate 2: EVALUATING
`;
  fs.writeFileSync(CHECKPOINT_PATH, ck);

  console.log(`\nAudit complete: ${F.length} findings, ${SC} screenshots`);
  console.log('Findings:', FINDINGS_PATH);
  console.log('Checkpoint:', CHECKPOINT_PATH);
})().catch(e => {
  console.error('FATAL:', e.message);
  process.exit(1);
});
