#!/usr/bin/env -S .venv/bin/python
"""Fetch sentiment data: news headlines, StockTwits messages, and holdings sentiment.

Usage: python scripts/fetch_sentiment.py <ticker> <date>
Example: python scripts/fetch_sentiment.py AAPL 2026-06-13

For UK assets in the registry, routes to UK-specific sources: Google News
RSS (by fund name + theme keywords), StockTwits (US proxy + top holdings),
and holdings-derived sentiment.

Outputs structured text to stdout for consumption by Claude Code skills.
"""

import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

sys.path.insert(0, ".")

from tradingagents.dataflows.fund_holdings import fetch_holdings_sentiment
from tradingagents.dataflows.google_news import fetch_google_news
from tradingagents.dataflows.stocktwits import fetch_stocktwits_messages
from tradingagents.dataflows.symbol_utils import normalize_symbol, is_isin
from tradingagents.dataflows.uk_asset_registry import get_sentiment_meta
from tradingagents.dataflows.yfinance_news import get_news_yfinance

NEWS_LOOKBACK_DAYS = 7


def _section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def _fetch_uk_sentiment(ticker: str, meta, curr_date: str, start_date: str) -> None:
    """UK asset pipeline: Google News + StockTwits proxy + holdings sentiment."""

    # Google News (primary UK source - searched by fund name + theme keywords)
    all_queries = meta.search_names + meta.theme_keywords
    _section(f"GOOGLE NEWS: {meta.search_names[0]} ({ticker})")
    try:
        news = fetch_google_news(all_queries)
        print(news)
    except Exception as e:
        print(f"Error fetching Google News: {e}", file=sys.stderr)
        print(f"<Google News unavailable: {e}>")

    # StockTwits via US proxy (sector-level sentiment)
    if meta.us_proxy:
        _section(f"STOCKTWITS (US PROXY via {meta.us_proxy} for {ticker})")
        try:
            stocktwits = fetch_stocktwits_messages(meta.us_proxy, limit=30)
            print(stocktwits)
        except Exception as e:
            print(f"Error fetching StockTwits proxy: {e}", file=sys.stderr)
            print(f"<StockTwits proxy unavailable: {e}>")

    # StockTwits for top underlying holdings (direct sentiment)
    _section(f"STOCKTWITS (TOP HOLDINGS): {ticker}")
    try:
        holdings_sentiment = fetch_holdings_sentiment(ticker, max_holdings=3, msgs_per_holding=10)
        print(holdings_sentiment)
    except Exception as e:
        print(f"Error fetching holdings sentiment: {e}", file=sys.stderr)
        print(f"<holdings sentiment unavailable: {e}>")


def _fetch_default_sentiment(ticker: str, curr_date: str, start_date: str) -> None:
    """Default US-style pipeline: yfinance news + StockTwits."""

    # News headlines (institutional framing)
    _section(f"NEWS HEADLINES: {ticker} ({start_date} to {curr_date})")
    try:
        news = get_news_yfinance(ticker, start_date, curr_date)
        print(news)
    except Exception as e:
        print(f"Error fetching news: {e}", file=sys.stderr)
        print(f"<news unavailable: {e}>")

    # StockTwits messages (retail sentiment)
    _section(f"STOCKTWITS: {ticker}")
    try:
        stocktwits = fetch_stocktwits_messages(ticker, limit=30)
        print(stocktwits)
    except Exception as e:
        print(f"Error fetching StockTwits: {e}", file=sys.stderr)
        print(f"<stocktwits unavailable: {e}>")


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/fetch_sentiment.py <ticker|ISIN> <date>", file=sys.stderr)
        sys.exit(1)

    raw_input = sys.argv[1]
    curr_date = sys.argv[2]

    # Try registry lookup with original input first (ISIN or ticker)
    meta = get_sentiment_meta(raw_input)

    # Resolve ISIN to ticker for display/fallback
    ticker = raw_input
    if is_isin(raw_input):
        ticker = normalize_symbol(raw_input)
        if meta is None:
            meta = get_sentiment_meta(ticker)

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_date = (curr_dt - relativedelta(days=NEWS_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    if meta is not None:
        _fetch_uk_sentiment(ticker, meta, curr_date, start_date)
    else:
        _fetch_default_sentiment(ticker, curr_date, start_date)


if __name__ == "__main__":
    main()
