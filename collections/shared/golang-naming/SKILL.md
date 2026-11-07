---
name: golang-naming
description: "Choose Go package, type, interface, method, and variable names for readable APIs. Preserve published identities and established repository conventions; renaming existing code also needs refactoring safeguards."
user-invocable: true
license: MIT
compatibility: Designed for Claude Code, Codex or similar harness, and for projects using Golang.
metadata:
  author: samber
  version: "1.2.1"
  openclaw:
    emoji: "🏷"
    homepage: https://github.com/samber/cc-skills-golang
    requires:
      bins:
        - go
    install: []
allowed-tools: Read Edit Write Glob Grep Bash(go build:*) Bash(go test:*) Bash(go vet:*) Bash(golangci-lint run:*) Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git show:*) Agent
paths:
  - "**/*.go"
---

> **Community default.** Company skill explicitly superseding `samber/cc-skills-golang@golang-naming` takes precedence.

# Go Naming Conventions

> "Clear is better than clever." — Go Proverbs
>
> "Design the architecture, name the components, document the details." — Go Proverbs

To ignore a rule, add code comment.

## Quick Reference

| Element | Convention | Example |
| --- | --- | --- |
| Package | lowercase, single word, \_test suffix OK for test files | `json`, `http`, `tabwriter`, `http_test` |
| File | lowercase, underscores OK | `user_handler.go` |
| Exported name | UpperCamelCase | `ReadAll`, `HTTPClient` |
| Unexported | lowerCamelCase | `parseToken`, `userCount` |
| Interface | method name + `-er` | `Reader`, `Closer`, `Stringer` |
| Struct | MixedCaps noun | `Request`, `FileHeader` |
| Constant | MixedCaps (not ALL_CAPS) | `MaxRetries`, `defaultTimeout` |
| Receiver | 1-2 letter abbreviation | `func (s *Server)`, `func (b *Buffer)` |
| Error variable | `Err` prefix | `ErrNotFound`, `ErrTimeout` |
| Error type | `Error` suffix | `PathError`, `SyntaxError` |
| Constructor | `New` (single type) or `NewTypeName` (multi-type) | `ring.New`, `http.NewRequest` |
| Boolean field | house style: `is`/`has`/`can` prefix (stdlib often uses bare names: `Closed`, `Valid`) | `isReady`, `IsConnected()` |
| Test function | `Test` + function name | `TestParseToken` |
| Acronym | all caps or all lower | `URL`, `HTTPServer`, `xmlParser` |
| Variant: context | `Context` suffix (stdlib style); `WithContext` also seen | `QueryContext`, `ExecContext` |
| Variant: in-place | no stdlib convention; in-place usually default (`slices.Sort`), copying variant gets name | `slices.Sort` (in place) vs `slices.Sorted` (returns new) |
| Variant: error | `Must` prefix | `MustParse()`, `MustLoadConfig()` |
| Option func | `With` + field name | `WithPort()`, `WithLogger()` |
| Enum (iota) | type name prefix, zero-value = unknown | `StatusUnknown` at 0, `StatusReady` |
| Named return | descriptive, docs only | `(n int, err error)` |
| Error string | not capitalized (initialisms keep case), no punctuation | `"image: unknown format"`, `"invalid ID"` |
| Import alias | short, only on collision | `mrand "math/rand"`, `pb "app/proto"` |
| Format func | `f` suffix | `Errorf`, `Wrapf`, `Logf` |
| Test table fields | `got`/`expected` prefixes | `input string`, `expected int` |

## MixedCaps

Capitalization controls visibility: uppercase is exported, lowercase unexported. All Go identifiers MUST use `MixedCaps` (or `mixedCaps`), NEVER underscores. Only exceptions: test function subcases (`TestFoo_InvalidInput`), generated code, OS/cgo interop.

```go
// ✓ Good
MaxPacketSize
userCount
parseHTTPResponse

// ✗ Bad — these conventions conflict with Go's export mechanism and tooling expectations
MAX_PACKET_SIZE   // C/Python style
max_packet_size   // snake_case
kMaxBufferSize    // Hungarian notation
```

## Avoid Stuttering

Name MUST NOT repeat what package name, type name, or surrounding context already says.

```go
// Good — clean at the call site
http.Client       // not http.HTTPClient
json.Decoder      // not json.JSONDecoder
user.New()        // not user.NewUser()
config.Parse()    // not config.ParseConfig()

// In package sqldb:
type Connection struct{}  // not DBConnection — "db" is already in the package name

// Anti-stutter applies to ALL exported types, not just the primary struct:
// In package dbpool:
type Pool struct{}        // not DBPool
type Status struct{}      // not PoolStatus — callers write dbpool.Status
type Option func(*Pool)   // not PoolOption
```

## Frequently Missed Conventions

**Constructor naming:** Package with single primary type: constructor is `New()`, not `NewTypeName()`. Use `NewTypeName()` only when package has multiple constructible types (like `http.NewRequest`, `http.NewServeMux`).

**Boolean struct fields (house style, not an official Go rule):** prefer `is`/`has`/`can` prefix on unexported boolean fields (`isConnected`, `hasPermission`). Exported getter keeps it: `IsConnected() bool`. Stdlib often uses bare names (`Closed`, `Valid`); follow codebase convention when it differs.

**Error strings start lowercase and have no trailing punctuation**: they often get concatenated with other context (`fmt.Errorf("parsing token: %w", err)`). Per Go Code Review Comments, proper nouns and initialisms keep case: `"invalid message ID"`, `"HTTP request failed"`. Sentinel errors should prefix package name: `errors.New("apiclient: not found")`.

**Enum zero values:** Always put explicit `Unknown`/`Invalid` sentinel at iota position 0. `var s Status` silently becomes 0. If 0 is real state like `StatusReady`, code can treat unset status as deliberate choice.

**Subtest names:** `t.Run()` table case names should be fully lowercase descriptive phrases: `"valid id"`, `"empty input"`, not `"valid ID"` or `"Valid Input"`.

## Detailed Categories

- **[Packages, Files & Import Aliasing](./references/packages-files.md)** — Package naming, file naming, import aliases, directory structure.

- **[Variables, Booleans, Receivers & Acronyms](./references/identifiers.md)** — Name length vs scope, receivers, acronym casing, boolean names.

- **[Functions, Methods & Options](./references/functions-methods.md)** — Getters without `Get`, constructors, named returns, format function suffixes, functional options.

- **[Types, Constants & Errors](./references/types-errors.md)** — Interfaces, structs, constants, enums, sentinel errors, error types, error messages.

- **[Test Naming](./references/testing.md)** — Test functions, table-driven fields, test helpers, subcases.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| `GetName()` getter | Drop `Get`: `user.Name()` reads naturally. Boolean predicates keep `Is`/`Has`/`Can`: `IsHealthy() bool` not `Healthy() bool` |
| `this` or `self` receiver | Methods get called often. Use 1-2 letter abbreviation (`s` for `Server`) to cut noise |
| `util`, `helper` packages | Say nothing about content. Use specific names describing the abstraction |
| `userSlice` type-in-name | Type leaks implementation detail. `users` says what it holds, not how |
| Inconsistent receiver names | Confuses readers. Use one name across all methods of a type |
| Long names for short scopes | Length should match scope. `i` fine for 3-line loop; `userIndex` is noise |
| Naming constants by value | Values change, roles don't. `DefaultPort` survives port change, `Port8080` doesn't |
| `FetchCtx()` context variant | Spell it out. Stdlib uses `Context` suffix (`QueryContext`, `DialContext`); `FetchWithContext()` also common |
| Ambiguous mutate vs copy | Document which one function does. Stdlib makes in-place default (`slices.Sort`) and names copying variant (`slices.Sorted`). `In` suffix is house convention, not Go's |
| `parse()` panicking on error | `MustParse()` warns callers failure panics. Surprises belong in name |
| Mixing `With*`, `Set*`, `Use*` | Stay consistent. `With*` is Go convention for functional options |
| Plural package names | Go uses singular (`net/url` not `net/urls`). Keeps import paths consistent |
| Inconsistent concept names | `user`/`account`/`person` for one concept forces readers to track synonyms. Pick one name |

Applying these fixes means renaming existing identifiers. Use `samber/cc-skills-golang@golang-gopls` skill to do it safely. Its rename updates every call site across workspace and refuses renames that would break interface satisfaction, which grep/sed or manual Edit-based renames silently miss.

## Enforce with Linters

Linters catch many naming issues automatically: `revive`, `predeclared`, `misspell`, `errname`. See `samber/cc-skills-golang@golang-lint` skill for configuration and usage.

## Cross-References

- → See `samber/cc-skills-golang@golang-code-style` skill for broader formatting and style
- → See `samber/cc-skills-golang@golang-structs-interfaces` skill for interface naming depth and receiver design
- → See `samber/cc-skills-golang@golang-refactoring` skill for safe renames at scale (gopls Rename/Inline, blast-radius mapping, staged PR workflow) once new names are chosen
