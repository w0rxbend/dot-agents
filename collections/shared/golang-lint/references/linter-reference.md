# Linter Reference

golangci-lint v2 uses `.golangci.yml` with `version: "2"` at project root.

Key `.golangci.yml` sections:

- **`run`** — concurrency, timeout, test inclusion, directory exclusions
- **`linters.enable`** / **`linters.disable`** — active linters
- **`linters.settings`** — per-linter thresholds, options
- **`formatters`** — code formatters (gofmt, gofumpt)
- **`issues`** — output limits, exclusion rules

Add linter: put it in `linters.enable`, optionally configure in `linters.settings`.

Disable linter: move it to `linters.disable` with reason comment.

## Table of Contents

- [Linter Categories](#linter-categories)
  - [Correctness & Safety](#correctness--safety)
  - [Style & Readability](#style--readability)
  - [Complexity](#complexity)
  - [Performance](#performance)
  - [Security & Resources](#security--resources)
  - [Logging](#logging)
  - [Testing](#testing)
  - [Modernization & Meta](#modernization--meta)
  - [Formatting](#formatting)

## Linter Categories

[recommended .golangci.yml](../assets/.golangci.yml) enables all linters below, grouped by domain.

### Correctness & Safety

- **govet** — Go built-in checker: copylocks, printf format mismatches, struct tag validation, context stored in structs, unreachable code, nil dereferences
- **staticcheck** — broad static analysis: deprecated APIs, common mistakes, unnecessary code, simplifications, stdlib misuse
- **unused** — unused variables, functions, types, struct fields
- **errcheck** — unchecked error returns, including type assertions (configured with `check-type-assertions: true`)
- **nilerr** — returning nil error while `err` is non-nil (common silent-failure source)
- **forcetypeassert** — type assertions without comma-ok (`v := x.(T)` instead of `v, ok := x.(T)`)
- **copyloopvar** — loop variable copy issues (Go 1.22+)
- **errorlint** — correct `errors.Is`/`errors.As` use and `%w` wrapping (Go 1.13+)
- **durationcheck** — `time.Duration * time.Duration` multiplication bugs (e.g., `2 * time.Second * time.Minute` gives nanoseconds squared, not seconds)
- **reassign** — reassigned package-level variables outside `init()` (hides state mutations)

### Style & Readability

- **gocritic** — opinionated style: unnecessary conversions, range copies, append-assign patterns, redundant code
- **revive** — naming of exported types, unexported returns, receivers, errors, stuttered package names
- **wsl_v5** — whitespace and blank-line rules for visual grouping
- **whitespace** — trailing whitespace, unnecessary blank lines in function bodies
- **godot** — exported-symbol comments must end with period
- **misspell** — common English misspellings in identifiers, comments
- **predeclared** — shadowed Go built-in identifiers (e.g., variable named `len`, `cap`, `error`)
- **errname** — error naming: error types end in `Error` (e.g., `DecodeError`), error variables start with `Err` (e.g., `ErrNotFound`)
- **dupword** — duplicate words in comments and strings (e.g., "the the", "is is"), often copy-paste artifacts
- **asciicheck** — non-ASCII identifiers enabling homoglyph/trojan source attacks (identical look, different Unicode codepoints)

### Complexity

- **gocyclo** — cyclomatic complexity threshold (configured: 13). Split functions above it
- **nestif** — deeply nested if/else chains hurting readability
- **funlen** — function length limits (configured: 120 lines, 80 statements)
- **dupl** — duplicate code (configured: 100 token threshold)

### Performance

- **perfsprint** — faster alternatives to `fmt.Sprintf` (e.g., `strconv.Itoa` instead of `fmt.Sprintf("%d", n)`)
- **unconvert** — unnecessary type conversions (e.g., `int(x)` when `x` is already `int`)
- **ineffassign** — assignments never read afterward
- **goconst** — repeated string/number literals that should be constants (configured: min 3 chars, min 4 occurrences)

### Security & Resources

- **gosec** — security scanner: SQL injection, hardcoded credentials, weak crypto, path traversal, unsafe usage, 50+ other rules. Primary SAST tool in config. Never suppress without strong justification.
- **bidichk** — dangerous bidirectional Unicode sequences (CVE-2021-42574 trojan source attack: code looks safe, runs differently)
- **noctx** — HTTP requests sent without `context.Context` (no proper timeouts or cancellation)
- **containedctx** — `context.Context` in struct fields instead of parameter (anti-pattern per Go docs)
- **fatcontext** — `context.WithValue`/`WithCancel` in loops: unbounded context chains grow per iteration, leak memory
- **bodyclose** — unclosed HTTP response bodies (leak connections)
- **sqlclosecheck** — `sql.Rows` and `sql.Stmt` not closed after use
- **rowserrcheck** — `sql.Rows.Err()` not checked after iteration

### Logging

- **sloglint** — consistent `log/slog` style: key-value pairing, message formatting, level usage
- **loggercheck** — key-value formatting for structured loggers (zap, slog, logr): odd arg counts, missing keys

### Testing

- **thelper** — test helpers must call `t.Helper()` so failures report correct call site
- **paralleltest** — tests and subtests missing `t.Parallel()`
- **testifylint** — testify best practices (e.g., `assert.Equal(t, expected, actual)` over `assert.True(t, expected == actual)`)
- **usetesting** — `t.Setenv`/`t.TempDir` instead of `os.Setenv`/`os.MkdirTemp` in tests (automatic cleanup, isolation)

### Modernization & Meta

- **modernize** — code rewritable with newer Go features (requires golangci-lint v2.6.0+)
- **exptostd** — `golang.org/x/exp/` functions that now have stdlib equivalents (e.g., `slices`, `maps`, `cmp` packages added in Go 1.21)
- **intrange** — `range N` over C-style `for i := 0; i < N; i++` loops (Go 1.22+)
- **usestdlibvars** — stdlib constants instead of hardcoded strings/numbers (e.g., `http.MethodGet` instead of `"GET"`)
- **exhaustive** — enum switch statements must cover all values
- **nolintlint** — proper `//nolint` usage: linter name and justification comment required (configured with `require-explanation` and `require-specific`)

### Formatting

`golangci-lint fmt ./...` runs formatters:

- **gofmt** — standard Go formatter (canonical formatting)
- **gofumpt** — stricter formatter, extra rules (configured with `extra-rules: true`): consistent empty lines, grouped imports, simplified code patterns
