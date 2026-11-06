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

Use fp-ts types where they make UI states explicit; keep components readable.

> fp-ts is in maintenance mode; its authors recommend Effect for new projects. New React app: prefer project's existing data library (TanStack Query, SWR, React 19 `use`) and plain TypeScript unions. Add fp-ts only if codebase already uses it.

## When to use what

| Situation | Use |
|---|---|
| Value might not exist | `Option<T>` (or `T \| null` if no composition follows) |
| Operation might fail (sync) | `Either<E, A>` |
| Async operation might fail | `TaskEither<E, A>` |
| Idle/loading/error/success UI | `RemoteData<E, A>` (`@devexperts/remote-data-ts`) or tagged union |
| Form with multiple field errors | `Either` with `getApplicativeValidation` |
| Dependency injection | React context with deps + `ReaderTaskEither` |
| fp-ts values in effect/memo dependency arrays | `useMemo`, depend on raw value, or `fp-ts-react-stable-hooks` |

## Procedure

1. **Keep fp-ts out of JSX.** Fold to plain values right before render: `O.match(() => <Empty />, (u) => <Profile user={u} />)`.
2. **Model async state as one value**, not three booleans. `RemoteData` or `{ _tag: 'Loading' } | { _tag: 'Failure'; error } | { _tag: 'Success'; data }` makes impossible states unrepresentable.
3. **Guard effects against stale responses.** `useEffect` running `TaskEither` must ignore results after cleanup (flag or `AbortController`). Otherwise slow earlier request overwrites newer one.
4. **Mind referential equality.** `O.some(x)` creates new object each render. Never put freshly built `Option`/`Either` values in dependency arrays.
5. **Validate forms with accumulation** so user sees every field error at once. Then map errors to `Record<field, string[]>` for display.
6. **React 19 / Next.js:** server actions and `useActionState` take plain serializable data. Run `TaskEither` inside action; return plain `{ ok, errors }` object.

## References

[references/detailed-guide.md](references/detailed-guide.md) - load section you need: 1 Option state, 2 form validation, 3 data fetching with TaskEither (hook, chaining, parallel), 4 RemoteData, 5 referential stability, 6 DI with context and testing, 7 React 19 patterns (`use`, `useActionState`, `useOptimistic`), 8 render cheat sheet, plus library list.

Related: fp-errors (error modeling), fp-async (parallel requests, retries), Option/Either cheat sheets in fp-data-transforms (`references/option-cheatsheet.md`) and fp-errors (`references/either-cheatsheet.md`).

## Done when

- Components render from folded plain values. No `O.isSome` checks scattered across JSX.
- Async UI has explicit loading, error and success branches. Stale responses ignored.
- Dependency arrays hold no fp-ts objects created during render.
- Form shows errors for every invalid field at once; tested with multi-error input.
