---
name: python-data-classes
user-invocable: false
description: Choose and write Python data models with dataclasses, attrs or Pydantic v2 - field options, frozen/slots/kw_only, validation, serialization and conversion. Use when defining or refactoring model classes; use python-type-system for general annotations.
allowed-tools:
  - Bash
  - Read
---

# Python Data Classes

Master Python data modeling using dataclasses, attrs, and Pydantic for
creating clean, type-safe data structures with validation and serialization.

## dataclasses Module

**Basic dataclass usage:**

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str
    is_active: bool = True  # Default value

# Create instance
user = User(
    id=1,
    name="Alice",
    email="alice@example.com"
)

print(user)
# User(id=1, name='Alice', email='alice@example.com', is_active=True)

print(user.name)  # Alice
```

**dataclass with methods:**

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

    def distance_from_origin(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def move(self, dx: float, dy: float) -> "Point":
        return Point(self.x + dx, self.y + dy)

point = Point(3.0, 4.0)
print(point.distance_from_origin())  # 5.0
new_point = point.move(1.0, 1.0)
print(new_point)  # Point(x=4.0, y=5.0)
```

## dataclass Parameters

**Controlling dataclass behavior:**

```python
from dataclasses import dataclass, field

# frozen=True makes it immutable
@dataclass(frozen=True)
class ImmutableUser:
    id: int
    name: str

# order=True enables comparison operators
@dataclass(order=True)
class Person:
    age: int
    name: str

p1 = Person(30, "Alice")
p2 = Person(25, "Bob")
print(p1 > p2)  # True (compares by age first)

# slots=True uses __slots__ for memory efficiency (3.10+)
@dataclass(slots=True)
class Coordinate:
    x: float
    y: float

# kw_only=True requires keyword arguments (3.10+)
@dataclass(kw_only=True)
class Config:
    host: str
    port: int

config = Config(host="localhost", port=8080)
```

## Field Configuration

**Using field() for advanced configuration:**

```python
import itertools
from dataclasses import dataclass, field

_product_ids = itertools.count(1)

@dataclass
class Product:
    name: str
    price: float

    # Exclude from __init__
    id: int = field(init=False)

    # Exclude from __repr__
    secret: str = field(repr=False, default="")

    # Default factory for mutable defaults
    tags: list[str] = field(default_factory=list)

    # Exclude from comparison
    created_at: float = field(compare=False, default=0.0)

    def __post_init__(self) -> None:
        # Set id after initialization. Do not use hash(self.name): str hashes
        # are salted per process, so the id would change between runs.
        self.id = next(_product_ids)

product = Product(name="Widget", price=9.99)
print(product.id)  # 1, then 2, 3, ... (use uuid.uuid4() for global ids)
```

**Computed fields:**

```python
from dataclasses import dataclass, field

@dataclass
class Rectangle:
    width: float
    height: float
    area: float = field(init=False)

    def __post_init__(self) -> None:
        self.area = self.width * self.height

rect = Rectangle(10, 20)
print(rect.area)  # 200.0
```

## Inheritance

**Dataclass inheritance:**

```python
from dataclasses import dataclass

@dataclass
class Animal:
    name: str
    age: int

@dataclass
class Dog(Animal):
    breed: str
    is_good_boy: bool = True

dog = Dog(name="Rex", age=5, breed="Labrador")
print(dog)
# Dog(name='Rex', age=5, breed='Labrador', is_good_boy=True)
```

## Conversion Methods

**Converting to/from dictionaries:**

```python
from dataclasses import dataclass, asdict, astuple

@dataclass
class User:
    id: int
    name: str
    email: str

user = User(1, "Alice", "alice@example.com")

# Convert to dict
user_dict = asdict(user)
print(user_dict)
# {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}

# Convert to tuple
user_tuple = astuple(user)
print(user_tuple)
# (1, 'Alice', 'alice@example.com')

# Create from dict
data = {"id": 2, "name": "Bob", "email": "bob@example.com"}
bob = User(**data)
```

## attrs Library

**Using attrs for enhanced features:**

```bash
pip install attrs
```

**Basic attrs usage:**

```python
import attrs

@attrs.define
class User:
    id: int
    name: str
    email: str
    is_active: bool = True

user = User(1, "Alice", "alice@example.com")
print(user)
```

**attrs validators:**

```python
import attrs
from attrs import validators

@attrs.define
class User:
    id: int = attrs.field(validator=validators.instance_of(int))
    name: str = attrs.field(
        validator=[
            validators.instance_of(str),
            validators.min_len(1)
        ]
    )
    email: str = attrs.field(
        validator=validators.matches_re(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    )
    age: int = attrs.field(
        validator=validators.and_(
            validators.instance_of(int),
            validators.ge(0),
            validators.le(150)
        )
    )

# Validates on initialization
user = User(
    id=1,
    name="Alice",
    email="alice@example.com",
    age=30
)
```

**attrs converters:**

```python
import attrs

@attrs.define
class User:
    name: str = attrs.field(converter=str.strip)
    age: int = attrs.field(converter=int)
    tags: list[str] = attrs.field(
        factory=list,
        converter=lambda x: [tag.lower() for tag in x]
    )

user = User(
    name="  Alice  ",
    age="30",
    tags=["ADMIN", "User"]
)

print(user.name)  # "Alice"
print(user.age)   # 30 (int)
print(user.tags)  # ["admin", "user"]
```

## Pydantic Models

**Install Pydantic:**

```bash
pip install pydantic               # core
pip install 'pydantic[email]'      # adds email-validator, needed for EmailStr
pip install pydantic-settings      # needed for BaseSettings (separate package in v2)
```

**Basic Pydantic model:**

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True

# Automatic validation and conversion
user = User(
    id="1",           # Converted to int
    name="Alice",
    email="alice@example.com"
)

print(user.id)  # 1 (int)
print(user.model_dump())  # Dict representation
print(user.model_dump_json())  # JSON string
```

**Pydantic validators:**

```python
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Annotated

class User(BaseModel):
    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    age: Annotated[int, Field(ge=0, le=150)]
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip().title()

user = User(
    id=1,
    name="  alice  ",
    email="alice@example.com",
    age=30,
    username="ALICE123"
)

print(user.name)      # "Alice"
print(user.username)  # "alice123"
```

**Pydantic model configuration:**

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        frozen=False,
        extra="forbid"
    )

    id: int
    name: str
    email: str

# Strips whitespace automatically
user = User(id=1, name="  Alice  ", email="alice@example.com")
print(user.name)  # "Alice"

# Validates on assignment
user.name = "  Bob  "
print(user.name)  # "Bob"
```

## Pydantic Advanced Features

**Computed fields:**

```python
from pydantic import BaseModel, computed_field

class User(BaseModel):
    first_name: str
    last_name: str

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

user = User(first_name="Alice", last_name="Smith")
print(user.full_name)  # "Alice Smith"
print(user.model_dump())
# {'first_name': 'Alice', 'last_name': 'Smith', 'full_name': 'Alice Smith'}
```

**Model validators:**

```python
from pydantic import BaseModel, model_validator

class DateRange(BaseModel):
    start_date: str
    end_date: str

    @model_validator(mode="after")
    def validate_date_range(self) -> "DateRange":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before end_date")
        return self

range_obj = DateRange(
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

**Nested models:**

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    country: str

class User(BaseModel):
    name: str
    email: str
    address: Address

user = User(
    name="Alice",
    email="alice@example.com",
    address={
        "street": "123 Main St",
        "city": "New York",
        "country": "USA"
    }
)

print(user.address.city)  # "New York"
```

**Generic models:**

```python
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    data: T
    message: str
    success: bool

class User(BaseModel):
    id: int
    name: str

# Create typed response
response = Response[User](
    data=User(id=1, name="Alice"),
    message="User retrieved",
    success=True
)

print(response.data.name)  # "Alice"
```

## Serialization and Deserialization

**Pydantic JSON handling:**

```python
from pydantic import BaseModel
from datetime import datetime

class Event(BaseModel):
    name: str
    timestamp: datetime
    metadata: dict[str, str]

# From JSON
json_data = '''
{
    "name": "User Login",
    "timestamp": "2024-01-15T10:30:00",
    "metadata": {"ip": "192.168.1.1"}
}
'''

event = Event.model_validate_json(json_data)
print(event.timestamp)

# To JSON
json_output = event.model_dump_json(indent=2)
print(json_output)
```

**Custom serialization:**

```python
from pydantic import BaseModel, field_serializer
from datetime import datetime

class Event(BaseModel):
    name: str
    timestamp: datetime

    @field_serializer("timestamp")
    def serialize_timestamp(self, value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S")

event = Event(name="Test", timestamp=datetime.now())
print(event.model_dump())
# {'name': 'Test', 'timestamp': '2024-01-15 10:30:00'}
```

## Comparison: dataclasses vs attrs vs Pydantic

**When to use dataclasses:**

- Simple data containers with type hints
- Part of standard library (no dependencies)
- Basic validation not required
- No third-party dependency allowed
- Immutability with frozen=True

**When to use attrs:**

- More features than dataclasses (validators, converters)
- Slots by default (`@define`), plus converters and on-setattr hooks
- Advanced field configuration needed
- Custom initialization logic

**When to use Pydantic:**

- Automatic data validation required
- JSON/dict serialization/deserialization
- API request/response models
- Configuration management
- Type coercion needed
- OpenAPI/JSON schema generation

## Best Practices

- Mutable defaults always go through `default_factory` (dataclasses/attrs) or
  `Field(default_factory=...)` (Pydantic).
- Validate at trust boundaries (API input, files, env) with Pydantic; use plain
  dataclasses or attrs for internal, already-trusted data.
- Prefer `frozen=True` (and `slots=True` on 3.10+) for value objects.

## Common Patterns

**Builder pattern with dataclass:**

```python
from dataclasses import dataclass, field
from typing import Self  # 3.11+; typing_extensions on older versions

@dataclass
class QueryBuilder:
    _select: list[str] = field(default_factory=list)
    _where: list[str] = field(default_factory=list)
    _limit: int | None = None

    def select(self, *columns: str) -> Self:
        self._select.extend(columns)
        return self

    def where(self, condition: str) -> Self:
        self._where.append(condition)
        return self

    def limit(self, n: int) -> Self:
        self._limit = n
        return self

    def build(self) -> str:
        query = f"SELECT {', '.join(self._select)}"
        if self._where:
            query += f" WHERE {' AND '.join(self._where)}"
        if self._limit:
            query += f" LIMIT {self._limit}"
        return query

query = (
    QueryBuilder()
    .select("id", "name")
    .where("active = true")
    .limit(10)
    .build()
)
```

**Configuration with Pydantic:**

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "My App"
    # Field names map to env vars case-insensitively (DATABASE_URL here);
    # use validation_alias only when the env var name differs.
    database_url: str = Field(validation_alias="APP_DB_URL")
    debug: bool = False
    max_connections: int = Field(10, ge=1, le=100)

settings = Settings()
```

## Common Pitfalls

- `x: list = []` on a dataclass raises `ValueError: mutable default`; on a plain
  class it silently shares one list across instances.
- Pydantic v1 idioms (`class Config:`, `Field(env=...)`, `.dict()`,
  `@validator`) still appear in examples online; in v2 use `model_config`,
  `validation_alias`, `.model_dump()` and `@field_validator`.
- `EmailStr` needs `pydantic[email]`; `BaseSettings` needs `pydantic-settings`.

## Done when

- Every model imports and instantiates in a quick REPL or test with valid data,
  and invalid data raises the expected `ValidationError`/`TypeError`.
- `python -W error::DeprecationWarning` runs the model module without Pydantic
  deprecation warnings (no v1-style config left).
- Round-trip holds where serialization matters:
  `Model.model_validate(m.model_dump()) == m` (or `asdict`/constructor for dataclasses).
- A type checker (mypy/pyright) passes on the model module.

## Resources

- [dataclasses Documentation](https://docs.python.org/3/library/dataclasses.html)
- [attrs Documentation](https://www.attrs.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [PEP 557 - Data Classes](https://peps.python.org/pep-0557/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
