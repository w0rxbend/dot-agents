---
name: caveman-stats
description: >
  Show recorded output and cache-read token usage and mode attribution for
  the current Claude Code session, or locate the host's native usage report.
  Trigger: /caveman-stats. Needs the upstream Caveman Claude Code hooks for
  the Claude Code report.
---

## Prerequisite: Caveman hooks (Claude Code)

The Claude Code report is produced by upstream Caveman hooks
(`caveman-mode-tracker.js` and `caveman-stats.js` from
https://github.com/JuliusBrussee/caveman). dot-agents installs only this skill,
not the hooks. Check: the report is present only if hook-injected context with
the caveman-stats output arrived with the `/caveman-stats` prompt (you can also
look for `caveman-mode-tracker` in the `hooks` section of
`~/.claude/settings.json` or `.claude/settings.json`). If it is absent, do not
build a report yourself. Say: "caveman-stats needs the Caveman Claude Code
hooks, which are not installed, so no Caveman usage report is available. Use
the host's own usage command (for example `/cost` in Claude Code) instead."

In Claude Code with the hooks installed, `caveman-mode-tracker.js` resolves `caveman-stats.js` next to itself and runs it on `/caveman-stats`. The hook does not block the prompt: it supplies the report through `hookSpecificOutput.additionalContext` with an instruction to print it verbatim inside a fenced code block. Do exactly that, and do not calculate, recompute or re-round the numbers yourself.

In Gemini CLI, direct the user to `/stats model` for current session token usage or `/stats session` for session statistics. Gemini custom commands are prompts; they cannot invoke the built-in command or read its live session metrics. Never read Claude Code transcripts as Gemini usage. In other hosts, use a native usage report if one is available; otherwise say that current session usage is unavailable. The Claude reader and its lifetime history apply only to Claude Code. Savings remain unknown in every host without a measured comparison.

The report shows recorded output and cache-read tokens, response counts, and mode attribution where available. Savings are unknown: the transcript has no measured comparison without Caveman. Do not infer saved tokens, percentages, dollars, rule overhead, or a net result from output counts or the current mode.

`--all` and `--since 7d` aggregate the latest recorded output count per session. `--share` reports observed usage with savings unknown. Historical `est_saved_*` fields are ignored; their original history rows remain on disk. The statusline shows the active mode without the retired savings badge.

Original/current memory-file pairs are reported by their measured byte sizes. Those file-size differences do not establish provider token or billing savings. See upstream `docs/HONEST-NUMBERS.md` (https://github.com/JuliusBrussee/caveman/blob/main/docs/HONEST-NUMBERS.md).
