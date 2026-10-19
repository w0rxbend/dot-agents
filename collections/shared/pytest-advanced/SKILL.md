---
name: pytest-advanced
user-invocable: false
description: Configure and drive pytest beyond basic asserts - markers, skip/xfail, pyproject configuration, test selection, assertion helpers, warnings-as-errors, local hooks, and coverage gates. Use when tuning a pytest setup, triaging flaky or slow suites, or adding project-wide test policy.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# pytest advanced usage

For fixtures and parametrization see `pytest-fixtures`; for third-party and custom
plugins see `pytest-plugins`. Check the installed version first (`pytest --version`)
and keep configuration in the file the project already uses.

## Configuration

Configuration lives in exactly one of `pytest.ini`, `pyproject.toml`
(`[tool.pytest.ini_options]`), `tox.ini`, or `setup.cfg`; the first one found wins and
the others are ignored. `pytest --co -q` prints the detected `rootdir` and `configfile`.

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = ["-ra", "--strict-markers", "--strict-config", "--import-mode=importlib"]
xfail_strict = true
filterwarnings = [
    "error",                                          # new warnings fail the suite
    "ignore::DeprecationWarning:some_third_party.*",  # documented, narrow exceptions
]
markers = [
    "slow: takes more than a few seconds; deselect with -m 'not slow'",
    "integration: needs external services",
]
```

- `--strict-markers` turns marker typos into errors; register every custom marker.
- `--strict-config` fails on unknown ini keys.
- `xfail_strict = true` makes an unexpectedly passing xfail a failure, so fixed bugs
  are noticed.
- `--import-mode=importlib` avoids `sys.path` mutation and same-basename test file
  conflicts; it requires test helpers to live in importable packages.

## Selecting and re-running tests

```bash
pytest tests/api/test_orders.py::TestCreate::test_rejects_zero   # node id
pytest -k "orders and not slow"          # substring expression on names
pytest -m "not integration"              # marker expression
pytest --lf                              # only last failures
pytest --ff -x                           # failures first, stop at the first new failure
pytest --sw                              # stepwise: resume from the last failure
pytest --co -q                           # collect only; check what would run
pytest --durations=15                    # slowest setup/call/teardown phases
```

## skip, skipif, xfail

```python
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals only")
def test_sigterm(): ...

@pytest.mark.xfail(raises=NotImplementedError, reason="#412 streaming not done")
def test_stream(): ...

def test_optional_dep():
    yaml = pytest.importorskip("yaml", minversion="6")
```

- Always give a `reason`; reference an issue for xfails.
- Use `xfail(raises=...)` so an unrelated exception is still reported as a failure.
- Prefer `skipif` at definition time over `pytest.skip()` inside the test, which hides
  the condition from collection output.

## Assertions

```python
assert result == expected            # plain assert; pytest rewrites it to show diffs
assert total == pytest.approx(0.3)   # floats, also works on lists and dicts of floats

with pytest.raises(ValueError, match=r"quantity must be > 0"):
    create_order(qty=0)

with pytest.raises(ExceptionGroup) as excinfo:
    run_all()
assert excinfo.group_contains(TimeoutError)

with pytest.warns(DeprecationWarning, match="use new_api"):
    old_api()
```

- `match` is a regex searched in `str(exc)`; escape literal special characters with
  `re.escape`.
- Assertion helper modules outside `conftest.py` and test files are not rewritten;
  register them in the package `__init__.py` or conftest with
  `pytest.register_assert_rewrite("tests.helpers")` before they are imported.
- For readable failures on custom objects, implement `pytest_assertrepr_compare` in
  `conftest.py`.

## Local hooks in conftest.py

```python
def pytest_addoption(parser):
    parser.addoption("--run-slow", action="store_true", help="run tests marked slow")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="needs --run-slow")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
```

Other useful hooks: `pytest_configure` (register markers dynamically, set global
state), `pytest_report_header` (print environment info), `pytest_runtest_setup`
(per-test gating). Options must be added in the rootdir `conftest.py` or a plugin.

## Coverage

With `pytest-cov`, configure coverage.py rather than stacking CLI flags:

```toml
[tool.coverage.run]
branch = true
source = ["src/mypkg"]

[tool.coverage.report]
show_missing = true
skip_covered = true
fail_under = 85
exclude_also = ["if TYPE_CHECKING:", "raise NotImplementedError"]
```

Run `pytest --cov --cov-report=term-missing`. A coverage gate should ratchet from the
current measured value, not jump to an aspirational number.

## Debugging failures

```bash
pytest -x --pdb            # drop into pdb at the first failure
pytest -l --tb=long        # show locals in tracebacks
pytest -s                  # disable output capture (print debugging)
pytest -rA                 # summary line for every outcome
pytest -p no:randomly      # rule out random ordering if pytest-randomly is installed
pytest --log-cli-level=DEBUG
```

## Flaky and slow suites

1. Reproduce: run the single test in a loop (`pytest --count=50` with
   `pytest-repeat`, or a shell loop) and with the suite's random seed.
2. Classify: shared state, time/timezone, ordering, network, concurrency.
3. Fix the cause. Retries (`pytest-rerunfailures`) only hide flakiness; use them only
   with an issue link and a narrow marker.
4. For slowness, read `--durations`, then move expensive setup to wider-scope
   immutable fixtures or parallelize with `pytest-xdist`.

## Done when

- `pytest --co -q` collects the expected tests with no warnings about unknown markers.
- The suite passes with the project's configured `addopts`, not only with ad-hoc flags.
- Any new skip/xfail has a reason, and new warning filters are narrow and justified.
