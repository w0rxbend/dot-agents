---
name: using-relational-databases
description: Relational database implementation across Python, Rust, Go, and TypeScript. Use when building CRUD applications, transactional systems, or structured data storage. Covers PostgreSQL (primary), MySQL, SQLite, ORMs (SQLAlchemy, Prisma, SeaORM, GORM), query builders (Drizzle, sqlc, SQLx), migrations, connection pooling, and serverless databases (Neon, PlanetScale, Turso).
---

# Relational Databases

## When to Use This Skill

**Trigger this skill when:**
- Building user authentication, content management or e-commerce applications
- Implementing CRUD operations (Create, Read, Update, Delete)
- Designing data models with relationships (users → posts, orders → items)
- Migrating schemas safely in production
- Setting up connection pooling for performance
- Evaluating serverless databases (Neon, PlanetScale, Turso)
- Integrating with frontend skills (forms, tables, dashboards, search-filter)

**Skip this skill for:**
- Time-series data at scale (use time-series databases)
- Real-time analytics (use columnar databases)
- Document-heavy workloads (use document databases)
- Key-value caching (use Redis, Memcached)

## Quick Reference: Database Selection

```
Database Selection Decision Tree
═══════════════════════════════════════════════════════════

PRIMARY CONCERN?
├─ MAXIMUM FLEXIBILITY & EXTENSIONS (JSON, arrays, vector search)
│  └─ PostgreSQL
│     ├─ Serverless → Neon (scale-to-zero, database branching)
│     └─ Traditional → Self-hosted, AWS RDS, Google Cloud SQL
│
├─ EMBEDDED / EDGE DEPLOYMENT (local-first, global latency)
│  └─ SQLite or Turso
│     ├─ Global distribution → Turso (libSQL, edge replicas)
│     └─ Local-only → SQLite (embedded, zero-config)
│
├─ LEGACY SYSTEM / MYSQL REQUIRED
│  └─ MySQL
│     ├─ Serverless → PlanetScale (non-blocking migrations)
│     └─ Traditional → Self-hosted, AWS RDS, Google Cloud SQL
│
└─ RAPID PROTOTYPING
   ├─ Python → SQLModel (FastAPI) or SQLAlchemy 2.0
   ├─ TypeScript → Prisma (best DX) or Drizzle (performance)
   ├─ Rust → SQLx (compile-time checks)
   └─ Go → sqlc (type-safe code generation)
```

## Quick Reference: ORM vs Query Builder

```
ORM vs Query Builder Selection
═══════════════════════════════════════════════════════════

TEAM PRIORITIES?
├─ DEVELOPMENT SPEED / DEVELOPER EXPERIENCE
│  └─ ORM (abstracts SQL, handles relations automatically)
│     ├─ Python → SQLAlchemy 2.0, SQLModel
│     ├─ TypeScript → Prisma (migrations, type generation)
│     ├─ Rust → SeaORM (Active Record + Data Mapper)
│     └─ Go → GORM, Ent
│
├─ PERFORMANCE / QUERY CONTROL
│  └─ Query Builder (SQL-like, zero abstraction overhead)
│     ├─ Python → SQLAlchemy Core, asyncpg
│     ├─ TypeScript → Drizzle, Kysely
│     ├─ Rust → SQLx (compile-time query validation!)
│     └─ Go → sqlc (generates types from SQL)
│
├─ TYPE SAFETY / COMPILE-TIME GUARANTEES
│  ├─ Rust → SQLx (queries checked at build time)
│  ├─ Go → sqlc (generates types from SQL)
│  ├─ TypeScript → Prisma or Drizzle
│  └─ Python → SQLModel (Pydantic integration)
│
└─ COMPLEX QUERIES / JOINS
   ├─ SQL-first → Query builders or raw SQL
   └─ ORM-friendly → SeaORM, SQLAlchemy ORM
```

## Multi-Language Implementation

### Python: SQLAlchemy 2.0 + SQLModel

**Recommended Libraries:**
- **SQLAlchemy 2.0** - ORM + Core
- **SQLModel** - FastAPI integration, Pydantic validation
- **asyncpg** - Fast async PostgreSQL driver

**When to Use:**
- Production applications needing flexibility
- FastAPI/Starlette backends
- Async/await workflows

**Quick Pattern:**
```python
from sqlmodel import SQLModel, Field, Session
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
```

**See:** `references/orms-python.md` for full SQLAlchemy/SQLModel patterns, async workflows and connection pooling.

### TypeScript: Prisma vs Drizzle

**Quick Comparison:**
- **Prisma**: Best DX, auto-generated types, migrations included
- **Drizzle**: Best performance, SQL-like syntax, zero overhead

**See:** `references/orms-typescript.md` for detailed Prisma vs Drizzle comparison, Kysely and TypeORM patterns.

### Rust: SQLx (Compile-Time Checked)

**Recommended Libraries:**
- **SQLx 0.8** - Compile-time query validation, async
- **SeaORM 1.x** - Full ORM, Active Record pattern
- **Diesel 2.3** - Mature, stable (sync/async)

**Quick Pattern:**
```rust
use sqlx::FromRow;
#[derive(FromRow)]
struct User { id: i32, email: String, name: String }
// The query_as! macro checks SQL and column types at build time
// (needs DATABASE_URL or `cargo sqlx prepare` offline data)
let user = sqlx::query_as!(User, "SELECT id, email, name FROM users WHERE email = $1", "test@example.com")
    .fetch_one(&pool).await?;
// sqlx::query_as::<_, User>(...).bind(..) also works but is only checked at runtime
```

**See:** `references/orms-rust.md` for SQLx macros, SeaORM and Diesel patterns, compile-time guarantees.

### Go: sqlc (Type-Safe Code Generation)

**Recommended Libraries:**
- **sqlc** - Generates Go code from SQL queries
- **GORM v2** - Full ORM with associations, hooks
- **Ent** - Graph-based ORM, schema as code
- **pgx** - Fast PostgreSQL driver

**Quick Pattern:**
```sql
-- queries.sql: SQL annotations generate type-safe Go code
-- name: CreateUser :one
INSERT INTO users (email, name) VALUES ($1, $2) RETURNING *;
```
```go
user, err := queries.CreateUser(ctx, db.CreateUserParams{Email: "test@example.com"})
```

**See:** `references/orms-go.md` for sqlc setup, GORM, Ent and pgx patterns.

## Connection Pooling

**Recommended Pool Sizes:**
- Web API (single instance): 10-20 connections
- Serverless (per function): 1-2 connections + pgBouncer
- Background workers: 5-10 connections

**See:** `references/connection-pooling.md` for configuration examples, sizing formulas and monitoring.

## Migrations

**Critical Principles:**
1. Drop columns with multi-phase deployment (never drop directly in production)
2. Use `CREATE INDEX CONCURRENTLY` (PostgreSQL) to avoid blocking writes
3. Test migrations in staging with production-like data volume

**Tools:** Alembic (Python), Prisma Migrate (TypeScript), SQLx migrations (Rust), golang-migrate (Go)

**See:** `references/migrations-guide.md` for safe migration patterns, multi-phase deployments and rollback strategies.

## Serverless Databases

| Database | Type | Key Feature | Best For |
|----------|------|-------------|----------|
| **Neon** | PostgreSQL | Database branching, scale-to-zero | Development workflows, preview environments |
| **PlanetScale** | MySQL (Vitess) | Non-blocking schema changes | MySQL apps, zero-downtime migrations |
| **Turso** | SQLite (libSQL) | Edge deployment, low latency | Edge functions, global distribution |

**See:** `references/serverless-databases.md` for setup examples, branching workflows and cost comparisons.

## Frontend Integration

**Common Integration Patterns:**
- **Forms skill**: Form submission → API validation → Database CRUD (INSERT/UPDATE)
- **Tables skill**: Paginated queries → API → Table display with sorting/filtering
- **Dashboards skill**: Aggregation queries (COUNT, SUM) → API → KPI cards
- **Search-filter skill**: Full-text search (PostgreSQL tsvector) → Ranked results

## Bundled Resources

### Reference Documentation
- `references/postgresql-guide.md` - PostgreSQL features (pgvector, PostGIS, TimescaleDB)
- `references/mysql-guide.md` - MySQL-specific patterns, PlanetScale integration
- `references/sqlite-guide.md` - SQLite patterns, Turso edge deployment

### Working Examples
- `examples/python-sqlalchemy/` - SQLAlchemy 2.0 + FastAPI with pooling, migrations

For Prisma, Drizzle, SQLx and sqlc, use patterns from matching `references/orms-*.md` file.

### Utility Scripts
- `scripts/validate_schema.py` - Validates database schema structure and constraints
- `scripts/generate_migration.py` - Generates migration templates for common operations

## Best Practices

**Security:**
- Always use parameterized queries (prevents SQL injection)
- Hash passwords with Argon2/bcrypt
- Keep connection strings in environment variables; never print or inline them in commands (use `"$DATABASE_URL"`)
- Enable SSL/TLS in production (`sslmode=verify-full`)
- Confirm with user before destructive or production-facing commands: `migrate reset`, `db push`/`drizzle-kit push`, branch delete/restore, backup restores, deploy requests, data copies from production
- Opt out of CLI telemetry: `export CHECKPOINT_DISABLE=1 PRISMA_DISABLE_TELEMETRY=1` (Prisma), `neonctl --no-analytics`, `VERCEL_TELEMETRY_DISABLED=1` (Vercel)
- Pin CLI versions (`go install ...@vX.Y.Z`); bump deliberately

**Performance:**
- Index filtered/sorted columns
- Paginate large result sets
- Run `EXPLAIN ANALYZE` on slow queries

**Reliability:**
- Wrap multi-statement operations in transactions
- Monitor connection pool exhaustion
- Set up and test database backups

**Development:**
- Write integration tests against real databases
