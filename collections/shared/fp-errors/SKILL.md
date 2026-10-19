---
name: fp-errors
description: "fp-ts: model failures as values with Either and TaskEither - tagged error unions, converting throwing/nullable/Promise code at boundaries, fail-fast vs accumulated validation, and mapping errors to responses. Use when designing or refactoring error handling in an fp-ts codebase; not for Effect (use effect-error-handling)."
source: community
date_added: "2026-09-04"
version: 1.1.0
author: kadu
tags:
  - fp-ts
  - error-handling
  - either
  - task-either
  - typescript
  - validation
  - practical
---

# Error Handling as Values with fp-ts

This is the canonical fp-ts skill for *what an error is and where it is handled*. Return expected failures as `Either` (sync) or `TaskEither` (async) so the compiler tracks them; keep `throw` for bugs and truly unrecoverable states. For async flow control (parallelism, retries, fallbacks) use fp-async.

> fp-ts is in maintenance mode and its authors recommend Effect for new projects. For Effect code use effect-error-handling.

## Procedure

1. **List the expected failures** of the operation (not found, validation, conflict, upstream unavailable). Each becomes a tagged type: `{ _tag: 'NotFound'; id: string }`. Avoid bare `string` and `Error` for domain errors - callers cannot branch on them.
2. **Convert at the boundary** where foreign code enters:
   - throwing sync code: `E.tryCatch(() => JSON.parse(s), toParseError)`
   - nullable: `E.fromNullable(notFound(id))(value)`
   - Promise: `TE.tryCatch(() => client.get(id), toUpstreamError)`
3. **Compose with `flatMap`.** It stops at the first `Left` and unions error types (`chain`/`chainW` are the legacy names, fp-ts 2.14+).
4. **Choose fail-fast or accumulate:** `flatMap`/`Do`+`bind` stop at the first error; `E.getApplicativeValidation(NEA.getSemigroup())` + `sequenceS` collect all errors (forms, config files).
5. **Handle once, at the edge.** `match`/`fold` into an HTTP status, CLI exit code or UI state. Use an exhaustive `switch (e._tag)` so a new error tag fails compilation until handled.
6. **Do not swallow.** `getOrElse(() => default)` is a decision to discard the error; log or map it first when it matters.

## Error type design

```typescript
type NotFound = { readonly _tag: 'NotFound'; readonly id: string }
type Invalid = { readonly _tag: 'Invalid'; readonly issues: ReadonlyArray<string> }
type Upstream = { readonly _tag: 'Upstream'; readonly cause: unknown }
type GetUserError = NotFound | Invalid | Upstream

const toStatus = (e: GetUserError): number => {
  switch (e._tag) {
    case 'NotFound': return 404
    case 'Invalid': return 400
    case 'Upstream': return 502
  }
}
```

| Choice | Prefer when |
|---|---|
| `Option` | Absence is normal and needs no reason |
| `Either<E, A>` | Sync failure the caller must branch on |
| `TaskEither<E, A>` | Async failure the caller must branch on |
| Validation (accumulating) | User input with several independent fields |
| `throw` / defect | Programmer error, broken invariant, startup misconfiguration |

## References

[references/either-cheatsheet.md](references/either-cheatsheet.md) is a one-page Either operator cheat sheet (create, transform, flatMap, accumulate, extract) for quick lookups.

[references/detailed-guide.md](references/detailed-guide.md) has before/after code for every step. Load the section you need:

| Need | Section |
|---|---|
| Why exceptions hide failures; the values approach | 1-2 |
| Chaining fallible steps, Do notation, widening error types | 3 |
| Collecting all validation errors, field-level form errors | 4 |
| Promise code to TaskEither, executing and folding | 5 |
| Converting nullable / throwing / Promise code and back (escape hatches) | 6 |
| Parsing input, full API call, lists where some items fail, bulk partial success | Real Scenarios |

Operator lookups: [references/either-cheatsheet.md](references/either-cheatsheet.md) here, and the TaskEither cheat sheet in fp-async (`references/taskeither-cheatsheet.md`). Moving a whole codebase over gradually: fp-refactor.

## Done when

- Every expected failure is a tagged type in a function signature; no `catch (e) { return null }`.
- Boundaries (JSON, DB, HTTP, env) convert to `Either`/`TaskEither` exactly once.
- Error handling is exhaustive (`switch` on `_tag` with no `default`), and each tag has a test.
