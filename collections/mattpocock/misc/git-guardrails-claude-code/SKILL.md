---
name: git-guardrails-claude-code
description: Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code.
---

# Setup Git Guardrails

Sets up a PreToolUse hook that intercepts and blocks dangerous git commands before Claude executes them.

## What Gets Blocked

- `git push` (any flags, including `--force`)
- `git reset --hard`
- `git clean` with any force flag (`-f`, `-df`, `-xfd`, `--force`), unless it is a dry run (`-n`)
- `git branch -D` / `git branch --delete --force`
- `git checkout .` / `git checkout -- .` / `git checkout --force`
- `git restore .` (except `git restore --staged .`, which only unstages)

The script tokenizes the command instead of substring-matching it: it splits on `;`, `&&`, `|`, newlines and subshells, skips `VAR=x`, `env`, `sudo`, `xargs` and similar prefixes, looks inside `bash -c` / `sh -c` / `eval` strings and `$(...)`, and ignores git global options such as `-C <dir>`. Quoted arguments such as commit messages are not treated as commands, so `git commit -m "don't git push"` is allowed.

When blocked, Claude sees a message telling it that it does not have authority to run the command.

This is a best-effort guard, not a sandbox: git aliases, scripts or Makefiles that call git internally, and deliberate obfuscation are not detected. For a harder stop, also add `permissions.deny` rules (for example `"Bash(git push:*)"`) to the same settings file.

**Prerequisite:** the hook needs `jq`. It fails closed: if `jq` is missing or the hook input cannot be parsed, it blocks every Bash command. Check `command -v jq` before installing and install jq first if it is absent.

## Steps

### 1. Ask scope

Ask the user: install for **this project only** (`.claude/settings.json`) or **all projects** (`~/.claude/settings.json`)?

### 2. Copy the hook script

The bundled script is at: [scripts/block-dangerous-git.sh](scripts/block-dangerous-git.sh)

Copy it to the target location based on scope:

- **Project**: `.claude/hooks/block-dangerous-git.sh`
- **Global**: `~/.claude/hooks/block-dangerous-git.sh`

Make it executable with `chmod +x`.

### 3. Add hook to settings

Add to the appropriate settings file:

**Project** (`.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

**Global** (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

If the settings file already exists, merge the hook into the existing `hooks.PreToolUse` array. Don't overwrite other settings.

### 4. Ask about customization

Ask if user wants to add or remove any blocked commands. Edit the `case $sub in` rules in `check_git` in the copied script accordingly.

### 5. Verify

Run a quick test:

```bash
echo '{"tool_input":{"command":"git push origin main"}}' | <path-to-script>
```

Should exit with code 2 and print a BLOCKED message to stderr. Also check a bypass and a false-positive case:

```bash
echo '{"tool_input":{"command":"git -C . push"}}' | <path-to-script>                 # exit 2
echo '{"tool_input":{"command":"git commit -m \"avoid git push\""}}' | <path-to-script>  # exit 0
```
