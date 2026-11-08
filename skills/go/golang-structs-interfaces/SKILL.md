---
name: golang-structs-interfaces
description: "Design Go types and interfaces with composition, embedding, narrow contracts, and explicit ownership. Use for API/type design or a concrete nil/interface issue, preserving existing published behavior."
user-invocable: true
license: MIT
compatibility: Designed for Claude Code, Codex or similar harness, and for projects using Golang.
metadata:
  author: samber
  version: "1.2.1"
  openclaw:
    emoji: "🧩"
    homepage: https://github.com/samber/cc-skills-golang
    requires:
      bins:
        - go
    install: []
allowed-tools: Read Edit Write Glob Grep Bash(go build:*) Bash(go vet:*) Bash(go test:*) Bash(go doc:*) Bash(golangci-lint run:*) Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git show:*) Agent AskUserQuestion
paths:
  - "**/*.go"
---

**Persona:** Go type system designer. Favor small, composable interfaces and concrete return types. Design for testability and clarity, not for abstraction's sake.

> **Community default.** Company skill that explicitly supersedes `samber/cc-skills-golang@golang-structs-interfaces` skill takes precedence.

# Go Structs & Interfaces

## Interface Design Principles

### Keep Interfaces Small

> "The bigger the interface, the weaker the abstraction." — Go Proverbs

Interfaces SHOULD have 1-3 methods. Build larger contracts from small interfaces:

→ See `samber/cc-skills-golang@golang-naming` skill for interface naming conventions (method + "-er" suffix, canonical names)

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

// Composed from small interfaces
type ReadWriter interface {
    Reader
    Writer
}
```

### Define Interfaces Where They're Consumed

Interfaces MUST be defined where consumed, not where implemented. Keeps consumer in control of contract; avoids importing a package just for its interface.

```go
// package notification — defines only what it needs
type Sender interface {
    Send(to, body string) error
}

type Service struct {
    sender Sender
}
```

`email` package exports concrete `Client` struct and need not know about `Sender`.

### Accept Interfaces, Return Structs

Functions SHOULD accept interface parameters (flexibility) and return concrete types (clarity). Callers get full access to returned type's fields and methods; upstream can still assign result to interface variable.

```go
// Good — accepts interface, returns concrete
func NewService(store UserStore) *Service { ... }

// Bad — an interface return hides every other method of the concrete type from callers
func NewService(store UserStore) ServiceInterface { ... }
```

### Don't Create Interfaces Prematurely

> "Don't design with interfaces, discover them."

Start concrete. Extract interface once second consumer, second implementation, or test mock demands it.

```go
// Bad — premature interface with a single implementation
type UserRepository interface {
    FindByID(ctx context.Context, id string) (*User, error)
}
type userRepository struct { db *sql.DB }

// Good — start concrete, extract an interface later when needed
type UserRepository struct { db *sql.DB }
```

## Make the Zero Value Useful

Structs should work without explicit initialization:

```go
// Good — zero value is ready to use
var buf bytes.Buffer
buf.WriteString("hello")

var mu sync.Mutex
mu.Lock()

// Bad — zero value is broken, requires constructor
type Registry struct {
    items map[string]Item // nil map, panics on write
}

// Good — lazy initialization guards the zero value
func (r *Registry) Register(name string, item Item) {
    if r.items == nil {
        r.items = make(map[string]Item)
    }
    r.items[name] = item
}
```

## Avoid `any` / `interface{}` When a Specific Type Will Do

Since Go 1.18+, MUST prefer generics over `any` for type-safe operations. Use `any` only at true boundaries where type is unknown (e.g., JSON decoding, reflection):

```go
// Bad — loses type safety
func Contains(slice []any, target any) bool { ... }

// Good — generic, type-safe
func Contains[T comparable](slice []T, target T) bool { ... }
```

## Key Standard Library Interfaces

| Interface     | Package         | Method                                |
| ------------- | --------------- | ------------------------------------- |
| `Reader`      | `io`            | `Read(p []byte) (n int, err error)`   |
| `Writer`      | `io`            | `Write(p []byte) (n int, err error)`  |
| `Closer`      | `io`            | `Close() error`                       |
| `Stringer`    | `fmt`           | `String() string`                     |
| `error`       | builtin         | `Error() string`                      |
| `Handler`     | `net/http`      | `ServeHTTP(ResponseWriter, *Request)` |
| `Marshaler`   | `encoding/json` | `MarshalJSON() ([]byte, error)`       |
| `Unmarshaler` | `encoding/json` | `UnmarshalJSON([]byte) error`         |

Canonical method signatures MUST be honored: `String()` method must match `fmt.Stringer`. Do not invent `ToString()` or `ReadData()`.

## Compile-Time Interface Check

Verify interface satisfaction at compile time with blank identifier assignment, near type definition:

```go
var _ io.ReadWriter = (*MyBuffer)(nil)
```

Zero runtime cost. If `MyBuffer` stops satisfying `io.ReadWriter`, build fails.

## Type Assertions & Type Switches

Type assertions MUST use comma-ok form (`s, ok := val.(string)`). Single-value form panics on mismatch instead of branching. Use type switch to dispatch on dynamic type. Assert to small optional interface (`if f, ok := w.(Flusher); ok`) to exploit richer implementations without widening declared parameter type.

→ See [Type Assertions & Type Switches](references/type-assertions.md) for type switch ordering, nil cases, optional-behavior pattern.

## Struct & Interface Embedding

### Struct Embedding

Embedding promotes inner type's methods and fields to outer type. Composition, not inheritance:

```go
type Logger struct {
    *slog.Logger
}

type Server struct {
    Logger
    addr string
}

// s.Info(...) works — promoted from slog.Logger through Logger
s := Server{Logger: Logger{slog.Default()}, addr: ":8080"}
s.Info("starting", "addr", s.addr)
```

Promoted methods' receiver is the _inner_ type, not outer. Outer type overrides by defining same-name method.

### When to Embed vs Named Field

| Use | When |
| --- | --- |
| **Embed** | Promote full API of inner type. Outer type "is a" enhanced version |
| **Named field** | Need inner type only internally. Outer type "has a" dependency |

```go
// Embed — Server exposes all http.Handler methods
type Server struct {
    http.Handler
}

// Named field — Server uses the store but doesn't expose its methods
type Server struct {
    store *DataStore
}
```

## Dependency Injection via Interfaces

Accept dependencies as interfaces in constructors (see `NewService(store UserStore) *Service` above). Decouples components. In tests, pass mock or stub satisfying `UserStore`; no real database needed.

## Struct Field Tags

Exported fields in serialized structs MUST have field tags. Without tag, encoder uses Go field name; renaming field silently changes wire format.

→ See [Struct Fields: Tags and Copy Safety](references/struct-fields.md) for full tag directive table, `omitempty` vs `omitzero` trap, `go vet` diagnostics.

## Pointer vs Value Receivers

| Use pointer `(s *Server)` | Use value `(s Server)` |
| --- | --- |
| Method modifies receiver | Receiver is small and immutable |
| Receiver contains `sync.Mutex` or similar | Receiver is basic type (int, string) |
| Receiver is large struct | Method is read-only accessor |
| Consistency: if any method uses pointer, all should | Map and function values (already reference types) |

Receiver type MUST be consistent across all methods of a type: one pointer receiver means all pointer receivers.

## Preventing Struct Copies with `noCopy`

Struct holding mutex, channel, or internal pointers breaks when copied. Embed `noCopy` sentinel so `go vet` reports every value copy. Pass such structs by pointer.

**Diagnose:** 1- `go vet ./...` — `copylocks` reports value copies of lock-bearing structs

→ See [Struct Fields: Tags and Copy Safety](references/struct-fields.md) for `noCopy` implementation and how `vet` detects it.

## Cross-References

- → See `samber/cc-skills-golang@golang-design-patterns` skill for functional options, constructors, builder patterns
- → See `samber/cc-skills-golang@golang-dependency-injection` skill for DI patterns using interfaces
- → See `samber/cc-skills-golang@golang-code-style` skill for value vs pointer function parameters (distinct from receivers)
- → See `samber/cc-skills-golang@golang-gopls` skill for safe rename and `implementInterface` code action. gopls rename updates every call site of a method or receiver in interface satisfaction. It refuses renames that would silently break the interface, which grep/sed cannot detect

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Large interfaces (5+ methods) | Split into focused 1-3 method interfaces, compose if needed |
| Embedding when only a few methods are needed | Use named field, delegate explicitly |
