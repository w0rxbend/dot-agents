---
name: scala-compiler-macro-refactoring
description: Use when refactoring or reviewing Scala compiler plugins, macros/inline combinators, or REPL/script tooling where the risk is changing what is captured, when it runs, or what the compiler sees - Acyclic whole-run Scala 2/3 analysis and diagnostics, sourcecode Args argument capture, Ammonite symbol-derived closure capture and static BSP script dependency propagation, and Fastparse shared-run combinator extraction. Not for effect cancellation, stream scoping, HTTP semantics, compatibility laws, or runtime hot-path cost.
license: MIT
---

# Scala compiler, macro and REPL refactoring

A compiler plugin, a macro, an inline combinator and a REPL wrapper all generate or analyse code on someone else's behalf. A refactor that leaves names, types and a green test run intact can still change **what is captured** (a value, a command instance, a dependency tree), **when or how often it runs** (per unit versus per run, eager versus deferred, re-initialized on deserialization), or **what the compiler sees** (a syntactic proxy instead of a symbol, an inserted implicit view, a type clause read as a term clause). This skill holds the shared model distilled from five historical case studies and routes to their library-specific procedures.

Each case was authored from pinned 2018-2024 source and maintainer review history, then audited. No upstream build or test was executed during that research; every proposed test below is unexecuted until you run it.

## When to Use

- Changing a compiler plugin's phase callbacks, shared analysis, or reporter adapter, especially when porting between Scala 2 and Scala 3.
- Changing a macro or inline entrypoint that captures enclosing-scope information (parameters, owners, values).
- Changing REPL/script wrapper generation, used-definition tracking, serialized closure capture, or static (IDE/BSP) dependency extraction for scripts.
- Extracting or consolidating parser/combinator code whose children run against shared mutable run state, or changing an implicit hook every combinator invokes.
- Reviewing a test that claims to cover one of the above but may observe only names, sets, or compile success.

## When Not to Use

- Ordinary application cycles, imports, dependency bumps, or logging of values already supplied explicitly.
- Generic ABI/binary-compatibility or law-backed instance questions: use `scala-library-compatibility-laws` or `scala-library-contracts`.
- Allocation, closure or bytecode cost with unchanged semantics, or failure-label/diagnostic-mode work with unchanged control flow: use `scala-runtime-diagnostics-hot-paths`.
- Effect cancellation/finalization (`scala-effect-cancellation-finalization`), stream resource scoping (`scala-stream-resource-scoping`), HTTP server semantics (`scala-http-server-semantics`).
- General type-level design (`scala-type-system`), FP structure (`scala-functional-patterns`), or library triage (`scala-oss-library-review`, the router).
- Do not introduce Cats Effect, ZIO, Ox or a lazy wrapper into these synchronous compiler/macro/REPL code paths; none of the sources support it.

## Prerequisites

1. Pin the exact revision, Scala compiler patch versions, platform versions (JVM/JS/Native), build tool and launcher version, test framework, and JDK. Calendar year never selects a compiler API.
2. Read the actual build and CI of that revision. Every case found that the obvious command was wrong for at least one era (sbt versus Mill; `./mill` versus `mill`; main-driven `test.run` versus a framework selector).
3. Identify the compiler-specific source roots (`src-2`, `src-3`, version-specific test roots) and the shared code between them.
4. Load the matching case reference from the routing table before proposing a patch.

## Routing Table

| Change touches | Load |
| --- | --- |
| Acyclic `RuntimePlugin`/`TestPlugin`, `PluginPhase` (`src-2`/`src-3`), `BasePluginPhase.runAllUnits`, `GraphAnalysis`, `reportInform`/`report.echo`, `TestUtils.make`/`makeFail`, `BaseCycleTests`, bootstrap self-plugin exclusions; any plugin that does whole-run work from a per-unit callback | [references/acyclic-whole-run-compiler-adapters.md](references/acyclic-whole-run-compiler-adapters.md) |
| sourcecode `Args`, `argsImpl`, `SourceContext.scala`, `src-2`/`src-3` `Macros.scala`, `ArgsTests` via `Main`/`Tests.run`; any macro reading parameter clauses, `ValDef` RHS, or enclosing owner | [references/sourcecode-args-capture-review.md](references/sourcecode-args-capture-review.md) |
| Ammonite `CodeClassWrapper`, `Preprocessor`, `AmmonitePlugin` used-command collector (`usedEarlierDefinitions`), session/cache bridge, `SerializationTests`, `EvaluatorTests`, `DualTestRepl`; any REPL wrapper whose import rewriting changes the captured object graph | [references/ammonite-symbol-derived-closure-capture.md](references/ammonite-symbol-derived-closure-capture.md) |
| Ammonite import hooks (`$repo`, `Result.Repo`), `Script.Dependencies`, `noDuplicates`, `ScriptProcessor.jarDependencies`/`jarPluginDependencies`, `ScriptCompiler`, BSP `scriptScalacOptions`, `AmmoniteBuildServerTests`; any static (IDE) extraction that mirrors an interactive interpreter | [references/ammonite-static-script-dependency-propagation.md](references/ammonite-static-script-dependency-propagation.md) |
| Fastparse `ParsingRun`, `P`, sequence/`.rep`/`.repX` macros (`MacroRepImpls`), higher-order wrappers such as `Indexed`, `Whitespace`, cuts in reusable whitespace/comment parsers, Scala 2 -> 3 combinator ports; any combinator library over a shared mutable run | [references/fastparse-shared-run-combinator-extraction.md](references/fastparse-shared-run-combinator-extraction.md) |

Pinned evidence for every case is in `references/evidence/` (exact copies of the original records; claim and record IDs cited in the references resolve there).

## Shared Model

These invariants recur across the cases. Each names the cases that demonstrate it; transfer to other libraries is an inference unless that library's source shows the same mechanism.

**M1. Capture the identity, not a syntactic proxy.** The captured thing must be what the runtime or compiler actually refers to.
- sourcecode: a parameter's optional `ValDef` RHS is not the caller's argument; PR 126 replaces the RHS/`None` fallback with `Ref(vd.symbol).asExpr`.
- Ammonite closure: `import ...cmd0.instance.a` resolves the same name but captures a singleton path, so deserialization reinitializes `a`; the command instance must be captured.
- Acyclic: dependency edges must retain their trees (positions, symbol names, supplemental lines), not just connectivity booleans.
- All three reject string-based substitutes: `tree.toString`/regex scans (Ammonite), rebuilt initializers or re-evaluated call-site expressions (sourcecode).

**M2. Derive dependencies from typed symbols, across both term and type paths.**
- Ammonite PR 944: `Select` receiver matching missed commands needed only through types; traversal of `TypeTree.tpe` for `SingleType` prefixes equal to the wrapper symbol fixed it. Dropping either branch breaks a different oracle.
- sourcecode: term clauses and type clauses must be classified by the compiler's real discriminator; erased `List[ValDef]` versus `List[TypeDef]` matching does not work (PR 103 extension-method counterexample, cast still present in late-2024 source).
- Acyclic: validity, different-source-file and `unitMap.contains(symbolPath(sym))` guards precede lookup; out-of-run symbols are not invented edges.

**M3. Execution count and timing belong to the right lifetime.**
- Acyclic: whole-run analysis from a per-unit callback ran once per file and duplicated diagnostics; it must run once per compilation run, and a second supported run must not be suppressed.
- Fastparse: a child parser executes at its original position, once; by-name for ordinary wrappers (PR 212 `Indexed`), inspected staging for macros.
- Ammonite closure: deserializing and invoking a captured value must not rerun its initializer.
- Ammonite static: dependency extraction must not evaluate arbitrary script bodies (hooks go through a dummy interpreter interface; that is an architectural boundary, not a sandbox).
- sourcecode: `Args` must materialize at the call site in the intended owner; extracting a helper that materializes it elsewhere changes the owner.

**M4. Know who owns mutable state and when it is reset.**
- Fastparse: a `val` holding a `ParsingRun` is not a snapshot; save child results into locals before a sibling overwrites `index`/`isSuccess`/`successValue`/`cut`/diagnostics/`noDropBuffer`.
- Acyclic: `alreadyRun` is plugin-instance state that `init` does not visibly reset; whether production reuses the instance is not established by the source.
- Ammonite static: the stateful Interpreter mutates its repositories while static `Script` metadata carries `extraRepositories`; both consumers are intentional and must not be merged.
- Ammonite closure: used-command metadata must stay associated with the command being instantiated, including cache hits and session restoration.

**M5. Metadata must survive every transformation to its final consumer.**
- Ammonite static: repositories through extraction, `Dependencies.+`, `noDuplicates`, and both ordinary and plugin resolution, to the dependent target's classpath.
- Acyclic: supplemental dependency lines through shared graph code to a default-visible reporter (`report.echo`, not verbose-only `inform`).
- Fastparse: diagnostic aggregates keep their child provenance after extraction.
- sourcecode: ordered outer-list grouping of term clauses survives to `Args.value`.

**M6. Keep compiler-specific representation in adapters; share only matching semantics.**
- Acyclic PR 136: share graph operations, keep bespoke tree/symbol/unit traversal and reporting per compiler.
- sourcecode: Scala 2 uses method symbols/`paramLists`, Scala 3 inspects definition trees; a common helper must not assert their equivalence.
- Ammonite: PR 944's `TypeTree`/`SingleType` shapes are Scala 2 internals, not APIs to copy into Scala 3; `-Ydelambdafy=inline` stays test-local.
- Fastparse: Scala 2 split common macros from runtime methods while Scala 3 shares one macro that inspects inline values; PR 310 shows compiler-internal test adapters need version-specific roots.

**M7. Check what the compiler inserts.**
- Fastparse PR 272: a function-typed implicit (`P[_] => P[Unit]`) was applied by Scala 2 as an implicit view, rewriting `Fail.!` into a whitespace call that overwrote the failure. Repair: a dedicated trait/SAM type plus a regression asserting `Parsed.Failure`; the trait change was binary incompatible and timed for 3.0.0.
- sourcecode: the implicit `Args` is materialized wherever the compiler resolves it, which defines the inspected owner.

**M8. The oracle must observe the invariant, and must actually run.**
- Observe the right thing: raw diagnostic events before set canonicalization (Acyclic); full nested `(name, value)` pairs with varying values (sourcecode); sentinel plus result plus a separate type-dependency evaluator transcript (Ammonite closure); dependent-target classpath plus an inverse case plus hook removal (Ammonite static); value plus consumed index plus `End` (Fastparse).
- Actually run: an unasserted `make(...).exists(...)` (Acyclic 2022); a names-only Scala 3 exemption (sourcecode 2022); a Scala 3 `disabled` case or an object-wrapper-only `DualTestRepl` run (Ammonite); a `scala2_11` guard that disabled the regression (Ammonite PR 1090); main-driven assertions reachable only via `__.test.run` (sourcecode).
- Prove discrimination with a mutation that must make the test fail (remove the once-per-run gate, revert to RHS fallback, import singletons directly, drop the `TypeTree` branch, remove the repo hook, re-add the comment cut).

## Workflow

1. **Classify the boundary** (transferable). Is the change in compile-time analysis, compile-time code generation, generated-code runtime, or test harness? Distinguish ordinary parameter, by-name, inline receiver, quoted expression, macro surface parameter, and completed value.
2. **Write the behavioural baseline** (transferable). For each output the user observes, record: what is captured (M1), from which symbol/type paths (M2), when and how often it runs (M3), which state it reads/writes and who resets it (M4), and which consumer finally reads the metadata (M5).
3. **Draw the adapter boundary** (transferable). List compiler-specific operations versus shared semantics (M6). Refuse a shared helper that hides a representation difference.
4. **Trace every transformation to the consumer** (transferable). Follow the value/metadata through folds, merges, deduplication, caches and reporters. Preserve ordering and dedup semantics; do not swap sequences for sets.
5. **Check compiler insertions** (transferable). Implicit views from function-typed implicits, implicit materialization site, inline expansion. Compile with conversion diagnostics when execution is authorized.
6. **Apply the smallest change** (transferable). Keep publication/toolchain edits separate. Route ABI consequences to compatibility guidance.
7. **Repair the oracle with the code** (transferable). Strengthen to observe M1-M5, confirm the test is reached on each claimed compiler cell, and specify a mutation that must fail (M8).
8. **Apply the case-specific procedure** (library-specific). Load the routed reference and follow its version-pinned steps, probe matrix and validation commands.

## Review and Refactoring Checks

| Check | Scope |
| --- | --- |
| Captured value is a symbol/instance reference, not an initializer, singleton path or text match (M1) | Transferable |
| Dependencies include type-derived paths, not just term selections (M2) | Transferable; collector shapes are Scala 2 Ammonite-specific |
| Term versus type clauses classified by the compiler's real discriminator; empty term clauses and group order preserved (M2) | Transferable; API is compiler-version-specific |
| Whole-run work executes once per run, keyed to the real run lifetime, not reset per callback (M3, M4) | Transferable; `alreadyRun` placement is Acyclic-specific |
| Children/arguments execute at their original position and count; earlier results saved before shared state is overwritten (M3, M4) | Transferable to any shared-run combinator library |
| Deserialization does not rerun captured initializers; unused whole commands nulled, required ones kept (M1, M3) | Ammonite class-wrapper-specific; command (not field) granularity |
| Static extraction does not evaluate script bodies; static and interactive consumers both updated (M3, M4) | Transferable pattern; `Result.Repo`/`extraRepositories` Ammonite-specific |
| Metadata survives merge/dedup and reaches every sibling consumer (ordinary and plugin resolution; reporter) (M5) | Transferable |
| Default visibility and severity of diagnostics unchanged; no byte-identical caret demands across compilers (M5) | Transferable; `echo` versus `inform` is Scala 3 Acyclic-specific |
| No function-typed implicit that Scala 2 can apply as a view (M7) | Transferable to Scala 2 libraries |
| Cuts/commitment inside reusable sub-parsers checked against the enclosing repetition/alternative (M3) | Fastparse-specific mechanism; transferable to cut-based parsers |
| Specialized generated paths not replaced by runtime branching on consolidation | Fastparse-specific; measure separately from correctness |
| Oracle observes raw/complete payload, runs on every claimed cell, and has a failing mutation (M8) | Transferable |
| Bootstrap/self-applied plugin not pre-rejecting test resources | Acyclic-specific, revision-dependent |

## Consolidated False Positives

- **Acyclic:** `makeFail` asserts internally, so its call site needs no outer `assert`; `acyclic.pkg` package-internal cycles (`success/pkg/innercycle`) are deliberate; distinct cycles may legitimately produce multiple diagnostics; caret-format differences are not drift; the 2024 build need not restore 2022 bootstrap exclusions; an analyzer that intentionally processes one unit per callback needs no whole-run guard.
- **sourcecode:** an empty `Seq()` for a parameterless method is correct; a names-only API need not capture values; an empty `testFramework` does not disable main-driven assertions; a suspicious cast justifies a targeted counterexample, not a claimed crash on every compiler; IO wrappers, framework migration or public `Args` flattening are not repairs; a `Name`-only formatting change is out of scope unless it alters shared ownership.
- **Ammonite closure:** a nonserializable sibling in the same required command can stay reachable (not a closure cleaner); intentional singleton references and object-only commands (kept for macro ownership) keep their initialization semantics; string-based source generation is not itself forbidden; a disabled Scala 3 variant is a coverage boundary, not proof Scala 3 closures are unserializable.
- **Ammonite static:** stateful REPL execution is intentional; a private synchronized `addRepository` helper is not API widening; generated inert imports are not the resolution effect; a different classloader topology is not automatically defective and isolated compilation does not require a classloader DAG; multi-stage scripts need their own contract.
- **Fastparse:** macro surface parameters can be staged without looking by-name; storing immutable `Parsed` results is safe; an intentional cut after a unique prefix may be necessary; an explicit non-implicit function parameter cannot become a view; removing all cuts or retaining all input is not a bounded repair; Scala 3 quote hygiene does not authorize removing Scala 2 qualification; shared source is not inherently slower.
- **All:** a merge or approval adds no independent behavioural proof; an open proposal (Fastparse #204) or an author report (#323, Acyclic PR 136 experiments) is not an adopted mechanism or a reproduced result.

## Version Fences

| Case | Pinned eras (historical, not recommendations) |
| --- | --- |
| Acyclic | 2022 `e090ee2b`: Scala 2.11.12/2.12.8-2.12.17/2.13.0-2.13.10, Mill 0.10.10, uTest 0.8.1, `(position, message, severity)` tuples. 2024 `fbb60d12`: adds Scala 3.3.0-3.5.1 via `src-3`, Mill 0.11.12, uTest 0.8.2, `(message, severity)` pairs; CI declares Java 8. JVM only. |
| sourcecode | PR 103: Scala 3.0.0-RC1 (2021). PR 126 (2023): Scala 3.1.3, 2.11.12/2.12.16/2.13.8, JS 1.10.1, Native 0.4.5. Nov 2024: 2.12.16/2.13.8/3.3.3, JS 1.17.0, Native 0.5.0, Mill 0.12.0. |
| Ammonite closure | PR 736 (2018): Scala 2.12.4/JVM, uTest 0.6.0, sbt `ammRepl`. PR 944 `50e075dd`: Mill 0.3.3 via `mill`, Scala 2.11.12/JDK 8 and 2.12.8/JDK 8 or 11. 2019 isolated-loader test; 2021 Scala 3 case disabled. |
| Ammonite static | PR 1090 `7017cb94` (June 2020): Scala 2.12.11/2.13.2, BSP 2.0.0-M6, coursier-interface 0.0.21, uTest 0.7.3, Mill 0.7.0 default; CI 2.12.11 with JDK 8/11, 2.13.2 with JDK 8. JVM Scala 2 only. |
| Fastparse | 2020: Scala 2.12.10/2.13.1 JVM. 2022: repetition under `src-2`. 2024: Scala 3.3.3/2.13.14/2.12.19, Scala.js 1.16.0, Native 0.5.1. Fastparse 1 is outside the shared-run model. Whitespace trait (PR 272) lands at 3.0.0. |

## Validation

- No upstream build or test was executed while researching any of these cases. Report every proposed test as `not executed` until you run it.
- Discover commands from the target revision's build file, launcher pin (`.mill-version`, `MILL_VERSION`, wrapper script) and CI workflow; then trace from the CI entry to the specific test. Historical examples: Acyclic `./mill -i -j 0 __.publishArtifacts + __.test`; sourcecode `./mill -i '__.test.run'`; Ammonite `TRAVIS_SCALA_VERSION=2.13.2 ./mill -i unitTest` (2020) and `TRAVIS_SCALA_VERSION=2.12.8 mill -i unitTest` (PR 944); Fastparse `./mill -i --disable-ticker __.jvm.__.publishArtifacts + __.jvm.__.compile + __.jvm.__.test` with focused selectors such as `'fastparse.jvm[3.3.3].test'`. Each is valid only for its pinned revision.
- Run only in a separately authorized, isolated, trusted checkout with the matching toolchain. Never run publish/release/signing jobs. Static inspection, hooks, resolution and macros can execute code or touch the network.
- Confirm the target test actually ran on each claimed compiler/platform cell (case count, wrapper member, not a disabled variant). JVM success is not JS/Native coverage.
- Run the specified mutation for each strengthened oracle and require failure, then restore.
- Keep correctness separate from throughput or generated-code-size measurement.

## Examples

### Good

A Scala 3 port of an analysis plugin keeps traversal and reporting in `src-3`, shares only graph policy, gates whole-run analysis to the run lifetime, reports supplemental lines with a default-visible call, and adds a raw-event test for a two-file cycle plus an unrelated third file that still expects one top-level diagnostic (Acyclic). The same discipline applied to a macro: reference the parameter symbol, assert complete nested `(name, value)` pairs across two invocations with different values (sourcecode).

### Broken and Correction

A cleanup makes a generated wrapper "simpler": it rewrites a captured instance to a direct import (Ammonite), or changes a by-name child to a strict parameter (Fastparse `Indexed`), or reads a parameter's default RHS (sourcecode). Names and types still resolve and existing name-only or success-only tests pass. Correction: restore instance/symbol capture and deferred execution, then add the oracle that observes the lost property (no reinitialization sentinel plus result; nested value/offset tuple; full value pairs) and its failing mutation.

### Negative

A diff only bumps a release number, edits `sourcecode.Name` formatting, changes an application import, or formats an already-produced `Parsed.Success`. None changes capture, timing or compiler-visible structure; decline this workflow rather than demanding macro surgery, by-name parameters or new compiler tests.

## Output Contract

For each finding return: `file:line`, severity, the violated invariant (M1-M8 plus the case-specific invariant), exact revision and compiler/platform cell, evidence record or claim ID from `references/evidence/` or a pinned source URL, minimal correction, and a discriminating test with its expected failure under mutation. Label each statement as historical observation, reviewer guidance, author report, new inference, or your own execution. Include tested versus untested cells, the actual command and result or `not executed`, and blockers. If no defect is found, list which capture/timing/state/metadata/insertion paths were checked and which remain untested.

## Limitations

- Five bounded historical samples (2018-2024), mostly from com-lihaoyi libraries; the shared model is a synthesis and is inference when applied elsewhere.
- No upstream build, test, mutation, reused-instance or cache-independence check was executed during research. Structural validity of this skill is not behavioural effectiveness.
- Unresolved in the sources: Acyclic plugin-instance reuse across runs; sourcecode mixed term/type clause classification (no compiled repair); Ammonite Scala 3 closure capture; Ammonite static semantics on Scala 3 or later BSP APIs and for multi-stage scripts.
- Mostly JVM evidence; Scala.js/Native behaviour needs separate validation. Untrusted deserialization and untrusted hook execution are out of scope.

## Sources

- Case procedures: the five `references/*.md` files in the routing table.
- Pinned evidence (byte copies of the original records): [acyclic](references/evidence/scala-acyclic-whole-run-compiler-adapters.json), [sourcecode](references/evidence/scala-sourcecode-args-capture-review.json), [Ammonite closure](references/evidence/scala-ammonite-symbol-derived-closure-capture.json), [Ammonite static](references/evidence/scala-ammonite-static-script-dependency-propagation.json), [Fastparse](references/evidence/scala-fastparse-shared-run-combinator-extraction.json).
- Key upstream discussions: [Acyclic PR 136](https://github.com/com-lihaoyi/acyclic/pull/136#discussion_r1760522833), [sourcecode PR 103](https://github.com/com-lihaoyi/sourcecode/pull/103#discussion_r577846016), [Ammonite PR 736](https://github.com/com-lihaoyi/Ammonite/pull/736#issuecomment-355239967), [Ammonite PR 1090](https://github.com/com-lihaoyi/Ammonite/pull/1090#issuecomment-638956149), [Fastparse PR 272](https://github.com/com-lihaoyi/fastparse/commit/22051f098d4cf3f2cb7510ba214cbf2e9b478108).
