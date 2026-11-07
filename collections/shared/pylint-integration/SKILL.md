---
name: pylint-integration
user-invocable: false
description: Run Pylint in CI, pre-commit, and editors - environment-correct invocation, GitHub annotations, incremental adoption on legacy code, changed-files linting, and performance tuning. Use when wiring Pylint into a pipeline or hook, or when Pylint results differ between local runs, editors, and CI.
allowed-tools: [Read, Write, Edit, Glob, Grep, "Bash(pylint:*)", "Bash(python -m pylint:*)", "Bash(uv run pylint:*)", "Bash(git diff:*)"]
---

# Pylint integration

Config options: see `pylint-configuration`. Core rule for every integration: **Pylint must
run in the same environment as the code's dependencies**, because it imports-and-infers
third-party packages. Most "works locally, fails in CI" reports are environment mismatches.

## Invocation

```bash
python -m pylint src/mypkg tests       # use the project interpreter, not a global pylint
uv run pylint src/mypkg                 # or: poetry run / hatch run / tox -e lint
```

Lint packages or directories, not file globs, so relative imports resolve.

## pre-commit

Mirrored `pylint` hook runs in isolated virtualenv without your dependencies: `import-error`
noise. Use local hook in project environment:

```yaml
repos:
  - repo: local
    hooks:
      - id: pylint
        name: pylint
        entry: python -m pylint
        language: system
        types: [python]
        require_serial: true   # pylint parallelizes itself and needs whole-package context
        args: ["--score=n"]
```

Isolated hook required? List runtime dependencies in `additional_dependencies`; keep that
list in sync with project.

## GitHub Actions

```yaml
- uses: actions/setup-python@v5
  with:
    python-version-file: .python-version   # or the project's declared version
    cache: pip
- run: pip install -e ".[dev]"             # or the project's lock-based install
- name: Pylint
  run: >
    python -m pylint src/mypkg
    --msg-template='::warning file={path},line={line},col={column},title={symbol}::{msg_id} {msg}'
```

`--msg-template` emits workflow-command annotations on PR diff. Do not combine with
`colorized` output: ANSI codes leak into annotations. Pin actions to versions or SHAs the
repository already uses. Machine-readable artifacts: `--output-format=json2` (or `json`)
plus `--output=pylint.json`. Formats combine, e.g. `--output-format=json2:pylint.json,text`.

## Adopting Pylint on an existing codebase

1. Measure: `python -m pylint src --exit-zero --score=y`, then count by message:
   `python -m pylint src --exit-zero --output-format=json2 | jq -r '.messages[].symbol' | sort | uniq -c | sort -rn`.
2. Gate on errors first: `--disable=all --enable=E,F` or `--fail-on=E,F`.
3. Disable noisiest non-error messages in config with "TODO: re-enable" note and issue,
   not thousands of inline suppressions.
4. Ratchet: re-enable one message per change set, fix its findings, repeat.
5. Optionally gate only changed files on stricter settings:

```bash
git diff --name-only --diff-filter=ACMR origin/main...HEAD -- '*.py' \
  | xargs -r python -m pylint
```

Changed-file linting can miss cross-module messages (`cyclic-import`, `duplicate-code`).
Still run full lint on default branch.

## Editors

- VS Code: `ms-python.pylint` extension uses selected interpreter. Select project venv;
  avoid pointing `pylint.path` at global binary. Reads project config automatically.
- PyCharm: Pylint plugin, or External Tool running `python -m pylint` with project
  interpreter.
- Any editor: confirm it uses same config file as CI.

## Performance

- `jobs = 0` (all CPUs) in config, or `-j 0`.
- Exclude generated, vendored, and migration directories with `ignore-paths`.
- Lower `limit-inference-results` if astroid inference slow on large dynamic code.
- `duplicate-code` relatively expensive on huge trees; scope it or run separately.
- Cache virtualenv, not Pylint output. Pylint has no incremental result cache.

## Troubleshooting mismatched results

| Symptom | Check |
| --- | --- |
| Different messages locally vs CI | `python -m pylint --version` in both (pylint and astroid versions); pin pylint in dev dependencies |
| `import-error` only in CI/pre-commit | dependencies missing from that environment; isolated pre-commit hook |
| Config ignored | run from project root; `--verbose` shows config file used |
| Exit code non-zero but no messages shown | usage error (bit 32) or fatal parse error; read stderr |

## Done when

- Local, editor, pre-commit, and CI runs use same pylint/astroid versions and config.
- CI fails on agreed categories and annotates findings on PR.
- Adoption plan, if any, recorded in config comments or an issue.
