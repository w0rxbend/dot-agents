---
name: caveman-stats
description: >
  Show recorded output and cache-read token usage and mode attribution for
  the current Claude Code session, or locate the host's native usage report.
  Trigger: /caveman-stats. Needs the upstream Caveman Claude Code hooks for
  the Claude Code report.
---

## Prerequisite: Caveman hooks (Claude Code)

Upstream Caveman hooks produce the Claude Code report
(`caveman-mode-tracker.js` and `caveman-stats.js` from
https://github.com/JuliusBrussee/caveman). dot-agents installs only this skill,
not hooks. Check: report exists only if hook-injected caveman-stats output
arrived with the `/caveman-stats` prompt (can also look for `caveman-mode-tracker`
under `hooks` in `~/.claude/settings.json` or `.claude/settings.json`). If absent, do
not build a report yourself. Say: "caveman-stats needs the Caveman Claude Code
hooks, which are not installed, so no Caveman usage report is available. Use
the host's own usage command (for example `/cost` in Claude Code) instead."

In Claude Code with hooks installed, `caveman-mode-tracker.js` resolves `caveman-stats.js` next to itself and runs it on `/caveman-stats`. Hook does not block the prompt. It supplies the report via `hookSpecificOutput.additionalContext`, plus an instruction to print it verbatim in a fenced code block. Do exactly that. Do not calculate, recompute or re-round numbers yourself.

Gemini CLI: send user to `/stats model` for current session token usage or `/stats session` for session statistics. Gemini custom commands are prompts: they cannot invoke the built-in command or read its live session metrics. Never read Claude Code transcripts as Gemini usage. Other hosts: use native usage report if one exists; else say current session usage is unavailable. Claude reader and its lifetime history apply only to Claude Code. Savings stay unknown in every host without measured comparison.

Report shows recorded output and cache-read tokens, response counts and mode attribution where available. Savings unknown: transcript has no measured comparison without Caveman. Do not infer saved tokens, percentages, dollars, rule overhead or net result from output counts or current mode.

`--all` and `--since 7d` aggregate latest recorded output count per session. `--share` reports observed usage, savings unknown. Historical `est_saved_*` fields ignored; original history rows stay on disk. Statusline shows active mode, without retired savings badge.

Original/current memory-file pairs: reported by measured byte sizes. File-size differences do not prove provider token or billing savings. See upstream `docs/HONEST-NUMBERS.md` (https://github.com/JuliusBrussee/caveman/blob/main/docs/HONEST-NUMBERS.md).
