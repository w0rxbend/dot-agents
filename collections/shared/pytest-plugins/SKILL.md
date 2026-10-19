---
name: pytest-plugins
user-invocable: false
description: Use and author pytest plugins - pytest-mock, pytest-xdist, pytest-asyncio/anyio, pytest-cov, pytest-randomly, pytest-timeout, Hypothesis - and write installable plugins tested with pytester. Use when adding a pytest plugin, debugging plugin interactions, or packaging shared test hooks and fixtures.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# pytest plugins

Check what is already installed and active before adding anything:

```bash
pytest --version -VV        # shows registered third-party plugins
pip list | grep -i pytest   # or: uv pip list / poetry show
pytest --trace-config -q --co | head -50
```

Add a plugin to the project's declared test dependencies (dependency group, extras, or
requirements file), not just the current environment.

## Common plugins and their sharp edges

### pytest-mock

```python
def test_sends_email(mocker):
    send = mocker.patch("app.orders.send_email", autospec=True)
    place_order()
    send.assert_called_once_with(to="a@example.com", template="confirm")
```

- Patch where the name is **looked up** (`app.orders.send_email`), not where it is
  defined.
- Use `autospec=True` so calls with the wrong signature fail.
- `mocker.spy(obj, "method")` records calls while keeping real behavior.
- Patches are undone automatically at test end; no `with` or `stop()` needed.

### pytest-xdist

```bash
pytest -n auto                 # one worker per CPU
pytest -n 4 --dist loadscope   # keep a module's/class's tests on one worker
```

- Tests must be independent: no shared files, ports, or DB rows without per-worker
  isolation. The `worker_id` fixture (`gw0`, `gw1`, or `master`) helps namespace them.
- Session fixtures run once **per worker**.
- `-p no:xdist` or `-n 0` disables it for debugging.

### pytest-asyncio / anyio

- pytest-asyncio has `strict` (default: mark tests with `@pytest.mark.asyncio`, use
  `@pytest_asyncio.fixture`) and `auto` modes (`asyncio_mode = "auto"`). Match the
  project's mode.
- Event loop scope is configured with `loop_scope` on markers/fixtures and the
  `asyncio_default_fixture_loop_scope` ini option in current releases; the old
  overridden `event_loop` fixture pattern is deprecated/removed. Check the installed
  version's docs before copying examples.
- If the project uses `anyio` (common with Trio or FastAPI/Starlette), use
  `@pytest.mark.anyio` and the `anyio_backend` fixture instead. Do not install both
  plugins to run the same tests.

### pytest-cov

Configure in `[tool.coverage.*]` (see `pytest-advanced`). With xdist, pytest-cov
combines worker data automatically. For subprocess coverage, follow coverage.py's
subprocess instructions rather than adding ad-hoc hooks.

### pytest-randomly

Shuffles test order and reseeds `random`, Faker, and NumPy per test. It prints the seed;
reproduce with `--randomly-seed=<n>` and disable with `-p no:randomly`.

### pytest-timeout

`timeout = 60` in config or `@pytest.mark.timeout(5)`. The `signal` method is cleaner
but POSIX main-thread only; `thread` works everywhere but kills the process.

### Hypothesis

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_is_idempotent(xs):
    assert sorted(sorted(xs)) == sorted(xs)
```

Function-scoped fixtures are not reset between Hypothesis examples; Hypothesis warns
about this (`HealthCheck.function_scoped_fixture`). Create per-example state inside
the test body instead.

### pytest-rerunfailures

Retries mask real defects. Use only on narrowly marked, ticketed flaky tests, never as
a global `--reruns` in `addopts`.

## Writing a plugin

Start in `conftest.py`. Promote to a package only when several projects need it.

```python
# src/pytest_myorg/plugin.py
import pytest

def pytest_addoption(parser):
    group = parser.getgroup("myorg")
    group.addoption("--myorg-env", default="local", help="target environment")

@pytest.fixture
def myorg_env(request):
    return request.config.getoption("--myorg-env")

@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    # new-style hook wrapper: code before/after the actual test call
    result = yield
    return result
```

Register it as an entry point so pytest auto-loads it when installed:

```toml
[project.entry-points.pytest11]
myorg = "pytest_myorg.plugin"
```

- Name the distribution `pytest-<name>` and add the `Framework :: Pytest` classifier.
- Use `tryfirst=True` / `trylast=True` on `@pytest.hookimpl` only when ordering
  matters; document why.
- Prefix options and fixtures with the plugin name to avoid collisions.
- `pytest_plugins = ["pytest_myorg.plugin"]` in the rootdir `conftest.py` loads an
  uninstalled plugin; it is ignored in non-root conftests.

## Testing a plugin with pytester

```python
pytest_plugins = ["pytester"]

def test_env_option(pytester):
    pytester.makepyfile(
        """
        def test_env(myorg_env):
            assert myorg_env == "staging"
        """
    )
    result = pytester.runpytest("--myorg-env=staging")
    result.assert_outcomes(passed=1)
```

Use `runpytest_subprocess` when the plugin touches global state or import machinery.

## Diagnosing plugin problems

| Symptom | Check |
| --- | --- |
| Option "unrecognized arguments" | option added in a non-root conftest, or plugin not installed in this env |
| Fixture not found | plugin not loaded: `pytest --trace-config`; entry point name/module path |
| Behavior differs locally vs CI | different plugin set installed; compare `pytest -VV` output |
| Two plugins fight | disable one with `-p no:<name>` to bisect |

## Done when

- The plugin is declared in project test dependencies and appears in `pytest -VV`.
- The suite passes with the plugin enabled and, where relevant, under `-n auto` and
  random order.
- A custom plugin has pytester tests covering its options, fixtures, and hooks.
