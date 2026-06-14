# Stage 1 handoff prompt

Copy everything below the line into a new Claude Code session.

---

## Context

I'm building a multi-agent trading research system. The repo at `/Users/jarda/Repositories/trading-system` is a fork of TauricResearch/TradingAgents (v0.2.5), a LangGraph-based framework where specialised LLM agents analyse stocks and debate investment decisions.

**Stage 0 is complete:** the framework runs end-to-end using Claude Sonnet 4.6 via the Anthropic API. A test run on AAPL worked. But each run costs ~$1-2 in API credits, which is too expensive for regular portfolio analysis.

**Stage 1 goal:** Replace the API-based LLM calls with Claude Code skills and subagents that run on my Teams subscription tokens (no extra cost). Keep the Python data-fetching code, replace the LangGraph orchestration with Claude Code workflows.

## Key files to read first

1. `CLAUDE.md` - project rules, safety constraints, portfolio context
2. `DEVELOPMENT.md` - full development plan with implementation steps, agent prompt mapping, data flow diagram, and session wrap-up checklist
3. `config/portfolio.yaml` - my ISA holdings (4 ETFs + 1 OEIC fund)
4. `tradingagents/agents/` - the existing agent implementations (prompts to extract)
5. `tradingagents/dataflows/y_finance.py` - the data fetching code to wrap as CLI scripts
6. `tradingagents/agents/utils/agent_utils.py` - tool definitions used by analysts

## What to build (in order)

### Step 1: Data extraction scripts
Create Python CLI scripts in `scripts/` that wrap the existing yfinance dataflow code:
- `fetch_market_data.py <ticker> <date>` - OHLCV + 8 technical indicators (RSI, MACD, MACDH, Bollinger, SMA, ATR)
- `fetch_sentiment.py <ticker> <date>` - news headlines + StockTwits + Reddit
- `fetch_news.py <ticker> <date>` - ticker news + global macro news
- `fetch_fundamentals.py <ticker> <date>` - financials, balance sheet, cash flow, income

Each should output structured text to stdout that can be piped into a skill prompt.

### Step 2: Agent skills
Create Claude Code skills in `orchestration/skills/` with the prompts extracted from the existing agent files. The source files and their prompts are mapped in DEVELOPMENT.md.

### Step 3: Orchestration
Create a master skill or workflow that runs the full pipeline for a single ticker: fetch data -> 4 analysts in parallel -> bull/bear debate -> research manager -> trader -> 3-way risk debate -> portfolio manager -> save decision to Obsidian vault.

### Step 4: Portfolio-level analysis
A skill that reads `config/portfolio.yaml` and runs the pipeline for each holding with a yfinance ticker, then synthesises portfolio-level recommendations.

## Constraints

- Read CLAUDE.md safety rules. No real trades. No API keys in code.
- No em dashes in any output.
- Keep the data-fetching scripts thin wrappers around existing `tradingagents/dataflows/` code - don't rewrite what works.
- Test each step before moving to the next. Run a data fetch script first, then test one analyst skill with that data, then wire up the full pipeline.
- Follow the session wrap-up checklist in DEVELOPMENT.md before ending.
