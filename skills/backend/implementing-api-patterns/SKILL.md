---
name: implementing-api-patterns
description: "Implement API servers in code: choose and scaffold FastAPI, Hono, Axum, Gin, tRPC, gRPC (Tonic, Connect-Go) or GraphQL libraries (Strawberry, async-graphql, gqlgen, Pothos), with pagination, rate limiting, caching, OpenAPI generation and frontend integration. Use when writing or changing server-side API code; use designing-apis for the contract and backend-dev-guidelines for Express/Prisma house conventions."
---

# API Patterns Skill

## When to Use This Skill

Use when:
- Building backend APIs for web, mobile or service consumers
- Connecting frontend components (forms, tables, dashboards) to databases
- Adding pagination, rate limiting or caching
- Generating OpenAPI docs automatically
- Choosing between REST, GraphQL, gRPC or tRPC
- Integrating authentication and authorization
- Tuning API performance and scalability

## Quick Decision Framework

```
WHO CONSUMES YOUR API?
├─ PUBLIC/THIRD-PARTY DEVELOPERS → REST with OpenAPI
│  ├─ Python → FastAPI (auto-docs)
│  ├─ TypeScript → Hono (edge-first, small bundle)
│  ├─ Rust → Axum (highest throughput)
│  └─ Go → Gin (mature ecosystem)
│
├─ FRONTEND TEAM (same org)
│  ├─ TypeScript full-stack? → tRPC (E2E type safety)
│  └─ Complex data needs? → GraphQL
│      ├─ Python → Strawberry
│      ├─ Rust → async-graphql
│      ├─ Go → gqlgen
│      └─ TypeScript → Pothos
│
├─ SERVICE-TO-SERVICE (microservices)
│  └─ High performance → gRPC
│      ├─ Rust → Tonic
│      ├─ Go → Connect-Go (browser-friendly)
│      └─ Python → grpcio
│
└─ MOBILE APPS
   ├─ Bandwidth constrained → GraphQL (request only needed fields)
   └─ Simple CRUD → REST (standard, well-understood)
```

## REST Framework Selection

### Python: FastAPI (Recommended)

**Key Features:** Auto OpenAPI docs, Pydantic v2 validation, async/await

**Basic Example:**
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.post("/items")
async def create_item(item: Item):
    return {"id": 1, **item.model_dump()}
```

FastAPI patterns: `references/rest-design-principles.md` and `examples/python-fastapi/`.

### TypeScript: Hono (Edge-First)

**Key Features:** 14KB bundle, runs on any runtime (Node/Deno/Bun/edge), Zod validation

**Basic Example:**
```typescript
import { Hono } from 'hono'
import { zValidator } from '@hono/zod-validator'
import { z } from 'zod'

const app = new Hono()
app.post('/items', zValidator('json', z.object({
  name: z.string(), price: z.number()
})), (c) => c.json({ id: 1, ...c.req.valid('json') }))
```

Hono patterns: `references/rest-design-principles.md` and `examples/typescript-hono/`.

### TypeScript: tRPC (Full-Stack Type Safety)

**Key Features:** Zero codegen, E2E type safety, React Query integration, WebSocket subscriptions

**Basic Example:**
```typescript
import { initTRPC } from '@trpc/server'
import { z } from 'zod'

const t = initTRPC.create()
export const appRouter = t.router({
  createItem: t.procedure
    .input(z.object({ name: z.string(), price: z.number() }))
    .mutation(({ input }) => ({ id: '1', ...input }))
})
export type AppRouter = typeof appRouter
```

Setup patterns: `references/trpc-setup-guide.md` and `examples/typescript-trpc/`.

### Rust: Axum (High Performance)

**Key Features:** Tower middleware, type-safe extractors, compile-time verification

**Basic Example:**
```rust
use axum::{routing::post, Json, Router};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct CreateItem { name: String, price: f64 }

#[derive(Serialize)]
struct Item { id: u64, name: String, price: f64 }

async fn create_item(Json(payload): Json<CreateItem>) -> Json<Item> {
    Json(Item { id: 1, name: payload.name, price: payload.price })
}
```

Axum patterns: `references/rest-design-principles.md` and `examples/rust-axum/`.

### Go: Gin (Mature Ecosystem)

**Key Features:** Largest Go ecosystem, struct tag validation

**Basic Example:**
```go
type Item struct {
    Name  string  `json:"name" binding:"required"`
    Price float64 `json:"price" binding:"required,gt=0"`
}

r := gin.Default()
r.POST("/items", func(c *gin.Context) {
    var item Item
    if err := c.ShouldBindJSON(&item); err != nil {
        c.JSON(400, gin.H{"error": err.Error()}); return
    }
    c.JSON(201, item)
})
```

Gin patterns: `references/rest-design-principles.md` and `examples/go-gin/`.

## Performance Benchmarks

| Language | Framework | Relative throughput | Best For |
|----------|-----------|---------------------|----------|
| Rust | Actix-web / Axum | Highest | Max throughput, low memory |
| Go | Gin | High | Mature ecosystem |
| TypeScript | Hono | Medium-high (runtime-dependent) | Edge deployment |
| Python | FastAPI | Medium | Developer experience |
| TypeScript | Express | Lower | Legacy systems |

**Notes:**
- Rough ordering, not measured numbers. Published benchmarks (e.g. TechEmpower) vary widely by workload, runtime and configuration
- Benchmark your own workload before choosing a framework for performance reasons
- Database and network I/O usually dominate real request latency

## Pagination Strategies

### Cursor-Based (Recommended)

**Advantages:** Handles real-time changes, no skipped/duplicate records, scales to billions

**FastAPI Example:**
```python
@app.get("/items")
async def list_items(cursor: Optional[int] = None, limit: int = 20):
    query = db.query(Item)
    if cursor is not None:
        query = query.filter(Item.id > cursor)
    items = query.order_by(Item.id).limit(limit).all()  # order by the cursor key
    return {
        "items": items,
        "next_cursor": items[-1].id if items else None,
        "has_more": len(items) == limit
    }
```

### Offset-Based (Simple Cases Only)

Use only for static datasets (<10k records) that need direct page access.

Full patterns and frontend integration: `references/pagination-patterns.md`.

## OpenAPI Documentation

| Framework | OpenAPI Support | Docs UI | Configuration |
|-----------|----------------|---------|---------------|
| FastAPI | Automatic | Swagger UI + ReDoc | Built-in |
| Hono | Middleware plugin | Swagger UI | `@hono/swagger-ui` |
| Axum | utoipa crate | Swagger UI | Manual annotations |
| Gin | swaggo/swag | Swagger UI | Comment annotations |

**FastAPI Example (Zero Config):**
```python
app = FastAPI(title="My API", version="1.0.0")

@app.post("/items", tags=["items"])
async def create_item(item: Item) -> Item:
    """Create item with name and price"""
    return item
# Docs at /docs, /redoc, /openapi.json
```

Framework-specific setup: `references/openapi-documentation.md`.
Extract specs programmatically with `scripts/generate_openapi.py`.

## Frontend Integration Patterns

### Forms → REST POST/PUT

**Backend:**
```python
class UserCreate(BaseModel):
    email: EmailStr; name: str; age: int

@app.post("/api/users", status_code=201)
async def create_user(user: UserCreate):
    return {"id": 1, **user.model_dump()}
```

**Frontend:**
```typescript
const res = await fetch('/api/users', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})
if (!res.ok) throw new Error((await res.json()).detail)
```

### Tables → GET with Pagination

See cursor pagination example above and `references/pagination-patterns.md`.

### AI Chat → SSE Streaming

**Backend:**
```python
from sse_starlette.sse import EventSourceResponse

# EventSource can only send GET requests without a body, so take the message as a query param.
# For POST bodies (long prompts, auth headers), stream with fetch() + ReadableStream instead.
@app.get("/api/chat")
async def chat(message: str):
    async def gen():
        for chunk in llm_stream(message):
            yield {"event": "message", "data": chunk}
    return EventSourceResponse(gen())
```

**Frontend:**
```typescript
const es = new EventSource(`/api/chat?message=${encodeURIComponent(message)}`)
es.addEventListener('message', (e) => appendToChat(e.data))
```

Full integration examples per frontend skill: `examples/`.

## Rate Limiting

**FastAPI Example (Token Bucket):**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/items")
@limiter.limit("100/minute")
async def list_items():
    return {"items": []}
```

Sliding window, distributed patterns and Redis implementation: `references/rate-limiting-strategies.md`.

## GraphQL Libraries

**By Language:**
- **Python**: Strawberry (type-hint-based, async)
- **Rust**: async-graphql (high performance, tokio)
- **Go**: gqlgen (code generation from schema)
- **TypeScript**: Pothos (type-safe builder, no codegen)

Schema patterns and N+1 prevention: `references/graphql-schema-design.md`.
Full Python example: `examples/graphql-strawberry/`.

## gRPC for Microservices

Use for service-to-service calls needing strong typing and high performance.

**By Language:**
- **Rust**: Tonic (async, type-safe, code generation)
- **Go**: Connect-Go (gRPC-compatible + browser-friendly)
- **Python**: grpcio (official implementation)
- **TypeScript**: @connectrpc/connect (browser + Node.js)

Protocol Buffers guide: `references/grpc-protobuf-guide.md`.
Full Rust example: `examples/grpc-tonic/`.

## Additional Resources

### References
- `references/rest-design-principles.md` - REST resource modeling, HTTP methods, status codes
- `references/graphql-schema-design.md` - Schema patterns, resolver optimization, N+1 prevention
- `references/grpc-protobuf-guide.md` - Proto3 syntax, service definitions, streaming
- `references/trpc-setup-guide.md` - Router patterns, middleware, Zod validation
- `references/pagination-patterns.md` - Cursor vs offset with math explanation
- `references/rate-limiting-strategies.md` - Token bucket, sliding window, Redis
- `references/caching-patterns.md` - HTTP caching, application caching
- `references/versioning-strategies.md` - URI, header, media type versioning
- `references/openapi-documentation.md` - Swagger/OpenAPI best practices by framework

### Scripts (Token-Free Execution)
- `scripts/generate_openapi.py` - Generate OpenAPI spec from code
- `scripts/validate_api_spec.py` - Validate OpenAPI 3.1 compliance
- `scripts/benchmark_endpoints.py` - Load test API endpoints

## Quick Reference

**Choose REST when:** Public API, standard CRUD, caching needed, OpenAPI docs required
**Choose GraphQL when:** Frontend needs flexible queries, mobile bandwidth limits, complex nested data
**Choose gRPC when:** Service-to-service calls, high performance, bidirectional streaming
**Choose tRPC when:** TypeScript full-stack, same team owns frontend + backend, E2E type safety

**Pagination:** Always cursor-based at production scale, offset-based only for simple cases
**Documentation:** Prefer frameworks with automatic OpenAPI generation (FastAPI, Hono)
