#!/usr/bin/env -S .venv/bin/python
"""Fetch ticker-specific and global macro news.

Usage: python scripts/fetch_news.py <ticker> <date>
Example: python scripts/fetch_news.py VUKG.L 2026-06-13

Outputs structured text to stdout for consumption by Claude Code skills.
"""

import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

sys.path.insert(0, ".")

from tradingagents.dataflows.yfinance_news import get_news_yfinance, get_global_news_yfinance
from tradingagents.dataflows.symbol_utils import normalize_symbol, is_isin

NEWS_LOOKBACK_DAYS = 7


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/fetch_news.py <ticker|ISIN> <date>", file=sys.stderr)
        sys.exit(1)

    ticker = sys.argv[1]
    curr_date = sys.argv[2]

    if is_isin(ticker):
        ticker = normalize_symbol(ticker)

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_date = (curr_dt - relativedelta(days=NEWS_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    # Ticker-specific news
    print("=" * 60)
    print(f"TICKER NEWS: {ticker} ({start_date} to {curr_date})")
    print("=" * 60)
    try:
        news = get_news_yfinance(ticker, start_date, curr_date)
        print(news)
    except Exception as e:
        print(f"Error fetching ticker news: {e}", file=sys.stderr)
        print(f"<ticker news unavailable: {e}>")

    # Global macro news
    print()
    print("=" * 60)
    print(f"GLOBAL MACRO NEWS (past {NEWS_LOOKBACK_DAYS} days)")
    print("=" * 60)
    try:
        global_news = get_global_news_yfinance(curr_date, look_back_days=NEWS_LOOKBACK_DAYS)
        print(global_news)
    except Exception as e:
        print(f"Error fetching global news: {e}", file=sys.stderr)
        print(f"<global news unavailable: {e}>")


if __name__ == "__main__":
    main()
