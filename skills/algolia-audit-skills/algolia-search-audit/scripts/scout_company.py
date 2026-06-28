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

# F1 FIX (see spike-unify-audit/F-scout-ab-evidence.md): Scout's HTML→markdown step
# yields EMPTY markdown (~1–4 chars) on Squarespace/JS bio-card CMSes even when it
# successfully fetched the page (raw_html is full). Below this many chars of markdown
# we treat the markdown as degraded and fall back to parsing raw_html — LOUDLY, never
# silently. raw_html below RAW_HTML_MIN means Scout got nothing usable at all.
MARKDOWN_MIN_CHARS = 50
RAW_HTML_MIN_CHARS = 1000


def _log(msg):
    print(msg, file=sys.stderr)

ABOUT_PATTERNS = ["/about", "/about-us", "/company", "/who-we-are", "/our-story"]
CAREERS_PATTERNS = ["/careers", "/jobs", "/join-us", "/work-with-us", "/join"]
INVESTOR_PATTERNS = ["/investors", "/investor-relations", "/ir"]
LEADERSHIP_PATTERNS = [
    "/about/leadership", "/about/team", "/about/executive-team",
    "/leadership", "/team", "/executive-team", "/about/executives",
    "/about/management", "/company/leadership", "/about/our-team",
]

EXEC_TITLE_KEYWORDS = [
    "chief executive", "ceo", "chief technology", "cto", "chief information", "cio",
    "chief digital", "cdo", "chief marketing", "cmo", "chief operating", "coo",
    "chief financial", "cfo", "president", "vp ", "vice president",
    "director", "head of", "general manager", "managing director",
]

def scout_available():
    try:
        r = requests.get(f"{SCOUT_BASE}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def scrape_with_scout(url, use_js=False):
    """
    Scrape a URL via Scout with stealth=true. Returns normalized dict.

    F1 FIX: ALSO request raw_html so that when Scout's markdown conversion is broken
    (Squarespace/JS CMS → ~1–4 char markdown) we can still recover content from the
    HTML. Sets degraded=True LOUDLY when markdown is empty/below threshold but raw_html
    is substantial, so callers can fall back instead of silently returning nothing.
    """
    try:
        r = requests.post(
            f"{SCOUT_BASE}/scrape",
            headers=HEADERS,
            json={
                "url": url,
                "formats": ["markdown", "raw_html"],
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
            markdown = data.get("markdown", "") or ""
            raw_html = data.get("raw_html", "") or data.get("html", "") or ""
            degraded = (
                len(markdown.strip()) < MARKDOWN_MIN_CHARS
                and len(raw_html) >= RAW_HTML_MIN_CHARS
            )
            if degraded:
                _log(
                    f"  ⚠ Scout markdown DEGRADED for {url}: "
                    f"md={len(markdown.strip())} chars (<{MARKDOWN_MIN_CHARS}), "
                    f"raw_html={len(raw_html)} chars — falling back to raw_html parse "
                    f"(likely Squarespace/JS CMS; see F-scout-ab-evidence.md F1)"
                )
            return {
                "success": data.get("success", False),
                "markdown": markdown,
                "raw_html": raw_html,
                "degraded": degraded,
                "links": links,
                "error": data.get("error", "")
            }
        return {"success": False, "markdown": "", "raw_html": "", "degraded": False,
                "links": [], "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "markdown": "", "raw_html": "", "degraded": False,
                "links": [], "error": str(e)}

def html_to_text(raw_html):
    """
    F1 FALLBACK: best-effort raw_html → text when Scout's markdown is degraded.
    Strips <script>/<style>, surfaces <img alt="..."> (Squarespace exec bio cards put
    name+title in alt attrs), then strips remaining tags and collapses whitespace.
    Not a full parser — just enough for the same regex extractors markdown feeds.
    """
    if not raw_html:
        return ""
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", raw_html)
    # Surface alt text as its own line so name/title bio cards survive tag-stripping.
    html = re.sub(r'(?i)<img[^>]*\balt=["\']([^"\']+)["\'][^>]*>', r"\n\1\n", html)
    # Surface common block boundaries as newlines.
    html = re.sub(r"(?i)<(/?)(p|div|li|tr|h[1-6]|br|section|article)[^>]*>", "\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    # Decode a few common entities; collapse whitespace per line.
    for ent, ch in (("&amp;", "&"), ("&nbsp;", " "), ("&#39;", "'"),
                    ("&quot;", '"'), ("&lt;", "<"), ("&gt;", ">")):
        text = text.replace(ent, ch)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def usable_text(result):
    """
    Return the best available text for a Scout result: markdown when healthy, else
    raw_html-derived text when markdown was degraded. Empty string if neither usable.
    """
    md = result.get("markdown", "") or ""
    if len(md.strip()) >= MARKDOWN_MIN_CHARS:
        return md
    if result.get("degraded") and result.get("raw_html"):
        return html_to_text(result["raw_html"])
    return md


def _result_usable(result):
    """A result is usable if markdown is substantial OR we recovered raw_html text."""
    if not result.get("success"):
        return False
    md = result.get("markdown", "") or ""
    if isinstance(md, str) and len(md) > 100:
        return True
    # F1: degraded markdown but recoverable raw_html.
    return bool(result.get("degraded") and len(usable_text(result)) > 100)


def try_url_patterns(domain, patterns, use_js=False):
    """Try a list of URL patterns against domain. Return first usable result.

    Usable now includes the F1 degraded-markdown case where raw_html recovered text.
    """
    for prefix in (f"https://www.{domain}", f"https://{domain}"):
        for pattern in patterns:
            url = f"{prefix}{pattern}"
            result = scrape_with_scout(url, use_js=use_js)
            if _result_usable(result):
                return result, url

    return None, None

def extract_description(markdown):
    """Extract company description from About page markdown. Returns first substantial paragraph."""
    if not markdown:
        return None
    # Strip markdown headers and bullets, find first paragraph ≥ 80 chars
    for line in markdown.split("\n"):
        line = line.strip()
        if line.startswith(("#", "-", "*", "|", "!", "[")):
            continue
        if len(line) >= 80:
            return line[:600]
    return None


def extract_executives(markdown):
    """
    Extract executive name+title pairs from a leadership page.
    Best-effort: looks for lines where a known title keyword appears near a capitalized name.
    Returns list of {"name": str, "title": str, "source": "Scout"}.
    """
    if not markdown:
        return []

    executives = []
    lines = markdown.split("\n")
    seen_names = set()

    for i, line in enumerate(lines):
        line_lower = line.lower()
        if not any(kw in line_lower for kw in EXEC_TITLE_KEYWORDS):
            continue

        # Extract title — the line itself or the keyword match
        title_line = line.strip().lstrip("#*- ").strip()
        if len(title_line) < 3 or len(title_line) > 120:
            continue

        # Look for a name on the preceding or following line (capitalized words)
        name = None
        for offset in [-1, +1, -2, +2]:
            idx = i + offset
            if 0 <= idx < len(lines):
                candidate = lines[idx].strip().lstrip("#*- ").strip()
                # Name heuristic: 2–4 capitalized words, no special chars, not a title keyword
                words = candidate.split()
                if (2 <= len(words) <= 4
                        and all(w[0].isupper() for w in words if w)
                        and not any(kw in candidate.lower() for kw in EXEC_TITLE_KEYWORDS)
                        and len(candidate) < 60):
                    name = candidate
                    break

        if name and name not in seen_names:
            seen_names.add(name)
            executives.append({
                "name": name,
                "title": title_line,
                "source": "Scout leadership page",
                "label": f"[FACT — Scout scrape, {TODAY}]"
            })

    return executives[:10]  # cap at 10


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

def run(domain, _output_dir=None):
    if not scout_available():
        return {
            "scout_available": False,
            "error": "Scout not running at " + SCOUT_BASE,
            "description": None,
            "executives": [],
            "linkedin_url": None,
            "twitter_handle": None,
            "careers_url": None,
            "website": None,
        }

    result = {
        "scout_available": True,
        "description": None,
        "executives": [],
        "linkedin_url": None,
        "twitter_handle": None,
        "careers_url": None,
        "website": f"https://www.{domain}",
        "scout_degraded": False,        # F1: True if ANY page fell back to raw_html
        "degraded_sources": [],         # which pages were degraded (loud, not silent)
        "sources": {},
    }

    def _method_label(res):
        """Per-source method + label: markdown when healthy, raw_html fallback when degraded."""
        if res.get("degraded"):
            result["scout_degraded"] = True
            return ("scout_raw_html_fallback",
                    f"[OBSERVED — Scout raw_html fallback (markdown degraded), {TODAY}]")
        return ("scout_markdown", f"[FACT — Scout scrape, {TODAY}]")

    # Step 1: About page — description + social links
    about_result, about_url = try_url_patterns(domain, ABOUT_PATTERNS, use_js=False)
    if not about_result:
        about_result, about_url = try_url_patterns(domain, ABOUT_PATTERNS, use_js=True)

    if about_result and about_result["success"]:
        text = usable_text(about_result)
        method, label = _method_label(about_result)
        if about_result.get("degraded"):
            result["degraded_sources"].append({"page": "about", "url": about_url})
        result["description"] = extract_description(text)
        social = extract_social_links(text, about_result.get("links", []))
        result["linkedin_url"] = social["linkedin_url"]
        result["twitter_handle"] = social["twitter_handle"]
        result["sources"]["about"] = {
            "url": about_url, "collection_method": method, "label": label,
        }

    # Step 2: Leadership page — exec name/title extraction
    leadership_result, leadership_url = try_url_patterns(domain, LEADERSHIP_PATTERNS, use_js=False)
    if not leadership_result:
        leadership_result, leadership_url = try_url_patterns(domain, LEADERSHIP_PATTERNS, use_js=True)

    if leadership_result and leadership_result["success"]:
        text = usable_text(leadership_result)
        method, label = _method_label(leadership_result)
        execs = extract_executives(text)
        if execs:
            # Stamp the per-source label on each exec so the degradation is visible downstream.
            for e in execs:
                e["source"] = "Scout leadership page"
                e["label"] = label
            result["executives"] = execs
            if leadership_result.get("degraded"):
                result["degraded_sources"].append({"page": "leadership", "url": leadership_url})
            result["sources"]["leadership"] = {
                "url": leadership_url, "collection_method": method, "label": label,
            }

    # Step 3: Careers page
    careers_result, careers_url = try_url_patterns(domain, CAREERS_PATTERNS, use_js=False)
    if careers_result and careers_result["success"]:
        method, label = _method_label(careers_result)
        result["careers_url"] = careers_url
        if careers_result.get("degraded"):
            result["degraded_sources"].append({"page": "careers", "url": careers_url})
        result["sources"]["careers"] = {
            "url": careers_url, "collection_method": method, "label": label,
        }

    # Step 4: Investor page — IR URL + PDF discovery
    investor_result, investor_url = try_url_patterns(domain, INVESTOR_PATTERNS, use_js=False)
    if investor_result and investor_result["success"]:
        method, label = _method_label(investor_result)
        result["ir_url"] = investor_url
        raw_links = investor_result.get("links", [])
        links_list = raw_links if isinstance(raw_links, list) else []
        pdfs = [l for l in links_list if isinstance(l, str) and l.lower().endswith(".pdf")]
        if investor_result.get("degraded"):
            result["degraded_sources"].append({"page": "investor", "url": investor_url})
        result["sources"]["investor"] = {
            "url": investor_url,
            "pdf_urls": pdfs[:3],
            "collection_method": method,
            "label": label,
        }

    # F1: surface degradation LOUDLY at the end, never silent.
    if result["scout_degraded"]:
        pages = ", ".join(s["page"] for s in result["degraded_sources"])
        _log(
            f"  ⚠⚠ Scout DEGRADED for {domain}: markdown empty on [{pages}] — "
            f"recovered via raw_html fallback (labels downgraded to [OBSERVED]). "
            f"Verify these fields; consider WebFetch. (F1: Squarespace/JS CMS)"
        )

    return result

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 scout-company.py <domain> <output_dir>", file=sys.stderr)
        sys.exit(1)
    domain, output_dir = sys.argv[1], sys.argv[2]
    print(json.dumps(run(domain, output_dir), indent=2))
