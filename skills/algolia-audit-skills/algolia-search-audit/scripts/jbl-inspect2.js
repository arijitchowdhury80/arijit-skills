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
    javaScriptEnabled: true,
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    window.chrome = { runtime: {} };
  });

  const allRequests = [];
  context.on('request', req => allRequests.push(req.url()));
  context.on('response', async resp => {
    const url = resp.url();
    if (url.includes('search') && !url.endsWith('.js') && !url.endsWith('.css') && !url.endsWith('.png')) {
      console.log(`Response: ${resp.status()} ${url.substring(0,120)}`);
    }
  });

  const page = await context.newPage();

  // Wait for Vue hydration
  console.log('Loading homepage...');
  await page.goto('https://www.jbl.com/', { waitUntil: 'domcontentloaded', timeout: 45000 });
  
  // Wait for Vue to hydrate
  await sleep(5000);

  // Inspect all buttons in DOM
  const buttonInfo = await page.evaluate(() => {
    return [...document.querySelectorAll('button')].map(b => ({
      text: b.textContent.trim().substring(0,30),
      ariaLabel: b.getAttribute('aria-label'),
      className: b.className.substring(0,60),
      id: b.id,
      visible: b.offsetParent !== null && window.getComputedStyle(b).display !== 'none'
    })).filter(b => b.visible);
  });
  
  console.log('All visible buttons:', JSON.stringify(buttonInfo.slice(0,15), null, 2));

  // Try clicking search icon using evaluate
  const searchButtonFound = await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    for (const btn of buttons) {
      const label = btn.getAttribute('aria-label') || '';
      const cls = btn.className || '';
      if (label.toLowerCase().includes('search') || cls.toLowerCase().includes('search-icon')) {
        btn.click();
        return { clicked: true, label, cls };
      }
    }
    return { clicked: false };
  });
  console.log('Search button click result:', JSON.stringify(searchButtonFound));
  await sleep(2000);

  // Check search input visibility
  const inputState = await page.evaluate(() => {
    const inputs = document.querySelectorAll('input');
    return [...inputs].map(inp => ({
      name: inp.name,
      type: inp.type,
      placeholder: inp.placeholder,
      visible: inp.offsetParent !== null,
      display: window.getComputedStyle(inp).display,
      visibility: window.getComputedStyle(inp).visibility,
      value: inp.value
    }));
  });
  console.log('Input fields:', JSON.stringify(inputState, null, 2));

  // Take screenshot after click
  const ss = `${SCREENSHOTS_DIR}/02-empty-state-v2.png`;
  await page.screenshot({ path: ss });
  console.log(`Empty state after search click: ${fs.statSync(ss).size} bytes`);

  // Now type into any visible input
  const visibleInput = inputState.find(i => i.visible && (i.name === 'q' || i.type === 'search' || i.placeholder?.toLowerCase().includes('search')));
  console.log('Visible input to type into:', visibleInput);

  if (visibleInput) {
    const selector = visibleInput.name ? `input[name="${visibleInput.name}"]` : `input[type="${visibleInput.type}"]`;
    const inp = await page.$(selector);
    if (inp) {
      await inp.click({ force: true });
      await sleep(300);
      await page.keyboard.type('headphones', { delay: 100 });
      await sleep(2500);
      
      const saytSS = `${SCREENSHOTS_DIR}/03-sayt-headphones-v2.png`;
      await page.screenshot({ path: saytSS });
      console.log(`SAYT screenshot: ${fs.statSync(saytSS).size} bytes`);
      
      const saytCheck = await page.evaluate(() => {
        const body = document.body.innerText.substring(0, 500);
        const inputs = [...document.querySelectorAll('input')].map(i => i.value);
        return { bodyPreview: body, inputValues: inputs };
      });
      console.log('After typing:', JSON.stringify(saytCheck, null, 2));
    }
  }

  await browser.close();

  console.log('\n=== KEY NETWORK REQUESTS ===');
  const interesting = allRequests.filter(u => u.includes('api') || u.includes('query') || u.includes('search') || u.includes('rapid') || u.includes('yottaa'));
  interesting.slice(0, 20).forEach(u => console.log(u.substring(0,150)));
}

main().catch(console.error);
