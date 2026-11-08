# Functional Programming and Monads in Go

## Table of Contents

- [What is Functional Programming?](#what-is-functional-programming)
- [What is a Monad?](#what-is-a-monad)
  - [The Railway Metaphor](#the-railway-metaphor)
- [Why Monads Are Valuable in Go](#why-monads-are-valuable-in-go)
  - [1. Compile-Time Nil Safety (Option)](#1-compile-time-nil-safety-option)
  - [2. Railway-Oriented Error Handling (Result)](#2-railway-oriented-error-handling-result)
  - [3. Composable Pipelines](#3-composable-pipelines)
- [The Three Core Monads](#the-three-core-monads)
  - [Option — Represents Absence](#option--represents-absence)
  - [Result — Represents Fallibility](#result--represents-fallibility)
  - [Either — Represents Alternatives](#either--represents-alternatives)
- [When to Use mo vs Plain Go](#when-to-use-mo-vs-plain-go)

## What is Functional Programming?

Functional programming (FP) treats computation as evaluation of mathematical functions. Core principles:

- **Immutability** — data does not change after creation. Transformations produce new values.
- **Pure functions** — same input always gives same output, no side effects
- **Composition** — build complex behavior by chaining simple functions
- **Types as documentation** — types express constraints and invariants

Go is not a pure FP language, but Go 1.18+ generics make FP patterns practical.

## What is a Monad?

Monad: design pattern (not class or interface) that:

1. **Wraps a value** in context (Option wraps "maybe absent", Result wraps "maybe failed")
2. **Chains operations** that transform wrapped value without unwrapping it
3. **Handles the context automatically**: if Option is None, Map/FlatMap skip transformation. If Result is Err, subsequent Maps short-circuit.

### The Railway Metaphor

Two parallel railway tracks:

- **Happy track** (top): data flows through transformations successfully
- **Error track** (bottom): once something goes wrong, train switches to error track and skips remaining transformations

```
Input → [Transform A] → [Transform B] → [Transform C] → Output
          ↓ (error)       (skipped)       (skipped)
       Error track ────────────────────────────────────→ Error
```

Result.Map and Result.FlatMap work exactly this way: errors propagate automatically without explicit if/else checks.

## Why Monads Are Valuable in Go

### 1. Compile-Time Nil Safety (Option)

Go's type system does not distinguish "this pointer could be nil" from "this pointer is always valid". Option[T] makes this explicit:

```go
// Without mo — caller must remember to check nil
func FindUser(id string) *User { ... }  // might return nil

// With mo — the type TELLS you it might be absent
func FindUser(id string) mo.Option[User] { ... }  // caller must handle None
```

Type signature is documentation. No nil pointer panics at runtime: compiler forces you to handle absence.

### 2. Railway-Oriented Error Handling (Result)

Idiomatic Go checks errors at every step:

```go
// Without mo — repetitive error checking
data, err := readFile(path)
if err != nil { return err }
config, err := parseConfig(data)
if err != nil { return err }
validated, err := validate(config)
if err != nil { return err }
```

With Result and `mo.Do`, errors short-circuit through chain:

```go
// With mo — errors propagate automatically via Do notation
result := mo.Do(func() Config {
    data := mo.TupleToResult(readFile(path)).MustGet()
    config := mo.TupleToResult(parseConfig(data)).MustGet()
    validated := mo.TupleToResult(validate(config)).MustGet()
    return validated
})
```

Monad handles error path: any `MustGet()` failure short-circuits to `Err`.

**Note:** direct `.Map`/`.FlatMap` methods cannot change type parameter (Go methods cannot introduce new generic types). For type-changing pipelines, use sub-package `result.Pipe` functions or `mo.Do` notation as shown above.

### 3. Composable Pipelines

Monads compose naturally. Build complex data transformations from simple, testable pieces:

```go
import "github.com/samber/mo/option"

result := option.Pipe3(
    getUserOption(id),
    option.Map(func(u User) string { return u.Email }),
    option.FlatMap(func(email string) mo.Option[string] {
        if isValid(email) { return mo.Some(email) }
        return mo.None[string]()
    }),
    option.Map(func(email string) EmailAddress { return NewEmailAddress(email) }),
)
```

Each step: pure function, independently testable. Pipeline handles None propagation.

## The Three Core Monads

### Option — Represents Absence

**Problem it solves:** nil pointer panics, ambiguous zero values.

| Concept       | Go without mo         | Go with mo                |
| ------------- | --------------------- | ------------------------- |
| Value present | `*User` (non-nil)     | `mo.Some(user)`           |
| Value absent  | `*User` (nil)         | `mo.None[User]()`         |
| Safe access   | `if u != nil { ... }` | `opt.OrElse(defaultUser)` |
| Transform     | manual nil check      | `opt.Map(transform)`      |

Use Option when: value might legitimately be absent (nullable DB columns, optional config, cache lookups).

Don't use Option when: zero value is meaningful (empty string is valid, 0 is valid count).

### Result — Represents Fallibility

**Problem it solves:** verbose error checking, lost error context in chains.

| Concept   | Go without mo                | Go with mo                    |
| --------- | ---------------------------- | ----------------------------- |
| Success   | `return value, nil`          | `mo.Ok(value)`                |
| Failure   | `return zero, err`           | `mo.Err[T](err)`              |
| Chain ops | `if err != nil` at each step | `.Map(...)` / `.FlatMap(...)` |
| Default   | manual fallback              | `.OrElse(default)`            |

Use Result when: chaining multiple fallible operations and wanting errors to propagate automatically.

Don't use Result when: you need to inspect or modify error at each step (standard Go error handling is more explicit).

### Either — Represents Alternatives

**Problem it solves:** functions that legitimately return one of two types.

| Concept                | Example                           |
| ---------------------- | --------------------------------- |
| Cached vs fresh data   | `Either[CachedUser, FreshUser]`   |
| Sync vs async result   | `Either[SyncResult, AsyncResult]` |
| Left vs right strategy | `Either[StrategyA, StrategyB]`    |

Use Either when: both outcomes are valid, neither is an "error". If one side is always an error, use Result instead.

## When to Use mo vs Plain Go

**Use mo when:**

- Building data transformation pipelines with multiple steps
- Needing type-safe nullable values (especially in JSON/DB models)
- Error handling chains become repetitive
- Making impossible states unrepresentable in type system

**Stick with plain Go when:**

- Simple one-step operations where `if err != nil` is clear enough
- Performance-critical hot paths (monads add thin allocation overhead)
- Team not familiar with FP concepts (readability over cleverness)
- Operation has complex error recovery at each step (explicit handling is clearer)
