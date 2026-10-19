---
name: scala-collections
user-invocable: false
description: Choose and transform Scala 2.13/3 collections - List/Vector/Array, Set/Map, transformations, views and LazyList, parallel collections (separate module on 2.13+), and 2.12-to-2.13 migration. Use when writing, reviewing or porting collection-heavy Scala code.
allowed-tools: []
---

# Work with Scala collections

Choose collections by ownership, ordering, access pattern, laziness, and measured cost. Inspect the repository's Scala version before adapting syntax or library methods; Scala 2.13 and Scala 3 share much of the collections library, while older Scala 2 APIs can differ. Preserve public collection types and caller behavior. Avoid incidental mutable-to-immutable or parallelization rewrites.

For a new Scala/JVM build in this environment, prefer Mill and its module-focused skills; preserve an existing build unless migration is requested.

Read only the relevant section of [references/language-patterns.md](references/language-patterns.md) for examples and detailed procedures:

- Introduction
- Immutable vs Mutable Collections
- Sequences: List, Vector, and Array
- Sets and Maps
- Collection Transformations
- For-Comprehensions with Collections
- Lazy Evaluation and Views
- Parallel Collections
- Scala 2.13 / Scala 3 Collections Migration Notes
- Best Practices
- Common Pitfalls
- When to Use This Skill
- Resources

Verify the affected behavior with the project's compiler, tests, or runtime checks. A syntax illustration does not override the version or abstractions already chosen by the repository.
