---
name: zio-reference
description: Use when writing ZIO Scala code — implementing services with ZLayer, handling typed errors vs defects, choosing concurrency primitives (Ref, Queue, Hub, STM, Semaphore), avoiding anti-patterns like blocking on ZIO threads, unsafe resource handling with ensuring, or overusing Task for business logic
license: MIT
compatibility: opencode,claude-code,copilot
---

# ZIO Coding Reference

## Core Concepts

- **Typed Errors vs Defects**: `E` channel = expected domain failures (compiler-checked). Defects = unexpected bugs captured in `Cause`, not in `E`.

> Deep dive: references/core-concepts.md

## Coding Rules

### Error Handling
> Deep dive: references/error-handling-deep-dive.md

- Model domain errors as sealed trait ADTs: `sealed trait UserError; case class NotFound(id: UUID) extends UserError`
- Use `ZIO.fail(NotFound(id))`, not `ZIO.fail(new Exception("not found"))`
- `orDie` shifts unrecoverable `Throwable` to defect channel: `ZIO.attempt(expr).orDie`
- `refineToOrDie[SpecificError]` keeps one error type, defects the rest
- Never swallow defects: `effect.tapDefect(c => ZIO.logErrorCause("Unexpected", c))`, not `effect.catchAllDefect(_ => ZIO.unit)`
- `mapError` unifies error hierarchies across layers
- `catchAll` for recovery, `foldZIO` to transform both paths
- Low-level: broad errors (`IOException`). High-level: refined domain ADTs or defects.
- Use `Either` only when errors are unrelated, to avoid widening `E` to `Any`

### Composition
- For-comprehensions for sequential composition:
  ```scala
  for { user <- getUser(id); _ <- notify(user) } yield ()
  ```
- `*>` (zipRight) / `<*` (zipLeft) when discarding one result:
  ```scala
  Console.printLine("Starting") *> runTask
  ```

### Dependencies (Service Pattern)
- Trait defines interface (methods return `IO[E, A]` with `R = Any`)
- Case class implements trait, gets dependencies via constructor
- Companion object provides `ZLayer`

### Resources
- Always use `ZIO.acquireRelease` or `ZIO.acquireReleaseWith` for resource cleanup, never `ensuring`
- `ZIO.scoped` for narrowest possible resource lifetime:
  ```scala
  ZIO.scoped { ZIO.acquireRelease(open)(r => ZIO.succeed(r.close())).flatMap(use) }
  ```

### Concurrency
> Deep dive: references/concurrency-and-fiber.md

- Prefer `foreachPar`, `zipPar`, `race` over manual `fork`/`join`
- Always `join` or `interrupt` any manually forked fiber
- Blocking I/O: `ZIO.attemptBlocking` or `ZIO.attemptBlockingIO`, never `ZIO.attempt`
- Custom operators: `ZIO.uninterruptibleMask(restore => setup *> restore(task) *> cleanup)`
- Don't wrap monolithic loops in `ZIO.succeed`: runtime can't interrupt inside them

## Anti-Patterns (Never Do These)
> Deep dive: references/anti-patterns.md

| Anti-Pattern | Correct |
|---|---|
| `Task[A]` for business logic | `IO[DomainError, A]` with sealed trait ADT |
| `val f = api(); ZIO.fromFuture(_ => f)` | `ZIO.fromFuture(ec => api()(ec))` |
| `ZIO.succeed(while(true) { ... })` | Recursive ZIO effect or `.forever` |
| `object Svc { def method(a: A): ZIO[Svc, E, B] = ZIO.serviceWithZIO(_.method(a)) }` | Call `ZIO.serviceWithZIO[Svc](_.method(a))` directly at call sites |

## Decision Guide: Which Abstraction?
> Deep dive: references/when-to-use-what.md

| Need | Use | Not |
|---|---|---|
| Service wiring + lifecycle | `ZLayer` | Manual instance passing |
| Single shared mutable state | `Ref` | `var`, `AtomicReference` |
| Multi-variable atomic updates | `STM` / `TRef` | Multiple `Ref` updates |
| Work distribution (one consumer per item) | `Queue` | `Hub` |
| Broadcast (all consumers get every item) | `Hub` | `Queue` |
| Retry with backoff / repeat on schedule | `Schedule` | Manual recursion |
| One-shot synchronization between fibers | `Promise` | `Queue`, `Ref` |
| Limit concurrent access | `Semaphore` | Manual counting |
| Incremental / infinite data processing | `ZStream` | `ZIO` returning `List` |
| Resource with finalization | `Scope` + `acquireRelease` | `ensuring` |
| Low-level fiber control | `Fiber` + `fork` | Default; prefer `foreachPar`/`zipPar` |

## Key Patterns
> More patterns: references/minimal-working-patterns.md | references/idioms.md

### Service Pattern (Repository variant)
```scala
trait UserRepo { def findById(id: UUID): IO[RepoError, Option[User]] }

case class PostgresUserRepo(ds: DataSource) extends UserRepo {
  def findById(id: UUID): IO[RepoError, Option[User]] =
    ZIO.attemptBlocking(query(ds, id)).mapError(DbError(_))
}

object UserRepo {
  val layer: ZLayer[DataSource, Nothing, UserRepo] = ZLayer.derive[PostgresUserRepo]
}
```

### Background Worker
```scala
def startWorker(queue: Queue[Job]): ZIO[Any, Nothing, Fiber.Runtime[Nothing, Nothing]] =
  queue.take.flatMap(job => process(job).ignoreLogged).forever.forkDaemon
```

### Retry with Backoff
```scala
val policy = Schedule.exponential(1.second) && Schedule.recurs(5)
ZIO.attempt(unstableCall()).retry(policy)
```

### Parallel with Limit
```scala
ZIO.foreachPar(urls)(fetch).withParallelism(10)
```

### HTTP Route (ZIO HTTP)
```scala
val route: Route[UserRepo, Nothing] =
  Method.GET / "users" / uuid("id") -> handler { (id: UUID, req: Request) =>
    ZIO.serviceWithZIO[UserRepo](_.findById(id)).map {
      case Some(user) => Response.json(user.toJson)
      case None       => Response.notFound
    }.orDie
  }
```
