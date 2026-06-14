---
name: "source-command-analyse-portfolio"
description: "Run the full analysis pipeline for all holdings in the ISA portfolio"
---
<!-- GENERATED from .claude/commands/analyse-portfolio.md by sync_agentic_commands.py -- DO NOT EDIT -->

# source-command-analyse-portfolio

Use this skill when the user asks to run the source command `analyse-portfolio`.

## Command Template

Run the full multi-agent trading analysis pipeline for each holding across all ISA accounts that has a yfinance ticker. Produce per-account summaries and a consolidated portfolio view.

Optional argument: date (defaults to today). Example:
- `/analyse-portfolio`
- `/analyse-portfolio 2026-06-13`

## Safety rules

- NEVER execute real trades. This produces research only.
- Do not use em dashes in any output. Use short dashes or rephrase.

## Pipeline

### Step 1: Read portfolio

Read all holding notes from the Obsidian vault portfolio folder at `/Users/jarda/Documents/ATES/10-projects/trading-system/portfolio/`. Each note has YAML frontmatter with `type: holding`, `account`, `ticker`, `isin`, and valuation fields.

All holdings are now analysable. For holdings with a `ticker` field, pass the ticker to `/analyse-ticker`. For holdings without a ticker but with an `isin` field, pass the ISIN instead - the pipeline auto-resolves ISINs to Yahoo Finance tickers.

**Vanguard ISA:** VUKG.L, VWRP.L (benchmark), VFEG.L, VJPB.L, LifeStrategy (via ISIN GB00B41XG308)
**AJ Bell ISA:** SGLP.L, PHGP.L, plus 4 funds via ISIN (GB00B0CNH163, LU1033663649, GB0031919235, IE00B5339C57)

### Step 2: Analyse each holding

For each holding, invoke the `/analyse-ticker` skill with either the ticker or ISIN. Run them sequentially to avoid overwhelming the system.

For each holding, collect:
- The portfolio manager's final rating
- The executive summary
- The investment thesis
- Key price levels

### Step 3: Per-account synthesis

For each account, produce a holdings summary table:

**Vanguard ISA:**

| Holding | Weight | Rating | Key Thesis | Current Price |
|---------|--------|--------|------------|---------------|
| VUKG.L | 17.25% | ... | ... | ... |
| VWRP.L | 27.86% | ... | ... | ... |
| VFEG.L | 8.57% | ... | ... | ... |
| VJPB.L | 17.67% | ... | ... | ... |
| LifeStrategy | 28.28% | N/A | No ticker | N/A |

**AJ Bell ISA:**

| Holding | Weight | Rating | Key Thesis | Current Price |
|---------|--------|--------|------------|---------------|
| L&G Global Tech | ~24% | N/A | No ticker | N/A |
| Fidelity Global Tech | ~20% | N/A | No ticker | N/A |
| Janus Henderson Financials | ~14% | N/A | No ticker | N/A |
| Polar Capital Insurance | ~14% | N/A | No ticker | N/A |
| PHGP.L | ~19% | ... | ... | ... |
| SGLP.L | ~9% | ... | ... | ... |

### Step 4: Consolidated portfolio view

Combine both accounts into a single view:

1. **Consolidated holdings table** - all holdings across both ISAs with combined weights (by value where available, by cost where not)

2. **Asset allocation** - break down by asset class (equity, commodity) and sector/geography across both accounts

3. **Correlation and diversification** - assess overlap and concentration across the combined portfolio. Note that the AJ Bell ISA is heavily tilted toward technology (~44% by cost) and gold (~28% by cost)

4. **Rebalancing recommendations** - consider cross-account rebalancing opportunities:
   - Holdings rated Overweight/Buy - increase allocation
   - Holdings rated Underweight/Sell - decrease allocation
   - Holdings rated Hold - maintain
   - Sector concentration risks across both accounts

5. **Risk assessment** - combined portfolio risk profile, concentrated risks, currency exposure

6. **Action items** - specific, prioritised recommendations per account

### Step 5: Save portfolio report

Write the portfolio analysis to the Obsidian vault. Always write directly to the vault path, never to the repo:

Path: `/Users/jarda/Documents/ATES/10-projects/trading-system/decisions/YYYY-MM-DD-PORTFOLIO.md`

### Step 6: Report to user

Present the consolidated portfolio summary with per-account tables, combined asset allocation, rebalancing recommendations, and action items.
