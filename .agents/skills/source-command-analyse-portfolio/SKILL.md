---
name: "source-command-analyse-portfolio"
description: "Run the full analysis pipeline for all holdings in the ISA portfolio"
---
<!-- GENERATED from .claude/commands/analyse-portfolio.md by sync_agentic_commands.py -- DO NOT EDIT -->

# source-command-analyse-portfolio

Use this skill when the user asks to run the source command `analyse-portfolio`.

## Command Template

Run the full multi-agent trading analysis pipeline for each holding in the ISA portfolio that has a yfinance ticker. Then synthesise portfolio-level recommendations.

Optional argument: date (defaults to today). Example:
- `/analyse-portfolio`
- `/analyse-portfolio 2026-06-13`

## Safety rules

- NEVER execute real trades. This produces research only.
- Do not use em dashes in any output. Use short dashes or rephrase.

## Pipeline

### Step 1: Read portfolio

Read `config/portfolio.yaml` to get the list of holdings. Filter to holdings that have a non-null `ticker` field (LifeStrategy 100% is excluded because it has no yfinance ticker).

The holdings with tickers are:
- VUKG.L (Vanguard FTSE 100 UCITS ETF)
- VWRP.L (Vanguard FTSE All-World UCITS ETF) - also the benchmark
- VFEG.L (Vanguard FTSE Emerging Markets UCITS ETF)
- VJPB.L (Vanguard FTSE Japan UCITS ETF)

### Step 2: Analyse each holding

For each holding with a ticker, invoke the `/analyse-ticker` skill (or run the same pipeline manually). Run them sequentially to avoid overwhelming the system.

For each holding, collect:
- The portfolio manager's final rating
- The executive summary
- The investment thesis
- Key price levels

### Step 3: Portfolio-level synthesis

After all individual analyses are complete, synthesise a portfolio-level view:

1. **Holdings summary table:**

| Holding | Weight | Rating | Key Thesis | Current Price |
|---------|--------|--------|------------|---------------|
| VUKG.L | 17.25% | ... | ... | ... |
| VWRP.L | 27.86% | ... | ... | ... |
| VFEG.L | 8.57% | ... | ... | ... |
| VJPB.L | 17.67% | ... | ... | ... |
| LifeStrategy | 28.28% | N/A | No ticker | N/A |

2. **Correlation and diversification** - Are the holdings well-diversified? Do they cover different geographies and sectors? Are any positions redundant?

3. **Rebalancing recommendations** - Based on the individual ratings, should any positions be adjusted? Consider:
   - Holdings rated Overweight/Buy - increase allocation
   - Holdings rated Underweight/Sell - decrease allocation
   - Holdings rated Hold - maintain
   - Overall portfolio balance across regions

4. **Risk assessment** - What is the portfolio's overall risk profile? Are there concentrated risks (e.g. all holdings correlated to US tech)?

5. **Action items** - Specific, prioritised recommendations for the next rebalancing.

### Step 4: Save portfolio report

Write the portfolio analysis to the Obsidian vault:
Path: `<vault>/10-projects/trading-system/decisions/YYYY-MM-DD-PORTFOLIO.md`

If the filesystem MCP server is not available, write to `decisions/YYYY-MM-DD-PORTFOLIO.md` in the repo.

### Step 5: Report to user

Present the portfolio-level summary with the holdings table, rebalancing recommendations, and action items.
