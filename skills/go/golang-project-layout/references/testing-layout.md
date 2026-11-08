# Tests, Benchmarks, and Examples

## Table of Contents

- [File Naming Conventions](#file-naming-conventions)
- [Where to Place Tests](#where-to-place-tests)
- [Test Package Options](#test-package-options)
- [Benchmarks](#benchmarks)
- [Examples](#examples)
- [Test Utilities](#test-utilities)
- [Test Fixtures](#test-fixtures)
- [Running Tests](#running-tests)
- [Test File Summary](#test-file-summary)

## File Naming Conventions

Go names test-related files by suffix:

| Suffix | Purpose | Build Tag |
| --- | --- | --- |
| `_test.go` | Tests | Not in normal builds |
| `_bench_test.go` | Benchmarks | Not in normal builds |
| `_example_test.go` | Examples that verify output | Not in normal builds |
| No suffix | Regular code | In all builds |

## Where to Place Tests

**Co-locate tests with code they test:**

```
internal/
├── handler/
│   ├── handler.go          # Production code
│   ├── handler_test.go     # Tests for handler
│   └── handler_bench_test.go  # Benchmarks (optional)
├── service/
│   ├── service.go
│   └── service_test.go
└── model/
    ├── user.go
    └── user_test.go

pkg/
└── logger/
    ├── logger.go
    └── logger_test.go
```

**Key principles:**

- Tests live in **same package** as code (e.g., `package handler`)

## Test Package Options

Two options for test package declaration:

**Option 1: Same package (white-box testing)**

```go
package handler  // Same package, can access unexported

import "testing"

func TestHandler(t *testing.T) {
    // Can access unexported functions and types
    internalFunction()
}
```

**Option 2: Package with `_test` suffix (black-box testing)**

```go
package handler_test  // Different package, only exported API

import "testing"

func TestHandler(t *testing.T) {
    // Can only access exported functions and types
    handler.PublicMethod()
}
```

**When to use each:**

- **Same package**: unit tests that need internals
- **`_test` suffix**: integration/behavioral tests

## Benchmarks

Benchmarks use `_bench_test.go` suffix and contain functions with `Benchmark` prefix.

## Examples

**In libraries**: use `*_example_test.go` files:

```
pkg/
└── logger/
    ├── logger.go
    ├── logger_test.go
    └── logger_example_test.go     # Examples
```

**Example function format:**

```go
package logger

import "fmt"

func ExampleLogger_Info() {
    log := New()
    log.Info("processing started")
    log.Info("processing complete")
    // Output:
    // INFO: processing started
    // INFO: processing complete
}
```

**Key points:**

- Example functions must start with `Example`
- `// Output:` comment verifies output
- Examples are runnable tests: `go test` fails if output doesn't match
- `godoc` displays examples as documentation
- File name format: `{package}_example_test.go` (e.g., `logger_example_test.go`)

**For executable examples** (standalone demo programs):

```
examples/
└── basic-usage/
    └── main.go                    # Executable example
```

## Test Utilities

Put shared test helpers in dedicated package:

```
test/
└── testutils/
    ├── mock.go
    └── fixtures.go
```

Or use `internal/testutil` pattern:

```
internal/
└── testutil/
    ├── mock.go
    └── fixtures.go
```

## Test Fixtures

Fixtures: test data files shared across tests. Pick one pattern:

**Option 1: Local testdata directory** (package-specific fixtures)

```
internal/
└── handler/
    ├── handler.go
    ├── handler_test.go
    └── testdata/
        ├── users.json
        ├── request_valid.json
        └── request_invalid.json
```

**Option 2: Global test directory** (shared across packages)

```
test/
└── fixtures/
    ├── users.json
    ├── products.json
    └── responses/
        ├── success.json
        └── error.json
```

**Option 3: Embedded fixtures** (Go 1.16+, use `//go:embed`)

```
internal/
└── handler/
    ├── handler.go
    ├── handler_test.go
    └── testdata/
        └── users.json
```

**Important notes:**

- Go ignores `testdata` when building regular packages
- Use `testdata/` for package-specific test data
- Use `test/fixtures/` for cross-package shared fixtures
- Don't put `.go` files in `testdata/`; they get ignored

## Running Tests

```bash
go test ./...                    # Run all tests
go test ./internal/handler       # Test specific package
go test -v ./...                 # Verbose output
go test -race ./...              # Race detection
go test -cover ./...             # Coverage report
go test -short ./...             # Skip long-running tests
```

## Test File Summary

| File Type | Suffix | Package | Purpose |
| --- | --- | --- | --- |
| Test | `*_test.go` | `package X` or `package X_test` | Unit/integration tests |
| Benchmark | `*_bench_test.go` | Same as code | Performance tests |
| Example (godoc) | `*_example_test.go` | Same as code | Documentation + verification |
| Executable example | No suffix | `package main` | Standalone demo programs |
| Test utilities | `*_test.go` | `package testutil` | Shared test helpers |
