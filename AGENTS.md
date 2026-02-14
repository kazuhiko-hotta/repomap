# AGENTS.md

## Purpose
This repository is operated with AI assistants.
Prefer structural summaries over raw source code.
Avoid full repository scans.

## Reading Order
Read in this order:

1. REPO_MAP.md or ARCHITECTURE.md
2. MEMORY.md
3. PROGRESS.md
4. Source code (only if required)

Do not scan the entire repository unless explicitly requested.

## File Roles

AGENTS.md
Global agent behavior rules. Do not store temporary state.

REPO_MAP.md / ARCHITECTURE.md
Repository structure and dependency overview. Primary source for understanding. you can update this.

MEMORY.md
Long-term rules and constraints, and to avoid same mistakes. you can update this.

PROGRESS.md
Current working state. May be updated by agents. you can update this.

TASKS.md
Short-lived task list. you can update this.

DECISIONS.md (optional)
Architecture decision records.

## Exploration Rules

- Prefer directory-level understanding.
- Expand only necessary files.
- Limit code expansion per step.
- Prefer summaries over raw code.

## Update Rules

Agents may update:
- PROGRESS.md
- MEMORY.md
- generated repository maps

Agents must not modify:
- AGENTS.md
- historical records without explicit instruction.
