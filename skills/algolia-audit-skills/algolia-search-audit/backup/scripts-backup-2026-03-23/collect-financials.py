#!/usr/bin/env python3
"""
collect-financials.py — Collect all financial data for Algolia Search Audit
Uses yfinance to get: income statement (3yr), balance sheet, stock info, analyst ratings, news.
Writes structured 08-financial-profile.md to the specified output directory.

Usage: python3 collect-financials.py <TICKER> <output-dir>
Requires: pip install yfinance
"""

import sys, os, json
from datetime import date

def check_yfinance():
    try:
        import yfinance as yf
        return yf
    except ImportError:
        print("Error: yfinance not installed. Run: pip install yfinance", file=sys.stderr)
        sys.exit(1)

def format_large_num(val):
    if val is None:
        return "N/A"
    try:
        v = float(val)
        if abs(v) >= 1e9:
            return f"${v/1e9:.3f}B"
        elif abs(v) >= 1e6:
            return f"${v/1e6:.1f}M"
        return f"${v:,.0f}"
    except:
        return str(val)

def pct(val):
    try:
        return f"{float(val)*100:.2f}%"
    except:
        return "N/A"

def safe_get(d, *keys, default="N/A"):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d if d is not None else default

def main():
    if len(sys.argv) < 3:
        print("Usage: collect-financials.py <TICKER> <output-dir>", file=sys.stderr)
        sys.exit(1)

    ticker_sym = sys.argv[1].upper()
    output_dir = sys.argv[2]
    today = date.today().isoformat()

    yf = check_yfinance()

    print(f"Fetching data for {ticker_sym}...", file=sys.stderr)
    ticker = yf.Ticker(ticker_sym)

    # 1. Stock info
    info = ticker.info or {}
    company_name = info.get('longName', info.get('shortName', ticker_sym))
    sector = info.get('sector', 'N/A')
    industry = info.get('industryDisp', info.get('industry', 'N/A'))
    employees = info.get('fullTimeEmployees', 'N/A')
    market_cap = format_large_num(info.get('marketCap'))
    current_price = info.get('currentPrice', info.get('regularMarketPrice', 'N/A'))
    analyst = info.get('recommendationKey', 'N/A').upper()
    analyst_mean = info.get('recommendationMean', 'N/A')
    analyst_count = info.get('numberOfAnalystOpinions', 'N/A')
    target_median = format_large_num(info.get('targetMedianPrice'))
    ebitda = format_large_num(info.get('ebitda'))
    ebitda_margin = pct(info.get('ebitdaMargins'))
    gross_margins = pct(info.get('grossMargins'))
    operating_margins = pct(info.get('operatingMargins'))
    profit_margins = pct(info.get('profitMargins'))
    revenue_ttm = format_large_num(info.get('totalRevenue'))

    # 2. Income statement (3 years)
    try:
        income = ticker.financials
        income_rows = []
        if income is not None and not income.empty:
            metrics = ['Total Revenue', 'Gross Profit', 'EBIT', 'EBITDA', 'Net Income', 'Operating Income']
            cols = list(income.columns)[:4]  # up to 4 years
            years = [str(c.year) + f" (FY{str(c.year)[-2:]})" for c in cols]
            header = "| Metric | " + " | ".join(years) + " |"
            sep = "|" + "---|" * (len(cols)+1)
            income_rows.append(header)
            income_rows.append(sep)
            for m in metrics:
                if m in income.index:
                    vals = [format_large_num(income.loc[m, c]) for c in cols]
                    income_rows.append(f"| {m} | " + " | ".join(vals) + " |")
    except Exception as e:
        income_rows = [f"*Income statement unavailable: {e}*"]

    # 3. Balance sheet highlights
    try:
        bs = ticker.balance_sheet
        total_assets = format_large_num(bs.loc['Total Assets', bs.columns[0]]) if bs is not None and 'Total Assets' in bs.index else "N/A"
        total_debt = format_large_num(bs.loc['Total Debt', bs.columns[0]]) if bs is not None and 'Total Debt' in bs.index else "N/A"
        cash = format_large_num(bs.loc['Cash And Cash Equivalents', bs.columns[0]]) if bs is not None and 'Cash And Cash Equivalents' in bs.index else "N/A"
    except:
        total_assets = total_debt = cash = "N/A"

    # 4. Analyst recommendations
    try:
        recs = ticker.recommendations
        rec_summary = ""
        if recs is not None and not recs.empty:
            latest = recs.tail(1)
            counts = []
            for col in ['strongBuy','buy','hold','sell','strongSell']:
                if col in latest.columns:
                    v = latest[col].values[0]
                    if v > 0:
                        counts.append(f"{v} {col.replace('strongBuy','Strong Buy').replace('strongSell','Strong Sell').replace('buy','Buy').replace('hold','Hold').replace('sell','Sell')}")
            rec_summary = " | ".join(counts)
    except:
        rec_summary = "N/A"

    # 5. Latest news (top 5)
    # yfinance news structure: each item is {'id': ..., 'content': {...}} (newer API)
    # or flat {'title': ..., 'link': ..., 'providerPublishTime': ...} (older API)
    try:
        news = ticker.news or []
        news_items = []
        from datetime import datetime
        for n in news[:5]:
            # Handle nested 'content' structure (yfinance >= 0.2.x)
            content = n.get('content', n)
            title = content.get('title', 'N/A')
            # Try clickThroughUrl first, then canonicalUrl, then top-level link
            click_url = content.get('clickThroughUrl', {})
            link = (click_url.get('url') if isinstance(click_url, dict) else None) or \
                   (content.get('canonicalUrl', {}).get('url') if isinstance(content.get('canonicalUrl'), dict) else None) or \
                   content.get('link', '')
            # Parse date: pubDate (ISO string) or providerPublishTime (unix timestamp)
            pub_date = ''
            if content.get('pubDate'):
                try:
                    pub_date = content['pubDate'][:10]  # ISO format: 2026-03-20T...
                except:
                    pass
            elif content.get('providerPublishTime'):
                try:
                    pub_date = datetime.fromtimestamp(content['providerPublishTime']).strftime('%Y-%m-%d')
                except:
                    pass
            if title and title != 'N/A':
                news_items.append(f"- [{title}]({link}) ({pub_date}) [FACT — Yahoo Finance news, {today}]")
        if not news_items:
            news_items = ["*No recent news available*"]
    except Exception as e:
        news_items = [f"*News unavailable: {e}*"]

    # Determine margin zone
    try:
        em = float(info.get('ebitdaMargins', 0)) * 100
        margin_zone = 'Red (<=10%)' if em <= 10 else 'Yellow (10-20%)' if em <= 20 else 'Green (>20%)'
    except:
        margin_zone = "Unknown"

    # Format employees safely
    try:
        employees_fmt = f"{int(employees):,}" if employees != 'N/A' else 'N/A'
    except:
        employees_fmt = str(employees)

    # Build output
    ir_url = f"https://finance.yahoo.com/quote/{ticker_sym}/financials"
    output = f"""# {company_name} — Financial Profile & ROI Estimate
**Ticker:** {ticker_sym}
**Generated:** {today}
**Source:** Yahoo Finance (yfinance) [FACT — collect-financials.py, {today}]

---

## Company Overview
- **Sector:** {sector}
- **Industry:** {industry}
- **Employees:** {employees_fmt} [FACT — Yahoo Finance, {today}]
- **Market Cap:** {market_cap} [FACT — Yahoo Finance, {today}]
- **Current Price:** ${current_price}

## Revenue Trend (3-Year)
{chr(10).join(income_rows)}

[FACT — Yahoo Finance income_stmt, {today}]
Source: {ir_url}

## Key Margins
| Metric | Value |
|--------|-------|
| EBITDA | {ebitda} |
| EBITDA Margin | {ebitda_margin} |
| Gross Margin | {gross_margins} |
| Operating Margin | {operating_margins} |
| Net Margin | {profit_margins} |

**Margin Zone:** {margin_zone}
[FACT — Yahoo Finance, {today}]

## Balance Sheet Highlights
- **Total Assets:** {total_assets}
- **Total Debt:** {total_debt}
- **Cash:** {cash}
[FACT — Yahoo Finance balance_sheet, {today}]

## Analyst Consensus
- **Rating:** {analyst}
- **Mean Score:** {analyst_mean}/5
- **Analyst Count:** {analyst_count}
- **Median Price Target:** {target_median}
- **Breakdown:** {rec_summary}
[FACT — Yahoo Finance recommendations, {today}]
Source: https://finance.yahoo.com/quote/{ticker_sym}

## Recent News
{chr(10).join(news_items)}

## ROI Estimate
Run: `python3 calculate-roi.py <workspace-dir>`
(Uses this file as input for the ROI calculation)
"""

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, '08-financial-profile.md')
    with open(out_path, 'w') as f:
        f.write(output)

    print(json.dumps({
        'status': 'success',
        'ticker': ticker_sym,
        'company': company_name,
        'output_file': out_path,
        'size_bytes': os.path.getsize(out_path),
        'revenue_ttm': revenue_ttm,
        'margin_zone': margin_zone,
        'analyst_consensus': analyst
    }, indent=2))

if __name__ == '__main__':
    main()
