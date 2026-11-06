---
name: fp-async
description: "fp-ts: build async pipelines with TaskEither - wrap Promises, sequence dependent calls, run independent calls in parallel or in batches, retry with backoff, fall back, and run the result in Express/Hono handlers. Use when composing async fp-ts code; not for Effect, and use fp-errors for modeling the error types themselves."
source: community
date_added: "2026-09-04"
version: 1.1.0
author: kadu
tags:
  - fp-ts
  - typescript
  - async
  - error-handling
  - practical
  - promises
  - api
  - fetch
---

# Async Pipelines with fp-ts TaskEither

`TaskEither<E, A>` is lazy `() => Promise<Either<E, A>>`. Never rejects. Failures travel in `Left`, so compiler tracks them through every step. This skill covers shape of async flows: ordering, concurrency, retries, recovery. Error type design (`_tag` unions, validation, converting throwing code) lives in fp-errors.

> fp-ts is in maintenance mode; its authors recommend Effect for new projects. Use this skill when codebase already uses fp-ts. For Effect use effect-core-patterns and effect-concurrency.

## Procedure

1. **Wrap at the boundary, once.** Each Promise API becomes function returning `TaskEither` via `TE.tryCatch(() => call(), toDomainError)` (or `TE.tryCatchK`). Always pass thunk so nothing starts early.
2. **Decide ordering per step** with table below.
3. **Compose with `flatMap`.** `TE.flatMap` sequences dependent calls, unions error types. `chain`/`chainW` are legacy aliases (fp-ts 2.14+). New code: `flatMap`, `tap`, `flatMapEither`.
4. **Recover deliberately.** `TE.orElse` for alternatives. Recover only from errors you can handle.
5. **Run at the edge.** Call task (`await program()`) in HTTP handler, CLI `main` or job runner, then `match`/`fold` into response.

## Sequential vs parallel

| Situation | Use |
|---|---|
| Step needs previous result | `TE.flatMap`, or `TE.Do` + `TE.bind` to keep earlier values |
| Independent calls, all required | `TE.Do` + `TE.apS` (uses `ApplyPar`), or `sequenceT(TE.ApplyPar)(a, b, c)` |
| Same call over list, unbounded | `TE.traverseArray(f)` (parallel, fails with first `Left` in array order) |
| Same call over list, rate-limited or ordered | `TE.traverseSeqArray(f)` |
| Bounded concurrency | Chunk list, `traverseSeqArray` over chunks, `traverseArray` inside each chunk |
| Keep successes and failures | `T.traverseArray(f)` (each item is `Either`), then `A.separate` |

```typescript
import { pipe } from 'fp-ts/function'
import * as A from 'fp-ts/Array'
import * as T from 'fp-ts/Task'
import * as TE from 'fp-ts/TaskEither'

// Dependent steps, keeping earlier values in scope
const checkout = (orderId: string) =>
  pipe(
    TE.Do,
    TE.bind('order', () => fetchOrder(orderId)),
    TE.bindW('user', ({ order }) => fetchUser(order.userId)),
    TE.flatMap(({ order, user }) => chargePayment(user, order.total))
  )

// Independent calls in parallel
const dashboard = (userId: string) =>
  pipe(
    TE.Do,
    TE.apS('user', fetchUser(userId)),
    TE.apS('notifications', fetchNotifications(userId))
  )

// Partial success: never short-circuits
const importAll = (ids: string[]) =>
  pipe(ids, T.traverseArray(fetchUser), T.map((results) => A.separate([...results])))
// Task<{ left: Error[]; right: User[] }>
```

## Retry and fallback

```typescript
const wait = (ms: number): T.Task<void> => () => new Promise((r) => setTimeout(r, ms))

const retry = <E, A>(
  task: TE.TaskEither<E, A>,
  attempts: number,
  delayMs: number,
  isRetryable: (e: E) => boolean = () => true
): TE.TaskEither<E, A> =>
  pipe(
    task,
    TE.orElse((e) =>
      attempts > 1 && isRetryable(e)
        ? pipe(TE.fromTask(wait(delayMs)), TE.flatMap(() => retry(task, attempts - 1, delayMs * 2, isRetryable)))
        : TE.left(e)
    )
  )

const getUser = (id: string) =>
  pipe(
    fetchUserFromCache(id),
    TE.orElse(() => retry(fetchUserFromApi(id), 3, 200)),
    TE.tapError((e) => TE.fromIO(() => console.error('getUser failed', e)))
  )
```

Retry only operations safe to repeat (GET, idempotent writes with idempotency key). Production backoff: add jitter and cap, or use library (`retry-ts` builds on fp-ts) instead of growing this helper.

## References

- [references/taskeither-cheatsheet.md](references/taskeither-cheatsheet.md) - one-page TaskEither operator cheat sheet (create, transform, sequential vs parallel, recover, run) for quick lookup.
- [references/detailed-guide.md](references/detailed-guide.md) - read section you need: 1 wrapping Promises, 2 chaining and Do notation, 3 parallel vs sequential and batching, 4 recovery (typed recovery, backoff, defaults), 5 handling results in Express/Hono handlers, 6 common patterns.
- [references/real-api-examples.md](references/real-api-examples.md) - complete fetch client, Prisma repository, Node file I/O wrappers. Read when building one of those layers.
- Related skills: fp-errors (error modeling), fp-backend (ReaderTaskEither services and DI).

## Pitfalls

- Forgetting to invoke task: `program` does nothing, `program()` runs it.
- `TE.tryCatch(promise, ...)` with already-created Promise: work started before pipeline, and retries reuse same settled Promise.
- `throw` inside `TE.map` escapes as rejected Promise. Use `flatMap` + `tryCatch` for code that can throw.
- `sequenceT(TE.ApplyPar)` for steps depending on each other's side effects (create user, then profile): use `flatMap`.
- Mixing `await` inside pipelines: keep `async` only inside `tryCatch` thunks.

## Done when

- Every Promise boundary wrapped once with domain error mapper. No `try/catch` inside pipelines.
- Ordering choices explicit (`flatMap`/`bind` vs `apS`/`traverseArray`) and match data dependencies.
- Retries bounded, applied only to retryable, idempotent operations.
- Tests cover success path and each `Left` tag the handler maps to a response.
