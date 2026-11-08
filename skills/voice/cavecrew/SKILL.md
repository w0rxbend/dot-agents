---
name: cavecrew
description: >
  When to delegate to `cavecrew-investigator` (locate code), `cavecrew-builder`
  (1-2 file edit) or `cavecrew-reviewer` (diff review) instead of working inline
  or using `Explore`. Use only when those three Claude Code subagents are
  installed; they come from upstream Caveman and dot-agents does not install
  them.
---

## Prerequisite: the cavecrew subagents

Skill only routes work. Agents are separate files in upstream Caveman (`agents/cavecrew-*.md` in https://github.com/JuliusBrussee/caveman).
dot-agents does not install them. Check before delegating:

- `cavecrew-investigator`, `cavecrew-builder` and `cavecrew-reviewer` show as
  agent types in Agent/Task tool, or
- `ls ~/.claude/agents/cavecrew-*.md .claude/agents/cavecrew-*.md` lists them.

If absent, do not spawn them. Tell user once: "cavecrew subagents
are not installed; using the built-in agents instead. To use cavecrew, install
the three agent files from the Caveman repo into ~/.claude/agents/." Then use
vanilla column of table below (`Explore`, main thread, or general-purpose agent).

Cavecrew = three subagent presets answering in ultracave voice (tool runs: one status line in, one out; nothing between routine calls). Same jobs as Anthropic defaults (`Explore`, edit-style agents, reviewer), but tool result comes back compressed. Main context shrinks per delegation.

## When to use cavecrew vs alternatives

| Task | Use |
|---|---|
| "Where is X defined / what calls Y / list uses of Z" | `cavecrew-investigator` |
| Same, plus suggestions/architecture commentary | `Explore` (vanilla) |
| Surgical edit, ≤2 files, scope obvious | `cavecrew-builder` |
| New feature / 3+ files / cross-cutting refactor | Main thread, or `feature-dev:code-architect` if installed |
| Review diff, branch or file for bugs | `cavecrew-reviewer` |
| Deep review with rationale and alternatives | `Code Reviewer` (vanilla) if installed, else main thread |
| One-line answer already known | Main thread, no subagent |

Rule of thumb: **want subagent output in 1/3 the tokens? Pick cavecrew. Want prose? Pick vanilla.**

## Output contracts

Main thread can rely on:

**`cavecrew-investigator`**
```
<Header>:
- path:line — `symbol` — short note
totals: <counts>.
```
Or `No match.` Always file-path-first, line number attached, symbols backticked. Safe to grep with `path:\d+`.

**`cavecrew-builder`**
```
<path:line-range> — <change ≤10 words>.
verified: <re-read OK | mismatch @ path:line>.
```
Or one of: `too-big.` / `needs-confirm.` / `ambiguous.` / `regressed.` (terminal first token).

**`cavecrew-reviewer`**
```
path:line: <emoji> <severity>: <problem>. <fix>.
totals: N🔴 N🟡 N🔵 N❓
```
Or `No issues.` Findings sorted by file, then line ascending.

## Chaining patterns

**Locate → fix → verify** (most common):
1. `cavecrew-investigator` returns site list.
2. Main thread picks 1-2 sites, hands paths to `cavecrew-builder`.
3. `cavecrew-reviewer` audits diff.

**Parallel scout** (broad investigation):
Spawn 2-3 `cavecrew-investigator` calls in one message, each from different angle (defs vs callers vs tests). Aggregate in main thread.

**Single-shot edit** (site already known):
Skip investigator. Hand exact path:line straight to `cavecrew-builder`.

## What NOT to do

- Don't use `cavecrew-builder` without knowing the file. Spawn investigator first, or main thread burns tokens passing context.
- Don't chain `cavecrew-investigator → cavecrew-builder` for 5-file refactor. Builder returns `too-big.`: wasted turn.
- Don't ask `cavecrew-reviewer` for "general feedback". Findings only, no architecture opinions. Use `Code Reviewer` for that when installed.
- Don't expect prose. Cavecrew output is structured, sometimes cryptically terse. If a human reads it directly, paraphrase.

## Auto-clarity (inherited)

Subagents switch to normal English for security warnings, irreversible-action confirmations, and output where fragments could be misread. Resume caveman after.
