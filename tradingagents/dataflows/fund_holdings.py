"""Fund holdings enrichment - news and sentiment for top underlying holdings.

Fetches top holdings from yfinance fund data, then gathers yfinance news
and StockTwits sentiment for the underlying stocks. Returns formatted
plaintext blocks ready for prompt injection.

Designed for ETFs and UCITS funds where the fund wrapper itself has no
yfinance news coverage but the underlying large-cap holdings do.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional

import yfinance as yf

from .stockstats_utils import yf_retry
from .stocktwits import fetch_stocktwits_messages
from .yfinance_news import get_news_yfinance

logger = logging.getLogger(__name__)


def _strip_exchange_suffix(symbol: str) -> str:
    """Strip exchange suffix for StockTwits lookups (.L, .AX, .TO, etc.)."""
    if "." in symbol:
        base = symbol.split(".")[0]
        if base:
            return base
    return symbol


def _get_top_holdings(ticker: str, limit: int = 5) -> list[dict]:
    """Fetch top holdings from yfinance fund data.

    Returns a list of dicts with keys: symbol, name, weight.
    Returns empty list if fund data is unavailable.
    """
    try:
        fd = yf_retry(lambda: yf.Ticker(ticker).get_funds_data())
        if fd is None or fd.top_holdings is None or fd.top_holdings.empty:
            return []

        holdings = []
        for sym, row in fd.top_holdings.head(limit).iterrows():
            if not sym or sym == "N/A":
                continue
            holdings.append({
                "symbol": str(sym),
                "name": row.get("Name", sym),
                "weight": round((row.get("Holding Percent", 0) or 0) * 100, 2),
            })
        return holdings
    except Exception as e:
        logger.warning("Failed to fetch holdings for %s: %s", ticker, e)
        return []


def fetch_holdings_news(
    ticker: str,
    start_date: str,
    end_date: str,
    max_holdings: int = 5,
) -> str:
    """Fetch yfinance news for a fund's top holdings.

    Returns a formatted plaintext block with news grouped by holding,
    or a placeholder if no holdings data is available.
    """
    holdings = _get_top_holdings(ticker, limit=max_holdings)
    if not holdings:
        return f"<no holdings data available for {ticker} - cannot fetch holdings news>"

    weight_summary = ", ".join(
        f"{h['symbol']} ({h['weight']}%)" for h in holdings
    )
    blocks = [
        f"Holdings-derived news for {ticker} top {len(holdings)}: {weight_summary}",
        "",
    ]

    total_articles = 0
    for h in holdings:
        sym = h["symbol"]
        try:
            news = get_news_yfinance(sym, start_date, end_date)
        except Exception as e:
            news = f"<news unavailable for {sym}: {e}>"

        has_articles = not news.startswith("No news found") and not news.startswith("Error")
        if has_articles:
            total_articles += 1

        blocks.append(f"--- {sym} ({h['name']}, {h['weight']}% of fund) ---")
        blocks.append(news)
        blocks.append("")

    if total_articles == 0:
        blocks.append(
            f"Note: no yfinance articles found for any of {ticker}'s top holdings."
        )

    return "\n".join(blocks)


def fetch_holdings_sentiment(
    ticker: str,
    max_holdings: int = 3,
    msgs_per_holding: int = 10,
) -> str:
    """Fetch StockTwits sentiment for a fund's top holdings.

    Returns a formatted plaintext block with sentiment per holding,
    or a placeholder if no holdings data is available.
    """
    holdings = _get_top_holdings(ticker, limit=max_holdings)
    if not holdings:
        return f"<no holdings data available for {ticker} - cannot fetch holdings sentiment>"

    weight_summary = ", ".join(
        f"{h['symbol']} ({h['weight']}%)" for h in holdings
    )
    blocks = [
        f"Holdings-derived sentiment for {ticker} top {len(holdings)}: {weight_summary}",
        "",
    ]

    for i, h in enumerate(holdings):
        sym = h["symbol"]
        st_sym = _strip_exchange_suffix(sym)
        if i > 0:
            time.sleep(0.3)
        try:
            sentiment = fetch_stocktwits_messages(st_sym, limit=msgs_per_holding)
        except Exception as e:
            sentiment = f"<StockTwits unavailable for {st_sym}: {e}>"

        blocks.append(f"--- {sym} ({h['name']}, {h['weight']}% of fund) ---")
        blocks.append(sentiment)
        blocks.append("")

    return "\n".join(blocks)
