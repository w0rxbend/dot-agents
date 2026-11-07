# Error Creation

## Table of Contents

- [Errors as Values](#errors-as-values)
- [Error String Conventions](#error-string-conventions)
- [Creating Errors](#creating-errors)
  - [`errors.New` — static error messages](#errorsnew--static-error-messages)
  - [`fmt.Errorf` — dynamic error messages](#fmterrorf--dynamic-error-messages)
  - [Decision table: which error strategy to use](#decision-table-which-error-strategy-to-use)
- [Low-Cardinality Error Messages](#low-cardinality-error-messages)
- [Custom Error Types](#custom-error-types)
  - [Custom types that wrap other errors](#custom-types-that-wrap-other-errors)

## Errors as Values

Go errors are ordinary values implementing `error` interface:

```go
type error interface {
    Error() string
}
```

Returned, not thrown. Every function that can fail returns `error` as last return value. Every caller must check it.

```go
// ✗ Bad — silently discarding errors
data, _ := os.ReadFile("config.yaml")

// ✗ Bad — only checking in some branches
result, err := doSomething()
fmt.Println(result) // using result without checking err

// ✓ Good — always check before using other return values
data, err := os.ReadFile("config.yaml")
if err != nil {
    return fmt.Errorf("reading config: %w", err)
}
```

## Error String Conventions

Error strings MUST be lowercase, no trailing punctuation. Should not duplicate context that wrapping adds.

```go
// ✗ Bad — capitalized, punctuation, redundant prefix
return errors.New("Failed to connect to database.")
return fmt.Errorf("UserService: failed to fetch user: %w", err)

// ✓ Good — lowercase, no punctuation, concise
return errors.New("connection refused")
return fmt.Errorf("fetching user: %w", err)
```

Each wrapping layer adds own prefix. Result reads like chain:

```
creating order: charging card: connecting to payment gateway: connection refused
```

## Creating Errors

### `errors.New` — static error messages

```go
var ErrNotFound = errors.New("not found")
var ErrUnauthorized = errors.New("unauthorized")
```

### `fmt.Errorf` — dynamic error messages

```go
import "github.com/samber/oops"

// ✗ Avoid at log/APM boundaries — each user/tenant combo becomes a unique group
return fmt.Errorf("user %s not found in tenant %s", userID, tenantID)

// ✓ Prefer for grouped production errors — static message, variable data as structured attributes
return oops.With("user_id", userID).With("tenant_id", tenantID).Errorf("user not found")
```

Why: see [Low-Cardinality Error Messages](#low-cardinality-error-messages).

### Decision table: which error strategy to use

| Situation | Strategy | Example |
| --- | --- | --- |
| Caller matches specific condition | Sentinel error (`errors.New` as package var) | `var ErrNotFound = errors.New("not found")` |
| Caller extracts structured data | Custom error type | `type ValidationError struct { Field, Msg string }` |
| Purely informational, not matched on | `fmt.Errorf` or `errors.New` | `fmt.Errorf("connecting to %s: %w", addr, err)` |
| Need stack traces, user context, structured attrs | `samber/oops` | See [Why Use samber/oops](./error-handling.md#why-use-samberoops) |

## Low-Cardinality Error Messages

APM and log aggregation tools (Datadog, Loki, Sentry) commonly group events by logged message or exception fingerprint. Variable data in stable log message can make each unique combination its own group: noisy dashboards, broken alerting.

```go
import "github.com/samber/oops"

// ✗ Bad at the log boundary — each file/line combo can create a unique group
fmt.Errorf("error in %s at line %d of the csv", csvPath, line)

// ✓ Good (stdlib) — static error, structured attributes at the log site
err := errors.New("csv parsing error")
// ... later, at the logging boundary:
slog.Error("csv parsing failed", "error", err, "csv_file_path", csvPath, "csv_file_line", line)

// ✓ Good (samber/oops, external dependency) — attributes travel with the error
oops.With("csv_file_path", csvPath).With("csv_file_line", line).Errorf("csv parsing error")
```

Stdlib approach works but scatters context: error travels up stack, and logging handler may lose access to variable data. `samber/oops` (external dependency `github.com/samber/oops`) attaches structured attributes to error itself, available wherever error gets logged.

**Static wrapping prefixes are fine** — `fmt.Errorf("fetching user: %w", err)` is low-cardinality: prefix never changes. Dynamic context in returned errors can help CLI output or debugging. Production logging should keep grouping message stable; put IDs, paths, counts, other variable data in structured attributes.

## Custom Error Types

Create custom error types when callers need to extract structured data.

```go
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed on %s: %s", e.Field, e.Message)
}

// Usage
func validateAge(age int) error {
    if age < 0 {
        return &ValidationError{Field: "age", Message: "must be non-negative"}
    }
    return nil
}
```

### Custom types that wrap other errors

Implement `Unwrap()` so `errors.Is` and `errors.As` can traverse chain:

```go
type QueryError struct {
    Query string
    Err   error
}

func (e *QueryError) Error() string {
    return fmt.Sprintf("query %q: %v", e.Query, e.Err)
}

func (e *QueryError) Unwrap() error {
    return e.Err
}
```
