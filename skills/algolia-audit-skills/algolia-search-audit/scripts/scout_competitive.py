#!/usr/bin/env python3
import sys, os, re, json, requests
from datetime import date
from anthropic import Anthropic

SCOUT_BASE = os.environ.get("SCOUT_URL", "http://localhost:8421")
SCOUT_KEY = os.environ.get("SCOUT_API_KEY", "dev-key")
HEADERS = {"Content-Type": "application/json", "X-API-Key": SCOUT_KEY}
TODAY = date.today().isoformat()

NEWSROOM_MAP = {
    "lufthansa":       "https://newsroom.lufthansagroup.com/en/",
    "emirates":        "https://www.emirates.com/media-centre/news/",
    "easyjet":         "https://corporate.easyjet.com/media",
    "ryanair":         "https://www.ryanair.com/gb/en/useful-info/about-ryanair/news/all",
    "delta":           "https://news.delta.com/",
    "iairgroup":       "https://www.iairgroup.com/press-releases/",
    "credit-agricole": "https://www.credit-agricole.com/en/finance/press-releases",
    "societegenerale": "https://www.societegenerale.com/en/news",
    "bnpparibas":      "https://group.bnpparibas/en/news",
}

def scrape_newsroom(domain):
    newsroom_url = next((url for frag, url in NEWSROOM_MAP.items() if frag in domain.lower()), None)
    if not newsroom_url:
        newsroom_url = f"https://www.{domain}/newsroom"
    try:
        r = requests.post(f"{SCOUT_BASE}/scrape", headers=HEADERS,
            json={"url": newsroom_url, "stealth": True, "timeout_ms": 35000}, timeout=45)
        if r.status_code == 200:
            data = r.json()
            md = data.get("markdown", "")
            words = len(md.split())
            return {"success": words >= 50, "url": newsroom_url, "markdown": md,
                    "word_count": words, "error": None if words >= 50 else f"Sparse ({words} words)"}
    except Exception as e:
        return {"success": False, "url": newsroom_url, "markdown": "", "word_count": 0, "error": str(e)}

def extract_signals_haiku(domain, markdown):
    client = Anthropic()
    prompt = f"""Analyse this competitor newsroom for signals relevant to an Algolia search pitch.

Competitor: {domain}
Content: {markdown[:2500]}

Return ONLY valid JSON:
{{"competitor":"{domain}","signals":[{{"headline":"exact text","date":"YYYY-MM-DD or null","signal_type":"digital|search|platform|ai|partnership","relevance":5}}],"top_signal":"one sentence most relevant finding","overall_relevance_score":5,"collection_date":"{TODAY}"}}

Only signals with relevance >= 5. Focus on: digital transformation, search/discovery, platform modernisation, AI, online booking improvements."""
    try:
        resp = Anthropic().messages.create(model="claude-haiku-4-5-20251001", max_tokens=600,
            messages=[{"role":"user","content":prompt}])
        raw = resp.content[0].text
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        return json.loads(m.group(0)) if m else {}
    except Exception as e:
        return {"competitor": domain, "signals": [], "top_signal": f"error: {e}",
                "overall_relevance_score": 0, "collection_date": TODAY}

def run(output_dir, competitor_domains):
    results = {}
    for domain in competitor_domains[:6]:
        print(f"  [{domain}] scraping newsroom...")
        s = scrape_newsroom(domain)
        if s["success"]:
            print(f"    ✓ {s['word_count']} words from {s['url']}")
            sig = extract_signals_haiku(domain, s["markdown"])
            results[domain] = {**sig, "source_url": s["url"]}
            n = len(sig.get("signals",[]))
            score = sig.get("overall_relevance_score", 0)
            print(f"    ✓ {n} signals | relevance {score}/10 | top: {sig.get('top_signal','')[:80]}")
        else:
            print(f"    ✗ {s['error']}")
            results[domain] = {"competitor": domain, "signals": [], "error": s["error"],
                               "source_url": s["url"], "collection_date": TODAY}
    return results

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("domain"); p.add_argument("output_dir")
    p.add_argument("--competitors", default="")
    args = p.parse_args()
    comp_list = [c.strip() for c in args.competitors.split(",") if c.strip()]
    results = run(args.output_dir, comp_list)
    print("\n=== RESULTS ===")
    for domain, r in results.items():
        print(f"\n{domain}: score={r.get('overall_relevance_score',0)}/10 | signals={len(r.get('signals',[]))}")
        print(f"  top: {r.get('top_signal','none')}")
        for s in r.get("signals",[])[:3]:
            print(f"  [{s.get('relevance',0)}/10 {s.get('signal_type','')}] {s.get('headline','')[:80]}")
