# Development plan

## Current state (Stage 1 in progress, Stage 1.6 planned - 2026-06-14)

### Stage 1 progress
- [x] 5 data extraction CLI scripts (`scripts/fetch_*.py`) - tested with tickers and ISINs
- [x] 12 agent skill files (`.claude/commands/*.md`) - all role prompts extracted
- [x] `analyse-ticker` orchestration skill - handles both tickers and ISINs
- [x] `analyse-portfolio` skill - multi-account portfolio analysis
- [x] Initial Codex mirror support in `.agents/skills/source-command-*/SKILL.md`
- [x] Codex filesystem config in `.codex/config.toml`
- [x] Agentic collaboration and skill-sync plan documented in `orchestration/AGENTIC-COLLABORATION.md`
- [x] End-to-end test of `/analyse-ticker` with 4 Vanguard ISA tickers: VUKG.L, VWRP.L, VFEG.L, VJPB.L
- [x] End-to-end test of `/analyse-ticker` with ISIN: IE00B5339C57 (Polar Capital Global Insurance)
- [ ] End-to-end test of `/analyse-portfolio` (full multi-account run)
- [x] Source-first sync: `scripts/sync_agentic_commands.py` generates Codex skills from Claude commands
- [x] ISIN-to-Yahoo resolver (`isin_resolver.py`) - all 5 OEIC/SICAV funds now analysable
- [x] Fund profile script (`fetch_fund_profile.py`) - top holdings, sectors, Morningstar ratings
- [x] Portfolio moved from repo (`config/portfolio.yaml`) to Obsidian vault (`portfolio/` with Dataview dashboard)
- [x] Multi-account portfolio support (Vanguard ISA + AJ Bell ISA)

### What's new in Stage 1
- `scripts/` directory with 5 Python CLI scripts wrapping tradingagents/dataflows/
- `.claude/commands/` with 14 skill files (12 agent roles + 2 orchestration)
- `.agents/skills/` with Codex-compatible mirrors of the source commands
- Skills-based pipeline replaces LangGraph orchestration
- Zero API cost - runs on Teams subscription tokens via Claude Code subagents
- ISIN resolution: `normalize_symbol()` detects ISINs and resolves via `yf.Search` with disk cache
- Fund profile data: `fetch_fund_profile.py` replaces `fetch_fundamentals.py` for OEIC/SICAV funds
- Portfolio in Obsidian vault: one note per holding with YAML frontmatter + Dataview dashboard
- Multi-account support: Vanguard ISA (passive index) + AJ Bell ISA (thematic/active + gold)

---

## Previous state (end of Stage 0 - 2026-06-13)

### What works
- TradingAgents framework (v0.2.5 fork) runs end-to-end with Claude Sonnet 4.6
- Single-ticker analysis tested successfully: AAPL on 2026-06-12
- Full pipeline: 4 analysts -> bull/bear debate -> research manager -> trader -> 3-way risk debate -> portfolio manager
- Data fetching via yfinance (no API key needed)
- Decision logged to `~/.tradingagents/memory/trading_memory.md`
- Full state saved to `~/.tradingagents/logs/AAPL/`

### Configuration
- LLM provider: Anthropic (Sonnet 4.6 for both tiers)
- Set via `.env`: `TRADINGAGENTS_LLM_PROVIDER`, `TRADINGAGENTS_DEEP_THINK_LLM`, `TRADINGAGENTS_QUICK_THINK_LLM`
- Data source: yfinance for all categories (OHLCV, indicators, fundamentals, news)

### Portfolio (Stage 0)
- `config/portfolio.yaml` populated from Vanguard Investor screenshot (since moved to Obsidian vault)
- 5 holdings: LifeStrategy 100% (OEIC, no ticker), VUKG.L, VWRP.L, VFEG.L, VJPB.L

### Cost observation
- Single AAPL run with Sonnet 4.6: ~$1-2, ~12 min wall clock
- Running 4 ETFs regularly via API would be expensive (~$5-8/run)

### Files changed from upstream fork
- `.env` - added `TRADINGAGENTS_*` config vars
- `main.py` - changed ticker/date for test run
- `CLAUDE.md` - project context with correct tickers
- `DEVELOPMENT.md` - this file

---

## Stage 1 plan: Skills-based pipeline (no API cost)

### Goal
Replace the LangGraph/API-based agent pipeline with Claude Code skills and workflows that run on Teams subscription tokens instead of per-call API credits.

### Architecture

```
Current (LangGraph + API):
  Python orchestrator -> langchain-anthropic -> Anthropic API ($$$)
  Each agent = LLM call via API key

Target (Claude Code skills):
  Claude Code workflow -> subagents (Teams tokens, no extra cost)
  Each agent = Claude Code skill with role prompt
  Data fetching = Python scripts called via Bash tool
```

### What to keep from TradingAgents
- **Data fetching code** - the yfinance wrappers in `tradingagents/dataflows/` are solid
- **Agent prompts** - extract verbatim from the agent files
- **Tool definitions** - `get_stock_data`, `get_indicators`, `get_fundamentals`, etc.
- **Decision logging** - the memory log format

### What to replace
- LangGraph graph execution -> Claude Code workflow orchestration
- langchain-anthropic LLM calls -> Claude Code subagents
- Structured output schemas -> skill output format conventions

### Implementation steps

#### Step 1: Data extraction scripts
Create standalone Python CLI scripts that fetch data and output to stdout/files:
- `scripts/fetch_market_data.py <ticker> <date>` - OHLCV + technical indicators
- `scripts/fetch_sentiment.py <ticker> <date>` - news sentiment + social
- `scripts/fetch_news.py <ticker> <date>` - macro + ticker news
- `scripts/fetch_fundamentals.py <ticker> <date>` - financial statements

These wrap the existing `tradingagents/dataflows/` code with a CLI interface.

#### Step 2: Agent skills
Create Claude Code skills in `.claude/commands/`:
- `market-analyst.md` - technical analysis from market data
- `sentiment-analyst.md` - sentiment scoring from news/social data
- `news-analyst.md` - macro + company news research
- `fundamentals-analyst.md` - financial statement analysis
- `bull-researcher.md` - bullish case advocate
- `bear-researcher.md` - bearish case advocate
- `research-manager.md` - debate synthesis into investment plan
- `trader.md` - investment plan to transaction proposal
- `risk-aggressive.md` / `risk-conservative.md` / `risk-neutral.md`
- `portfolio-manager.md` - final decision synthesis

#### Step 3: Orchestration workflow
Create `.claude/commands/analyse-ticker.md` (or a workflow script) that:
1. Runs the 4 data fetch scripts in parallel via Bash
2. Spawns 4 analyst subagents in parallel with fetched data
3. Spawns bull + bear researchers sequentially (debate)
4. Spawns research manager to synthesise
5. Spawns trader
6. Spawns 3 risk debaters sequentially
7. Spawns portfolio manager for final decision
8. Writes decision to Obsidian vault

#### Step 4: Portfolio-level analysis
Create `.claude/commands/analyse-portfolio.md` that:
1. Reads portfolio holdings from Obsidian vault (`portfolio/` folder)
2. Runs analyse-ticker for each holding (ticker or ISIN)
3. Synthesises portfolio-level recommendations (rebalancing, correlation)

### Agent prompt mapping

| Agent | Source file | Tools | LLM tier |
|-------|-----------|-------|----------|
| Market analyst | `analysts/market_analyst.py` | get_stock_data, get_indicators | quick |
| Sentiment analyst | `analysts/sentiment_analyst.py` | (pre-fetched data) | quick |
| News analyst | `analysts/news_analyst.py` | get_news, get_global_news | quick |
| Fundamentals analyst | `analysts/fundamentals_analyst.py` | get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement | quick |
| Bull researcher | `researchers/bull_researcher.py` | none | deep |
| Bear researcher | `researchers/bear_researcher.py` | none | deep |
| Research manager | `managers/research_manager.py` | none (structured output) | deep |
| Trader | `trader/trader.py` | none (structured output) | deep |
| Aggressive risk | `risk_mgmt/aggressive_debator.py` | none | deep |
| Conservative risk | `risk_mgmt/conservative_debator.py` | none | deep |
| Neutral risk | `risk_mgmt/neutral_debator.py` | none | deep |
| Portfolio manager | `managers/portfolio_manager.py` | none (structured output) | deep |

### Data flow (state keys)

```
fetch scripts -> analyst skills:
  market_data     -> Market analyst   -> market_report
  sentiment_data  -> Sentiment analyst -> sentiment_report
  news_data       -> News analyst     -> news_report
  fundamentals    -> Fundamentals     -> fundamentals_report

analyst reports -> researchers:
  {all 4 reports} -> Bull researcher  -> bull_argument
  {all 4 reports} -> Bear researcher  -> bear_argument

debate -> synthesis:
  {bull + bear}   -> Research manager -> investment_plan

plan -> execution:
  investment_plan -> Trader           -> trade_proposal

proposal -> risk:
  trade_proposal  -> Aggressive       -> aggressive_view
  trade_proposal  -> Conservative     -> conservative_view
  trade_proposal  -> Neutral          -> neutral_view

risk debate -> final:
  {3 risk views}  -> Portfolio manager -> final_decision
```

---

## Stage 1.5: Agentic command sync (DONE)

Source-first sync implemented. Claude Code commands are the canonical source;
Codex skills are generated by `scripts/sync_agentic_commands.py`.

- `python3 scripts/sync_agentic_commands.py` - generate Codex skills
- `python3 scripts/sync_agentic_commands.py --check` - verify sync, exit 1 if stale
- `AGENTS.md` slimmed to a stub pointing at `CLAUDE.md`
- Full contract documented in `orchestration/AGENTIC-COLLABORATION.md`

---

## Stage 1.6: Sentiment data improvement (PLANNED - 2026-06-14)

### Problem

The Sentiment Analyst agent gets zero usable data for the entire portfolio.
All three current sources (yfinance news, StockTwits, Reddit) search by a
single ticker string, but 17 holdings are UK-listed ETFs, ETCs, and UCITS
OEICs/SICAVs with no presence on US-centric platforms.

Live testing on 2026-06-14 confirmed:

| Source | Query method | UK ETF result | OEIC/SICAV result |
|--------|-------------|---------------|-------------------|
| yfinance `Ticker.get_news()` | ticker | 0 articles (all 17) | 0 articles |
| yfinance `yf.Search()` | ISIN | 0 news (quote resolves OK) | 0 news |
| yfinance `yf.Search()` | SEDOL | 0 news (quote resolves OK) | 0 news |
| yfinance `yf.Search()` | fund name | 0-5 (loose thematic match) | 0-5 |
| StockTwits | ticker | HTTP 404 (all `.L` tickers) | N/A |
| Reddit (US subs) | ticker | 0 posts | 0 posts |
| FinnHub | ticker | HTTP 403 (free tier, no UK) | N/A |
| Google News RSS | ticker (`.L`) | 0 articles | N/A |
| Google News RSS | ISIN | 0 articles | 0 articles |
| Google News RSS | SEDOL | 0 articles | 0 articles |
| **Google News RSS** | **fund name** | **50-80+ articles** | **50-80+ articles** |
| **StockTwits (US proxy)** | **US equivalent ETF** | **28-30 msgs w/ sentiment** | **28-30 msgs** |
| **Reddit (UK subs, RSS)** | **fund name** | **3-5 posts (rate-limited)** | **1-3 posts** |

### Identifier coverage (17 holdings)

Each holding has multiple identifiers, but only fund name works for
sentiment search. The others serve market data resolution only.

| Identifier | Holdings with it | Useful for sentiment? | Useful for market data? |
|------------|-----------------|----------------------|------------------------|
| Exchange ticker (`.L`) | 10/17 | No (zero results everywhere) | Yes (yfinance OHLCV) |
| ISIN | 16/17 | No (zero results everywhere) | Yes (yf.Search quote resolution) |
| SEDOL | 8/17 (explicit field), 4 more used as ticker | No (zero results everywhere) | Yes (yf.Search quote resolution) |
| Fund name | 17/17 | **Yes - the only key that works** | No |
| US proxy ticker | mappable for all 17 | **Yes - StockTwits only** | No |

Holdings where ticker field contains a SEDOL (not an exchange ticker):
Fidelity Global Tech (BJVDZ16), Fidelity Index EM (BHZK8D2),
L&G Infrastructure (BF0TZG2), Polar Capital Insurance (B5339C5),
L&G Tech (B0CNH16), Janus Henderson (3191923).

### Design considerations (open questions)

Before implementing, these need resolution:

1. **Google News query design.** A naive "search by fund name" approach will
   fire 2-3 Google News queries per holding x 17 holdings = 34-51 HTTP
   requests per portfolio run. Need to consider:
   - Rate limiting / IP blocking risk from Google
   - Query specificity vs noise tradeoff (broad queries return many
     irrelevant articles)
   - Whether to deduplicate across holdings that share themes (e.g. both
     gold ETCs return overlapping gold articles)
   - Caching strategy for articles already seen in recent runs
   - Whether to fetch article bodies or just headlines + source

2. **UK-specific sentiment platforms.** A dedicated UK retail investor
   sentiment source would be higher quality than generic Google News.
   Evaluated on 2026-06-14 (all 12 candidates):

   **Best candidate - Investing.com sentiment scoreboards:**
   Investing.com has per-ETF sentiment scoreboards
   (`uk.investing.com/etfs/[etf]-scoreboard`) where users vote
   Bullish/Bearish across time periods. Covers UK ETFs and FTSE 100.
   No API but structured HTML (percentages, vote counts) that could be
   scraped. Most realistic near-term source for structured bull/bear
   data on UK ETFs.

   **Viable but restricted:**
   - Interactive Investor (ii) Community - powered by StockRepublic,
     17K+ profiles, 37% weekly active. Best UK social investing
     platform, but API is B2B only (StockRepublic developer hub is
     password-protected, requires commercial partnership)
   - eToro Social API - has feed/social endpoints, but access is
     "currently available to select users" and UK ETF coverage is thin
   - Adanos API (adanos.org) - aggregates Reddit + X + news, covers
     80 exchanges, free tier 250 calls/mo. Needs registration to
     verify actual UK ETF mention volume

   **Not viable (researched and rejected):**
   - LSE.co.uk ShareChat - ETF pages exist but discussion volume near
     zero; site returns HTTP 403 for scraping
   - ADVFN - same problem as LSE.co.uk; ETF boards exist but empty;
     OEICs not covered at all; HTTP 403
   - Freetrade Community - **shut down**; forum closed, redirects
   - Hargreaves Lansdown - has no community features at all
   - Trustnet (FE fundinfo) - excellent fund data but zero sentiment
     capability; no forums, no social, no community
   - Citywire Moneyforums - declining activity (last posts mid-2023);
     no API; not worth scraping
   - MoneySavingExpert - active discussion volume but wrong format;
     posts are long-form advice seeking ("should I buy VWRP?") not
     structured sentiment signals; no API
   - Getquin - DACH-focused (Germany/Austria/Switzerland), no public
     API, portfolio-centric not per-instrument sentiment
   - Trading 212 - active Discourse community but API is trading-only,
     no social/sentiment data exposed
   - Google Trends - pytrends library archived Apr 2025; official API
     not public yet

   **Conclusion:** No UK StockTwits equivalent exists. Best path is
   Investing.com scoreboards (scraping) + Adanos API (if free tier
   covers UK ETFs) + Reddit UK subs (already have). Generic Google
   News is a news source, not a sentiment source - it provides
   headlines the Sentiment Analyst can interpret, but not structured
   bull/bear signals

3. **US proxy ticker mapping.** Need a maintained mapping from each UK
   holding to its closest US equivalent for StockTwits. This is subjective
   for active funds (which US ETF best proxies "Polar Capital Global
   Insurance"?). Mapping must be stored somewhere and kept in sync with
   portfolio changes.

4. **Asset metadata registry vs portfolio notes.** The portfolio notes in
   Obsidian already have name, ticker, ISIN, SEDOL, sector. The sentiment
   fetcher needs search_names, us_proxy, theme, reddit_subs. Two options:
   - Extend portfolio YAML frontmatter with sentiment-specific fields
   - Separate registry file in the repo (`tradingagents/dataflows/asset_registry.py`)
   The registry duplicates data but keeps sentiment logic out of the vault.

5. **SEDOL and ISIN utility.** Both resolve quotes via `yf.Search()` and
   could serve as additional identifiers for market data scripts, but
   neither returns news or sentiment on any tested platform. They should
   be added to the symbol resolution pipeline for robustness (fallback
   chain: ticker -> ISIN -> SEDOL -> name-based search) but not relied
   on for sentiment.

6. **Analyst skill prompt update.** The sentiment-analyst.md skill needs
   to understand:
   - Which data came from direct vs proxy sources
   - How to weight proxy sentiment (lower confidence, directional only)
   - That Google News articles may be thematically related rather than
     fund-specific
   - Data source attribution in the output

### Implementation plan (when ready)

#### Phase 1: Asset metadata and multi-source pipeline (DONE - 2026-06-20)

- [x] Decide: separate registry in repo (not Obsidian frontmatter)
- [x] `uk_asset_registry.py` - all 17 holdings with search_names, US proxy,
  theme keywords, UK subreddits, keyed by ticker/ISIN/Morningstar/SEDOL
- [x] `google_news.py` - Google News RSS fetcher by fund name, en-GB locale,
  deduplication across query variants, 1s inter-query delay
- [x] `apewisdom.py` - ApeWisdom REST API (free, no auth) for aggregated
  Reddit+4chan mention counts and 24h deltas on US proxy tickers
- [x] `reddit.py` - added `search_query` parameter for fund name search,
  added UK subreddit routing (UKPersonalFinance, UKInvesting, FIREUK)
- [x] `fetch_sentiment.py` - UK pipeline: Google News + StockTwits proxy +
  ApeWisdom + Reddit UK/global; falls back to original for non-UK assets
- [x] `sentiment-analyst.md` - source-type awareness (direct/proxy/thematic/buzz),
  data coverage grading (A-D), updated output table with source type column
- [x] Codex skills synced via `sync_agentic_commands.py`
- [x] Unit tests: 18 tests in `test_uk_sentiment_sources.py` (all pass)
- [x] End-to-end smoke test: VUKG.L (8 Google News articles, 28 StockTwits
  proxy msgs, 5 Reddit UK posts), IE00B5339C57 (4 articles, 30 proxy msgs)

Remaining identifer cleanup (not blocking, tracked separately):
- [ ] Audit and fix portfolio notes where ticker contains SEDOL
- [ ] Add missing ISINs (Fidelity Index EM has ISIN GB00BHZK8D21 in registry)

#### Phase 2: Structured sentiment sources (PLANNED)

- [ ] Investigate Investing.com sentiment scoreboards for UK ETF coverage
  - Test scraping `uk.investing.com/etfs/[etf]-scoreboard` for portfolio holdings
  - Check ToS and blocking behaviour
  - Assess data quality (vote counts, time-period breakdown)
  - If viable: `investing_com_sentiment.py` scraper with bull/bear ratios
- [ ] Register Adanos free tier, test UK ETF mention volume
  - If viable: `adanos_sentiment.py` fetcher (replaces StockTwits for UK)
- [ ] Bluesky AT Protocol firehose - cashtag filtering for UK tickers
  - Requires persistent WebSocket consumer (Stage 2 scheduling prerequisite)
- [ ] `yfinance_news.py` - add `yf.Search(theme)` fallback when
  `Ticker.get_news()` returns zero (for news-analyst.md)

#### Phase 3: Behavioural flow data (PLANNED)

- [ ] AJ Bell Favourite Funds / HL most-bought as OEIC sentiment proxy
  - Weekly scrape cadence, editorial web pages
- [ ] Google News caching layer (skip seen articles, 6h TTL)

### Verified data sources (tested 2026-06-14)

**Working and free (no auth):**
- Google News RSS (`news.google.com/rss/search`) - fund name queries, en-GB
- StockTwits (US proxy) - ISF, VT, VWO, EWJ, GLD, IAU, QQQ, XLF, KIE all return 30 msgs
- Reddit RSS fallback - UK subs work when not rate-limited
- yf.Search thematic - broad theme queries return ~5 articles

**Needs investigation (most promising structured sentiment):**
- Investing.com scoreboards - bull/bear vote ratios for UK ETFs, scrapeable
  structured HTML, no API, need to test coverage and scraping feasibility
- Adanos (adanos.org) - aggregated Reddit + X + news sentiment, 250 free
  calls/mo, covers 80 exchanges. Need to register and test UK ETF volume

**Requires API key (secondary):**
- EODHD - tweet + news sentiment, free tier limited to 6 US tickers
- Alpha Vantage news sentiment - 25 free calls/day

**Not viable (tested and rejected 2026-06-14):**
- FinnHub company news - HTTP 403 for UK tickers on free tier
- GDELT - HTTP 429 after 1-2 requests, too aggressive rate limiting
- Google Trends - pytrends library archived Apr 2025, official API not public
- StockTwits direct - HTTP 404 for all `.L` tickers (US-only)
- yfinance Ticker.get_news() - zero results for all UK tickers
- Any platform searching by ISIN or SEDOL - zero sentiment results everywhere
- Trustpilot - measures platform satisfaction, not fund sentiment
- LSE.co.uk ShareChat - HTTP 403, near-zero ETF discussion volume
- ADVFN - HTTP 403, ETF boards empty, no OEIC coverage
- Freetrade Community - shut down
- Hargreaves Lansdown - no community features
- Trustnet - no sentiment/social capability
- Citywire forums - declining activity (last posts mid-2023)
- MoneySavingExpert - advice-seeking format, not sentiment signals
- Getquin - DACH-focused, no public API
- Trading 212 - API is trading-only, no social data
- ii Community / StockRepublic - best UK platform but B2B API only
- eToro Social API - restricted access, thin UK ETF coverage

---

## Session wrap-up checklist

At the end of each development session, do the following:

1. **Update this file** - mark completed steps, note blockers, update current state
2. **Commit changes** - conventional commit messages (feat:, fix:, docs:, chore:)
3. **Update CLAUDE.md** if architecture or conventions changed
4. **Update AGENTS.md** if Codex architecture or conventions changed
5. **Update `orchestration/AGENTIC-COLLABORATION.md`** if command or skill sync rules changed
6. **Update portfolio notes in Obsidian vault** if holdings changed
7. **Note token/cost observations** for any test runs
8. **Write a handoff summary** - what was done, what's next, any gotchas
