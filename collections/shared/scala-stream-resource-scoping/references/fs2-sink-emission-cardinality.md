# FS2 (typelevel/fs2): sink emission cardinality — originally `scala-fs2-sink-emission-cardinality`

Evidence: [evidence/scala-fs2-sink-emission-cardinality.json](evidence/scala-fs2-sink-emission-cardinality.json), claim
`fs2-claim-cardinality`.

Scope: replacing a sink, adding `.drain`, changing `Unit` to `Nothing`, or refactoring post-write continuation. Applies
to library definitions and downstream `flatMap`, `>>`, for-comprehension and `take` call sites. Output count is
observable behavior even when every output value is `()`.

Not for: ordinary value transformations with unchanged cardinality, pure collection style, generic resource
finalization. Do not replace every bind with append. Continuation depending on each emitted value still belongs in
`flatMap`; resource-lifetime transfer across parallel operators belongs in
[fs2-per-element-scope-propagation.md](fs2-per-element-scope-propagation.md).

## Prerequisites and version fences

Read exact sink implementation, signature, downstream usages, versioned tests. Take Scala, FS2, Cats Effect versions
from actual build, not calendar year.

- #1913 finally targeted FS2 3.0, not 2.x, but its inspected August 2020 branch still used CE 2.2.0-RC3, Scala
  2.13.2/2.12.10 and Dotty 0.26.0-RC1. Its `Blocker` file APIs are not current CE3 examples.
- Check whether target version has `NotNothing` on `flatMap`/`>>`, a successor diagnostic, or no such protection.
  `NotNothing` prevents some statically empty binds, not every empty `Stream[F, Unit]`.
- Preserve existing sbt build and effect style. Do not introduce different effect library or build tool.

## Workflow

1. Record existing emission contract for empty, one and several inputs: zero outputs; one completion output; or one
   output per successful input. Distinguish per-element vs per-chunk emission. Returning `F[Unit]` is not itself a
   stream emission; `Stream[F, Unit]` does not guarantee any emissions.
2. Trace implementation operations. `evalMap` can preserve per-input outputs; historical `foreach` drains them. Compare
   docs against source. In #1913, printing docs still described unit emissions beside drained implementation: flag
   discrepancy; do not pick the comment as oracle.
3. Enumerate sink consumers. `flatMap` and `>>` continue once per output, not once at stream termination. `take(n)`
   after a sink counts sink emissions, not completed effects invisibly discarded upstream. Infinite draining sink can
   keep working without satisfying `take(1)`.
4. If intent is one continuation after successful exhaustion, independent of outputs, use version-supported append
   (`++`). Explicitly discard old output only if intended output contract permits it. Test upstream failure and
   cancellation separately; append is not a finalizer and not a general always-run cleanup mechanism.
5. If changing public behavior, separate binary compatibility, source diagnostics, runtime compatibility. Specify
   migration/release policy and representative consumer before altering signature. Eventual #1913 revision kept
   Queue/Topic per-element units and added diagnostic witness; initial all-sinks proposal was not final decision.
   (Evidence stages differ: review request, author intention, merged patch.)
6. Add both precisely typed empty-stream compile probe and widened empty-stream runtime probe. Witness against
   `Nothing` cannot prove stream widened to `Unit` will emit. Do not silence witness by widening without repairing
   sequencing.

## Review checks

Documented output counts, continuation counts, bounded-consumption behavior stay unchanged unless intentionally
migrated. Check effect execution, not only output values: two programs can both compile to `Unit` while one never
executes read-back.

Counterexample from claim: `Queue.enqueue` emitting one `Unit` per enqueued element intentionally supports `take(n)`;
draining it and moving `take` after the drain changes termination.

## False positives

- Intentional `evalMap(_ => action)` followed by `take(n)` uses units as progress signals.
- Terminal writer that never promised per-byte emissions need not invent them.
- Historical decision does not authorize changing all current Queue/Topic APIs; inspect their present signatures and
  semantics first.
- Historical `Queue.enqueue` uses `evalMap(enqueue1)`, emits a unit per successful enqueue; consumer deliberately taking
  two outputs relies on it. Do not convert it to `foreach` just to make sink signatures uniform.

## Validation

With permission to execute upstream build code, inspect `build.sbt`, launcher/plugins, toolchain requirements. Use
`sbt projects` and `sbt 'show io / Test / definedTests'` on #1913 branch; its `testJVM` alias explicitly includes
`io/test`. Run `sbt 'io/testOnly fs2.io.file.FileSuite'` for historical write/read round trip. On newer cross-built
I/O branches rediscover platform project; do not assume `io` remains runnable.

Assert output length and continuation count for empty/nonempty inputs, several chunk layouts, failed writes, early
termination. Compile target version's precise-`Nothing` misuse fixture; separately execute widened empty bind. Require
specific expected compile failure, not any build error. No historical build or Scala fixture was executed in this
research run.

## Examples

- Good: drained file write followed by `++ readBack`; read runs once after finite successful write, bytes equal input.
  Historical FileSuite uses this structure. Separate failure case asserts read-back did not run. Review does not infer
  always-run cleanup contract from append.
- Broken and correction: refactor changes `drainedWrite ++ readBack` to `drainedWrite.flatMap(_ => readBack)`.
  Correction: restore append for stated once-after-exhaustion intent. If `drainedWrite` has precise `Nothing` output,
  version-specific witness may catch misuse; if widened to `Stream[F, Unit]`, it may compile and still skip
  continuation. Assert continuation counter and round-trip result, not compilation alone.

## Case-specific output

Before/after emission table (empty / one / many inputs); affected consumer expressions; intended compatibility policy;
compile checks vs executed effect/output checks.

## Limitations

Specific public semantic migration, not universal preference for `Nothing` or `Unit`. Historical printing docs were
inconsistent; do not cite them as passing positive example. Current behavior and compiler diagnostics need
current-branch inspection. Independent behavioral review remains outstanding.

## Sources

- [SystemFw's compatibility alternative](https://github.com/typelevel/fs2/pull/1913#pullrequestreview-434456142),
  [narrowed revision](https://github.com/typelevel/fs2/pull/1913#issuecomment-660487448) and
  [major-version boundary](https://github.com/typelevel/fs2/pull/1913#issuecomment-674277120).
- [Earlier empty-bind concern](https://github.com/typelevel/fs2/pull/1754#issuecomment-578140568).
- [Actual write/read test](https://github.com/typelevel/fs2/blob/d18ed74177e1622cf51f6f3621ac35df557141a7/io/src/test/scala/fs2/io/file/FileSuite.scala#L68-L87).
- `NotNothing` witness, Queue, Stream and printing sources at same SHA in evidence file.
