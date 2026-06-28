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
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    window.chrome = { runtime: {} };
  });

  // Track network
  const apiRequests = [];
  context.on('request', req => {
    const url = req.url();
    if (!url.endsWith('.js') && !url.endsWith('.css') && !url.endsWith('.png') && !url.endsWith('.jpg') && !url.endsWith('.woff') && !url.endsWith('.ico')) {
      apiRequests.push({ url, method: req.method() });
    }
  });
  context.on('response', async resp => {
    const url = resp.url();
    if ((url.includes('search') || url.includes('api') || url.includes('query')) && !url.endsWith('.js')) {
      const ct = resp.headers()['content-type'] || '';
      if (ct.includes('json') || ct.includes('text')) {
        try {
          const text = await resp.text();
          console.log(`API RESPONSE: ${resp.status()} ${url.substring(0,100)}`);
          console.log(`  Content preview: ${text.substring(0, 200)}`);
        } catch(e) {}
      }
    }
  });

  const page = await context.newPage();

  // Load homepage - capture SSR HTML immediately before JS runs
  console.log('=== Loading JBL homepage (capturing SSR HTML) ===');
  const response = await page.goto('https://www.jbl.com/', { 
    waitUntil: 'domcontentloaded', 
    timeout: 45000 
  });
  
  // Get the raw HTML immediately (SSR content)
  const rawHTML = await page.content();
  
  // Write raw HTML for analysis
  fs.writeFileSync(`${AUDIT_DIR}/JBL/research/jbl-ssr-homepage.html`, rawHTML);
  console.log(`Saved SSR HTML: ${rawHTML.length} chars`);
  
  // Parse it for useful signals
  const htmlAnalysis = await page.evaluate(() => {
    // Look for search-related scripts
    const scripts = [...document.querySelectorAll('script[src]')].map(s => s.src);
    const inlineScripts = [...document.querySelectorAll('script:not([src])')].map(s => s.textContent.substring(0,100));
    
    // Check meta tags
    const metas = [...document.querySelectorAll('meta')].map(m => ({
      name: m.name || m.getAttribute('property'),
      content: m.content?.substring(0, 80)
    })).filter(m => m.name);
    
    // Check for Nuxt/Vue markers
    const nuxtMarkers = document.querySelector('#__nuxt, #__vue, [data-server-rendered]');
    const nuxtData = document.querySelector('#__NUXT_DATA__') || document.querySelector('script#__NUXT__');
    
    // Find search-related data
    const bodyHTML = document.body.innerHTML;
    const searchFormMatch = bodyHTML.match(/<form[^>]*search[^>]*>/i);
    const searchInputMatch = bodyHTML.match(/<input[^>]*search[^>]*>/i);
    
    return {
      scriptCount: scripts.length,
      searchScripts: scripts.filter(s => s.toLowerCase().includes('search')),
      hasNuxt: !!nuxtMarkers,
      hasNuxtData: !!nuxtData,
      bodyLength: document.body.innerHTML.length,
      searchFormFound: !!searchFormMatch,
      searchInputFound: !!searchInputMatch,
      metaTags: metas.slice(0, 10),
      scriptPreviews: scripts.slice(0, 15),
    };
  });
  
  console.log('HTML Analysis:', JSON.stringify(htmlAnalysis, null, 2));
  
  // Search for search-vendor signatures in the raw HTML
  const vendorSignatures = {
    algolia: /algolia/i.test(rawHTML),
    coveo: /coveo/i.test(rawHTML),
    bloomreach: /bloomreach|brsrvr/i.test(rawHTML),
    klevu: /klevu/i.test(rawHTML),
    constructor: /constructor\.io|cnstrc/i.test(rawHTML),
    elasticsearch: /elasticsearch/i.test(rawHTML),
    searchspring: /searchspring/i.test(rawHTML),
    bazaarvoice: /bazaarvoice/i.test(rawHTML),
    datadome: /datadome|captcha-delivery/i.test(rawHTML),
    akamai: /akamai/i.test(rawHTML),
    yottaa: /yottaa/i.test(rawHTML),
    insider: /insider/i.test(rawHTML),
  };
  console.log('Vendor signatures in HTML:', JSON.stringify(vendorSignatures, null, 2));
  
  // Extract any search-related URLs from scripts
  const searchURLs = rawHTML.match(/https?:\/\/[^"']+(?:search|query|suggest|autocomplete)[^"']*/gi) || [];
  console.log('Search-related URLs in HTML:', [...new Set(searchURLs)].slice(0, 20));
  
  // Look for search endpoint patterns
  const apiPatterns = rawHTML.match(/\/api\/[^"'\s]+/g) || [];
  console.log('API patterns found:', [...new Set(apiPatterns)].slice(0, 15));
  
  // Wait and take screenshots of various pages
  await sleep(4000);
  
  // Try to capture what we can from homepage
  const ss01 = `${SCREENSHOTS_DIR}/01-homepage-ssr.png`;
  await page.screenshot({ path: ss01, fullPage: false });
  console.log(`Homepage SSR screenshot: ${fs.statSync(ss01).size} bytes`);
  
  // Navigate to PDP for recommendations check
  console.log('\n=== Attempting PDP navigation ===');
  try {
    await page.goto('https://www.jbl.com/FLIP6.html', { waitUntil: 'domcontentloaded', timeout: 30000 });
    const pdpTitle = await page.title();
    console.log(`PDP title: ${pdpTitle}`);
    await sleep(4000);
    const ssPDP = `${SCREENSHOTS_DIR}/18-recommendations-pdp-v2.png`;
    await page.screenshot({ path: ssPDP });
    console.log(`PDP screenshot: ${fs.statSync(ssPDP).size} bytes`);
    
    const pdpHTML = await page.content();
    const pdpVendors = {
      algolia: /algolia/i.test(pdpHTML),
      bazaarvoice: /bazaarvoice/i.test(pdpHTML),
      insider: /insider/i.test(pdpHTML),
      searchURLs: (pdpHTML.match(/\/api\/[^"'\s]+/g) || []).slice(0,10)
    };
    console.log('PDP vendors:', JSON.stringify(pdpVendors, null, 2));
  } catch(e) {
    console.log('PDP error:', e.message);
  }
  
  await browser.close();
  
  console.log('\n=== Network API requests captured ===');
  apiRequests.filter(r => !r.url.includes('.js') && !r.url.includes('.css') && !r.url.includes('google-analytics')).slice(0, 20).forEach(r => console.log(`${r.method} ${r.url.substring(0, 130)}`));
}

main().catch(console.error);
