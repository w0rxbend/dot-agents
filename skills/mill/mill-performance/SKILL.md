---
name: mill-performance
description: Diagnose Mill evaluation, caching, invalidation, daemon behavior, parallelism, output metadata, and sandbox problems in large builds without masking undeclared inputs. Use when a Mill build is slow, over-invalidates or behaves inconsistently between runs.
license: MIT
---

# Mill evaluation and performance

Read [diagnostics.md](references/diagnostics.md) for per-phase evidence, output files, concurrency budgets, sandboxing, benchmark design.

Distinguish build-definition compilation, module/selector resolution, planning, execution and bootstrapping; any can dominate slow build. Check profiles and invalidation roots before changing concurrency or deleting caches.

Keep build constructors/definitions deterministic, task inputs tracked, outputs owned by current task. Mill reuses modules/classloaders/workers and may skip tasks. Correctness cannot rely on initialization side effects, independent-task order or hidden external state. Parallelism needs thread-safe shared workers, isolated outputs.

Use pinned launcher. Debug daemon issues with supported shutdown/non-server tools. Clean only affected tasks. Passing clean rebuild does not explain stale incremental build. Fix missing input or invalidation boundary.

Sandboxing gives filesystem guardrails and working-directory isolation, not hermetic execution or hostile-code containment. State benchmark conditions and limits. Don't extrapolate published speedups to every monorepo.
