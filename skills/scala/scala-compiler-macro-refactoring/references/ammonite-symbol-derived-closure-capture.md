# Ammonite (com-lihaoyi/Ammonite): symbol-derived REPL closure capture

Originally `scala-ammonite-symbol-derived-closure-capture`. Evidence: [evidence/scala-ammonite-symbol-derived-closure-capture.json](evidence/scala-ammonite-symbol-derived-closure-capture.json) (claims `c-capture`, `c-metadata`).

## Scope

Use for changes to class-based REPL wrapping, compiler extraction of `usedEarlierDefinitions`, transport of that metadata, or serialization-test isolation. Source-equivalent import rewrite can change serialized object graph. Refactoring procedure for that mechanism, not general Scala style guide.

Not for: ordinary application imports, BSP repository propagation (see [ammonite-static-script-dependency-propagation.md](ammonite-static-script-dependency-propagation.md)), arbitrary Java deserialization security, or every singleton in REPL. Object-only command deliberately kept singleton wrapping for macro ownership. Do not add effect runtime to Ammonite.

## Prerequisites

Identify checkout SHA, actual compiler patch version, caller-selected wrapper, JDK/test-runner arrangement. Primary implementation: Scala 2.12.4/JVM with uTest 0.6.0 in PR 736. Plugin lives in `amm/interp`; later compiler extraction moves packages, so trace symbols instead of copying paths.

Read `CodeClassWrapper`, compiler's used-command collector, compilation output/session bridge, `SerializationTests`. 2018 layout nests wrapper in `Preprocessor`. 2019 test isolation revision moves serialization helpers into separate test API and calls `cloneClassLoader(null)`. In 2021 this suite explicitly selects a disabled test on Scala 3: coverage boundary, not evidence all Scala 3 closures are unserializable.

## Workflow

1. **State command-granularity invariant.** Keep required earlier-command instances as captured values; null only wholly unused command references. Not field-level closure cleaning: unused siblings inside required `Helper` can stay reachable. Serialization succeeds only if retained reachable graph is serializable. For ordinary captured values, deserializing and invoking must not rerun initialization. Intentional singleton references keep different semantics.
2. **Trace both term- and type-derived dependencies.** Locate phase relative to typer and wrapper symbol. PR 736's `Select` receiver-symbol matching was incomplete. PR 944 adds `TypeTree.tpe` traversal, collecting `SingleType` names whose prefix type symbol equals wrapper symbol, then deduplicates combined names. Keep commands required through trait bounds/path-dependent types as well as term selections. Reject `tree.toString`/regex matching and lookalike string literals. These are Scala 2 compiler-internal shapes, not APIs to copy into Scala 3; rediscover equivalent typed dependency paths for another compiler.
3. **Trace metadata with compiled command.** Follow callback/output, cache/session storage, runtime bridge. Verify result belongs to command being instantiated, including cache hits and session restoration. Do not hide it in a classpath resource to avoid threading a field through existing structures. These lifecycle checks extend historical review rationale; they do not claim every lifecycle regressed in PR 736.
4. **Preserve wrapper's exceptions.** Check object-only commands, wrapper nesting levels, import rewriting. 2018 plugin explicitly distinguishes nesting levels 1 and 2; silently accepting another shape is not equivalent. Do not remove intentional unused-reference nulling only to apply modern application-style rule.
5. **Exercise genuinely separate loader.** Put nonserializable unused `d` in one command, captured `a` with sentinel-producing initializer in second, closure using `a` in third. Serialize, clear sentinel, deserialize with isolated generated classes, invoke. Require successful serialization, no new sentinel, expected result. Historical test checks sentinel but discards reflected return value; result assertion is proposed stronger oracle. Keep separate same-command sibling case to show scope limit, not to demand field pruning.
6. **Test type dependencies independently of serialization.** Reproduce PR 944's evaluator transcript: define `trait A` and `class X` together; in next command define `class Z[T <: A]` and construct `z1`; in third construct `z2`. Both results must print `Z(X(7))`, without null-reference exception under class wrapping. Inspect `DualTestRepl` dispatch; do not assume object-wrapper run covers it.
7. **Prove oracles discriminate.** In separately authorized checkout, try three isolated mutations: direct singleton imports, retaining wholly unused nonserializable command, dropping only type-derived dependency collection. Expect, respectively, reinitialization, serialization failure, evaluator regression. Restore each mutation. Literal-lookalike/cache-restore probes and mutation outcomes stay proposed until executed. Never claim serialization sentinel alone validates type retention.

## Checks

- Preserve capture identity at **command** granularity, not merely names/output or minimal field set. Do not solve unused capture by requiring every session value to implement `Serializable`, or by nulling a command needed through a type.
- Preserve compiler/runtime metadata association. Stale comment mentioning `tree.txt` does not prove final implementation reads that resource; inspect generated bridge expression.
- Verify classloader separation explicitly. 2019 harness asserts test API loader differs from thread context loader; serialization test passes null parent to its clone. Preserve intended isolation, not necessarily that exact API on newer version.

## False positives

Source generation using strings is not itself forbidden.

## Validation

Do not execute historical upstream code during read-only research task. For authorized development checkout, first inspect build, launcher pin, JDK matrix, generated test resources, suite guards.

At PR 736's pinned revision, `build.sbt` defines `ammRepl`; author reports `sbt "ammRepl/testOnly ammonite.session.SerializationTests"`. Confirm real closure case runs with class wrapper. Keep `-Ydelambdafy=inline` test-local; never copy it into Scala 3.

At PR 944's SHA `50e075ddd8fb223046ae7be68827bc744e3c6037`, actual build is Mill: CI uses `mill -i unitTest`, provisions Mill 0.3.3, declares Scala 2.11.12/JDK 8 and 2.12.8/JDK 8 or 11 with uTest 0.6.0. With those separately authorized prerequisites, `TRAVIS_SCALA_VERSION=2.12.8 mill -i unitTest` dispatches `amm.repl(scalaVersion).test.test()()`. First check Git tags/master and build imports. Do not substitute `./mill` or 2018 sbt selector without discovering that checkout's launcher. Command is broad; discover version-matching filters for narrower run. Verify `EvaluatorTests.referenceTraitFromPreviousCommand` runs through class-wrapper member of `DualTestRepl`, not merely its object-wrapper member.

Record compiler, JDK, wrapper, suite, executed case count, sentinel/result assertions, command partition, loader identity. Require both serialization and type-reference evaluator oracles; one cannot stand in for the other. Green Scala 3 `disabled` case is insufficient. Report prerequisite failures as blocked validation instead of sharing initialized singletons. Later documentation-only `build.sbt` is not the main REPL test build. Research established no upstream compilation or behavioral effectiveness.

## Examples

**Good.** Wrapper refactor keeps union of term- and type-derived command dependencies. Unused `d` sits in a **different command** from captured `a = Option(2)`; retained graph of `a` is serializable. Closure round trip checks initialization is not repeated, plus result assertion for current validation. Separately, PR 944's `A`/`X` then `Z[T <: A]` transcript retains required command through types and produces both `Z(X(7))` results. Distinct oracles, not universal minimal-capture promise.

**Broken and correction.** Cleanup replaces stored `cmd0` reference with `import ...cmd0.instance.a` because names still resolve. Deserialization reinitializes `a`. Correction: keep instance capture and structured typed-dependency metadata. Reject text scan of `cmd2.this.cmd0` using lookalike literal control.

Another cleanup keeps symbol equality but drops `TypeTree` branch as redundant with `Select`. Correction: restore type-derived names in used-command union; run `referenceTraitFromPreviousCommand` with class wrapping.

**Negative.** Hypothetical command defines `a = Option(2)` and nonserializable `d` together; later closure uses `a`. Retained command may include `d`. Do not report this unchanged behavior as failed whole-command pruning, null required command, or introduce field-level closure cleaner. Use separate commands when testing exclusion of wholly unused command. This boundary probe is inference, not compiled historical fixture. Object-only command needed by macro, or intentional user singleton reference, keeps distinct semantics; do not demand universal class wrapping or suppressed singleton initialization.

## Limitations

History supports JVM Scala 2 capture behavior, not Scala.js/Native or present-day Scala 3 parity. 2019 change strengthens test harness; it is not independent reviewer endorsement of every 2018 design decision. Serialization of untrusted bytes is out of scope.

## Sources

- [PR 736: why direct imports fail capture](https://github.com/com-lihaoyi/Ammonite/pull/736#issuecomment-355239967), [symbol-based alternative](https://github.com/com-lihaoyi/Ammonite/pull/736#issuecomment-355323534), and [structured metadata](https://github.com/com-lihaoyi/Ammonite/pull/736#issuecomment-359009219).
- [PR 944 type-dependency collector](https://github.com/com-lihaoyi/Ammonite/blob/50e075ddd8fb223046ae7be68827bc744e3c6037/amm/interp/src/main/scala/ammonite/interp/AmmonitePlugin.scala#L149-L160) and [previous-command trait regression](https://github.com/com-lihaoyi/Ammonite/blob/50e075ddd8fb223046ae7be68827bc744e3c6037/amm/repl/src/test/scala/ammonite/session/EvaluatorTests.scala#L353-L367): source-backed inference, not a substantive reviewer exchange.
- [Whole-command nulling](https://github.com/com-lihaoyi/Ammonite/blob/74306e64a5717fa6f185ed85047b48d11c6a66b0/amm/interp/src/main/scala/ammonite/interp/Preprocessor.scala#L435-L437) and [separate-command serialization fixture](https://github.com/com-lihaoyi/Ammonite/blob/74306e64a5717fa6f185ed85047b48d11c6a66b0/amm/repl/src/test/scala/ammonite/session/SerializationTests.scala#L54-L62).
- [2019 isolated-loader serialization test](https://github.com/com-lihaoyi/Ammonite/blob/b7275a45d5aa4a2d1242e70e8a87a15c6aef0541/amm/repl/src/test/scala/ammonite/session/SerializationTests.scala#L74-L90).
- [2021 compiler guard and disabled Scala 3 case](https://github.com/com-lihaoyi/Ammonite/blob/5c4d79f1b023a80583444d5593073c216c325b5a/amm/repl/src/test/scala/ammonite/session/SerializationTests.scala#L7-L11).
