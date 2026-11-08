---
name: effect-resource-management
user-invocable: false
description: "Effect-TS v3: acquire and release resources safely with Scope, acquireRelease, addFinalizer, acquireUseRelease and ensuring, pool them with the Pool module, and tie them to application lifetime with Layer.scoped. Use when Effect code opens connections, files, sockets, subscriptions or background fibers that must be cleaned up on success, failure and interruption."
allowed-tools:
  - Read
  - Write
  - Edit
---

# Effect Resource Management

> **Version:** targets `effect` 3.x (examples checked against 3.22). Check
> `effect` in package.json; Effect 4 keeps `Scope`/`acquireRelease` but renames
> other nearby APIs.

`Scope` collects finalizers. When scope closes (success, failure or
interruption), finalizers run in reverse registration order. Effect needing a
scope has `Scope` in its `R` channel. `Effect.scoped` provides fresh scope and
closes it when inner effect ends.

## Choosing the tool

| Need | Use |
| --- | --- |
| Resource used inside one code block | `Effect.acquireUseRelease(acquire, use, release)` |
| Reusable "resource" effect callers compose and scope | `Effect.acquireRelease(acquire, release)` -> `Effect<A, E, Scope>` |
| Cleanup not tied to acquired value | `Effect.addFinalizer((exit) => ...)` |
| Always run something after effect (no resource) | `Effect.ensuring(cleanup)`, `Effect.onExit`, `Effect.onInterrupt` |
| Resource living as long as app / service | `Layer.scoped(Tag, acquireRelease(...))` (see **effect-dependency-injection**) |
| N interchangeable expensive resources | `Pool.make` / `Pool.makeWithTTL` |
| Background fiber that must stop with scope | `Effect.forkScoped` (see **effect-concurrency**) |

## acquireRelease + scoped

```typescript
import { Data, Effect } from "effect"
import * as fs from "node:fs/promises"

class FileError extends Data.TaggedError("FileError")<{ readonly cause: unknown }> {}

// A reusable resource: acquisition is uninterruptible, release always runs
const openFile = (path: string) =>
  Effect.acquireRelease(
    Effect.tryPromise({
      try: () => fs.open(path, "r"),
      catch: (cause) => new FileError({ cause })
    }),
    // release must not fail: swallow/log errors here
    (handle) => Effect.promise(() => handle.close()).pipe(Effect.ignore)
  )
// Effect<FileHandle, FileError, Scope>

const readFirstLine = (path: string) =>
  Effect.scoped(
    Effect.gen(function* () {
      const handle = yield* openFile(path)
      const text = yield* Effect.promise(() => handle.readFile({ encoding: "utf8" }))
      return text.split("\n")[0]
    })
  )
// Effect<string, FileError, never>; the file is closed before this returns
```

- Several resources in one scope release in reverse order (last acquired,
  first released).
- `release` gets `Exit` as second argument. Use it when cleanup differs on
  failure (for example roll back vs commit).

## acquireUseRelease (bracket)

```typescript
import { Effect } from "effect"

interface Tx { commit(): Promise<void>; rollback(): Promise<void>; run(sql: string): Promise<void> }
declare const begin: () => Promise<Tx>

const transfer = Effect.acquireUseRelease(
  Effect.promise(begin),
  (tx) => Effect.promise(() => tx.run("UPDATE accounts ...")),
  (tx, exit) =>
    exit._tag === "Success"
      ? Effect.promise(() => tx.commit())
      : Effect.promise(() => tx.rollback())
)
```

## Finalizers with exit information

```typescript
import { Effect, Exit, Cause } from "effect"

const tracked = Effect.gen(function* () {
  yield* Effect.addFinalizer((exit) =>
    Exit.isSuccess(exit)
      ? Effect.log("scope closed: success")
      : Cause.isInterruptedOnly(exit.cause)
        ? Effect.log("scope closed: interrupted")
        : Effect.logError("scope closed: failure", Cause.pretty(exit.cause))
  )
  return 42
})

const program = Effect.scoped(tracked)
```

`Exit` has only two cases, `Success` and `Failure`. Interruption is a
`Failure` whose cause is interruption. Detect it with
`Cause.isInterruptedOnly` / `Exit.isInterrupted`.

## Pooling with the Pool module

Do not hand-roll pools with `Queue`. `Pool` handles concurrent borrowers,
lazy growth, invalidation and shutdown.

```typescript
import { Effect, Pool } from "effect"

interface Conn { readonly id: number; query(sql: string): Promise<unknown[]>; close(): Promise<void> }
declare const connect: () => Promise<Conn>

// Each pool item is itself a scoped resource
const acquireConn = Effect.acquireRelease(
  Effect.promise(connect),
  (c) => Effect.promise(() => c.close())
)

const program = Effect.scoped(
  Effect.gen(function* () {
    // Fixed size; Pool.makeWithTTL({ acquire, min, max, timeToLive }) grows and shrinks
    const pool = yield* Pool.make({ acquire: acquireConn, size: 10 })

    // Borrow: Pool.get needs a Scope; the item returns to the pool when it closes
    const query = (sql: string) =>
      Effect.scoped(
        Effect.gen(function* () {
          const conn = yield* Pool.get(pool)
          return yield* Effect.promise(() => conn.query(sql))
        })
      )

    return yield* Effect.all([query("select 1"), query("select 2")], { concurrency: "unbounded" })
  })
)
// closing the outer scope closes every pooled connection
```

- `Pool.invalidate(pool, item)` drops broken item; pool replaces it.
- Put pool in `Layer.scoped` service so whole app shares one pool.
- Keyed resources (one pool per tenant/host): use `KeyedPool`. Single shared,
  reference-counted resource: use `RcRef`.

## Nested and parallel scopes

```typescript
import { Effect, Scope } from "effect"

declare const conn: Effect.Effect<{ q: (s: string) => Effect.Effect<void> }, never, Scope.Scope>

const nested = Effect.scoped(
  Effect.gen(function* () {
    const db = yield* conn // lives for the outer scope
    yield* Effect.scoped(
      Effect.gen(function* () {
        yield* Effect.addFinalizer(() => Effect.log("inner done"))
        yield* db.q("BEGIN; ...; COMMIT")
      })
    ) // inner finalizers run here
    yield* db.q("SELECT 1")
  })
) // db released here

// Each branch has its own scope; all are released even if one fails
const parallel = Effect.all(
  [Effect.scoped(conn), Effect.scoped(conn)],
  { concurrency: 2 }
)
```

## Long-lived resources in services

```typescript
import { Context, Effect, Layer } from "effect"

class Ws extends Context.Tag("Ws")<Ws, { readonly send: (m: string) => Effect.Effect<void> }>() {}
declare const openSocket: (url: string) => Promise<{ send(m: string): void; close(): void }>

const WsLive = Layer.scoped(
  Ws,
  Effect.gen(function* () {
    const sock = yield* Effect.acquireRelease(
      Effect.promise(() => openSocket("wss://example.test")),
      (s) => Effect.sync(() => s.close())
    )
    return { send: (m) => Effect.sync(() => sock.send(m)) }
  })
)
// Closed when the runtime/layer scope closes (app shutdown, end of test)
```

## Pitfalls

- **Unscoped acquisition:** running `openFile(...)` without `Effect.scoped`
  (or scoped layer) is a type error. Do not silence it with casts or by
  providing a never-closed scope.
- **Scope confusion:** scope ends where `Effect.scoped` ends, so a resource
  returned from inside it is already released (closed handle). Keep all use
  inside, or widen scope.
- **Failing finalizers:** release that can fail turns cleanup errors into
  defects. `Effect.ignore` or log in release.
- **Slow finalizers:** finalizers are uninterruptible. Bound them with
  `Effect.timeout` if they do I/O.
- **Acquire then register later:** registering finalizer a few steps after
  acquisition leaks if interrupted in between. Use `acquireRelease`; it makes
  acquire+register atomic.
- **Per-call `Effect.provide(LayerWithPool)`**: builds new pool every call.
  Provide once at the edge.

## Done when

- Every acquired handle (file, socket, connection, subscription, fiber) comes
  from `acquireRelease`, `acquireUseRelease`, `Layer.scoped` or `Pool`. No
  code calls `close()` manually on success path only.
- A test interrupts or fails the using effect and asserts finalizer ran (see
  **effect-testing**).

## Related skills

- effect-dependency-injection - `Layer.scoped`, `ManagedRuntime.dispose`
- effect-concurrency - `forkScoped`, interruption
- effect-testing - asserting cleanup with `it.scoped`

Docs: <https://effect.website/docs/resource-management/scope/>
