# Code Coverage

Use coverage as gap finder (read uncovered lines), not quality target.

## Commands

```bash
# Generate coverage file
go test -coverprofile=coverage.out ./...

# View coverage in HTML (uncovered lines in red)
go tool cover -html=coverage.out

# Coverage by function
go tool cover -func=coverage.out

# Total coverage percentage
go tool cover -func=coverage.out | grep total

# Count how many times each statement ran, not just whether it ran
go test -covermode=count -coverprofile=coverage.out ./...

# Safe under -race (atomic counters)
go test -race -covermode=atomic -coverprofile=coverage.out ./...

# Attribute coverage of package A to tests living in package B
go test -coverpkg=./... ./...

# Coverage of a single package, printed inline
go test -cover ./internal/store
```

## Modes

| Mode | Records | Use when |
| --- | --- | --- |
| `set` | Statement executed (default) | Normal runs |
| `count` | Execution count per statement | Finding never-taken branches in hot paths |
| `atomic` | Count, race-safe | Any run combined with `-race` or `t.Parallel()` |

## Pitfalls

- **Per-package by default.** Without `-coverpkg`, test in `api` exercising `store` reports nothing for `store`, so well-tested packages look untested.
- **Integration tests are invisible** unless build tag is passed: `go test -tags=integration -coverprofile=...`.
- **Generated code inflates the number.** Exclude it before setting any threshold, or metric measures generator.
- **A covered line is not an asserted line.** Test calling function and ignoring result reports 100% coverage, verifies nothing.

→ See `samber/cc-skills-golang@golang-continuous-integration` skill for wiring coverage reporting into CI.
