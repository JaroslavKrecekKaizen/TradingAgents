#!/usr/bin/env -S .venv/bin/python
"""Fetch sentiment data: news headlines, StockTwits messages, and Reddit posts.

Usage: python scripts/fetch_sentiment.py <ticker> <date>
Example: python scripts/fetch_sentiment.py AAPL 2026-06-13

Outputs structured text to stdout for consumption by Claude Code skills.
"""

import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

sys.path.insert(0, ".")

from tradingagents.dataflows.yfinance_news import get_news_yfinance
from tradingagents.dataflows.stocktwits import fetch_stocktwits_messages
from tradingagents.dataflows.reddit import fetch_reddit_posts

NEWS_LOOKBACK_DAYS = 7


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/fetch_sentiment.py <ticker> <date>", file=sys.stderr)
        sys.exit(1)

    ticker = sys.argv[1]
    curr_date = sys.argv[2]

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_date = (curr_dt - relativedelta(days=NEWS_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    # News headlines (institutional framing)
    print("=" * 60)
    print(f"NEWS HEADLINES: {ticker} ({start_date} to {curr_date})")
    print("=" * 60)
    try:
        news = get_news_yfinance(ticker, start_date, curr_date)
        print(news)
    except Exception as e:
        print(f"Error fetching news: {e}", file=sys.stderr)
        print(f"<news unavailable: {e}>")

    # StockTwits messages (retail sentiment)
    print()
    print("=" * 60)
    print(f"STOCKTWITS: {ticker}")
    print("=" * 60)
    try:
        stocktwits = fetch_stocktwits_messages(ticker, limit=30)
        print(stocktwits)
    except Exception as e:
        print(f"Error fetching StockTwits: {e}", file=sys.stderr)
        print(f"<stocktwits unavailable: {e}>")

    # Reddit posts
    print()
    print("=" * 60)
    print(f"REDDIT: {ticker}")
    print("=" * 60)
    try:
        reddit = fetch_reddit_posts(ticker)
        print(reddit)
    except Exception as e:
        print(f"Error fetching Reddit: {e}", file=sys.stderr)
        print(f"<reddit unavailable: {e}>")


if __name__ == "__main__":
    main()
