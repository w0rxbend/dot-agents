---
name: effect-concurrency
user-invocable: false
description: "Effect-TS v3: run effects concurrently with Effect.all/forEach concurrency options, fibers (fork, join, interrupt, forkScoped, forkDaemon), racing and timeouts, and coordinate them with Queue, Deferred, Semaphore, PubSub and request batching. Use when Effect code must do work in parallel, limit parallelism, run background workers or pass data between fibers."
allowed-tools:
  - Read
  - Write
  - Edit
---

# Effect Concurrency

> **Version:** targets `effect` 3.x (examples checked against 3.22). Effect 4
> renames `Effect.fork` to `Effect.forkChild`, among others. Check `effect` in
> package.json first.

Concurrency is *structured*: fiber forked with `Effect.fork` is interrupted
when parent finishes; interruption runs finalizers. Prefer high-level combinators.
Fork manually only for background work or custom coordination.

## Pick the primitive

| Need | Use |
| --- | --- |
| Run N independent effects, collect results | `Effect.all([...], { concurrency })` |
| Map collection with effect | `Effect.forEach(items, f, { concurrency })` |
| First success wins, cancel rest | `Effect.race`, `Effect.raceAll` |
| Deadline | `Effect.timeout`, `Effect.timeoutFail`, `Effect.timeoutTo` |
| Background work tied to scope | `Effect.forkScoped` (or `FiberSet`/`FiberMap` for many) |
| Background work outliving caller | `Effect.forkDaemon` (rarely right) |
| Producer/consumer, work queue, back-pressure | `Queue` |
| One-shot signal / promise between fibers | `Deferred` |
| Limit concurrent access (rate, connections) | `Semaphore` via `Effect.makeSemaphore` |
| Broadcast to many subscribers | `PubSub` |
| Shared mutable state | `Ref` / `SynchronizedRef` (effectful updates) |
| Batch and dedupe lookups (N+1) | `Request` + `RequestResolver` |

## Effect.all and forEach

Default is **sequential**. Set `concurrency` explicitly.

```typescript
import { Effect } from "effect"

declare const fetchUser: (id: string) => Effect.Effect<{ id: string }, Error>
const ids = Array.from({ length: 100 }, (_, i) => `${i}`)

const sequential = Effect.forEach(ids, fetchUser) // one at a time
const bounded = Effect.forEach(ids, fetchUser, { concurrency: 10 }) // max 10 in flight
const unbounded = Effect.all(ids.map(fetchUser), { concurrency: "unbounded" })

// Struct form keeps names; first failure interrupts the others
const page = Effect.all(
  { user: fetchUser("1"), friend: fetchUser("2") },
  { concurrency: 2 }
)

// Keep going on failure: per-item Either, or discard results
const settled = Effect.all(ids.map(fetchUser), { concurrency: 10, mode: "either" })
const fireAll = Effect.forEach(ids, fetchUser, { concurrency: 10, discard: true })
```

Use `concurrency: "inherit"` in library code so caller decides via
`Effect.withConcurrency(n)`.

## Fibers

```typescript
import { Effect, Fiber } from "effect"

const task = Effect.sleep("1 second").pipe(Effect.as(42))

const program = Effect.gen(function* () {
  const fiber = yield* Effect.fork(task) // child of this fiber
  yield* Effect.log("parent keeps working")
  const n = yield* Fiber.join(fiber) // waits; re-raises the child's failure
  const other = yield* Effect.fork(task)
  const exit = yield* Fiber.await(other) // Exit instead of re-raising
  return [n, exit] as const
})

const cancelLater = Effect.gen(function* () {
  const fiber = yield* Effect.fork(Effect.never)
  yield* Effect.sleep("100 millis")
  yield* Fiber.interrupt(fiber) // waits until the fiber's finalizers finished
})
```

| Fork variant | Lifetime |
| --- | --- |
| `Effect.fork` | interrupted when parent fiber ends |
| `Effect.forkScoped` | interrupted when enclosing `Scope` closes (use in `Layer.scoped` for background services) |
| `Effect.forkIn(scope)` | interrupted when given scope closes |
| `Effect.forkDaemon` | global; lives until done or program exits |

`FiberSet` / `FiberMap` (scoped fiber collections) fit
"start a fiber per connection/job and interrupt all on shutdown".

## Racing, timeouts, interruption

```typescript
import { Effect } from "effect"

declare const primary: Effect.Effect<string, Error>
declare const replica: Effect.Effect<string, Error>

const fastest = Effect.race(primary, replica) // loser is interrupted
const bounded = primary.pipe(Effect.timeout("2 seconds")) // fails with TimeoutException

// Critical section: cannot be interrupted midway
declare const debit: Effect.Effect<void>
declare const credit: Effect.Effect<void>
const transfer = Effect.uninterruptible(Effect.zipRight(debit, credit))

const logged = primary.pipe(Effect.onInterrupt(() => Effect.log("cancelled")))
```

`Effect.race` returns first *success*; fails only if both fail. Use
`Effect.raceFirst` when first completion (success or failure) should win.
Interrupting fiber blocked in `Effect.tryPromise` aborts `AbortSignal`
passed to `try`, so pass that signal to `fetch`.

## Queue: producer/consumer with back-pressure

```typescript
import { Effect, Queue } from "effect"

interface Job { readonly id: number }
declare const handle: (job: Job) => Effect.Effect<void>

const processAll = (jobs: ReadonlyArray<Job>) =>
  Effect.gen(function* () {
    const queue = yield* Queue.bounded<Job>(100) // offer suspends when full

    // Producer runs in the background; owned by the scope
    yield* Effect.forkScoped(Effect.forEach(jobs, (j) => Queue.offer(queue, j), { discard: true }))

    // 4 consumers drain exactly jobs.length items
    yield* Effect.forEach(jobs, () => Effect.flatMap(Queue.take(queue), handle), {
      concurrency: 4,
      discard: true
    })
  }).pipe(Effect.scoped)
```

For long-lived worker service, fork
`Effect.forever(Effect.flatMap(Queue.take(queue), handle))` with
`Effect.forkScoped` inside `Layer.scoped`, so workers stop on shutdown.
Do not fork workers then let scope close immediately: workers get
interrupted before taking anything.

| Constructor | When full |
| --- | --- |
| `Queue.bounded(n)` | `offer` waits (back-pressure) |
| `Queue.dropping(n)` | new items dropped, `offer` returns `false` |
| `Queue.sliding(n)` | oldest items dropped |
| `Queue.unbounded()` | never full (watch memory) |

`Queue.shutdown` interrupts waiting `take`/`offer` callers. For transforming
pipelines, `Stream.fromQueue` often beats manual loops.

## Deferred: one-shot handoff

```typescript
import { Deferred, Effect, Fiber } from "effect"

const handshake = Effect.gen(function* () {
  const ready = yield* Deferred.make<string, Error>()
  const waiter = yield* Effect.fork(
    Deferred.await(ready).pipe(Effect.flatMap((v) => Effect.log(`got ${v}`)))
  )
  yield* Effect.sleep("10 millis")
  yield* Deferred.succeed(ready, "go") // completes once; later completions return false
  yield* Fiber.join(waiter)
})
```

Use `Deferred` for "wait until initialized", request/response correlation, or
gating many fibers on one event. Reusable open/close gate: `Effect.makeLatch`.

## Semaphore: limit concurrent access

```typescript
import { Effect } from "effect"

declare const callApi: (i: number) => Effect.Effect<string>

const limited = Effect.gen(function* () {
  const sem = yield* Effect.makeSemaphore(3) // 3 permits
  // Even with unbounded concurrency, at most 3 calls run at once
  return yield* Effect.forEach(
    [1, 2, 3, 4, 5, 6],
    (i) => sem.withPermits(1)(callApi(i)),
    { concurrency: "unbounded" }
  )
})
```

Share one semaphore across call sites (put it in a service) to protect
resource globally. `concurrency: n` on single `forEach` limits only that call.
Semaphore with 1 permit is mutex.

## PubSub: broadcast

```typescript
import { Effect, PubSub, Queue } from "effect"

const broadcast = Effect.scoped(
  Effect.gen(function* () {
    const hub = yield* PubSub.bounded<string>(16)
    const a = yield* PubSub.subscribe(hub) // Dequeue; unsubscribed when the scope closes
    const b = yield* PubSub.subscribe(hub)
    yield* PubSub.publish(hub, "hello") // only subscribers that exist now receive it
    return [yield* Queue.take(a), yield* Queue.take(b)] as const
  })
)
```

Subscribe *before* publishing; messages published with no subscribers are
gone. `Stream.fromPubSub` turns hub into stream per consumer.

## Batching and deduplicating requests

```typescript
import { Effect, Request, RequestResolver } from "effect"

interface User { readonly id: string; readonly name: string }
interface GetUser extends Request.Request<User, Error> {
  readonly _tag: "GetUser"
  readonly id: string
}
const GetUser = Request.tagged<GetUser>("GetUser")

declare const fetchUsersByIds: (ids: ReadonlyArray<string>) => Effect.Effect<ReadonlyArray<User>>

const UserResolver = RequestResolver.makeBatched((reqs: ReadonlyArray<GetUser>) =>
  fetchUsersByIds(reqs.map((r) => r.id)).pipe(
    Effect.flatMap((users) =>
      Effect.forEach(reqs, (req) => {
        const u = users.find((x) => x.id === req.id)
        return u ? Request.succeed(req, u) : Request.fail(req, new Error(`no user ${req.id}`))
      }, { discard: true })
    )
  )
)

const getUser = (id: string) => Effect.request(GetUser({ id }), UserResolver)

// One fetchUsersByIds(["1","2"]) call: `batching: true` groups the requests,
// withRequestCaching(true) dedupes the repeated "1"
const users = Effect.forEach(["1", "2", "1"], getUser, {
  concurrency: "unbounded",
  batching: true
}).pipe(Effect.withRequestCaching(true))
```

Without `batching: true` (or `Effect.withRequestBatching(true)`), each request
runs as own batch. Resolver must complete every request, otherwise callers hang.

## Pitfalls

- Unbounded fan-out over user-controlled input: always cap with number.
- `forkDaemon` for request-scoped work: leaks past cancellation.
- Shared mutable JS variables across fibers: use `Ref`. For effectful
  read-modify-write, use `SynchronizedRef` or 1-permit semaphore.
- `while (true)` loops without yield point: use `Effect.forever` or
  `Effect.repeat` with `Schedule` so loop is interruptible.
- Interrupting just-forked fiber before it starts skips its body, including
  `ensuring`/`acquireRelease` inside it. Signal readiness with `Deferred`
  when order matters.
- Timing-based tests: use `TestClock` (see **effect-testing**).

## Done when

- Every parallel call site has explicit `concurrency`.
- Background fibers owned by scope (`forkScoped`, `FiberSet`, scoped
  layer) and stop on shutdown.
- Caller interruption cancels in-flight work (verified by test that
  interrupts and checks finalizers or `onInterrupt`).

## Related skills

- effect-resource-management - scopes owning fibers and resources
- effect-error-handling - timeouts and retries
- effect-testing - `TestClock`, testing interruption

Docs: <https://effect.website/docs/concurrency/basic-concurrency/>
