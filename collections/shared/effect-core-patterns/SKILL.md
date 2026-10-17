---
name: effect-core-patterns
user-invocable: false
description: "Effect-TS v3: the Effect<A, E, R> type, constructors (succeed, fail, sync, try, tryPromise, async), composing with Effect.gen/Effect.fn and pipe, and running effects at the program edge. Start here for any Effect code; for fp-ts (pipe/TaskEither) code use the fp-* skills instead."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Effect Core Patterns

> **Version:** targets `effect` 3.x (`import { Effect } from "effect"`). Effect 4
> renames many APIs (`Context.Tag` -> `Context.Service`, `Effect.catchAll` ->
> `Effect.catch`, `Effect.fork` -> `Effect.forkChild`, `Either` -> `Result`).
> Check `effect` in package.json before copying signatures.

## The Effect type

`Effect<A, E, R>` is a lazy, immutable description of a program:

| Param | Meaning | `never` means |
| --- | --- | --- |
| `A` | success value | it never succeeds (e.g. `Effect.never`, infinite loop) |
| `E` | expected, typed failures | it cannot fail with an expected error |
| `R` | services it needs from context | it is ready to run |

Nothing runs until a `run*` function executes it. Unexpected failures (thrown
exceptions, bugs) are *defects* and do not appear in `E`.

## Choosing a constructor

| Situation | Use |
| --- | --- |
| Pure value already in hand | `Effect.succeed(x)` / `Effect.void` |
| Expected failure | `Effect.fail(new MyError(...))` |
| Sync side effect that cannot throw | `Effect.sync(() => ...)` |
| Sync code that may throw | `Effect.try({ try, catch })` |
| Promise that cannot reject | `Effect.promise(() => ...)` |
| Promise that may reject | `Effect.tryPromise({ try: (signal) => ..., catch })` |
| Callback API | `Effect.async<A, E>((resume, signal) => ...)` |
| Build lazily / recursion | `Effect.suspend(() => ...)` |

A throw inside `sync`/`promise` (or a rejected `promise`) becomes a defect, not
a typed error. Use `try`/`tryPromise` whenever the call can fail for an
expected reason.

```typescript
import { Data, Effect } from "effect"

class ParseError extends Data.TaggedError("ParseError")<{ readonly cause: unknown }> {}
class HttpError extends Data.TaggedError("HttpError")<{ readonly status: number }> {}

const parseJson = (text: string) =>
  Effect.try({
    try: (): unknown => JSON.parse(text),
    catch: (cause) => new ParseError({ cause })
  })
// Effect<unknown, ParseError, never>

const fetchJson = (url: string) =>
  Effect.tryPromise({
    // the AbortSignal fires if the fiber is interrupted (timeout, race loser)
    try: (signal) => fetch(url, { signal }),
    catch: () => new HttpError({ status: 0 })
  }).pipe(
    Effect.filterOrFail(
      (res) => res.ok,
      (res) => new HttpError({ status: res.status })
    ),
    Effect.flatMap((res) => Effect.promise(() => res.text()))
  )
// Effect<string, HttpError, never>

// Callback API; the returned effect is the interruption cleanup
const sleepMs = (ms: number) =>
  Effect.async<void>((resume) => {
    const id = setTimeout(() => resume(Effect.void), ms)
    return Effect.sync(() => clearTimeout(id))
  })
```

`Effect.tryPromise(() => p)` without `catch` fails with `UnknownException`;
prefer the object form so `E` stays meaningful. Tagged error classes are
covered in **effect-error-handling**.

## Composing with Effect.gen

`Effect.gen` reads like async/await: `yield*` an effect to get its value; the
first failure short-circuits. Errors and requirements of every yielded effect
are unioned into the result type.

```typescript
import { Data, Effect } from "effect"

class DivideByZero extends Data.TaggedError("DivideByZero") {}

const divide = (a: number, b: number) =>
  Effect.gen(function* () {
    if (b === 0) {
      // `return yield*` makes TypeScript narrow and stops the generator
      return yield* new DivideByZero()
    }
    return a / b
  })
// Effect<number, DivideByZero, never>

const program = Effect.gen(function* () {
  const x = yield* divide(10, 2)
  const y = yield* divide(x, 0)
  return x + y
})
```

Rules:

- Always `return yield* Effect.fail(...)` (or `return yield* new TaggedErr()`);
  a bare `yield*` without `return` leaves the code after it reachable in the
  types.
- Do not `await` inside `Effect.gen`; wrap promises with `tryPromise`.
- Independent steps written one after another run *sequentially*. Use
  `Effect.all` (see **effect-concurrency**) when they can run in parallel.

### Effect.fn for named functions

For functions that return effects, `Effect.fn` (v3.11+) combines `gen` with a
tracing span named after the function, which shows up in stack traces and
OpenTelemetry:

```typescript
import { Effect } from "effect"

const getUserName = Effect.fn("getUserName")(function* (id: string) {
  yield* Effect.annotateCurrentSpan("userId", id)
  return `user-${id}`
})
// (id: string) => Effect<string, never, never>
```

## Pipelines

Use `pipe`/`.pipe` for short transformations; switch to `Effect.gen` once
there are more than two or three dependent steps.

| Operator | Does |
| --- | --- |
| `Effect.map(f)` | transform success value |
| `Effect.flatMap(f)` | next step depends on the value and returns an effect |
| `Effect.andThen(x)` | flexible sequencing; `x` may be a value, a function, a promise-returning function or an effect |
| `Effect.tap(f)` | run a side effect, keep the original value |
| `Effect.mapError(f)` | transform the error |
| `Effect.mapBoth({ onFailure, onSuccess })` | transform both channels |
| `Effect.orElse(() => fallback)` | replace any failure with another effect |
| `Effect.as(v)` / `Effect.asVoid` | replace the value |

```typescript
import { Effect } from "effect"

const program = Effect.succeed("hello").pipe(
  Effect.map((s) => s.toUpperCase()),
  Effect.tap((s) => Effect.log(`got ${s}`)),
  Effect.flatMap((s) => (s.length > 3 ? Effect.succeed(s.length) : Effect.fail("too short" as const)))
)
// Effect<number, "too short", never>
```

## Running effects

Run once, at the edge (main, request handler, test). Inside effects, compose;
never call `runPromise` from within an effect.

| Runner | Use when | On failure |
| --- | --- | --- |
| `Effect.runPromise(e)` | async entry point, `R` must be `never` | rejects with a `FiberFailure` wrapper |
| `Effect.runPromiseExit(e)` | you need the typed error or cause | resolves with `Exit` |
| `Effect.runSync(e)` | effect is fully synchronous | throws; also throws if it hits async work |
| `Effect.runFork(e)` | fire-and-forget, get a `RuntimeFiber` | observe via the fiber |
| `NodeRuntime.runMain(e)` (`@effect/platform-node`) | Node CLI/server main | logs, sets exit code, handles SIGINT |

```typescript
import { Effect, Exit, Cause } from "effect"

const exit = await Effect.runPromiseExit(Effect.fail("boom" as const))
if (Exit.isFailure(exit)) {
  // Cause.failureOption extracts the typed error, if the cause is a Fail
  console.log(Cause.failureOption(exit.cause)) // { _id: 'Option', _tag: 'Some', value: 'boom' }
}
```

Do not `try/catch` around `runPromise` and expect your tagged error: the
rejection is a `FiberFailure`. Handle errors inside the effect, or use
`runPromiseExit`. If `R` is not `never`, provide layers first (see
**effect-dependency-injection**); a missing service is a compile-time error,
not a runtime one.

## Pitfalls

- `Effect.runSync` on an effect that sleeps, awaits a promise or uses async
  callbacks throws ("cannot be resolved synchronously").
- Side effects outside constructors (`const x = Date.now()` at module level)
  run once at import, not on each execution. Wrap in `Effect.sync`.
- `Effect.promise` around a call that can reject hides the failure as a defect.
- Long `pipe(flatMap(... flatMap(...)))` chains: rewrite with `Effect.gen`.
- Using plain objects `{ _tag: "X" }` as errors works with `catchTag`, but
  `Data.TaggedError` gives stack traces, `instanceof`, and structural equality.

## Done when

- Every async/throwing boundary is wrapped in `try`/`tryPromise` with a typed
  error, and the `E` channel lists only meaningful failures.
- `run*` is called only at the program edge with `R = never`.
- `tsc --noEmit` passes without `any` casts on effect types.

## Related skills

- effect-error-handling - tagged errors, catchTag, retries, causes
- effect-dependency-injection - services and layers (`R`)
- effect-concurrency - `Effect.all`, fibers, queues
- effect-resource-management - scopes and finalizers
- effect-schema - decoding unknown input
- effect-testing - `@effect/vitest`, TestClock

Docs: <https://effect.website/docs/getting-started/the-effect-type/>
