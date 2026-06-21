#!/usr/bin/env -S .venv/bin/python
"""Fetch ticker-specific and global macro news.

Usage: python scripts/fetch_news.py <ticker> <date>
Example: python scripts/fetch_news.py VUKG.L 2026-06-13

For UK assets in the registry, adds Google News RSS results (by fund name)
alongside the yfinance ticker news.

Outputs structured text to stdout for consumption by Claude Code skills.
"""

import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

sys.path.insert(0, ".")

from tradingagents.dataflows.fund_holdings import fetch_holdings_news
from tradingagents.dataflows.google_news import fetch_google_news
from tradingagents.dataflows.yfinance_news import get_news_yfinance, get_global_news_yfinance
from tradingagents.dataflows.symbol_utils import normalize_symbol, is_isin
from tradingagents.dataflows.uk_asset_registry import get_sentiment_meta

NEWS_LOOKBACK_DAYS = 7


def _section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/fetch_news.py <ticker|ISIN> <date>", file=sys.stderr)
        sys.exit(1)

    raw_input = sys.argv[1]
    curr_date = sys.argv[2]

    meta = get_sentiment_meta(raw_input)

    ticker = raw_input
    if is_isin(raw_input):
        ticker = normalize_symbol(raw_input)
        if meta is None:
            meta = get_sentiment_meta(ticker)

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_date = (curr_dt - relativedelta(days=NEWS_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    # Google News for UK assets (primary fund-specific news source)
    if meta is not None:
        all_queries = meta.search_names + meta.theme_keywords
        _section(f"GOOGLE NEWS: {meta.search_names[0]} ({ticker})")
        try:
            news = fetch_google_news(all_queries)
            print(news)
        except Exception as e:
            print(f"Error fetching Google News: {e}", file=sys.stderr)
            print(f"<Google News unavailable: {e}>")

    # Ticker-specific news (yfinance)
    _section(f"TICKER NEWS: {ticker} ({start_date} to {curr_date})")
    try:
        news = get_news_yfinance(ticker, start_date, curr_date)
        print(news)
    except Exception as e:
        print(f"Error fetching ticker news: {e}", file=sys.stderr)
        print(f"<ticker news unavailable: {e}>")

    # Holdings-derived news for funds/ETFs
    if meta is not None:
        _section(f"TOP HOLDINGS NEWS: {ticker}")
        try:
            holdings_news = fetch_holdings_news(ticker, start_date, curr_date)
            print(holdings_news)
        except Exception as e:
            print(f"Error fetching holdings news: {e}", file=sys.stderr)
            print(f"<holdings news unavailable: {e}>")

    # Global macro news
    _section(f"GLOBAL MACRO NEWS (past {NEWS_LOOKBACK_DAYS} days)")
    try:
        global_news = get_global_news_yfinance(curr_date, look_back_days=NEWS_LOOKBACK_DAYS)
        print(global_news)
    except Exception as e:
        print(f"Error fetching global news: {e}", file=sys.stderr)
        print(f"<global news unavailable: {e}>")


if __name__ == "__main__":
    main()
