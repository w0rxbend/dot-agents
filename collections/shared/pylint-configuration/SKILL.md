---
name: pylint-configuration
user-invocable: false
description: Configure Pylint - pyproject/pylintrc settings, enabling and disabling messages, inline suppressions, import resolution, extensions, thresholds, and coexistence with Ruff/mypy. Use when setting up or tuning Pylint for a project, fixing false positives such as import-error, or deciding which messages to enforce.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Pylint configuration

For CI, pre-commit, and editor wiring see `pylint-integration`; for writing custom
checks see `pylint-checkers`.

## First, find the existing setup

```bash
pylint --version                         # pylint, astroid, and Python versions
grep -n "tool.pylint" pyproject.toml; ls .pylintrc pylintrc setup.cfg tox.ini 2>/dev/null
pylint --generate-toml-config > /tmp/pylint-defaults.toml   # every option with defaults
```

Pylint reads the first config it finds: `pylintrc`/`.pylintrc` in the working
directory, then `pyproject.toml` (`[tool.pylint.*]`), then `setup.cfg`, then parent
directories and the user's home. Keep exactly one project config, and run pylint from
the project root so the same file is used locally and in CI.

Also check for Ruff, Flake8, and mypy configuration. Overlapping linters double-report
the same problem; decide which tool owns which rule family before enabling more.

## Minimal pyproject configuration

```toml
[tool.pylint.main]
py-version = "3.11"           # match the project's minimum supported Python
jobs = 0                      # use all CPUs
source-roots = ["src"]        # src layout: lets pylint resolve first-party imports
ignore-paths = ["^src/mypkg/_generated/.*$"]
load-plugins = [
    "pylint.extensions.docparams",
    "pylint.extensions.mccabe",
]
fail-under = 9.5              # optional score floor; prefer --fail-on for hard rules

[tool.pylint."messages control"]
disable = [
    "missing-module-docstring",   # each entry: why it is off for this project
    "too-few-public-methods",
]

[tool.pylint.format]
max-line-length = 100         # match the formatter (Black/Ruff format)

[tool.pylint.design]
max-args = 6
max-locals = 20

[tool.pylint.basic]
good-names = ["i", "j", "k", "df", "id", "_"]
```

## Message names, categories, and control

- Refer to messages by **symbolic name** (`unused-import`), not code (`W0611`); names
  are stable and readable. `pylint --list-msgs-enabled` and
  `pylint --help-msg=<name>` explain them.
- Categories: `C` convention, `R` refactor, `W` warning, `E` error, `F` fatal,
  `I` informational.
- Config order matters: `disable = ["all"]` then `enable = [...]` gives an allowlist,
  useful when introducing Pylint to a large legacy codebase.

Inline suppressions, narrowest first:

```python
value = eval(expr)  # pylint: disable=eval-used  -- trusted admin input, see #231

# pylint: disable-next=too-many-branches
def dispatch(event): ...
```

- A `# pylint: disable=` on its own line applies from there to the end of the current
  block/scope (or module, at top level), which often silences far more than intended.
  Prefer end-of-line or `disable-next`.
- Always pair a suppression with a reason.
- Enable `useless-suppression` (an `I` message, so pass `--enable=useless-suppression`)
  occasionally to find stale disables.

## Fixing common false positives

| Message | Usual cause | Fix |
| --- | --- | --- |
| `import-error` (E0401) | pylint runs in a different interpreter/venv, or src layout not on path | run pylint from the project venv (`python -m pylint`); set `source-roots`; avoid `init-hook` sys.path hacks unless nothing else works |
| `no-member` on C extensions / generated attrs | astroid cannot infer dynamic attributes | `extension-pkg-allow-list = ["lxml", "pydantic_core"]` or `generated-members`; a plugin such as `pylint-django`/`pylint-pydantic` for framework magic |
| `no-name-in-module` | stub-only or compiled module | same as above; check the module actually exports the name |
| `cyclic-import` | real cycle, or package `__init__` re-exports | fix the cycle; this is often a true design signal |
| `duplicate-code` | similar test fixtures, generated code | raise `min-similarity-lines` or ignore tests/generated paths in `[tool.pylint.similarities]` |

Do not respond to false positives by globally disabling an `E`-category message;
scope the fix to the module or configure the inference hint.

## Choosing what to enforce

1. Errors (`E`, `F`): always on.
2. Warnings (`W`): on; disable individually with a written reason.
3. Refactor and convention (`R`, `C`): adopt deliberately, aligned with the formatter
   and the team's style. Disable rules a formatter or Ruff already owns
   (e.g. `line-too-long` when the formatter enforces length).
4. Design thresholds (`max-args`, `max-branches`, ...): set from the codebase's current
   distribution, then ratchet down.

Useful optional extensions (`load-plugins`): `pylint.extensions.docparams`
(docstring/signature agreement), `mccabe` (complexity), `code_style`, `typing`
(modern typing syntax for `py-version`), `broad_try_clause`, `no_self_use`,
`redefined_variable_type`. Enable one at a time and review the findings.

## Scores and exit codes

The score is informational; gates should use exit status. Pylint's exit code is a bit
mask: 1 fatal, 2 error, 4 warning, 8 refactor, 16 convention, 32 usage error.
`--fail-on=E,W,unused-import` fails on specific categories or messages regardless of
score; `--fail-under` gates on score; `--exit-zero` never fails (reporting only).

## Done when

- `python -m pylint <package>` from the project root uses the intended config (check
  the "Using config file" line with `--verbose`).
- No new global disables of `E`-category messages; each disabled message has a reason.
- Pylint and any co-installed linter do not report the same rule twice.
