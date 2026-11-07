---
name: scala-collections
user-invocable: false
description: Choose and transform Scala 2.13/3 collections - List/Vector/Array, Set/Map, transformations, views and LazyList, parallel collections (separate module on 2.13+), and 2.12-to-2.13 migration. Use when writing, reviewing or porting collection-heavy Scala code.
allowed-tools: []
---

# Work with Scala collections

Choose collections by ownership, ordering, access pattern, laziness, measured cost. Check repository's Scala version before adapting syntax or library methods. Scala 2.13 and Scala 3 share much of collections library; older Scala 2 APIs can differ. Preserve public collection types and caller behavior. Avoid incidental mutable-to-immutable or parallelization rewrites.

New Scala/JVM build here: prefer Mill and its module-focused skills. Keep existing build unless migration requested.

Read only relevant section of [references/language-patterns.md](references/language-patterns.md) for examples and procedures:

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
- Resources

Verify affected behavior with project's compiler, tests or runtime checks. Syntax illustrations do not override repository's chosen version or abstractions.
