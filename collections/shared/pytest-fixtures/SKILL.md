---
name: pytest-fixtures
user-invocable: false
description: Design pytest fixtures, conftest.py layering, scopes, teardown, and parametrization. Use when writing or refactoring test setup, sharing state between tests, or diagnosing fixture ordering, scope-mismatch, or leaking-state failures.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# pytest fixtures

Fixtures are pytest's dependency-injection system: a test names what it needs as
arguments, pytest builds it, and tears it down afterwards. Good fixture design keeps
tests independent, fast, and readable. Before adding anything, read the existing
`conftest.py` files and reuse what is there.

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

- Prefer `yield` fixtures over `request.addfinalizer`; code after `yield` is teardown.
  If setup raises before `yield`, the teardown does not run, so acquire one resource
  per fixture rather than several in a row.
- Return the thing the test needs, not a bag of unrelated objects.
- Give fixtures noun names (`client`, `tmp_repo`), and a docstring when the name is
  not self-explanatory; `--fixtures` shows it.

## Scope

| Scope | Created once per | Use for |
| --- | --- | --- |
| `function` (default) | test | anything mutable |
| `class` | test class | rare; shared expensive setup for a grouped class |
| `module` | test file | read-only expensive resources |
| `package` | package directory | as module, across a package |
| `session` | whole run | containers, compiled assets, DB engines |

Rules:
- A fixture may only depend on fixtures of the **same or wider** scope; otherwise
  pytest raises `ScopeMismatch`. Fix by widening the dependency or narrowing the
  dependent, not by caching in a global.
- Wide-scope fixtures must be effectively immutable. A common pattern is a
  session-scoped engine plus a function-scoped transaction that rolls back:

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

- Under `pytest-xdist`, "session" means per worker process. Use `tmp_path_factory`
  plus a file lock if a resource must be built exactly once across workers.

## conftest.py layering

- A `conftest.py` applies to its directory and everything below it. Put fixtures at
  the lowest directory that covers all users.
- A fixture with the same name in a deeper `conftest.py` or test module overrides the
  outer one, and can request the outer one by the same name to extend it.
- Do not import from `conftest.py` in tests; pytest discovers it automatically.
  Shared helper functions belong in a normal module (e.g. `tests/helpers.py`).
- `pytest_plugins = [...]` is only honored in the rootdir `conftest.py`.

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

Use a factory when tests need several instances or different variants of the same thing.

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

- Always give readable `id`s for non-trivial values; they appear in failure output and
  `-k` selection.
- Parametrized fixtures run every dependent test once per param:
  `@pytest.fixture(params=["sqlite", "postgres"])` and read `request.param`.
- `indirect=True` (or `indirect=["name"]`) routes a parametrize value through the
  fixture of that name, so setup logic stays in the fixture.
- Stacked `parametrize` decorators produce the cartesian product; check the count does
  not explode.

## Built-in fixtures worth knowing

| Fixture | Purpose |
| --- | --- |
| `tmp_path` / `tmp_path_factory` | per-test / per-session `pathlib.Path` temp dirs |
| `monkeypatch` | set/del attributes, env vars (`setenv`), dict items, `chdir`; auto-undone |
| `capsys` / `capfd` | captured stdout/stderr (`readouterr()`) |
| `caplog` | log records; `caplog.set_level(logging.INFO, logger="app")` |
| `request` | fixture introspection: `param`, `node`, `config`, `getfixturevalue` |
| `recwarn` | recorded warnings (prefer `pytest.warns` in the test body) |

## autouse and usefixtures

- `autouse=True` hides a dependency. Reserve it for truly global concerns (resetting a
  singleton, blocking network) and keep it in the narrowest `conftest.py` possible.
- `@pytest.mark.usefixtures("clean_cache")` is for fixtures whose value the test does
  not need; it does not work on fixtures themselves.

## Async fixtures

Async fixtures need a plugin: `pytest-asyncio` (`@pytest_asyncio.fixture` in strict
mode) or `anyio` (`@pytest.fixture` with the `anyio_backend` fixture). Follow whatever
the project already uses; see `pytest-plugins`.

## Diagnosing fixture problems

| Symptom | Likely cause |
| --- | --- |
| Test passes alone, fails in the suite | shared mutable state in a wide-scope fixture, or missing teardown |
| `ScopeMismatch` | wider-scoped fixture requests a narrower one |
| `fixture 'x' not found` | `conftest.py` not on the path of the test, or fixture defined in a non-conftest module that is not imported/registered |
| Teardown never runs | exception before `yield`, or resource acquired outside the fixture |
| Order-dependent failures | reproduce with `pytest-randomly` and its printed seed (`--randomly-seed=<seed>`), narrow with `--lf`/`-x`, then `--setup-show` |

## Done when

- `pytest --setup-show` on an affected test shows the intended scopes and order.
- The suite passes when run in random order or with `-n auto` if the project uses
  xdist, not only in file order.
- No fixture is duplicated across `conftest.py` files without an intentional override.
