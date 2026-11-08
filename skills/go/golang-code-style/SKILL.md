---
name: golang-code-style
description: "Write or review Go declarations, control flow, formatting, and comments for clarity. Follow existing repository style and formatter configuration; avoid unrelated cosmetic rewrites."
user-invocable: true
license: MIT
compatibility: Designed for Claude Code, Codex or similar harness, and for projects using Golang.
metadata:
  author: samber
  version: "1.3.0"
  openclaw:
    emoji: "🎨"
    homepage: https://github.com/samber/cc-skills-golang
    requires:
      bins:
        - go
    install: []
allowed-tools: Read Edit Write Glob Grep Bash(gofmt:*) Bash(go build:*) Bash(go vet:*) Bash(golangci-lint run:*) Bash(git status:*) Bash(git diff:*) Bash(git log:*) Bash(git show:*) Agent
paths:
  - "**/*.go"
---

> **Community default.** Company skill explicitly superseding `samber/cc-skills-golang@golang-code-style` skill wins.

# Go Code Style

Style rules needing human judgment. Linters handle formatting; this skill handles clarity.

> "Clear is better than clever." — Go Proverbs

When ignoring a rule, add a code comment.

## Line Length & Breaking

No rigid limit, but lines over ~120 characters MUST break, at **semantic boundaries**, not arbitrary columns. Calls with 4+ arguments SHOULD go one argument per line when otherwise long and repository already formats them so. If user explicitly asks for single-line code, comply:

```go
// Good — each argument on its own line, closing paren separate
mux.HandleFunc("/api/users", func(w http.ResponseWriter, r *http.Request) {
    handleUsers(
        w,
        r,
        serviceName,
        cfg,
        logger,
        authMiddleware,
    )
})
```

Signature too long: real fix often **fewer parameters** (options struct), not better wrapping. Multi-line signatures: one parameter per line.

## Variable Declarations

SHOULD use `:=` for non-zero values, `var` for zero-value initialization. Form signals intent: `var` means "this starts at zero."

```go
var count int              // zero value, set later
name := "default"          // non-zero, := is appropriate
var buf bytes.Buffer       // zero value is ready to use
```

### Slice & Map Initialization

Initialize maps before writes; nil maps panic on write. Nil slice (`var s []T`) is idiomatic zero value; `len`, `append` and `range` work on it (Go Code Review Comments prefers it). Initialize slices explicitly (`[]T{}` or `make`) where difference is observable: JSON encoding (nil encodes as `null`, empty as `[]`), APIs whose callers distinguish nil from empty, or existing repository practice.

```go
var users []User                        // nil slice: fine for internal use
users := []User{}                       // empty, encodes as [] in JSON
m := map[string]int{}                   // maps must be initialized before writes
users := make([]User, 0, len(ids))      // preallocate when capacity is known
m := make(map[string]int, len(items))   // preallocate when size is known
```

Do not preallocate speculatively: `make([]T, 0, 1000)` wastes memory when common case is 10 items.

### Composite Literals

Composite literals MUST use field names — positional fields break when type adds or reorders fields:

```go
srv := &http.Server{
    Addr:         ":8080",
    ReadTimeout:  5 * time.Second,
    WriteTimeout: 10 * time.Second,
}
```

## Control Flow

### Reduce Nesting

MUST handle errors and edge cases first (early return). Happy path stays at minimal indentation:

```go
func process(data []byte) (*Result, error) {
    if len(data) == 0 {
        return nil, errors.New("empty data")
    }

    parsed, err := parse(data)
    if err != nil {
        return nil, fmt.Errorf("parsing: %w", err)
    }

    return transform(parsed), nil
}
```

### Eliminate Unnecessary `else`

If `if` body ends with `return`/`break`/`continue`, MUST drop `else`. Simple assignments: default-then-override (assign default, override via independent conditions or `switch`):

```go
// Good — default-then-override with switch (cleanest for mutually exclusive overrides)
level := slog.LevelInfo
switch {
case debug:
    level = slog.LevelDebug
case verbose:
    level = slog.LevelWarn
}

// Bad — else-if chain hides that there's a default
if debug {
    level = slog.LevelDebug
} else if verbose {
    level = slog.LevelWarn
} else {
    level = slog.LevelInfo
}
```

### Complex Conditions & Init Scope

`if` with 3+ operands: MUST extract named booleans. Wall of `||` is unreadable, hides business logic. Keep expensive checks inline (short-circuit). [Details](./references/details.md)

```go
// Good — named booleans make intent clear
isAdmin := user.Role == RoleAdmin
isOwner := resource.OwnerID == user.ID
isPublicVerified := resource.IsPublic && user.IsVerified
if isAdmin || isOwner || isPublicVerified || permissions.Contains(PermOverride) {
    allow()
}
```

Scope variables to `if` when only check needs them:

```go
if err := validate(input); err != nil {
    return err
}
```

### Switch Over If-Else Chains

Same variable compared repeatedly: prefer `switch`:

```go
switch status {
case StatusActive:
    activate()
case StatusInactive:
    deactivate()
default:
    panic(fmt.Sprintf("unexpected status: %d", status))
}
```

## Function Design

- Functions SHOULD be **short and focused**: one function, one job.
- Functions SHOULD have **≤4 parameters**; beyond that, options struct (see `samber/cc-skills-golang@golang-design-patterns` skill).
- **Parameter order**: `context.Context` first, then inputs, then output destinations.
- Naked returns help in very short functions (1-3 lines) with obvious return values. Longer functions: name returns explicitly, else readers scroll to find what's returned.

```go
func FetchUser(ctx context.Context, id string) (*User, error)
func SendEmail(ctx context.Context, msg EmailMessage) error  // grouped into struct
```

### Prefer `range` for Iteration

SHOULD use `range` over index-based loops. `range n` (Go 1.22+) for simple counting.

```go
for _, user := range users {
    process(user)
}
```

## Value vs Pointer Arguments

Pass small types (`string`, `int`, `bool`, `time.Time`) by value. Pointers for mutation, large structs (~128+ bytes), or meaningful nil. [Details](./references/details.md)

## Code Organization Within Files

- **Group related declarations**: type, constructor, methods together
- **Order**: package doc, imports, constants, types, constructors, methods, helpers
- **One primary type per file** when it has significant methods
- **Blank imports** (`_ "pkg"`) register side effects (init functions). Restrict to `main` and test packages so side effects show at application root, not hidden in library code
- **Dot imports** pollute namespace and hide where a name comes from — never use in library code
- **Unexport aggressively** — can always export later; unexporting is a breaking change. Unexport safely with `samber/cc-skills-golang@golang-gopls` skill: its rename updates every call site atomically and refuses when lowercasing a method would break interface satisfaction, a breakage grep/sed silently ships.

## String Handling

Use `strconv` for simple conversions (faster), `fmt.Sprintf` for complex formatting. Use `%q` in error messages to show string boundaries. `strings.Builder` in loops, `+` for simple concatenation.

## Type Conversions

Prefer explicit, narrow conversions. Generics over `any` when concrete type will do:

```go
func Contains[T comparable](slice []T, target T) bool  // not []any
```

## Philosophy

- **"A little copying is better than a little dependency"**
- **Use `slices` and `maps` standard packages**; for filter/group-by/chunk, use `github.com/samber/lo`
- **"Reflection is never clear"** — avoid `reflect` unless necessary
- **Don't abstract prematurely** — extract once pattern is stable
- **Minimize public surface** — every exported name is a commitment

## Parallelizing Code Style Reviews

For large-codebase style review, use up to 5 parallel sub-agents, one per independent concern (e.g. control flow, function design, variable declarations, string handling, code organization); merge findings.

## Enforce with Linters

Linters enforce many rules: `gofmt`, `gofumpt`, `goimports`, `gocritic`, `revive`, `wsl_v5`. See `samber/cc-skills-golang@golang-lint` skill.

## Cross-References

- `samber/cc-skills-golang@golang-naming` skill: identifier naming conventions
- `samber/cc-skills-golang@golang-structs-interfaces` skill: pointer vs value receivers, interface design
- `samber/cc-skills-golang@golang-design-patterns` skill: functional options, builders, constructors
- `samber/cc-skills-golang@golang-continuous-integration` skill: automated AI-driven code review in CI using these guidelines
- `samber/cc-skills-golang@golang-refactoring` skill: mechanically, safely applying guard-clause conversion, function extraction and options-struct migration across many call sites once review finds violations at scale
