# Trading System - Project Context

## What this is

A multi-agent automated trading research and simulation system built on a fork of
TauricResearch/TradingAgents (LangGraph, v0.2.5). It analyses markets, debates
investment theses, logs decisions, reflects on outcomes, and learns over time.

All trading is simulated (paper trading via Alpaca) until explicitly authorised otherwise.

## CRITICAL SAFETY RULES

- NEVER execute real trades. All execution goes through Alpaca paper API only.
- NEVER commit API keys or secrets. Use environment variables via .env (gitignored).
- Always log decisions before acting on them.
- Every recommendation must include confidence level and risk assessment.
- Do not use em dashes in any output. Use short dashes or rephrase.

## Repository structure

This repo contains only code and configuration. All knowledge, logs, and human-readable
output live in the Obsidian vault (accessed via filesystem MCP server).

```
trading-system/                  # Root = forked TradingAgents repo
  tradingagents/                 # Upstream Python package
  scripts/
    fetch_market_data.py         # OHLCV + indicators + verified snapshot
    fetch_sentiment.py           # News headlines + StockTwits + Reddit
    fetch_news.py                # Ticker news + global macro news
    fetch_fundamentals.py        # Financials, balance sheet, cash flow, income
    fetch_fund_profile.py        # Fund profile: holdings, sectors, Morningstar (for OEICs/SICAVs)
  .claude/
    commands/                    # Claude Code slash commands (skills)
      analyse-ticker.md          # Master pipeline for single-ticker analysis
      analyse-portfolio.md       # Portfolio-level analysis across all holdings
      market-analyst.md          # Technical analysis role
      sentiment-analyst.md       # Sentiment analysis role
      news-analyst.md            # News research role
      fundamentals-analyst.md    # Financial analysis role
      bull-researcher.md         # Bullish case advocate
      bear-researcher.md         # Bearish case advocate
      research-manager.md        # Debate synthesis into investment plan
      trader.md                  # Investment plan to transaction proposal
      risk-aggressive.md         # High-risk/high-reward advocate
      risk-conservative.md       # Asset protection advocate
      risk-neutral.md            # Balanced perspective
      portfolio-manager.md       # Final decision synthesis
  orchestration/
    routines/                    # Routine definitions
    hooks/                       # Lifecycle hooks (decision logging, safety)
  config/
    providers.yaml               # API provider config (no secrets - those go in .env)
  CLAUDE.md                      # This file
  .mcp.json                      # MCP server configuration
  .env                           # API keys (gitignored, never committed)
  .gitignore
  requirements.txt               # From upstream + our extensions
```

## Obsidian vault structure

The Obsidian vault lives at `/Users/jarda/Documents/ATES`. All knowledge, logs, and
human-readable output live there. The trading-system subtree:

```
/Users/jarda/Documents/ATES/10-projects/trading-system/
  portfolio/                     # One note per holding (YAML frontmatter) + Dashboard
  decisions/                     # Structured decision records (YYYY-MM-DD-TICKER.md)
  reflections/                   # Post-hoc outcome analysis, lessons learned
  market-notes/                  # Manual observations
  books/                         # Trading theory book summaries
  papers/                        # Research paper notes
  performance/                   # QuantStats reports, weekly/monthly metrics
```

## Codex skill sync

Codex executes the same pipeline through generated skills in
`.agents/skills/source-command-*/SKILL.md`. These are generated from the Claude
Code commands by `scripts/sync_agentic_commands.py`.

After editing any command in `.claude/commands/`, regenerate the Codex skills:

```
python3 scripts/sync_agentic_commands.py          # generate
python3 scripts/sync_agentic_commands.py --check   # verify without writing
```

See `orchestration/AGENTIC-COLLABORATION.md` for the full collaboration contract.

### Decision log format

Each decision is a markdown file saved to the Obsidian vault:
`/Users/jarda/Documents/ATES/10-projects/trading-system/decisions/YYYY-MM-DD-TICKER.md`

```markdown
# Decision: TICKER - ACTION

- **Date:** YYYY-MM-DD
- **Ticker:** TICKER
- **Action:** Buy / Sell / Hold / Overweight / Underweight
- **Confidence:** High / Medium / Low
- **Risk level:** 1-5
- **Rationale:** [1-3 sentence summary of the agent team's reasoning]
- **Bull case:** [key bull argument]
- **Bear case:** [key bear argument]
- **Risk factors:** [top risks identified by risk management team]
- **Benchmark:** VWRP.L
```

### Reflection log format

Each reflection: `reflections/YYYY-MM-DD-TICKER-reflection.md`

```markdown
# Reflection: TICKER - YYYY-MM-DD decision

- **Original decision:** [link to decision file]
- **Holding period:** X days
- **Return:** X%
- **Alpha vs benchmark:** X%
- **What went right:** [paragraph]
- **What went wrong:** [paragraph]
- **Lesson:** [one actionable takeaway for future decisions]
```

## Current portfolio (ISA simulation)

Holdings live in the Obsidian vault under `portfolio/` (one note per holding with
YAML frontmatter, queryable via Dataview). Two ISA accounts, benchmark VWRP.L.

All holdings are analysable - pass either tickers or ISINs to `/analyse-ticker`.
ISINs are auto-resolved to Yahoo Finance tickers via `isin_resolver.py`.

**Vanguard ISA** (~GBP 46K value, passive index ETFs):
- VUKG.L (FTSE 100 Acc - 17%)
- VWRP.L (All-World Acc - 28%) - also the benchmark
- VFEG.L (Emerging Markets Acc - 9%)
- VJPB.L (Japan Acc - 18%)
- LifeStrategy 100% Equity Fund Acc (ISIN GB00B41XG308 - 28%)

**AJ Bell ISA** (~GBP 70K value, thematic/active + commodities + defence):
- L&G Global Technology Index I Acc (ISIN GB00B0CNH163 - 20%)
- Fidelity Global Technology W-Acc-GBP (ISIN LU1033663649 - 15%)
- PHGP.L (WisdomTree Physical Gold - 14%)
- Janus Henderson Global Financials I Acc (ISIN GB0031919235 - 9%)
- Polar Capital Global Insurance I Acc (ISIN IE00B5339C57 - 8%)
- L&G Global Infrastructure Index I Acc (SEDOL BF0TZG2 - 7%)
- SGLP.L (Invesco Physical Gold ETC - 6%)
- Fidelity Index Emerging Markets P Acc (SEDOL BHZK8D2 - 5%)
- DFNG.L (VanEck Defense ETF - 4%)
- WDEP.L (WisdomTree Europe Defence ETF - 4%)
- WREE.L (WisdomTree Strategic Metals & Rare Earths Miners ETF - 4%)
- URNG.L (Global X Uranium ETF - 3%)
- Cash GBP - 0.2%

## Tech stack

- Python 3.11+, LangGraph (TradingAgents framework)
- ChromaDB (local vector store for RAG knowledge base)
- yfinance (UK ETF prices)
- justetf-scraping (UCITS ETF holdings data)
- Riskfolio-Lib (portfolio optimisation - Stage 4)
- QuantStats (performance analytics - Stage 4)
- Alpaca paper trading API (US-listed simulation)
- FinnHub (market data, TradingAgents default)

## LLM provider

Claude via Anthropic API (Teams subscription). Configure in .env:

- ANTHROPIC_API_KEY for Claude access
- Use Claude Sonnet for analyst/retrieval agents (cost-efficient)
- Use Claude Opus for debate/decision nodes (reasoning quality)

## Agent architecture

Seven agents across four teams (TradingAgents upstream design):

1. Analyst Team (parallel): Fundamentals, Sentiment, News, Technical
2. Research Team: Bull + Bear debate -> Research Manager synthesis
3. Trader: buy/sell/hold plan with decision log check
4. Risk Management: Aggressive/Conservative/Neutral -> Portfolio Manager

## Development stages

- Stage 0: Fork, env setup, first test run (DONE)
- Stage 1: Skills-based pipeline, UK ISA data integration (CURRENT)
- Stage 2: Claude Code Local Routine scheduling (daily/weekly)
- Stage 3: Self-learning (ChromaDB RAG + reflection loop)
- Stage 4: Portfolio optimisation + performance attribution

## Coding conventions

- No em dashes. Use short dashes or rephrase.
- Markdown for all structured output.
- Python: type hints, docstrings, ruff for formatting.
- Commit messages: conventional commits (feat:, fix:, docs:, chore:).
