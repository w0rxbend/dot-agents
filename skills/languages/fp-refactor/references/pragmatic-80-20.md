# Pragmatic fp-ts: The 80/20

## The Golden Rule

> **If functional programming makes the code harder to read for the team that maintains it, don't use it.**

## The 80/20

Five tools cover most benefit. Introduce in this order; stop when code is clear:

1. `pipe` - read transformations top to bottom instead of nesting calls.
2. `Option` - replace chains of null checks that feed further logic (not one-off `?.`).
3. `Either` - make failures part of return type.
4. `map` - transform value inside `Option`/`Either`/`TaskEither` without unpacking it.
5. `flatMap` - sequence steps that can each miss or fail.

Everything else (Reader, Validation, Do notation, type classes) comes later, only when concrete problem needs it.

## Quick Wins: Easy Changes That Improve Code Today

### 1. Replace Nested Ternaries with pipe + fold

```typescript
// Before: Nested ternary nightmare
const message = user === null
  ? 'No user'
  : user.isAdmin
    ? `Admin: ${user.name}`
    : `User: ${user.name}`

// After: Clear case handling
const message = pipe(
  O.fromNullable(user),
  O.fold(
    () => 'No user',
    (u) => u.isAdmin ? `Admin: ${u.name}` : `User: ${u.name}`
  )
)
```

### 2. Replace try-catch with tryCatch

```typescript
// Before: try-catch everywhere
let config
try {
  config = JSON.parse(rawConfig)
} catch {
  config = defaultConfig
}

// After: One-liner
const config = pipe(
  E.tryCatch(() => JSON.parse(rawConfig), () => 'parse error'),
  E.getOrElse(() => defaultConfig)
)
```

### 3. Replace undefined Returns with Option

```typescript
// Before: Caller might forget to check
function findUser(id: string): User | undefined {
  return users.find(u => u.id === id)
}

// After: Type forces caller to handle missing case
function findUser(id: string): O.Option<User> {
  return O.fromNullable(users.find(u => u.id === id))
}
```

### 4. Replace Error Strings with Typed Errors

```typescript
// Before: Just strings
function validate(data: unknown): E.Either<string, User> {
  // ...
  return E.left('validation failed')
}

// After: Structured errors
type ValidationError = {
  field: string
  message: string
}

function validate(data: unknown): E.Either<ValidationError, User> {
  // ...
  return E.left({ field: 'email', message: 'Invalid format' })
}
```

### 5. Use const Assertions for Error Types

```typescript
// Create specific error types without classes
const NotFound = (id: string) => ({ _tag: 'NotFound' as const, id })
const Unauthorized = { _tag: 'Unauthorized' as const }
const ValidationFailed = (errors: string[]) =>
  ({ _tag: 'ValidationFailed' as const, errors })

type AppError =
  | ReturnType<typeof NotFound>
  | typeof Unauthorized
  | ReturnType<typeof ValidationFailed>

// Now you can pattern match
const handleError = (error: AppError): string => {
  switch (error._tag) {
    case 'NotFound': return `Item ${error.id} not found`
    case 'Unauthorized': return 'Please log in'
    case 'ValidationFailed': return error.errors.join(', ')
  }
}
```

## The Readability Rule

Before any FP pattern, ask: **"Would a junior developer understand this?"**

### Too Clever (Avoid)

Point-free style with Ramda-like helpers (`prop`, `equals`, `multiply`, `gt`):

```typescript
const result = pipe(
  data,
  A.filter(flow(prop('status'), equals('active'))),
  A.map(flow(prop('value'), multiply(2))),
  A.reduce(monoid.concat, monoid.empty),
  O.fromPredicate(gt(threshold))
)
```

### Just Right (Prefer)

```typescript
const activeItems = data.filter(item => item.status === 'active')
const doubledValues = activeItems.map(item => item.value * 2)
const total = doubledValues.reduce((sum, val) => sum + val, 0)
const result = total > threshold ? O.some(total) : O.none
```

### The Middle Ground (Often Best)

```typescript
const result = pipe(
  data,
  A.filter(item => item.status === 'active'),
  A.map(item => item.value * 2),
  A.reduce(0, (sum, val) => sum + val),
  total => total > threshold ? O.some(total) : O.none
)
```

## When Your Team Doesn't Know FP

Plain `async` function with `try/catch` returning `null` on failure is fine when nobody branches on failure reason. Introduce `TaskEither` at a boundary where typed errors pay for themselves (API client, repository). Add short example in PR description. Do not convert whole module at once.

## When to Level Up

Once comfortable with basics, explore:

1. **TaskEither** - async operations that can fail (replaces Promise + try/catch)
2. **Validation** - collect ALL errors instead of stopping at first
3. **Reader** - dependency injection without classes
4. **Do notation** - cleaner syntax for multiple bindings

Don't rush: basics handle 80% of real-world scenarios.
