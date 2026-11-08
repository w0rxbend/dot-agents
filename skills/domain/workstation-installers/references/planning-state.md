# Planning, configuration, and durable state

## Preserve the config's semantics

Locate schema frontend; YAML does not imply one common model. Fluxion supports jobs/steps DAG and WorkstationProfile frontend. Lowering to common plan must keep their ordering, conditions and dependencies. Dotbot directive sequence has order-sensitive defaults and actions. Do not deserialize ordered link map through unordered representation and silently reorder its shell/link behavior. See [Fluxion frontends and workflow](https://github.com/worxbend/fluxion/blob/f2551688877610a629b0bfe13d377acc9809d154/README.md) and [cross-format directive ordering tests](https://github.com/worxbend/dotbot-scala/blob/b96d07ea88cdc891ae7c8fe3b3d46264e47f2c45/app/test/src/io/worxbend/dotbot/ConfigOrderSuite.scala).

Handle absent, malformed and intentionally empty values distinctly. Keep supported formats and CLI flags explicit: dotbot-scala omits Python plugins and differs from dotbot-go. Port should preserve documented behavior, not add every feature from another implementation by analogy. See [documented compatibility and differences](https://github.com/worxbend/dotbot-scala/blob/b96d07ea88cdc891ae7c8fe3b3d46264e47f2c45/README.md).

## One operation model, several presentations

Prefer shared operation values for validation, preview, JSON/human rendering, TUI selection and application. Dry run must not invoke package managers, change shell configuration, fetch-and-execute scripts, write completion state or prompt for privilege as if applying. If metadata resolution legitimately needs network access, state that separately and keep project's offline/locked mode.

Preserve command argv and working-directory boundaries. Human-readable string is display representation, not execution API. Do not interpolate profile values into shell unless schema explicitly defines shell operation. Redact command credentials without altering actual argv executor uses.

## Idempotence and resume are evidence-based

State record should identify effective inputs and completed operation; tool name alone is not proof. Ask whether state refers to validated version/checksum/target, whether live probe is required, and what changed profile invalidates. Persist completion only after successful effects and final placement. Keep failed, skipped-by-condition, already-present, interrupted and successful outcomes distinct. Resume should not skip unverified half-install.

Preserve atomic state writes, recovery behavior and schema migrations. Atomic replacement prevents torn file but does not serialize two processes. If current tool permits concurrent writers, use its locking or conflict policy and test whole read-modify-write transaction, not only final rename. See [Crystal state persistence and delegation handling](https://github.com/worxbend/fluxion.cr/blob/466585ebd93facc97699a93245049c594fc19aae/src/fluxion/state/store.cr).

## Validation and parity

Pick changed parser, planner, executor or persistence suites first, then current CI gate. Java Fluxion uses `sysboot/build.mill.yaml` plus per-module declarative files. Do not rewrite it to programmable Mill merely because application Java logic is complex. Crystal Fluxion uses frozen shards, format, Ameba, specs and warning-clean build. See [Java build root](https://github.com/worxbend/fluxion/blob/f2551688877610a629b0bfe13d377acc9809d154/sysboot/build.mill.yaml), [Java test/native gates](https://github.com/worxbend/fluxion/blob/f2551688877610a629b0bfe13d377acc9809d154/.github/workflows/ci.yml), and [Crystal quality gates](https://github.com/worxbend/fluxion.cr/blob/466585ebd93facc97699a93245049c594fc19aae/.github/workflows/ci.yml).

For native releases, exercise actual binary's CLI and its parser/reflection/resources. Passing JVM tests do not establish GraalVM reachability. Preserve repository's supported architecture and checksum filename conventions.
