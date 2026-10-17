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

`TaskEither<E, A>` is a lazy `() => Promise<Either<E, A>>`. It never rejects; failures travel in `Left`, so the compiler tracks them through every step. This skill is about the *shape of async flows*: ordering, concurrency, retries and recovery. How to design the error types (`_tag` unions, validation, converting throwing code) lives in fp-errors.

> fp-ts is in maintenance mode and its authors recommend Effect for new projects. Use this skill when the codebase already uses fp-ts; for Effect use effect-core-patterns and effect-concurrency.

## Procedure

1. **Wrap at the boundary, once.** Turn each Promise API into a function returning `TaskEither` with `TE.tryCatch(() => call(), toDomainError)` (or `TE.tryCatchK`). Always pass a thunk so nothing starts early.
2. **Decide ordering per step** with the table below.
3. **Compose with `flatMap`.** `TE.flatMap` sequences dependent calls and unions error types. `chain`/`chainW` are legacy aliases (fp-ts 2.14+); write `flatMap`, `tap`, `flatMapEither` in new code.
4. **Recover deliberately.** Use `TE.orElse` for alternatives, retry only idempotent operations, and recover only from errors you can handle.
5. **Run at the edge.** Call the task (`await program()`) in the HTTP handler, CLI `main`, or job runner, then `match`/`fold` into a response.

## Sequential vs parallel

| Situation | Use |
|---|---|
| Step needs the previous result | `TE.flatMap`, or `TE.Do` + `TE.bind` to keep earlier values |
| Independent calls, all required | `TE.Do` + `TE.apS` (uses `ApplyPar`), or `sequenceT(TE.ApplyPar)(a, b, c)` |
| Same call over a list, unbounded | `TE.traverseArray(f)` (parallel, fails with the first `Left` in array order) |
| Same call over a list, rate-limited or ordered | `TE.traverseSeqArray(f)` |
| Bounded concurrency | Chunk the list, `traverseSeqArray` over chunks, `traverseArray` inside each chunk |
| Keep successes and failures | `T.traverseArray(f)` (each item is an `Either`), then `A.separate` |

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

Retry only operations that are safe to repeat (GET, idempotent writes with an idempotency key). Add jitter and a cap for production backoff, or use a library (`retry-ts` builds on fp-ts) instead of growing this helper.

## References

- [references/detailed-guide.md](references/detailed-guide.md) - read the section you need: 1 wrapping Promises, 2 chaining and Do notation, 3 parallel vs sequential and batching, 4 recovery (typed recovery, backoff, defaults), 5 handling results in Express/Hono handlers, 6 common patterns and a quick reference card.
- [references/real-api-examples.md](references/real-api-examples.md) - complete fetch client, Prisma repository and Node file I/O wrappers; read when building one of those layers.
- Related skills: fp-taskeither-ref (operator lookup), fp-errors (error modeling), fp-backend (ReaderTaskEither services and DI).

## Pitfalls

- Forgetting to invoke the task: `program` does nothing, `program()` runs it.
- `TE.tryCatch(promise, ...)` with an already-created Promise: the work started before the pipeline and retries reuse the same settled Promise.
- `throw` inside `TE.map` escapes as a rejected Promise; use `flatMap` + `tryCatch` for code that can throw.
- `sequenceT(TE.ApplyPar)` for steps that depend on each other's side effects (create user, then profile): use `flatMap`.
- Mixing `await` inside pipelines: keep `async` only inside `tryCatch` thunks.

## Done when

- Every Promise boundary is wrapped once with a domain error mapper; no `try/catch` inside pipelines.
- Ordering choices are explicit (`flatMap`/`bind` vs `apS`/`traverseArray`) and match data dependencies.
- Retries apply only to retryable, idempotent operations and are bounded.
- Tests cover a success path and each `Left` tag the handler maps to a response.
