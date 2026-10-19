---
name: pylint-integration
user-invocable: false
description: Run Pylint in CI, pre-commit, and editors - environment-correct invocation, GitHub annotations, incremental adoption on legacy code, changed-files linting, and performance tuning. Use when wiring Pylint into a pipeline or hook, or when Pylint results differ between local runs, editors, and CI.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Pylint integration

Configuration options are covered in `pylint-configuration`. The core rule for every
integration: **Pylint must run in the same environment as the code's dependencies**,
because it imports-and-infers third-party packages. Most "works locally, fails in CI"
reports are environment mismatches.

## Invocation

```bash
python -m pylint src/mypkg tests       # use the project interpreter, not a global pylint
uv run pylint src/mypkg                 # or: poetry run / hatch run / tox -e lint
```

Lint packages or directories, not a glob of files, so relative imports resolve.

## pre-commit

The mirrored `pylint` hook runs in an isolated virtualenv without your dependencies,
causing `import-error` noise. Use a local hook that runs in the project environment:

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

If an isolated hook is required, list the runtime dependencies in
`additional_dependencies` and keep that list in sync with the project.

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

The `--msg-template` produces workflow-command annotations that show on the PR diff.
Do not combine it with `colorized` output: ANSI codes end up inside the annotations.
Pin actions to the versions or SHAs the repository already uses. For machine-readable
artifacts use `--output-format=json2` (or `json`) and write to a file with
`--output=pylint.json`; several formats can be combined, e.g.
`--output-format=json2:pylint.json,text`.

## Adopting Pylint on an existing codebase

1. Measure: `python -m pylint src --exit-zero --score=y`, and count by message:
   `python -m pylint src --exit-zero --output-format=json2 | jq -r '.messages[].symbol' | sort | uniq -c | sort -rn`.
2. Gate on errors first: `--disable=all --enable=E,F` or `--fail-on=E,F`.
3. Disable the noisiest non-error messages in config with a "TODO: re-enable" note and
   an issue, rather than adding thousands of inline suppressions.
4. Ratchet: re-enable one message per change set, fix its findings, repeat.
5. Optionally gate only changed files on stricter settings:

```bash
git diff --name-only --diff-filter=ACMR origin/main...HEAD -- '*.py' \
  | xargs -r python -m pylint
```

Changed-file linting can miss cross-module messages (`cyclic-import`,
`duplicate-code`); still run a full lint on the default branch.

## Editors

- VS Code: the `ms-python.pylint` extension uses the selected interpreter; select the
  project venv and avoid setting `pylint.path` to a global binary. It reads the project
  config automatically.
- PyCharm: use the Pylint plugin or an External Tool running `python -m pylint` with
  the project interpreter.
- Whatever the editor, confirm it uses the same config file as CI.

## Performance

- `jobs = 0` (all CPUs) in config, or `-j 0`.
- Exclude generated, vendored, and migration directories with `ignore-paths`.
- Lower `limit-inference-results` if astroid inference is slow on large dynamic code.
- `duplicate-code` is relatively expensive on huge trees; scope it or run it
  separately.
- Cache the virtualenv, not Pylint output; Pylint has no incremental result cache.

## Troubleshooting mismatched results

| Symptom | Check |
| --- | --- |
| Different messages locally vs CI | `python -m pylint --version` in both (pylint and astroid versions); pin pylint in dev dependencies |
| `import-error` only in CI/pre-commit | dependencies missing from that environment; isolated pre-commit hook |
| Config ignored | run from project root; `--verbose` shows which config file is used |
| Exit code non-zero but no messages shown | usage error (bit 32) or a fatal parse error; read stderr |

## Done when

- Local, editor, pre-commit, and CI runs use the same pylint/astroid versions and config.
- CI fails on the agreed categories and annotates findings on the PR.
- The adoption plan, if any, is recorded in config comments or an issue.
