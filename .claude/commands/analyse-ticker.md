---
name: analyse-ticker
description: Run the full multi-agent trading analysis pipeline for a single ticker
---

Run the full multi-agent trading research pipeline for the given ticker. The pipeline replicates the TradingAgents framework using Claude Code subagents instead of API calls.

The argument should be a ticker symbol, optionally followed by a date (defaults to today). Examples:
- `/analyse-ticker VUKG.L`
- `/analyse-ticker AAPL 2026-06-13`

## Safety rules

- NEVER execute real trades. This produces research only.
- NEVER commit API keys or secrets.
- Always log decisions before acting on them.
- Every recommendation must include confidence level and risk assessment.
- Do not use em dashes in any output. Use short dashes or rephrase.

## Pipeline

Execute these steps in order. Use the Agent tool to spawn subagents for each role. Each subagent receives the role prompt from the corresponding skill file plus the relevant data context.

### Step 1: Parse arguments

Extract ticker and date from the args. If no date is provided, use today's date (YYYY-MM-DD format).

### Step 2: Fetch data (parallel)

Run all 4 data fetch scripts via Bash. These can run in parallel since they are independent:

```
.venv/bin/python scripts/fetch_market_data.py <ticker> <date>
.venv/bin/python scripts/fetch_sentiment.py <ticker> <date>
.venv/bin/python scripts/fetch_news.py <ticker> <date>
.venv/bin/python scripts/fetch_fundamentals.py <ticker> <date>
```

Capture each script's stdout as the data payload for the corresponding analyst.

### Step 3: Analyst reports (parallel)

Spawn 4 analyst subagents in parallel using the Agent tool. Each subagent receives:
- The role instructions from `.claude/commands/<role>.md`
- The relevant data from Step 2

The 4 analysts and their data sources:
1. **Market Analyst** - receives market data (OHLCV, indicators, verified snapshot)
2. **Sentiment Analyst** - receives sentiment data (news headlines, StockTwits, Reddit)
3. **News Analyst** - receives news data (ticker news, global macro news)
4. **Fundamentals Analyst** - receives fundamentals data (company overview, financials)

Each agent prompt should follow this template:

```
You are the [Role] in a multi-agent trading research team.
[Read and include the full instructions from the skill file]

The instrument to analyse is `<ticker>`. The analysis date is <date>.

Here is the data for your analysis:

<data from fetch script>

Write your report now.
```

Save each report for the next stage.

### Step 4: Bull/Bear debate (sequential, 2 rounds)

Run 2 rounds of debate between bull and bear researchers.

**Round 1 - Bull opens:**
Spawn a bull researcher subagent with:
- All 4 analyst reports from Step 3
- The bull researcher role prompt from `.claude/commands/bull-researcher.md`
- No prior debate history (this is the opening argument)

**Round 1 - Bear responds:**
Spawn a bear researcher subagent with:
- All 4 analyst reports
- The bear researcher role prompt
- The bull's opening argument as "Last bull argument"

**Round 2 - Bull counters:**
Spawn bull again with the full debate history so far and the bear's argument.

**Round 2 - Bear closes:**
Spawn bear again with the full debate history and the bull's latest argument.

### Step 5: Research Manager synthesis

Spawn a research manager subagent with:
- The instrument context (ticker)
- The full bull/bear debate history from Step 4
- The research manager role prompt from `.claude/commands/research-manager.md`

Save the investment plan (recommendation, rationale, strategic actions).

### Step 6: Trader proposal

Spawn a trader subagent with:
- The instrument context
- The Research Manager's investment plan from Step 5
- The trader role prompt from `.claude/commands/trader.md`

Save the transaction proposal (action, reasoning, entry/stop/sizing).

### Step 7: Risk debate (sequential, 2 rounds)

Run 2 rounds of the 3-way risk debate. Each debater receives the trader's proposal plus all analyst reports.

**Round 1:**
1. Aggressive risk analyst opens (prompt from `.claude/commands/risk-aggressive.md`)
2. Conservative risk analyst responds (with aggressive argument)
3. Neutral risk analyst responds (with both aggressive and conservative arguments)

**Round 2:**
1. Aggressive counters (with full history)
2. Conservative counters (with full history)
3. Neutral synthesises (with full history)

### Step 8: Portfolio Manager final decision

Spawn a portfolio manager subagent with:
- The instrument context
- The Research Manager's investment plan
- The Trader's proposal
- The full risk debate history from Step 7
- The portfolio manager role prompt from `.claude/commands/portfolio-manager.md`

### Step 9: Save decision

Write the final decision to the Obsidian vault using the filesystem MCP server. The decision file should follow the format specified in CLAUDE.md:

Path: `<vault>/10-projects/trading-system/decisions/YYYY-MM-DD-TICKER.md`

```markdown
# Decision: TICKER - ACTION

- **Date:** YYYY-MM-DD
- **Ticker:** TICKER
- **Action:** Buy / Sell / Hold / Overweight / Underweight
- **Confidence:** High / Medium / Low
- **Risk level:** 1-5
- **Rationale:** [1-3 sentence summary from portfolio manager]
- **Bull case:** [key bull argument summary]
- **Bear case:** [key bear argument summary]
- **Risk factors:** [top risks from risk debate]
- **Benchmark:** VWRP.L
```

If the filesystem MCP server is not available, write the decision to `decisions/YYYY-MM-DD-TICKER.md` in the repo instead.

### Step 10: Report to user

Present the final decision to the user with:
1. The portfolio manager's rating and executive summary
2. The investment thesis
3. Key price levels (entry, stop loss, target)
4. Time horizon
5. A note about where the full decision was saved

## Performance notes

This pipeline spawns approximately 16 subagents total:
- 4 analysts (parallel)
- 4 debate turns (bull/bear x 2 rounds)
- 1 research manager
- 1 trader
- 6 risk debate turns (3 debaters x 2 rounds)
- 1 portfolio manager

All run on Teams subscription tokens (no API cost). Expect 5-10 minutes wall clock time.
