# Evaluation, caching, process architecture, and diagnosis

## Locate the cost

Mill phases: compile build definitions, resolve modules/selectors, plan task graph, execute, bootstrap meta-build layers. Each reuses differently. Editing `.mill` definition can trigger build compilation/classloader replacement. Editing application source normally hits downstream compilation/tasks, not whole definition pipeline.

| Observation | Evidence to inspect | Likely action |
| --- | --- | --- |
| Every invocation recompiles build definitions | Build source changes, meta-build inputs/classpath, profiles | Remove nondeterministic generated build inputs or cut inappropriate shared dependencies |
| Many unrelated tasks invalidate | Invalidation tree, changed root inputs | Split volatile conventions/input scopes or narrow overly broad source roots |
| Task stays cached after meaningful input change | Source/Input graph, implementation | Declare hidden file/env/tool input; don't delete `out/` in CI as workaround |
| No-op invocation slow | Resolution/planning/daemon profiles | Inspect build object construction, selector expansion, bootstrap/tool overhead |
| Parallel build slower/OOM | Chrome profile, memory, workers/forks | Cut jobs/fork budgets, isolate heavy tools |
| CLI and IDE results differ | Version/BSP output/config/runtime | Align toolchain, inspect independent output/cache contexts |

## Output directory evidence

Named tasks keep metadata JSON, destination and logs under `out/`, at paths named by module/task. Overridden `super` implementations may get separate paths. `show` is supported way to get artifact values. Downstream tasks should consume returned `PathRef`s, not internal filenames.

`mill-profile.json`: task timing/cache information. `mill-chrome-profile.json`: timeline view. `mill-invalidation-tree.json`: root uncached inputs and downstream effects, including implementation changes where supported. Other version-specific files cover dependency graphs, selective snapshots, runner/daemon state, console tails, bootstrap builds. Use as diagnostic evidence. Do not treat their schema as stable public API without checking version.

Unchanged custom generator should keep its output. Tracked schema change should regenerate and affect consumers. Verify with output bytes/timestamps and application results. Can break caching: returning absolute path string without tracked contents, reading files directly in cached task without Source inputs, mutating returned destination.

## Reuse and purity

Default tasks serialize/cache results. Persistent tasks keep destination state for incremental machinery. Workers keep live state in memory. Invalidation/lifetime semantics differ. Build must work whether module is newly instantiated or reused, whatever order independent tasks run in. Keep filesystem effects inside tasks. Avoid global mutable module registries.

Resolution-time external reads need documented watch mechanism when that advanced pattern is unavoidable. Make normal values task inputs where possible. Worker keys must include classpath/tool/options whose change invalidates state. Close replaced classloaders/processes. Persistent destinations need stale-file cleanup: removed generated source must not leave obsolete class posing as current output.

## Parallelism and daemon behavior

Independent tasks can run concurrently, limited by jobs and graph structure. More threads cannot parallelize long serial dependency chain. Build jobs, forked tests, compiler worker threads, external npm/pip processes, framework concurrency all use resources. Base runner-specific jobs policy on representative peak measurements.

Current architecture: Mill launcher delegates to reusable daemon. Daemon can keep compiled build classes and workers. Non-daemon/interactive options change reuse/terminal behavior. Isolate apparent daemon issue with `shutdown` and supported `--no-daemon` run, then check worker state or toolchain differences. Avoid killing unrelated Java processes or clearing all user caches as routine diagnosis.

Concurrent invocations and IDE/CLI builds can contend for outputs/locks. Read version's process/parallelism docs. Use supported separate BSP output settings when appropriate. Experimental in-task futures need correct separate destinations and explicit joins. Not default replacement for graph-level parallelism.

## Sandboxing and benchmark interpretation

Mill redirects/guards filesystem access to encourage task output ownership. OS-Lib reads/writes and process working directories can expose accidental checkout-root assumptions. Subprocess writing beside its input should get copy in current destination or explicit output flags. Do not disable checks globally to keep faulty task behavior. Tests need tracked resources and deliberate working directories.

Sandbox is not fully hermetic and cannot enforce all external tools/network behavior. Hidden remote state can stay outside fingerprints. In performance comparisons, separate cold downloads, clean compile, one-module incremental compile, no-op, application tests, build-definition changes. Keep machines/JDKs/compiler flags/tasks comparable. Include warm-up. State whether caches and daemons were retained.

Design principles: explicit hierarchical task graph, caching by default, ordinary typed Scala abstractions, controlled execution effects. Do not expose complex evaluator APIs in every simple build.

Sources: [evaluation model](https://mill-build.org/mill/depth/evaluation-model.html), [caching](https://mill-build.org/mill/depth/caching.html), [parallelism](https://mill-build.org/mill/depth/parallelism.html), [process architecture](https://mill-build.org/mill/depth/process-architecture.html), [sandboxing](https://mill-build.org/mill/depth/sandboxing.html), [output directory](https://mill-build.org/mill/fundamentals/out-dir.html), [design principles](https://mill-build.org/mill/depth/design-principles.html), [why Scala](https://mill-build.org/mill/depth/why-scala.html), [performance comparisons](https://mill-build.org/mill/comparisons/performance.html).
