# Mill task design

## Select the lifetime

| Task kind | Use | Caching/lifetime concern |
| --- | --- | --- |
| `Task.Source` / `Task.Sources` | Tracked files/directories | Fingerprints must capture actual inputs |
| `Task.Input` | Environment/system property/changing external value | Re-read each evaluation; avoid exposing secrets in results |
| `Task { ... }` | Deterministic computation or generated files | Serialized value and output content drive cache invalidation |
| `Task.Command { ... }` | Run, test, interactive or external action | Executes on invocation; not skipped like cached artifact |
| `Task(persistent = true) { ... }` | Tool needing incremental state across evaluations | State persists; manage stale data, correctness explicitly |
| `Task.Worker` | Compiler/tool/classloader cached in memory | Handle concurrency, cleanup, invalidation |
| `Task.Anon` | Composed internal task, not independently named | Still in explicit graph |
| Uncached task form | Specialized value, intentionally reevaluated | Verify version-specific API, concrete need |

Cached results need supported JSON writer/reader. Primitives/collections and `PathRef` are convenient; custom result types need serialization. Do not return live stream, process, classloader or mutable compiler instance as ordinary cached value; use worker or action scope.

Dependencies are planned before execution. `def archive = Task { packageFiles(compile(), resources()) }` exposes both prerequisites. Task graph is applicative, not arbitrary dynamic workflow engine: do not conditionally discover and invoke unknown tasks only after executing another. Statically known module collection: `Task.traverse(modules)(_.compile)()` exposes dependencies. Evaluator APIs, if truly needed, are advanced/version-sensitive, not default shortcut.

## Inputs and output ownership

Disk inputs: `Task.Source("schema.json")` or `Task.Sources("schemas")`, not `os.read(moduleDir / "schema.json")` hidden in cached computation. Untracked file reads can produce stale output. Capture environment/system properties via documented input mechanism. Keep configuration values immutable, deterministic; top-level `val` reading time/git/environment may miss task invalidation.

Each task owns a destination: write under `Task.dest`. Use separate subdirectories when one task deliberately manages multiple outputs. Return `PathRef` only after final output is written, so content signature describes completed artifact. Consumers use producer's returned path, not `out/foo/task.dest` hardcoded from Mill's internal layout.

Do not mutate upstream `PathRef` directory after consuming it: parallel consumers may read mid-change, and signature stops matching real bytes. For transformations, copy into current task's destination. Keep static resources by appending generated directory to `super.resources()` when intended. Replacing list can be valid but needs explicit reason.

## External tools and sandboxing

Use managed/pinned executable or make its version explicit input. Pass structured arguments through OS-Lib, not shell string built from user-controlled text. Set working directory and environment deliberately, collect useful failure diagnostics, fail task on subprocess failure. Tool output belongs in task destination; if tool insists on writing beside inputs, copy immutable inputs there.

Mill's filesystem checks and working-directory redirection encourage input/output isolation but are not hostile-code sandbox or fully hermetic build. Bypass checks only as exceptional integration choice with documented reason, not default fix for faulty task. Tests may also use sandboxed working directory: configure tracked fixtures, pass paths, do not assume repository root.

Use commands for network publication, applying database migrations, other intentional external effects. Cached tasks fit migration bundles, publishable archives. Defining publish task does not authorize publishing; follow actual user's scope for external action.

Sources: [tasks](https://mill-build.org/mill/fundamentals/tasks.html), [evaluation](https://mill-build.org/mill/depth/evaluation-model.html), [sandboxing](https://mill-build.org/mill/depth/sandboxing.html), [bundled libraries](https://mill-build.org/mill/fundamentals/bundled-libraries.html), [dynamic JVM code](https://mill-build.org/mill/extending/running-jvm-code.html).
