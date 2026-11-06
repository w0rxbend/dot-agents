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
| `pipe` | Have value, want result |
| `flow` | Want named, reusable function (point-free) |
| Plain method chaining | Native array methods already read well (`xs.filter(...).map(...)`) |

## With fp-ts data-last operators

fp-ts operators are curried, data-last, so they slot into `pipe`:

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

- `pipe` is typed for up to 19 functions after start value. Split long pipelines into named steps anyway.
- Type inference flows left to right: annotate first lambda in `flow`, or input value in `pipe`.
- Debug pipeline by inserting `(x) => { console.log(x); return x }` (or `O.tap` / `E.tap` / `TE.tap` for wrapped values).
- If pipeline reads worse than imperative version, keep imperative one (fp-refactor, "When NOT to refactor").
