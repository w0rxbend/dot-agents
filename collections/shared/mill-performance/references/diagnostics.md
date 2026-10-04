# Evaluation, caching, process architecture, and diagnosis

## Locate the cost

Mill compiles build definitions, resolves modules/selectors, plans the task graph, executes it, and bootstraps meta-build layers. Each phase has different reuse behavior. Editing a `.mill` definition can trigger build compilation/classloader replacement; editing application source normally affects downstream compilation/tasks rather than the whole definition pipeline.

| Observation | Evidence to inspect | Likely action |
| --- | --- | --- |
| Every invocation recompiles build definitions | Build source changes, meta-build inputs/classpath, profiles | Remove nondeterministic generated build inputs or reduce inappropriate shared dependencies |
| Many unrelated tasks invalidate | Invalidation tree and changed root inputs | Split volatile conventions/input scopes or correct overly broad source roots |
| Task stays cached after meaningful input change | Source/Input graph and implementation | Declare hidden file/env/tool input; don't simply delete `out/` in CI |
| No-op invocation slow | Resolution/planning/daemon profiles | Inspect build object construction, selector expansion, or bootstrap/tool overhead |
| Parallel build slower/OOM | Chrome profile, memory, workers/forks | Reduce jobs/fork budgets and isolate heavyweight tools |
| CLI and IDE results differ | Version/BSP output/config/runtime | Align toolchain and inspect independent output/cache contexts |

## Output directory evidence

Named tasks have metadata JSON, a destination, and logs under `out/`, with paths reflecting module/task names. Overridden `super` implementations may have separate paths. `show` is the supported way to get artifact values; downstream tasks should consume returned `PathRef`s rather than internal filenames.

`mill-profile.json` includes task timing/cache information; `mill-chrome-profile.json` supports a timeline view. `mill-invalidation-tree.json` identifies root uncached inputs and downstream effects, including implementation changes where supported. Other version-specific files describe dependency graphs, selective snapshots, runner/daemon state, console tails, and bootstrap builds. Use them as diagnostic evidence; do not treat their schema as a stable public API without checking the version.

A no-change custom generator should retain its output; changing its tracked schema should regenerate and affect consumers. Validate these behaviors with output bytes/timestamps and application results. Returning an absolute path string without tracked contents, reading files directly inside a cached task without Source inputs, or mutating a returned destination can produce incorrect caching.

## Reuse and purity

Default tasks serialize/cache results; persistent tasks retain destination state for incremental machinery; workers retain live state in memory. These have different invalidation/lifetime semantics. The build must work whether a module is newly instantiated or reused and whether an independent task runs first or later. Keep filesystem effects inside tasks and avoid global mutable module registries.

Resolution-time external reads need the documented watch mechanism when that advanced pattern is unavoidable; normal values should become task inputs where possible. Worker keys must include the classpath/tool/options whose change invalidates state. Close classloaders/processes when replaced. Persistent destinations need stale-file cleanup: removing a generated source must not leave an obsolete class masquerading as a current output.

## Parallelism and daemon behavior

Independent tasks can run concurrently, limited by jobs and graph structure. Adding threads cannot parallelize a long serial dependency chain. Build jobs, forked tests, compiler worker threads, external npm/pip processes, and framework concurrency all consume resources. Use representative peak measurements and a runner-specific jobs policy.

Mill uses a launcher delegating to a reusable daemon in its current architecture. The daemon can retain compiled build classes and workers; non-daemon/interactive options change reuse/terminal behavior. Use `shutdown` and a supported `--no-daemon` run to isolate an apparent daemon issue, then investigate worker state or toolchain differences. Avoid killing unrelated Java processes or clearing all user caches as routine diagnosis.

Concurrent invocations and IDE/CLI builds can contend for outputs/locks. Read the version's process/parallelism docs and use supported separate BSP output settings when appropriate. Experimental in-task futures need correct separate destinations and explicit joins; they are not a default replacement for graph-level parallelism.

## Sandboxing and benchmark interpretation

Mill redirects/guards filesystem access to encourage task output ownership; OS-Lib reads/writes and process working directories can expose accidental checkout-root assumptions. A subprocess that writes beside its input should receive a copy in the current destination or explicit output flags. Do not disable checks globally to preserve faulty task behavior. Tests need tracked resources and deliberate working directories.

The sandbox is not fully hermetic and cannot enforce all external tools/network behavior. Hidden remote state can remain outside fingerprints. For performance comparisons, distinguish cold downloads, clean compile, one-module incremental compile, no-op, application tests, and build-definition changes. Keep machines/JDKs/compiler flags/tasks comparable, include warm-up, and state whether caches and daemons were retained.

The design principles emphasize an explicit hierarchical task graph, caching by default, ordinary typed Scala abstractions, and controlled execution effects. Scala's static typing, traits, and JVM libraries help build authors express reusable behavior; those benefits do not justify exposing complex evaluator APIs in every simple build.

Sources: [evaluation model](https://mill-build.org/mill/depth/evaluation-model.html), [caching](https://mill-build.org/mill/depth/caching.html), [parallelism](https://mill-build.org/mill/depth/parallelism.html), [process architecture](https://mill-build.org/mill/depth/process-architecture.html), [sandboxing](https://mill-build.org/mill/depth/sandboxing.html), [output directory](https://mill-build.org/mill/fundamentals/out-dir.html), [design principles](https://mill-build.org/mill/depth/design-principles.html), [why Scala](https://mill-build.org/mill/depth/why-scala.html), [performance comparisons](https://mill-build.org/mill/comparisons/performance.html).
