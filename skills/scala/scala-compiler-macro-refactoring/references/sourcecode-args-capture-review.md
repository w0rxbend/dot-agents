# sourcecode (com-lihaoyi/sourcecode): `Args` macro capture

Originally `scala-sourcecode-args-capture-review`. Evidence: [evidence/scala-sourcecode-args-capture-review.json](evidence/scala-sourcecode-args-capture-review.json) (claims `c-args-versioned-boundary`, `c-args-runtime-values`, `c-parameter-clause-boundary`, `c-assertion-runner`; source observations marked as inference; discussion attribution date-bounded).

Review path from compiler parameter definitions to nested runtime `Text` payload, not only macro compilation.

## Scope

Use for `sourcecode.Args` materialization bugs, `argsImpl` changes, compiler upgrades touching parameter clauses, enclosing-method/constructor selection refactors, or tests claiming value-capture repair yet comparing only parameter names.

Not for: ordinary `Name`, `Line`, `File`, `Text` use; names-only reflection utilities; generic ABI reviews; build-only platform upgrades unrelated to Args. Logging explicitly supplied values needs no macro surgery. Keep library's plain-value contract; add no effect runtime or new lazy wrapper.

## Prerequisites

Before suggesting patch, identify target commit, Scala compiler and platform versions, build pin, public Args shape. Read shared `SourceContext.scala`, selected `src-2`/`src-3` implementation, `ArgsTests.scala`, and its `Main`/`Tests` invocation.

Historical anchors, not current-version guarantees:

- PR 103 (2021) discusses Scala 3.0.0-RC1 parameter clauses and erasure.
- PR 126's 2023 repair build declares Scala 3.1.3, Scala 2.11.12/2.12.16/2.13.8, JS 1.10.1, Native 0.4.5 (`e-build-2023`).
- November 2024 snapshot declares Scala 2.12.16/2.13.8/3.3.3, JS 1.17.0, Native 0.5.0, Mill 0.12.0 (`e-build-2024`, `e-platforms-2024`, `e-mill-pin-2024`).

Calendar year alone does not select compiler API. No effect-library version to migrate here. For other compiler versions, inspect actual reflection representation; do not transplant modern helper into old release. Shared runtime wrappers differ from compile-time reflection code. Default-public implementation helpers are not automatically private API.

## Workflow

1. **State the payload invariant.** `Args.value` keeps ordered argument lists, each with parameter name and supplied value. Do not flatten outer sequence or swap declaration syntax for runtime values. Distinguish parameterless method from method with empty term clause; historical test covers former, not every empty-clause representation.
2. **Trace ownership.** Follow implicit/inline entrypoint into `argsImpl`. Inspect method and constructor branches, and how lookup walks out of nested local blocks. Scala 2 uses method symbols/`paramLists`; Scala 3 inspects definition trees. Common helper must preserve both representations, not assert equivalence.
3. **Identify the value source.** Parameter's optional `ValDef` RHS is not caller's argument. PR 126 replaces RHS/`None` fallback with `Ref(vd.symbol).asExpr` in generated `Text`. Keep symbol ownership and names; do not rebuild initializer or re-evaluate call-site expression. Verify target compiler has equivalent operation.
4. **Classify clauses before reading values.** Challenge every `List[ValDef]` cast in method and constructor paths. RC1 reviewer flagged extension blocks and methods both having type parameters. Matching erased `List[ValDef]` versus `List[TypeDef]` does not solve this. Use target version's real clause discriminator, or inspect individual tree kinds where representation requires. Keep empty term clauses and ordered term groups; exclude type clauses from runtime values. If representation or supported semantics unresolved, stop with regression request; do not claim complete fix.
5. **Strengthen the oracle with the repair.** Compare complete nested `(name, value)` pairs with nontrivial arguments, including two calls with different values. Keep curried methods, nested blocks, primary/secondary constructors, explicit/implicit argument cases. Remove names-only Scala 3 exemption only together with value fix. Mixed-clause support claim requires version-specific generic-extension consumer.
6. **Separate conclusions.** Report value capture, clause classification, assertion execution separately. PR 126 repairs first and strengthens tests; it does not demonstrate second. Unchecked cast still visible in late-2024 source. Neither merge nor approval proves all Scala 3 method shapes work.

## Invariants

Nearest intended callable, parameter names, supplied values, outer-list grouping, term-parameter order. Keep shared public representation stable while repairing compiler-specific internals. Check sibling constructor and method paths for same assumption; avoid unrelated metadata-macro rewrites.

## False positives

Name-only API need not capture values. Empty `testFramework` alone does not disable sourcecode's main-driven assertions. Suspicious cast warrants targeted counterexample, not proof of observed crash on every compiler release. Do not demand IO wrapper, framework migration, or public Args flattening as repair. `sourcecode.Name` owner-name formatting change alone needs no Args value fixtures unless it also changes shared ownership behavior Args uses.

## Evidence chain

| Record | Observation | What it does not establish |
|---|---|---|
| `e-api-2020` | Shared `Args` stores nested sequences of strict `Text` values. | By-name macro entrypoint does not make stored field lazy. |
| `e-args-broken-2022`, `e-args-oracle-2022` | Scala 3 reads optional initializer trees, substitutes `None`, tests names only. | Passing test process would not validate values. |
| `e-args-fixed-2023`, `e-args-oracle-2023` | PR 126 references parameter symbol, restores full equality. | Approval adds no design reasoning; mixed-clause case unresolved. |
| `e103-erasure`, `e103-counterexample`, `e-casts-2024` | RC1 discussion names erased clause distinctions and generic extension case; casts persist in later snapshot. | Do not assert same exact runtime error across all compiler representations, or claim verified classifier patch. |
| `e-args-scala2-owner`, `e-args-scala2-emission` | Scala 2 chooses method/constructor symbols and emits nested values. | Do not copy Scala 3 tree operations into this branch. |
| `e154-runner`, `e-main-2024`, `e-tests-dispatch-2024`, `e-ci-2024` | Main-driven assertions wired into `test.run`. | Wiring is not recorded execution. |

## Consumer regression specification

Keep parameter reference in enclosing callable's scope. Call debug/capture helper whose implicit `Args` materializes at call site; materializing inside separately extracted helper can change inspected owner.

2023 `ArgsTests` cases:

- Curried method has two ordered term groups.
- Local value block still captures surrounding method arguments.
- Primary constructor captures both groups; secondary constructor's later capture records its own parameters.
- Parameterless method records empty outer sequence.
- Implicit parameter records actual explicit or implicitly supplied value, not only name.

Extend corpus with original probes, labelled unexecuted until run:

1. Call same method with different values to separate runtime references from cached/default values. Do not use only literal `None` arguments: they would mask historical fallback bug.
2. Compare `def f` and `def f()` under chosen compiler. Establish whether representation keeps empty term clause; do not erase it as side effect of filtering type clauses.
3. Define extension block with type parameter and extension method with another type parameter. Materialize Args inside method. Inspect compiler's clause shape, identify expected receiver/term groups, assert names/values only for actual term parameters. Decide receiver exposure explicitly; historical review gives counterexample, not full expected payload.
4. Repeat classifier check in constructor extraction. Fixing only method branch leaves sibling cast assumption intact.

Correction must distinguish type clauses without erased generic-list tests. Where compiler has dedicated term-clause API, verify its signature and empty-clause behavior before use. On older list-of-trees representation, inspect tree kinds and homogeneous-clause invariants. Do not infer kind from nonexistent first element, or silently flatten/filter away meaningful structure.

## Review attribution

Alexarchambault explains erasure concern as PR 103's author. Li Haoyi's PR 56 access grant independently establishes Alexarchambault's historical commit/merge access; still not independent design review. Smarter gives extension-method counterexample; historical repository-maintainer status unverified. Li Haoyi explains his own main-runner design in PR 154. PR 126's value-source repair is source-derived lesson, not inferred reviewer preference. Do not attribute source-derived repairs to reviewer who only approved PR.

## Validation

Discover commands from target checkout's build file, launcher pin and CI; trace main to `ArgsTests`. At November 2024 SHA, CI includes `__.test.run`; derived test-only invocation: `./mill -i '__.test.run'`. Chain: `sourcecode.Main`, then `Tests.run`, then `ArgsTests`. Do not replace it with `sbt test`, guessed uTest selector, or compile-only task; conventional framework selector can miss that chain.

Run it only in separately authorized, trusted checkout with matching Mill/JDK and JS/Native prerequisites. This historical research executed no upstream builds. Rediscover selectors if checkout differs. Report missing platform toolchains; do not imply aggregate ran. Do not run publication/setup scripts as test substitutes. Publication success and binary-compatibility checks cannot replace value-sensitive consumer.

In authorized implementation task, make value-sensitive consumer fail against old RHS fallback first, then pass with symbol references. Check names, values, group boundaries together. Verify corrupting one expected value fails assertion process. Mixed clauses need consumer compile and runtime assertion on specified compiler; source inspection or ordinary-method test is insufficient.

## Examples

**Good.** For `capture("left")(7)`, curried `capture(a: String)(b: Int)` records `Seq(Seq("a" -> "left"), Seq("b" -> 7))`; second invocation records changed values. Original test design extending PR 126's nested-pair oracle, not recorded execution. Symbol-based fix plus full equality addresses value capture without claiming generic-extension coverage.

**Broken and correction.** Macro uses `optV.fold('None)(_.asExpr)` from `ValDef`; Scala 3 test checks names only. Correct names hide substituted `None` values. Correction: follow PR 126's parameter-symbol reference; compare full nested pairs on Scala 3 and Scala 2. Keep separate open finding for unchecked term/type casts; replacing cast with erased generic-list pattern matching is not a correction.

**Negative.** Parameterless `baz` records `Seq()` and passes full equality. Do not manufacture missing-value defect where no argument exists.

## Output additions

Use `file:line | severity | violated invariant | evidence | correction | test`. Distinguish reproduced wrong value, unexecuted compiler counterexample, test-coverage gap. Include actual command/result or explicit `not executed`, plus unchecked matrix cells.

## Limitations

Historical, source-backed review procedure, not proof of currently available patch. Mixed-clause repair not compiled. By-name, repeated, erased, inline, and other advanced parameter forms need own specified semantics and consumers; ordinary Args tests do not establish them. These records support no benchmark, cancellation, security-sandbox, or broad compatibility claim.

## Sources

- [PR 103 erasure explanation](https://github.com/com-lihaoyi/sourcecode/pull/103#discussion_r577495682) and [reviewer counterexample](https://github.com/com-lihaoyi/sourcecode/pull/103#discussion_r577846016).
- [PR 126 parameter-symbol repair](https://github.com/com-lihaoyi/sourcecode/blob/502d980afce26eff20def43ec345a4e712e95926/sourcecode/src-3/sourcecode/Macros.scala#L184-L217) and [full-payload assertion](https://github.com/com-lihaoyi/sourcecode/blob/502d980afce26eff20def43ec345a4e712e95926/sourcecode/test/src/sourcecode/ArgsTests.scala#L6-L61).
- [PR 154 main-runner explanation](https://github.com/com-lihaoyi/sourcecode/pull/154#discussion_r1564716506).
