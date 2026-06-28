const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1440, height: 900 });
  
  // Try search results page directly - lighter than homepage
  console.log('Navigating to BA search results page...');
  await page.goto('https://www.britishairways.com/travel/searchba/public/en_gb?q=baggage', 
    { waitUntil: 'commit', timeout: 30000 });
  await page.waitForTimeout(5000);
  
  await page.screenshot({ path: '/tmp/ba-search-page.png' });
  console.log('Screenshot: /tmp/ba-search-page.png');
  
  const inputs = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('input')).map(el => ({
      id: el.id,
      name: el.name,
      type: el.type,
      placeholder: el.placeholder,
      className: el.className.substring(0, 80),
      ariaLabel: el.getAttribute('aria-label') || '',
      value: el.value,
      visible: el.getBoundingClientRect().width > 0
    }));
  });
  
  console.log('\n=== ALL INPUTS ===');
  inputs.forEach(i => console.log(JSON.stringify(i)));
  
  await browser.close();
})();
