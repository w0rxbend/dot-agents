---
name: fp-refactor
description: "fp-ts: decide whether and how far to move imperative TypeScript to fp-ts, then refactor step by step - try/catch to Either/TaskEither, null checks to Option, callbacks and Promise chains to TaskEither, class DI to Reader, loops to array combinators - with the 80/20 of what is worth adopting and when not to refactor. Use for migrating or reviewing an fp-ts adoption; not for Effect."
source: community
date_added: "2026-09-04"
version: 1.1.0
author: fp-ts-skills
tags:
  - fp-ts
  - refactoring
  - functional-programming
  - typescript
  - migration
  - either
  - option
  - task
  - reader
---

# Refactoring Imperative TypeScript to fp-ts

Refactor toward fp-ts only where it fixes real problem: lost error information, unchecked nulls feeding further logic, untestable hard-wired dependencies. Behavior must not change; types get more precise.

> fp-ts is in maintenance mode; authors recommend Effect for new projects. Before large migration *to* fp-ts, confirm with team that target is fp-ts (not Effect, not plain TypeScript). Skill assumes it is.

## 1. Decide whether to refactor

**Golden rule:** if FP makes code harder to read for team that maintains it, don't use it.

| Refactor when | Leave it when |
|---|---|
| Errors caught, turned into `null`/`false`; callers need reason | Two-line function with obvious `if` |
| Three or more nullable lookups feed further logic | One property path: `a?.b?.c ?? d` clearer than `Option` pipeline |
| Promise chain mixes `try/catch`, flags and early returns | Hot loops where intermediate arrays or closures were measured to matter |
| Classes exist only to hold injected dependencies | Third-party callbacks/interfaces you must implement as given |
| Validation should report every field error at once | Test code, where thrown assertion is clearest failure |
| | Team cannot yet read `pipe`/`flatMap` code and nobody will teach it |

## 2. Introduce in the 80/20 order

1. `pipe` for multi-step transformations.
2. `Option` for chained nullable lookups.
3. `Either` / `TaskEither` for operations whose failure callers must handle.
4. `map` / `flatMap` to work inside those types (`chain` is legacy name, fp-ts 2.14+).
5. Only then: Validation (error accumulation), `Reader`/`ReaderTaskEither` (DI), Do notation.

Prefer "middle ground": lambdas inside `pipe` over point-free helper soup (example: "The Middle Ground" in [references/pragmatic-80-20.md](references/pragmatic-80-20.md)).

## 3. Refactor safely

1. **Pin behavior first.** Add or run characterization tests for function and callers, failure paths included.
2. **Start at a boundary** (API client, repository, parser); wrap it once: `TE.tryCatch`, `E.tryCatch`, `O.fromNullable`.
3. **Add a bridge for unconverted callers** (`const legacyGet = (id: string) => pipe(get(id), TE.getOrElse((e) => () => Promise.reject(e)))()` returns plain Promise that rejects with typed error) so migration proceeds module by module.
4. **Change signature, let compiler list call sites**, update them one at a time.
5. **Replace stringly errors with tagged unions** (see fp-errors) as you go.
6. **Run tests after each function.** Remove bridges once all callers converted.

## References

- [references/pragmatic-80-20.md](references/pragmatic-80-20.md) - golden rule, quick wins (nested ternaries, try/catch, undefined returns, typed errors), readability rule with too-clever vs middle-ground examples, introducing FP to team. Read before proposing how much to change.
- [references/detailed-guide.md](references/detailed-guide.md) - before/after recipes. Load section you need: 1 try/catch to Either/TaskEither, 2 null checks to Option, 3 callbacks to Task, 4 class DI to Reader, 5 loops to combinators, 6 Promise chains to TaskEither (`Promise.all` to traverse), 7 common pitfalls, 8 gradual adoption strategies, 9 when NOT to refactor, plus imperative-to-fp-ts mapping table.

Related: fp-errors, fp-async, fp-backend, fp-data-transforms; operator cheat sheets in fp-errors (`references/either-cheatsheet.md`), fp-async (`references/taskeither-cheatsheet.md`) and fp-data-transforms (`references/option-cheatsheet.md`, `references/pipe-cheatsheet.md`).

## Done when

- Characterization tests pass unchanged before and after.
- Each converted function's signature states its failure/absence (`Either`, `TaskEither`, `Option`); no caller unwraps with `as` or `!`.
- No `Task`/`TaskEither` is created and never invoked (search for pipelines without trailing `()` at edge).
- Diff reads as simpler to team member who did not write it; if not, roll back that part.
