# Rules

Apply to lines you add or change. Do not restyle unrelated code. A requested sweep stays inside the named files. One smell at a time.

When two sources disagree, follow [sources.md](sources.md). Do not pick a new winner here.

## Names

- The name says the role. It is searchable and pronounceable.
- No type prefix. No type word that repeats the declared type.
- One idea keeps the word the file already uses.
- No `utils`, `helpers`, `common`, or `manager` unless that boundary already exists for a real cross-cutting type.

## Functions

- One function does one job at one level of abstraction.
- Prefer under 20 lines. Do not pass 50. A longer function that is one straight sequence may stay.
- Stop at 3 or 4 parameters. Past that, introduce a parameter object.
- No flag argument. A boolean that selects a second behavior means two functions.
- No hidden side effect. A function is a command or a query.
- Guards sit at the top. The main path falls through at the bottom.
- Prefer a positive condition. Use `else` when only one branch may run.
- Boundary checks live in one place, at the trust boundary.
- Do not return null, empty, or a fake success from a caught failure.
- Do not swallow an exception.
- Do not mutate a parameter to smuggle a second result.
- Do not read and write the same collection in one pass.
- A variable sits next to its use. The caller sits above the callee.

## Data

- Use a value object, not a bare primitive, at a domain boundary.
- A data clump becomes one type.
- Keep data and the behavior that uses it in the same type.
- A base type does not know its derivatives.
- A type knows its direct collaborators only. Inject them through the constructor.
- No global mutable data. No hidden dependency. No tramp data.
- No shared mutation. Local obvious mutation may stay outside worxbend Scala.

## Conditionals

- A repeated switch or type test becomes polymorphism, or one sealed match.
- Scattered handling of one rare value becomes a special-case object.

## Comments

- Comment why, a warning, or a constraint the code cannot say.
- Delete a comment that restates the next line.
- Delete commented-out code.
- A temporary comment may stay while you untangle one function. Delete it before you finish.
- Do not delete comments as a class.

## Errors

- A recoverable failure is a value the caller must handle.
- An exception is for a defect, a broken invariant, a failed start, or a third-party API that cannot return a value.
- An absence type is only for real absence. Unwrap it next to the call. Do not use it to hide a failure.

## Tests

- One scenario per test. Assert the domain result.
- Add a test for an edge you discovered.
- Do not weaken a test to go green.

## Change hygiene

- Keep public compatibility unless the break is intentional and in scope.
- Warnings stay failures. Do not weaken compiler settings.
- No secret in source, tests, logs, errors, or docs.
- No unlabeled timeout, size, or retry. Put the unit in the name.
- Pass time, random, and ids in. Do not fetch them from deep domain logic.
- Load config once. Pass it through constructors.
- Clean the lines this change already touches. Do not clean unrelated code.
- Match the file. The formatter owns layout.

## Design costs to refuse

- Rigidity: one change forces unrelated edits.
- Fragility: one change breaks a distant behavior.
- Immobility: a useful part cannot move without its neighbors.
- Needless complexity: extra types with no caller today.
- Needless repetition: one rule written twice.
- Opacity: the reader cannot see the intent.

## Scala and worxbend

Apply when the file is Scala. In a worxbend repo, this section is mandatory for Scala.

`CODE_STYLE.md` wins when it disagrees with `SCALA_CODE_STYLE.md`. The older guide still supplies the numeric limits and the naming details the current guide does not restate. Do not apply the older brace, `Future`, `ZIO`, or `ZLayer` rules on current work.

### Layout

- Scalafmt owns formatting, import order, braces, blank lines, and trailing commas.
- The hard line limit is 120 columns.

### Names and files

- Types and constants use UpperCamelCase. Not ALL_CAPS.
- Methods and vals use lowerCamelCase.
- An acronym is a word: `HttpClient`.
- A predicate starts with `is`, `has`, or `can`, as in `isPaid`.
- A side-effecting operation uses an active verb and parentheses.
- A pure accessor omits parentheses.
- No JavaBean `get` or `set` prefix.
- The file name matches the primary type.
- One public type per file. A small sealed family may share the file.
- Packages are `com.worxbend.<product>.<concept>`.
- No `utils`, `helpers`, or `common` package unless the type is truly cross-cutting.

### Types

- Every public and protected member has an explicit result type.
- A domain id is an opaque type.
- Use a sealed enum. Never `scala.Enumeration`.
- A case class is data only. No `var` in a case class.
- The companion holds factories and constants.
- No default arguments.
- No lifecycle object stuffed with many optional fields.
- A DTO and a domain type stay apart. Convert at the boundary.
- Pick `List`, `Vector`, a non-empty collection, or a byte array from the data. Do not default every collection to `List`.
- Use immutable collections.

### Control and errors

- No `return`.
- No `null`.
- No `Option#get`.
- `Option` is for unexplained absence.
- `Either[DomainError, A]` is for a failure the caller must understand.
- Use a domain ADT once more than one reason exists.
- No `Either[Error, Option[A]]` unless the two layers mean different things.
- Matches on a closed set are exhaustive. No catch-all on that set.
- A for-comprehension sequences one type. Keep branches out of the generator list.
- An exception is only for a defect, a broken invariant, a failed start, or a third-party API that cannot return a value.

### Effects and structure

- Write direct style.
- Inject dependencies through the constructor.
- Use Ox for new concurrency.
- No raw threads. No ad hoc executors.
- Resource ownership is explicit. Release in reverse order.
- No wildcard import except a documented exception.
- Narrow the visibility first.
- Prefer methods under 20 lines. Do not exceed 50.
- Stop at 3 or 4 parameters.
- No shared mutable state. No `var` unless a written project rule relaxes it.

### Build, secrets, and config

- A Mill module states its Scala version and its `moduleDeps`.
- Tests use MUnit `ScalaTests`.
- Warnings are failures.
- No secret in source, tests, logs, errors, or docs.
- Load config once. Pass it through the constructor.
- Time, random, and ids are arguments.
