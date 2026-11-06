---
name: golang-design-patterns
description: "Design Go APIs with functional options, interfaces, composition, constructors, and clear ownership. Select a pattern for a concrete design problem rather than adding abstractions by default."
user-invocable: true
license: MIT
compatibility: Designed for Claude Code, Codex or similar harness, and for projects using Golang.
metadata:
  author: samber
  version: "1.2.1"
  openclaw:
    emoji: "🏗"
    homepage: https://github.com/samber/cc-skills-golang
    requires:
      bins:
        - go
    install: []
allowed-tools: Read Edit Write Glob Grep Bash(go build:*) Bash(go test:*) Bash(go vet:*) Bash(golangci-lint run:*) Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git show:*) Agent AskUserQuestion
paths:
  - "**/*.go"
---

**Persona:** Go architect who values simplicity and explicitness. Apply patterns only when they solve real problem, not to show sophistication. Push back on premature abstraction.

**Modes:**

- **Design mode** — new APIs, packages, application structure: ask developer's architecture preference before proposing patterns; favor smallest pattern meeting requirement.
- **Review mode** — audit existing code: scan for `init()` abuse, unbounded resources, missing timeouts, implicit global state; report findings before suggesting refactors.

> **Community default.** Company skill that explicitly supersedes `samber/cc-skills-golang@golang-design-patterns` skill takes precedence.

# Go Design Patterns & Idioms

## Best Practices Summary

1. Constructors SHOULD use **functional options** — scale as APIs evolve (one function per option, no breaking changes)
2. Functional options MUST **return an error** if validation can fail — catch bad config at construction, not runtime
3. **Avoid `init()`** — implicit, cannot return errors, makes tests unpredictable. Use explicit constructors
4. Enums SHOULD **start at 1** (or Unknown sentinel at 0) — Go's zero value silently passes as first member
5. Error cases MUST be **handled first** with early return — keep happy path flat → see `samber/cc-skills-golang@golang-code-style`
6. **Panic is for bugs, not expected errors** — callers handle returned errors; panics crash process
7. **`defer Close()` immediately after opening** — later edits can skip cleanup
8. **`runtime.AddCleanup`** over `runtime.SetFinalizer` — finalizers are unpredictable, can resurrect objects
9. Every external call SHOULD **have a timeout** — slow upstream hangs goroutine indefinitely
10. **Limit everything** (pool sizes, queue depths, buffers) — unbounded resources grow until crash
11. Retry logic MUST **check context cancellation** between attempts
12. **Use `strings.Builder`** for concatenation in loops → see `samber/cc-skills-golang@golang-code-style`
13. string vs []byte: **use `[]byte` for mutation and I/O**, `string` for display and keys — conversions allocate
14. Iterators (Go 1.23+): **use for lazy evaluation** — avoid loading everything into memory
15. **Stream large transfers** — loading millions of rows causes OOM; streaming keeps memory constant
16. `//go:embed` for **static assets** — embedded at compile time, no runtime file I/O errors
17. **Use `crypto/rand`** for keys/tokens — `math/rand` is predictable → see `samber/cc-skills-golang@golang-security`
18. Regexp MUST be **compiled once at package level** — compilation is O(n), allocates
19. Compile-time interface checks: **`var _ Interface = (*Type)(nil)`** → see `samber/cc-skills-golang@golang-structs-interfaces`
20. **A little recode > a big dependency** — each dep adds attack surface, maintenance burden
21. **Design for testability** — accept interfaces, inject dependencies, keep functions pure

## Constructor Patterns: Functional Options vs Builder

### Functional Options (Preferred)

```go
type Server struct {
    addr         string
    readTimeout  time.Duration
    writeTimeout time.Duration
    maxConns     int
}

type Option func(*Server)

func WithReadTimeout(d time.Duration) Option {
    return func(s *Server) { s.readTimeout = d }
}

func WithWriteTimeout(d time.Duration) Option {
    return func(s *Server) { s.writeTimeout = d }
}

func WithMaxConns(n int) Option {
    return func(s *Server) { s.maxConns = n }
}

func NewServer(addr string, opts ...Option) *Server {
    // Default options
    s := &Server{
        addr:         addr,
        readTimeout:  5 * time.Second,
        writeTimeout: 10 * time.Second,
        maxConns:     100,
    }
    for _, opt := range opts {
        opt(s)
    }
    return s
}

// Usage
srv := NewServer(":8080",
    WithReadTimeout(30*time.Second),
    WithMaxConns(500),
)
```

If option can be invalid, make option type return error; constructor returns it (rule 2):

```go
type Option func(*Server) error

func WithMaxConns(n int) Option {
    return func(s *Server) error {
        if n <= 0 {
            return fmt.Errorf("max conns must be positive, got %d", n)
        }
        s.maxConns = n
        return nil
    }
}

func NewServer(addr string, opts ...Option) (*Server, error) {
    s := &Server{addr: addr, readTimeout: 5 * time.Second, writeTimeout: 10 * time.Second, maxConns: 100}
    for _, opt := range opts {
        if err := opt(s); err != nil {
            return nil, fmt.Errorf("new server: %w", err)
        }
    }
    return s, nil
}
```

Use builder pattern only for complex validation between configuration steps.

## Constructors & Initialization

### Avoid `init()` and Mutable Globals

`init()` runs implicitly, hinders testing, creates hidden dependencies:

- Multiple `init()` functions run in declaration order, across files in **filename alphabetical order** — fragile
- Cannot return errors — failures must panic or `log.Fatal`
- Runs before `main()` and tests — side effects make tests unpredictable

```go
// Bad — hidden global state
var db *sql.DB

func init() {
    var err error
    db, err = sql.Open("postgres", os.Getenv("DATABASE_URL"))
    if err != nil {
        log.Fatal(err)
    }
}

// Good — explicit initialization, injectable
func NewUserRepository(db *sql.DB) *UserRepository {
    return &UserRepository{db: db}
}
```

### Enums: Start at 1

```go
type Status int

const (
    StatusUnknown Status = iota // 0 = invalid/unset
    StatusActive                // 1
    StatusInactive              // 2
    StatusSuspended             // 3
)
```

### Compile Regexp Once

```go
// Good — compiled once at package level
var emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)

func ValidateEmail(email string) bool {
    return emailRegex.MatchString(email)
}
```

### Use `//go:embed` for Static Assets

```go
import "embed"

//go:embed templates/*
var templateFS embed.FS

//go:embed version.txt
var version string
```

## Error Flow Patterns

### When to Panic vs Return Error

- **Return error**: network failures, file not found, invalid input — anything caller can handle
- **Panic**: nil pointer where it should be impossible, violated invariant, `Must*` constructors used at init time
- **`.Close()` / `Flush()` errors**: read-only cleanup can often use `defer f.Close()`; write/flush resources must report close or flush errors when durability matters

## Data Handling

### string vs []byte vs []rune

| Type     | Default for | Use when                                            |
| -------- | ----------- | --------------------------------------------------- |
| `string` | Everything  | Immutable, safe, UTF-8                              |
| `[]byte` | I/O         | Writing to `io.Writer`, building strings, mutations |
| `[]rune` | Unicode ops | `len()` must mean characters, not bytes             |

Avoid repeated conversions — each allocates. Stay in one type until you need the other.

### Iterators & Streaming for Large Data

Code examples: [Data Handling Patterns](references/data-handling.md).

## Resource Management

`defer Close()` examples, graceful shutdown, resource pools and `runtime.AddCleanup`: see [Resource Management](references/resource-management.md).

## Resilience & Limits

### Timeout Every External Call

```go
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()

resp, err := httpClient.Do(req.WithContext(ctx))
```

### Retry & Context Checks

Retry logic MUST check `ctx.Err()` between attempts and use exponential/linear backoff via `select` on `ctx.Done()`. Long loops MUST check `ctx.Err()` periodically. → See `samber/cc-skills-golang@golang-context` skill.

## Database Patterns

→ See `samber/cc-skills-golang@golang-database` skill for sqlx/pgx, transactions, nullable columns, connection pools, repository interfaces, testing.

## Architecture

Ask developer's preferred architecture: clean architecture, hexagonal, DDD, or flat layout. Don't impose complex architecture on small project.

Core principles regardless of architecture (details: [Architecture Patterns](references/architecture.md)):

- **Keep domain pure** — no framework dependencies in domain layer
- **Fail fast** — validate at boundaries, trust internal code
- **Make illegal states unrepresentable** — use types to enforce invariants
- **Respect 12-factor app** principles → see `samber/cc-skills-golang@golang-project-layout`

## Detailed Guides

| Guide | Scope |
| --- | --- |
| [Architecture Patterns](references/architecture.md) | High-level principles, when each architecture fits |
| [Clean Architecture](references/clean-architecture.md) | Use cases, dependency rule, layered adapters |
| [Hexagonal Architecture](references/hexagonal-architecture.md) | Ports and adapters, domain core isolation |
| [Domain-Driven Design](references/ddd.md) | Aggregates, value objects, bounded contexts |

## Cross-References

- → See `samber/cc-skills-golang@golang-data-structures` skill for data structure selection, internals, container/ packages
- → See `samber/cc-skills-golang@golang-error-handling` skill for error wrapping, sentinel errors, single handling rule
- → See `samber/cc-skills-golang@golang-structs-interfaces` skill for interface design and composition
- → See `samber/cc-skills-golang@golang-concurrency` skill for goroutine lifecycle and graceful shutdown
- → See `samber/cc-skills-golang@golang-context` skill for timeout and cancellation patterns
- → See `samber/cc-skills-golang@golang-project-layout` skill for architecture and directory structure
- → See `samber/cc-skills-golang@golang-refactoring` skill to safely stage migration toward one of these patterns (options struct, DI, consumer-side interfaces) across existing codebase
