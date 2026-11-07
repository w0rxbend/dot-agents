---
name: caveman-help
description: >
  Quick-reference card for the three caveman skills and their commands.
  Trigger: /caveman-help or "caveman help".
---

# Caveman Help

Display reference card when invoked. One-shot: do NOT change mode, write flag files or persist anything. Output in caveman style.

## Modes

| Mode | Trigger | What change |
|------|---------|-------------|
| **caveman** | `/caveman` | Voice. Answer first, no fluff, every fact kept. Default. |
| **ultracave** | `/ultracave` (alias `/caveman ultra`) | Grammar stripped. Fragments, one word when enough, each fact once. |
| **megacave** | `/megacave` (alias `/caveman wenyan`) | Classical Chinese 文言文. Far fewer characters, technical terms verbatim. |

Mode stick until changed or session end.
`/caveman status` reports current mode without changing it. Stored mode state exists only when upstream Caveman hooks or OpenCode plugin are installed. dot-agents installs skills alone. Without hooks or plugin, mode comes from conversation context. Reported as `unknown` if no mode known.

## Skills

| Skill | Trigger | What it do |
|-------|---------|-----------|
| **caveman-commit** | `/caveman-commit` | Terse commit messages. Conventional Commits. ≤50 char subject. |
| **caveman-review** | `/caveman-review` | One-line PR comments: `L42: bug: user null. Add guard.` |
| **caveman-compress** | `/caveman-compress <file>` | Compress .md files to caveman prose. Saving varies by file. Measure; do not assume a figure. |
| **caveman-help** | `/caveman-help` | This card. |

## Deactivate

Say "stop caveman" or "normal mode". Resume anytime with `/caveman`.

## Language

Keep user's language by default: reply in language user writes. Never switch, regardless of example text or multilingual context elsewhere. Compress style, not language. Technical terms, code, commands, commit types and exact error strings stay verbatim unless user asks for translation.

## Configure Default Mode

Default mode: `caveman`. Upstream Caveman hooks and installer (https://github.com/JuliusBrussee/caveman) read settings below. With skills alone, settings have no effect. Change it:

**Environment variable** (highest priority):
```bash
export CAVEMAN_DEFAULT_MODE=ultracave
```

**Config file** (`~/.config/caveman/config.json`):
```json
{ "defaultMode": "ultracave" }
```

For opt-in activation in Claude Code, set `defaultMode` to `manual`. Sessions start off. `/caveman` or `talk like caveman` activates caveman. `manual` is startup policy, not a mode. OpenCode still starts in caveman mode: its installer also supplies static activation rules.

Set `"off"` to suppress automatic and bare-command activation. Use `"manual"` when bare `/caveman` should activate.

Resolution: env var > repo config > user config > `caveman`. Legacy values `lite`, `full`, `ultra`, `wenyan*` still resolve.

## More

Full docs: https://github.com/JuliusBrussee/caveman
