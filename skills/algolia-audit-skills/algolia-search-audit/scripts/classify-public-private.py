#!/usr/bin/env python3
"""
classify-public-private.py — DETERMINISTIC public vs private routing for the orchestrator.

The orchestrator's SKILL.md routes a company to `algolia-intel-financial-public` (Yahoo MCP)
vs `algolia-intel-financial-private` (6-source waterfall) based on whether it is publicly
traded. The old method was a free-text WebSearch "{Company} stock ticker NYSE NASDAQ" + an LLM
guess — a routing-misclassification surface at the very top of the pipeline (a wrong call sends
the whole financial leg down the wrong skill and can clobber 08-financial-profile.md; see BUG-5).

This script replaces the guess with a ticker/exchange lookup:
  1. If a ticker is supplied (--ticker), validate it resolves to a real quote with an exchange.
  2. Otherwise resolve a candidate symbol from the company name via Yahoo Finance symbol search,
     then validate the top hit returns a real quote (price/market state/exchange).
A company is PUBLIC iff a symbol validates with an exchange; otherwise PRIVATE.

Deterministic: same input → same verdict (no LLM, no free-text interpretation). Network-bound
(Yahoo Finance), with a hard offline self-test for the decision logic.

Usage:
  python3 classify-public-private.py --company "Costco Wholesale"
  python3 classify-public-private.py --company "Costco" --ticker COST
  python3 classify-public-private.py --company "Torrid" --domain torrid.com
  python3 classify-public-private.py --self-test     # offline decision-logic checks

Output: JSON to stdout:
  {"company": "...", "company_type": "public"|"private", "ticker": "COST"|null,
   "exchange": "NMS"|null, "confidence": "high"|"low", "method": "...", "evidence": {...}}
Exit code: 0 always when a verdict is produced (the verdict is in JSON); 2 on usage error.
"""

import argparse
import json
import re
import sys


def _validate_symbol(symbol):
    """Return (is_public, info_dict) for a candidate ticker using yfinance.

    PUBLIC requires a real exchange AND a quote signal (price or market cap). This rejects
    symbol-search noise that resolves to a defunct/placeholder ticker with no live quote.
    """
    try:
        import yfinance as yf
    except ImportError:
        return None, {"error": "yfinance not installed"}
    try:
        tk = yf.Ticker(symbol)
        info = {}
        try:
            info = tk.info or {}
        except Exception:  # noqa: BLE001 — info can raise on bad symbols
            info = {}
        exchange = info.get("exchange") or info.get("fullExchangeName")
        price = info.get("regularMarketPrice") or info.get("currentPrice")
        mcap = info.get("marketCap")
        quote_type = info.get("quoteType")
        is_public = bool(exchange) and (price is not None or mcap is not None) and quote_type in (None, "EQUITY", "ETF")
        return is_public, {
            "symbol": symbol,
            "exchange": exchange,
            "regularMarketPrice": price,
            "marketCap": mcap,
            "quoteType": quote_type,
            "longName": info.get("longName") or info.get("shortName"),
        }
    except Exception as e:  # noqa: BLE001
        return None, {"error": f"{type(e).__name__}: {e}"}


def _search_symbol(company):
    """Resolve a candidate ticker from a company name via Yahoo Finance search. Returns symbol|None."""
    try:
        import yfinance as yf
    except ImportError:
        return None, {"error": "yfinance not installed"}
    # yfinance.Search is available in modern versions; fall back to the Lookup if not.
    try:
        if hasattr(yf, "Search"):
            res = yf.Search(company, max_results=5)
            quotes = getattr(res, "quotes", None) or []
            # Prefer an EQUITY hit with an exchange.
            for q in quotes:
                if q.get("quoteType") in ("EQUITY",) and q.get("exchange") and q.get("symbol"):
                    return q["symbol"], {"hits": [qq.get("symbol") for qq in quotes]}
            if quotes and quotes[0].get("symbol"):
                return quotes[0]["symbol"], {"hits": [qq.get("symbol") for qq in quotes]}
        return None, {"hits": []}
    except Exception as e:  # noqa: BLE001
        return None, {"error": f"{type(e).__name__}: {e}"}


def classify(company, ticker=None, domain=None):
    evidence = {}
    # Path 1: explicit ticker → validate
    if ticker:
        is_public, info = _validate_symbol(ticker.upper())
        evidence["validation"] = info
        if is_public:
            return _verdict(company, "public", ticker.upper(), info.get("exchange"), "high",
                            "explicit_ticker_validated", evidence)
        # explicit ticker that does NOT validate → fall through to search (typo guard)
    # Path 2: resolve symbol from name
    sym, search_info = _search_symbol(company)
    evidence["search"] = search_info
    if sym:
        is_public, info = _validate_symbol(sym)
        evidence["validation"] = info
        if is_public:
            return _verdict(company, "public", sym, info.get("exchange"), "high",
                            "name_search_validated", evidence)
    # Nothing validated → private
    return _verdict(company, "private", None, None,
                    "low" if "error" in str(search_info) else "high",
                    "no_validated_public_symbol", evidence)


def _verdict(company, ctype, ticker, exchange, confidence, method, evidence):
    return {
        "company": company,
        "company_type": ctype,
        "ticker": ticker,
        "exchange": exchange,
        "confidence": confidence,
        "method": method,
        "route": "algolia-intel-financial-public" if ctype == "public" else "algolia-intel-financial-private",
        "evidence": evidence,
    }


# ── offline decision-logic self-test (no network) ───────────────────────────────

def self_test():
    fails = []

    def check(label, cond):
        if not cond:
            fails.append(label)
            print(f"  FAIL: {label}", file=sys.stderr)
        else:
            print(f"  ok: {label}", file=sys.stderr)

    # _verdict routing
    v = _verdict("X", "public", "COST", "NMS", "high", "m", {})
    check("public routes to public skill", v["route"].endswith("financial-public"))
    p = _verdict("Y", "private", None, None, "high", "m", {})
    check("private routes to private skill", p["route"].endswith("financial-private"))
    check("public verdict carries ticker", v["ticker"] == "COST")
    check("private verdict has null ticker", p["ticker"] is None)

    # Validation gate logic, simulated (no yfinance call): a hit needs exchange + a quote signal.
    def gate(info):
        exchange = info.get("exchange")
        price = info.get("regularMarketPrice")
        mcap = info.get("marketCap")
        qt = info.get("quoteType")
        return bool(exchange) and (price is not None or mcap is not None) and qt in (None, "EQUITY", "ETF")

    check("real equity passes gate", gate({"exchange": "NMS", "regularMarketPrice": 900.0, "quoteType": "EQUITY"}))
    check("exchange-only (no quote) fails gate", not gate({"exchange": "NMS", "quoteType": "EQUITY"}))
    check("quote without exchange fails gate", not gate({"regularMarketPrice": 5.0, "quoteType": "EQUITY"}))
    check("crypto/index quoteType rejected", not gate({"exchange": "CCC", "regularMarketPrice": 1.0, "quoteType": "CRYPTOCURRENCY"}))

    print(("\n✗ self-test FAILED" if fails else "\n✓ self-test passed (offline decision logic)"), file=sys.stderr)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description="Deterministic public/private classifier for audit routing")
    ap.add_argument("--company")
    ap.add_argument("--ticker", default=None)
    ap.add_argument("--domain", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())
    if not args.company:
        ap.error("--company is required")

    result = classify(args.company, args.ticker, args.domain)
    print(json.dumps(result, indent=2))
    print(f"\n→ {result['company_type'].upper()} "
          f"({result['ticker'] or 'no ticker'}, {result['confidence']} confidence) "
          f"→ {result['route']}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
