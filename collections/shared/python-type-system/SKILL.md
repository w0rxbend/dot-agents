---
name: python-type-system
user-invocable: false
description: Annotate Python code and fix type-checker errors with mypy or pyright - builtin generics, X | None, PEP 695 generics and `type` aliases, Protocol, TypedDict, Literal, overload, ParamSpec, Self, @override, TypeIs/TypeGuard. Use when adding or reviewing annotations or configuring type checking; use python-data-classes for model classes.
allowed-tools:
  - "Bash(uv run mypy:*)"
  - "Bash(uv run pyright:*)"
  - "Bash(mypy:*)"
  - "Bash(pyright:*)"
  - "Bash(python -m mypy:*)"
  - Read
---

# Python Type System

First find project's minimum Python (`requires-python` in `pyproject.toml`) and
its current checker. Features newer than minimum come from `typing_extensions`
(works at runtime on older versions) or need legacy spelling.

## Version Map

| Feature | Native from | Older spelling |
|---------|-------------|----------------|
| `list[int]`, `dict[str, int]` | 3.9 | `typing.List`, `typing.Dict` |
| `X \| Y`, `X \| None` | 3.10 | `Union[X, Y]`, `Optional[X]` |
| `ParamSpec`, `TypeAlias`, `TypeGuard` | 3.10 | `typing_extensions` |
| `Self`, `Required`/`NotRequired`, `assert_never`, `reveal_type` | 3.11 | `typing_extensions` |
| `class Box[T]:`, `def f[T](...)`, `type Alias = ...` (PEP 695) | 3.12 | `TypeVar` + `Generic[T]`, `TypeAlias` |
| `@override` | 3.12 | `typing_extensions.override` |
| `TypeIs`, `ReadOnly` (TypedDict), TypeVar defaults | 3.13 | `typing_extensions` |

`from __future__ import annotations` allows newer annotation syntax on older
interpreters (annotations stay unevaluated). Not in runtime-evaluated places:
base classes, `cast()` arguments, Pydantic/dataclass field introspection.

## Checkers and Configuration

```bash
uv add --dev mypy        # or: uv add --dev pyright / pip install mypy
uv run mypy src/
uv run mypy --strict src/
uv run pyright           # reads [tool.pyright] from pyproject.toml
```

```toml
# pyproject.toml - set python_version / pythonVersion to the project's MINIMUM
# supported Python (omit it to use the running interpreter).
[tool.mypy]
strict = true                     # enables the disallow_untyped_*/warn_* family
warn_unreachable = true
# python_version = "3.X"

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = ["some_untyped_lib.*"]   # prefer installing types-* stubs first
ignore_missing_imports = true

[tool.pyright]
typeCheckingMode = "strict"       # or "standard" while adopting
# pythonVersion = "3.X"
```

Pick one checker as CI gate. Adopt gradually: per-package `strict` via
overrides, not blanket `# type: ignore`.

## Everyday Annotations

```python
from collections.abc import Callable, Iterable, Mapping, Sequence

def count_words(lines: Iterable[str]) -> dict[str, int]: ...
def find_user(user_id: int) -> User | None: ...
def parse(value: int | str) -> str: ...
def apply(fn: Callable[[int], str], items: Sequence[int]) -> list[str]: ...
def render(config: Mapping[str, object]) -> str: ...
```

- Accept abstract types (`Iterable`, `Sequence`, `Mapping`) for parameters.
  Return concrete types (`list`, `dict`).
- Import ABCs from `collections.abc`; `typing` aliases are deprecated.
- Prefer `object` over `Any` for "anything" inputs. `Any` disables checking;
  `object` forces narrowing.
- Annotate locals only where inference cannot: empty containers, `None` initial values.

## Generics

PEP 695 syntax (3.12+) declares type parameters inline. Variance is inferred.

```python
from collections.abc import Sequence, Sized

def first[T](items: Sequence[T]) -> T | None:
    return items[0] if items else None

def longest[S: Sized](a: S, b: S) -> S:          # upper bound
    return a if len(a) >= len(b) else b

def concat[S: (str, bytes)](a: S, b: S) -> S:     # constrained: str or bytes
    return a + b

class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

type Pair[T] = tuple[T, T]
type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
```

Before 3.12:

```python
from typing import Generic, TypeVar
from typing_extensions import TypeAlias

T = TypeVar("T")
S = TypeVar("S", bound=Sized)

class Stack(Generic[T]): ...
UserId: TypeAlias = int
```

Do not mix styles in one class. `type X = ...` aliases evaluate lazily, so
recursion needs no string quotes.

## Protocols (Structural Typing)

```python
from typing import Protocol, runtime_checkable

class SupportsClose(Protocol):
    def close(self) -> None: ...

def shutdown(resources: list[SupportsClose]) -> None:
    for r in resources:
        r.close()          # any object with close() matches, no inheritance needed

@runtime_checkable
class HasName(Protocol):
    name: str
```

Use Protocol at boundaries where callers own concrete type (adapters, test
doubles). `@runtime_checkable` enables `isinstance`, but checks only attribute
existence, not signatures.

## TypedDict, Literal, Final, Enums

```python
from typing import Final, Literal, NotRequired, TypedDict

class Movie(TypedDict):
    title: str
    year: int
    rating: NotRequired[float]   # key may be absent (3.11+)

Mode = Literal["r", "w", "a"]
def open_file(path: str, mode: Mode) -> None: ...

MAX_RETRIES: Final = 3
```

TypedDict: JSON-shaped dicts you do not control. Dataclass or Pydantic model:
own data (see `python-data-classes`). `Literal`: small fixed string sets in
signatures. `enum.Enum`: values needing behavior or iteration.

## Narrowing

```python
from typing import Literal, TypeGuard, TypeIs, assert_never   # TypeIs: 3.13+ or typing_extensions

def is_user(val: object) -> TypeIs[User]:            # narrowed type is a subtype of input
    return isinstance(val, User) and val.active

def is_str_list(val: list[object]) -> TypeGuard[list[str]]:   # list[str] is NOT a subtype
    return all(isinstance(x, str) for x in val)                 # of list[object]: TypeGuard

def handle(value: User | str | list[object]) -> str:
    if is_user(value):
        return value.name
    if isinstance(value, str):                         # else-branch of TypeIs already
        return value                                   # excluded User
    if is_str_list(value):
        return ",".join(value)
    return repr(value)

def describe(mode: Literal["r", "w"]) -> str:
    match mode:
        case "r": return "read"
        case "w": return "write"
        case _: assert_never(mode)       # checker errors if a case is missing
```

Prefer `TypeIs` over `TypeGuard`. `TypeIs` narrows both `if` and `else`
branches; narrowed type must be subtype of input. `TypeGuard` narrows only positive
branch. Use `TypeGuard` when target is not a subtype (for example
`list[object]` -> `list[str]` under invariance).

## Methods: Self, @override, overload

```python
from typing import Self, overload, override

class Builder:
    def with_name(self, name: str) -> Self:      # subclasses keep their own type
        self.name = name
        return self

class Base:
    def run(self) -> None: ...

class Child(Base):
    @override                                    # error if Base.run is renamed/removed
    def run(self) -> None: ...

@overload
def load(path: str, *, raw: Literal[True]) -> bytes: ...
@overload
def load(path: str, *, raw: Literal[False] = ...) -> str: ...
def load(path: str, *, raw: bool = False) -> bytes | str:
    data = open(path, "rb").read()
    return data if raw else data.decode()
```

## Decorators: ParamSpec

```python
from collections.abc import Callable
from functools import wraps

def logged[**P, R](fn: Callable[P, R]) -> Callable[P, R]:    # 3.12 syntax
    @wraps(fn)
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"calling {fn.__name__}")
        return fn(*args, **kwargs)
    return inner
```

Before 3.12: `P = ParamSpec("P")`, `R = TypeVar("R")`. Use
`typing.Concatenate[Ctx, P]` when decorator injects or removes leading argument.

## Escape Hatches

```python
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:                     # import only for annotations; breaks cycles
    from .models import User

user = cast("User", payload)          # unchecked assertion; keep rare
reveal_type(user)                     # checker prints the inferred type

x = legacy_call()  # type: ignore[no-untyped-call]   # always scope ignores to an error code
```

Enable `warn_unused_ignores` (part of mypy `strict`) to flag stale ignores.

## Common Pitfalls

- Mutable invariance: `list[int]` is not a `list[float]`. Accept `Sequence[float]`.
- `Any` from untyped libraries spreads silently. Install `types-*` stubs or
  wrap call in typed function.
- `Optional[X]` means "may be None", not "optional argument". Default value
  makes argument optional.
- `isinstance` with parameterized generics (`isinstance(x, list[int])`) raises
  at runtime.
- `self`-returning methods annotated with class name instead of `Self`.

## Done When

- Configured checker passes in CI at project's minimum Python version.
- New `# type: ignore` comments carry error code and reason.
- Public functions and methods fully annotated. `Any` appears only at
  documented boundaries.

## Resources

- [typing module](https://docs.python.org/3/library/typing.html)
- [Typing specification and guides](https://typing.python.org/)
- [mypy configuration](https://mypy.readthedocs.io/en/stable/config_file.html)
- [pyright configuration](https://microsoft.github.io/pyright/#/configuration)
