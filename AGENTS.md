# Trading System - Codex Project Context

Read `CLAUDE.md` for the full project context, safety rules, portfolio details,
and development stages. Everything there applies to Codex sessions too.

This file covers only the Codex-specific differences.

## Codex skill paths

Codex skills are generated from the canonical Claude Code commands by
`scripts/sync_agentic_commands.py`. Do not edit the generated SKILL.md files
directly - edit the source in `.claude/commands/*.md` and re-run the sync script.

- Skills: `.agents/skills/source-command-*/SKILL.md`
- Config: `.codex/config.toml`

## Python interpreter

Codex skills use `.venv/bin/python` to invoke data fetch scripts, ensuring the
virtual environment is used regardless of shell activation state.

## LLM provider

The LLM provider is Claude via Anthropic API, same as Claude Code sessions.
Codex orchestrates the pipeline; Claude provides the reasoning. Configure in
`.env`:

- `ANTHROPIC_API_KEY` for Claude access
- Use Claude Sonnet for analyst/retrieval agents (cost-efficient)
- Use Claude Opus for debate/decision nodes (reasoning quality)
