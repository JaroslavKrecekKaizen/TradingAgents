#!/usr/bin/env -S .venv/bin/python
"""Fetch fundamental data: company overview, balance sheet, cash flow, income statement.

Usage: python scripts/fetch_fundamentals.py <ticker> [<date>]
Example: python scripts/fetch_fundamentals.py AAPL 2026-06-13

Date is optional; when provided, financial statements are filtered to exclude
periods after that date (prevents look-ahead bias in backtesting).

Outputs structured text to stdout for consumption by Claude Code skills.
"""

import sys

sys.path.insert(0, ".")

from tradingagents.dataflows.y_finance import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch_fundamentals.py <ticker> [<date>]", file=sys.stderr)
        sys.exit(1)

    ticker = sys.argv[1]
    curr_date = sys.argv[2] if len(sys.argv) > 2 else None

    # Company overview
    print("=" * 60)
    print(f"COMPANY FUNDAMENTALS: {ticker}")
    print("=" * 60)
    try:
        fundamentals = get_fundamentals(ticker, curr_date)
        print(fundamentals)
    except Exception as e:
        print(f"Error fetching fundamentals: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not fetch fundamentals for {ticker}")

    # Balance sheet (quarterly)
    print()
    print("=" * 60)
    print(f"BALANCE SHEET (quarterly): {ticker}")
    print("=" * 60)
    try:
        balance = get_balance_sheet(ticker, "quarterly", curr_date)
        print(balance)
    except Exception as e:
        print(f"Error fetching balance sheet: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not fetch balance sheet for {ticker}")

    # Cash flow (quarterly)
    print()
    print("=" * 60)
    print(f"CASH FLOW (quarterly): {ticker}")
    print("=" * 60)
    try:
        cashflow = get_cashflow(ticker, "quarterly", curr_date)
        print(cashflow)
    except Exception as e:
        print(f"Error fetching cash flow: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not fetch cash flow for {ticker}")

    # Income statement (quarterly)
    print()
    print("=" * 60)
    print(f"INCOME STATEMENT (quarterly): {ticker}")
    print("=" * 60)
    try:
        income = get_income_statement(ticker, "quarterly", curr_date)
        print(income)
    except Exception as e:
        print(f"Error fetching income statement: {e}", file=sys.stderr)
        print(f"NO_DATA_AVAILABLE: Could not fetch income statement for {ticker}")


if __name__ == "__main__":
    main()
