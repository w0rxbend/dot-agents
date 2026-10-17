---
name: fp-react
description: "fp-ts: patterns for React 18/19 and Next.js - Option state, Either form validation, TaskEither data fetching, RemoteData for loading/error/success UI, referential stability, and dependency injection via context. Use when a React codebase already uses fp-ts; not for Effect, and not needed when plain hooks plus a data-fetching library suffice."
source: community
date_added: "2026-09-04"
version: 2.1.0
author: fp-ts-skills
tags: [fp-ts, react, typescript, hooks, state-management, forms, data-fetching, remote-data, react-19, next-js]
---

# fp-ts in React

Use fp-ts types where they make UI states explicit: a value that may be missing, a form with several independent errors, a request that can be idle, loading, failed or loaded. Keep components readable; convert to plain values at the render boundary.

> fp-ts is in maintenance mode and its authors recommend Effect for new projects. In a new React app, prefer the data library the project already uses (TanStack Query, SWR, React 19 `use`) and plain TypeScript unions; add fp-ts only if the codebase is already on it.

## When to use what

| Situation | Use |
|---|---|
| Value might not exist | `Option<T>` (or `T \| null` if no composition follows) |
| Operation might fail (sync) | `Either<E, A>` |
| Async operation might fail | `TaskEither<E, A>` |
| Need idle/loading/error/success UI | `RemoteData<E, A>` (`@devexperts/remote-data-ts`) or a tagged union |
| Form with multiple field errors | `Either` with `getApplicativeValidation` |
| Dependency injection | React context providing deps + `ReaderTaskEither` |
| fp-ts values in effect/memo dependency arrays | `useMemo`, depend on the raw value, or `fp-ts-react-stable-hooks` |

## Procedure

1. **Keep fp-ts out of JSX.** Fold to plain values right before rendering: `O.match(() => <Empty />, (u) => <Profile user={u} />)`.
2. **Model async state as one value**, not three booleans. `RemoteData` or `{ _tag: 'Loading' } | { _tag: 'Failure'; error } | { _tag: 'Success'; data }` makes impossible states unrepresentable.
3. **Guard effects against stale responses.** A `useEffect` that runs a `TaskEither` must ignore results after cleanup (flag or `AbortController`), or a slow earlier request overwrites a newer one.
4. **Mind referential equality.** `O.some(x)` creates a new object each render; never put freshly built `Option`/`Either` values in dependency arrays.
5. **Validate forms with accumulation** so the user sees every field error at once, then map errors to a `Record<field, string[]>` for display.
6. **React 19 / Next.js:** server actions and `useActionState` take plain serializable data; run the `TaskEither` inside the action and return a plain `{ ok, errors }` object.

## References

[references/detailed-guide.md](references/detailed-guide.md) - load the section you need: 1 Option state, 2 form validation, 3 data fetching with TaskEither (hook, chaining, parallel), 4 RemoteData, 5 referential stability, 6 DI with context and testing, 7 React 19 patterns (`use`, `useActionState`, `useOptimistic`), 8 render cheat sheet, plus a library list.

Related: fp-errors (error modeling), fp-async (parallel requests, retries), fp-option-ref / fp-either-ref.

## Done when

- Components render from folded plain values; no `O.isSome` checks scattered across JSX.
- Async UI has explicit loading, error and success branches, and stale responses are ignored.
- No fp-ts objects created during render appear in dependency arrays.
- Form errors are shown for every invalid field at once and tested with a multi-error input.
