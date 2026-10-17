---
name: fp-backend
description: "fp-ts: structure Node.js/Deno backend services with ReaderTaskEither - dependencies as the Reader environment, typed domain errors, Prisma/transaction wrappers, Express/Hono adapters, and tests with mocked dependencies. Use when building or refactoring an fp-ts backend; not for Effect (use effect-dependency-injection)."
source: community
date_added: "2026-09-04"
version: 1.1.0
author: kadu
tags:
  - fp-ts
  - typescript
  - backend
  - functional-programming
  - node
  - deno
  - dependency-injection
  - reader-task-either
---

# fp-ts Backend Patterns

`ReaderTaskEither<R, E, A>` = "given dependencies `R`, asynchronously produce `A` or fail with `E`". Service functions return RTE values; the composition root supplies real dependencies once; tests supply fakes. No DI container, no classes required.

> fp-ts is in maintenance mode and its authors recommend Effect for new projects. If the codebase uses Effect, use effect-dependency-injection instead (Layer/Context replace Reader).

## Procedure

1. **Define narrow dependency types per service** (`type UserDeps = { db: Db; logger: Logger }`), not one global `Deps`. RTE intersects requirements as you compose (`RTE.flatMap` yields `R1 & R2`), so each function declares only what it uses.
2. **Define tagged domain errors** (see fp-errors). Keep infrastructure errors (`DatabaseError`) separate from domain errors (`NotFound`, `Conflict`) and map one to the other at the repository boundary.
3. **Wrap infrastructure once.** Repositories turn Prisma/HTTP/queue calls into `TaskEither` (`TE.tryCatch`) and expose RTE functions.
4. **Write services as RTE pipelines:** `RTE.ask<Deps>()` or `RTE.asks(d => d.db)` to read deps, `RTE.flatMap` to sequence, `RTE.tap` for logging/metrics, `RTE.orElse` for recovery.
5. **Build the composition root** at startup: create clients, assemble the `Deps` object, and fail fast on bad config.
6. **Adapt at the edge.** A route handler runs `service(input)(deps)()` and maps `Left` tags to HTTP responses in one exhaustive function.
7. **Test by supplying fake deps:** `await createUser(input)(fakeDeps)()` and assert on the `Either`.

```typescript
import { pipe } from 'fp-ts/function'
import * as RTE from 'fp-ts/ReaderTaskEither'
import * as TE from 'fp-ts/TaskEither'

type UserDeps = { users: { findById: (id: string) => TE.TaskEither<DbError, User | null> } }
type LogDeps = { logger: { info: (msg: string) => void } }
type NotFound = { _tag: 'NotFound'; id: string }

const getUser = (id: string): RTE.ReaderTaskEither<UserDeps & LogDeps, DbError | NotFound, User> =>
  pipe(
    RTE.asks((d: UserDeps) => d.users),
    RTE.flatMapTaskEither((users) => users.findById(id)),
    RTE.flatMap((u) => (u ? RTE.right(u) : RTE.left<UserDeps, NotFound>({ _tag: 'NotFound', id }))),
    RTE.tap((u) => RTE.asks((d: LogDeps) => d.logger.info(`loaded ${u.id}`)))
  )

// Edge: Express/Hono handler
const result = await getUser(req.params.id)(deps)()
```

## Decide

| Need | Use |
|---|---|
| Function needs deps and is async/fallible | `ReaderTaskEither` |
| Pure function of deps (config lookup) | `Reader` or just a parameter |
| No deps, async/fallible | `TaskEither` (fp-async) |
| Transaction spanning several repository calls | Pass a transaction-scoped client in `R` for the duration (see guide, Transaction Handling) |
| Request-scoped data (user, request id) | Extend `R` per request in middleware (guide, Request Context Pattern) |

## References

[references/detailed-guide.md](references/detailed-guide.md) - load the section you need:

- **Core Concepts / Service Layer Patterns** - RTE basics, service modules, composing services.
- **Functional Dependency Injection** - building the dependency object, running programs.
- **Database Operations** - Prisma wrappers and transaction handling.
- **Middleware Patterns** - Express and Hono middleware, request context.
- **Error Handling Patterns** - typed error hierarchy, error recovery.
- **Testing Strategies** - mocking deps, Testcontainers integration tests, property-based tests.
- **Quick Reference** - imports, RTE cheat sheet, service template.

Related: fp-errors (error types), fp-async (parallelism, retries), fp-taskeither-ref.

## Done when

- Each service function's type names only the deps it uses; the composition root is the only place that builds the full deps object.
- Infrastructure exceptions cannot escape a repository (every call is wrapped).
- Handlers map every error tag to a response with an exhaustive switch.
- Unit tests run services with fake deps and need no network or database.
