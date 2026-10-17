---
name: fp-taskeither-ref
description: "fp-ts cheat sheet: TaskEither operators for async operations that can fail - wrap Promises, flatMap, run in parallel, recover, run at the edge. Use for a quick lookup while writing fp-ts code; not for Effect, and see fp-async for full async pipelines."
risk: none
source: community
date_added: "2026-09-04"
version: 1.1.0
tags: [fp-ts, taskeither, async, promise, error-handling, quick-reference]
---

# TaskEither Quick Reference (fp-ts 2.x)

`TaskEither<E, A>` is `() => Promise<Either<E, A>>`: a lazy async computation that never rejects; failure lives in `Left`. Nothing runs until you call it.

`chain`, `chainW`, `chainFirst`, `chainEitherK` are legacy names (fp-ts 2.14+). Use `flatMap`, `tap`, `flatMapEither`.

## Create

```typescript
import * as TE from 'fp-ts/TaskEither'

TE.right(value)
TE.left(error)
TE.tryCatch(() => fetch(url), E.toError)          // Promise -> TaskEither (rejection -> Left)
TE.tryCatchK(fetchJson, E.toError)                 // lift a Promise-returning function
TE.fromEither(either) / TE.fromOption(() => err)(opt)
```

## Transform

| Operator | Use when |
|---|---|
| `TE.map(f)` | `f` is sync and cannot fail |
| `TE.mapLeft(f)` | Reshape or annotate the error |
| `TE.flatMap(f)` | `f` returns a `TaskEither` (sequential; error types are unioned) |
| `TE.flatMapEither(f)` | `f` returns a sync `Either` (validation step) |
| `TE.tap(f)` | Side effect that can fail, keep the original value |
| `TE.tapError(f)` | Log/observe a failure, keep the original error |
| `TE.orElse(f)` | Recover from a `Left` with another `TaskEither` |
| `TE.Do`, `TE.bind`/`TE.bindW`, `TE.apS`/`TE.apSW` | Build up context from several steps (`W` variants union differing error types) |

## Sequential vs parallel

```typescript
import { pipe } from 'fp-ts/function'
import * as TE from 'fp-ts/TaskEither'

// Sequential: second call needs the first result
pipe(fetchUser('123'), TE.flatMap((user) => fetchPosts(user.id)))

// Independent calls: TE.apS uses ApplyPar, so both start together; any Left fails the result
pipe(
  TE.Do,
  TE.apS('user', fetchUser('1')),
  TE.apSW('posts', fetchPosts('1')) // apSW when the error types differ
)

// Need sequential independent steps (rate limits, ordering)? Use TE.bind instead of TE.apS

// Arrays
TE.traverseArray(fetchUser)(ids)     // parallel
TE.traverseSeqArray(fetchUser)(ids)  // one at a time
```

## Recover and run

```typescript
import * as T from 'fp-ts/Task'

pipe(fetchUser('123'), TE.orElse(() => fetchUserFromCache('123')))  // still a TaskEither
pipe(fetchUser('123'), TE.getOrElse(() => T.of(defaultUser)))        // Task<User>, error gone

const result = await fetchUser('123')()          // Either<E, User>
await pipe(fetchUser('123'), TE.match(onError, onUser))()
```

## Pitfalls

- Forgetting the final `()` - nothing runs.
- `TE.getOrElse` expects a function returning a `Task`, not a plain value.
- `TE.tryCatch(() => promise, ...)` - pass a thunk; creating the Promise outside starts it eagerly and loses laziness.
- `throw` inside `TE.map` is not caught; use `flatMap` + `tryCatch` for code that can throw.

Full pipelines, retries and batching: fp-async. Error modeling: fp-errors.
