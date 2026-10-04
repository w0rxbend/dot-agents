---
name: mill-build-logic
description: Implement tracked Mill tasks for code generation, resources, external tools, and reusable build logic with correct inputs, destinations, caching, and task types.
license: MIT
---

# Tracked custom build logic

Read [tasks.md](references/tasks.md) for task-kind selection and dependency graph invariants. Read [generation.md](references/generation.md) for generated sources/resources, generator-module boundaries, and validation. `assets/codegen` is a tested programmable Mill 1.1.10 example.

Choose programmable configuration when build behavior needs computation; ordinary values can remain declarative. Use tracked `Task.Source`/`Task.Sources` inputs, `Task.Input` for changing external inputs, cached `Task` for reproducible artifacts, and `Task.Command` for actions that should execute when invoked. Use `Task.Worker` only for deliberately reusable in-memory machinery.

Task calls define dependencies. Keep dependency topology visible to Mill; use `Task.traverse` for a known collection of tasks instead of invoking dependencies through arbitrary loops/lambdas the task macro cannot analyze. Write artifacts into the current `Task.dest` and return `PathRef` after writing. Append to `super.generatedSources()` / `super.resources()` when preserving normal inputs.

Do not read untracked files/environment, embed machine-specific paths, write into another task's destination, mutate sources during compile, or treat Mill's filesystem sandbox as a security boundary. Build initialization should define the graph without performing I/O side effects. Separate a code generator into an upstream module if invoking the consumer's compiled code would create a cycle.

Prove repeated execution is cached, a changed declared input changes the generated artifact and downstream result, and an unrelated module remains unaffected. Check actual output behavior, not only whether the build definition compiles.
