---
name: mill-build-logic
description: Implement tracked Mill tasks for code generation, resources, external tools, and reusable build logic with correct inputs, destinations, caching, and task types. Use when writing or debugging custom Mill tasks in build.mill.
license: MIT
---

# Tracked custom build logic

[tasks.md](references/tasks.md): task-kind selection, dependency graph invariants. [generation.md](references/generation.md): generated sources/resources, generator-module boundaries, validation. `assets/codegen`: tested programmable Mill 1.1.10 example.

Programmable configuration when build behavior needs computation; ordinary values can stay declarative. Tracked inputs: `Task.Source`/`Task.Sources`. Changing external inputs: `Task.Input`. Reproducible artifacts: cached `Task`. Actions that run on invocation: `Task.Command`. `Task.Worker` only for deliberately reusable in-memory machinery.

Task calls define dependencies; keep topology visible to Mill. Known task collection: `Task.traverse`, not dependencies invoked through arbitrary loops/lambdas the task macro cannot analyze. Write artifacts into current `Task.dest`, return `PathRef` after writing. Keep normal inputs by appending to `super.generatedSources()` / `super.resources()`.

Do not read untracked files/environment, embed machine-specific paths, write into another task's destination, mutate sources during compile, or treat Mill's filesystem sandbox as security boundary. Build initialization defines graph, no I/O side effects. If generator invoking consumer's compiled code would create cycle, move generator into upstream module.

Prove: repeat run cached; changed declared input changes generated artifact and downstream result; unrelated module unaffected. Check real output behavior, not only that build definition compiles.
