#!/usr/bin/env node
/**
 * collect-similarweb-browser.js — SimilarWeb browser-based data collector
 *
 * One-time interactive login saves a session; all subsequent runs are headless.
 * Login flow: SimilarWeb → Google → Algolia SSO (Okta) → MFA → back to SW.
 * Script handles navigation; user handles SSO + MFA in the headed window.
 *
 * Usage:
 *   node collect-similarweb-browser.js --setup
 *     → Headed browser, user completes Google/Okta/MFA, session saved
 *
 *   node collect-similarweb-browser.js --mode tech --domain homedepot.com.mx
 *     → Scrape technology stack (for algolia-intel-techstack)
 *
 *   node collect-similarweb-browser.js --mode traffic --domain homedepot.com.mx
 *     → Scrape traffic overview + channels + keywords + referrals + geo
 *       (for algolia-intel-traffic — includes referring industries, previously API-only)
 *
 *   node collect-similarweb-browser.js --mode all --domain homedepot.com.mx
 *     → All modes, combined JSON to stdout
 *
 *   node collect-similarweb-browser.js --check-session
 *     → Verify session is still valid, exit 0 if yes, 1 if expired
 *
 * Output: JSON to stdout. Progress/errors to stderr.
 * Exit codes: 0 = success, 1 = session expired (run --setup), 2 = other error
 */

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());

const path = require('path');
const fs   = require('fs');

// ── Config ────────────────────────────────────────────────────────────────────

const SCRIPT_DIR   = __dirname;
const AUTH_DIR     = path.join(SCRIPT_DIR, '..', 'auth');
// Persistent browser profile — stores full browser state including TLS session cache
// and anti-bot fingerprint tokens. Survives restarts unlike storageState (cookies only).
const PROFILE_DIR  = path.join(AUTH_DIR, 'sw-profile');
const SW_BASE      = 'https://www.similarweb.com';
// Credentials are NEVER stored or auto-filled. User enters them manually in --setup.

// How long to wait for the user to complete SSO + MFA (ms)
const LOGIN_TIMEOUT_MS  = 5 * 60 * 1000; // 5 minutes
const LOGIN_POLL_MS     = 3000;
const PAGE_SETTLE_MS    = 3500; // wait after navigation for JS to render

const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
const VIEWPORT   = { width: 1440, height: 900 };

// ── Arg parsing ───────────────────────────────────────────────────────────────

const args    = process.argv.slice(2);
const getArg  = (f) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : null; };
const hasFlag = (f) => args.includes(f);

const isSetup        = hasFlag('--setup');
const isCheckSession = hasFlag('--check-session');
const mode           = getArg('--mode');   // tech | traffic | all
const domain         = getArg('--domain');

// ── Profile helpers ───────────────────────────────────────────────────────────
// Using launchPersistentContext instead of storageState — preserves full browser
// state including TLS session cache and anti-bot fingerprint tokens across restarts.

function profileExists() {
  // A valid Chromium profile has a Default/Cookies file
  return fs.existsSync(path.join(PROFILE_DIR, 'Default', 'Cookies'));
}

function launchOptions(headless = false) {
  return {
    headless,
    slowMo: headless ? 0 : 60,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    viewport: VIEWPORT,
    userAgent: USER_AGENT,
  };
}

// ── Login detection ───────────────────────────────────────────────────────────

async function isLoggedIn(page) {
  try {
    const url = page.url();
    // Still on an auth provider page
    if (
      url.includes('accounts.google.com') ||
      url.includes('okta.com') ||
      url.includes('/sso/') ||
      url.includes('/login') ||
      url.includes('/signin') ||
      url.includes('/signup')
    ) return false;

    // Back on SimilarWeb — look for any logged-in indicator
    const indicators = [
      '[data-testid="user-menu"]',
      '[class*="UserMenu"]',
      '[class*="user-menu"]',
      '[class*="account-menu"]',
      '[class*="AccountMenu"]',
      '[aria-label*="account" i]',
      '[data-testid="header-user"]',
      // SW Research Intelligence layout
      '[class*="AppHeader"] [class*="avatar"]',
      '[class*="navbar"] [class*="user"]',
      '.sw-user-menu',
    ];
    for (const sel of indicators) {
      if (await page.$(sel)) return true;
    }
    // Soft check: on SW domain, not on a login/auth path
    return (
      (url.startsWith('https://www.similarweb.com') ||
       url.startsWith('https://pro.similarweb.com')) &&
      !url.includes('/corp/login') &&
      !url.includes('/login')
    );
  } catch { return false; }
}

// ── Screenshot helper ─────────────────────────────────────────────────────────

async function screenshot(page, label, domain) {
  try {
    fs.mkdirSync(AUTH_DIR, { recursive: true });
    const filename = `sw-${label}-${domain}-${Date.now()}.png`;
    const filepath = path.join(AUTH_DIR, filename);
    await page.screenshot({ path: filepath, fullPage: false });
    const size = fs.statSync(filepath).size;
    console.error(`  📸 ${label}: ${filepath} (${size} bytes${size < 50000 ? ' ⚠️ small — possible WAF/paywall' : ''})`);
    return filepath;
  } catch (e) {
    console.error(`  ⚠️  Screenshot failed (${label}): ${e.message}`);
    return null;
  }
}

// ── Wait helpers ──────────────────────────────────────────────────────────────

async function safeGoto(page, url) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(PAGE_SETTLE_MS);
  const landed = page.url();
  console.error(`    [safeGoto] ${url} → landed: ${landed}`);
  if (landed.includes('/login') || landed.includes('/corp/login')) {
    console.error(`    ⚠️  Redirected to login — not closing window, continuing`);
    // Don't throw — log and carry on so the window stays alive for debugging
  }
}

async function tryExtract(page, selectors, fallback = null) {
  for (const sel of Array.isArray(selectors) ? selectors : [selectors]) {
    try {
      const el = await page.$(sel);
      if (el) return (await el.innerText()).trim();
    } catch { /* try next */ }
  }
  return fallback;
}

async function tryExtractAll(page, selectors) {
  for (const sel of Array.isArray(selectors) ? selectors : [selectors]) {
    try {
      const els = await page.$$(sel);
      if (els.length > 0) return Promise.all(els.map(e => e.innerText().then(t => t.trim())));
    } catch { /* try next */ }
  }
  return [];
}

// ── Setup: interactive login (manual credentials — never auto-filled) ─────────
// Opens a browser window. User enters credentials manually. Persistent profile
// saved to PROFILE_DIR — survives restarts, preserves full TLS fingerprint.
// Only needs to be run once; subsequent scraping runs reuse the profile.

async function runSetup() {
  fs.mkdirSync(PROFILE_DIR, { recursive: true });

  console.error('');
  console.error('🔐 SimilarWeb Login Setup');
  console.error('   Profile: ' + PROFILE_DIR);
  console.error('');
  console.error('   A browser window will open at the SimilarWeb login page.');
  console.error('   Please enter your credentials manually in the browser.');
  console.error('   No credentials are auto-filled, stored, or logged by this script.');
  console.error('');

  const context = await chromium.launchPersistentContext(PROFILE_DIR, launchOptions(false));
  const page    = await context.newPage();

  await page.goto(`${SW_BASE}/corp/login/`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  console.error('   → Login page open. Please sign in now.');
  console.error('⏳ Waiting up to 5 minutes for you to complete login...');

  const deadline = Date.now() + LOGIN_TIMEOUT_MS;
  let loggedIn   = false;
  let verificationPrompted = false;

  while (Date.now() < deadline) {
    await page.waitForTimeout(LOGIN_POLL_MS);
    const url = page.url();

    if (url.includes('device-verification') && !verificationPrompted) {
      console.error('   ⚠️  Device verification required — check your email for a code from SimilarWeb');
      verificationPrompted = true;
    }

    const onSW = (url.startsWith('https://www.similarweb.com') ||
                  url.startsWith('https://pro.similarweb.com') ||
                  url.startsWith('https://secure.similarweb.com')) &&
                 !url.includes('/login') &&
                 !url.includes('device-verification');

    if (onSW) { loggedIn = true; break; }
  }

  if (!loggedIn) {
    console.error('❌ Login not detected within time limit. Re-run --setup.');
    await context.close();
    process.exit(1);
  }

  await context.close(); // profile auto-saved to PROFILE_DIR

  console.error('');
  console.error('✓ Login complete. Profile saved → ' + PROFILE_DIR);
  console.error('  Subsequent scraping runs will reuse this profile automatically.');
  console.error('  Re-run --setup if you see 403 errors (profile expired ~30–60 days).');
  console.error('');
  process.exit(0);
}

// ── Session check ─────────────────────────────────────────────────────────────

async function runCheckSession() {
  if (!profileExists()) {
    console.error('No browser profile found. Run: node collect-similarweb-browser.js --setup');
    process.exit(1);
  }
  const context = await chromium.launchPersistentContext(PROFILE_DIR, launchOptions(true));
  const page    = await context.newPage();

  await page.goto(SW_BASE, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(2000);
  const valid = await isLoggedIn(page);
  await context.close();

  if (valid) {
    console.error('✓ Profile valid');
    process.exit(0);
  } else {
    console.error('❌ Profile expired — run: node collect-similarweb-browser.js --setup');
    process.exit(1);
  }
}

// ── Tech stack scraping ───────────────────────────────────────────────────────

async function scrapeTech(page, domain) {
  console.error('  📊 Scraping: technology stack');
  const url = `${SW_BASE}/website/${domain}/technologies/`;
  await safeGoto(page, url);

  const result = {
    source_url:  url,
    scraped_at:  new Date().toISOString(),
    technologies: {},
    raw_fallback: null,
  };

  // SimilarWeb tech page shows categories (e.g. "CMS", "Analytics", "Search & Discovery")
  // with individual tech names inside each. Selectors vary by SW version.
  const categorySels = [
    '[class*="technology-category"]',
    '[class*="TechnologyCategory"]',
    '[data-testid*="technology-group"]',
    '[class*="technologies-group"]',
  ];
  const nameSels = [
    '[class*="technology-name"]',
    '[class*="TechnologyName"]',
    '[class*="tech-name"]',
    'li[class*="technology"]',
  ];
  const headingSels = ['h3', 'h4', '[class*="category-title"]', '[class*="group-title"]'];

  let extracted = false;
  for (const catSel of categorySels) {
    const cats = await page.$$(catSel);
    if (cats.length === 0) continue;
    for (const cat of cats) {
      const heading = await tryExtract(cat, headingSels, 'Unknown');
      const names = await tryExtractAll(cat, nameSels);
      if (names.length > 0) {
        result.technologies[heading] = names;
        extracted = true;
      }
    }
    if (extracted) break;
  }

  // Fallback: grab raw page text for LLM parsing
  if (!extracted) {
    console.error('  ⚠️  Named selectors found nothing — falling back to raw text');
    result.raw_fallback = await page.$eval(
      'main, [class*="content-main"], #app, body',
      el => el.innerText.replace(/\s+/g, ' ').substring(0, 4000)
    ).catch(() => null);
  }

  result.screenshot = await screenshot(page, 'tech', domain);
  return result;
}

// ── Traffic scraping ──────────────────────────────────────────────────────────

async function scrapeOverview(page, domain) {
  console.error('  📊 Scraping: traffic overview');
  await safeGoto(page, `${SW_BASE}/website/${domain}/overview/`);

  // KPI tile selectors — SW uses these consistently across versions
  const kpiMap = {
    monthly_visits:    ['[data-test="total-visits"] [class*="value"]',   '[class*="totalVisits"] [class*="engagement-value"]', '[class*="visits"] [class*="bigNumber"]'],
    bounce_rate:       ['[data-test="bounce-rate"] [class*="value"]',    '[class*="bounceRate"] [class*="engagement-value"]'],
    pages_per_visit:   ['[data-test="pages-per-visit"] [class*="value"]','[class*="pagesPerVisit"] [class*="engagement-value"]'],
    avg_visit_duration:['[data-test="avg-visit-duration"] [class*="value"]', '[class*="avgVisitDuration"] [class*="engagement-value"]'],
  };

  const result = { source_url: page.url(), scraped_at: new Date().toISOString() };
  for (const [key, sels] of Object.entries(kpiMap)) {
    result[key] = await tryExtract(page, sels);
  }

  // Fallback raw capture
  if (!result.monthly_visits) {
    result.raw_overview = await page.$eval('main', el => el.innerText.replace(/\s+/g, ' ').substring(0, 3000)).catch(() => null);
  }

  result.screenshot = await screenshot(page, 'overview', domain);
  return result;
}

async function scrapeChannels(page, domain) {
  console.error('  📊 Scraping: traffic channels');
  await safeGoto(page, `${SW_BASE}/website/${domain}/traffic-sources/`);

  const channelSels = [
    '[class*="channel"] [class*="source-name"]',
    '[class*="trafficSource"] [class*="name"]',
    '[data-testid*="channel"]',
  ];
  const valueSels = [
    '[class*="channel"] [class*="value"]',
    '[class*="trafficSource"] [class*="percentage"]',
  ];

  const names  = await tryExtractAll(page, channelSels);
  const values = await tryExtractAll(page, valueSels);

  const channels = names.length > 0
    ? names.reduce((acc, n, i) => { acc[n] = values[i] || null; return acc; }, {})
    : null;

  const result = {
    source_url:   page.url(),
    scraped_at:   new Date().toISOString(),
    channels,
    raw_fallback: channels ? null : await page.$eval('main', el => el.innerText.replace(/\s+/g, ' ').substring(0, 2000)).catch(() => null),
    screenshot:   await screenshot(page, 'channels', domain),
  };
  return result;
}

async function scrapeReferrals(page, domain) {
  // This section includes referring industries — previously NOT available via SW API
  console.error('  📊 Scraping: referrals + referring industries (UI-only data)');
  await safeGoto(page, `${SW_BASE}/website/${domain}/referrals/`);

  const industrySels = [
    '[class*="referring-industry"]',
    '[class*="referringIndustry"]',
    '[data-testid*="industry"]',
  ];
  const industries = await tryExtractAll(page, industrySels);

  const result = {
    source_url:           page.url(),
    scraped_at:           new Date().toISOString(),
    referring_industries: industries.length > 0 ? industries : null,
    raw_fallback:         industries.length > 0 ? null : await page.$eval('main', el => el.innerText.replace(/\s+/g, ' ').substring(0, 2000)).catch(() => null),
    screenshot:           await screenshot(page, 'referrals', domain),
  };
  return result;
}

async function scrapeKeywords(page, domain) {
  console.error('  📊 Scraping: search keywords');
  await safeGoto(page, `${SW_BASE}/website/${domain}/search-keywords/`);

  const kwSels = ['[class*="keyword-name"]', '[class*="keywordName"]', '[data-testid*="keyword"]'];
  const keywords = await tryExtractAll(page, kwSels);

  return {
    source_url:   page.url(),
    scraped_at:   new Date().toISOString(),
    keywords:     keywords.length > 0 ? keywords.slice(0, 30) : null,
    raw_fallback: keywords.length > 0 ? null : await page.$eval('main', el => el.innerText.replace(/\s+/g, ' ').substring(0, 2000)).catch(() => null),
    screenshot:   await screenshot(page, 'keywords', domain),
  };
}

async function scrapeGeo(page, domain) {
  console.error('  📊 Scraping: geography');
  await safeGoto(page, `${SW_BASE}/website/${domain}/geography/`);
  return {
    source_url:   page.url(),
    scraped_at:   new Date().toISOString(),
    raw_fallback: await page.$eval('main', el => el.innerText.replace(/\s+/g, ' ').substring(0, 2000)).catch(() => null),
    screenshot:   await screenshot(page, 'geo', domain),
  };
}

async function scrapeCompetitors(page, domain) {
  console.error('  📊 Scraping: competitors (summary for traffic report)');
  await safeGoto(page, `${SW_BASE}/website/${domain}/competitors/`);

  const compSels = ['[class*="competitor-name"]', '[class*="competitorName"]', '[data-testid*="competitor"] [class*="name"]'];
  const competitors = await tryExtractAll(page, compSels);

  return {
    source_url:   page.url(),
    scraped_at:   new Date().toISOString(),
    competitors:  competitors.length > 0 ? competitors.slice(0, 15) : null,
    raw_fallback: competitors.length > 0 ? null : await page.$eval('main', el => el.innerText.replace(/\s+/g, ' ').substring(0, 2000)).catch(() => null),
    screenshot:   await screenshot(page, 'competitors', domain),
  };
}

// Discovery mode: extracts structured competitor objects with verified domains.
// Used by collect-competitors.py as replacement for the dead SW similar-sites API.
// Strategy: SW always links to competitor profiles as /website/{domain}/ — extract
// domains from those internal navigation links rather than relying on class selectors.
// Two-hop navigation: overview first → competitors, to set proper HTTP referrer and
// avoid CloudFront 403 on cold direct navigation to deep SW paths.
async function scrapeCompetitorDiscovery(page, domain) {
  console.error('  📊 Competitor discovery — two-hop nav: overview → competitors tab');

  // Hop 1: overview (establishes session context + referrer for CloudFront)
  await safeGoto(page, `${SW_BASE}/website/${domain}/overview/`);
  await page.waitForTimeout(2000);

  // Hop 2: navigate to competitors tab via SW internal link (preserves referrer)
  // Try clicking the Competitors tab first — if not found, navigate directly
  const tabClicked = await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll('a, button, [role="tab"]'));
    const compTab = tabs.find(t => /^competitors?$/i.test((t.textContent || '').trim()));
    if (compTab) { compTab.click(); return true; }
    return false;
  });

  if (tabClicked) {
    console.error('  → Clicked Competitors tab in nav');
    await page.waitForTimeout(3000);
  } else {
    console.error('  → Tab click failed — navigating directly');
    await page.goto(`${SW_BASE}/website/${domain}/competitors/`, {
      waitUntil: 'domcontentloaded', timeout: 30000,
      referer: `${SW_BASE}/website/${domain}/overview/`,
    });
    await page.waitForTimeout(3000);
  }

  // Check for CloudFront 403 block
  const bodyText = await page.$eval('body', el => el.innerText.substring(0, 200)).catch(() => '');
  if (bodyText.includes('403') || bodyText.includes('Request blocked')) {
    console.error('  ⚠️  CloudFront 403 — falling back to WebSearch competitor discovery');
    return { competitors: [], raw_fallback: null, screenshot: null, error: 'CloudFront 403' };
  }

  // Wait for the competitor list to render
  await page.waitForTimeout(1500);

  const shot = await screenshot(page, 'competitor-discovery', domain);

  // Primary: extract competitor domains from SW internal /website/{domain}/ links
  // These are always present regardless of UI version
  const discovered = await page.$$eval('a[href*="/website/"]', (els, targetDomain) => {
    const seen = new Set();
    const results = [];
    for (const el of els) {
      const href = el.getAttribute('href') || '';
      const match = href.match(/\/website\/([a-z0-9][a-z0-9\-\.]+\.[a-z]{2,})\//i);
      if (!match) continue;
      const compDomain = match[1].toLowerCase();
      // Skip self, SW internal pages, and duplicates
      if (compDomain === targetDomain) continue;
      if (compDomain.includes('similarweb')) continue;
      if (seen.has(compDomain)) continue;
      seen.add(compDomain);

      // Try to get the display name from the link text or nearby heading
      const name = el.innerText.trim() || el.getAttribute('title') || compDomain;

      // Try to find visits/traffic data nearby (parent row)
      const row = el.closest('tr, [class*="row"], [class*="Row"], li');
      let visits = null;
      if (row) {
        const text = row.innerText || '';
        const visitMatch = text.match(/(\d+[\.,]?\d*\s*[KMB]?)\s*(visits|\/mo)?/i);
        if (visitMatch) visits = visitMatch[1].trim();
      }

      results.push({ domain: compDomain, name: name.split('\n')[0].trim(), visits });
    }
    return results.slice(0, 10);
  }, domain).catch(() => []);

  // Fallback: raw text for LLM parsing if link extraction fails
  let rawFallback = null;
  if (discovered.length === 0) {
    console.error('  ⚠️  Link extraction returned 0 — capturing raw text fallback');
    rawFallback = await page.$eval('main', el =>
      el.innerText.replace(/\s+/g, ' ').substring(0, 3000)
    ).catch(() => null);
  }

  console.error(`  Found ${discovered.length} competitors via link extraction`);

  return {
    source_url:  page.url(),
    scraped_at:  new Date().toISOString(),
    competitors: discovered,
    raw_fallback: rawFallback,
    screenshot:  shot,
  };
}

async function scrapeTraffic(page, domain) {
  return {
    overview:     await scrapeOverview(page, domain),
    channels:     await scrapeChannels(page, domain),
    referrals:    await scrapeReferrals(page, domain),
    keywords:     await scrapeKeywords(page, domain),
    geo:          await scrapeGeo(page, domain),
    competitors:  await scrapeCompetitors(page, domain),
  };
}

// ── Main ──────────────────────────────────────────────────────────────────────

(async () => {
  if (isSetup)        { await runSetup();        return; }
  if (isCheckSession) { await runCheckSession(); return; }

  if (!mode || !domain) {
    console.error('Usage:');
    console.error('  node collect-similarweb-browser.js --setup');
    console.error('  node collect-similarweb-browser.js --check-session');
    console.error('  node collect-similarweb-browser.js --mode tech                  --domain example.com');
    console.error('  node collect-similarweb-browser.js --mode traffic               --domain example.com');
    console.error('  node collect-similarweb-browser.js --mode all                   --domain example.com');
    console.error('  node collect-similarweb-browser.js --mode competitors-discovery --domain example.com');
    process.exit(2);
  }

  // CloudFront uses session-only __cf_bm cookies that are destroyed when the browser
  // closes. Research pages 403 on any cold start — even with persistent profile.
  // Fix: login + scraping MUST happen in the same browser session. Login first,
  // then scrape immediately while the cf_bm cookie is fresh.

  console.error(`\n🔍 SimilarWeb scrape — ${domain} (mode: ${mode})`);
  console.error('   Browser will open. Please log in to SimilarWeb, then scraping starts automatically.');
  console.error('   (With persistent profile this is usually just one click — "Continue as Arijit")');

  fs.mkdirSync(PROFILE_DIR, { recursive: true });
  const context = await chromium.launchPersistentContext(PROFILE_DIR, launchOptions(false));
  const page    = await context.newPage();

  // Step 1: Login — use the correct SW login URL
  console.error('   → Opening: https://secure.similarweb.com/account/login');
  await page.goto('https://secure.similarweb.com/account/login', { waitUntil: 'domcontentloaded', timeout: 30000 });
  console.error('   → Login page open. Please sign in (click Login with Google, select your account).');
  console.error('   ⚠️  KEEP THE BROWSER WINDOW OPEN — scraping runs in the same window after you log in.');

  const loginDeadline = Date.now() + LOGIN_TIMEOUT_MS;
  let loggedIn = false;
  let landingUrl = '';

  while (Date.now() < loginDeadline) {
    try {
      await page.waitForTimeout(LOGIN_POLL_MS);
    } catch {
      console.error('❌ Browser window was closed during login. Please re-run and keep the window open.');
      process.exit(1);
    }

    let url = '';
    try { url = page.url(); } catch { break; }

    const isLoginPage   = url.includes('account/login') || url.includes('/corp/login');
    const isGoogleOAuth = url.includes('accounts.google.com');
    const isDeviceVerif = url.includes('device-verification');
    const isSWDomain    = url.includes('similarweb.com');

    if (isDeviceVerif) {
      console.error('   ⚠️  DEVICE VERIFICATION: Enter the code from your email in the browser — DO NOT close the window!');
    }

    if (isSWDomain && !isLoginPage && !isGoogleOAuth && !isDeviceVerif) {
      loggedIn   = true;
      landingUrl = url;
      break;
    }
  }

  if (!loggedIn) {
    console.error('❌ Login not detected within 5 minutes. Re-run to try again.');
    await context.close().catch(() => {});
    process.exit(1);
  }

  console.error(`   ✓ Logged in — landed on: ${landingUrl}`);

  // Bridge authentication: after login, navigate to www.similarweb.com to establish
  // www-domain cookies before accessing research pages.
  console.error('   → Bridging to www.similarweb.com research pages...');
  await page.goto('https://www.similarweb.com/', { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(3000);
  console.error('   → Ready. Starting scrape.');

  // Step 2: Navigate to SW research pages (cf_bm cookie is fresh from login)
  let output = { domain, mode, scraped_at: new Date().toISOString() };

  try {

    if (mode === 'tech' || mode === 'all') {
      output.tech = await scrapeTech(page, domain);
    }
    if (mode === 'traffic' || mode === 'all') {
      output.traffic = await scrapeTraffic(page, domain);
    }
    if (mode === 'competitors-discovery') {
      output.competitors_discovery = await scrapeCompetitorDiscovery(page, domain);
    }

    console.log(JSON.stringify(output, null, 2));
  } catch (e) {
    console.error('❌ Scrape error: ' + e.message);
    console.error('   Current URL: ' + page.url());
    // DO NOT close the window — keep it open so we can see what happened
    console.error('   Window kept open for inspection.');
  }

  await context.close();
})();
