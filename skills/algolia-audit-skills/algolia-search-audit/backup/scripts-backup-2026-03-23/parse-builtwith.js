#!/usr/bin/env node
/**
 * parse-builtwith.js — Filter BuiltWith API response
 * Extracts only audit-relevant categories from the large (~190KB) BuiltWith response.
 * Prevents context window destruction from raw BuiltWith output.
 *
 * Usage: node parse-builtwith.js [input-file] OR pipe stdin
 * Output: JSON with only relevant technology categories
 */

const RELEVANT_CATEGORIES = [
  'search', 'ecommerce', 'analytics', 'personalization', 'recommendations',
  'cdn', 'tag-management', 'a-b-testing', 'advertising', 'widgets', 'cms',
  'payment', 'review', 'chat', 'marketing-automation'
];

const SEARCH_VENDORS = [
  'algolia', 'coveo', 'bloomreach', 'constructor', 'searchspring', 'klevu',
  'lucidworks', 'elasticsearch', 'solr', 'endeca', 'hawksearch', 'fastly',
  'searchanise', 'doofinder', 'attraqt', 'nosto'
];

function parseBuiltWith(rawData) {
  let parsed;
  try {
    parsed = typeof rawData === 'string' ? JSON.parse(rawData) : rawData;
  } catch (e) {
    process.stderr.write(`parse-builtwith.js: invalid JSON input — ${e.message}\n`);
    process.exit(1);
  }

  // Handle both array and object responses
  const results = Array.isArray(parsed) ? parsed : [parsed];
  const firstResult = results[0];

  if (!firstResult) {
    process.stderr.write('parse-builtwith.js: empty response\n');
    process.exit(1);
  }

  // Extract text content if wrapped
  let dataStr = typeof firstResult === 'string' ? firstResult :
                (firstResult.text || JSON.stringify(firstResult));
  let data;
  try {
    data = typeof dataStr === 'string' ? JSON.parse(dataStr) : dataStr;
  } catch (e) {
    data = firstResult;
  }

  const output = {
    domain: '',
    search_vendors: [],
    ecommerce_platform: [],
    analytics: [],
    cdn_waf: [],
    personalization: [],
    recommendations: [],
    tag_management: [],
    reviews: [],
    removed_technologies: [],
    algolia_detected: false,
    competitor_detected: false,
    all_relevant: []
  };

  // Navigate to technologies array
  const techArray = data.Results?.[0]?.Result?.Paths?.[0]?.Technologies ||
                    data.Technologies ||
                    data.Paths?.[0]?.Technologies ||
                    [];

  for (const tech of techArray) {
    const name = (tech.Name || '').toLowerCase();
    const tag = (tech.Tag || '').toLowerCase();
    const isRemoved = tech.IsPremium === false || tech.FirstDetected && tech.LastDetected &&
                      tech.LastDetected < tech.FirstDetected;

    // Check if relevant category
    const isRelevant = RELEVANT_CATEGORIES.some(cat => tag.includes(cat));
    if (!isRelevant && !SEARCH_VENDORS.some(v => name.includes(v))) continue;

    const entry = {
      name: tech.Name,
      tag: tech.Tag,
      link: tech.Link || '',
      first_detected: tech.FirstDetected,
      last_detected: tech.LastDetected
    };

    if (isRemoved) {
      output.removed_technologies.push(entry);
      continue;
    }

    output.all_relevant.push(entry);

    // Categorize
    if (SEARCH_VENDORS.some(v => name.includes(v))) {
      output.search_vendors.push(entry);
      if (name.includes('algolia')) output.algolia_detected = true;
      if (['coveo','bloomreach','constructor','searchspring','klevu','lucidworks']
          .some(v => name.includes(v))) output.competitor_detected = true;
    } else if (tag.includes('ecommerce') || name.includes('commerce') || name.includes('shopify') || name.includes('magento')) {
      output.ecommerce_platform.push(entry);
    } else if (tag.includes('analytics') || name.includes('analytics') || name.includes('omniture') || name.includes('dynatrace')) {
      output.analytics.push(entry);
    } else if (tag.includes('cdn') || name.includes('akamai') || name.includes('cloudflare') || name.includes('fastly')) {
      output.cdn_waf.push(entry);
    } else if (tag.includes('personalization') || name.includes('personalization')) {
      output.personalization.push(entry);
    } else if (tag.includes('review') || name.includes('bazaarvoice') || name.includes('powerreviews')) {
      output.reviews.push(entry);
    } else if (tag.includes('tag') || name.includes('tealium') || name.includes('adobe dtm') || name.includes('google tag')) {
      output.tag_management.push(entry);
    }
  }

  // Extract domain
  output.domain = data.Results?.[0]?.Result?.Attribute || data.Domain || '';

  return output;
}

// Main execution
let inputData = '';

if (process.argv[2]) {
  const fs = require('fs');
  try {
    inputData = fs.readFileSync(process.argv[2], 'utf8');
  } catch (e) {
    process.stderr.write(`parse-builtwith.js: cannot read file ${process.argv[2]} — ${e.message}\n`);
    process.exit(1);
  }
} else {
  // Read from stdin
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => { inputData += chunk; });
  process.stdin.on('end', () => {
    const result = parseBuiltWith(inputData);
    process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  });
  return;
}

const result = parseBuiltWith(inputData);
process.stdout.write(JSON.stringify(result, null, 2) + '\n');
