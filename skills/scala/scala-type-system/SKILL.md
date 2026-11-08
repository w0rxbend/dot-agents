---
name: scala-type-system
user-invocable: false
description: Model Scala 2 and Scala 3 types - variance, bounds, type classes with implicits vs given/using/extension, opaque types, union/intersection types, higher-kinded and path-dependent types. Use when designing typed Scala APIs or migrating implicits to Scala 3; not for effect-system specifics.
allowed-tools: []
---

# Model Scala types

Pick smallest type model that makes real invariant clear. Check Scala 2 versus Scala 3 and library versions before choosing typeclass/implicit/contextual syntax. Keep public type and binary compatibility when required. Explain concrete benefit before adding higher-kinded, path-dependent or advanced type-level machinery.

New Scala/JVM build here: prefer Mill and its module-focused skills. Keep existing build unless migration requested.

For examples and detailed procedures, read only relevant section of [references/language-patterns.md](references/language-patterns.md):

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

Verify affected behavior with project's compiler, tests or runtime checks. Syntax examples do not override version or abstractions repository already chose.
