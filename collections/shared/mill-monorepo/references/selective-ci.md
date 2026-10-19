# Selective execution with a valid baseline

Mill's selective workflow snapshots task implementations and inputs, then finds tasks affected by changes. Use the same candidate selectors when preparing and evaluating:

```sh
./mill selective.prepare '__.test'
# Change sources, or move the isolated checkout from baseline to the reviewed revision.
./mill selective.resolve '__.test'
./mill selective.run '__.test'
```

Do not prepare after the change and call the resulting empty selection proof that tests are unnecessary. In CI, establish the target branch/merge-base policy, check out that baseline, prepare the snapshot, then evaluate the PR revision in the same preserved output/snapshot context. Separate worktrees have separate `out/` directories unless deliberately configured; merely running prepare in one and run in another does not automatically transfer the baseline. Avoid changing a developer's dirty checkout to emulate this procedure; use an isolated checkout for revision switching.

The baseline should be known and appropriate for the proposed change. If preparation fails, the snapshot is absent/stale, or the graph cannot be evaluated, fail clearly or use full candidate execution. Cache restore must not silently substitute a snapshot from an unrelated branch/toolchain. Preserve selector scope: preparing only application tests and later selecting other modules needs an explicit policy and validation.

Use `selective.resolveChanged` for changed input tasks and `selective.resolveTree` for their downstream selected tasks on versions supporting them. For the mixed-language template, a Kotlin implementation change should affect the Scala service test; the independent Java module should stay outside that path. Shared convention/compiler/BOM changes should invalidate all relevant consumers even when no source files changed. These are meaningful affectedness checks.

Task graph correctness is the foundation. Undeclared environment variables, mutable remote services, external clocks, filesystem reads outside source tasks, and test fixtures outside tracked inputs can cause selective execution to miss real behavior changes. `selectiveInputs` can deliberately refine command selection where documented, but overly narrow input lists hide dependencies. Avoid narrowing them just to make CI faster.

Keep full test execution at suitable milestones or scheduled runs when tests depend on environment/runtime behavior beyond the graph. Commands such as tests normally execute when selected, so the selective snapshot determines which commands are invoked rather than converting tests into permanent cached results. Tests that never run due to a broken selector or zero framework discovery are not a performance improvement.

Parallelism compounds resource demand: build jobs, test-fork groups, framework threads, databases, and containers are separate concurrency budgets. Give CI an explicit jobs limit suited to runner memory and isolate service ports/temp files. Retain test reports and selection diagnostics when execution fails.

Sources: [selective execution](https://mill-build.org/mill/large/selective-execution.html), [stable selective execution](https://mill-build.org/mill/1.1.x/large/selective-execution.html), [CI setup](https://mill-build.org/mill/cli/installation-ide.html), [parallelism](https://mill-build.org/mill/depth/parallelism.html), [task inputs](https://mill-build.org/mill/fundamentals/tasks.html).
