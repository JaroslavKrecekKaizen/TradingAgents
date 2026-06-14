# Development plan

## Current state (Stage 1 in progress - 2026-06-13)

### Stage 1 progress
- [x] 4 data extraction CLI scripts (`scripts/fetch_*.py`) - tested with VUKG.L and AAPL
- [x] 12 agent skill files (`.claude/commands/*.md`) - all role prompts extracted
- [x] `analyse-ticker` orchestration skill - full pipeline definition
- [x] `analyse-portfolio` skill - portfolio-level analysis
- [x] Initial Codex mirror support in `.agents/skills/source-command-*/SKILL.md`
- [x] Codex filesystem config in `.codex/config.toml`
- [x] Agentic collaboration and skill-sync plan documented in `orchestration/AGENTIC-COLLABORATION.md`
- [x] End-to-end test of `/analyse-ticker` with 4 Vanguard ISA tickers: VUKG.L, VWRP.L, VFEG.L, VJPB.L
- [ ] End-to-end test of `/analyse-portfolio`
- [x] Source-first sync: `scripts/sync_agentic_commands.py` generates Codex skills from Claude commands

### What's new in Stage 1
- `scripts/` directory with 4 Python CLI scripts wrapping tradingagents/dataflows/
- `.claude/commands/` with 14 skill files (12 agent roles + 2 orchestration)
- `.agents/skills/` with Codex-compatible mirrors of the source commands
- Skills-based pipeline replaces LangGraph orchestration
- Zero API cost - runs on Teams subscription tokens via Claude Code subagents

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

### Portfolio
- `config/portfolio.yaml` populated from Vanguard Investor screenshot
- 5 holdings: LifeStrategy 100% (OEIC, no ticker), VUKG.L, VWRP.L, VFEG.L, VJPB.L
- LifeStrategy fund cannot be analysed via yfinance (not exchange-traded)

### Cost observation
- Single AAPL run with Sonnet 4.6: ~$1-2, ~12 min wall clock
- Running 4 ETFs regularly via API would be expensive (~$5-8/run)

### Files changed from upstream fork
- `.env` - added `TRADINGAGENTS_*` config vars
- `main.py` - changed ticker/date for test run
- `config/portfolio.yaml` - new file with ISA holdings
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
1. Reads `config/portfolio.yaml`
2. Runs analyse-ticker for each holding with a yfinance ticker
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

## Session wrap-up checklist

At the end of each development session, do the following:

1. **Update this file** - mark completed steps, note blockers, update current state
2. **Commit changes** - conventional commit messages (feat:, fix:, docs:, chore:)
3. **Update CLAUDE.md** if architecture or conventions changed
4. **Update AGENTS.md** if Codex architecture or conventions changed
5. **Update `orchestration/AGENTIC-COLLABORATION.md`** if command or skill sync rules changed
6. **Update `config/portfolio.yaml`** if holdings changed
7. **Note token/cost observations** for any test runs
8. **Write a handoff summary** - what was done, what's next, any gotchas
