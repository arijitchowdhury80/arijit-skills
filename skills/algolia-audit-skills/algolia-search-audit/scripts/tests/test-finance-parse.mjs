// Test: financial value parser for the Financials chart in index-template.html
// Bug: pv() strips all non-digits and parseFloats the rest, so it is BOTH
//   - unit-blind ("$910M" -> 910 -> rendered "$910.0B", 1000x too big), and
//   - range-blind ("~$9–10B" -> "910" -> 910, concatenated).
// The chart axis/table/tooltips/YoY are all in $B, but the parser never
// normalizes its input to $B. This test pins the correct behavior so the
// regression can never silently return.
//
// Run: node scripts/tests/test-finance-parse.mjs

// ── OLD (buggy) parser, kept here to document the failure mode ──────────────
function pvOld(s) {
  if (!s || s === '—' || s === '—') return null;
  const str = String(s);
  const neg = str.includes('−') || str.startsWith('-');
  const n = parseFloat(str.replace(/[^0-9.]/g, ''));
  if (isNaN(n)) return null;
  return neg ? -n : n;
}

// ── NEW parser: normalizes any monetary string to a number in $B ────────────
// MUST be kept byte-identical to pvB() in templates/index-template.html.
function pvB(s) {
  if (s == null) return null;
  const str = String(s).trim();
  if (!str || str === '—' || str === '—') return null;
  // Negative only if a minus sign LEADS the string (a hyphen *between* two
  // numbers is a range separator, not a sign).
  const negative = /^\s*[-−]/.test(str);
  // Pull numeric tokens (allow thousands commas + decimals).
  const nums = (str.match(/\d[\d,]*\.?\d*/g) || []).map(x => parseFloat(x.replace(/,/g, '')));
  if (!nums.length) return null;
  // Range ("9–10", "5-7", "9 to 10") -> midpoint.
  const isRange = nums.length >= 2 && /\d\s*(?:[-–—]|to)\s*\d/i.test(str);
  const val = isRange ? (nums[0] + nums[1]) / 2 : nums[0];
  // Unit suffix that follows a digit -> multiplier to convert to $B.
  const um = str.match(/\d\s*([tTbBmMkK])/);
  const u = um ? um[1].toLowerCase() : '';
  let mult;
  if (u === 't') mult = 1000;          // trillions -> B
  else if (u === 'b') mult = 1;        // billions
  else if (u === 'm') mult = 0.001;    // millions -> B
  else if (u === 'k') mult = 1e-6;     // thousands -> B
  else mult = val >= 1e6 ? 1e-9 : 1;   // raw $ -> B, else assume already-B
  const out = val * mult;
  return negative ? -out : out;
}

const cases = [
  // [input, expected $B]
  ['~$9.5B (est.)', 9.5],
  ['~$9.8B (est.)', 9.8],
  ['~$9–10B (est.)', 9.5],   // range -> midpoint  (was 910, the reported bug)
  ['$910M', 0.91],           // millions          (was 910 -> $910.0B)
  ['~$750M [ESTIMATE]', 0.75],
  ['$125M (est.)', 0.125],
  ['$766M [ESTIMATE]', 0.766],
  ['$1.2T', 1200],           // trillions         (was 1.2 -> $1.2B)
  ['$9,100,000,000', 9.1],   // raw dollars
  ['$5-7B', 6],              // range -> midpoint
  ['~$1.26B (ESTIMATE)', 1.26],
  ['-$1.2B', -1.2],
  ['−$2B', -2],
  ['—', null],
  [null, null],
  ['', null],
];

const EPS = 1e-9;
let failed = 0;
console.log('input'.padEnd(24), 'old'.padStart(14), 'new'.padStart(12), 'expected'.padStart(12), '  ok');
for (const [inp, exp] of cases) {
  const got = pvB(inp);
  const old = pvOld(inp);
  const ok = (exp === null) ? (got === null) : (got !== null && Math.abs(got - exp) < EPS);
  if (!ok) failed++;
  console.log(
    JSON.stringify(inp).padEnd(24),
    String(old).padStart(14),
    String(got).padStart(12),
    String(exp).padStart(12),
    ok ? '  ✓' : '  ✗ FAIL'
  );
}
console.log('');
if (failed) { console.error(`FAILED ${failed}/${cases.length}`); process.exit(1); }
console.log(`PASSED ${cases.length}/${cases.length}`);
