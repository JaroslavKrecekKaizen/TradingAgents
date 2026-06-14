"""Resolve ISINs to Yahoo Finance tickers via yf.Search.

UK OEICs and SICAV funds are not exchange-traded, so they lack standard
tickers. Yahoo Finance indexes many of them under Morningstar-derived IDs
(e.g. 0P0000SY4N.L). This module searches by ISIN and caches the mapping
so subsequent calls skip the network round trip.
"""

import json
import logging
import os
import re

import yfinance as yf

from .config import get_config
from .symbol_utils import NoMarketDataError

logger = logging.getLogger(__name__)

_ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{10}$")

CACHE_FILENAME = "isin_ticker_cache.json"


def is_isin(value: str) -> bool:
    return bool(_ISIN_RE.match(value.strip().upper()))


def _load_cache() -> dict[str, str]:
    config = get_config()
    cache_dir = config["data_cache_dir"]
    path = os.path.join(cache_dir, CACHE_FILENAME)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict[str, str]) -> None:
    config = get_config()
    cache_dir = config["data_cache_dir"]
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, CACHE_FILENAME)
    with open(path, "w") as f:
        json.dump(cache, f, indent=2)


def resolve_isin(isin: str) -> str:
    """Resolve an ISIN to a Yahoo Finance ticker symbol.

    Returns the Yahoo ticker string (e.g. '0P0000SY4N.L').
    Raises NoMarketDataError if the ISIN cannot be resolved.
    """
    isin = isin.strip().upper()
    if not _ISIN_RE.match(isin):
        raise ValueError(f"Invalid ISIN format: {isin}")

    cache = _load_cache()
    if isin in cache:
        logger.info(f"ISIN {isin} resolved from cache: {cache[isin]}")
        return cache[isin]

    search = yf.Search(isin)
    if not search.quotes:
        raise NoMarketDataError(
            isin, isin, "Yahoo Finance search returned no results for this ISIN"
        )

    ticker = search.quotes[0]["symbol"]
    name = search.quotes[0].get("longname", "")
    logger.info(f"ISIN {isin} resolved to {ticker} ({name})")

    cache[isin] = ticker
    _save_cache(cache)

    return ticker
