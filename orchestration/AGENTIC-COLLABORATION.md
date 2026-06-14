# Agentic collaboration and skill sync

## Purpose

This note documents how Claude Code and Codex currently execute the skills-based
TradingAgents workflow, and recommends the next development stage to reduce drift
between duplicated command and skill files.

The aim is to keep the agent workflow easy to run from either tool while avoiding
silent divergence in prompts, tool commands, safety rules, and output formats.

## Current support

Initial Codex execution support is implemented as a mirror of the Claude Code
slash commands.

- Claude Code commands live in `.claude/commands/*.md`.
- Codex skills live in `.agents/skills/source-command-*/SKILL.md`.
- Codex skill names use the `source-command-` prefix so they can coexist with
  other local skills.
- Codex filesystem MCP config lives in `.codex/config.toml` and mirrors the
  repository plus Obsidian vault access configured in `.mcp.json`.
- Root project context is duplicated as `CLAUDE.md` for Claude Code and
  `AGENTS.md` for Codex.
- Both execution surfaces share the same Python data tools in `scripts/`.

The Codex skill bodies are intentionally close to the Claude command bodies.
Codex adds skill frontmatter, a skill heading, a trigger sentence, and a
`Command Template` wrapper. The role and pipeline instructions should remain
semantically identical unless a platform-specific difference is required.

## Valid platform differences

These differences are expected and should not be treated as drift:

- Claude commands refer to Claude Code, while Codex skills refer to Codex.
- Claude role prompts are referenced via `.claude/commands/<role>.md`.
- Codex role prompts are referenced via
  `.agents/skills/source-command-<role>/SKILL.md`.
- Claude commands reference `CLAUDE.md` for root project rules.
- Codex skills reference `AGENTS.md` for root project rules.
- Codex skill metadata and wrapper text differ from Claude command metadata.

## Invalid drift

These differences should be fixed as soon as they are found:

- Safety rules differ between Claude and Codex surfaces.
- A role prompt changes in one surface but not the other.
- Data fetch command names, arguments, or output expectations differ.
- Rating scales, confidence requirements, or risk requirements differ.
- Decision log format differs.
- Portfolio scope differs.
- Any file references point to paths that do not exist.

## Current operating rule

Until the sync tooling exists, treat `.claude/commands/*.md` and
`.agents/skills/source-command-*/SKILL.md` as paired files.

When changing a command or skill:

1. Update both paired files in the same commit.
2. Preserve only the valid platform differences listed above.
3. Check for stale path references with `rg`.
4. Review the diff before staging.
5. Keep safety rules and output contracts identical.

## Recommended next stage

The recommended next stage is to replace hand-maintained copies with a
source-first agentic command system.

### 1. Add canonical source files

Create a canonical command source directory, for example:

```text
orchestration/agentic/commands/
  analyse-ticker.md
  analyse-portfolio.md
  market-analyst.md
  sentiment-analyst.md
  news-analyst.md
  fundamentals-analyst.md
  bull-researcher.md
  bear-researcher.md
  research-manager.md
  trader.md
  risk-aggressive.md
  risk-conservative.md
  risk-neutral.md
  portfolio-manager.md
```

Each source file should contain the platform-neutral role or pipeline
instructions. Platform-specific path references should use placeholders such as
`{{role_prompt_path}}` or `{{project_rules_file}}`.

### 2. Add a manifest for metadata and tools

Create a machine-readable manifest, for example:

```text
orchestration/agentic/manifest.yaml
```

The manifest should define:

- command name and description
- command type, such as role or pipeline
- matching Claude output path
- matching Codex output path
- required data fetch scripts
- expected input and output contract
- allowed tool commands
- safety gates

This creates one visible place to review the workflow contract.

### 3. Generate Claude and Codex adapters

Add a sync script, for example:

```text
scripts/sync_agentic_commands.py
```

The script should render:

- `.claude/commands/*.md`
- `.agents/skills/source-command-*/SKILL.md`

The generated files should include a short header saying they are generated from
`orchestration/agentic/`. After this point, agents should edit the canonical
source files, not the generated adapters.

### 4. Add drift checks

The sync script should support:

```bash
.venv/bin/python scripts/sync_agentic_commands.py --check
```

The check mode should fail when generated files are missing, stale, or contain
unexpected platform path references.

Useful validation checks:

- every Claude command has a matching Codex skill
- every Codex skill has a matching Claude command
- no legacy Codex command-directory references exist
- all referenced local files exist
- safety rule blocks are identical
- data fetch commands match the shared manifest

### 5. Treat data scripts as shared tools

The existing scripts in `scripts/` should be treated as the shared tool layer for
both Claude Code and Codex.

Add a small tool contract document or manifest section for each script:

- command invocation
- arguments
- whether network access is expected
- stdout sections produced
- known failure modes
- whether output can be cached

This gives future agents a clear tool boundary and reduces prompt-level
guesswork.

### 6. Add development workflow guidance

Document the expected agentic development loop:

1. Update canonical command source or tool contract.
2. Run the sync script.
3. Run the drift check.
4. Run targeted tests or a dry-run data fetch.
5. Commit source, generated adapters, and docs together.

Small, reviewable commits are preferred. Any prompt, safety, or tool contract
change should be explicit in the commit message.

## Milestone recommendation

This is a good milestone to commit before refactoring because it captures the
current mirror state, fixes stale Codex paths, and records the plan before
introducing generation tooling. The next development stage can then focus on
building the source-first sync layer without mixing it with the initial Codex
support commit.
