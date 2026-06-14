---
name: "source-command-analyse-ticker"
description: "Run the full multi-agent trading analysis pipeline for a single ticker"
---
<!-- GENERATED from .claude/commands/analyse-ticker.md by sync_agentic_commands.py -- DO NOT EDIT -->

# source-command-analyse-ticker

Use this skill when the user asks to run the source command `analyse-ticker`.

## Command Template

Run the full multi-agent trading research pipeline for the given ticker. The pipeline replicates the TradingAgents framework using Codex subagents instead of API calls.

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

Execute these steps in order. Spawn subagents for each role. Each subagent receives the role prompt from the corresponding skill file plus the relevant data context.

### Step 1: Parse arguments

Extract ticker/ISIN and date from the args. If no date is provided, use today's date (YYYY-MM-DD format).

Detect whether the input is an ISIN (12 characters, starts with 2-letter country code, e.g. IE00B5339C57) or a ticker (e.g. VUKG.L). This determines which fetch scripts to use in Step 2.

### Step 2: Fetch data (parallel)

Run all 4 data fetch scripts via Bash. These can run in parallel since they are independent.

**For tickers** (e.g. VUKG.L, AAPL):
```
.venv/bin/python scripts/fetch_market_data.py <ticker> <date>
.venv/bin/python scripts/fetch_sentiment.py <ticker> <date>
.venv/bin/python scripts/fetch_news.py <ticker> <date>
.venv/bin/python scripts/fetch_fundamentals.py <ticker> <date>
```

**For ISINs** (e.g. IE00B5339C57 - OEIC/SICAV funds):
```
.venv/bin/python scripts/fetch_market_data.py <ISIN> <date>
.venv/bin/python scripts/fetch_sentiment.py <ISIN> <date>
.venv/bin/python scripts/fetch_news.py <ISIN> <date>
.venv/bin/python scripts/fetch_fund_profile.py <ISIN> <date>
```

The ISIN is resolved to a Yahoo Finance ticker automatically by the scripts. The key difference is that ISINs use `fetch_fund_profile.py` instead of `fetch_fundamentals.py` because funds have holdings and sector data, not company financial statements.

Capture each script's stdout as the data payload for the corresponding analyst.

### Step 3: Analyst reports (parallel)

Spawn 4 analyst subagents in parallel. Each subagent receives:
- The role instructions from `.agents/skills/source-command-<role>/SKILL.md`
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
- The bull researcher role prompt from `.agents/skills/source-command-bull-researcher/SKILL.md`
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
- The research manager role prompt from `.agents/skills/source-command-research-manager/SKILL.md`

Save the investment plan (recommendation, rationale, strategic actions).

### Step 6: Trader proposal

Spawn a trader subagent with:
- The instrument context
- The Research Manager's investment plan from Step 5
- The trader role prompt from `.agents/skills/source-command-trader/SKILL.md`

Save the transaction proposal (action, reasoning, entry/stop/sizing).

### Step 7: Risk debate (sequential, 2 rounds)

Run 2 rounds of the 3-way risk debate. Each debater receives the trader's proposal plus all analyst reports.

**Round 1:**
1. Aggressive risk analyst opens (prompt from `.agents/skills/source-command-risk-aggressive/SKILL.md`)
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
- The portfolio manager role prompt from `.agents/skills/source-command-portfolio-manager/SKILL.md`

### Step 9: Save decision

Write the final decision to the Obsidian vault. Use the Write tool (or Bash `mkdir -p` + Write) to save directly to the vault path:

Path: `/Users/jarda/Documents/ATES/10-projects/trading-system/decisions/YYYY-MM-DD-TICKER.md`

Always write to the vault, never to the repo. The `decisions/` directory already exists in the vault.

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
