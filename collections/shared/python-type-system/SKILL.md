---
name: python-type-system
user-invocable: false
description: Annotate Python code and fix type-checker errors with mypy or pyright - builtin generics, X | None, PEP 695 generics and `type` aliases, Protocol, TypedDict, Literal, overload, ParamSpec, Self, @override, TypeIs/TypeGuard. Use when adding or reviewing annotations or configuring type checking; use python-data-classes for model classes.
allowed-tools:
  - Bash
  - Read
---

# Python Type System

Write annotations that a checker can verify and that read well. First find the
project's minimum Python (`requires-python` in `pyproject.toml`) and the checker
it already uses; syntax below is tagged with the version that introduced it.
Features newer than the minimum come from `typing_extensions` (works at runtime
on older versions) or need the legacy spelling.

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

`from __future__ import annotations` lets annotations use newer syntax on older
interpreters (they are not evaluated), but not in runtime-evaluated places such
as base classes, `cast()` arguments, or Pydantic/dataclass field introspection.

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

Pick one checker as the CI gate. Adopt gradually: enable `strict` per package
via overrides rather than adding blanket `# type: ignore`.

## Everyday Annotations

```python
from collections.abc import Callable, Iterable, Mapping, Sequence

def count_words(lines: Iterable[str]) -> dict[str, int]: ...
def find_user(user_id: int) -> User | None: ...
def parse(value: int | str) -> str: ...
def apply(fn: Callable[[int], str], items: Sequence[int]) -> list[str]: ...
def render(config: Mapping[str, object]) -> str: ...
```

- Accept abstract types (`Iterable`, `Sequence`, `Mapping`) for parameters;
  return concrete types (`list`, `dict`).
- Import ABCs from `collections.abc`; the `typing` aliases are deprecated.
- Prefer `object` over `Any` for "anything" inputs: `Any` disables checking,
  `object` forces narrowing.
- Annotate locals only when inference cannot (empty containers, `None` initial values).

## Generics

PEP 695 syntax (3.12+) declares type parameters inline; variance is inferred.

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

Before 3.12, the equivalent is:

```python
from typing import Generic, TypeVar
from typing_extensions import TypeAlias

T = TypeVar("T")
S = TypeVar("S", bound=Sized)

class Stack(Generic[T]): ...
UserId: TypeAlias = int
```

Do not mix styles within one class. `type X = ...` aliases are lazily evaluated,
so they can be recursive without string quotes.

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

Use a Protocol at boundaries where callers own the concrete type (adapters,
test doubles). `@runtime_checkable` makes `isinstance` work, but it checks only
that the attributes exist, not their signatures.

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

Use TypedDict for JSON-shaped dicts you do not control. Use a dataclass or
Pydantic model for your own data (see `python-data-classes`). Use `Literal` for
small fixed string sets in signatures, and `enum.Enum` when values need behavior
or iteration.

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

Prefer `TypeIs` over `TypeGuard`: `TypeIs` narrows in both the `if` and `else`
branches and requires the narrowed type to be a subtype of the input.
`TypeGuard` narrows only the positive branch; use it when the target is not a
subtype (for example `list[object]` -> `list[str]` under invariance).

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
`typing.Concatenate[Ctx, P]` when the decorator injects or removes a leading
argument.

## Escape Hatches

```python
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:                     # import only for annotations; breaks cycles
    from .models import User

user = cast("User", payload)          # unchecked assertion; keep rare
reveal_type(user)                     # checker prints the inferred type

x = legacy_call()  # type: ignore[no-untyped-call]   # always scope ignores to an error code
```

Enable `warn_unused_ignores` (part of mypy `strict`) so stale ignores get removed.

## Common Pitfalls

- Mutable invariance: `list[int]` is not a `list[float]`; accept `Sequence[float]`.
- Returning `Any` from untyped libraries silently spreads; install `types-*`
  stubs or wrap the call with a typed function.
- Using `Optional[X]` as "optional argument": it means "may be None"; a default
  value is what makes an argument optional.
- `isinstance` with parameterized generics (`isinstance(x, list[int])`) raises
  at runtime.
- Annotating `self`-returning methods with the class name instead of `Self`.

## Done When

- The configured checker passes in CI at the project's minimum Python version.
- New `# type: ignore` comments carry an error code and a reason.
- Public functions and methods are fully annotated; `Any` appears only at
  documented boundaries.

## Resources

- [typing module](https://docs.python.org/3/library/typing.html)
- [Typing specification and guides](https://typing.python.org/)
- [mypy configuration](https://mypy.readthedocs.io/en/stable/config_file.html)
- [pyright configuration](https://microsoft.github.io/pyright/#/configuration)
