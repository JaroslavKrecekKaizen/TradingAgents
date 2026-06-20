#!/usr/bin/env -S .venv/bin/python
"""Fetch sentiment data: news headlines, StockTwits messages, and Reddit posts.

Usage: python scripts/fetch_sentiment.py <ticker> <date>
Example: python scripts/fetch_sentiment.py AAPL 2026-06-13

For UK assets in the registry, routes to UK-specific sources: Google News
RSS (by fund name), StockTwits (US proxy), ApeWisdom (Reddit/4chan buzz),
and Reddit (UK + global subreddits by fund name/theme).

Outputs structured text to stdout for consumption by Claude Code skills.
"""

import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

sys.path.insert(0, ".")

from tradingagents.dataflows.apewisdom import fetch_apewisdom_mentions
from tradingagents.dataflows.google_news import fetch_google_news
from tradingagents.dataflows.reddit import DEFAULT_SUBREDDITS, fetch_reddit_posts
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
    """UK asset pipeline: Google News + StockTwits proxy + ApeWisdom + Reddit UK/global."""

    # Google News (primary UK source - searched by fund name)
    _section(f"GOOGLE NEWS: {meta.search_names[0]} ({ticker})")
    try:
        news = fetch_google_news(meta.search_names)
        print(news)
    except Exception as e:
        print(f"Error fetching Google News: {e}", file=sys.stderr)
        print(f"<Google News unavailable: {e}>")

    # StockTwits via US proxy (labelled as proxy)
    if meta.us_proxy:
        _section(f"STOCKTWITS (US PROXY via {meta.us_proxy} for {ticker})")
        try:
            stocktwits = fetch_stocktwits_messages(meta.us_proxy, limit=30)
            print(stocktwits)
        except Exception as e:
            print(f"Error fetching StockTwits proxy: {e}", file=sys.stderr)
            print(f"<StockTwits proxy unavailable: {e}>")

    # ApeWisdom Reddit/4chan buzz for proxy ticker
    if meta.us_proxy:
        _section(f"APEWISDOM (US PROXY BUZZ): {meta.us_proxy} trending on Reddit/4chan?")
        try:
            apewisdom = fetch_apewisdom_mentions([meta.us_proxy])
            print(apewisdom)
        except Exception as e:
            print(f"Error fetching ApeWisdom: {e}", file=sys.stderr)
            print(f"<ApeWisdom unavailable: {e}>")

    # Reddit UK subreddits (searched by fund name)
    _section(
        f"REDDIT (UK): {ticker} via "
        + ", ".join(f"r/{s}" for s in meta.uk_subreddits)
    )
    try:
        reddit_uk = fetch_reddit_posts(
            ticker,
            subreddits=meta.uk_subreddits,
            search_query=meta.search_names[0],
        )
        print(reddit_uk)
    except Exception as e:
        print(f"Error fetching Reddit UK: {e}", file=sys.stderr)
        print(f"<Reddit UK unavailable: {e}>")

    # Reddit global subreddits (searched by theme keywords)
    if meta.theme_keywords:
        theme_query = meta.theme_keywords[0]
        _section(f"REDDIT (GLOBAL): {theme_query} themes")
        try:
            reddit_global = fetch_reddit_posts(
                ticker,
                subreddits=DEFAULT_SUBREDDITS,
                search_query=theme_query,
            )
            print(reddit_global)
        except Exception as e:
            print(f"Error fetching Reddit global: {e}", file=sys.stderr)
            print(f"<Reddit global unavailable: {e}>")


def _fetch_default_sentiment(ticker: str, curr_date: str, start_date: str) -> None:
    """Default US-style pipeline: yfinance news + StockTwits + Reddit."""

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

    # Reddit posts
    _section(f"REDDIT: {ticker}")
    try:
        reddit = fetch_reddit_posts(ticker)
        print(reddit)
    except Exception as e:
        print(f"Error fetching Reddit: {e}", file=sys.stderr)
        print(f"<reddit unavailable: {e}>")


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
