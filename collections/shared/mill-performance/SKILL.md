---
name: mill-performance
description: Diagnose Mill evaluation, caching, invalidation, daemon behavior, parallelism, output metadata, and sandbox problems in large builds without masking undeclared inputs.
license: MIT
---

# Mill evaluation and performance

Read [diagnostics.md](references/diagnostics.md) for phase-specific evidence, output files, concurrency budgets, sandboxing, and benchmark design.

Distinguish build-definition compilation, module/selector resolution, planning, execution, and bootstrapping. A slow build can be dominated by any of them. Inspect profiles and invalidation roots before changing concurrency or deleting caches.

Keep build constructors/definitions deterministic, task inputs tracked, and outputs owned by the current task. Mill reuses modules/classloaders/workers and may skip tasks; correctness cannot rely on initialization side effects, execution order among independent tasks, or hidden external state. Parallelism requires thread-safe shared workers and isolated outputs.

Use the pinned launcher and diagnose a daemon-specific issue with supported shutdown/non-server tools. Target cleanup to affected tasks. A successful clean rebuild does not explain why an incremental build was stale; correct the missing input or invalidation boundary.

Mill sandboxing provides filesystem guardrails and working-directory isolation, not hermetic execution or hostile-code containment. Describe benchmark conditions and practical limits; don't extrapolate published speedup figures to every monorepo.
