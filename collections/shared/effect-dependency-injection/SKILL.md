---
name: effect-dependency-injection
user-invocable: false
description: "Effect-TS v3: define services with Context.Tag classes or Effect.Service, build them with Layer (succeed/effect/scoped), compose and provide layers, and swap implementations for tests or environments. Use when an effect has a non-never R channel or you are wiring an Effect application's dependency graph."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Effect Dependency Injection

> **Version:** targets `effect` 3.x (examples checked against 3.22). Effect 4
> replaces `Context.Tag`/`Effect.Service` with `Context.Service`; check
> `effect` in package.json before copying.

The `R` in `Effect<A, E, R>` lists the services an effect needs. A **tag**
identifies a service; a **layer** (`Layer<ROut, E, RIn>`) is a recipe that
builds `ROut` from `RIn`. You provide layers once at the edge; until then the
compiler refuses to run an effect whose `R` is not `never`.

## Choosing how to define a service

| Situation | Use |
| --- | --- |
| Interface with several implementations (live, test, in-memory) defined separately | `class X extends Context.Tag("X")<X, Shape>() {}` + layers |
| One canonical implementation that is constructed from other services | `class X extends Effect.Service<X>()("X", { effect, dependencies })` |
| Value with a sensible default that callers may override (feature flag, log level) | `Context.Reference` |
| Library code that must not use classes, or legacy code | `Context.GenericTag<Shape>("X")` (older style; prefer the class forms) |

Tag keys must be globally unique strings; use a package-qualified name
(`"@app/UserRepo"`) in libraries.

## Context.Tag + Layer

```typescript
import { Context, Data, Effect, Layer, Option } from "effect"

class DbError extends Data.TaggedError("DbError")<{ readonly cause: unknown }> {}
interface User { readonly id: string; readonly name: string }

// 1. Tag: the class is both the type and the key
class UserRepo extends Context.Tag("@app/UserRepo")<
  UserRepo,
  {
    readonly findById: (id: string) => Effect.Effect<Option.Option<User>, DbError>
    readonly save: (user: User) => Effect.Effect<void, DbError>
  }
>() {}

class AppConfig extends Context.Tag("@app/AppConfig")<
  AppConfig,
  { readonly dbUrl: string }
>() {}

// 2. Use it: yield the tag to get the implementation
const rename = (id: string, name: string) =>
  Effect.gen(function* () {
    const repo = yield* UserRepo
    const user = yield* repo.findById(id)
    if (Option.isNone(user)) return false
    yield* repo.save({ ...user.value, name })
    return true
  })
// Effect<boolean, DbError, UserRepo>

// 3. Layers
const AppConfigLive = Layer.succeed(AppConfig, { dbUrl: "postgres://localhost/app" })

const UserRepoLive = Layer.effect(
  UserRepo,
  Effect.gen(function* () {
    const { dbUrl } = yield* AppConfig // dependency becomes RIn
    yield* Effect.log(`connecting to ${dbUrl}`)
    const rows = new Map<string, User>()
    return UserRepo.of({
      findById: (id) => Effect.succeed(Option.fromNullable(rows.get(id))),
      save: (user) => Effect.sync(() => void rows.set(user.id, user))
    })
  })
)
// Layer<UserRepo, never, AppConfig>

// 4. Provide at the edge
const MainLive = UserRepoLive.pipe(Layer.provide(AppConfigLive))
// Layer<UserRepo, never, never>

const main = rename("1", "Ada").pipe(Effect.provide(MainLive))
// Effect<boolean, DbError, never>  -> Effect.runPromise(main)
```

Keep the service shape free of requirements (`R = never` on its methods):
dependencies belong in the layer that builds it, not in each method's type.

## Effect.Service (one canonical implementation)

`Effect.Service` defines the tag and its default layer together. The class
gets a `Default` layer (with `dependencies` already provided) and
`DefaultWithoutDependencies`.

```typescript
import { Effect, Layer } from "effect"

class Clock2 extends Effect.Service<Clock2>()("@app/Clock2", {
  succeed: { now: () => new Date() }
}) {}

class Greeter extends Effect.Service<Greeter>()("@app/Greeter", {
  effect: Effect.gen(function* () {
    const clock = yield* Clock2
    return {
      greet: (name: string) => Effect.succeed(`Hello ${name} at ${clock.now().toISOString()}`)
    }
  }),
  dependencies: [Clock2.Default],
  accessors: true // adds static Greeter.greet(...) returning Effect<..., Greeter>
}) {}

const program = Greeter.greet("Ada").pipe(Effect.provide(Greeter.Default))
// Effect<string, never, never>

// Tests: keep the real Greeter, swap its dependency for a fake
const FixedClock = Layer.succeed(Clock2, new Clock2({ now: () => new Date(0) }))
const testGreeter = Greeter.greet("Ada").pipe(
  Effect.provide(Greeter.DefaultWithoutDependencies.pipe(Layer.provide(FixedClock)))
)
```

Instances of an `Effect.Service` class are created with `new X(impl)`, which
is how you build fakes for `Layer.succeed`. Use `scoped:` instead of
`effect:` when construction acquires resources (see below).

## Constructors for layers

| Constructor | When |
| --- | --- |
| `Layer.succeed(Tag, impl)` | implementation is a plain value |
| `Layer.sync(Tag, () => impl)` | lazy, synchronous construction |
| `Layer.effect(Tag, effect)` | construction needs other services or async work |
| `Layer.scoped(Tag, effect)` | construction acquires a resource that must be released (pool, connection, subscription) |
| `Layer.unwrapEffect(effect)` | choose a layer at runtime (env var, config) |
| `Layer.function(In, Out, f)` | derive one service from another |

```typescript
import { Config, Context, Effect, Layer } from "effect"

class Db extends Context.Tag("@app/Db")<Db, { readonly query: (sql: string) => Effect.Effect<unknown[]> }>() {}

declare const openPool: (url: string) => Promise<{ query(sql: string): Promise<unknown[]>; end(): Promise<void> }>

// Scoped layer: the finalizer runs when the application (or test) scope closes
const DbLive = Layer.scoped(
  Db,
  Effect.gen(function* () {
    const url = yield* Config.string("DATABASE_URL")
    const pool = yield* Effect.acquireRelease(
      Effect.promise(() => openPool(url)),
      (p) => Effect.promise(() => p.end())
    )
    return { query: (sql) => Effect.promise(() => pool.query(sql)) }
  })
)
// Layer<Db, ConfigError, never>

// Environment-selected implementation
const DbInMemory = Layer.succeed(Db, { query: () => Effect.succeed([]) })
const DbAuto = Layer.unwrapEffect(
  Config.boolean("USE_FAKE_DB").pipe(
    Config.withDefault(false),
    Effect.map((fake) => (fake ? DbInMemory : DbLive))
  )
)
```

## Composing layers

| Operator | Result |
| --- | --- |
| `Layer.merge(a, b)` / `Layer.mergeAll(...)` | outputs of both; inputs of both |
| `outer.pipe(Layer.provide(inner))` | feeds `inner`'s outputs into `outer`'s inputs; output is only `outer`'s |
| `outer.pipe(Layer.provideMerge(inner))` | same, but output also includes `inner`'s services |

```typescript
import { Context, Effect, Layer } from "effect"

class A extends Context.Tag("A")<A, { readonly a: number }>() {}
class B extends Context.Tag("B")<B, { readonly b: number }>() {}
class C extends Context.Tag("C")<C, { readonly c: number }>() {}

const ALive = Layer.succeed(A, { a: 1 })
const BLive = Layer.effect(B, Effect.map(A, ({ a }) => ({ b: a + 1 }))) // needs A
const CLive = Layer.effect(C, Effect.map(B, ({ b }) => ({ c: b + 1 }))) // needs B

const AppLive = CLive.pipe(
  Layer.provide(BLive),
  Layer.provide(ALive)
)
// Layer<C, never, never>  (A and B are internal)

const AppWithAll = CLive.pipe(
  Layer.provideMerge(BLive),
  Layer.provideMerge(ALive)
)
// Layer<A | B | C, never, never>

// Wrong: merge does NOT feed BLive into CLive -> Layer<B | C, never, A | B>
const notWired = Layer.mergeAll(CLive, BLive)
```

Build one `MainLive` layer per entry point and provide it once. If the type
still shows a requirement, the error message names the missing service.

**Memoization:** a layer value is built once per `Effect.provide` even if it
appears in several branches of the graph (layers are compared by reference).
Calling a function that returns a *new* layer each time defeats this; define
layers as constants. Use `Layer.fresh(layer)` when you really want a second
instance.

**Do not** call `Effect.provide` deep inside library functions: each call
builds the layer again (new pool, new connections). Provide at the edge.

## Integrating with non-Effect frameworks

Use `ManagedRuntime` to build layers once and run effects from callbacks
(Express handlers, React server actions, queues):

```typescript
import { Context, Effect, Layer, ManagedRuntime } from "effect"

class Greeting extends Context.Tag("Greeting")<Greeting, { readonly text: string }>() {}

const runtime = ManagedRuntime.make(Layer.succeed(Greeting, { text: "hi" }))

export async function handler(): Promise<string> {
  return runtime.runPromise(Effect.map(Greeting, (g) => g.text))
}
// on shutdown: await runtime.dispose()  (runs scoped-layer finalizers)
```

## Optional and default services

```typescript
import { Context, Effect, Option } from "effect"

class Cache extends Context.Tag("Cache")<Cache, { readonly get: (k: string) => Effect.Effect<Option.Option<string>> }>() {}

// Optional dependency: does not add Cache to R
const lookup = (k: string) =>
  Effect.gen(function* () {
    const cache = yield* Effect.serviceOption(Cache)
    return Option.isSome(cache) ? yield* cache.value.get(k) : Option.none()
  })

// Service with a default value: never appears in R; override with provideService
class LogLevelRef extends Context.Reference<LogLevelRef>()("LogLevelRef", {
  defaultValue: () => "info" as "info" | "debug"
}) {}

const level = Effect.gen(function* () {
  return yield* LogLevelRef
}) // Effect<"info" | "debug", never, never>
const debugLevel = level.pipe(Effect.provideService(LogLevelRef, "debug"))
```

## GenericTag (legacy)

`Context.GenericTag<Shape>("Key")` creates a tag without a class. It still
works in v3 and appears in older code and docs, but the class form gives a
nominal type, `Tag.of(...)`, and better error messages. When editing such
code, migrate opportunistically: `const X = Context.GenericTag<XShape>("X")`
becomes `class X extends Context.Tag("X")<X, XShape>() {}`, and call sites
(`yield* X`, `Layer.succeed(X, ...)`) do not change.

## Pitfalls

- Service methods whose types include `R`: the requirement leaks to every
  caller. Resolve dependencies when building the layer instead.
- Reusing a tag key string for two different tags: they collide at runtime.
- Creating layers inside functions or per request: destroys memoization and
  re-opens resources.
- `Layer.provide` vs `provideMerge` confusion: if a service "disappears" from
  the output type, you used `provide` where you meant `provideMerge`.
- Circular service dependencies: split the shared part into its own service.
- Heavy work in `Layer.effect` without a scope (sockets, timers): use
  `Layer.scoped` with `acquireRelease` so shutdown is clean.

## Done when

- Every service has a class tag (or `Effect.Service`) with a single live layer
  and, where tests need it, a test layer.
- There is one composed `MainLive` per entry point, provided once; `R` is
  `never` at `run*` / `ManagedRuntime`.
- Resources acquired in layers are released on shutdown (`Layer.scoped`,
  `runtime.dispose()`).

## Related skills

- effect-core-patterns - `Effect.gen`, running effects
- effect-resource-management - scopes and finalizers inside `Layer.scoped`
- effect-testing - test layers with `@effect/vitest` `it.layer`

Docs: <https://effect.website/docs/requirements-management/services/>,
<https://effect.website/docs/requirements-management/layers/>
