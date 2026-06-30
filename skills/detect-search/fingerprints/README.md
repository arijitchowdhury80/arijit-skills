# fingerprints/technologies.json — Open-DB Fingerprint Source

## What this file is

A JSON file in the **webappanalyzer schema** (community fork of the original Wappalyzer database).
`tech-fingerprint-db.js` loads this file at runtime and matches its rules against the browser
signals captured by `detectTechStack()`. If this file is absent, the open-DB matcher silently
returns [] — no code change required.

## Seeded sample (5 technologies)

The file ships with 5 illustrative entries (jQuery, WordPress, Lodash, Bootstrap, Intercom) to
demonstrate the schema and verify the pipeline works. These will rarely fire on typical ecommerce
audit targets and are intentionally low-noise.

## Upgrading to full coverage (~3000 technologies)

The community `webappanalyzer` project (a maintained fork of the original Wappalyzer data) publishes
a large `technologies.json` in the same schema. Dropping the full file here gives detect-search
coverage of ~3000 technologies with zero code change.

### Steps

1. Check the license first. The webappanalyzer data is published under the MIT License:
   - Repository: https://github.com/enthec/webappanalyzer
   - License file: https://github.com/enthec/webappanalyzer/blob/main/LICENSE
   - Confirm it remains MIT before vendoring. Do NOT vendor if the license is GPL or proprietary.

2. Download the current technologies JSON (the upstream file may be split by letter A–Z or by
   category depending on the fork version):

   ```bash
   # Single-file variant (older format):
   curl -L https://raw.githubusercontent.com/enthec/webappanalyzer/main/src/technologies/a.json \
        -o fingerprints/technologies-a.json
   # Merge all letter files into one technologies.json (jq required):
   jq -s 'reduce .[] as $f ({}; . * $f)' fingerprints/technologies-?.json \
        > fingerprints/technologies.json
   ```

3. Commit the merged file. tech-fingerprint-db.js picks it up on next run.

## Schema reference (webappanalyzer format)

```json
{
  "TechName": {
    "cats":      ["Category Label"],
    "website":   "https://vendor.com",
    "url":       ["regex against any request URL"],
    "scriptSrc": ["regex against JS request URLs only"],
    "html":      ["regex against page HTML source"],
    "headers":   { "response-header-name": "value-regex" },
    "cookies":   { "cookie-name": "value-regex" },
    "js":        ["global variable expression (not evaluated by detect-search)"]
  }
}
```

Pattern strings support the `\\;version:\\1` meta-hint suffix used by Wappalyzer for version
extraction — `tech-fingerprint-db.js` strips everything after `\\;` before compiling the RegExp,
so the hints are safe to leave in place.

## Confidence level

Matches from this file are returned with `"confidence":"likely-opendb"` and `"source":"opendb"`.
They are always secondary to curated `detect-search` hits — if a technology is already matched by
the hand-curated `TECH_SIGNATURES` registry in `detect-search.js`, the open-DB duplicate is
suppressed (curated wins, no double-counting).
