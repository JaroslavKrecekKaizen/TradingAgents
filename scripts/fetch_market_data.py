#!/usr/bin/env -S .venv/bin/python
"""Fetch OHLCV data, technical indicators, and a verified market snapshot for a ticker.

Usage: python scripts/fetch_market_data.py <ticker> <date>
Example: python scripts/fetch_market_data.py VUKG.L 2026-06-13

Outputs structured text to stdout for consumption by Claude Code skills.
"""

import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

sys.path.insert(0, ".")

from tradingagents.dataflows.y_finance import (
    get_YFin_data_online,
    get_stock_stats_indicators_window,
)
from tradingagents.dataflows.market_data_validator import build_verified_market_snapshot

INDICATORS = ["rsi", "macd", "macdh", "boll", "boll_ub", "boll_lb", "close_50_sma", "atr"]
OHLCV_LOOKBACK_DAYS = 60
INDICATOR_LOOKBACK_DAYS = 30


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/fetch_market_data.py <ticker> <date>", file=sys.stderr)
        sys.exit(1)

    ticker = sys.argv[1]
    curr_date = sys.argv[2]

    curr_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_date = (curr_dt - relativedelta(days=OHLCV_LOOKBACK_DAYS)).strftime("%Y-%m-%d")

    # OHLCV price data
    print("=" * 60)
    print(f"OHLCV DATA: {ticker} ({start_date} to {curr_date})")
    print("=" * 60)
    try:
        ohlcv = get_YFin_data_online(ticker, start_date, curr_date)
        print(ohlcv)
    except Exception as e:
        print(f"Error fetching OHLCV: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not fetch OHLCV for {ticker}")

    # Technical indicators
    print()
    print("=" * 60)
    print(f"TECHNICAL INDICATORS: {ticker}")
    print("=" * 60)
    for ind in INDICATORS:
        try:
            result = get_stock_stats_indicators_window(
                ticker, ind, curr_date, INDICATOR_LOOKBACK_DAYS
            )
            print(result)
            print()
        except Exception as e:
            print(f"Error fetching {ind}: {e}", file=sys.stderr)
            print(f"{ind}: NO_DATA_AVAILABLE")
            print()

    # Verified market snapshot
    print("=" * 60)
    print(f"VERIFIED MARKET SNAPSHOT: {ticker}")
    print("=" * 60)
    try:
        snapshot = build_verified_market_snapshot(ticker, curr_date)
        print(snapshot)
    except Exception as e:
        print(f"Error building snapshot: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not build verified snapshot for {ticker}")


if __name__ == "__main__":
    main()
