---
name: python-patterns
description: "Make Python architecture decisions - FastAPI vs Django vs Flask, sync vs async, project layout, tooling (uv, ruff, mypy/pyright), background jobs, error handling and test strategy. Use when starting or restructuring a Python service, not for line-level async or typing questions (see python-async-patterns, python-type-system)."
source: community
date_added: "2026-02-27"
---

# Python Patterns

Decision guide for structuring Python applications. It complements the focused
skills: `python-async-patterns` (asyncio code), `python-type-system` (annotations
and checkers), `python-data-classes` (models), `pytest-fixtures` /
`pytest-advanced` (tests).

## How to Use This Skill

- Inspect the repository first: `pyproject.toml`, lock files, CI config and the
  framework already in use. An existing choice wins unless migration is requested.
- Ask for the framework preference when it is unclear and nothing exists yet.
- Choose async vs sync from the workload, not by habit.

---

## 1. Framework Selection

### Decision Tree

```
What are you building?
│
├── API-first / Microservices
│   └── FastAPI (async, modern, fast)
│
├── Full-stack web / CMS / Admin
│   └── Django (batteries-included)
│
├── Simple / Script / Learning
│   └── Flask (minimal, flexible)
│
├── AI/ML API serving
│   └── FastAPI (Pydantic, async, uvicorn)
│
└── Background workers
    └── Celery + any framework
```

### Comparison Principles

| Factor | FastAPI | Django | Flask |
|--------|---------|--------|-------|
| **Best for** | APIs, microservices | Full-stack, CMS | Simple, learning |
| **Async** | Native (ASGI) | Async views (3.1+), async ORM API (4.1+, still runs sync DB drivers in threads) | Native `async def` views (2.0+), but still WSGI: one request per worker; use Quart for full ASGI |
| **Admin** | Manual | Built-in | Via extensions |
| **ORM** | Choose your own | Django ORM | Choose your own |
| **Learning curve** | Low | Medium | Low |

### Selection Questions to Ask:
1. Is this API-only or full-stack?
2. Need admin interface?
3. Team familiar with async?
4. Existing infrastructure?

---

## 2. Async vs Sync Decision

### When to Use Async

```
async def is better when:
├── I/O-bound operations (database, HTTP, file)
├── Many concurrent connections
├── Real-time features
├── Microservices communication
└── FastAPI/Starlette/Django ASGI

def (sync) is better when:
├── CPU-bound operations
├── Simple scripts
├── Legacy codebase
├── Team unfamiliar with async
└── Blocking libraries (no async version)
```

### The Golden Rule

```
I/O-bound → async (waiting for external)
CPU-bound → sync + multiprocessing (computing)

Don't:
├── Mix sync and async carelessly
├── Use sync libraries in async code
└── Force async for CPU work
```

### Async Library Selection

| Need | Async Library |
|------|---------------|
| HTTP client | httpx |
| PostgreSQL | asyncpg |
| Redis | `redis.asyncio` (redis-py 4.2+; `aioredis` is deprecated and merged into it) |
| File I/O | aiofiles |
| Database ORM | SQLAlchemy 2.0 async, Tortoise |

---

## 3. Type Hints Strategy

### When to Type

```
Always type:
├── Function parameters
├── Return types
├── Class attributes
├── Public APIs

Can skip:
├── Local variables (let inference work)
├── One-off scripts
├── Tests (usually)
```

### Common Type Patterns

```python
# These are patterns, understand them:

# Might be None (3.10+ syntax; use Optional[User] only on older targets)
def find_user(id: int) -> User | None: ...

# Union → one of multiple types
def process(data: str | dict) -> None: ...

# Generic collections
def get_items() -> list[Item]: ...
def get_mapping() -> dict[str, int]: ...

# Callable
from collections.abc import Callable
def apply(fn: Callable[[int], str]) -> str: ...
```

### Pydantic for Validation

```
When to use Pydantic:
├── API request/response models
├── Configuration/settings
├── Data validation
├── Serialization

Benefits:
├── Runtime validation
├── Auto-generated JSON schema
├── Works with FastAPI natively
└── Clear error messages
```

---

## 4. Project Structure Principles

### Structure Selection

```
Small project / Script:
├── main.py
├── utils.py
└── pyproject.toml   (or PEP 723 inline script metadata for single files)

Medium API:
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── schemas/
├── tests/
└── pyproject.toml

Large application:
├── src/
│   └── myapp/
│       ├── core/
│       ├── api/
│       ├── services/
│       ├── models/
│       └── ...
├── tests/
└── pyproject.toml
```

### FastAPI Structure Principles

```
Organize by feature or layer:

By layer:
├── routes/ (API endpoints)
├── services/ (business logic)
├── models/ (database models)
├── schemas/ (Pydantic models)
└── dependencies/ (shared deps)

By feature:
├── users/
│   ├── routes.py
│   ├── service.py
│   └── schemas.py
└── products/
    └── ...
```

### Tooling Stance

Keep whatever the repository already uses. For a new project:

| Concern | Default | Notes |
|---------|---------|-------|
| Environments, deps, lock | `uv` (`uv init`, `uv add`, `uv lock`, `uv run`) | Commit `uv.lock`; Poetry/PDM/pip-tools are fine if already present |
| Lint + format | `ruff check` + `ruff format` | Replaces flake8/isort/black in most setups; configure in `pyproject.toml` |
| Type checking | `mypy --strict` or `pyright` | Pick one as the CI gate; see `python-type-system` |
| Tests | `pytest` (+ `pytest-asyncio` or `anyio` plugin for async) | See `pytest-fixtures`, `pytest-advanced` |
| Python version | Declare `requires-python` and test the minimum in CI | Use syntax available at that minimum |

Run lint, type check and tests in CI with the same commands developers run locally.

---

## 5. Django Principles

### Django Async

```
Django supports async:
├── Async views (3.1+)
├── Async middleware
├── Async ORM API (aget, acreate, asave, `async for` over querysets; 4.1+) - DB I/O still
│   runs in a thread pool, transactions need sync_to_async
└── ASGI deployment (uvicorn/daphne/granian)

When to use async in Django:
├── External API calls
├── WebSocket (Channels)
├── High-concurrency views
└── Background task triggering
```

### Django Best Practices

```
Model design:
├── Fat models, thin views
├── Use managers for common queries
├── Abstract base classes for shared fields

Views:
├── Class-based for complex CRUD
├── Function-based for simple endpoints
├── Use viewsets with DRF

Queries:
├── select_related() for FKs
├── prefetch_related() for M2M
├── Avoid N+1 queries
└── Use .only() for specific fields
```

---

## 6. FastAPI Principles

### async def vs def in FastAPI

```
Use async def when:
├── Using async database drivers
├── Making async HTTP calls
├── I/O-bound operations
└── Want to handle concurrency

Use def when:
├── Blocking operations
├── Sync database drivers
├── CPU-bound work
└── FastAPI runs in threadpool automatically
```

### Dependency Injection

```
Use dependencies for:
├── Database sessions
├── Current user / Auth
├── Configuration
├── Shared resources

Benefits:
├── Testability (mock dependencies)
├── Clean separation
├── Automatic cleanup (yield)
```

### Pydantic v2 Integration

```python
# FastAPI + Pydantic are tightly integrated:

# Request validation
@app.post("/users")
async def create(user: UserCreate) -> UserResponse:
    # user is already validated
    ...

# Response serialization
# Return type becomes response schema
```

---

## 7. Background Tasks

### Selection Guide

| Solution | Best For |
|----------|----------|
| **BackgroundTasks** | Simple, in-process tasks |
| **Celery** | Distributed, complex workflows |
| **ARQ** | Async, Redis-based |
| **RQ** | Simple Redis queue |
| **Dramatiq** | Actor-based, simpler than Celery |

### When to Use Each

```
FastAPI BackgroundTasks:
├── Quick operations
├── No persistence needed
├── Fire-and-forget
└── Same process

Celery/ARQ:
├── Long-running tasks
├── Need retry logic
├── Distributed workers
├── Persistent queue
└── Complex workflows
```

---

## 8. Error Handling Principles

### Exception Strategy

```
In FastAPI:
├── Create custom exception classes
├── Register exception handlers
├── Return consistent error format
└── Log without exposing internals

Pattern:
├── Raise domain exceptions in services
├── Catch and transform in handlers
└── Client gets clean error response
```

### Error Response Philosophy

```
Include:
├── Error code (programmatic)
├── Message (human readable)
├── Details (field-level when applicable)
└── NOT stack traces (security)
```

---

## 9. Testing Principles

### Testing Strategy

| Type | Purpose | Tools |
|------|---------|-------|
| **Unit** | Business logic | pytest |
| **Integration** | API endpoints | pytest + httpx/TestClient |
| **E2E** | Full workflows | pytest + DB |

### Async Testing

```python
# pytest-asyncio (or anyio's pytest plugin); httpx >= 0.28 requires an explicit transport
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users")
        assert response.status_code == 200
```

For sync tests, FastAPI's `TestClient` is simpler. `ASGITransport` does not run
lifespan events; use `asgi-lifespan`'s `LifespanManager` or `TestClient` as a
context manager when startup/shutdown hooks matter.

### Fixtures Strategy

```
Common fixtures:
├── db_session → Database connection
├── client → Test client
├── authenticated_user → User with token
└── sample_data → Test data setup
```

---

## 10. Decision Checklist

Before implementing:

- [ ] **Asked user about framework preference?**
- [ ] **Chosen framework for THIS context?** (not just default)
- [ ] **Decided async vs sync?**
- [ ] **Planned type hint strategy?**
- [ ] **Defined project structure and tooling (deps, lint, types, tests in CI)?**
- [ ] **Planned error handling?**
- [ ] **Considered background tasks?**

---

## 11. Anti-Patterns to Avoid

### Don't
- Default to Django for simple APIs (FastAPI may be better)
- Use sync libraries in async code
- Skip type hints for public APIs
- Put business logic in routes/views
- Ignore N+1 queries
- Call blocking libraries (requests, sync DB drivers, time.sleep) inside `async def`
- Mix async and sync carelessly

### Do
- Choose framework based on context
- Ask about async requirements
- Use Pydantic for validation
- Separate concerns (routes → services → repos)
- Test critical paths

---

## Done When

- The framework, async model and tooling choice are stated with the reason tied
  to this project's workload and existing setup.
- `ruff check`, the type checker and `pytest` pass locally and are wired into CI.
