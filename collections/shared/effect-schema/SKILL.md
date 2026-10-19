---
name: effect-schema
user-invocable: false
description: "Effect-TS v3: define schemas with effect/Schema (Struct, Union, Class, TaggedError, brands), decode unknown input and encode output, write filters and transformations, and format ParseError messages. Use when validating or transforming data at a boundary in Effect code; for fp-ts io-ts or Zod codebases keep their existing validator."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Effect Schema

> **Version:** examples target the `Schema` module bundled in `effect` 3.10+
> (`import { Schema } from "effect"`, checked against 3.22). Projects on older
> releases import the standalone `@effect/schema` package with the same
> concepts; keep that import only in an existing older project. Effect 4
> reworks Schema (new modules and signatures); follow its migration guide
> rather than assuming these signatures carry over. Check the installed
> version first.

A `Schema<Type, Encoded, R>` describes both a runtime validator and a two-way
transformation: **decode** turns `Encoded` (wire/JSON shape) into `Type`
(domain shape); **encode** goes back. For plain validation `Type = Encoded`.

## Workflow

1. Define the schema once, next to the domain type; derive the type with
   `typeof X.Type` (or `Schema.Schema.Type<typeof X>`) instead of writing an
   interface by hand.
2. Decode at the boundary (HTTP body, env, message, file) with
   `Schema.decodeUnknown` inside Effect code, or `decodeUnknownSync` /
   `decodeUnknownEither` outside it.
3. Encode when sending data out (`Schema.encode`), so transformations (Date ->
   string) run in reverse.
4. Turn `ParseError` into a domain error or an HTTP 400 with a formatted
   message.

## Core schemas

```typescript
import { Schema } from "effect"

const Status = Schema.Literal("pending", "approved", "rejected")

const Address = Schema.Struct({
  street: Schema.String,
  city: Schema.String
})

const User = Schema.Struct({
  id: Schema.String,
  name: Schema.String.pipe(Schema.minLength(1)),
  age: Schema.Number.pipe(Schema.int(), Schema.between(0, 150)),
  email: Schema.optional(Schema.String), // email?: string | undefined
  role: Schema.optionalWith(Schema.String, { default: () => "member" }), // filled on decode
  status: Status,
  address: Address,
  tags: Schema.Array(Schema.String),
  scores: Schema.Record({ key: Schema.String, value: Schema.Number }),
  point: Schema.Tuple(Schema.Number, Schema.Number),
  nickname: Schema.NullOr(Schema.String)
})

type User = typeof User.Type
type UserJson = typeof User.Encoded

// Discriminated union: TaggedStruct adds a `_tag` literal field
const Shape = Schema.Union(
  Schema.TaggedStruct("Circle", { radius: Schema.Number }),
  Schema.TaggedStruct("Rect", { width: Schema.Number, height: Schema.Number })
)

// Reuse and reshape
const UserSummary = User.pipe(Schema.pick("id", "name"))
const UserPatch = Schema.partial(User.pipe(Schema.omit("id")))
const WithTimestamps = Schema.Struct({ ...Address.fields, updatedAt: Schema.Date })
```

| Need | v3 API |
| --- | --- |
| Optional key | `Schema.optional(S)`; `Schema.optionalWith(S, { default, exact, nullable })` |
| Nullable value | `Schema.NullOr(S)`, `Schema.UndefinedOr(S)`, `Schema.NullishOr(S)` |
| Optional tuple element | `Schema.Tuple(A, Schema.optionalElement(B))` |
| Non-empty array | `Schema.NonEmptyArray(S)` |
| Recursive schema | `Schema.suspend(() => Node)` with an explicit type annotation |
| Extend a struct | spread `X.fields` into a new `Struct`, or `Schema.extend` |

## Built-in transformations

| Schema | Encoded -> Type |
| --- | --- |
| `Schema.NumberFromString` | `"42"` -> `42` |
| `Schema.Date` | ISO string -> valid `Date` |
| `Schema.DateFromSelf` | `Date` -> `Date` (no transformation) |
| `Schema.BooleanFromString` | `"true"` -> `true` |
| `Schema.parseJson(S)` | JSON string -> decoded `S` |
| `Schema.Trim`, `Schema.Lowercase` | normalized string |
| `Schema.Redacted(S)` | value hidden from logs |
| `Schema.BigInt` | string -> `bigint` |

Rule of thumb: the `...FromSelf` variants validate an already-typed value;
the plain names decode from a JSON-friendly encoding.

## Filters, brands, custom transformations

```typescript
import { ParseResult, Schema } from "effect"

// Filter: return true, or a string / false to fail with a message
const Password = Schema.String.pipe(
  Schema.minLength(8),
  Schema.filter((s) => (/[A-Z]/.test(s) && /[0-9]/.test(s)) || "needs an uppercase letter and a digit")
)

// Cross-field check on a struct
const Signup = Schema.Struct({ password: Password, confirm: Schema.String }).pipe(
  Schema.filter((f) => f.password === f.confirm || "passwords must match")
)

// Brand: nominal type so a raw string cannot be passed as a UserId
const UserId = Schema.String.pipe(Schema.pattern(/^usr_[a-z0-9]+$/), Schema.brand("UserId"))
type UserId = typeof UserId.Type

// Total transformation (cannot fail)
const CsvList = Schema.transform(Schema.String, Schema.Array(Schema.String), {
  strict: true,
  decode: (s) => s.split(",").map((x) => x.trim()),
  encode: (xs) => xs.join(",")
})

// Fallible transformation
const UrlFromString = Schema.transformOrFail(Schema.String, Schema.instanceOf(URL), {
  strict: true,
  decode: (s, _, ast) => {
    try {
      return ParseResult.succeed(new URL(s))
    } catch {
      return ParseResult.fail(new ParseResult.Type(ast, s, `invalid URL: ${s}`))
    }
  },
  encode: (u) => ParseResult.succeed(u.toString())
})
```

## Classes and errors

```typescript
import { Effect, Schema } from "effect"

class Person extends Schema.Class<Person>("Person")({
  name: Schema.String,
  born: Schema.Date
}) {
  get age() {
    return new Date().getFullYear() - this.born.getFullYear()
  }
}

// Serializable tagged error, usable with Effect.catchTag
class UserNotFound extends Schema.TaggedError<UserNotFound>()("UserNotFound", {
  id: Schema.String
}) {}

const p = Schema.decodeUnknownSync(Person)({ name: "Ada", born: "1815-12-10" })
// p instanceof Person, p.born is a Date

const find = (id: string) => Effect.fail(new UserNotFound({ id }))
```

Use `Schema.TaggedClass` / `Schema.TaggedRequest` for tagged data and RPC
requests.

## Decoding and handling errors

```typescript
import { Effect, Either, ParseResult, Schema } from "effect"

const Body = Schema.Struct({ name: Schema.String, age: Schema.NumberFromString })

// Inside Effect: fails with ParseError (tag "ParseError")
const handler = (raw: unknown) =>
  Schema.decodeUnknown(Body)(raw, { errors: "all", onExcessProperty: "error" }).pipe(
    Effect.catchTag("ParseError", (e) =>
      Effect.fail({ status: 400, message: ParseResult.TreeFormatter.formatErrorSync(e) })
    )
  )

// Outside Effect
const result = Schema.decodeUnknownEither(Body)({ name: "Ada", age: "x" })
if (Either.isLeft(result)) {
  // [{ _tag: "Transformation", path: ["age"], message: 'Unable to decode "x" into a number' }]
  console.log(ParseResult.ArrayFormatter.formatErrorSync(result.left))
}

// Throws on failure: scripts and tests only
const ok = Schema.decodeUnknownSync(Body)({ name: "Ada", age: "36" }) // { name: "Ada", age: 36 }
```

| Option | Effect |
| --- | --- |
| `errors: "all"` | report every issue, not just the first (good for forms) |
| `onExcessProperty: "error"` | reject unknown keys (default: strip them) |
| `onExcessProperty: "preserve"` | keep unknown keys |

`ParseError` has an `issue` tree, not an `errors` array; use
`TreeFormatter` for humans and `ArrayFormatter` for field-level API errors.

## Interop

- `JSONSchema.make(S)` produces JSON Schema (for OpenAPI or LLM tools).
- `Schema.standardSchemaV1(S)` (v3.13+) exposes a Standard Schema validator
  for libraries that accept one (form libraries, tRPC, etc.).
- `Arbitrary.make(S)` produces fast-check arbitraries for property tests.
- `Schema.Config` reads and validates a config value with a schema.

## Pitfalls

- Using `decodeUnknownSync` in request handlers: it throws; use the Effect or
  Either variant.
- Declaring a TS interface and a schema separately: they drift. Derive the
  type from the schema.
- Using `Schema.Date` when the input is already a `Date` (use `DateFromSelf`)
  or vice versa.
- Encoding with `JSON.stringify(value)` instead of `Schema.encode`: skips
  reverse transformations (Dates, brands, bigint).
- Union order: put the more specific member first when members overlap
  (prefer tagged unions, which are unambiguous).
- Old `@effect/schema` snippets: `Schema.filter` predicates returning
  `{ message, test }` objects, `ParseError.errors`, and some renamed
  combinators do not exist in v3; check the API reference.

## Done when

- Every external input is decoded through a schema before use, with
  `errors: "all"` where users need all messages.
- Domain types are derived from schemas (`typeof S.Type`).
- Outgoing data is encoded with the same schema; round-trip tests
  (`encode(decode(x))`) pass for transforming schemas.

## Related skills

- effect-error-handling - mapping `ParseError` to domain errors
- effect-core-patterns - running decode effects
- effect-testing - property tests with `Arbitrary`

Docs: <https://effect.website/docs/schema/introduction/>
