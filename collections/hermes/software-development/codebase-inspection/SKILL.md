---
name: codebase-inspection
description: "Inspect codebases w/ pygount: LOC, languages, ratios."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [LOC, Code Analysis, pygount, Codebase, Metrics, Repository]
    related_skills: [github]
prerequisites:
  commands: [pygount]
---

# Codebase Inspection with pygount

## When to Use

- User asks for LOC (lines of code) count
- User wants language breakdown of repo
- User asks about codebase size or composition
- User wants code-vs-comment ratios
- General "how big is this repo" questions

## Prerequisites

```bash
# Isolated CLI install (preferred) — do not disable the PEP 668 guard on system Python
pipx install pygount   # or: uv tool install pygount
# Inside an already-active virtualenv, plain `pip install pygount` is fine
```

## 1. Basic Summary (Most Common)

```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs,*.egg-info" \
  .
```

**IMPORTANT:** Always use `--folders-to-skip` to exclude dependency and build directories (at minimum .git, node_modules, venv). Otherwise pygount crawls them and may take minutes or hang on large dependency trees.

## 2. Common Folder Exclusions

Adjust per project type:

```bash
# Python projects
--folders-to-skip=".git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache"

# JavaScript/TypeScript projects
--folders-to-skip=".git,node_modules,dist,build,.next,.cache,.turbo,coverage"

# General catch-all
--folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,vendor,third_party"
```

## 3. Filter by Specific Language

```bash
# Only count Python files
pygount --suffix=py --format=summary .

# Only count Python and YAML
pygount --suffix=py,yaml,yml --format=summary .
```

## 4. Detailed File-by-File Output

```bash
# Default format shows per-file breakdown
pygount --folders-to-skip=".git,node_modules,venv" .

# Sort by code lines (pipe through sort)
pygount --folders-to-skip=".git,node_modules,venv" . | sort -t$'\t' -k1 -nr | head -20
```

## 5. Output Formats

```bash
# Summary table (default recommendation)
pygount --format=summary .

# JSON output for programmatic use
pygount --format=json .

# Pipe-friendly: Language, file count, code, docs, empty, string
pygount --format=summary . 2>/dev/null
```

## 6. Interpreting Results

Summary table columns:
- **Language** — detected programming language
- **Files** — file count for that language
- **Code** — lines of code (executable/declarative)
- **Comment** — comment or documentation lines
- **%** — percentage of total

Special pseudo-languages:
- `__empty__` — empty files
- `__binary__` — binary files (images, compiled, etc.)
- `__generated__` — auto-generated files (detected heuristically)
- `__duplicate__` — files with identical content
- `__unknown__` — unrecognized file types

## Pitfalls

1. **Markdown shows 0 code lines** — pygount classifies all Markdown content as comments, not code. Expected behavior.
2. **JSON files show low code counts** — pygount may count JSON lines conservatively. For accurate JSON line counts, use `wc -l` directly.
3. **Large monorepos** — for very large repos, consider `--suffix` to target specific languages instead of scanning everything.
