# Nolint Directives

## Syntax

```go
//nolint:lintername // justification explaining why this suppression is needed
```

Put directive on flagged line or line directly above.

## Rules

1. **MUST specify linter name** — bare `//nolint` silences all linters on that line and hides what is suppressed
2. **MUST add justification comment**
3. **`nolintlint` enforces both rules** — flags bare `//nolint` and missing reasons
4. **MUST fix root cause before suppressing** — suppress only after confirming false positive or intentional pattern

## Examples

```go
// Specific linter with reason
//nolint:errcheck // fire-and-forget logging, error not actionable
_ = logger.Sync()

// Type assertion is safe because preceding type switch guarantees the type
v := x.(MyType) //nolint:forcetypeassert // guaranteed by type switch on line 42

// Orchestration function has inherent complexity
//nolint:gocyclo // orchestration function coordinating 8 subsystems
func orchestrate() error {

// Table-driven test with many cases
//nolint:funlen // table-driven test, length is proportional to case count
func TestParser(t *testing.T) {

// Intentional parallel structure is clearer than abstracting
//nolint:dupl // intentional parallel structure for readability
```

## Multiple Linters

Suppress several linters on one line, comma-separated:

```go
//nolint:errcheck,gosec // fire-and-forget in test helper
```

## When to Suppress vs. When to Fix

**Fix** (almost always):

- `errcheck` — check error, even if only logging it
- `govet` — usually real bugs
- `staticcheck` — deprecated APIs, logic errors
- `bodyclose`, `sqlclosecheck` — real resource leaks

**Suppress** (with justification):

- `funlen` — table-driven tests with many cases
- `gocyclo` — orchestration functions where splitting obscures flow
- `dupl` — intentional parallel structure clearer than abstraction
- `exhaustive` — default case intentionally handles remaining values
- `goconst` — constant would hurt clarity (e.g., test assertions)

**Never suppress without strong justification**:

- Security linters (`bodyclose`, `sqlclosecheck`, `rowserrcheck`) — catch real resource leaks
- `errcheck` on production code paths — unchecked errors cause silent failures
