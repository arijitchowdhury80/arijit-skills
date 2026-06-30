// tech-fingerprint-db.js — Open-DB fallback matcher for detectTechStack().
//
// Loads a Wappalyzer-fork "webappanalyzer" schema from
// detect-search/fingerprints/technologies.json if present, then matches rules
// against the captured browser signals (request URLs, response headers, HTML
// sources, cookies).  If the JSON file is absent, returns [] — no error thrown.
//
// Schema per technology (subset of webappanalyzer format):
//   { "headers": { "header-name": "regexp" },
//     "cookies": { "cookie-name": "regexp" },
//     "html":    ["regexp", ...],
//     "url":     ["regexp", ...],
//     "scriptSrc": ["regexp", ...],
//     "cats":    ["CategoryName"],
//     "website": "https://..." }
//
// capturedSignals shape (from detectTechStack):
//   { requestUrls: string[], responseHeaders: { url: { header: val } },
//     htmlSources: string[], cookieNames: string[] }
//
// Returns an array of { technology, category, evidence } objects.

'use strict';

const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, 'fingerprints', 'technologies.json');

// Load and parse the fingerprint DB once per process (lazy, cached).
let _db = null;
let _dbLoaded = false;

function loadDb() {
  if (_dbLoaded) return _db;
  _dbLoaded = true;
  if (!fs.existsSync(DB_PATH)) {
    return null;
  }
  try {
    const raw = fs.readFileSync(DB_PATH, 'utf8');
    _db = JSON.parse(raw);
  } catch (e) {
    process.stderr.write(`[tech-fingerprint-db] failed to parse ${DB_PATH}: ${e.message}\n`);
    _db = null;
  }
  return _db;
}

// Compile a webappanalyzer pattern string into a RegExp.
// Wappalyzer uses "pattern\\;version:\\1" syntax — we strip the meta-hints.
function compilePattern(str) {
  if (!str || typeof str !== 'string') return null;
  const raw = str.split('\\;')[0]; // strip \\;version:, \\;confidence: etc.
  try {
    return new RegExp(raw, 'i');
  } catch {
    return null;
  }
}

/**
 * Match the open-DB fingerprints against captured browser signals.
 *
 * @param {object} capturedSignals
 *   { requestUrls, responseHeaders, htmlSources, cookieNames }
 * @returns {{ technology: string, category: string, evidence: string }[]}
 */
function matchOpenDb(capturedSignals) {
  const db = loadDb();
  if (!db) return [];

  const { requestUrls = [], responseHeaders = {}, htmlSources = [], cookieNames = [] } = capturedSignals;

  // Flatten all response header objects into [{ header, value }] pairs for fast scanning
  const allResponseHeaders = [];
  for (const headers of Object.values(responseHeaders)) {
    for (const [k, v] of Object.entries(headers)) {
      allResponseHeaders.push({ header: k.toLowerCase(), value: v });
    }
  }

  const combinedHtml = htmlSources.join(' ');
  const results = [];

  for (const [techName, techDef] of Object.entries(db)) {
    if (!techDef || typeof techDef !== 'object') continue;

    const cats = Array.isArray(techDef.cats) ? techDef.cats : ['Other'];
    const category = cats[0] || 'Other';
    let evidence = null;

    // 1. URL patterns
    if (!evidence && techDef.url) {
      const patterns = Array.isArray(techDef.url) ? techDef.url : [techDef.url];
      for (const pat of patterns) {
        const re = compilePattern(pat);
        if (!re) continue;
        for (const url of requestUrls) {
          if (re.test(url)) {
            evidence = `Open-DB URL match: ${url.substring(0, 150)} [${techName}]`;
            break;
          }
        }
        if (evidence) break;
      }
    }

    // 2. scriptSrc patterns (subset of URL patterns targeting JS files)
    if (!evidence && techDef.scriptSrc) {
      const patterns = Array.isArray(techDef.scriptSrc) ? techDef.scriptSrc : [techDef.scriptSrc];
      for (const pat of patterns) {
        const re = compilePattern(pat);
        if (!re) continue;
        for (const url of requestUrls) {
          if (/\.js(\?|$)/i.test(url) && re.test(url)) {
            evidence = `Open-DB scriptSrc match: ${url.substring(0, 150)} [${techName}]`;
            break;
          }
        }
        if (evidence) break;
      }
    }

    // 3. Response header patterns
    if (!evidence && techDef.headers && typeof techDef.headers === 'object') {
      for (const [headerName, patternStr] of Object.entries(techDef.headers)) {
        const re = compilePattern(patternStr || '');
        const lowerHeader = headerName.toLowerCase();
        for (const { header, value } of allResponseHeaders) {
          if (header === lowerHeader) {
            if (!re || re.test(value) || patternStr === '') {
              evidence = `Open-DB response header ${headerName}: "${value.substring(0, 60)}" [${techName}]`;
              break;
            }
          }
        }
        if (evidence) break;
      }
    }

    // 4. Cookie patterns
    if (!evidence && techDef.cookies && typeof techDef.cookies === 'object') {
      for (const [cookieName, patternStr] of Object.entries(techDef.cookies)) {
        const re = compilePattern(patternStr || '');
        const lowerCookie = cookieName.toLowerCase();
        for (const name of cookieNames) {
          if (name.toLowerCase() === lowerCookie || (re && re.test(name))) {
            evidence = `Open-DB cookie match: ${name} [${techName}]`;
            break;
          }
        }
        if (evidence) break;
      }
    }

    // 5. HTML patterns
    if (!evidence && techDef.html) {
      const patterns = Array.isArray(techDef.html) ? techDef.html : [techDef.html];
      for (const pat of patterns) {
        const re = compilePattern(pat);
        if (re && re.test(combinedHtml)) {
          evidence = `Open-DB HTML match: ${techName}`;
          break;
        }
      }
    }

    if (evidence) {
      results.push({ technology: techName, category, evidence });
    }
  }

  return results;
}

module.exports = { matchOpenDb };
