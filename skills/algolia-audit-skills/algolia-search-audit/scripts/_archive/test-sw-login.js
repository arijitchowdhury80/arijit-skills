#!/usr/bin/env node
/**
 * test-sw-login.js — Pressure test for SimilarWeb Google login flow
 *
 * Flow: similarweb.com → Login → Continue with Google → pick arijit.chowdhury@algolia.com
 *
 * Run: node test-sw-login.js
 *
 * What it does:
 *   1. Opens a visible browser (you watch it happen)
 *   2. Navigates to SimilarWeb login
 *   3. Clicks "Continue with Google"
 *   4. Selects / fills arijit.chowdhury@algolia.com on Google account picker
 *   5. Waits for redirect back to SimilarWeb
 *   6. Confirms login and saves session to test-sw-session.json
 *   7. Optionally tests the session by navigating to a domain research page
 *
 * Exits 0 on success, 1 on failure.
 * Screenshots saved to: ../auth/test-login-*.png
 */

const { chromium } = require('playwright-extra');
const stealth      = require('puppeteer-extra-plugin-stealth');
chromium.use(stealth());

const path = require('path');
const fs   = require('fs');

const AUTH_DIR      = path.join(__dirname, '..', 'auth');
const SESSION_FILE  = path.join(AUTH_DIR, 'test-sw-session.json');
const LOGIN_EMAIL   = 'arijit.chowdhury@algolia.com';
const SW_LOGIN_URL  = 'https://www.similarweb.com/corp/login/';
const TEST_DOMAIN   = 'homedepot.com.mx'; // used to verify session after login

fs.mkdirSync(AUTH_DIR, { recursive: true });

// ── Helpers ───────────────────────────────────────────────────────────────────

async function shot(page, label) {
  const file = path.join(AUTH_DIR, `test-login-${label}-${Date.now()}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log(`  📸 ${label}: ${file}`);
  return file;
}

async function clickFirst(page, selectors, description, timeout = 6000) {
  for (const sel of selectors) {
    try {
      await page.waitForSelector(sel, { timeout });
      await page.click(sel);
      console.log(`  ✓ Clicked: ${description} (${sel})`);
      return sel;
    } catch { /* try next */ }
  }
  console.log(`  ⚠️  Could not find: ${description}`);
  return null;
}

// ── Main ──────────────────────────────────────────────────────────────────────

(async () => {
  console.log('\n🧪 SimilarWeb Login Test');
  console.log('   Email:', LOGIN_EMAIL);
  console.log('   Browser: headed (watch the window)\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 80,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();

  // ── Step 1: SimilarWeb login page ────────────────────────────────────────────
  console.log('Step 1: Navigate to SimilarWeb login');
  await page.goto(SW_LOGIN_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(2000);
  await shot(page, '01-sw-login-page');
  console.log('  URL:', page.url());

  // ── Step 2: Click "Continue with Google" ─────────────────────────────────────
  console.log('\nStep 2: Click "Continue with Google"');
  const googleClicked = await clickFirst(page, [
    'a:has-text("Continue with Google")',
    'button:has-text("Continue with Google")',
    'a:has-text("Sign in with Google")',
    'button:has-text("Sign in with Google")',
    '[class*="google" i]:visible',
    'a[href*="google"]:visible',
    '[data-provider="google"]',
  ], 'Continue with Google button', 8000);

  if (!googleClicked) {
    await shot(page, '02-google-btn-not-found');
    console.log('\n  ❌ Could not find the Google login button.');
    console.log('  Check screenshot above — the login form may have changed.');
    await browser.close();
    process.exit(1);
  }

  await page.waitForTimeout(2500);
  await shot(page, '02-after-google-click');
  console.log('  URL after click:', page.url());

  // ── Step 3: Google account picker ────────────────────────────────────────────
  console.log('\nStep 3: Google account picker');
  await page.waitForTimeout(2000);

  // Google may show:
  //   a) Account picker with existing signed-in accounts (most likely)
  //   b) Email input field (no accounts in browser)
  const currentUrl = page.url();
  console.log('  URL:', currentUrl);

  if (currentUrl.includes('accounts.google.com')) {
    await shot(page, '03-google-page');

    // Try to find and click the algolia account in the picker
    const accountSels = [
      `[data-email="${LOGIN_EMAIL}"]`,
      `[data-identifier="${LOGIN_EMAIL}"]`,
      `div:has-text("${LOGIN_EMAIL}")`,
      `li:has-text("${LOGIN_EMAIL}")`,
    ];

    let accountClicked = false;
    for (const sel of accountSels) {
      try {
        await page.waitForSelector(sel, { timeout: 4000 });
        await page.click(sel);
        console.log(`  ✓ Selected account: ${LOGIN_EMAIL}`);
        accountClicked = true;
        break;
      } catch { /* try next */ }
    }

    if (!accountClicked) {
      // No matching account found — try "Use another account" then fill email
      console.log('  Account not in picker — trying "Use another account"');
      const otherAcct = await clickFirst(page, [
        'div:has-text("Use another account")',
        '[data-identifier=""]',
        'li:last-child',   // "Use another account" is usually last
      ], 'Use another account', 4000);

      if (otherAcct) {
        await page.waitForTimeout(1500);
        // Now we should have an email input
        try {
          await page.waitForSelector('input[type="email"]', { timeout: 5000 });
          await page.fill('input[type="email"]', LOGIN_EMAIL);
          await page.keyboard.press('Enter');
          console.log(`  ✓ Filled email: ${LOGIN_EMAIL}`);
        } catch {
          console.log('  ⚠️  Email field not found after "Use another account"');
          await shot(page, '03-email-field-missing');
        }
      } else {
        // Last resort: just try filling an email field directly
        try {
          await page.waitForSelector('input[type="email"]', { timeout: 5000 });
          await page.fill('input[type="email"]', LOGIN_EMAIL);
          await page.keyboard.press('Enter');
          console.log(`  ✓ Filled email directly: ${LOGIN_EMAIL}`);
        } catch {
          console.log('  ⚠️  Could not interact with Google login page');
          await shot(page, '03-google-stuck');
          console.log('\n  Manual action needed — please select your account in the browser window.');
          console.log('  Waiting up to 60 seconds...');
        }
      }
    }
  } else {
    console.log('  Not on Google — may have been redirected elsewhere');
    await shot(page, '03-unexpected-redirect');
  }

  // ── Step 4: Wait for redirect back to SimilarWeb ─────────────────────────────
  console.log('\nStep 4: Waiting for redirect back to SimilarWeb...');
  const TIMEOUT = 180000; // 3 min — enough for device verification
  const POLL    = 2000;
  const deadline = Date.now() + TIMEOUT;
  let landed = false;
  let verificationPrompted = false;

  while (Date.now() < deadline) {
    await page.waitForTimeout(POLL);
    const url = page.url();

    // Device verification step — SimilarWeb sends a code to your email/phone
    if (url.includes('device-verification') && !verificationPrompted) {
      console.log('\n  ⚠️  SimilarWeb device verification required (new browser/device)');
      console.log('  → Check your email or phone for a verification code from SimilarWeb');
      console.log('  → Enter the code in the browser window');
      console.log('  → Waiting up to 3 minutes for you to complete it...\n');
      await shot(page, '04-device-verification');
      verificationPrompted = true;
    }

    process.stdout.write('.');

    const onSW = url.startsWith('https://www.similarweb.com') ||
                 url.startsWith('https://pro.similarweb.com') ||
                 url.startsWith('https://secure.similarweb.com');

    if (onSW && !url.includes('/login') && !url.includes('device-verification')) {
      landed = true;
      break;
    }
  }
  console.log('');

  if (!landed) {
    await shot(page, '04-timeout');
    console.log(`\n  ❌ Did not land back on SimilarWeb within ${TIMEOUT/1000}s`);
    console.log('  Current URL:', page.url());
    await browser.close();
    process.exit(1);
  }

  console.log('  ✓ Back on SimilarWeb:', page.url());
  await page.waitForTimeout(2000);
  await shot(page, '04-sw-logged-in');

  // ── Step 5: Save session ──────────────────────────────────────────────────────
  console.log('\nStep 5: Saving session');
  const state = await context.storageState();
  fs.writeFileSync(SESSION_FILE, JSON.stringify(state, null, 2));
  console.log('  ✓ Session saved →', SESSION_FILE);
  const cookieCount = state.cookies?.length ?? 0;
  console.log(`  Cookies captured: ${cookieCount}`);

  // ── Step 6: Quick session smoke test ─────────────────────────────────────────
  console.log(`\nStep 6: Smoke test — navigating to ${TEST_DOMAIN} research page`);
  const testUrl = `https://www.similarweb.com/website/${TEST_DOMAIN}/overview/`;
  await page.goto(testUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(3000);
  await shot(page, '05-research-page');

  const finalUrl = page.url();
  const onResearch = finalUrl.includes('/website/') || finalUrl.includes('/overview');
  const onLogin    = finalUrl.includes('/login');

  console.log('  URL:', finalUrl);
  if (onLogin) {
    console.log('\n  ❌ Got redirected to login — session may not have saved properly');
    await browser.close();
    process.exit(1);
  } else if (onResearch) {
    console.log(`  ✓ Research page loaded — session is working`);
  } else {
    console.log('  ⚠️  Unexpected URL — check screenshot');
  }

  console.log('\n✅ Login test complete.');
  console.log('   Session file:', SESSION_FILE);
  console.log('   If the research page screenshot shows real data, the session is good.');
  console.log('   Copy session file to: auth/similarweb-session.json to use in production.\n');

  await browser.close();
  process.exit(0);
})();
