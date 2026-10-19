---
name: effect-testing
user-invocable: false
description: "Effect-TS v3: test Effect code with @effect/vitest (it.effect, it.scoped, it.live, layer), drive time with TestClock, swap services with test layers, and assert on failures via Exit/Either. Use when writing or fixing tests for Effect programs, especially ones involving services, time, concurrency or resource cleanup."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Effect Testing

> **Version:** targets `effect` 3.x with `@effect/vitest` 0.x and `vitest` 3
> (checked with effect 3.22, @effect/vitest 0.30, vitest 3.2). `@effect/vitest`
> 4.x pairs with Effect 4. Check versions in package.json; peer dependency
> ranges must match.

## Setup

```bash
npm i -D vitest @effect/vitest
```

Import `it`, `describe`, `expect` and the rest of Vitest from
`@effect/vitest` (it re-exports `vitest`).

| Test helper | Provides | Use for |
| --- | --- | --- |
| `it.effect` | `TestClock`, `TestRandom` and other test services | default for unit tests |
| `it.scoped` | test services + a `Scope` closed after the test | tests that acquire resources |
| `it.live` | real clock and services | timing against real I/O (rare) |
| `it.scopedLive` | live services + `Scope` | real resources with cleanup |
| `layer(L)(name, (it) => ...)` | builds `L` once for a block of tests | shared test services, expensive fixtures |
| `it.prop` / `it.effect.prop` | property tests from Schemas or fast-check arbitraries | invariants |
| `it.flakyTest(effect, timeout)` | retries until success or timeout | known-flaky external dependency |

Avoid `await Effect.runPromise(...)` inside plain `it(...)`: it bypasses the
test clock, reports failures as an opaque `FiberFailure`, and does not close
scopes per test.

## Basic tests and failures

```typescript
import { describe, expect, it } from "@effect/vitest"
import { Data, Effect, Either, Exit } from "effect"

class InvalidEmail extends Data.TaggedError("InvalidEmail")<{ readonly input: string }> {}

const validateEmail = (s: string) =>
  s.includes("@") ? Effect.succeed(s.toLowerCase()) : Effect.fail(new InvalidEmail({ input: s }))

describe("validateEmail", () => {
  it.effect("accepts and normalizes a valid email", () =>
    Effect.gen(function* () {
      const email = yield* validateEmail("Ada@Example.com")
      expect(email).toBe("ada@example.com")
    })
  )

  it.effect("fails with InvalidEmail", () =>
    Effect.gen(function* () {
      // Effect.flip swaps channels: the error becomes the success value
      const error = yield* Effect.flip(validateEmail("nope"))
      expect(error).toBeInstanceOf(InvalidEmail)
      expect(error.input).toBe("nope")
    })
  )

  it.effect("inspects the full outcome", () =>
    Effect.gen(function* () {
      const result = yield* Effect.either(validateEmail("nope"))
      expect(Either.isLeft(result)).toBe(true)

      const exit = yield* Effect.exit(validateEmail("a@b"))
      expect(exit).toStrictEqual(Exit.succeed("a@b"))
    })
  )
})
```

If a test effect fails, `@effect/vitest` fails the test and prints the pretty
`Cause` (including defects), so you do not need `try/catch`.

## Test layers

Define the real service with a class tag (see **effect-dependency-injection**)
and provide a test implementation per test or per block.

```typescript
import { describe, expect, it, layer } from "@effect/vitest"
import { Context, Effect, Layer, Option, Ref } from "effect"

interface User { readonly id: string; readonly name: string }

class UserRepo extends Context.Tag("UserRepo")<UserRepo, {
  readonly find: (id: string) => Effect.Effect<Option.Option<User>>
  readonly save: (u: User) => Effect.Effect<void>
}>() {}

// Stateful in-memory fake; a fresh Ref each time the layer is built
const UserRepoTest = Layer.effect(
  UserRepo,
  Effect.gen(function* () {
    const store = yield* Ref.make(new Map<string, User>())
    return {
      find: (id) => Ref.get(store).pipe(Effect.map((m) => Option.fromNullable(m.get(id)))),
      save: (u) => Ref.update(store, (m) => new Map(m).set(u.id, u))
    }
  })
)

const rename = (id: string, name: string) =>
  Effect.gen(function* () {
    const repo = yield* UserRepo
    const user = yield* repo.find(id)
    if (Option.isSome(user)) yield* repo.save({ ...user.value, name })
  })

describe("rename (per-test layer)", () => {
  it.effect("updates an existing user", () =>
    Effect.gen(function* () {
      const repo = yield* UserRepo
      yield* repo.save({ id: "1", name: "Ada" })
      yield* rename("1", "Grace")
      expect(yield* repo.find("1")).toStrictEqual(Option.some({ id: "1", name: "Grace" }))
    }).pipe(Effect.provide(UserRepoTest)) // new store for this test only
  )
})

// Shared layer: built once for all tests in the block (state is shared!)
layer(UserRepoTest)("rename (shared layer)", (it) => {
  it.effect("ignores unknown ids", () =>
    Effect.gen(function* () {
      yield* rename("missing", "X")
      const repo = yield* UserRepo
      expect(Option.isNone(yield* repo.find("missing"))).toBe(true)
    })
  )
})
```

Choose per-test `Effect.provide` when tests mutate state; use `layer(...)`
for read-only or expensive fixtures (a test container, a migrated DB).
Spies are just test layers that record calls in a `Ref` and expose them via
the service or a second tag.

## Time with TestClock

Under `it.effect`, the clock starts at 0 and only moves when you adjust it,
so tests with sleeps, timeouts, retries and schedules run instantly and
deterministically.

```typescript
import { expect, it } from "@effect/vitest"
import { Duration, Effect, Fiber, Option, Schedule, TestClock } from "effect"

it.effect("times out a slow call", () =>
  Effect.gen(function* () {
    const fiber = yield* Effect.fork(
      Effect.sleep("10 seconds").pipe(Effect.as("done"), Effect.timeoutOption("5 seconds"))
    )
    yield* TestClock.adjust("5 seconds") // fork FIRST, then move time
    expect(yield* Fiber.join(fiber)).toStrictEqual(Option.none())
  })
)

it.effect("retries with backoff", () =>
  Effect.gen(function* () {
    let attempts = 0
    const flaky = Effect.suspend(() => (++attempts < 3 ? Effect.fail("boom") : Effect.succeed("ok")))
    const fiber = yield* Effect.fork(flaky.pipe(Effect.retry(Schedule.spaced("1 second"))))
    yield* TestClock.adjust(Duration.seconds(2))
    expect(yield* Fiber.join(fiber)).toBe("ok")
    expect(attempts).toBe(3)
  })
)
```

Pattern: **fork the time-dependent effect, adjust the clock, then join**.
Adjusting before forking, or joining before adjusting, hangs the test.

## Resources and interruption

```typescript
import { expect, it } from "@effect/vitest"
import { Deferred, Effect, Fiber, Ref } from "effect"

it.effect("releases on failure", () =>
  Effect.gen(function* () {
    const released = yield* Ref.make(false)
    const resource = Effect.acquireRelease(Effect.succeed("conn"), () => Ref.set(released, true))
    const exit = yield* Effect.exit(Effect.scoped(Effect.zipRight(resource, Effect.fail("boom"))))
    expect(exit._tag).toBe("Failure")
    expect(yield* Ref.get(released)).toBe(true)
  })
)

it.effect("runs finalizers when interrupted", () =>
  Effect.gen(function* () {
    const cleaned = yield* Ref.make(false)
    const started = yield* Deferred.make<void>()
    const fiber = yield* Effect.fork(
      Deferred.succeed(started, undefined).pipe(
        Effect.zipRight(Effect.never),
        Effect.ensuring(Ref.set(cleaned, true))
      )
    )
    // Wait until the fiber is running; interrupting a fiber that has not
    // started yet skips its body (and the ensuring) entirely
    yield* Deferred.await(started)
    yield* Fiber.interrupt(fiber)
    expect(yield* Ref.get(cleaned)).toBe(true)
  })
)

// it.scoped: resources acquired in the test are released after it
it.scoped("uses a scoped resource", () =>
  Effect.gen(function* () {
    const conn = yield* Effect.acquireRelease(Effect.succeed({ open: true }), () => Effect.void)
    expect(conn.open).toBe(true)
  })
)
```

## Property tests

```typescript
import { expect, it } from "@effect/vitest"
import { Effect, Schema } from "effect"

const roundTrip = (n: number) => Effect.succeed(Number(String(n)))

it.effect.prop("number survives string round trip", [Schema.Int], ([n]) =>
  Effect.gen(function* () {
    expect(yield* roundTrip(n)).toBe(n)
  })
)
```

Arbitraries can be Schemas (generated via `Arbitrary.make`) or fast-check
arbitraries (`import { FastCheck } from "effect"`).

## Pitfalls

- Real time in tests: `Effect.sleep` under `it.effect` never completes unless
  you `TestClock.adjust`; under `it.live` it really sleeps.
- Shared mutable fakes across tests via `layer(...)` causing order-dependent
  results.
- Asserting with `expect(...).rejects` on `runPromise`: the rejection is a
  `FiberFailure`, not your error. Use `Effect.flip`, `Effect.either` or
  `Effect.exit`.
- Mocking modules (`vi.mock`) for things that are services: provide a test
  layer instead.
- Forgetting to test the failure and interruption paths of code that acquires
  resources.

## Done when

- Tests use `it.effect`/`it.scoped`/`layer` rather than manual `runPromise`.
- Every service dependency in tests comes from an explicit test layer.
- Time-based behavior is tested with `TestClock`, and `vitest run` finishes in
  milliseconds per such test.
- Error tags, retries, and finalizers on failure/interruption each have a test.

## Related skills

- effect-dependency-injection - defining services and layers
- effect-error-handling - error types to assert on
- effect-concurrency - fibers and interruption under test
- effect-resource-management - scopes and finalizers

Docs: <https://effect.website/docs/testing/testclock/>,
<https://github.com/Effect-TS/effect/tree/main/packages/vitest>
