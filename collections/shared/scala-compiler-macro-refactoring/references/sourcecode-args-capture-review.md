# sourcecode (com-lihaoyi/sourcecode): `Args` macro capture

Originally `scala-sourcecode-args-capture-review`. Evidence: [evidence/scala-sourcecode-args-capture-review.json](evidence/scala-sourcecode-args-capture-review.json) (claims `c-args-versioned-boundary`, `c-args-runtime-values`, `c-parameter-clause-boundary`, `c-assertion-runner`; source observations are marked as inference; discussion attribution is date-bounded).

Review the path from compiler parameter definitions to the nested runtime `Text` payload, not merely whether the macro compiles. The key historical failure combined a wrong value source with an assertion that deliberately ignored values on Scala 3.

## Scope

Use for `sourcecode.Args` materialization bugs, changes to `argsImpl`, compiler upgrades touching parameter clauses, or refactors of enclosing-method/constructor selection; also when tests claim a value-capture repair but still compare only parameter names.

Not for: ordinary `Name`, `Line`, `File`, or `Text` use, names-only reflection utilities, generic ABI reviews, or a build-only platform upgrade unrelated to Args. An application logging values already supplied explicitly does not require macro surgery. Preserve this library's plain-value contract; do not introduce an effect runtime or a new lazy wrapper.

## Prerequisites

Identify the target commit, Scala compiler versions, platform versions, build pin, and public Args shape before suggesting a patch. Read shared `SourceContext.scala`, the selected `src-2`/`src-3` implementation, `ArgsTests.scala`, and its invocation from `Main`/`Tests`.

Historical anchors are not current-version guarantees:

- PR 103 discusses Scala 3.0.0-RC1 parameter clauses and erasure in 2021.
- PR 126's 2023 repair build declares Scala 3.1.3, alongside Scala 2.11.12/2.12.16/2.13.8, JS 1.10.1 and Native 0.4.5 (`e-build-2023`).
- The November 2024 snapshot declares Scala 2.12.16/2.13.8/3.3.3, JS 1.17.0, Native 0.5.0 and Mill 0.12.0 (`e-build-2024`, `e-platforms-2024`, `e-mill-pin-2024`).

Calendar year alone does not select a compiler API. There is no effect-library version to migrate in this path. For another compiler version, inspect its actual reflection representation rather than transplanting a modern helper into an old release. Shared runtime wrappers are distinct from compile-time reflection code; default-public implementation helpers are not automatically private API.

## Workflow

1. **State the payload invariant.** `Args.value` preserves ordered argument lists, each containing the parameter name and its supplied value. Do not flatten the outer sequence or substitute declaration syntax for runtime values. Distinguish a parameterless method from a method with an empty term clause; the historical test covers the former, not every empty-clause representation.
2. **Trace ownership.** Follow the implicit/inline entrypoint into `argsImpl`. Inspect both the method and constructor branches and the walk out of nested local blocks. Scala 2 uses method symbols/`paramLists`; Scala 3 inspects definition trees. A common helper must preserve those distinct representations rather than assert their equivalence.
3. **Identify the value source.** A parameter's optional `ValDef` RHS is not the argument passed by its caller. PR 126 replaces the RHS/`None` fallback with `Ref(vd.symbol).asExpr` in generated `Text`. Preserve symbol ownership and names; do not rebuild an initializer or re-evaluate a call-site expression. Verify the equivalent operation exists in the target compiler.
4. **Classify clauses before reading values.** Challenge every `List[ValDef]` cast in method and constructor paths. In the RC1 discussion, a reviewer identified extension blocks and methods both having type parameters. Matching erased `List[ValDef]` versus `List[TypeDef]` does not solve this. Use the target version's real clause discriminator, or inspected individual tree kinds when that representation requires it. Preserve empty term clauses and ordered term groups; exclude type clauses from runtime values. If the representation or supported semantics is unresolved, stop with a regression request rather than claim a complete fix.
5. **Strengthen the oracle with the repair.** Compare complete nested `(name, value)` pairs using nontrivial arguments, including two calls with different supplied values. Keep curried methods, nested blocks, primary/secondary constructors, and explicit/implicit argument cases. Remove a names-only Scala 3 exemption only together with the value fix. Add a version-specific generic-extension consumer when claiming support for mixed clauses.
6. **Separate conclusions.** Report value capture, clause classification, and assertion execution independently. PR 126 repairs the first and strengthens tests; it does not demonstrate the second. The unchecked cast remains visible in late-2024 source. Neither merge nor approval establishes all Scala 3 method shapes work.

## Invariants

Nearest intended callable, parameter names, supplied values, outer-list grouping, and term-parameter order. Keep the shared public representation stable while repairing compiler-specific internals. Inspect sibling constructor and method paths for the same assumption; avoid unrelated metadata-macro rewrites.

## False positives

An empty result for the tested parameterless method is legitimate; a name-only API need not capture values; an empty `testFramework` does not by itself disable sourcecode's main-driven assertions. A suspicious cast is grounds for a targeted counterexample, not proof of an observed crash on every compiler release. Do not demand an IO wrapper, framework migration, or public Args flattening as a repair. A change solely to `sourcecode.Name` owner-name formatting does not need Args value fixtures unless it also changes shared ownership behavior used by Args.

## Evidence chain

| Record | Observation | What it does not establish |
|---|---|---|
| `e-api-2020` | Shared `Args` stores nested sequences of strict `Text` values. | A by-name macro entrypoint does not make the stored field lazy. |
| `e-args-broken-2022`, `e-args-oracle-2022` | Scala 3 reads optional initializer trees, substitutes `None`, and tests names only. | A successful test process would not validate values. |
| `e-args-fixed-2023`, `e-args-oracle-2023` | PR 126 references the parameter symbol and restores full equality. | Approval supplies no additional design reasoning; the mixed-clause case is unresolved. |
| `e103-erasure`, `e103-counterexample`, `e-casts-2024` | RC1 discussion names erased clause distinctions and a generic extension case; casts persist in a later snapshot. | Do not assert the same exact runtime error across all compiler representations, or claim a verified classifier patch. |
| `e-args-scala2-owner`, `e-args-scala2-emission` | Scala 2 chooses method/constructor symbols and emits nested values. | Do not copy Scala 3 tree operations into this branch. |
| `e154-runner`, `e-main-2024`, `e-tests-dispatch-2024`, `e-ci-2024` | Main-driven assertions are wired into `test.run`. | Wiring is not recorded execution. |

## Consumer regression specification

Keep the parameter reference in the enclosing callable's scope. Invoke a debug/capture helper whose implicit `Args` materializes at the call site; materializing it inside a separately extracted helper can change the owner being inspected.

The 2023 `ArgsTests` source supplies these cases:

- A curried method has two ordered term groups.
- A local value block still captures the surrounding method arguments.
- A primary constructor captures both of its groups; a secondary constructor's later capture records that constructor's own parameters.
- A parameterless method records an empty outer sequence.
- An implicit parameter records the actual explicit or implicitly supplied value, not merely its name.

Extend that corpus with original probes, labelled unexecuted until run:

1. Invoke the same method with different values to distinguish runtime references from cached/default values. Do not use only literal `None` arguments: they would mask the historical fallback bug.
2. Compare `def f` and `def f()` under the chosen compiler. Establish whether its representation preserves an empty term clause; do not erase it as a side effect of filtering type clauses.
3. Define an extension block with a type parameter and an extension method with another type parameter. Materialize Args inside the method. Inspect that compiler's clause shape, identify expected receiver/term groups, and assert names/values only for actual term parameters. Decide the intended receiver exposure explicitly; the historical review supplies a counterexample, not a full expected payload.
4. Repeat the classifier check in constructor extraction. Fixing only the method branch leaves the sibling cast assumption intact.

The correction must distinguish type clauses without erased generic-list tests. On compiler releases with a dedicated term-clause API, verify its signature and empty-clause behavior before using it. On an older list-of-trees representation, inspect tree kinds and homogeneous-clause invariants; do not infer a kind from a nonexistent first element or silently flatten/filter away meaningful structure.

## Review attribution

Alexarchambault explains the erasure concern as PR 103's author. His historical commit/merge access is independently established by Li Haoyi's access grant in PR 56; that does not make this an independent design review. Smarter supplies the extension-method counterexample; historical repository-maintainer status is unverified. Li Haoyi explains his own submitted main-runner design in PR 154. PR 126's value-source repair is a source-derived lesson, not an inferred reviewer preference. Do not attribute source-derived repairs to a reviewer who only approved the PR.

## Validation

Discover commands from the target checkout's build file, launcher pin and CI, then trace the main to `ArgsTests`. At the November 2024 SHA, CI includes `__.test.run`; the test-only invocation derived from that configuration is `./mill -i '__.test.run'`. It enters `sourcecode.Main`, then `Tests.run`, then `ArgsTests`. Do not replace it with `sbt test`, a guessed uTest selector, or a compile-only task; a conventional framework selector can miss that chain.

Only run that command in a separately authorized, trusted checkout with the matching Mill/JDK and JS/Native prerequisites. This historical research did not execute upstream builds. Rediscover selectors if the checkout differs; report missing platform toolchains rather than implying the aggregate ran. Do not run publication/setup scripts as substitutes for tests. Publication success and binary-compatibility checks cannot replace a value-sensitive consumer.

In an authorized implementation task, first make the value-sensitive consumer fail against the old RHS fallback, then pass with symbol references. Check names, values and group boundaries together. Verify that deliberately corrupting one expected value makes the assertion process fail. For mixed clauses, require a consumer compile and runtime assertion on the specified compiler; source inspection or the ordinary-method test is insufficient.

## Examples

**Good.** A curried `capture(a: String)(b: Int)` records `Seq(Seq("a" -> "left"), Seq("b" -> 7))` for `capture("left")(7)`, then the corresponding changed values on a second invocation. This is an original test design extending PR 126's existing nested-pair oracle, not a recorded execution. A symbol-based fix plus full equality addresses value capture without claiming generic-extension coverage.

**Broken and correction.** The macro uses `optV.fold('None)(_.asExpr)` from `ValDef`, and the Scala 3 test checks names only. Correct names conceal substituted `None` values. Correction: follow PR 126's parameter-symbol reference and compare full nested pairs on Scala 3 as well as Scala 2. Retain a separate open finding for unchecked term/type casts; replacing the cast with erased generic-list pattern matching is not a correction.

**Negative.** The parameterless `baz` case records `Seq()` and passes full equality. Do not manufacture a missing-value defect because no argument exists.

## Output additions

Use `file:line | severity | violated invariant | evidence | correction | test`. Distinguish a reproduced wrong value, an unexecuted compiler counterexample, and a test-coverage gap. Include the actual command/result or explicitly `not executed`, plus unchecked matrix cells.

## Limitations

This is a historical, source-backed review procedure, not proof of a currently available patch. The mixed-clause repair has not been compiled. By-name, repeated, erased, inline, and other advanced parameter forms need their own specified semantics and consumers; the ordinary Args tests do not establish them. No benchmark, cancellation, security-sandbox, or broad compatibility claim follows from these records.

## Sources

- [PR 103 erasure explanation](https://github.com/com-lihaoyi/sourcecode/pull/103#discussion_r577495682) and [reviewer counterexample](https://github.com/com-lihaoyi/sourcecode/pull/103#discussion_r577846016).
- [PR 126 parameter-symbol repair](https://github.com/com-lihaoyi/sourcecode/blob/502d980afce26eff20def43ec345a4e712e95926/sourcecode/src-3/sourcecode/Macros.scala#L184-L217) and [full-payload assertion](https://github.com/com-lihaoyi/sourcecode/blob/502d980afce26eff20def43ec345a4e712e95926/sourcecode/test/src/sourcecode/ArgsTests.scala#L6-L61).
- [PR 154 main-runner explanation](https://github.com/com-lihaoyi/sourcecode/pull/154#discussion_r1564716506).
