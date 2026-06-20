#!/usr/bin/env -S .venv/bin/python
"""Detect instrument type (ETF, MUTUALFUND, EQUITY) via yfinance.

Usage: python scripts/detect_instrument_type.py <ticker|ISIN>
Prints the quoteType to stdout. Prints UNKNOWN on failure.
"""

import sys

sys.path.insert(0, ".")

from tradingagents.dataflows.symbol_utils import normalize_symbol, is_isin
from tradingagents.dataflows.stockstats_utils import yf_retry
import yfinance as yf


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/detect_instrument_type.py <ticker|ISIN>", file=sys.stderr)
        sys.exit(1)

    raw_symbol = sys.argv[1]
    ticker = normalize_symbol(raw_symbol) if is_isin(raw_symbol) else raw_symbol

    try:
        info = yf_retry(lambda: yf.Ticker(ticker).info)
        quote_type = info.get("quoteType", "UNKNOWN") if info else "UNKNOWN"
        print(quote_type)
    except Exception:
        print("UNKNOWN")


if __name__ == "__main__":
    main()
