# Functions, Methods & Options

## Table of Contents

- [Functions and Methods](#functions-and-methods)
  - [Getters and Setters](#getters-and-setters)
  - [Constructors](#constructors)
  - [Named Return Values](#named-return-values)
- [Functional Options Pattern](#functional-options-pattern)

## Functions and Methods

Value-returning functions: **nouns** (what they return). Action functions: **verbs** (what they do).

```go
// Noun-like: returns something
func UserName() string { ... }
func DefaultConfig() Config { ... }

// Verb-like: performs an action
func WriteFile(name string, data []byte) error { ... }
func SendNotification(user *User) error { ... }
```

NEVER repeat package name in function names:

```go
// Good: users call http.Get(), not http.HTTPGet()
package http
func Get(url string) (*Response, error)

// Bad: stutters at the call site
package http
func HTTPGet(url string) (*Response, error)
```

Functions taking format string and variadic args (like `fmt.Sprintf`) MUST end with **`f`**:

```go
// Good
func Errorf(format string, args ...any) error
func Wrapf(err error, format string, args ...any) error
func Logf(format string, args ...any)

// Bad
func Error(format string, args ...any) error    // looks like it takes a plain string
func WrapError(err error, format string, args ...any) error
```

### Getters and Setters

Getters MUST NOT use `Get` prefix. Getter is field name, capitalized.

```go
// Good
func (u *User) Name() string        { return u.name }
func (u *User) SetName(name string)  { u.name = name }

// Bad
func (u *User) GetName() string      { return u.name }
```

Use `Get` only when underlying concept inherently uses "get" (e.g., HTTP GET). For expensive or blocking operations, use `Fetch` or `Compute` to signal non-trivial call.

**Exception — boolean predicates keep the `Is`/`Has`/`Can` prefix.** No-Get rule covers value getters, not boolean predicates. Method returning `bool` SHOULD use `Is`/`Has`/`Can` to read as question, like stdlib (`reflect.Type.IsVariadic()`, `net.IP.IsLoopback()`, `big.Int.IsInt64()`).

```go
// Good — boolean predicate keeps Is prefix
func (s *Server) IsHealthy() bool   { return s.healthy }

// Good — value getter omits Get prefix
func (s *Server) Port() int         { return s.port }

// Good — richer return type, bare name is fine (different semantics)
func (s *Server) Healthy() (HealthStatus, error)

// Bad — bare adjective for bool is ambiguous
func (s *Server) Healthy() bool     { return s.healthy }

// Bad — Get prefix on value getter is redundant
func (s *Server) GetPort() int      { return s.port }
```

### Constructors

`New` when package exports single primary type; `NewTypeName` when it has multiple types.

```go
// Single primary type — New is unambiguous
package ring
func New(size int) *Ring

// Multiple types — qualify with the type name
package http
func NewRequest(method, url string, body io.Reader) (*Request, error)
func NewServeMux() *ServeMux
```

### Named Return Values

Named returns SHOULD appear only when they aid readability: typically several returns of same type, or names as documentation.

```go
// Good — names clarify which int64 is which
func Copy(dst Writer, src Reader) (written int64, err error)
func ScanBytes(data []byte, atEOF bool) (advance int, token []byte, err error)

// Good — single error return, no name needed
func Write(p []byte) (int, error)

// Bad — names add no clarity
func Read(p []byte) (bytes int, e error)  // "bytes" shadows the package, "e" is non-standard
```

NEVER use named returns just to enable bare `return`.

## Functional Options Pattern

Constructor with 3+ optional parameters that may grow: use **functional options pattern** for extensible APIs.

- **Struct**: `ServerOptions`, `ClientOptions` (not `Opts`, `Params`, `Settings`, `Config`)
- **Function type**: `ServerOption` (singular, not plural)
- **With\* functions**: `WithPort()`, `WithTimeout()`, `WithLogger()`
- **Factory**: `DefaultServerOptions()`
