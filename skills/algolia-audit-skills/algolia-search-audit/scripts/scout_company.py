#!/usr/bin/env python3
"""
scout-company.py — Scout-based company field extractor.
Uses Scout at http://localhost:8421 to crawl About + Careers pages
and extract: linkedin_url, twitter_handle, careers_url, website.

Usage: python3 scout-company.py <domain> <output_dir>
       (output_dir only used for context — this script does not write)

Returns JSON to stdout:
{
  "linkedin_url": "...",
  "twitter_handle": "...",
  "careers_url": "...",
  "website": "...",
  "sources": {...},
  "scout_available": true
}
"""
import sys, os, re, json, requests
from datetime import date

SCOUT_BASE = os.environ.get("SCOUT_URL", "http://localhost:8421")
SCOUT_KEY = os.environ.get("SCOUT_API_KEY", "dev-key")
TODAY = date.today().isoformat()
HEADERS = {"Content-Type": "application/json", "X-API-Key": SCOUT_KEY}
TIMEOUT = 30

ABOUT_PATTERNS = ["/about", "/about-us", "/company", "/who-we-are", "/our-story"]
CAREERS_PATTERNS = ["/careers", "/jobs", "/join-us", "/work-with-us", "/join"]
INVESTOR_PATTERNS = ["/investors", "/investor-relations", "/ir"]

def scout_available():
    try:
        r = requests.get(f"{SCOUT_BASE}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def scrape_with_scout(url, use_js=False):
    """Scrape a URL via Scout with stealth=true. Returns normalized dict."""
    try:
        r = requests.post(
            f"{SCOUT_BASE}/scrape",
            headers=HEADERS,
            json={
                "url": url,
                "formats": ["markdown"],
                "use_js": use_js,
                "stealth": True,
                "timeout_ms": TIMEOUT * 1000
            },
            timeout=TIMEOUT + 5
        )
        if r.status_code == 200:
            data = r.json()
            # Scout returns links as a list of strings (URLs)
            links = data.get("links", [])
            if links and isinstance(links[0], dict):
                # Handle old format with dicts
                links = [l.get("href", "") for l in links if l.get("href")]
            # Else links are already strings; filter out empty ones
            links = [l for l in links if l]
            return {
                "success": data.get("success", False),
                "markdown": data.get("markdown", ""),
                "links": links,
                "error": data.get("error", "")
            }
        return {"success": False, "markdown": "", "links": [], "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "markdown": "", "links": [], "error": str(e)}

def try_url_patterns(domain, patterns, use_js=False):
    """Try a list of URL patterns against domain. Return first successful result."""
    for pattern in patterns:
        url = f"https://www.{domain}{pattern}"
        result = scrape_with_scout(url, use_js=use_js)
        if result["success"] and len(result["markdown"]) > 100:
            return result, url

    # Fallback: try without www
    for pattern in patterns:
        url = f"https://{domain}{pattern}"
        result = scrape_with_scout(url, use_js=use_js)
        if result["success"] and len(result["markdown"]) > 100:
            return result, url

    return None, None

def extract_social_links(markdown, links):
    """
    Extract linkedin_url and twitter_handle from page markdown and link list.
    Three-strategy fallback: regex on markdown → link scan → None.
    """
    result = {"linkedin_url": None, "twitter_handle": None}

    # Strategy 1: regex on markdown for LinkedIn URL
    li_match = re.search(r'https?://(?:www\.)?linkedin\.com/company/[\w\-]+/?', markdown, re.IGNORECASE)
    if li_match:
        result["linkedin_url"] = li_match.group(0).rstrip("/")

    # Strategy 1: regex on markdown for Twitter handle
    tw_match = re.search(r'@([A-Za-z0-9_]{1,50})(?=\s|$|[^A-Za-z0-9_])', markdown)
    if tw_match:
        candidate = tw_match.group(0)
        # Filter out generic @mentions that aren't handles
        if not any(w in candidate.lower() for w in ["email", "contact", "support"]):
            result["twitter_handle"] = candidate

    # Strategy 2: scan links list for LinkedIn
    if not result["linkedin_url"]:
        for link in links:
            if "linkedin.com/company/" in link.lower():
                result["linkedin_url"] = link.rstrip("/")
                break

    # Strategy 2: scan links list for Twitter/X
    if not result["twitter_handle"]:
        for link in links:
            if "twitter.com/" in link.lower() or "x.com/" in link.lower():
                slug = link.rstrip("/").split("/")[-1]
                if slug and slug not in ("home", "search", "explore", "intent"):
                    result["twitter_handle"] = f"@{slug}"
                    break

    return result

def run(domain, output_dir):
    if not scout_available():
        return {
            "scout_available": False,
            "error": "Scout not running at " + SCOUT_BASE,
            "linkedin_url": None,
            "twitter_handle": None,
            "careers_url": None,
            "website": None
        }

    result = {
        "scout_available": True,
        "linkedin_url": None,
        "twitter_handle": None,
        "careers_url": None,
        "website": f"https://www.{domain}",
        "sources": {}
    }

    # Step 1: Try About pages
    about_result, about_url = try_url_patterns(domain, ABOUT_PATTERNS, use_js=False)
    if not about_result:
        # Retry with JS if no-JS failed
        about_result, about_url = try_url_patterns(domain, ABOUT_PATTERNS, use_js=True)

    if about_result and about_result["success"]:
        social = extract_social_links(about_result["markdown"], about_result["links"])
        result["linkedin_url"] = social["linkedin_url"]
        result["twitter_handle"] = social["twitter_handle"]
        result["sources"]["about"] = {
            "url": about_url,
            "label": f"[FACT — Scout scrape, {TODAY}]"
        }

    # Step 2: Try Careers pages
    careers_result, careers_url = try_url_patterns(domain, CAREERS_PATTERNS, use_js=False)
    if careers_result and careers_result["success"]:
        result["careers_url"] = careers_url
        result["sources"]["careers"] = {
            "url": careers_url,
            "label": f"[FACT — Scout scrape, {TODAY}]"
        }

    # Step 3: Try Investor pages (extract PDFs if any)
    investor_urls = []
    investor_result, investor_url = try_url_patterns(domain, INVESTOR_PATTERNS, use_js=False)
    if investor_result and investor_result["success"]:
        # Find PDF links
        pdfs = [l for l in investor_result["links"] if l.lower().endswith(".pdf")]
        if pdfs:
            investor_urls = pdfs[:3]  # Top 3 PDFs
            result["sources"]["investor_urls"] = {
                "urls": investor_urls,
                "label": f"[FACT — Scout scrape, {TODAY}]"
            }

    return result

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 scout-company.py <domain> <output_dir>", file=sys.stderr)
        sys.exit(1)
    domain, output_dir = sys.argv[1], sys.argv[2]
    print(json.dumps(run(domain, output_dir), indent=2))
