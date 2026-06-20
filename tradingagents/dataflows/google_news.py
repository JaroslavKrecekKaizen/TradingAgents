"""Google News RSS fetcher for UK fund/ETF sentiment data.

Queries Google News by fund name (the only search key that reliably
returns articles for UK-listed assets) and returns formatted plaintext
blocks ready for prompt injection.

Uses the public RSS endpoint with en-GB locale and UK region to bias
toward UK financial media. No API key required.
"""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_RSS_URL = (
    "https://news.google.com/rss/search?"
    "q={query}+when:7d&hl=en-GB&gl=GB&ceid=GB:en"
)
_UA = "tradingagents/0.2 (+https://github.com/TauricResearch/TradingAgents)"


def _parse_rss(xml_bytes: bytes, limit: int) -> list[dict]:
    """Parse a Google News RSS response into a list of article dicts."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        logger.warning("Google News RSS parse error: %s", exc)
        return []

    channel = root.find("channel")
    if channel is None:
        return []

    articles = []
    for item in channel.findall("item")[:limit]:
        title = (item.findtext("title") or "").strip()
        source = (item.findtext("source") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()

        if not title:
            continue

        articles.append({
            "title": title,
            "source": source,
            "link": link,
            "pub_date": pub_date,
        })

    return articles


def _format_articles(articles: list[dict], query: str) -> str:
    """Format parsed articles into plaintext lines."""
    if not articles:
        return f"<no Google News articles found for '{query}'>"

    lines = [f"Google News: {len(articles)} articles for '{query}'", ""]
    for a in articles:
        source_tag = f" [{a['source']}]" if a["source"] else ""
        date_tag = f" ({a['pub_date']})" if a["pub_date"] else ""
        lines.append(f"  {a['title']}{source_tag}{date_tag}")

    return "\n".join(lines)


def fetch_google_news(
    search_names: list[str],
    limit: int = 20,
    timeout: float = 10.0,
    inter_query_delay: float = 1.0,
) -> str:
    """Fetch Google News articles for a UK asset using fund name queries.

    Accepts multiple search name variants (e.g. full fund name and short
    name), deduplicates articles by title across queries, and returns a
    formatted plaintext block.

    Returns a placeholder string on failure - never raises.
    """
    if not search_names:
        return "<no search names provided for Google News>"

    seen_titles: set[str] = set()
    all_articles: list[dict] = []
    errors = 0

    for i, name in enumerate(search_names):
        if i > 0:
            time.sleep(inter_query_delay)

        url = _RSS_URL.format(query=quote_plus(name))
        req = Request(url, headers={"User-Agent": _UA})

        try:
            with urlopen(req, timeout=timeout) as resp:
                articles = _parse_rss(resp.read(), limit)
        except (HTTPError, URLError, TimeoutError) as exc:
            logger.warning("Google News fetch failed for '%s': %s", name, exc)
            errors += 1
            continue

        for a in articles:
            title_key = a["title"].lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                all_articles.append(a)

    if not all_articles:
        if errors == len(search_names):
            return "<Google News unavailable: all queries failed>"
        return (
            f"<no Google News articles found for "
            f"{', '.join(repr(n) for n in search_names)}>"
        )

    all_articles = all_articles[:limit]
    combined_query = " / ".join(search_names)
    return _format_articles(all_articles, combined_query)
