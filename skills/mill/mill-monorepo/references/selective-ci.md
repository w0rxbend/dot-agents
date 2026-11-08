# Selective execution with a valid baseline

Mill's selective workflow snapshots task implementations and inputs, then finds tasks affected by changes. Use same candidate selectors to prepare and evaluate:

```sh
./mill selective.prepare '__.test'
# Change sources, or move the isolated checkout from baseline to the reviewed revision.
./mill selective.resolve '__.test'
./mill selective.run '__.test'
```

Do not prepare after change and call empty selection proof that tests are unnecessary. CI: set target branch/merge-base policy, check out baseline, prepare snapshot, evaluate PR revision in same preserved output/snapshot context. Separate worktrees have separate `out/` directories unless deliberately configured; running prepare in one and run in another does not transfer baseline automatically. Avoid changing developer's dirty checkout for this; switch revisions in isolated checkout.

Baseline should be known and fit proposed change. If preparation fails, snapshot is absent/stale, or graph cannot be evaluated: fail clearly or run full candidate set. Cache restore must not silently substitute snapshot from unrelated branch/toolchain. Preserve selector scope: preparing only application tests, then selecting other modules, needs explicit policy and validation.

On versions supporting them, inspect with `selective.resolveChanged` (changed input tasks) and `selective.resolveTree` (their downstream selected tasks). Meaningful affectedness checks: in mixed-language template, Kotlin implementation change should affect Scala service test; independent Java module should stay outside that path. Shared convention/compiler/BOM changes should invalidate all relevant consumers, even without source file changes.

Selective execution can miss real behavior changes from undeclared environment variables, mutable remote services, external clocks, filesystem reads outside source tasks, test fixtures outside tracked inputs. `selectiveInputs` can deliberately refine command selection where documented; overly narrow input lists hide dependencies. Do not narrow them for CI speed alone.

Keep full test runs at milestones or on schedule when tests depend on environment/runtime behavior beyond graph. Selected commands such as tests normally execute: snapshot picks which commands run; tests do not become permanent cached results. Tests that never run (broken selector, zero framework discovery) are no performance win.

Parallelism compounds resource demand: build jobs, test-fork groups, framework threads, databases, containers are separate concurrency budgets. Set explicit CI jobs limit fitting runner memory. Isolate service ports/temp files. Keep test reports and selection diagnostics on failure.

Sources: [selective execution](https://mill-build.org/mill/large/selective-execution.html), [stable selective execution](https://mill-build.org/mill/1.1.x/large/selective-execution.html), [CI setup](https://mill-build.org/mill/cli/installation-ide.html), [parallelism](https://mill-build.org/mill/depth/parallelism.html), [task inputs](https://mill-build.org/mill/fundamentals/tasks.html).
