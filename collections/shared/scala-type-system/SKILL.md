---
name: scala-type-system
user-invocable: false
description: Model Scala 2 and Scala 3 types - variance, bounds, type classes with implicits vs given/using/extension, opaque types, union/intersection types, higher-kinded and path-dependent types. Use when designing typed Scala APIs or migrating implicits to Scala 3; not for effect-system specifics.
allowed-tools: []
---

# Model Scala types

Choose the smallest type model that makes the actual invariant clear. Inspect Scala 2 versus Scala 3 and library versions before choosing typeclass/implicit/contextual syntax. Preserve public type and binary compatibility when required. Explain the concrete benefit before adding higher-kinded, path-dependent, or advanced type-level machinery.

For a new Scala/JVM build in this environment, prefer Mill and its module-focused skills; preserve an existing build unless migration is requested.

Read only the relevant section of [references/language-patterns.md](references/language-patterns.md) for examples and detailed procedures:

- Introduction
- Generics and Type Parameters
- Variance Annotations
- Type Bounds
- Implicit Conversions and Parameters (Scala 2 vs Scala 3 mapping, anti-patterns)
- Type Classes
- Higher-Kinded Types
- Path-Dependent Types and Abstract Type Members
- Scala 3 Type Features
- Best Practices
- Common Pitfalls
- When to Use This Skill
- Resources

Verify the affected behavior with the project's compiler, tests, or runtime checks. A syntax illustration does not override the version or abstractions already chosen by the repository.
