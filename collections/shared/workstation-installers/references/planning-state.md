# Planning, configuration, and durable state

## Preserve the config's semantics

Locate the schema frontend rather than assuming YAML means one common model. Fluxion supports a jobs/steps DAG and a WorkstationProfile frontend; their ordering, conditions, and dependencies must survive lowering to a common plan. A Dotbot directive sequence has order-sensitive defaults and actions. Do not deserialize an ordered link map through an unordered representation and silently reorder its shell/link behavior. See [Fluxion frontends and workflow](https://github.com/worxbend/fluxion/blob/f2551688877610a629b0bfe13d377acc9809d154/README.md) and [cross-format directive ordering tests](https://github.com/worxbend/dotbot-scala/blob/b96d07ea88cdc891ae7c8fe3b3d46264e47f2c45/app/test/src/io/worxbend/dotbot/ConfigOrderSuite.scala).

Handle absent, malformed, and intentionally empty values distinctly. Keep supported formats and CLI flags explicit: dotbot-scala omits Python plugins and differs from dotbot-go. A port should preserve documented behavior, not add every feature from another implementation by analogy. See [documented compatibility and differences](https://github.com/worxbend/dotbot-scala/blob/b96d07ea88cdc891ae7c8fe3b3d46264e47f2c45/README.md).

## One operation model, several presentations

Prefer shared operation values for validation, preview, JSON/human rendering, TUI selection, and application. Dry run must not invoke package managers, change shell configuration, fetch-and-execute scripts, write completion state, or prompt for privilege as if applying. If metadata resolution legitimately needs network access, state that separately and retain the project's offline/locked mode.

Preserve command argv and working-directory boundaries. A human-readable string is a display representation, not the execution API. Do not interpolate profile values into a shell unless the schema explicitly defines a shell operation. Redact command credentials without altering the actual argv used by the executor.

## Idempotence and resume are evidence-based

A state record should identify the effective inputs and completed operation rather than treating a tool name alone as proof. Ask whether the state refers to a validated version/checksum/target, whether a live probe is required, and what a changed profile invalidates. Persist completion only after successful effects and final placement. Keep failed, skipped-by-condition, already-present, interrupted, and successful outcomes distinct. Resume should not skip an unverified half-install.

Preserve atomic state writes, recovery behavior, and schema migrations. Atomic replacement prevents a torn file; it does not serialize two processes. If the current tool permits concurrent writers, use its locking or conflict policy and test the whole read-modify-write transaction, not just the final rename. See [Crystal state persistence and delegation handling](https://github.com/worxbend/fluxion.cr/blob/466585ebd93facc97699a93245049c594fc19aae/src/fluxion/state/store.cr).

## Validation and parity

Choose the changed parser, planner, executor, or persistence suites first, then the current CI gate. Java Fluxion really uses `sysboot/build.mill.yaml` plus per-module declarative files; do not rewrite it to programmable Mill merely because logic is complex in application Java. Crystal Fluxion uses frozen shards, format, Ameba, specs, and a warning-clean build. See [Java build root](https://github.com/worxbend/fluxion/blob/f2551688877610a629b0bfe13d377acc9809d154/sysboot/build.mill.yaml), [Java test/native gates](https://github.com/worxbend/fluxion/blob/f2551688877610a629b0bfe13d377acc9809d154/.github/workflows/ci.yml), and [Crystal quality gates](https://github.com/worxbend/fluxion.cr/blob/466585ebd93facc97699a93245049c594fc19aae/.github/workflows/ci.yml).

For native releases, exercise the actual binary's CLI and its parser/reflection/resources. JVM tests passing does not establish GraalVM reachability. Preserve the repository's supported architecture and checksum filename conventions.
