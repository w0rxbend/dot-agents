---
name: git-pushing
description: "Commit explicitly named paths with a Conventional Commit message and push them through a race-safe helper (isolated index, hooks, atomic ref update). Use only when the user explicitly asks to commit and push or to save work to the remote; use git-workflow-and-versioning to plan commits and messages, and the repository's own release flow for tags and releases."
risk: critical
source: community
date_added: "2026-02-27"
---

# Git Push Workflow

Stage only the intended changes, create one Conventional Commit, and push it to the branch's remote.

## When to Use

Only on an explicit request: "push this", "commit and push", "save this to GitHub/the remote". Finishing a feature is not a request to push; ask, or stop at a local commit if the user asked for one.

Do not use it for a maintainer merge batch, canonical synchronization, versioned release, tag publication, or a repository with an explicit `merge:batch`, `release:prepare` or `release:publish` workflow. Use that repository's maintainer/release flow, which owns pull-request evidence, protected-branch checks, generated files, tags and publication verification.

## Safety Gates

1. Inspect `git status --short --branch` and list the files that belong to this change. Leave unrelated dirty files out.
2. Fetch the upstream branch when a concurrent push is plausible.
3. Read repository policy before choosing the destination branch. If `main`/`master` is protected, or the repository defines a maintainer command such as `merge:batch`, use a topic branch and finish through the required pull-request checks. "Push to main" describes the desired end state; it does not authorize bypassing server-side protection. Never keep retrying a direct push after a protected-branch rejection.
4. Write the message in the repository's convention (see `git-workflow-and-versioning`). The helper accepts only `<type>(<scope>)?!?: <subject>`.

## Workflow

Resolve the directory that contains this `SKILL.md` and substitute its absolute path for `<skill-directory>`. Do not assume the current directory is the catalog repository.

Stage named paths (the default):

```bash
bash "<skill-directory>/scripts/smart_commit.sh" "fix(parser): handle empty input" -- src/parser.ts test/parser.test.ts
```

Stage every change, only when the user said to include everything and `git status` shows nothing unrelated:

```bash
bash "<skill-directory>/scripts/smart_commit.sh" "chore: regenerate lockfile" --all
```

The message and one of `-- <paths>` or `--all` are required. The helper exits with usage text otherwise.

## What the helper guarantees

- It refuses to run if the live index already has staged changes, or if HEAD is detached.
- It builds the commit in an isolated temporary index while holding the index lock. It runs `pre-commit`, `prepare-commit-msg` and `commit-msg` hooks, and aborts if a hook modifies the staged tree.
- It re-validates the message after hooks run, and signs the commit when `commit.gpgsign` is true.
- It updates the branch ref atomically, only if its parent is unchanged, and refuses to push if the branch moved concurrently.
- It pushes to `branch.<name>.pushRemote`, then `remote.pushDefault`, then the configured upstream. A new branch requires `origin` and gets `origin/<branch>` as its upstream.
- It requires Git's `files` ref backend and rejects `reftable` repositories before creating a commit.

It does not run the project's tests or replace release tooling. Run the required checks before pushing. If the push is rejected because the upstream advanced, fetch and integrate (rebase or merge per repository policy), then rerun.

## Done When

- `git log -1` shows the new commit containing only the intended paths.
- The helper printed `Successfully pushed <branch> to <remote>/<branch>`, and `git status` still shows any unrelated dirty files untouched.
- You report the commit hash, the branch and remote, and any checks that were run or skipped.
