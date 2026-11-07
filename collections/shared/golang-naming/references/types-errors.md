# Types, Constants & Errors

## Table of Contents

- [Interfaces](#interfaces)
  - [Single-Method Interfaces](#single-method-interfaces)
  - [Multi-Method Interfaces](#multi-method-interfaces)
  - [Canonical Method Names](#canonical-method-names)
- [Structs](#structs)
- [Constants](#constants)
  - [Enums (iota)](#enums-iota)
- [Errors](#errors)
  - [Sentinel Errors](#sentinel-errors)
  - [Error Types](#error-types)
  - [Error Strings](#error-strings)

## Interfaces

### Single-Method Interfaces

Use **method name + `-er`** suffix:

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Stringer interface {
    String() string
}

type Closer interface {
    Close() error
}
```

### Multi-Method Interfaces

Use descriptive **noun** or compose from single-method interfaces:

```go
type ReadWriteCloser interface {
    Reader
    Writer
    Closer
}

type Handler interface {
    ServeHTTP(ResponseWriter, *Request)
}
```

### Canonical Method Names

Honor established Go method names and signatures. Type implementing `Read` MUST match `io.Reader`'s signature. NEVER invent variants like `ReadData` or `ToString`; use `String`.

| Method name | Expected interface |
| ----------- | ------------------ |
| `Read`      | `io.Reader`        |
| `Write`     | `io.Writer`        |
| `Close`     | `io.Closer`        |
| `String`    | `fmt.Stringer`     |
| `Error`     | `error`            |
| `Len`       | `sort.Interface`   |
| `ServeHTTP` | `http.Handler`     |

## Structs

Name structs with **MixedCaps nouns** describing entity. Fields follow exported/unexported rules.

```go
type Server struct {
    Addr     string        // exported
    Handler  http.Handler  // exported
    timeout  time.Duration // unexported
}
```

NEVER suffix struct names with `Struct`, `Object`, or `Data`.

## Constants

Constants MUST use **MixedCaps**, NEVER `ALL_CAPS`. Name should explain **role**, not **value**.

```go
// Good — MixedCaps, name explains purpose
const MaxRetries = 3
const defaultTimeout = 30 * time.Second
const DefaultPort = 8080

// Bad — ALL_CAPS is not idiomatic Go
const MAX_RETRIES = 3
const DEFAULT_TIMEOUT = 30

// Bad — name is the value, not the purpose
const Three = 3
const Port8080 = 8080
```

### Enums (iota)

Prefix enum values with **type name**: avoids collisions, reads better at call site.

```go
type Status int

const (
    StatusUnknown Status = iota // zero value = unknown/invalid
    StatusReady
    StatusRunning
    StatusDone
)

type Color int

const (
    ColorRed Color = iota + 1  // skip zero to catch uninitialized values
    ColorGreen
    ColorBlue
)
```

**Always protect the zero value.** `var s Status` silently becomes 0. If 0 is real state like `StatusReady`, code can treat unset status as deliberate choice. Either put explicit `Unknown` sentinel at iota 0, or start at `iota + 1`. Not optional: uninitialized enums commonly cause silent bugs.

## Errors

### Sentinel Errors

Sentinel error variables use `Err` prefix. Error strings SHOULD prefix package name to identify origin when errors are wrapped:

```go
// Good — package prefix identifies origin
var ErrNotFound = errors.New("mypackage: not found")
var ErrPermissionDenied = errors.New("mypackage: permission denied")
var ErrTimeout = errors.New("mypackage: operation timed out")

// Bad — bare strings lose origin when wrapped
var ErrNotFound = errors.New("not found")
```

### Error Types

Custom error types use `Error` suffix:

```go
type PathError struct {
    Op   string
    Path string
    Err  error
}

type SyntaxError struct {
    Offset int64
    msg    string
}
```

### Error Strings

Error strings MUST NOT be **capitalized** and MUST NOT **end with punctuation**: they often print after other context (`fmt.Errorf("parsing config: %w", err)`). Per Go Code Review Comments, proper nouns and initialisms (`ID`, `URL`, `HTTP`) keep usual case.

```go
// Good — lowercase start, initialisms keep their case, no punctuation
errors.New("image: unknown format")
errors.New("mypackage: invalid message ID")
errors.New("mypackage: invalid URL")
fmt.Errorf("decoding config: %w", err)

// Bad — capitalized start, punctuation
errors.New("Image: Unknown format.")
fmt.Errorf("Failed to decode config: %w.", err)
```
