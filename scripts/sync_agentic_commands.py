#!/usr/bin/env python3
"""Generate Codex skills from Claude Code commands.

Claude Code commands in .claude/commands/*.md are the canonical source.
This script generates the corresponding Codex skills in
.agents/skills/source-command-*/SKILL.md.

Usage:
    python scripts/sync_agentic_commands.py          # generate
    python scripts/sync_agentic_commands.py --check   # verify, exit 1 if stale
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_DIR = REPO_ROOT / ".claude" / "commands"
CODEX_DIR = REPO_ROOT / ".agents" / "skills"

GENERATED_NOTICE = (
    "<!-- GENERATED from .claude/commands/{name}.md by sync_agentic_commands.py"
    " -- DO NOT EDIT -->"
)

PLATFORM_REPLACEMENTS = [
    ("Claude Code subagents", "Codex subagents"),
    ("Claude Code subagent", "Codex subagent"),
    (
        "Use the Agent tool to spawn subagents for each role.",
        "Spawn subagents for each role.",
    ),
    (" using the Agent tool", ""),
]

PATH_RE = re.compile(r"\.claude/commands/([a-z<>-]+)\.md")
CLAUDE_MD_RE = re.compile(r"(?<![/\w])CLAUDE\.md(?![/\w])")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        raise ValueError("missing frontmatter")
    end = text.index("---", 3)
    meta: dict[str, str] = {}
    for line in text[3:end].strip().splitlines():
        key, _, val = line.partition(":")
        meta[key.strip()] = val.strip()
    body = text[end + 3 :].lstrip("\n")
    return meta, body


def transform_body(body: str) -> str:
    for old, new in PLATFORM_REPLACEMENTS:
        body = body.replace(old, new)
    body = PATH_RE.sub(r".agents/skills/source-command-\1/SKILL.md", body)
    body = CLAUDE_MD_RE.sub("AGENTS.md", body)
    return body


def render_skill(name: str, meta: dict[str, str], body: str) -> str:
    transformed = transform_body(body)
    parts = [
        "---",
        f'name: "source-command-{name}"',
        f'description: "{meta["description"]}"',
        "---",
        GENERATED_NOTICE.format(name=name),
        "",
        f"# source-command-{name}",
        "",
        f"Use this skill when the user asks to run the source command `{name}`.",
        "",
        "## Command Template",
        "",
        transformed,
    ]
    return "\n".join(parts)


def sync(*, check: bool = False) -> int:
    commands = sorted(CLAUDE_DIR.glob("*.md"))
    if not commands:
        print("error: no Claude commands found in", CLAUDE_DIR, file=sys.stderr)
        return 1

    issues: list[str] = []

    for cmd_path in commands:
        name = cmd_path.stem
        meta, body = parse_frontmatter(cmd_path.read_text())
        expected = render_skill(name, meta, body)

        skill_dir = CODEX_DIR / f"source-command-{name}"
        skill_path = skill_dir / "SKILL.md"

        if check:
            if not skill_path.exists():
                issues.append(f"MISSING  {skill_path.relative_to(REPO_ROOT)}")
            elif skill_path.read_text() != expected:
                issues.append(f"STALE    {skill_path.relative_to(REPO_ROOT)}")
        else:
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(expected)
            print(f"  wrote  {skill_path.relative_to(REPO_ROOT)}")

    for skill_dir in sorted(CODEX_DIR.glob("source-command-*")):
        name = skill_dir.name.removeprefix("source-command-")
        if not (CLAUDE_DIR / f"{name}.md").exists():
            if check:
                issues.append(f"ORPHAN   {skill_dir.relative_to(REPO_ROOT)}")
            else:
                print(f"  orphan {skill_dir.relative_to(REPO_ROOT)} (not removed)")

    if check:
        if issues:
            print("Codex skills out of sync:", file=sys.stderr)
            for issue in issues:
                print(f"  {issue}", file=sys.stderr)
            return 1
        print(f"All {len(commands)} Codex skills in sync.")
        return 0

    print(f"Generated {len(commands)} Codex skills from Claude commands.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Codex skills from Claude Code commands."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify generated files are up to date without writing",
    )
    args = parser.parse_args()
    raise SystemExit(sync(check=args.check))
