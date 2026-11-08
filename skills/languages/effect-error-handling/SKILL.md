---
name: effect-error-handling
user-invocable: false
description: "Effect-TS v3: model expected failures as Data.TaggedError, recover with catchTag/catchTags/catchAll, convert with either/option, retry with Schedule, and handle defects and interruptions via Cause. Use when designing or fixing the E channel of Effect code; for fp-ts Either/TaskEither use fp-errors."
allowed-tools:
  - Read
  - Write
  - Edit
---

# Effect Error Handling

> **Version:** targets `effect` 3.x. In Effect 4, `Effect.catchAll` became
> `Effect.catch`, `Effect.either` became `Effect.result`, `Either` became
> `Result`. Check `effect` in package.json first.

## Errors vs defects vs interruption

| Kind | Where it lives | Created by | Handle with |
| --- | --- | --- | --- |
| Expected error | `E` type parameter | `Effect.fail`, `try`/`tryPromise` `catch`, `yield* new TaggedErr()` | `catchTag`, `catchAll`, `either`, `retry` |
| Defect | `Cause` only (not in types) | throw inside `sync`/`promise`, `Effect.die`, `orDie` | `catchAllDefect`, `catchAllCause`, top-level logging |
| Interruption | `Cause` only | timeout, race loser, `Fiber.interrupt` | finalizers, `onInterrupt` |

Decision rule: if caller can reasonably act differently on the failure (show
404, retry, fall back), make it an expected error with its own tag. If it means
a bug or broken invariant, make it a defect (`orDie`) and let the edge log it.

## Define errors as tagged classes

```typescript
import { Data, Effect } from "effect"

class NotFound extends Data.TaggedError("NotFound")<{ readonly id: string }> {}
class Unauthorized extends Data.TaggedError("Unauthorized")<{ readonly userId: string }> {}
class NetworkError extends Data.TaggedError("NetworkError")<{ readonly cause: unknown }> {}

interface User { readonly id: string; readonly name: string }

const fetchUser = (id: string): Effect.Effect<User, NotFound | NetworkError> =>
  Effect.gen(function* () {
    const res = yield* Effect.tryPromise({
      try: (signal) => fetch(`/api/users/${id}`, { signal }),
      catch: (cause) => new NetworkError({ cause })
    })
    if (res.status === 404) return yield* new NotFound({ id })
    return yield* Effect.promise(() => res.json() as Promise<User>)
  })
```

`Data.TaggedError` gives `_tag` for `catchTag` and a real `Error` with stack.
`yield*` the instance directly to fail. Use `Schema.TaggedError` instead when
error must be serialized (RPC, HTTP API).

## Recovering

```typescript
import { Effect, Data } from "effect"

class NotFound extends Data.TaggedError("NotFound")<{ readonly id: string }> {}
class NetworkError extends Data.TaggedError("NetworkError")<{ readonly cause: unknown }> {}
class Timeout extends Data.TaggedError("Timeout") {}
declare const op: Effect.Effect<string, NotFound | NetworkError | Timeout>

// One tag; the rest stay in E
const a = op.pipe(Effect.catchTag("NotFound", (e) => Effect.succeed(`missing ${e.id}`)))
// Effect<string, NetworkError | Timeout>

// Several tags at once
const b = op.pipe(
  Effect.catchTags({
    NotFound: () => Effect.succeed("default"),
    Timeout: () => Effect.succeed("cached")
  })
)
// Effect<string, NetworkError>

// Everything expected (removes E); prefer catchTag(s) so new errors stay visible
const c = op.pipe(Effect.catchAll((e) => Effect.succeed(`failed: ${e._tag}`)))

// Predicate-based
const d = op.pipe(
  Effect.catchIf(
    (e): e is NetworkError | Timeout => e._tag !== "NotFound",
    () => Effect.succeed("transient")
  )
)
```

| Need | Operator |
| --- | --- |
| Handle one or few tags | `catchTag`, `catchTags` |
| Translate errors between layers | `mapError` |
| Observe without handling (log, metric) | `tapError`, `tapErrorTag` |
| Fallback effect on any error | `orElse`, `orElseSucceed` |
| Value to branch on | `Effect.either` (`Either<A, E>`), `Effect.option`, `Effect.exit` |
| Both channels into one handler | `Effect.match`, `Effect.matchEffect` |
| Turn "impossible" errors into defects | `Effect.orDie`, `Effect.orDieWith` |
| Fail on bad value | `Effect.filterOrFail` |

```typescript
import { Effect, Either } from "effect"

declare const load: Effect.Effect<number, "Bad">

const handled = Effect.gen(function* () {
  const r = yield* Effect.either(load)
  if (Either.isLeft(r)) return `error: ${r.left}`
  return `ok: ${r.right}`
})
// Effect<string, never>
```

## Retry, timeout, fallback

```typescript
import { Data, Duration, Effect, Schedule } from "effect"

class NetworkError extends Data.TaggedError("NetworkError") {}
class BadRequest extends Data.TaggedError("BadRequest") {}
declare const call: Effect.Effect<string, NetworkError | BadRequest>

// Exponential backoff with jitter, max 5 retries, only for transient errors
const policy = Schedule.exponential("100 millis").pipe(
  Schedule.jittered,
  Schedule.intersect(Schedule.recurs(5))
)

const robust = call.pipe(
  Effect.retry({ schedule: policy, while: (e) => e._tag === "NetworkError" }),
  Effect.timeoutFail({
    duration: Duration.seconds(10),
    onTimeout: () => new NetworkError()
  }),
  Effect.orElse(() => Effect.succeed("fallback"))
)
```

- `Effect.retry` re-runs whole effect. Make it idempotent first (idempotency
  key for writes).
- `Effect.timeout(d)` fails with `TimeoutException`. `timeoutFail` picks the
  error. Timed-out effect is interrupted, so its finalizers run.
- Never retry validation/authorization errors. Filter with `while`/`until`.

## Collecting several errors

`Effect.all` short-circuits on first failure. To report every failure:

```typescript
import { Effect } from "effect"

declare const validateField: (f: string) => Effect.Effect<string, string>
const fields = ["name", "email", "age"]

// Fails with Array<string> of all errors if any fail
const all = Effect.validateAll(fields, validateField)

// Keeps both sides: [failures, successes]
const split = Effect.partition(fields, validateField)

// Per-item Either, never fails
const each = Effect.all(fields.map(validateField), { mode: "either" })
```

To parse input, prefer `effect/Schema` with `{ errors: "all" }` (see
**effect-schema**).

## Defects and causes

```typescript
import { Cause, Effect, Option } from "effect"

declare const risky: Effect.Effect<number, "Expected">

const safe = risky.pipe(
  Effect.catchAllCause((cause) => {
    if (Cause.isInterruptedOnly(cause)) return Effect.succeed(-1)
    const expected = Cause.failureOption(cause)
    if (Option.isSome(expected)) return Effect.succeed(0)
    // defect: log the whole cause (includes stack and parallel failures)
    return Effect.logError("defect", Cause.pretty(cause)).pipe(Effect.as(-2))
  })
)

// Defects only
const noCrash = risky.pipe(Effect.catchAllDefect((defect) => Effect.succeed(-3)))
```

`Effect.sandbox` moves full `Cause<E>` into error channel. `Effect.unsandbox`
reverses it. Use for cause-aware handling mid-pipeline. Catch defects rarely: at
request or job boundary, to log and convert to 500/failed-job result.

## Pitfalls

- `catchAll` early in pipeline erases error types callers could use.
- Plain `throw` inside `Effect.sync`/`gen` is a defect. `catchTag`/`catchAll`
  will not catch it.
- `try/catch` around `Effect.runPromise` sees `FiberFailure`, not your tagged
  error. Use `runPromiseExit` or handle inside the effect.
- Error union grows to many tags in high-level function: map lower-level errors
  to domain error with `mapError` at module boundaries.

## Done when

- Each module exposes small set of tagged errors in its signatures. No
  `unknown`/`Error` in `E` except at external boundaries being wrapped.
- Every retry has bounded schedule and error filter.
- Defects logged once with `Cause.pretty` at the edge.

## Related skills

- effect-core-patterns - constructors and `Effect.gen`
- effect-schema - parse errors and `Schema.TaggedError`
- effect-testing - asserting on `Exit` and failures

Docs: <https://effect.website/docs/error-management/expected-errors/>
