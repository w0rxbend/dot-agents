---
name: fp-either-ref
description: "fp-ts cheat sheet: Either operators for synchronous typed errors - create, transform, chain with flatMap, accumulate validation errors, extract. Use for a quick lookup while writing fp-ts code; not for Effect (use effect-error-handling), and see fp-errors for the full error-handling approach."
risk: none
source: community
date_added: "2026-09-04"
version: 1.1.0
tags: [fp-ts, either, error-handling, validation, quick-reference]
---

# Either Quick Reference (fp-ts 2.x)

`Either<E, A>` is `Left<E>` (failure) or `Right<A>` (success). Use it when a synchronous operation can fail and the caller needs to know why. For async work use `TaskEither` (fp-taskeither-ref); for "missing, no reason needed" use `Option` (fp-option-ref).

`chain`/`chainW` are legacy aliases of `flatMap` (fp-ts 2.14+). Write `flatMap`; it already unions error types.

## Create

```typescript
import * as E from 'fp-ts/Either'

E.right(42)                                   // Right(42)
E.left('not found')                           // Left('not found')
E.fromNullable('missing')(maybeValue)         // null/undefined -> Left
E.fromPredicate((n: number) => n > 0, (n) => `${n} is not positive`)(x)
E.tryCatch(() => JSON.parse(raw), E.toError)  // throwing code -> Either<Error, unknown>
```

## Transform and chain

| Operator | Use when |
|---|---|
| `E.map(f)` | `f` cannot fail |
| `E.mapLeft(f)` | Reshape or add context to the error |
| `E.flatMap(f)` | `f` returns an `Either`; stops at the first `Left`, error types are unioned |
| `E.tap(f)` | Run a fallible check but keep the original value |
| `E.filterOrElse(pred, onFalse)` | Turn a `Right` into a `Left` when a predicate fails |
| `E.orElse(f)` | Recover from a `Left` with another `Either` |
| `E.Do`, `E.bind`/`E.bindW`, `E.apS`/`E.apSW` | Build an object from several results (`W` = widen error type; `flatMap` widens by default) |

## Extract (only at the edge)

```typescript
E.getOrElse((err: string) => fallback)(result) // A
E.match(onLeft, onRight)(result)               // handle both cases
E.isLeft(result) / E.isRight(result)           // type guards for if/else code
```

## Common patterns

```typescript
import { pipe } from 'fp-ts/function'
import * as E from 'fp-ts/Either'

type InvalidEmail = { _tag: 'InvalidEmail' }
type TooYoung = { _tag: 'TooYoung'; age: number }

const validateEmail = (s: string): E.Either<InvalidEmail, string> =>
  s.includes('@') ? E.right(s) : E.left({ _tag: 'InvalidEmail' })

const validateAge = (n: number): E.Either<TooYoung, number> =>
  n >= 18 ? E.right(n) : E.left({ _tag: 'TooYoung', age: n })

// Fail fast: first error wins, error type is InvalidEmail | TooYoung
const signup = (email: string, age: number) =>
  pipe(
    E.Do,
    E.apS('email', validateEmail(email)),
    E.apSW('age', validateAge(age)) // apS needs one error type; apSW/bindW widen it
  )

// Collect every error (forms): accumulate into a NonEmptyArray
import { sequenceS } from 'fp-ts/Apply'
import * as NEA from 'fp-ts/NonEmptyArray'

const V = E.getApplicativeValidation(NEA.getSemigroup<string>())
const lift = <A>(e: E.Either<string, A>) => pipe(e, E.mapLeft(NEA.of))

const signupAll = (email: string, age: number) =>
  sequenceS(V)({
    email: lift(email.includes('@') ? E.right(email) : E.left('email: missing @')),
    age: lift(age >= 18 ? E.right(age) : E.left('age: must be 18+')),
  }) // Either<NonEmptyArray<string>, { email: string; age: number }>
```

## Decide

- Only absence matters, no reason: `Option`.
- One error is enough: `flatMap` / `Do` + `apS`.
- User needs every error at once: `getApplicativeValidation` + `sequenceS`.
- Plain `if (!x) return` code is clearer for a two-line function: keep it (see fp-refactor, "When NOT to refactor").

Full patterns, typed error unions and real scenarios: fp-errors.
