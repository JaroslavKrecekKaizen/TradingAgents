"""ApeWisdom REST API fetcher for aggregated Reddit + 4chan sentiment.

ApeWisdom (apewisdom.io) tracks ticker mentions and upvotes across ~30
Reddit boards (r/wallstreetbets, r/stocks, r/investing, etc.) plus
4chan /biz. The API is free, requires no authentication, and returns
clean JSON with rank, mention counts, upvotes, and 24-hour deltas.

For UK assets, we query by US proxy tickers (e.g. GLD for PHGP.L)
since ApeWisdom tracks US tickers. The data shows whether the
theme/sector has retail buzz, not direct UK asset sentiment.
"""

from __future__ import annotations

import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_API = "https://apewisdom.io/api/v1.0/filter/all-stocks/page/{page}"
_UA = "tradingagents/0.2 (+https://github.com/TauricResearch/TradingAgents)"
_MAX_PAGES = 3


def fetch_apewisdom_mentions(
    tickers: list[str],
    timeout: float = 10.0,
) -> str:
    """Check if any of the given tickers appear in ApeWisdom's trending data.

    Scans the first few pages (300 tickers) of the all-stocks leaderboard.
    Returns a formatted plaintext block with rank, mentions, upvotes,
    and 24-hour deltas for any matches found.

    Returns a placeholder string on failure - never raises.
    """
    if not tickers:
        return "<no tickers provided for ApeWisdom lookup>"

    target = {t.upper() for t in tickers}
    found: list[dict] = []

    for page in range(1, _MAX_PAGES + 1):
        url = _API.format(page=page)
        req = Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
        try:
            with urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
        except (HTTPError, URLError, json.JSONDecodeError, TimeoutError) as exc:
            logger.warning("ApeWisdom fetch failed (page %d): %s", page, exc)
            if page == 1:
                return f"<ApeWisdom unavailable: {type(exc).__name__}>"
            break

        results = data.get("results", []) if isinstance(data, dict) else []
        if not results:
            break

        for entry in results:
            ticker = (entry.get("ticker") or "").upper()
            if ticker in target:
                found.append(entry)
                target.discard(ticker)

        if not target:
            break

    if not found:
        ticker_list = ", ".join(tickers)
        return (
            f"<no ApeWisdom mentions found for {ticker_list} "
            f"in top {_MAX_PAGES * 100} trending stocks>"
        )

    lines = [f"ApeWisdom Reddit/4chan buzz ({len(found)} proxy tickers found):", ""]
    for entry in sorted(found, key=lambda e: e.get("rank", 9999)):
        ticker = entry.get("ticker", "?")
        rank = entry.get("rank", "?")
        mentions = entry.get("mentions", 0)
        upvotes = entry.get("upvotes", 0)
        mentions_24h_ago = entry.get("mentions_24h_ago", 0)

        delta = mentions - mentions_24h_ago
        delta_str = f"+{delta}" if delta >= 0 else str(delta)

        lines.append(
            f"  #{rank} {ticker}: {mentions} mentions, "
            f"{upvotes} upvotes, 24h change: {delta_str} mentions"
        )

    return "\n".join(lines)
