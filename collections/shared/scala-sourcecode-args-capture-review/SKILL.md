---
name: scala-sourcecode-args-capture-review
description: Use when reviewing sourcecode.Args macro changes. Preserve runtime argument values, parameter-clause structure and compiler-specific ownership during Scala migrations and refactoring.
license: MIT
---

# Review sourcecode Args capture

Review the path from compiler parameter definitions to the nested runtime `Text` payload, not merely whether the macro compiles. The key historical failure combined a wrong value source with an assertion that deliberately ignored values on Scala 3.

## When to Use

Use for `sourcecode.Args` materialization bugs, changes to `argsImpl`, compiler upgrades touching parameter clauses, or refactors of enclosing-method/constructor selection. Also use when tests claim a value-capture repair but still compare only parameter names. Claims and their historical boundaries are in [evidence.json](references/evidence.json).

## When Not to Use

Do not trigger for ordinary `Name`, `Line`, `File`, or `Text` use, names-only reflection utilities, generic ABI reviews, or a build-only platform upgrade unrelated to Args. An application logging values already supplied explicitly does not require macro surgery. Preserve this library's plain-value contract; do not introduce an effect runtime or a new lazy wrapper.

## Prerequisites

Identify the target commit, Scala compiler versions, platform versions, build pin, and public Args shape before suggesting a patch. Read shared `SourceContext.scala`, the selected `src-2`/`src-3` implementation, `ArgsTests.scala`, and its invocation from `Main`/`Tests`.

Historical anchors are not current-version guarantees:

- PR 103 discusses Scala 3.0.0-RC1 parameter clauses and erasure in 2021.
- PR 126's 2023 repair build declares Scala 3.1.3, alongside Scala 2.11.12/2.12.16/2.13.8, JS 1.10.1 and Native 0.4.5.
- The November 2024 snapshot declares Scala 2.12.16/2.13.8/3.3.3, JS 1.17.0, Native 0.5.0 and Mill 0.12.0.

There is no effect-library version to migrate in this path. For another compiler version, inspect its actual reflection representation rather than transplanting a modern helper into an old release. See [historical boundaries](references/review-cases.md).

## Workflow

1. **State the payload invariant.** `Args.value` preserves ordered argument lists, each containing the parameter name and its supplied value. Do not flatten the outer sequence or substitute declaration syntax for runtime values. Distinguish a parameterless method from a method with an empty term clause; the historical test covers the former, not every empty-clause representation.
2. **Trace ownership.** Follow the implicit/inline entrypoint into `argsImpl`. Inspect both the method and constructor branches and the walk out of nested local blocks. Scala 2 uses method symbols/`paramLists`; Scala 3 inspects definition trees. A common helper must preserve those distinct representations rather than assert their equivalence.
3. **Identify the value source.** A parameter's optional `ValDef` RHS is not the argument passed by its caller. PR 126 replaces the RHS/`None` fallback with `Ref(vd.symbol).asExpr` in generated `Text`. Preserve symbol ownership and names; do not rebuild an initializer or re-evaluate a call-site expression. Verify the equivalent operation exists in the target compiler.
4. **Classify clauses before reading values.** Challenge every `List[ValDef]` cast in method and constructor paths. In the RC1 discussion, a reviewer identified extension blocks and methods both having type parameters. Matching erased `List[ValDef]` versus `List[TypeDef]` does not solve this. Use the target version's real clause discriminator, or inspected individual tree kinds when that representation requires it. Preserve empty term clauses and ordered term groups; exclude type clauses from runtime values. If the representation or supported semantics is unresolved, stop with a regression request rather than claim a complete fix.
5. **Strengthen the oracle with the repair.** Compare complete nested `(name, value)` pairs using nontrivial arguments, including two calls with different supplied values. Keep curried methods, nested blocks, primary/secondary constructors, and explicit/implicit argument cases. Remove a names-only Scala 3 exemption only together with the value fix. Add a version-specific generic-extension consumer when claiming support for mixed clauses.
6. **Separate conclusions.** Report value capture, clause classification, and assertion execution independently. PR 126 repairs the first and strengthens tests; it does not demonstrate the second. The unchecked cast remains visible in late-2024 source. Neither merge nor approval establishes all Scala 3 method shapes work.

## Review and Refactoring Checks

Preserve these invariants: nearest intended callable, parameter names, supplied values, outer-list grouping, and term-parameter order. Keep the shared public representation stable while repairing compiler-specific internals. Inspect sibling constructor and method paths for the same assumption; avoid unrelated metadata-macro rewrites.

False positives: an empty result for the tested parameterless method is legitimate; a name-only API need not capture values; an empty `testFramework` does not by itself disable sourcecode's main-driven assertions. A suspicious cast is grounds for a targeted counterexample, not proof of an observed crash on every compiler release. Do not demand an IO wrapper, framework migration, or public Args flattening as a repair.

## Validation

Discover commands from the target checkout's build file, launcher pin and CI, then trace the main to `ArgsTests`. At the November 2024 SHA, CI includes `__.test.run`; the test-only invocation derived from that configuration is `./mill -i '__.test.run'`. It enters `sourcecode.Main`, then `Tests.run`, then `ArgsTests`. Do not replace it with `sbt test`, a guessed uTest selector, or a compile-only task.

Only run that command in a separately authorized, trusted checkout with the matching Mill/JDK and JS/Native prerequisites. This historical research did not execute upstream builds. Rediscover selectors if the checkout differs; report missing platform toolchains rather than implying the aggregate ran. Do not run publication/setup scripts as substitutes for tests.

In an authorized implementation task, first make the value-sensitive consumer fail against the old RHS fallback, then pass with symbol references. Check names, values and group boundaries together. Verify that deliberately corrupting one expected value makes the assertion process fail. For mixed clauses, require a consumer compile and runtime assertion on the specified compiler; source inspection or the ordinary-method test is insufficient.

## Examples

### Good

A curried `capture(a: String)(b: Int)` records `Seq(Seq("a" -> "left"), Seq("b" -> 7))` for `capture("left")(7)`, then the corresponding changed values on a second invocation. This is an original test design extending PR 126's existing nested-pair oracle, not a recorded execution. A symbol-based fix plus full equality addresses value capture without claiming generic-extension coverage.

### Broken and Correction

The macro uses `optV.fold('None)(_.asExpr)` from `ValDef`, and the Scala 3 test checks names only. Correct names conceal substituted `None` values. Correction: follow PR 126's parameter-symbol reference and compare full nested pairs on Scala 3 as well as Scala 2. Retain a separate open finding for unchecked term/type casts; replacing the cast with erased generic-list pattern matching is not a correction.

### Negative

The parameterless `baz` case records `Seq()` and passes full equality. Do not manufacture a missing-value defect because no argument exists. Likewise, a change solely to `sourcecode.Name` owner-name formatting falls outside this skill; do not demand Args value fixtures unless it also changes shared ownership behavior used by Args.

## Output Contract

Return each finding as `file:line | severity | violated invariant | evidence | correction | test`. State compiler/platform and exact source revision. Distinguish a reproduced wrong value, an unexecuted compiler counterexample, and a test-coverage gap. Include the actual command/result or explicitly `not executed`, plus unchecked matrix cells. Use historical evidence IDs without attributing source-derived repairs to a reviewer who only approved the PR.

## Limitations

This is a historical, source-backed review procedure, not proof of a currently available patch. The mixed-clause repair has not been compiled here. By-name, repeated, erased, inline, and other advanced parameter forms need their own specified semantics and consumers; the ordinary Args tests do not establish them. No benchmark, cancellation, security-sandbox, or broad compatibility claim follows from these records. Frontmatter/structural validity is not behavioral effectiveness.

## Sources

- [Evidence and claim mapping](references/evidence.json): source observations are marked as inference; discussion attribution is date-bounded.
- [PR 103 erasure explanation](https://github.com/com-lihaoyi/sourcecode/pull/103#discussion_r577495682) and [reviewer counterexample](https://github.com/com-lihaoyi/sourcecode/pull/103#discussion_r577846016).
- [PR 126 parameter-symbol repair](https://github.com/com-lihaoyi/sourcecode/blob/502d980afce26eff20def43ec345a4e712e95926/sourcecode/src-3/sourcecode/Macros.scala#L184-L217) and [full-payload assertion](https://github.com/com-lihaoyi/sourcecode/blob/502d980afce26eff20def43ec345a4e712e95926/sourcecode/test/src/sourcecode/ArgsTests.scala#L6-L61).
- [PR 154 main-runner explanation](https://github.com/com-lihaoyi/sourcecode/pull/154#discussion_r1564716506).
