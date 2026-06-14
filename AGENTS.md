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
  .agents/
    skills/                      # Codex skills mirrored from Claude commands
      source-command-analyse-ticker/SKILL.md       # Master pipeline for single-ticker analysis
      source-command-analyse-portfolio/SKILL.md    # Portfolio-level analysis across all holdings
      source-command-market-analyst/SKILL.md       # Technical analysis role
      source-command-sentiment-analyst/SKILL.md    # Sentiment analysis role
      source-command-news-analyst/SKILL.md         # News research role
      source-command-fundamentals-analyst/SKILL.md # Financial analysis role
      source-command-bull-researcher/SKILL.md      # Bullish case advocate
      source-command-bear-researcher/SKILL.md      # Bearish case advocate
      source-command-research-manager/SKILL.md     # Debate synthesis into investment plan
      source-command-trader/SKILL.md               # Investment plan to transaction proposal
      source-command-risk-aggressive/SKILL.md      # High-risk/high-reward advocate
      source-command-risk-conservative/SKILL.md    # Asset protection advocate
      source-command-risk-neutral/SKILL.md         # Balanced perspective
      source-command-portfolio-manager/SKILL.md    # Final decision synthesis
  orchestration/
    routines/                    # Routine definitions
    hooks/                       # Lifecycle hooks (decision logging, safety)
  config/
    portfolio.yaml               # ISA holdings, tickers, weights, simulation params
    providers.yaml               # API provider config (no secrets - those go in .env)
  AGENTS.md                      # This file
  .mcp.json                      # MCP server configuration
  .env                           # API keys (gitignored, never committed)
  .gitignore
  requirements.txt               # From upstream + our extensions
```

## Obsidian vault structure

The Obsidian vault path is configured in .mcp.json under the filesystem MCP server.
All knowledge and logs live there:

```
<vault>/10-projects/trading-system/
  decisions/                     # Structured decision records (YYYY-MM-DD-TICKER.md)
  reflections/                   # Post-hoc outcome analysis, lessons learned
  market-notes/                  # Manual observations
  books/                         # Trading theory book summaries
  papers/                        # Research paper notes
  performance/                   # QuantStats reports, weekly/monthly metrics
```

## Codex skill mirror

Codex executes the skills-based pipeline through mirrored skills in
`.agents/skills/source-command-*/SKILL.md`. These mirror the Claude Code
commands in `.claude/commands/*.md`, with only platform-specific wrappers and
path references changed.

When editing agent prompts or pipeline steps, keep the Claude and Codex surfaces
in sync. See `orchestration/AGENTIC-COLLABORATION.md` for the current mirror
contract and the next-stage source-first sync plan.

### Decision log format

Each decision is a markdown file: `decisions/YYYY-MM-DD-TICKER.md`

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

See config/portfolio.yaml for full details. Holdings (all accumulating share classes):

- LifeStrategy 100% Equity Fund Acc (OEIC, no yfinance ticker - 28%)
- VUKG.L (FTSE 100 Acc - 17%)
- VWRP.L (All-World Acc - 28%) - also the benchmark
- VFEG.L (Emerging Markets Acc - 9%)
- VJPB.L (Japan Acc - 18%)

Total cost: ~GBP 49,750. Total value: ~GBP 46,050.

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

Codex via Anthropic API (Teams subscription). Configure in .env:

- ANTHROPIC_API_KEY for Codex access
- Use Codex Sonnet for analyst/retrieval agents (cost-efficient)
- Use Codex Opus for debate/decision nodes (reasoning quality)

## Agent architecture

Seven agents across four teams (TradingAgents upstream design):

1. Analyst Team (parallel): Fundamentals, Sentiment, News, Technical
2. Research Team: Bull + Bear debate -> Research Manager synthesis
3. Trader: buy/sell/hold plan with decision log check
4. Risk Management: Aggressive/Conservative/Neutral -> Portfolio Manager

## Development stages

- Stage 0: Fork, env setup, first test run (DONE)
- Stage 1: Skills-based pipeline, UK ISA data integration (CURRENT)
- Stage 2: Codex Local Routine scheduling (daily/weekly)
- Stage 3: Self-learning (ChromaDB RAG + reflection loop)
- Stage 4: Portfolio optimisation + performance attribution

## Coding conventions

- No em dashes. Use short dashes or rephrase.
- Markdown for all structured output.
- Python: type hints, docstrings, ruff for formatting.
- Commit messages: conventional commits (feat:, fix:, docs:, chore:).
