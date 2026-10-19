---
name: ameba-integration
user-invocable: false
description: Use when running Ameba (the Crystal linter) outside the editor prompt - its CLI flags and exit codes, pre-commit hooks, GitHub Actions, GitLab or other CI, editor plugins and gradual adoption. For .ameba.yml rule settings use ameba-configuration; for writing new rules use ameba-custom-rules.
allowed-tools:
  - Bash
  - Read
---

# Ameba Integration

Run Ameba automatically in hooks, CI and editors so Crystal code is checked before it is merged.

Every flag below was checked against the Ameba source for v1.6.4 and v1.7.0. Ameba renamed and added flags in 1.7.0, so check the installed version first and use the matching column:

```bash
ameba --version
ameba --help
```

## Installing Ameba

As a development dependency (recommended, so CI and developers use the same version):

```yaml
# shard.yml
development_dependencies:
  ameba:
    github: crystal-ameba/ameba
    version: ~> 1.7      # pin the minor version you tested
```

```bash
shards install
crystal build -o bin/ameba lib/ameba/bin/ameba.cr   # compiled binary at bin/ameba
```

Alternatively add a target and use `shards build ameba`:

```yaml
targets:
  ameba:
    main: lib/ameba/bin/ameba.cr
```

Other options: `brew tap crystal-ameba/ameba && brew install ameba`, the `ghcr.io/crystal-ameba/ameba` container image (`docker run -v $(pwd):/src ghcr.io/crystal-ameba/ameba`), or building from source with `make install`. The examples below call `bin/ameba`; use `ameba` if it is on `PATH`.

## Command-line reference

```bash
bin/ameba                              # inspect files from Globs in .ameba.yml (default **/*.cr, **/*.ecr; lib excluded)
bin/ameba src/models spec/user_spec.cr # inspect specific files or directories
bin/ameba src '!src/generated'         # a leading ! excludes a path
bin/ameba --fix                        # autocorrect issues marked [Correctable]
bin/ameba --only Lint/UselessAssign    # run only these rules or groups (comma-separated)
bin/ameba --only Lint,Naming
bin/ameba --except Style/LargeNumbers  # run everything except these rules or groups
bin/ameba --all                        # also enable rules that are disabled by default/config
bin/ameba --config path/to/ameba.yml   # use a specific config file
bin/ameba --gen-config                 # write .ameba.yml that silences all current failures (overwrites!)
bin/ameba --format json                # choose a formatter (see below)
bin/ameba --silent                     # no output; exit code still reports the result
bin/ameba --no-color
bin/ameba --without-affected-code      # do not print the source excerpt under each issue
bin/ameba src/user.cr:10:5             # explain the issue at that location (same as --explain)
bin/ameba --describe Lint/UselessAssign
bin/ameba --rules                      # list all rules
cat file.cr | bin/ameba --stdin-filename file.cr   # lint source from stdin
```

Version-specific flags:

| Purpose | Ameba 1.6.x | Ameba 1.7+ |
|---|---|---|
| Ignore issues below a severity (`error`, `warning`, `convention`) | `--fail-level SEVERITY` | `--min-severity SEVERITY` |
| Ignore the `.ameba.yml` file | - | `--ignore-config` |
| Do not error when a path argument matches no file | - | `--ignore-unmatched-paths` |
| Only run rules introduced up to a version | - | `-u/--up-to-version VERSION` |
| List rules with the version that added them | - | `-R/--rule-versions` |

Formatters (`--format`): `progress` (default), `json`, `flycheck`, `todo`, `silent`, `disabled`, and `github-actions` (1.7+ only). There is no JUnit, HTML or parallel-mode option.

Exit status: `0` when no reported issue meets the severity threshold, `1` when issues were found, and `255` (1.7) for usage or runtime errors such as an unknown flag or formatter. CI only needs to check for a non-zero exit.

### JSON output

`--format json` prints one document:

```json
{
  "sources": [
    {
      "path": "src/user.cr",
      "issues": [
        {
          "rule_name": "Lint/UselessAssign",
          "severity": "Warning",
          "message": "Useless assignment to variable `a`",
          "location": {"line": 2, "column": 3},
          "end_location": {"line": 2, "column": 9}
        }
      ]
    }
  ],
  "summary": {"target_sources_count": 1, "issues_count": 1},
  "metadata": {"ameba_version": "1.7.0", "crystal_version": "1.19.0"}
}
```

```bash
bin/ameba --format json > ameba.json || true
jq '.summary.issues_count' ameba.json
jq -r '.sources[] | .path as $p | .issues[] | "\($p):\(.location.line):\(.location.column) \(.rule_name) \(.message)"' ameba.json
```

## Pre-commit hooks

### Plain git hook

```sh
#!/bin/sh
# .git/hooks/pre-commit  (chmod +x)
# Lint staged Crystal files that still exist (added, copied, modified).
files=$(git diff --cached --name-only --diff-filter=ACM -- '*.cr')
[ -z "$files" ] && exit 0

# shellcheck disable=SC2086
bin/ameba $files || {
  echo "Ameba found issues. Fix them, or run 'bin/ameba --fix' for correctable ones."
  exit 1
}
```

Notes:

- Ameba reads files from the working tree, not the index, so partially staged files are checked in their working-tree state.
- The hook breaks on file names containing spaces; use `git diff -z` with `xargs -0` if your repository has them.
- Do not run `--fix` from the hook and silently `git add` the result; show the user what changed and let them stage it.

### pre-commit framework

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: crystal-format
        name: crystal tool format
        entry: crystal tool format
        language: system
        files: \.cr$
      - id: ameba
        name: ameba
        entry: bin/ameba
        language: system
        files: \.cr$
```

`pre-commit` passes the matching staged file names as arguments. Add `args: [--min-severity, warning]` (1.7+) or `args: [--fail-level, warning]` (1.6) to ignore convention-level issues locally.

## GitHub Actions

### Official action

[`crystal-ameba/github-action`](https://github.com/crystal-ameba/github-action) runs Ameba inside its own container image and reports issues as workflow annotations. It does not use the Ameba version from your `shard.lock`: `@v1` bundles the latest Ameba release, and older action tags map to older Ameba versions (for example `v0.12.0` to Ameba 1.6.4, see the action's README).

```yaml
# .github/workflows/ameba.yml
name: Ameba
on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: crystal-ameba/github-action@v1
        with:
          min-severity: warning   # optional; also: config, version, only, except, formatter
```

The `with:` inputs apply to `@v1`. Pin a commit SHA instead of `@v1` if your policy requires immutable action references (see github-actions-advanced).

### Using the project's own Ameba version

To lint with exactly the version pinned in `shard.lock` (or a custom binary with project rules, see ameba-custom-rules):

```yaml
name: Ameba
on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: crystal-lang/install-crystal@v1
      - uses: actions/cache@v4
        with:
          path: lib
          key: ${{ runner.os }}-shards-${{ hashFiles('shard.lock') }}
      - run: shards install
      - run: crystal build -o bin/ameba lib/ameba/bin/ameba.cr
      # Ameba 1.7+: annotations on the PR diff
      - run: bin/ameba --format github-actions
      # Ameba 1.6.x has no github-actions formatter; use the default output instead:
      # - run: bin/ameba --no-color
```

### Lint only changed files in a pull request

```yaml
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      # ... install Crystal and build bin/ameba as above ...
      - name: Ameba on changed files
        run: |
          files=$(git diff --name-only --diff-filter=ACM "origin/${{ github.base_ref }}...HEAD" -- '*.cr')
          if [ -n "$files" ]; then bin/ameba $files; fi
```

## Other CI systems

Any CI that runs a shell command works the same way: install shards, build `bin/ameba`, run it, and let the exit code fail the job. For example, GitLab CI:

```yaml
# .gitlab-ci.yml
ameba:
  image: crystallang/crystal:latest
  cache:
    key:
      files: [shard.lock]
    paths: [lib/]
  script:
    - shards install
    - crystal build -o bin/ameba lib/ameba/bin/ameba.cr
    - bin/ameba --format json > ameba.json || status=$?
    - bin/ameba --no-color --without-affected-code || true   # readable log
    - exit ${status:-0}
  artifacts:
    when: always
    paths: [ameba.json]
```

Pin the `crystallang/crystal` image tag to the Crystal version your project supports. CircleCI, Jenkins and others follow the same pattern.

## Editors

- VS Code: [vscode-crystal-ameba](https://github.com/crystal-ameba/vscode-crystal-ameba)
- Vim/Neovim: [ALE](https://github.com/dense-analysis/ale) (has an `ameba` linter for Crystal) or [vim-crystal](https://github.com/rhysd/vim-crystal)
- Emacs: [ameba.el](https://github.com/crystal-ameba/ameba.el) (uses `--format flycheck`)
- Sublime Text: [SublimeLinter-contrib-ameba](https://github.com/epergo/SublimeLinter-contrib-ameba)

Point the plugin at the same `bin/ameba` that CI uses so local results match.

## Adopting Ameba on an existing codebase

1. **Baseline**: `bin/ameba --gen-config` writes a `.ameba.yml` that disables or excludes every currently failing rule. Commit it; CI now passes and blocks new kinds of issues.
2. **Ratchet**: remove one entry from the generated file, fix (or `--fix`) the issues it reveals, commit. Repeat.
3. **Severity gate**: while the backlog is large, fail CI only on higher severities - `--min-severity warning` (1.7+) or `--fail-level warning` (1.6) - and tighten later.
4. **Version pin** (1.7+): set `Version:` in `.ameba.yml` or pass `--up-to-version` so upgrading Ameba does not introduce new failing rules until you choose to.

## Best practices

1. Pin the Ameba version (shard dependency or action tag) so local and CI results match.
2. Run `crystal tool format --check` alongside Ameba; Ameba does not replace the formatter.
3. Keep hooks fast by linting only staged or changed files; run the full project in CI.
4. Fail CI on the exit code, not by parsing text output.
5. Use annotations (`github-actions` formatter or the official action) instead of bots that post PR comments.

## Common pitfalls

1. Copying flags that do not exist: there is no `--parallel`, `--format junit` or HTML report; `--fail-level` was replaced by `--min-severity` in 1.7.
2. Assuming the official GitHub Action uses your shard's Ameba version; it uses its own.
3. Passing deleted files from `git diff` to Ameba; filter with `--diff-filter=ACM`.
4. Running `--gen-config` on a project that already has a curated `.ameba.yml`; it overwrites it.
5. Hiding failures with `|| true` and never re-checking the saved exit status.

## Resources

- [Ameba repository and README](https://github.com/crystal-ameba/ameba)
- [crystal-ameba/github-action](https://github.com/crystal-ameba/github-action)
- [pre-commit framework](https://pre-commit.com/)
