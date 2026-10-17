---
name: scala-fs2-sink-emission-cardinality
description: Use when changing an FS2 sink result type or sequencing after a draining pipe. Preserve zero, completion-only and per-input emissions across API migrations.
license: MIT
---

# Preserve sink emission cardinality

## When to Use

Use when replacing a sink, adding `.drain`, changing `Unit` to `Nothing`, or refactoring a continuation after a write. Apply `fs2-claim-cardinality` to both library definitions and downstream `flatMap`, `>>`, for-comprehension and `take` call sites. Output count is observable behavior even when every output value is `()`.

## When Not to Use

Do not load this for ordinary value transformations with unchanged cardinality, pure collection style, or generic resource finalization. Do not replace every bind with append. A continuation depending on each emitted value still belongs in `flatMap`; resource-lifetime transfer across parallel operators belongs in the scope-propagation skill.

## Prerequisites

Read the exact sink implementation, signature, downstream usages and versioned tests. Identify Scala, FS2 and Cats Effect versions from the actual build, not the calendar year. #1913 finally targeted FS2 3.0 rather than 2.x, but its inspected August 2020 branch still used CE 2.2.0-RC3, Scala 2.13.2/2.12.10 and Dotty 0.26.0-RC1. Its `Blocker` file APIs are not current CE3 examples.

Check whether the target version has `NotNothing` on `flatMap`/`>>`, a successor diagnostic or no such protection. Preserve the existing sbt build and effect style. Do not introduce a different effect library or build tool to apply this review.

## Workflow

1. Record the existing emission contract on empty input, one input and several inputs: zero outputs; one completion output; or one output per successful input. Distinguish per-element and per-chunk emission. `F[Unit]` returning is not itself a stream emission, and `Stream[F, Unit]` does not guarantee any emissions.
2. Trace implementation operations. `evalMap` can preserve per-input outputs; the historical `foreach` drains them. Compare documentation against source. In #1913, printing documentation still described unit emissions beside a drained implementation: flag this discrepancy rather than choosing the comment as the oracle.
3. Enumerate consumers of the sink. `flatMap` and `>>` continue once per output, not once at stream termination. `take(n)` after a sink counts sink emissions, not completed effects invisibly discarded upstream. An infinite draining sink can continue working without satisfying `take(1)`.
4. If intent is a continuation once after successful exhaustion independent of outputs, use the version-supported append operation (`++`) and explicitly discard any old output only if the intended output contract permits it. Test upstream failure and cancellation separately; append is not a finalizer and not a general always-run cleanup mechanism.
5. If changing public behavior, separate binary compatibility, source diagnostics and runtime compatibility. Specify migration/release policy and a representative consumer before altering the signature. The eventual #1913 revision retained Queue/Topic per-element units and added a diagnostic witness; the initial all-sinks proposal is not the final decision.
6. Add both a precisely typed empty-stream compile probe and a widened empty-stream runtime probe. A witness against `Nothing` cannot prove that a stream widened to `Unit` will emit. Do not silence the witness by widening without repairing sequencing.

## Review and Refactoring Checks

Preserve the invariant that documented output counts, continuation counts and bounded-consumption behavior remain unchanged unless intentionally migrated. Check effect execution as well as output values: two programs can both compile to `Unit` while one never executes the read-back operation.

False positives: intentional `evalMap(_ => action)` followed by `take(n)` uses units as progress signals. A terminal writer that never promised per-byte emissions need not invent them. The historical decision does not authorize changing all current Queue/Topic APIs; inspect their present signatures and semantics first.

## Validation

With permission to execute upstream build code, inspect `build.sbt`, launcher/plugins and toolchain requirements. Use `sbt projects` and `sbt 'show io / Test / definedTests'` on the #1913 branch; its `testJVM` alias explicitly includes `io/test`. Run `sbt 'io/testOnly fs2.io.file.FileSuite'` for the historical write/read round trip. Rediscover the platform project on newer cross-built I/O branches instead of assuming `io` remains runnable.

Add assertions for output length and continuation count on empty/nonempty inputs, several chunk layouts, failed writes and early termination. Compile the target version's precise-`Nothing` misuse fixture and separately execute a widened empty bind. Require a specific expected compile failure, not any build error. No historical build or Scala fixture was executed in this research run.

## Examples

### Good

A drained file write is followed by `++ readBack`; the read runs once after a finite successful write and its bytes equal the input. The historical FileSuite uses this structure. A separate failure case asserts read-back did not run. The review does not infer an always-run cleanup contract from append.

### Broken and Correction

A refactor changes `drainedWrite ++ readBack` to `drainedWrite.flatMap(_ => readBack)`. Correction: restore append for the stated once-after-exhaustion intent. If `drainedWrite` has precise `Nothing` output, a version-specific witness may catch misuse; if widened to `Stream[F, Unit]`, it may compile and still skip the continuation. Assert a continuation counter and round-trip result rather than compilation alone.

### Negative

The historical `Queue.enqueue` uses `evalMap(enqueue1)` and emits a unit per successful enqueue. A consumer deliberately takes two outputs. Do not convert it to `foreach` just to make sink signatures uniform: it removes the signal that bounds consumption. For a value-dependent continuation, retain bind rather than prescribing append.

## Output Contract

Report `file:line`, severity, evidence ID/URL, version/platform and before/after emission table. Include affected consumer expressions, intended compatibility policy, proposed correction and test oracle. Distinguish compile checks from executed effect/output checks; say when a version or regression is unverified.

## Limitations

This skill captures a specific public semantic migration, not a universal preference for `Nothing` or `Unit`. A review request, author intention and merged patch are different evidence stages. Historical printing documentation was inconsistent; do not cite it as a passing positive example. Current behavior and compiler diagnostics require current-branch inspection. Independent behavioral review remains outstanding.

## Sources

- [Evidence and claim mapping](references/evidence.json).
- [SystemFw's compatibility alternative](https://github.com/typelevel/fs2/pull/1913#pullrequestreview-434456142), [narrowed revision](https://github.com/typelevel/fs2/pull/1913#issuecomment-660487448) and [major-version boundary](https://github.com/typelevel/fs2/pull/1913#issuecomment-674277120).
- [Earlier empty-bind concern](https://github.com/typelevel/fs2/pull/1754#issuecomment-578140568).
- [Actual write/read test](https://github.com/typelevel/fs2/blob/d18ed74177e1622cf51f6f3621ac35df557141a7/io/src/test/scala/fs2/io/file/FileSuite.scala#L68-L87).
