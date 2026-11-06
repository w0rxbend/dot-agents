---
name: git-guardrails-claude-code
description: Set up Claude Code hooks to block dangerous git commands (push, reset --hard, clean, branch -D, etc.) before they execute. Use when user wants to prevent destructive git operations, add git safety hooks, or block git push/reset in Claude Code.
---

# Setup Git Guardrails

## What Gets Blocked

- `git push` (any flags, including `--force`)
- `git reset --hard`
- `git clean` with any force flag (`-f`, `-df`, `-xfd`, `--force`), unless dry run (`-n`)
- `git branch -D` / `git branch --delete --force`
- `git checkout .` / `git checkout -- .` / `git checkout --force`
- `git restore .` (except `git restore --staged .`, which only unstages)

Script tokenizes command instead of substring-matching. Splits on `;`, `&&`, `|`, newlines and subshells. Skips `VAR=x`, `env`, `sudo`, `xargs` and similar prefixes. Looks inside `bash -c` / `sh -c` / `eval` strings and `$(...)`. Ignores git global options such as `-C <dir>`. Quoted arguments like commit messages are not commands, so `git commit -m "don't git push"` is allowed.

When blocked, Claude gets message saying it does not have authority to run command.

Best-effort guard, not sandbox. Not detected: git aliases, scripts or Makefiles calling git internally, deliberate obfuscation. Harder stop: also add `permissions.deny` rules (for example `"Bash(git push:*)"`) to same settings file.

**Prerequisite:** hook needs `jq`. Fails closed: if `jq` is missing or hook input cannot be parsed, it blocks every Bash command. Check `command -v jq` before installing. Install jq first if absent.

## Steps

### 1. Ask scope

Ask user: install for **this project only** (`.claude/settings.json`) or **all projects** (`~/.claude/settings.json`)?

### 2. Copy the hook script

Bundled script: [scripts/block-dangerous-git.sh](scripts/block-dangerous-git.sh)

Copy to target location by scope:

- **Project**: `.claude/hooks/block-dangerous-git.sh`
- **Global**: `~/.claude/hooks/block-dangerous-git.sh`

Make executable with `chmod +x`.

### 3. Add hook to settings

Add to matching settings file:

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

If settings file exists, merge hook into existing `hooks.PreToolUse` array. Do not overwrite other settings.

### 4. Ask about customization

Ask if user wants to add or remove blocked commands. Edit `case $sub in` rules in `check_git` in copied script to match.

### 5. Verify

Run quick test:

```bash
echo '{"tool_input":{"command":"git push origin main"}}' | <path-to-script>
```

Expect exit code 2 and BLOCKED message on stderr. Also check bypass and false-positive cases:

```bash
echo '{"tool_input":{"command":"git -C . push"}}' | <path-to-script>                 # exit 2
echo '{"tool_input":{"command":"sudo -u bob git push"}}' | <path-to-script>          # exit 2
echo '{"tool_input":{"command":"git commit -m \"avoid git push\""}}' | <path-to-script>  # exit 0
```
