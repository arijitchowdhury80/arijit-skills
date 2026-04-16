#!/usr/bin/env node
/**
 * Algolia Audit — SPA Runtime Test
 * Catches JS runtime errors in section functions BEFORE pushing to GitHub.
 *
 * Usage: node test-spa-runtime.js <slug>
 * Example: node test-spa-runtime.js brooks-running
 *
 * Exits 0 if all sections render without error.
 * Exits 1 if any section throws.
 */

const fs = require('fs');
const vm = require('vm');
const path = require('path');

const slug = process.argv[2];
if (!slug) {
  console.error('Usage: node test-spa-runtime.js <slug>');
  process.exit(1);
}

// Support both published path and local deliverables path
const auditDir = process.env.ALGOLIA_AUDIT_DIR;
let htmlPath;
if (process.argv[3]) {
  // Explicit path provided as third argument
  htmlPath = process.argv[3];
} else if (auditDir) {
  // Try local deliverables first, then fall back to hub
  const localPath = path.join(auditDir, slug.charAt(0).toUpperCase() + slug.slice(1), 'deliverables', slug, 'index.html');
  const hubPath = path.join(process.env.HOME, 'algolia-arian-v2', slug, 'index.html');
  const fs2 = require('fs');
  htmlPath = fs2.existsSync(localPath) ? localPath : hubPath;
} else {
  htmlPath = path.join(process.env.HOME, 'algolia-arian-v2', slug, 'index.html');
}
if (!fs.existsSync(htmlPath)) {
  console.error(`File not found: ${htmlPath}`);
  process.exit(1);
}

const html = fs.readFileSync(htmlPath, 'utf8');

// Extract data block
const dataMatch = html.match(/window\.AUDIT_DATA = (\{[\s\S]*?\});<\/script>/);
if (!dataMatch) {
  console.error('❌ window.AUDIT_DATA not found in HTML');
  process.exit(1);
}

let D;
try {
  D = JSON.parse(dataMatch[1]);
} catch(e) {
  console.error('❌ AUDIT_DATA JSON parse error:', e.message);
  process.exit(1);
}

// Extract main script
const scripts = html.match(/<script>([\s\S]*?)<\/script>/g);
if (!scripts || scripts.length < 2) {
  console.error('❌ Could not find main script block');
  process.exit(1);
}
const main = scripts[1].replace(/<\/?script>/g,'').replace(/'use strict';/,'');

// Minimal browser environment mock
const ctx = vm.createContext({
  window: {
    AUDIT_DATA: D, scrollTo:()=>{}, addEventListener:()=>{}, print:()=>{},
    innerWidth:1200, innerHeight:800
  },
  document: {
    title: '',
    getElementById: () => ({
      innerHTML:'', style:{},
      classList:{toggle:()=>{},add:()=>{},remove:()=>{},contains:()=>false},
      dataset:{}, querySelectorAll:()=>[], closest:()=>null,
      getAttribute:()=>null, setAttribute:()=>{}, addEventListener:()=>{}
    }),
    querySelector: () => null,
    querySelectorAll: () => [],
    addEventListener: () => {},
    createElement: () => ({style:{},classList:{add:()=>{},remove:()=>{}},appendChild:()=>{},setAttribute:()=>{}}),
    createTreeWalker: () => ({nextNode:()=>null}),
  },
  sessionStorage: {getItem:()=>null, setItem:()=>{}},
  requestAnimationFrame: ()=>{},
  navigator: {userAgent:'node-test'},
  location: {hash:'', hostname:'localhost'},
  history: {pushState:()=>{}},
  MutationObserver: class{observe(){}disconnect(){}},
  IntersectionObserver: class{observe(){}disconnect(){}},
  ResizeObserver: class{observe(){}disconnect(){}},
  console: {log:()=>{}, warn:()=>{}, error:()=>{}}
});

// Load the script
try {
  vm.runInContext(main, ctx);
} catch(e) {
  console.error('❌ Script load error:', e.message);
  console.error(e.stack?.split('\n').slice(0,4).join('\n'));
  process.exit(1);
}

// Section functions to test
const sections = [
  'sectionExecSummary', 'sectionCompanySnapshot', 'sectionFinancials',
  'sectionTechStack', 'sectionTraffic', 'sectionHiring', 'sectionSignals',
  'sectionPartnerIntel',
  'sectionScoreHeatmap', 'sectionBusinessCaseHook', 'sectionCompetitiveSynthesis',
  'sectionRevenueAtRisk', 'sectionCaseStudies', 'sectionWhyNow',
  'sectionStrategicAngles', 'sectionPreCallBrief', 'sectionBuyingCommittee',
  'sectionBattleCard', 'sectionDiscoveryObjections', 'sectionOutreachPlan'
];

let passed = 0, failed = 0;
sections.forEach(fn => {
  try {
    vm.runInContext(`${fn}(window.AUDIT_DATA)`, ctx);
    console.log(`  ✓ ${fn}`);
    passed++;
  } catch(e) {
    console.error(`  ❌ ${fn}: ${e.message.slice(0,120)}`);
    if (e.stack) console.error(`     ${e.stack.split('\n')[1]?.trim()}`);
    failed++;
  }
});

console.log(`\n${passed}/${sections.length} sections passed`);
if (failed > 0) {
  console.error(`\n❌ ${failed} section(s) have runtime errors — fix before pushing`);
  process.exit(1);
}
console.log(`✅ All sections render without runtime errors`);
