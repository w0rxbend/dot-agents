# Project Context Files

Hermes reads context files from working directory into system prompt. Discovery is **first match wins** — only one project context source loads per session.

| File (in priority order) | Discovery | Use when |
|---|---|---|
| `.hermes.md` / `HERMES.md` | Walks parents, stops at git root | Hierarchical rules (root + per-package overrides) |
| `AGENTS.md` / `agents.md` | **Cwd only** — subdirectory and parent copies ignored | Portable instructions, same in Hermes, Claude Code, Codex, etc. |
| `CLAUDE.md` / `claude.md` | Cwd only | Same as AGENTS.md, Claude-flavored |
| `.cursorrules` / `.cursor/rules/*.mdc` | Cwd only | Migrating from Cursor |

`SOUL.md` (in `$HERMES_HOME`) is independent, always loaded when present. Sets agent identity, not project rules.

### Pick the right one

- **Use `.hermes.md`** for Hermes-specific rules above cwd (root + subtree) or inherited from parent directory. Walk stops at git root, so home-level `.hermes.md` won't leak into every project.
- **Use `AGENTS.md`** when other agents (Codex, Claude Code, OpenCode) share the project. They have own `AGENTS.md` conventions; "cwd only" contract keeps file portable.
- **Don't put project rules in `~/.hermes/AGENTS.md`** (or any other home-level location). Loads only when Hermes runs with that exact directory as cwd. Cross-project context: use `SOUL.md` (in `$HERMES_HOME`, identity-only) or install skill via `hermes skills install`.

### Size and truncation

Each context file capped at 20,000 characters. Longer files get **head + tail** truncated (middle dropped, `[...truncated...]` marker). Large project rules: split into multiple skills, not one crammed file.

### Security

All context files pass threat-pattern scanner before system prompt. Prompt-injection or promptware patterns become `[BLOCKED: ...]` placeholder. Scanner blocks content, not file: obvious injection attempts in `AGENTS.md` won't reach model, rest of file still loads.

### Disable for one session

`hermes --ignore-rules` skips auto-injection of all project context files (`.hermes.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`) **and** `SOUL.md` identity, plus user config, plugins, and MCP servers. Use to isolate whether problem is your setup or Hermes itself.

### Example: a small `.hermes.md`

```markdown
# My Project

Hermes: when working in this repo, follow these rules.

## Build
- Always run `make test` before declaring a change done.
- Use `uv run` for Python, not `pip install`.

## Style
- Prefer `pathlib.Path` over `os.path`.
- No `print()` in production code — use the `logger`.
```

File at `/home/me/projects/myrepo/.hermes.md` auto-loads when Hermes runs in any subdirectory of `/home/me/projects/myrepo`, not in `/home/me/other-project`.
