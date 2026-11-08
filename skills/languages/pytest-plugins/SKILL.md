---
name: pytest-plugins
user-invocable: false
description: Use and author pytest plugins - pytest-mock, pytest-xdist, pytest-asyncio/anyio, pytest-cov, pytest-randomly, pytest-timeout, Hypothesis - and write installable plugins tested with pytester. Use when adding a pytest plugin, debugging plugin interactions, or packaging shared test hooks and fixtures.
allowed-tools: [Read, Write, Edit, Glob, Grep, "Bash(pytest:*)", "Bash(python -m pytest:*)", "Bash(pip list:*)", "Bash(uv pip list:*)", "Bash(poetry show:*)"]
---

# pytest plugins

Check installed, active plugins before adding any:

```bash
pytest --version -VV        # shows registered third-party plugins
pip list | grep -i pytest   # or: uv pip list / poetry show
pytest --trace-config -q --co | head -50
```

Declare plugin in project test dependencies (dependency group, extras, or
requirements file), not only current environment.

## Common plugins and their sharp edges

### pytest-mock

```python
def test_sends_email(mocker):
    send = mocker.patch("app.orders.send_email", autospec=True)
    place_order()
    send.assert_called_once_with(to="a@example.com", template="confirm")
```

- Patch where name is **looked up** (`app.orders.send_email`), not where defined.
- Use `autospec=True` so wrong-signature calls fail.
- `mocker.spy(obj, "method")` records calls, keeps real behavior.
- Patches revert at test end; no `with` or `stop()` needed.

### pytest-xdist

```bash
pytest -n auto                 # one worker per CPU
pytest -n 4 --dist loadscope   # keep a module's/class's tests on one worker
```

- Tests must be independent: no shared files, ports, or DB rows without per-worker
  isolation. Namespace with `worker_id` fixture (`gw0`, `gw1`, or `master`).
- Session fixtures run once **per worker**.
- `-p no:xdist` or `-n 0` disables xdist for debugging.

### pytest-asyncio / anyio

- pytest-asyncio modes: `strict` (default: mark tests with `@pytest.mark.asyncio`, use
  `@pytest_asyncio.fixture`) and `auto` (`asyncio_mode = "auto"`). Match project's mode.
- Current releases scope event loop via `loop_scope` on markers/fixtures and
  `asyncio_default_fixture_loop_scope` ini option. Old overridden `event_loop` fixture
  pattern is deprecated/removed. Check installed version's docs before copying examples.
- If project uses `anyio` (common with Trio or FastAPI/Starlette), use
  `@pytest.mark.anyio` and `anyio_backend` fixture instead. Do not install both
  plugins to run same tests.

### pytest-cov

Configure in `[tool.coverage.*]` (see `pytest-advanced`). pytest-cov combines xdist
worker data automatically. For subprocess coverage, follow coverage.py's subprocess
instructions, not ad-hoc hooks.

### pytest-randomly

Shuffles test order; reseeds `random`, Faker, and NumPy per test. Prints seed.
Reproduce with `--randomly-seed=<n>`; disable with `-p no:randomly`.

### pytest-timeout

Set `timeout = 60` in config or `@pytest.mark.timeout(5)`. `signal` method: cleaner
but POSIX main-thread only. `thread` works everywhere but kills process.

### Hypothesis

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_is_idempotent(xs):
    assert sorted(sorted(xs)) == sorted(xs)
```

Hypothesis does not reset function-scoped fixtures between examples; it warns
(`HealthCheck.function_scoped_fixture`). Create per-example state inside test body.

### pytest-rerunfailures

Retries mask real defects. Use only on narrowly marked, ticketed flaky tests. Never
as global `--reruns` in `addopts`.

## Writing a plugin

Start in `conftest.py`. Promote to package only when several projects need it.

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

Register entry point so pytest auto-loads installed plugin:

```toml
[project.entry-points.pytest11]
myorg = "pytest_myorg.plugin"
```

- Name distribution `pytest-<name>`; add `Framework :: Pytest` classifier.
- Use `tryfirst=True` / `trylast=True` on `@pytest.hookimpl` only when ordering
  matters. Document why.
- Prefix options and fixtures with plugin name to avoid collisions.
- `pytest_plugins = ["pytest_myorg.plugin"]` in rootdir `conftest.py` loads uninstalled
  plugin. Non-root conftests ignore it.

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

Use `runpytest_subprocess` when plugin touches global state or import machinery.

## Diagnosing plugin problems

| Symptom | Check |
| --- | --- |
| Option "unrecognized arguments" | option added in non-root conftest, or plugin not installed in this env |
| Fixture not found | plugin not loaded: `pytest --trace-config`; entry point name/module path |
| Behavior differs locally vs CI | different plugin set installed; compare `pytest -VV` output |
| Two plugins fight | disable one with `-p no:<name>` to bisect |

## Done when

- Plugin declared in project test dependencies, listed in `pytest -VV`.
- Suite passes with plugin enabled and, where relevant, under `-n auto` and random
  order.
- Custom plugin has pytester tests for its options, fixtures, and hooks.
