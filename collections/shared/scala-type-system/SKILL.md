---
name: scala-type-system
user-invocable: false
description: Use when scala's advanced type system including generics, variance, type bounds, implicit conversions, type classes, higher-kinded types, path-dependent types, and abstract type members for building type-safe, flexible APIs.
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
- Implicit Conversions and Parameters
- Type Classes
- Higher-Kinded Types
- Path-Dependent Types and Abstract Type Members
- Best Practices
- Common Pitfalls
- When to Use This Skill
- Resources

Verify the affected behavior with the project's compiler, tests, or runtime checks. A syntax illustration does not override the version or abstractions already chosen by the repository.
