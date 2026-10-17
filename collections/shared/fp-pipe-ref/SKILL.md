---
name: fp-pipe-ref
description: "fp-ts cheat sheet: pipe and flow for composing functions and data-last fp-ts operators. Use for a quick lookup on building readable pipelines; not for Effect (Effect has its own pipe and .pipe method)."
risk: none
source: community
date_added: "2026-09-04"
version: 1.1.0
tags: [fp-ts, pipe, flow, composition, quick-reference]
---

# pipe and flow Quick Reference (fp-ts 2.x)

## pipe: transform a value now

```typescript
import { pipe } from 'fp-ts/function'

// pipe(a, f, g, h) === h(g(f(a)))
const words = pipe(
  '  hello world  ',
  (s) => s.trim(),
  (s) => s.toUpperCase(),
  (s) => s.split(' ')
) // ['HELLO', 'WORLD']
```

## flow: build a reusable function

```typescript
import { flow } from 'fp-ts/function'

const normalize = flow(
  (s: string) => s.trim(), // the first function's parameter needs a type annotation
  (s) => s.toUpperCase(),
  (s) => s.split(' ')
)
normalize('  foo bar  ') // ['FOO', 'BAR']
```

| Use | When |
|---|---|
| `pipe` | You have the value and want the result |
| `flow` | You want a named, reusable function (point-free) |
| Plain method chaining | Native array methods already read well (`xs.filter(...).map(...)`) |

## With fp-ts data-last operators

fp-ts operators are curried and take the data last, so they slot into `pipe`:

```typescript
import * as O from 'fp-ts/Option'
import * as A from 'fp-ts/Array'

const email = pipe(O.fromNullable(user), O.map((u) => u.email), O.getOrElse(() => 'no email'))

const getActiveNames = flow(
  A.filter((u: User) => u.active),
  A.map((u) => u.name)
)
getActiveNames(users)
```

## Gotchas

- `pipe` is typed for up to 19 functions after the start value; long pipelines read better split into named steps anyway.
- Type inference flows left to right: annotate the first lambda in `flow`, or the input value in `pipe`.
- Debug a pipeline by inserting `(x) => { console.log(x); return x }` (or `O.tap` / `E.tap` / `TE.tap` for wrapped values).
- If a pipeline is harder to read than the imperative version, keep the imperative version (fp-refactor, "When NOT to refactor").
