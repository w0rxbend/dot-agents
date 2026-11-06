---
name: hermes-agent-skill-authoring
description: "Author SKILL.md files in the hermes-agent repo."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, authoring, hermes-agent, conventions, skill-md]
    related_skills: [requesting-code-review]
---

# Authoring Hermes-Agent Skills (in-repo)

## Overview

Two homes for SKILL.md:

1. **User-local:** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — personal, not shared. Made via `skill_manage(action='create')`.
2. **In-repo (this skill's case):** `skills/<category>/<name>/SKILL.md` or `optional-skills/<category>/<name>/SKILL.md` in hermes-agent repo — committed, ships with package. Use `write_file` + `git add`.

In-repo skills must meet **hardline authoring standards** (source of truth: AGENTS.md, "Skill authoring standards (HARDLINE)"; this skill is operational walkthrough).

## When to Use

- User asks to add skill "in this branch / repo / commit"
- Committing reusable workflow that ships with hermes-agent
- Editing skill under `skills/` or `optional-skills/`
- Don't use for: personal skills in `~/.hermes/skills/` (use `skill_manage`)

## Decide the Tier First: Bundled vs Optional

- **Bundled (`skills/<category>/`)** — daily-driver, useful to many user types, low footprint. Hard bar: you can honestly say "a user will load this in 5+ sessions per month".
- **Optional (`optional-skills/<category>/`)** — niche, vertical-specific (blockchain, gaming, finance, one app), recurring-job/task skills, or anything heavy. Install: `hermes skills install official/<category>/<skill>`.

**When in doubt, optional.** "Would be useful to anyone who ever needs this" argues optional, not bundled.

Pick category by what tool IS, not how it feels (AI-agent CLI goes in `autonomous-ai-agents/` even if it "feels productivity"). Confirm existing categories with `search_files(pattern='*', target='files', path='skills')`; don't casually invent new top-level ones.

**No router / index / hub skills.** If skill is empty without "load skill X instead" pointers, don't write it; catalog and sibling triggers already route.

## Required Frontmatter

Validator source of truth: `tools/skill_manager_tool.py::_validate_frontmatter`. Hard requirements:

- Starts with `---` as first bytes (no leading blank line).
- Closes with `\n---\n` before body.
- Parses as YAML mapping.
- `name` present.
- `description` present (validator ceiling 1024 chars; repo hardline below is far stricter).
- Non-empty body after closing `---`.

Repo-standard shape (all fields expected, enforced or not):

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars (MAX_NAME_LENGTH)
description: Concise capability statement, under sixty chars.
version: 0.1.0                    # semver; new skills start at 0.1.0
author: Real Name (github-handle), Hermes Agent
license: MIT
platforms: [linux, macos, windows]   # audit, don't guess — see Platform Gating
metadata:
  hermes:
    tags: [Short, Descriptive, Tags]
    related_skills: [other-in-repo-skill]
---
```

### `description` rules (HARDLINE — the validator's 1024 is NOT the standard)

- **≤ 60 characters.** One sentence, ends with period.
- State capability, not implementation. Don't repeat skill name.
- No marketing words ("powerful", "comprehensive", "seamless", "advanced").
- System prompt skill index truncates at 57 chars + "...". Trigger/capability must fit in that window.
- If description contains `:`, wrap it in double quotes; else YAML parses a mapping and docs generator crashes. Quotes don't count toward the 60.

Good: `Track named companies for material news with cited digests.`
Bad: `Use when a user asks to monitor named competitors or companies for product launches, pricing changes, funding, ...` (240 chars — rejected in review)

### `author` rules

- Credit **human first**, "Hermes Agent" second: `Ben Barclay (benbarclay), Hermes Agent`.
- Never `author: Hermes Agent` alone on contributed skills. Credit human, not tool, especially when agent drafted text.
- Maintainer-authored skills: `Teknium (teknium1), Hermes Agent`.

### `related_skills` rules

- Each entry must resolve to existing **in-repo** skill in your PR's tree state. Do not reference planned skills, skills in another PR, or skills only in `~/.hermes/skills/`.
- Verify each: `search_files(pattern='<name>', target='files', path='skills')` (and `optional-skills/`).

## Platform Gating: audit, don't trust

`platforms:` gates loading by host OS. Set it from what prose and scripts actually invoke:

| Skill uses only… | `platforms:` |
|---|---|
| Hermes tools + stdlib Python + cross-platform CLIs | `[linux, macos, windows]` |
| bash pipelines, `grep`/`awk`/`sed` chains, heredocs | `[linux, macos]` |
| `osascript`, `defaults`, `pmset` | `[macos]` |
| `apt`/`systemctl`/`/proc` | `[linux]` |

<!-- no-tmp: ok — names the anti-pattern skill authors must avoid -->
POSIX-only signals to search in `scripts/`: `fcntl`, `termios`, `pty`, `os.fork`, `os.killpg`, `signal.SIGKILL`, `os.kill(pid, 0)` liveness checks, hardcoded `/tmp` `/proc` `/etc`. Default: fix cross-platform first (`tempfile.gettempdir()`, `pathlib.Path`, `psutil.pid_exists`). Gate narrower only for genuinely platform-bound dependency; explain why in `## Pitfalls`.

## Size Limits

- Full SKILL.md: ≤ 100,000 chars enforced (`MAX_SKILL_CONTENT_CHARS`); target **~100 lines simple, ~200 complex**. Peer skills: 8-14k chars.
- Bulky or branch-specific material goes in `references/*.md`, `templates/`, or `scripts/`. Link from SKILL.md; don't inline.
- Don't expect model to inline-write parsers or non-trivial logic every call. Ship helper script in `scripts/`; reference it by path.

## Body Structure (modern section order)

```
# <Skill> Skill
2-3 sentence intro: what it does, what it doesn't do, dependency stance.

## When to Use          — bulleted triggers (+ "Don't use for:" counter-triggers)
## Prerequisites        — exact env vars, installs, API key sourcing
## How to Run           — canonical invocation through the `terminal` tool
## Quick Reference      — flat command list, no narration
## Procedure            — numbered steps, each with a checkable completion criterion
## Pitfalls             — known limits, things that look broken but aren't
## Verification         — how to prove the skill worked
```

Not every section fits every skill (pure-procedure task skill may skip Quick Reference). Minimum: When to Use, actionable body, Pitfalls, Verification. Cut marketing intros, "Setup Check" no-ops, and re-explained env vars already in Prerequisites.

### Reference Hermes tools, not raw shell

Name needed Hermes tools in backticks: `terminal`, `read_file`, `write_file`, `patch`, `search_files`, `web_search`, `web_extract`, `browser_navigate`, `vision_analyze`, `delegate_task`, `cronjob`. Do NOT name shell utilities Hermes already wraps (`grep` → `search_files`, `cat` → `read_file`, `sed`/`awk` → `patch`, `find`/`ls` → `search_files target='files'`). CLI-wrapper skills: frame invocations as `terminal(command="<tool> ...", timeout=...)`. Bare shell prose ("run `foo --version`") blocks review. If skill depends on MCP server, name it and document setup in Prerequisites.

### Never use machine-local paths

Write repo-relative paths (`skills/...`, `tools/skill_manager_tool.py`). Committed `/home/<you>/...` path breaks for every other user. Instant review flag.

## Writing Quality Principles

1. **Optimize for process predictability.** Cut any line that does not change behavior.
2. **Choose right context load.** Description costs every turn; details go in body or linked references.
3. **End steps with completion criteria.** Checkable, exhaustive when it matters: "every modified file accounted for" beats "summarize changes."
4. **Co-locate rules with concept they govern.**
5. **Use strong leading words** ("tight loop," "root cause," "regression test") over long repeated explanations.
6. **Prune duplication and no-ops.** "Be careful" and "use best practices" don't change model behavior. Replace with checkable criterion or delete.

## Tests and Docs (required for repo skills)

1. **Tests** at `tests/skills/test_<skill>_skill.py` — stdlib + pytest + `unittest.mock` only, no live network. Run `scripts/run_tests.sh tests/skills/test_<skill>_skill.py -q`. (Generic `tests/tools/test_skill_manager_tool.py` passing proves nothing about YOUR skill.)
2. **Docs regen:** run `python website/scripts/generate-skill-docs.py`, then apply scope discipline: generator rewrites EVERY auto-gen page. Run `git status` before regen; `git checkout --` only generator-changed files that were clean before. Never discard pre-existing uncommitted edits; ask user if unsure. Final diff must show only your SKILL.md, your one per-skill docs page, one-line catalog row, one-line `website/sidebars.ts` insertion. Verify with `search_files(pattern='<your-slug>', path='website/sidebars.ts')`: exactly one hit, else page is orphan.
3. **`.env.example`** (only if skill needs new env vars): one clearly delimited commented block. Touch nothing else in file.

## Workflow

1. **Survey peers** in target category with `search_files(target='files')`. Read 2-3 peer SKILL.md files to match tone and structure. Prefer extending existing skill over narrow sibling.
2. **Decide tier and category** (above). When in doubt, optional, and ask before pushing rather than defaulting.
3. **Draft** with `write_file` to `skills/<category>/<name>/SKILL.md` (or `optional-skills/...`).
4. **Validate locally**:
   ```python
   import re, pathlib
   from ruamel.yaml import YAML
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---")
   m = re.search(r'\n---\s*\n', content[3:])
   fm = YAML(typ="safe").load(content[3:m.start()+3])
   assert "name" in fm and "description" in fm
   assert len(fm["description"]) <= 60, f"description {len(fm['description'])} chars — hardline is 60"
   assert fm["description"].endswith(".")
   assert "platforms" in fm
   assert len(content) <= 100_000
   ```
   Also verify every `related_skills` entry exists in-repo.
5. **Add tests + regen docs** (previous section).
6. Review intended diff. Commit or open PR when requested or part of authorized contribution workflow. Follow repository branch and release policy.
7. **Note:** CURRENT session's skill loader is cached. `skill_view` / `skills_list` will not see new skill until new session. Expected, not bug.

## Editing Existing In-Repo Skills

- **Small fix:** `skill_manage(action='patch', ...)` or `patch`; both work on in-repo skills.
- **Major rewrite:** `write_file` whole SKILL.md.
- **Supporting files:** `write_file` to `references/`, `templates/`, or `scripts/` under skill dir.
- Treat in-repo skills as source. Re-run docs generator when frontmatter changed. Commit within authorized repository workflow.

## Common Pitfalls

1. **Using `skill_manage(action='create')` for in-repo skill.** It writes to `~/.hermes/skills/`, not repo tree. Use `write_file`.
2. **Trusting validator limits as standard.** Validator allows 1024-char descriptions; review rejects over 60. Validator doesn't check `platforms:`, author format, tests, or docs; review does.
3. **Leading whitespace before `---`.** Any leading blank line or BOM fails validation.
4. **Skipping docs generator or pushing its unrelated drift.** Both wrong. No regen: orphan skill, no docs page. Blind regen: diff ballooned with other skills' drift.
5. **Letting skills accumulate sediment.** When adding rule, remove old wording it replaces.

## Verification Checklist

- [ ] Tier decided deliberately (bundled bar: 5+ sessions/month; else `optional-skills/`)
- [ ] File at `skills/<category>/<name>/SKILL.md` or `optional-skills/<category>/<name>/SKILL.md`
- [ ] Frontmatter starts at byte 0 with `---`, closes with `\n---\n`
- [ ] `name`, `description`, `version`, `author`, `license`, `platforms`, `metadata.hermes.{tags, related_skills}` all present
- [ ] Description ≤ 60 chars, one sentence, ends with period, no marketing words
- [ ] `author` credits human contributor first
- [ ] `platforms:` audited against real prose/scripts, not copied from sibling
- [ ] Every `related_skills` entry resolves in-repo
- [ ] Modern section order; commands framed through Hermes tools
- [ ] No machine-local paths in file
- [ ] Each ordered step has checkable completion criterion
- [ ] Tests at `tests/skills/test_<skill>_skill.py` pass under `scripts/run_tests.sh`
- [ ] Docs regenerated with scope discipline; sidebar has exactly one entry for slug
- [ ] If requested or authorized (Workflow step 6): committed on intended branch, PR opened
