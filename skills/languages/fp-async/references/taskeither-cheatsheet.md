# TaskEither Quick Reference (fp-ts 2.x)

`TaskEither<E, A>` is `() => Promise<Either<E, A>>`: lazy async computation that never rejects; failure lives in `Left`.

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
| `TE.mapLeft(f)` | Reshape or annotate error |
| `TE.flatMap(f)` | `f` returns `TaskEither` (sequential; error types unioned) |
| `TE.flatMapEither(f)` | `f` returns sync `Either` (validation step) |
| `TE.tap(f)` | Side effect that can fail; keep original value |
| `TE.tapError(f)` | Log/observe failure; keep original error |
| `TE.orElse(f)` | Recover from `Left` with another `TaskEither` |
| `TE.Do`, `TE.bind`/`TE.bindW`, `TE.apS`/`TE.apSW` | Build context from several steps (`W` variants union differing error types) |

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

- Forgetting final `()`: nothing runs.
- `TE.getOrElse` expects function returning `Task`, not plain value.
- `TE.tryCatch(() => promise, ...)`: pass thunk. Creating Promise outside starts it eagerly and loses laziness.
- `throw` inside `TE.map` is not caught. Use `flatMap` + `tryCatch` for code that can throw.

Full pipelines, retries and batching: [the fp-async skill](../SKILL.md) and [detailed-guide.md](detailed-guide.md). Error modeling: fp-errors.
