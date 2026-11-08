---
name: pytest-fixtures
user-invocable: false
description: Design pytest fixtures, conftest.py layering, scopes, teardown, and parametrization. Use when writing or refactoring test setup, sharing state between tests, or diagnosing fixture ordering, scope-mismatch, or leaking-state failures.
allowed-tools: [Read, Write, Edit, Glob, Grep, "Bash(pytest:*)", "Bash(python -m pytest:*)"]
---

# pytest fixtures

Before adding anything, read existing `conftest.py` files; reuse what exists.

## Inspect before changing

```bash
pytest --fixtures -q path/to/tests          # every fixture visible from here, with docstrings
pytest --fixtures-per-test path/to/test_x.py # which fixtures each test actually uses
pytest --setup-show path/to/test_x.py::test_y  # setup/teardown order and scopes
```

## Defining fixtures

```python
import pytest

@pytest.fixture
def user(db):                      # fixtures can depend on other fixtures
    u = db.create_user(name="ada")
    yield u                        # value handed to the test
    db.delete_user(u.id)           # teardown runs even if the test fails
```

- Prefer `yield` fixtures over `request.addfinalizer`. Code after `yield` is teardown.
  If setup raises before `yield`, teardown does not run, so acquire one resource per
  fixture.
- Return what test needs, not bag of unrelated objects.
- Name fixtures with nouns (`client`, `tmp_repo`). Add docstring if name is not
  self-explanatory; `--fixtures` shows it.

## Scope

| Scope | Created once per | Use for |
| --- | --- | --- |
| `function` (default) | test | anything mutable |
| `class` | test class | rare; shared expensive setup for grouped class |
| `module` | test file | read-only expensive resources |
| `package` | package directory | as module, across package |
| `session` | whole run | containers, compiled assets, DB engines |

Rules:
- Fixture may only depend on fixtures of **same or wider** scope, else pytest raises
  `ScopeMismatch`. Fix by widening dependency or narrowing dependent, not by
  caching in a global.
- Wide-scope fixtures must be effectively immutable. Common pattern: session-scoped
  engine plus function-scoped rollback transaction:

```python
@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_URL)
    yield eng
    eng.dispose()

@pytest.fixture
def session(engine):
    conn = engine.connect()
    tx = conn.begin()
    yield Session(bind=conn)
    tx.rollback()
    conn.close()
```

- Under `pytest-xdist`, "session" means per worker process. To build resource exactly
  once across workers, use `tmp_path_factory` plus file lock.

## conftest.py layering

- `conftest.py` covers its directory and all below. Put fixtures in lowest directory
  covering all users.
- Same-name fixture in deeper `conftest.py` or test module overrides outer one. Inner
  one can request outer by same name to extend it.
- Do not import from `conftest.py` in tests; pytest auto-discovers it. Shared helper
  functions go in normal module (e.g. `tests/helpers.py`).
- `pytest_plugins = [...]` only honored in rootdir `conftest.py`.

## Factories instead of many near-identical fixtures

```python
@pytest.fixture
def make_order(db):
    created = []
    def _make(**overrides):
        order = db.create_order(**{"qty": 1, "sku": "A1", **overrides})
        created.append(order)
        return order
    yield _make
    for order in created:
        db.delete_order(order.id)
```

Use factory when tests need several instances or variants of same thing.

## Parametrization

```python
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param("1", 1, id="int"),
        pytest.param(" 2 ", 2, id="whitespace"),
        pytest.param("x", None, id="invalid", marks=pytest.mark.xfail(strict=True)),
    ],
)
def test_parse(raw, expected):
    assert parse(raw) == expected
```

- Always give readable `id`s for non-trivial values. They show in failure output and
  `-k` selection.
- Parametrized fixtures run each dependent test once per param:
  `@pytest.fixture(params=["sqlite", "postgres"])`, read `request.param`.
- `indirect=True` (or `indirect=["name"]`) routes parametrize value through same-named
  fixture, keeping setup logic in fixture.
- Stacked `parametrize` decorators give cartesian product. Check count does not explode.

## Built-in fixtures worth knowing

| Fixture | Purpose |
| --- | --- |
| `tmp_path` / `tmp_path_factory` | per-test / per-session `pathlib.Path` temp dirs |
| `monkeypatch` | set/del attributes, env vars (`setenv`), dict items, `chdir`; auto-undone |
| `capsys` / `capfd` | captured stdout/stderr (`readouterr()`) |
| `caplog` | log records; `caplog.set_level(logging.INFO, logger="app")` |
| `request` | fixture introspection: `param`, `node`, `config`, `getfixturevalue` |
| `recwarn` | recorded warnings (prefer `pytest.warns` in test body) |

## autouse and usefixtures

- `autouse=True` hides a dependency. Reserve for truly global concerns (resetting a
  singleton, blocking network). Keep in narrowest `conftest.py` possible.
- `@pytest.mark.usefixtures("clean_cache")` is for fixtures whose value test does not
  need. Does not work on fixtures themselves.

## Async fixtures

Async fixtures need plugin: `pytest-asyncio` (`@pytest_asyncio.fixture` in strict
mode) or `anyio` (`@pytest.fixture` with `anyio_backend` fixture). Follow project's
existing choice; see `pytest-plugins`.

## Diagnosing fixture problems

| Symptom | Likely cause |
| --- | --- |
| Test passes alone, fails in suite | shared mutable state in wide-scope fixture, or missing teardown |
| `fixture 'x' not found` | `conftest.py` not on test's path, or fixture in non-conftest module not imported/registered |
| Teardown never runs | exception before `yield`, or resource acquired outside fixture |
| Order-dependent failures | reproduce with `pytest-randomly` and its printed seed (`--randomly-seed=<seed>`), narrow with `--lf`/`-x`, then `--setup-show` |

## Done when

- `pytest --setup-show` on affected test shows intended scopes and order.
- Suite passes in random order, or with `-n auto` if project uses xdist, not only in
  file order.
- No fixture duplicated across `conftest.py` files without intentional override.
