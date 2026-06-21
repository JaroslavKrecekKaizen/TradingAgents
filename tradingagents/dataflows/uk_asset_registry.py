"""UK asset sentiment metadata registry.

Maps UK portfolio holdings to the query parameters needed to fetch
sentiment data from non-US sources. Each holding is keyed by every
known identifier (exchange ticker, ISIN, resolved Morningstar ticker)
so callers can look up by whichever identifier they have.

Holdings not in the registry get ``None``, signalling the caller to
fall back to the default US-style sentiment pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AssetSentimentMeta:
    """Query parameters for fetching sentiment data about a UK asset."""

    search_names: list[str]
    us_proxy: str | None
    theme_keywords: list[str]
    asset_type: str = "etf"


_HOLDINGS: list[tuple[list[str], AssetSentimentMeta]] = [
    # --- Vanguard ISA ---
    (
        ["VUKG.L", "GB00BFNHP716"],
        AssetSentimentMeta(
            search_names=["Vanguard FTSE 100 UCITS ETF", "VUKG"],
            us_proxy="ISF",
            theme_keywords=["FTSE 100 ETF", "UK large cap index"],
        ),
    ),
    (
        ["VWRP.L", "IE00BK5BQT80"],
        AssetSentimentMeta(
            search_names=["Vanguard FTSE All-World UCITS ETF", "VWRP"],
            us_proxy="VT",
            theme_keywords=["global equity ETF", "all world index"],
        ),
    ),
    (
        ["VFEG.L", "IE00BK5BR733"],
        AssetSentimentMeta(
            search_names=["Vanguard FTSE Emerging Markets UCITS ETF", "VFEG"],
            us_proxy="VWO",
            theme_keywords=["emerging markets ETF"],
        ),
    ),
    (
        ["VJPB.L", "IE00BFMXYY33"],
        AssetSentimentMeta(
            search_names=["Vanguard FTSE Japan UCITS ETF", "VJPB"],
            us_proxy="EWJ",
            theme_keywords=["Japan ETF", "Nikkei index"],
        ),
    ),
    (
        ["GB00B41XG308", "0P0000TKZO.L"],
        AssetSentimentMeta(
            search_names=[
                "Vanguard LifeStrategy 100% Equity Fund",
                "LifeStrategy 100",
            ],
            us_proxy="VT",
            theme_keywords=["global equity fund", "passive multi-asset"],
            asset_type="oeic",
        ),
    ),
    # --- AJ Bell ISA ---
    (
        ["GB00B0CNH163", "0P000023MW.L", "B0CNH16"],
        AssetSentimentMeta(
            search_names=[
                "L&G Global Technology Index Fund",
                "Legal & General Global Technology",
            ],
            us_proxy="QQQ",
            theme_keywords=["technology index fund", "global tech ETF"],
            asset_type="oeic",
        ),
    ),
    (
        ["LU1033663649", "0P00012CU7.L", "BJVDZ16"],
        AssetSentimentMeta(
            search_names=[
                "Fidelity Global Technology Fund",
                "Fidelity Global Tech",
            ],
            us_proxy="QQQ",
            theme_keywords=["technology fund", "global tech active"],
            asset_type="oeic",
        ),
    ),
    (
        ["PHGP.L", "JE00B1VS3770"],
        AssetSentimentMeta(
            search_names=["WisdomTree Physical Gold", "PHGP"],
            us_proxy="GLD",
            theme_keywords=["gold ETC", "physical gold price"],
            asset_type="etc",
        ),
    ),
    (
        ["SGLP.L", "IE00B579F325"],
        AssetSentimentMeta(
            search_names=["Invesco Physical Gold ETC", "SGLP"],
            us_proxy="IAU",
            theme_keywords=["gold ETC", "physical gold price"],
            asset_type="etc",
        ),
    ),
    (
        ["GB0031919235", "0P00000WPX.L", "3191923"],
        AssetSentimentMeta(
            search_names=[
                "Janus Henderson Global Financials Fund",
                "Janus Henderson Financials",
            ],
            us_proxy="XLF",
            theme_keywords=["financial sector fund", "global financials"],
            asset_type="oeic",
        ),
    ),
    (
        ["IE00B5339C57", "0P0000SY4N.L", "B5339C5"],
        AssetSentimentMeta(
            search_names=[
                "Polar Capital Global Insurance Fund",
                "Polar Capital Insurance",
            ],
            us_proxy="KIE",
            theme_keywords=["insurance sector fund", "global insurance"],
            asset_type="oeic",
        ),
    ),
    (
        ["GB00BF0TZG22", "0P0001CQS8.L", "BF0TZG2"],
        AssetSentimentMeta(
            search_names=[
                "L&G Global Infrastructure Index Fund",
                "Legal & General Infrastructure",
            ],
            us_proxy="IGF",
            theme_keywords=["infrastructure fund", "global infrastructure"],
            asset_type="oeic",
        ),
    ),
    (
        ["GB00BHZK8D21", "0P00011YDA.L", "BHZK8D2"],
        AssetSentimentMeta(
            search_names=[
                "Fidelity Index Emerging Markets Fund",
                "Fidelity Emerging Markets",
            ],
            us_proxy="VWO",
            theme_keywords=["emerging markets fund"],
            asset_type="oeic",
        ),
    ),
    (
        ["DFNG.L", "IE000YYE6WK5"],
        AssetSentimentMeta(
            search_names=["VanEck Defense ETF", "DFNG"],
            us_proxy="ITA",
            theme_keywords=["defence ETF", "aerospace defense"],
        ),
    ),
    (
        ["WDEP.L", "IE0002Y8CX98"],
        AssetSentimentMeta(
            search_names=["WisdomTree Europe Defence UCITS ETF", "WDEP"],
            us_proxy="ITA",
            theme_keywords=["European defence ETF", "NATO defence spending"],
        ),
    ),
    (
        ["WREE.L", "IE000KHX9DX6"],
        AssetSentimentMeta(
            search_names=[
                "WisdomTree Strategic Metals & Rare Earths Miners ETF",
                "WREE",
            ],
            us_proxy="REMX",
            theme_keywords=["rare earth miners ETF", "strategic metals"],
        ),
    ),
    (
        ["URNG.L", "IE000NDWFGA5"],
        AssetSentimentMeta(
            search_names=["Global X Uranium ETF", "URNG"],
            us_proxy="URA",
            theme_keywords=["uranium ETF", "nuclear energy"],
        ),
    ),
]

_INDEX: dict[str, AssetSentimentMeta] = {}
for _keys, _meta in _HOLDINGS:
    for _key in _keys:
        _INDEX[_key.upper()] = _meta


def get_sentiment_meta(ticker_or_isin: str) -> AssetSentimentMeta | None:
    """Look up sentiment query metadata for a UK asset.

    Accepts exchange tickers (``VUKG.L``), ISINs (``GB00BFNHP716``),
    resolved Morningstar tickers (``0P0000TKZO.L``), or SEDOLs used as
    ticker fields (``B0CNH16``).

    Returns ``None`` for assets not in the registry.
    """
    return _INDEX.get(ticker_or_isin.strip().upper())
