---
name: fp-option-ref
description: "fp-ts cheat sheet: Option operators for values that may be absent - create, map, flatMap, filter, extract, convert to Either. Use for a quick lookup while writing fp-ts code; not for Effect (Effect has its own Option module), and plain ?. / ?? is often enough."
risk: none
source: community
date_added: "2026-09-04"
version: 1.1.0
tags: [fp-ts, option, nullable, maybe, quick-reference]
---

# Option Quick Reference (fp-ts 2.x)

`Option<A>` is `Some<A>` or `None`. Use it when absence is a normal outcome and you want to compose several steps over it. `chain` is a legacy alias of `flatMap` (fp-ts 2.14+).

## When Option is worth it

| Situation | Use |
|---|---|
| One property path with a default | `user?.profile?.name ?? 'Guest'` - optional chaining is clearer |
| Several lookups that each may miss, then a transformation | `Option` pipeline |
| Function result where "not found" is expected | Return `Option<A>` instead of `A \| undefined` |
| Caller needs to know why it is missing | `Either` (fp-either-ref) |

## Create

```typescript
import * as O from 'fp-ts/Option'

O.some(5)
O.none
O.fromNullable(x)                              // null/undefined -> None
O.fromPredicate((n: number) => n > 0)(x)       // false -> None
O.tryCatch(() => JSON.parse(raw))              // throws -> None
```

## Transform

```typescript
O.map(f)          // f cannot miss
O.flatMap(f)      // f returns Option
O.filter(pred)    // None when pred is false
O.alt(() => other) // first Some wins
```

## Extract and convert

```typescript
O.getOrElse(() => fallback)        // A
O.match(() => onNone, (a) => onSome(a))
O.toNullable(opt) / O.toUndefined(opt)
E.fromOption(() => 'not found')(opt) // Option -> Either (import * as E from 'fp-ts/Either')
```

## Common patterns

```typescript
import { pipe } from 'fp-ts/function'
import * as O from 'fp-ts/Option'
import * as A from 'fp-ts/Array'
import * as R from 'fp-ts/Record'

// Safe first element and record lookup
const firstName = pipe(users, A.head, O.map((u) => u.name), O.getOrElse(() => 'No users'))
const port = pipe(R.lookup('PORT', env), O.flatMap((s) => O.fromPredicate((n: number) => n > 0)(Number(s))))

// Several optional parts that must all be present
const fullName = pipe(
  O.Do,
  O.apS('first', O.fromNullable(user.firstName)),
  O.apS('last', O.fromNullable(user.lastName)),
  O.map(({ first, last }) => `${first} ${last}`)
)
```

More context: fp-data-transforms (null-safe access section) and fp-refactor (null checks to Option).
