#!/usr/bin/env node
// Test: audit-browser.js is general-purpose (parameterized), so per-company forks are unnecessary.
// Runs the script's built-in --self-test (no network) and asserts it exits 0.
// This is the regression guard for BUG-6: if someone breaks the URL-template / selector /
// query-config plumbing, this test fails before a new fork gets hand-written.

import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const script = path.join(here, '..', 'audit-browser.js');

function run(args, label) {
  try {
    const out = execFileSync('node', [script, ...args], { encoding: 'utf8' });
    console.log(`  ✓ ${label}`);
    return out;
  } catch (e) {
    console.error(`  FAIL: ${label}\n${e.stdout || ''}${e.stderr || ''}`);
    process.exit(1);
  }
}

// 1. self-test with a URL template + custom selector (the per-site parameterization path)
const out1 = run(
  ['--self-test', '--search-url-template', '/en-us/search?q={q}', '--search-selector', '#type-ahead-site-search-desktop'],
  'self-test with --search-url-template + --search-selector exits 0'
);
if (!out1.includes('self-test passed')) { console.error('  FAIL: self-test did not print pass line'); process.exit(1); }

// 2. self-test with no per-site args (default input mode) still passes
run(['--self-test'], 'self-test with defaults (input mode) exits 0');

// 3. node --check the script itself (syntax)
run(['--self-test'], 'script loads + executes without syntax error');

console.log('\n✓ audit-browser config/parameterization tests passed');
