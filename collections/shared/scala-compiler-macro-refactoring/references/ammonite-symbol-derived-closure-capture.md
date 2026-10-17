# Ammonite (com-lihaoyi/Ammonite): symbol-derived REPL closure capture

Originally `scala-ammonite-symbol-derived-closure-capture`. Evidence: [evidence/scala-ammonite-symbol-derived-closure-capture.json](evidence/scala-ammonite-symbol-derived-closure-capture.json) (claims `c-capture`, `c-metadata`).

## Scope

Use for changes to class-based REPL wrapping, compiler extraction of `usedEarlierDefinitions`, transport of that metadata, or serialization-test isolation. A source-equivalent import rewrite can change the serialized object graph. This is a refactoring procedure for that mechanism, not a general Scala style guide.

Not for: ordinary application imports, BSP repository propagation (see [ammonite-static-script-dependency-propagation.md](ammonite-static-script-dependency-propagation.md)), arbitrary Java deserialization security, or every singleton in the REPL. An object-only command deliberately retained singleton wrapping for macro ownership. Do not add an effect runtime to Ammonite.

## Prerequisites

Identify the checkout SHA, actual compiler patch version, wrapper selected by the caller, and JDK/test-runner arrangement. The primary implementation is Scala 2.12.4/JVM with uTest 0.6.0 in PR 736. Its plugin lives in `amm/interp`; later compiler extraction moves packages, so trace symbols instead of copying paths.

Read `CodeClassWrapper`, the compiler's used-command collector, compilation output/session bridge, and `SerializationTests`. In the 2018 layout the wrapper is nested in `Preprocessor`. The 2019 test isolation revision moves serialization helpers into a separate test API and calls `cloneClassLoader(null)`. In 2021 this suite explicitly selects a disabled test on Scala 3. That is a coverage boundary, not evidence that all Scala 3 closures are unserializable. No Cats Effect, ZIO, or Ox API is part of this contract.

## Workflow

1. **State the command-granularity invariant.** Preserve required earlier-command instances as captured values; null only wholly unused command references. This is not field-level closure cleaning: unused siblings inside a required `Helper` can remain reachable. Successful serialization requires the retained reachable graph to be serializable. For ordinary captured values, deserializing and invoking must not rerun their initialization; intentional singleton references retain their different semantics.
2. **Trace both term- and type-derived dependencies.** Locate the phase relative to typer and the wrapper symbol. PR 736's `Select` receiver-symbol matching was incomplete: PR 944 adds traversal of `TypeTree.tpe`, collecting `SingleType` names whose prefix type symbol equals the wrapper symbol, then deduplicates the combined names. Preserve commands required through trait bounds/path-dependent types as well as term selections. Reject `tree.toString`/regex matching and lookalike string literals. These are Scala 2 compiler-internal shapes, not APIs to copy into Scala 3; rediscover equivalent typed dependency paths for another compiler.
3. **Trace metadata with the compiled command.** Follow callback/output, cache/session storage, and the runtime bridge. Verify the result belongs to the command being instantiated, including cache hits and session restoration. Do not hide it in a classpath resource to avoid threading a field through the existing structures. These lifecycle checks extend the historical review rationale; they are not a claim that every lifecycle had a regression in PR 736.
4. **Preserve the wrapper's exceptions.** Check object-only commands, wrapper nesting levels, and import rewriting. The 2018 plugin explicitly distinguishes nesting levels 1 and 2; silently accepting another shape is not equivalent. Do not remove intentionally unused-reference nulling merely to apply a modern application-style rule.
5. **Exercise a genuinely separate loader.** Put nonserializable unused `d` in one command, captured `a` with a sentinel-producing initializer in a separate command, and the closure using `a` in a third. Serialize, clear the sentinel, deserialize with isolated generated classes, and invoke. Require successful serialization, no new sentinel, and the expected result. The historical test checks the sentinel but discards the reflected return value; a result assertion is a proposed stronger oracle. Keep a separate same-command sibling case to demonstrate the scope limit, not to demand field pruning.
6. **Test type dependencies independently of serialization.** Reproduce PR 944's evaluator transcript: define `trait A` and `class X` together; in the next command define `class Z[T <: A]` and construct `z1`; in a third construct `z2`. Both results must print `Z(X(7))`, without a null-reference exception under class wrapping. Inspect `DualTestRepl` dispatch rather than assuming the object-wrapper run covers it. This source-observed regression is distinct from the closure sentinel test.
7. **Prove the oracles discriminate.** In a separately authorized checkout, try three isolated mutations: direct singleton imports, retaining a wholly unused nonserializable command, and dropping only type-derived dependency collection. Check respectively reinitialization, serialization failure, and the evaluator regression. Restore each mutation. Literal-lookalike/cache-restore probes and mutation outcomes remain proposed until executed; never claim that the serialization sentinel alone validates type retention.

## Checks

- Preserve capture identity at **command** granularity, not merely names/output or a minimal field set. Retain both term- and type-derived dependencies. Do not solve unused capture by requiring every session value to implement `Serializable`, or by nulling a command needed through a type.
- Preserve compiler/runtime metadata association. A stale comment mentioning `tree.txt` is not evidence that the final implementation reads that resource; inspect the generated bridge expression.
- Verify classloader separation explicitly. The 2019 harness asserts that its test API loader differs from the thread context loader; the serialization test passes a null parent to its clone. Preserve the intended isolation, not necessarily that exact API on a newer version.

## False positives

A nonserializable `d` next to captured `a` in the same required `Helper` can legitimately remain reachable; this implementation is not a closure cleaner. Intentional singleton references and object-only definitions keep their distinct initialization behavior. Source generation using strings is not itself forbidden. A documented disabled compiler variant is not a passing serialization test.

## Validation

Do not execute historical upstream code during a read-only research task. For an authorized development checkout, inspect its build, launcher pin, JDK matrix, generated test resources, and suite guards first.

At PR 736's pinned revision, `build.sbt` defines `ammRepl`; the author reports `sbt "ammRepl/testOnly ammonite.session.SerializationTests"`. Confirm the real closure case executes with the class wrapper. Keep `-Ydelambdafy=inline` test-local; never copy it into Scala 3.

At PR 944's SHA `50e075ddd8fb223046ae7be68827bc744e3c6037`, the actual build is Mill: CI uses `mill -i unitTest`, provisions Mill 0.3.3, and declares Scala 2.11.12/JDK 8 and 2.12.8/JDK 8 or 11 with uTest 0.6.0. With those separately authorized prerequisites, `TRAVIS_SCALA_VERSION=2.12.8 mill -i unitTest` dispatches `amm.repl(scalaVersion).test.test()()`. Check Git tags/master and build imports first. Do not substitute `./mill` or the 2018 sbt selector without discovering that checkout's launcher. The command is broad; discover version-matching filters for a narrower run. Verify `EvaluatorTests.referenceTraitFromPreviousCommand` executes through the class-wrapper member of `DualTestRepl`, not merely its object-wrapper member.

Record compiler, JDK, wrapper, suite, executed case count, sentinel/result assertions, command partition, and loader identity. Require both serialization and type-reference evaluator oracles; one cannot stand in for the other. A green Scala 3 `disabled` case is insufficient. Report prerequisite failures as blocked validation rather than sharing initialized singletons. A later documentation-only `build.sbt` is not the main REPL test build. No upstream compilation or behavioral effectiveness was established during research.

## Examples

**Good.** A wrapper refactor retains the union of term- and type-derived command dependencies. Unused `d` is in a **different command** from captured `a = Option(2)`; the latter's retained graph is serializable. Its closure round trip checks that initialization is not repeated, with a result assertion added for current validation. Separately, PR 944's `A`/`X` then `Z[T <: A]` transcript retains the required command through types and produces both `Z(X(7))` results. These are distinct oracles, not a universal minimal-capture promise.

**Broken and correction.** A cleanup replaces a stored `cmd0` reference with `import ...cmd0.instance.a` because names still resolve. Deserialization reinitializes `a`. Correction: retain instance capture and structured typed-dependency metadata. Reject a text scan of `cmd2.this.cmd0` using a lookalike literal control.

Another cleanup keeps symbol equality but drops the `TypeTree` branch as redundant with `Select`. Correction: restore type-derived names in the used-command union and run `referenceTraitFromPreviousCommand` with class wrapping. PR 944 supplies the source-observed regression; merely rerunning the serialization sentinel cannot validate this repair.

**Negative.** A hypothetical command defines `a = Option(2)` and nonserializable `d` together, then a later closure uses `a`. The retained command may include `d`; do not report this unchanged behavior as failed whole-command pruning, null the required command, or introduce a field-level closure cleaner. Separate commands when testing exclusion of a wholly unused command. This boundary probe is an inference, not a compiled historical fixture. An object-only command needed by a macro, or an intentional user singleton reference, retains its distinct semantics; do not demand universal class wrapping or suppressed singleton initialization.

## Limitations

This history supports JVM Scala 2 capture behavior, not Scala.js/Native or present-day Scala 3 parity. The 2019 change strengthens the test harness; it is not an independent reviewer endorsement of every 2018 design decision. Serialization of untrusted bytes is out of scope.

## Sources

- [PR 736: why direct imports fail capture](https://github.com/com-lihaoyi/Ammonite/pull/736#issuecomment-355239967), [symbol-based alternative](https://github.com/com-lihaoyi/Ammonite/pull/736#issuecomment-355323534), and [structured metadata](https://github.com/com-lihaoyi/Ammonite/pull/736#issuecomment-359009219).
- [PR 944 type-dependency collector](https://github.com/com-lihaoyi/Ammonite/blob/50e075ddd8fb223046ae7be68827bc744e3c6037/amm/interp/src/main/scala/ammonite/interp/AmmonitePlugin.scala#L149-L160) and [previous-command trait regression](https://github.com/com-lihaoyi/Ammonite/blob/50e075ddd8fb223046ae7be68827bc744e3c6037/amm/repl/src/test/scala/ammonite/session/EvaluatorTests.scala#L353-L367): source-backed inference, not a substantive reviewer exchange.
- [Whole-command nulling](https://github.com/com-lihaoyi/Ammonite/blob/74306e64a5717fa6f185ed85047b48d11c6a66b0/amm/interp/src/main/scala/ammonite/interp/Preprocessor.scala#L435-L437) and [separate-command serialization fixture](https://github.com/com-lihaoyi/Ammonite/blob/74306e64a5717fa6f185ed85047b48d11c6a66b0/amm/repl/src/test/scala/ammonite/session/SerializationTests.scala#L54-L62).
- [2019 isolated-loader serialization test](https://github.com/com-lihaoyi/Ammonite/blob/b7275a45d5aa4a2d1242e70e8a87a15c6aef0541/amm/repl/src/test/scala/ammonite/session/SerializationTests.scala#L74-L90).
- [2021 compiler guard and disabled Scala 3 case](https://github.com/com-lihaoyi/Ammonite/blob/5c4d79f1b023a80583444d5593073c216c325b5a/amm/repl/src/test/scala/ammonite/session/SerializationTests.scala#L7-L11).
