---
name: golang-database
description: "Implement or review Go database queries, parameterization, scanning, transactions, context cancellation, pooling, and cleanup. Preserve the project's SQL driver, ORM, and migration conventions."
user-invocable: true
license: MIT
compatibility: Designed for Claude Code, Codex or similar harness, and for projects using Golang.
metadata:
  author: samber
  version: "1.3.2"
  openclaw:
    emoji: "🗄"
    homepage: https://github.com/samber/cc-skills-golang
    requires:
      bins:
        - go
    install: []
allowed-tools: Read Edit Write Glob Grep Bash(go build:*) Bash(go vet:*) Bash(go test:*) Bash(golangci-lint run:*) Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git show:*) Agent AskUserQuestion
paths:
  - "**/*.go"
---

**Persona:** Go backend engineer. Write safe, explicit, observable database code. SQL is first-class — no ORMs, no magic. Catch data integrity issues at boundary, not deep in application.

**Modes:**

- **Write mode** — repository functions, query helpers, transactions: inspect existing query and naming conventions first. Large codebase: authorized read-only scout may help; else search inline.
- **Review/debug mode** — audit resource cleanup, parameterization, cancellation, errors alongside business logic. Broad authorized audit: split read-only modules among available reviewers. Focused fix usually clearer inline.

> **Community default.** Company skill explicitly superseding `samber/cc-skills-golang@golang-database` skill takes precedence.

# Go Database Best Practices

Go's `database/sql` is solid foundation. New code: prefer `sqlx` or `pgx` on top of it over ORM. Existing ORM project: follow its conventions.

sqlx or pgx: check library's official docs and code examples for current API signatures.

## Best Practices Summary

1. Queries MUST use parameterized placeholders — NEVER concatenate user input into SQL strings
2. Context MUST reach all database operations — use `*Context` variants (`QueryContext`, `ExecContext`, `GetContext`)
3. `sql.ErrNoRows` MUST be handled explicitly — `errors.Is` separates "not found" from real errors
4. Rows MUST be closed after iteration — `defer rows.Close()` immediately after `QueryContext`
5. NEVER use `db.Query` for statements returning no rows — `Query` returns `*Rows` that must be closed; if forgotten, connection leaks back to pool. Use `db.Exec`
6. **Use transactions for multi-statement operations** — wrap related writes in `BeginTxx`/`Commit`
7. **Use `SELECT ... FOR UPDATE`** when reading data you will modify — prevents race conditions
8. **Set custom isolation levels** when default READ COMMITTED falls short (e.g., serializable for financial operations)
9. **Handle NULLable columns** with pointer fields (`*string`, `*int`) or `sql.NullXxx` types
10. Connection pool MUST be configured — `SetMaxOpenConns`, `SetMaxIdleConns`, `SetConnMaxLifetime`, `SetConnMaxIdleTime`
11. **Use external tools for migrations** — golang-migrate, Flyway or Atlas (or project's existing tool). Never ad-hoc schema changes from application code. Migration SQL requested: write versioned migration file (plus down migration where tool supports it); flag it for human review before it runs against production
12. **Batch operations in reasonable sizes** — not row-by-row (too many round trips), not millions at once (locks, memory)
13. **Create or modify schemas only when asked; flag the risk** — schema that looks correct on toy data can cause hotspots, lock contention or missing indexes under real production load. State assumptions (data volumes, access patterns, DDL locking behavior). Require human review before applying.

## Library Choice

| Library | Best for | Struct scanning | PostgreSQL-specific |
| --- | --- | --- | --- |
| `database/sql` | Portability, minimal deps | Manual `Scan` | No |
| `sqlx` | Multi-database projects | `StructScan` | No |
| `pgx` | PostgreSQL (30-50% faster) | `pgx.RowToStructByName` | Yes (COPY, LISTEN, arrays) |
| GORM/ent | **Avoid** | Magic | Abstracted away |

**Why NOT ORMs:**

- ORMs hide SQL; unpredictable queries — N+1 problems you cannot see in code
- Magic hooks and callbacks (BeforeCreate, AfterUpdate) hinder debugging
- Schema migrations coupled to application code
- ORM API harder to learn than SQL; abstraction leaks

## Parameterized Queries

```go
// ✗ VERY BAD — SQL injection vulnerability
query := fmt.Sprintf("SELECT * FROM users WHERE email = '%s'", email)

// ✓ Good — parameterized (PostgreSQL)
var user User
err := db.GetContext(ctx, &user, "SELECT id, name, email FROM users WHERE email = $1", email)

// ✓ Good — parameterized (MySQL)
err := db.GetContext(ctx, &user, "SELECT id, name, email FROM users WHERE email = ?", email)
```

### Dynamic IN clauses

```go
query, args, err := sqlx.In("SELECT * FROM users WHERE id IN (?)", ids)
if err != nil {
    return fmt.Errorf("building IN clause: %w", err)
}
query = db.Rebind(query) // adjust placeholders for your driver
err = db.SelectContext(ctx, &users, query, args...)
```

### Dynamic column names

Never interpolate column names from user input. Use allowlist:

```go
allowed := map[string]bool{"name": true, "email": true, "created_at": true}
if !allowed[sortCol] {
    return fmt.Errorf("invalid sort column: %s", sortCol)
}
query := fmt.Sprintf("SELECT id, name, email FROM users ORDER BY %s", sortCol)
```

## Struct Scanning and NULLable Columns

sqlx: `db:"column_name"` tags. pgx: `pgx.CollectRows` with `pgx.RowToStructByName`. NULLable columns: pointer fields (`*string`, `*time.Time`) — clean with scanning and JSON marshaling. All approaches: [Scanning Reference](./references/scanning.md).

## Error Handling

```go
func GetUser(ctx context.Context, id string) (*User, error) {
    var user User

    err := db.GetContext(ctx, &user, "SELECT id, name FROM users WHERE id = $1", id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, ErrUserNotFound // translate to domain error
        }
        return nil, fmt.Errorf("querying user %s: %w", id, err)
    }

    return &user, nil
}
```

or:

```go
func GetUser(ctx context.Context, id string) (u *User, exists bool, err error) {
    var user User

    err = db.GetContext(ctx, &user, "SELECT id, name FROM users WHERE id = $1", id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, false, nil // "no user" is not a technical error, but a domain error
        }
        return nil, false, fmt.Errorf("querying user %s: %w", id, err)
    }

    return &user, true, nil
}
```

### Always close rows

```go
rows, err := db.QueryContext(ctx, "SELECT id, name FROM users")
if err != nil {
    return fmt.Errorf("querying users: %w", err)
}
defer rows.Close() // prevents connection leaks

for rows.Next() {
    // ...
}
if err := rows.Err(); err != nil { // always check after iteration
    return fmt.Errorf("iterating users: %w", err)
}
```

### Common database error patterns

| Error | How to detect | Action |
| --- | --- | --- |
| Row not found | `errors.Is(err, sql.ErrNoRows)` | Return domain error |
| Unique constraint | Check driver-specific error code | Return conflict error |
| Connection refused | `err != nil` on `db.PingContext` | Fail fast, log, retry with backoff |
| Serialization failure | PostgreSQL error code `40001` | Retry entire transaction |
| Context canceled | `errors.Is(err, context.Canceled)` | Stop processing, propagate |

## Context Propagation

```go
// ✗ Bad — no context, query runs until completion even if client disconnects
db.Query("SELECT ...")

// ✓ Good — respects context cancellation and timeouts
db.QueryContext(ctx, "SELECT ...")
```

## Connection Pool

```go
db.SetMaxOpenConns(25)              // limit total connections
db.SetMaxIdleConns(10)              // keep warm connections ready
db.SetConnMaxLifetime(5 * time.Minute)  // recycle stale connections
db.SetConnMaxIdleTime(1 * time.Minute)  // close idle connections faster
```

Sizing guidance and formulas: [Database Performance](./references/performance.md).

## Migrations

Schema changes need human review with understanding of data volumes, existing indexes, foreign keys, production constraints.

Recommended tools:

- [golang-migrate](https://github.com/golang-migrate/migrate) — CLI + Go library, all major databases
- [Flyway](https://flywaydb.org/) — JVM-based, common in enterprise
- [Atlas](https://atlasgo.io/) — modern, declarative schema management

May draft migration SQL when user asks. It MUST be human-reviewed, versioned in source control, applied via project's migration tool or CI/CD pipeline — never run directly against shared or production database.

## Avoid Hidden SQL Features

Do not rely on triggers, views, materialized views, stored procedures or row-level security in application code — invisible side effects, impossible debugging. Keep SQL explicit and visible in Go: testable, version-controlled.

## Schema Creation

**This skill does not cover schema design in depth** — use database-design skill (using-relational-databases for engine specifics). Schema or migration requested: write it, but name what you could not know (data volumes, access patterns, query profiles, business constraints). List chosen indexes and constraints with reasons. Ask for human review before applying. Generated schemas often subtly wrong — missing indexes, incorrect column types, bad normalization, missing constraints.

## Deep Dives

- **[Transactions](./references/transactions.md)** — Transaction boundaries, isolation levels, deadlock prevention, `SELECT FOR UPDATE`
- **[Testing Database Code](./references/testing.md)** — Mock connections, integration tests with containers, fixtures, schema setup/teardown
- **[Database Performance](./references/performance.md)** — Connection pool sizing, batch processing, indexing strategy, query optimization
- **[Struct Scanning](./references/scanning.md)** — Struct tags, NULLable column handling, JSON marshaling patterns

## Cross-References

- → `samber/cc-skills-golang@golang-security` skill: SQL injection prevention
- → `samber/cc-skills-golang@golang-context` skill: context propagation to database operations
- → `samber/cc-skills-golang@golang-error-handling` skill: database error wrapping
- → `samber/cc-skills-golang@golang-testing` skill: database integration tests

## References

- [database/sql tutorial](https://go.dev/doc/database/)
- [sqlx](https://github.com/jmoiron/sqlx)
- [pgx](https://github.com/jackc/pgx)
