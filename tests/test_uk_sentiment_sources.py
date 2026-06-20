"""Tests for UK sentiment data pipeline components."""

import json
from unittest.mock import MagicMock, patch

import pytest

from tradingagents.dataflows.uk_asset_registry import (
    AssetSentimentMeta,
    get_sentiment_meta,
)
from tradingagents.dataflows.google_news import fetch_google_news, _parse_rss
from tradingagents.dataflows.apewisdom import fetch_apewisdom_mentions
from tradingagents.dataflows.reddit import fetch_reddit_posts


# --- UK Asset Registry ---


class TestAssetRegistry:
    def test_lookup_by_ticker(self):
        meta = get_sentiment_meta("VUKG.L")
        assert meta is not None
        assert meta.us_proxy == "ISF"
        assert "Vanguard FTSE 100" in meta.search_names[0]

    def test_lookup_by_isin(self):
        meta = get_sentiment_meta("GB00BFNHP716")
        assert meta is not None
        assert meta.us_proxy == "ISF"

    def test_lookup_by_resolved_morningstar_ticker(self):
        meta = get_sentiment_meta("0P0000SY4N.L")
        assert meta is not None
        assert meta.us_proxy == "KIE"
        assert meta.asset_type == "oeic"

    def test_lookup_by_sedol_as_ticker(self):
        meta = get_sentiment_meta("B0CNH16")
        assert meta is not None
        assert meta.us_proxy == "QQQ"

    def test_lookup_case_insensitive(self):
        meta = get_sentiment_meta("vukg.l")
        assert meta is not None
        assert meta.us_proxy == "ISF"

    def test_unknown_asset_returns_none(self):
        assert get_sentiment_meta("AAPL") is None
        assert get_sentiment_meta("UNKNOWN") is None

    def test_all_holdings_have_search_names(self):
        tickers = [
            "VUKG.L", "VWRP.L", "VFEG.L", "VJPB.L",
            "GB00B41XG308",
            "GB00B0CNH163", "LU1033663649",
            "PHGP.L", "SGLP.L",
            "GB0031919235", "IE00B5339C57", "GB00BF0TZG22", "GB00BHZK8D21",
            "DFNG.L", "WDEP.L", "WREE.L", "URNG.L",
        ]
        for t in tickers:
            meta = get_sentiment_meta(t)
            assert meta is not None, f"Missing registry entry for {t}"
            assert len(meta.search_names) >= 1, f"No search names for {t}"
            assert meta.us_proxy is not None, f"No US proxy for {t}"

    def test_uk_subreddits_default(self):
        meta = get_sentiment_meta("VUKG.L")
        assert "UKPersonalFinance" in meta.uk_subreddits


# --- Google News RSS ---


SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Vanguard FTSE 100 - Google News</title>
    <item>
      <title>FTSE 100 hits record high</title>
      <source url="https://www.ft.com">Financial Times</source>
      <link>https://news.google.com/rss/articles/abc123</link>
      <pubDate>Fri, 20 Jun 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Vanguard ETF inflows surge</title>
      <source url="https://www.reuters.com">Reuters</source>
      <link>https://news.google.com/rss/articles/def456</link>
      <pubDate>Thu, 19 Jun 2026 08:30:00 GMT</pubDate>
    </item>
    <item>
      <title>FTSE 100 hits record high</title>
      <source url="https://www.bbc.co.uk">BBC</source>
      <link>https://news.google.com/rss/articles/ghi789</link>
      <pubDate>Fri, 20 Jun 2026 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""


class TestGoogleNews:
    def test_parse_rss_extracts_articles(self):
        articles = _parse_rss(SAMPLE_RSS, limit=10)
        assert len(articles) == 3
        assert articles[0]["title"] == "FTSE 100 hits record high"
        assert articles[0]["source"] == "Financial Times"
        assert articles[1]["title"] == "Vanguard ETF inflows surge"

    def test_parse_rss_respects_limit(self):
        articles = _parse_rss(SAMPLE_RSS, limit=1)
        assert len(articles) == 1

    def test_parse_rss_handles_malformed_xml(self):
        articles = _parse_rss(b"not xml at all", limit=10)
        assert articles == []

    @patch("tradingagents.dataflows.google_news.urlopen")
    def test_fetch_deduplicates_by_title(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = SAMPLE_RSS
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = fetch_google_news(
            ["Vanguard FTSE 100", "VUKG"],
            inter_query_delay=0,
        )
        assert "FTSE 100 hits record high" in result
        assert result.count("FTSE 100 hits record high") == 1

    def test_fetch_empty_search_names(self):
        result = fetch_google_news([])
        assert "no search names" in result


# --- ApeWisdom ---


SAMPLE_APEWISDOM = {
    "results": [
        {"rank": 1, "ticker": "GME", "mentions": 500, "upvotes": 12000, "mentions_24h_ago": 400},
        {"rank": 5, "ticker": "GLD", "mentions": 120, "upvotes": 3000, "mentions_24h_ago": 80},
        {"rank": 12, "ticker": "QQQ", "mentions": 85, "upvotes": 2100, "mentions_24h_ago": 90},
    ]
}


class TestApeWisdom:
    @patch("tradingagents.dataflows.apewisdom.urlopen")
    def test_finds_matching_tickers(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(SAMPLE_APEWISDOM).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = fetch_apewisdom_mentions(["GLD", "QQQ"])
        assert "GLD" in result
        assert "QQQ" in result
        assert "#5" in result
        assert "120 mentions" in result

    @patch("tradingagents.dataflows.apewisdom.urlopen")
    def test_not_found_returns_placeholder(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(SAMPLE_APEWISDOM).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        result = fetch_apewisdom_mentions(["DOESNOTEXIST"])
        assert "no ApeWisdom mentions found" in result

    def test_empty_tickers(self):
        result = fetch_apewisdom_mentions([])
        assert "no tickers provided" in result


# --- Reddit with search_query ---


class TestRedditSearchQuery:
    @patch("tradingagents.dataflows.reddit._fetch_subreddit")
    def test_search_query_used_instead_of_ticker(self, mock_fetch):
        mock_fetch.return_value = []
        fetch_reddit_posts(
            "VUKG.L",
            subreddits=("UKPersonalFinance",),
            search_query="Vanguard FTSE 100",
            inter_request_delay=0,
        )
        call_args = mock_fetch.call_args
        assert call_args[0][0] == "Vanguard FTSE 100"

    @patch("tradingagents.dataflows.reddit._fetch_subreddit")
    def test_ticker_used_when_no_search_query(self, mock_fetch):
        mock_fetch.return_value = []
        fetch_reddit_posts(
            "AAPL",
            subreddits=("stocks",),
            inter_request_delay=0,
        )
        call_args = mock_fetch.call_args
        assert call_args[0][0] == "AAPL"
