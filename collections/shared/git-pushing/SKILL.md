---
name: git-pushing
description: "Commit explicitly named paths with a Conventional Commit message and push them through a race-safe helper (isolated index, hooks, atomic ref update). Use only when the user explicitly asks to commit and push or to save work to the remote; use git-workflow-and-versioning to plan commits and messages, and the repository's own release flow for tags and releases."
risk: critical
source: community
date_added: "2026-02-27"
---

# Git Push Workflow

## When to Use

Only on explicit request: "push this", "commit and push", "save this to GitHub/the remote". Finished feature is not a push request. Ask, or stop at local commit if user asked for one.

Not for maintainer merge batches, canonical synchronization, versioned releases, tag publication, or repositories with explicit `merge:batch`, `release:prepare` or `release:publish` workflow. Use that repository's maintainer/release flow. It owns PR evidence, protected-branch checks, generated files, tags, publication verification.

## Safety Gates

1. Run `git status --short --branch`; list files in this change. Leave unrelated dirty files out.
2. Fetch upstream branch if concurrent push is plausible.
3. Read repository policy before picking destination branch. If `main`/`master` is protected, or repository defines maintainer command like `merge:batch`, use topic branch and finish through required PR checks. "Push to main" names desired end state, not permission to bypass server-side protection. Never keep retrying direct push after protected-branch rejection.
4. Follow repository's message convention (see `git-workflow-and-versioning`). Helper accepts only `<type>(<scope>)?!?: <subject>`.

## Workflow

Substitute absolute path of directory holding this `SKILL.md` for `<skill-directory>`. Do not assume current directory is catalog repository.

Stage named paths (default):

```bash
bash "<skill-directory>/scripts/smart_commit.sh" "fix(parser): handle empty input" -- src/parser.ts test/parser.test.ts
```

Stage everything only when user said include everything and `git status` shows nothing unrelated:

```bash
bash "<skill-directory>/scripts/smart_commit.sh" "chore: regenerate lockfile" --all
```

Message and one of `-- <paths>` or `--all` required. Otherwise helper exits with usage text.

## What the helper guarantees

- Refuses to run if live index has staged changes or HEAD is detached.
- Builds commit in isolated temporary index under index lock. Runs `pre-commit`, `prepare-commit-msg`, `commit-msg` hooks; aborts if hook modifies staged tree.
- Re-validates message after hooks. Signs commit when `commit.gpgsign` is true.
- Updates branch ref atomically, only if parent unchanged. Refuses push if branch moved concurrently.
- Push target order: `branch.<name>.pushRemote`, `remote.pushDefault`, configured upstream. New branch requires `origin`, gets `origin/<branch>` as upstream.
- Requires Git's `files` ref backend; rejects `reftable` repositories before committing.

Does not run project tests or replace release tooling. Run required checks before pushing. If push rejected because upstream advanced, commit already exists locally: do not rerun helper (it stops with "No changes staged for commit"). Fetch, integrate (rebase or merge per repository policy), re-run required checks. Then push with plain Git to helper's chosen destination, for example `git push <remote> HEAD:<branch>`. Never force-push without asking.

## Done When

- `git log -1` shows new commit with only intended paths.
- Helper printed `Successfully pushed <branch> to <remote>/<branch>`; `git status` still shows unrelated dirty files untouched.
- Report commit hash, branch, remote, and checks run or skipped.
