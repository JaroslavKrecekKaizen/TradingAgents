#!/usr/bin/env -S .venv/bin/python
"""Fetch fund profile data: overview, top holdings, sector weights, asset allocation.

Usage: python scripts/fetch_fund_profile.py <ticker|ISIN> [<date>]
Example: python scripts/fetch_fund_profile.py IE00B5339C57 2026-06-13

Designed for OEIC/SICAV/mutual funds. Replaces fetch_fundamentals.py for
instruments that lack company financial statements.

Outputs structured text to stdout for consumption by Claude Code skills.
"""

import sys
from datetime import datetime

sys.path.insert(0, ".")

from tradingagents.dataflows.symbol_utils import normalize_symbol, is_isin, NoMarketDataError
from tradingagents.dataflows.stockstats_utils import yf_retry
import yfinance as yf


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch_fund_profile.py <ticker|ISIN> [<date>]", file=sys.stderr)
        sys.exit(1)

    raw_symbol = sys.argv[1]
    curr_date = sys.argv[2] if len(sys.argv) > 2 else None

    ticker = normalize_symbol(raw_symbol)

    # Fund overview from .info
    print("=" * 60)
    print(f"FUND OVERVIEW: {raw_symbol} (resolved: {ticker})")
    print("=" * 60)
    try:
        ticker_obj = yf.Ticker(ticker)
        info = yf_retry(lambda: ticker_obj.info)

        if not info:
            raise NoMarketDataError(raw_symbol, ticker, "no fund info returned")

        fields = [
            ("Name", info.get("longName")),
            ("Type", info.get("quoteType")),
            ("Currency", info.get("currency")),
            ("Exchange", info.get("fullExchangeName")),
            ("Morningstar Rating", info.get("morningStarOverallRating")),
            ("Morningstar Risk Rating", info.get("morningStarRiskRating")),
            ("Beta (3Y)", info.get("beta3Year")),
            ("52 Week High", info.get("fiftyTwoWeekHigh")),
            ("52 Week Low", info.get("fiftyTwoWeekLow")),
            ("50 Day Average", info.get("fiftyDayAverage")),
            ("200 Day Average", info.get("twoHundredDayAverage")),
            ("YTD Return", info.get("ytdReturn")),
            ("Trailing 3 Month Returns", info.get("trailingThreeMonthReturns")),
            ("Annual Holdings Turnover", info.get("annualHoldingsTurnover")),
            ("Previous Close", info.get("previousClose")),
            ("Current Price", info.get("regularMarketPrice")),
        ]

        header = f"# Fund Profile for {ticker}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        lines = [f"{label}: {value}" for label, value in fields if value is not None]

        if not lines:
            raise NoMarketDataError(raw_symbol, ticker, "no fund profile fields returned")

        print(header + "\n".join(lines))
    except NoMarketDataError:
        raise
    except Exception as e:
        print(f"Error fetching fund overview: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not fetch fund overview for {raw_symbol}")

    # Fund data (holdings, sectors, asset classes)
    try:
        fd = yf_retry(lambda: ticker_obj.get_funds_data())
    except Exception as e:
        print(f"Error fetching fund data: {e}", file=sys.stderr)
        fd = None

    # Top holdings
    print()
    print("=" * 60)
    print(f"TOP HOLDINGS: {ticker}")
    print("=" * 60)
    try:
        if fd is not None and fd.top_holdings is not None and not fd.top_holdings.empty:
            header = f"# Top {len(fd.top_holdings)} Holdings for {ticker}\n"
            header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            lines = []
            for sym, row in fd.top_holdings.iterrows():
                pct = row.get("Holding Percent", 0) * 100
                name = row.get("Name", sym)
                lines.append(f"| {sym} | {name} | {pct:.2f}% |")
            table = "| Ticker | Name | Weight |\n|---|---|---:|\n" + "\n".join(lines)
            print(header + table)
        else:
            print(f"NO_DATA_AVAILABLE: No holdings data for {ticker}")
    except Exception as e:
        print(f"Error fetching holdings: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not fetch holdings for {ticker}")

    # Sector weightings
    print()
    print("=" * 60)
    print(f"SECTOR WEIGHTINGS: {ticker}")
    print("=" * 60)
    try:
        if fd is not None and fd.sector_weightings:
            header = f"# Sector Weightings for {ticker}\n"
            header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            lines = []
            for sector, weight in sorted(fd.sector_weightings.items(), key=lambda x: -x[1]):
                if weight > 0:
                    lines.append(f"| {sector.replace('_', ' ').title()} | {weight * 100:.1f}% |")
            if lines:
                table = "| Sector | Weight |\n|---|---:|\n" + "\n".join(lines)
                print(header + table)
            else:
                print(f"NO_DATA_AVAILABLE: No sector weightings for {ticker}")
        else:
            print(f"NO_DATA_AVAILABLE: No sector weightings for {ticker}")
    except Exception as e:
        print(f"Error fetching sector weightings: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not fetch sector weightings for {ticker}")

    # Asset allocation
    print()
    print("=" * 60)
    print(f"ASSET ALLOCATION: {ticker}")
    print("=" * 60)
    try:
        if fd is not None and fd.asset_classes:
            header = f"# Asset Allocation for {ticker}\n"
            header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            label_map = {
                "cashPosition": "Cash",
                "stockPosition": "Stocks",
                "bondPosition": "Bonds",
                "preferredPosition": "Preferred",
                "convertiblePosition": "Convertible",
                "otherPosition": "Other",
            }
            lines = []
            for key, label in label_map.items():
                weight = fd.asset_classes.get(key, 0)
                if weight and weight > 0:
                    lines.append(f"| {label} | {weight * 100:.1f}% |")
            if lines:
                table = "| Asset Class | Weight |\n|---|---:|\n" + "\n".join(lines)
                print(header + table)
            else:
                print(f"NO_DATA_AVAILABLE: No asset allocation for {ticker}")
        else:
            print(f"NO_DATA_AVAILABLE: No asset allocation for {ticker}")
    except Exception as e:
        print(f"Error fetching asset allocation: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not fetch asset allocation for {ticker}")

    # Equity holdings metrics
    print()
    print("=" * 60)
    print(f"PORTFOLIO METRICS: {ticker}")
    print("=" * 60)
    try:
        if fd is not None and fd.equity_holdings is not None and not fd.equity_holdings.empty:
            header = f"# Portfolio Metrics for {ticker}\n"
            header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            lines = []
            for metric, row in fd.equity_holdings.iterrows():
                value = row.iloc[0]
                if value is not None and str(value) != "<NA>":
                    lines.append(f"{metric}: {value}")
            if lines:
                print(header + "\n".join(lines))
            else:
                print(f"NO_DATA_AVAILABLE: No portfolio metrics for {ticker}")
        else:
            print(f"NO_DATA_AVAILABLE: No portfolio metrics for {ticker}")
    except Exception as e:
        print(f"Error fetching portfolio metrics: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not fetch portfolio metrics for {ticker}")

    # Fund description
    print()
    print("=" * 60)
    print(f"FUND DESCRIPTION: {ticker}")
    print("=" * 60)
    try:
        if fd is not None and fd.description:
            print(fd.description)
        elif fd is not None and fd.fund_overview:
            overview = fd.fund_overview
            lines = []
            if overview.get("family"):
                lines.append(f"Fund Family: {overview['family']}")
            if overview.get("categoryName"):
                lines.append(f"Category: {overview['categoryName']}")
            if overview.get("legalType"):
                lines.append(f"Legal Type: {overview['legalType']}")
            if lines:
                print("\n".join(lines))
            else:
                print(f"NO_DATA_AVAILABLE: No fund description for {ticker}")
        else:
            print(f"NO_DATA_AVAILABLE: No fund description for {ticker}")
    except Exception as e:
        print(f"Error fetching fund description: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not fetch fund description for {ticker}")


if __name__ == "__main__":
    main()
