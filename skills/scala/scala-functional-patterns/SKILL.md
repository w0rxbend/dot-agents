---
name: scala-functional-patterns
user-invocable: false
description: Apply functional patterns in plain Scala 2/3 - immutability, higher-order functions, pattern matching, ADTs (sealed traits or Scala 3 enums), Option/Either/Try, for-comprehensions and composition. Use for pure domain logic; follow the project's ZIO, Cats Effect or Ox conventions for effects.
allowed-tools: []
---

# Apply Scala functional patterns

Use project's chosen abstractions for pure transformations, effect boundaries, errors, concurrency. Direct-style Ox/Tapir, ZIO, Cats Effect and plain Scala are distinct established choices. Do not migrate between them merely to apply a pattern. Check Scala/library versions; use their supported syntax.

New Scala/JVM build here: prefer Mill and its module-focused skills. Keep existing build unless migration is requested.

Read only relevant section of [references/language-patterns.md](references/language-patterns.md) for examples and procedures:

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

Verify affected behavior with project's compiler, tests or runtime checks. A syntax example does not override the version or abstractions the repository already chose.
