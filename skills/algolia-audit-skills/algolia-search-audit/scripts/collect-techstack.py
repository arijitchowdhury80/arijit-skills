#!/usr/bin/env python3
"""
collect-techstack.py — Collect the prospect's technology stack, KEYLESS.

PRIMARY source: detect-search (`detect-search.js --full-tech`) — live multi-page network
packet inspection (home/PLP/PDP/search/cart). Fingerprints search vendor, ecommerce platform,
analytics, tag manager, CDN/WAF, personalization, payment, CDP, frontend framework, hosting,
etc. from request URLs + response headers + cookies + HTML. No API keys. This is exactly how
BuiltWith/Wappalyzer work (load the domain, fingerprint what's exposed).

OPTIONAL cross-check: SimilarWeb technologies endpoint (only if SIMILARWEB_API_KEY is set).

The `--full-tech` JSON is translated into the 02-tech-stack.json schema by map-detect-tech.py.

Usage: python3 collect-techstack.py <domain> <output-dir>
Env:   SIMILARWEB_API_KEY  (optional cross-check; absent -> skipped gracefully)

No fabrication: only tech the live load actually exposed is reported. Client-side only —
backend tech is invisible (so is BuiltWith's; and live load can't see historical/removed tech).
BuiltWith removed from pipeline (2026-06-29) — no key required anywhere.
"""

import sys, os, json, subprocess, importlib.util
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_detect_js():
    """detect-search lives at ~/.claude/skills/detect-search/ on both Mac and the VPS
    (the algolia skills resolve through a symlink to the repo, so a relative-to-__file__
    path is unreliable). Try env override, the ~ install path, then relative guesses."""
    candidates = [
        os.environ.get('DETECT_SEARCH_JS', ''),
        os.path.expanduser('~/.claude/skills/detect-search/detect-search.js'),
        os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', '..', 'detect-search', 'detect-search.js')),
        os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', 'detect-search', 'detect-search.js')),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return candidates[1]  # default to the ~ path (for a clear error message)


DETECT_JS = _resolve_detect_js()
DETECT_DIR = os.path.dirname(DETECT_JS)
SIMILARWEB_API_KEY = os.environ.get('SIMILARWEB_API_KEY', '')
TODAY = date.today().isoformat()

# Load the hyphenated bridge module (map-detect-tech.py) via importlib.
_spec = importlib.util.spec_from_file_location(
    "map_detect_tech", os.path.join(SCRIPT_DIR, "map-detect-tech.py")
)
map_detect_tech = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(map_detect_tech)


def run_detect_tech(domain):
    """Run detect-search.js --full-tech on the domain. Returns (full_tech_dict, error)."""
    if not os.path.exists(DETECT_JS):
        return None, f"detect-search.js not found at {DETECT_JS}"
    try:
        proc = subprocess.run(
            ['node', DETECT_JS, f'https://www.{domain}', '--full-tech'],
            cwd=DETECT_DIR, capture_output=True, text=True, timeout=300,
        )
    except subprocess.TimeoutExpired:
        return None, "detect-search timed out (300s)"
    except Exception as e:
        return None, f"detect-search invocation failed: {e}"
    if proc.returncode != 0:
        return None, f"detect-search exit {proc.returncode}: {(proc.stderr or '')[:300]}"
    try:
        return json.loads(proc.stdout), None
    except Exception as e:
        return None, f"detect-search returned non-JSON: {e}"


def call_similarweb_tech(domain):
    """Optional SimilarWeb technologies cross-check. Returns (data, error)."""
    import requests
    from datetime import timedelta
    end = date.today().replace(day=1) - timedelta(days=1)
    start = end.replace(month=max(1, end.month - 2))
    url = f"https://api.similarweb.com/v1/website/{domain}/content/technologies"
    params = {'api_key': SIMILARWEB_API_KEY,
              'start_date': start.strftime('%Y-%m'), 'end_date': end.strftime('%Y-%m')}
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code in (403, 404):
            return None, f"HTTP {r.status_code}"
        r.raise_for_status()
        return r.json(), None
    except Exception as e:
        return None, str(e)


def render_md(domain, tech, sw_section, sources_failed):
    """Render 02-tech-stack.md from the mapped tech-stack JSON."""
    lines = [f"# Tech Stack — {domain}", f"*Generated: {TODAY} — {tech.get('detection_method','')}*", ""]
    lines.append(f"**Pages inspected:** {', '.join(tech.get('pages_visited') or []) or 'n/a'}")
    if tech.get('bot_blocked'):
        lines.append("\n> ⚠ Bot/WAF block encountered on one or more pages — coverage may be partial.")
    lines.append("")

    vendors = tech.get('search_vendors') or []
    lines.append("## Search Vendor")
    if vendors:
        for v in vendors:
            ep = f" — `{v.get('network_endpoint')}`" if v.get('network_endpoint') else ""
            lines.append(f"- **{v.get('vendor')}** ({v.get('confidence')}){ep}  [FACT — detect-search network, {TODAY}]")
        lines.append(f"\n**Algolia already in use:** {'YES' if tech.get('algolia_detected') else 'no'}")
    else:
        lines.append("- No search vendor detected via network inspection (could be server-side/proxied, or WAF-blocked).")
    lines.append("")

    ts = tech.get('tech_stack') or {}
    lines.append("## Technology Stack (live network fingerprint)")
    any_tech = False
    for cat, items in ts.items():
        if not items:
            continue
        any_tech = True
        lines.append(f"\n### {cat.replace('_', ' ').title()}")
        for it in items:
            pages = ', '.join(it.get('pages') or [])
            src = it.get('source', 'detect-search')
            lines.append(f"- {it.get('technology')} — {it.get('confidence')} "
                         f"({src}; pages: {pages})  [FACT — detect-search network, {TODAY}]")
    if not any_tech:
        lines.append("\n*No technologies fingerprinted (site may be bot-walled or minimal).*")
    lines.append("")

    if tech.get('limitations'):
        lines.append("## Limitations")
        for lim in tech['limitations']:
            lines.append(f"- {lim}")
        lines.append("")

    lines.append(sw_section)
    if sources_failed:
        lines.append("## Sources Failed\n" + "\n".join(f"- {s}" for s in sources_failed) + "\n")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 3:
        print("Usage: collect-techstack.py <domain> <output-dir>", file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1].lower().replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)
    sources_failed = []

    # PRIMARY: detect-search live fingerprint
    print(f"Fingerprinting tech stack for {domain} via detect-search (--full-tech)...", file=sys.stderr)
    full_tech, dt_err = run_detect_tech(domain)
    if dt_err:
        sources_failed.append(f"detect-search: {dt_err}")
        print(f"  detect-search: {dt_err}", file=sys.stderr)
        # Build an empty-but-valid mapped result so downstream still gets the schema.
        full_tech = {"url": domain, "pages_visited": [], "detected": [], "search": {},
                     "not_detectable_note": "detect-search unavailable this run", "bot_blocked": False}
    tech = map_detect_tech.map_tech(full_tech, domain)

    # OPTIONAL: SimilarWeb cross-check
    if SIMILARWEB_API_KEY:
        sw_tech, sw_err = call_similarweb_tech(domain)
        if sw_err:
            sources_failed.append(f"similarweb_technologies: {sw_err}")
            sw_section = f"## SimilarWeb Cross-Check\n*Unavailable: {sw_err}*\n"
        else:
            techs = (sw_tech.get('technologies')
                     or sw_tech.get('data', {}).get('technologies', []))[:10]
            sw_section = ("## SimilarWeb Cross-Check (top 10)\n"
                          + "\n".join(f"- {t.get('name', t.get('technology', 'Unknown'))} ({t.get('category', '')})"
                                      for t in techs)
                          + f"\n[FACT — SimilarWeb API, {TODAY}]\n") if techs else \
                         "## SimilarWeb Cross-Check\n*No technology data returned.*\n"
    else:
        sources_failed.append("similarweb_technologies: key not configured")
        sw_section = "## SimilarWeb Cross-Check\n*Skipped — SIMILARWEB_API_KEY not set (optional).*\n"

    # Write outputs
    json_path = os.path.join(output_dir, '02-tech-stack.json')
    with open(json_path, 'w') as f:
        json.dump(tech, f, indent=2)
    md_path = os.path.join(output_dir, '02-tech-stack.md')
    with open(md_path, 'w') as f:
        f.write(render_md(domain, tech, sw_section, sources_failed))

    n_tech = sum(len(v) for v in (tech.get('tech_stack') or {}).values())
    result = {
        'status': 'success',
        'domain': domain,
        'output_file': md_path,
        'json_file': json_path,
        'search_vendors': [v.get('vendor') for v in (tech.get('search_vendors') or [])],
        'algolia_detected': tech.get('algolia_detected', False),
        'tech_count': n_tech,
        'pages_visited': tech.get('pages_visited') or [],
        'sources_failed': sources_failed,
        'note': 'Tech stack via detect-search live network fingerprint (keyless). BuiltWith removed.',
    }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
