---
name: scala-functional-patterns
user-invocable: false
description: Apply functional patterns in plain Scala 2/3 - immutability, higher-order functions, pattern matching, ADTs (sealed traits or Scala 3 enums), Option/Either/Try, for-comprehensions and composition. Use for pure domain logic; follow the project's ZIO, Cats Effect or Ox conventions for effects.
allowed-tools: []
---

# Apply Scala functional patterns

Use the project's chosen abstractions for pure transformations, effect boundaries, errors, and concurrency. Direct-style Ox/Tapir, ZIO, Cats Effect, and plain Scala are distinct established choices; do not migrate between them merely to apply a functional pattern. Inspect the Scala/library versions and use their supported syntax.

For a new Scala/JVM build in this environment, prefer Mill and its module-focused skills; preserve an existing build unless migration is requested.

Read only the relevant section of [references/language-patterns.md](references/language-patterns.md) for examples and detailed procedures:

- Introduction
- Immutability and Pure Functions
- Higher-Order Functions
- Pattern Matching
- Algebraic Data Types (ADTs)
- Option and Either Monads
- For-Comprehensions
- Function Composition and Combinators
- Best Practices
- Common Pitfalls
- When to Use This Skill
- Scala Version and Effect-System Notes
- Resources

Verify the affected behavior with the project's compiler, tests, or runtime checks. A syntax illustration does not override the version or abstractions already chosen by the repository.
