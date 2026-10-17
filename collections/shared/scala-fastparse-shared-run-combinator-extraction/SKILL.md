---
name: scala-fastparse-shared-run-combinator-extraction
description: Use when refactoring Fastparse higher-order parsers, sequence or repetition macros, or reusable whitespace cuts. Preserve deferred execution, shared ParsingRun fields, backtracking and specialization.
license: MIT
---

# Refactor Fastparse combinators without changing the parse

Treat a parser expression as an operation on the current run, not as an immutable parser AST. Preserve Fastparse's synchronous, allocation-conscious implementation. Do not introduce an effect runtime or mechanically replace its mutable fields with immutable application-state patterns.

## When to Use

Use for an extracted parser wrapper that changes evaluation order, a sequence/repetition consolidation, a cut moved into reusable whitespace or comment parsing, a change to an implicit/given hook that every combinator calls on the shared run (for example `Whitespace`), or a Scala 2 → Scala 3 port of these combinators where the question is whether the shared-run behaviour survived the compiler change. Review both the generated operation and its enclosing grammar. Claims `fp-claim-evaluation-order`, `fp-claim-cut-regression`, `fp-claim-staging-boundaries`, `fp-claim-function-typed-implicit` and `fp-claim-compiler-migration-scope` in the [evidence reference](references/evidence.json) define this scope. For a port, the migration claim bounds the work: compile the engine and keep all consumer suites passing, without teaching ScalaParse new Scala 3 syntax.

## When Not to Use

Do not use for ordinary immutable `Parsed` values, a general Scala collection refactor, generic ABI cleanup, or a compiler syntax-only rename. Do not apply the Fastparse 2/3 shared-run model to Fastparse 1 without inspecting that implementation. For a custom failure label with unchanged parsing control flow, use the separate diagnostic-mode workflow instead. If semantics are unchanged and the question is allocation, closure or callsite-bytecode cost, use `scala-fastparse-hot-path-cost-review`.

## Prerequisites

Identify the Fastparse revision, Scala compiler version, source roots and target platforms from the actual build. Read the public `P` alias, changed combinator, `ParsingRun`, input implementation, and consumer tests before editing.

Historical boundaries: the 2020 build uses Scala 2.12.10/2.13.1 for JVM; the 2022 repetition implementation lives under `src-2`. The 2024 build uses Scala 3.3.3/2.13.14/2.12.19, Scala.js 1.16.0 and Native 0.5.1. Scala 3 has inline/by-name entrypoints and quoted macros; do not infer their staging from a Scala 2 signature. These are evidence-era pins, not recommendations to downgrade a current project. No Cats Effect, ZIO or Ox conversion is supported by these sources.

## Workflow

1. **Classify the boundary.** Distinguish an ordinary method parameter, a by-name parser, an inline receiver, a quoted expression, and a completed `Parsed` result. Trace call sites through the relevant compiler-specific package API. A `val` containing a `ParsingRun` is not a snapshot of that run's mutable fields.
2. **Write an execution ledger.** For each child, list when it executes and which fields it reads/writes: `index`, `isSuccess`, `successValue`, `cut`, diagnostic aggregates and `noDropBuffer`. The historical sequence macro saves the left value, index and messages before whitespace/right-child execution. Preserve those dependencies rather than merely retaining local-variable names. Map historical field names to the target revision; they changed across eras.
3. **Extract with the same staging.** Defer child expressions until their original position. Save earlier results into locals before another child overwrites the shared run; do not read the earlier child through an aliased run afterwards. Preserve failure short-circuiting. For ordinary wrappers, by-name is the demonstrated mechanism; for macros, inspect expansion/staging instead of adding `=>` blindly.
4. **Trace commitment through the caller.** For a whitespace/comment cut, inspect the surrounding `.rep`, optional parser, alternative and closing delimiter. Ask which branch must still backtrack after whitespace succeeds but the following item fails. Keep input needed by capture/lookahead/backtracking available; preserve scoped `noDropBuffer` restoration and existing buffer-drop guards.
5. **Keep specialization observable.** Enumerate `.rep`/`.repX` overloads, literal versus runtime bounds, separator presence, and whitespace implementation. Scala 2 historically split common macros from general runtime methods; later Scala 3 shares a macro while inspecting inline values. Source consolidation is allowed, but it must not accidentally replace specialized generated paths with repeated runtime branching.
6. **Check implicit hooks for accidental conversions.** A hook whose implicit value is function-typed, such as the pre-3.0 whitespace `P[_] => P[Unit]`, can also be applied by Scala 2 as an implicit conversion. In PR 272 this silently rewrote `def fail2[T: P]: P[Unit] = Fail.!` into a whitespace call. Whitespace ignores failures, so the `Fail` result was overwritten on the shared run. When a value type and an expected type differ only by what such a function maps between, ask whether a view was inserted. Compile with the target's implicit-conversion diagnostics if execution is authorized. The repair is a dedicated trait or SAM type, not a function type, plus a minimal regression that ascribes the conversion-triggering type and asserts `Parsed.Failure`. The trait change in PR 272 was binary incompatible and was timed for 3.0.0, so route that ABI decision to library-contract guidance.
7. **Make the reproduction discriminating.** Retain prior success tests and add a separate, issue-named minimal case. Assert the semantic value and consumed index, not just `isSuccess`. For a whole-input grammar also assert `End` or full consumption. Keep throughput and generated-code-size measurements separate from correctness.

The field/staging procedure is an inference from source and documented examples. Lolgab's separate minimal-regression request in PR 256 is explicit review guidance. An open proposal to detect eager parser parameters (#204) is not evidence that a compiler check exists; #323's Scala-version-dependent delegation discussion is contextual, not an adopted API.

## Review and Refactoring Checks

Preserve these invariants: each child executes at the intended position and count; saved child values survive sibling execution; success/failure and final index agree; no implicitly inserted call overwrites a child's failure; cuts commit only intended branches; diagnostics retain their intended child provenance; capture/backtracking never access discarded input.

Use [the probe matrix](references/probes.md) when repetition or whitespace changes. A short successful string does not exercise separator failure, cut propagation or chunk boundaries. Re-probe compiler-specific call syntax before imposing `.rep()` rewrites; PR 271 records reverting unnecessary parentheses.

False positives: a macro surface parameter can be staged without resembling an ordinary by-name method; storing immutable results is safe; an intentional cut after an unambiguous prefix may be necessary. An explicit, non-implicit function parameter cannot be inserted as a view, so it is not a PR 272-style finding. Removing all cuts or retaining all input indefinitely is not a bounded repair. Scala 3 quote hygiene does not authorize removing Scala 2 name qualification, and shared source is not inherently slower.

## Validation

First read the target checkout's `build.sc` or `build.mill`, pinned launcher/version and CI. The sampled `build.sbt` renders documentation; do not use `sbt test` as the library gate. Do not execute a fetched launcher or build in a read-only research session.

In a separately authorized, trusted checkout with the matching toolchain, the 2024 CI provides the concrete JVM gate `./mill -i --disable-ticker __.jvm.__.publishArtifacts + __.jvm.__.compile + __.jvm.__.test`. Its build declares core and CssParse JVM test modules, permitting focused selectors such as `./mill -i --disable-ticker 'fastparse.jvm[3.3.3].test'` and `./mill -i --disable-ticker 'cssparse.jvm[3.3.3].test'` for that revision. Rediscover selectors for other versions; confirm the named regression actually ran. Use the corresponding declared Scala 2 cells as well when editing shared/macro code.

Run affected ScalaParse/PythonParse/CssParse consumers after core checks. If JS or Native code paths change, inspect and run their separate CI jobs with suitable platform tools; JVM success is not platform coverage. For performance work, locate the revision's `perftests` modules and compare before/after with the same inputs/toolchain, without inventing a pass threshold. This skill's authoring run executed none of these upstream commands.

## Examples

### Good

PR 212's Scala 2 wrapper uses `def Indexed[_: P, T](p: => P[T]): P[(Int, T, Int)] = P(Index ~ p ~ Index)`. Its `1+2` example checks the nested result `(0, "1", 1, (2, "2", 3))`: the leading indices belong to the input before each child runs. Preserve that value/offset oracle when extracting the wrapper. Add a final-index assertion for a new whole-input acceptance test; the historical test discarded that outer index.

### Broken and Correction

Changing that ordinary wrapper to accept `p: P[T]`, or caching its argument before entering the wrapper, executes the parser too early. Correction: restore deferred evaluation and keep leading `Index` before child execution; recheck nested values as well as offsets. Do not promise a specific exception on every compiler.

A second composition trap appears in PR 256: cuts inside `comment` commit the failed declaration repetition when a trailing comment precedes `}`. The bounded correction removes those cuts from this reusable comment path, not from the whole library. The new issue-255 fixture preserves both declarations and asserts index 80 for its exact multiline input; a reformatted input needs its own index oracle.

### Negative

A method merely takes an already-produced `Parsed.Success` and formats its value. It neither executes a parser nor shares a mutable run with a later child. Do not make this parameter by-name or rewrite it into a macro. Likewise, a deliberate commit after a unique grammar prefix is not defective solely because backtracking is disabled.

## Output Contract

For each finding return `file:line`, severity, changed evaluation/control-flow edge, violated invariant, evidence ID and source URL, minimal input, expected value/index/commit behavior, bounded correction, and regression test. State the exact compiler/platform cells, commands and test names actually exercised; separate source reasoning, author-reported historical results and your execution. If no defect is found, identify which aliasing/cut/specialization paths were checked and which remain untested.

## Limitations

The evidence is sampled historical implementation and review, not a current API guarantee or a parser-performance benchmark. Do not infer a maintainer's permanent style preference from a merge. The compiler migration's consumer-test requirement is useful supporting scope, not a reason to implement Scala 3 grammar syntax. Public compatibility cleanup belongs to existing library-contract guidance. Independent peer and behavioral evaluation remain necessary.

## Sources

- [Attributed evidence and claims](references/evidence.json), with source observations separated from inference.
- [Deferred wrapper and value/offset test, PR 212 head](https://github.com/com-lihaoyi/fastparse/blob/75853db8a510bc56019d7bcb74dd87e28a58457d/fastparse/test/src/fastparse/ExampleTests.scala#L515-L522).
- [Shared-run field ownership](https://github.com/com-lihaoyi/fastparse/blob/dd74612224846d3743e19419b3f1191554b973f5/fastparse/src/fastparse/ParsingRun.scala#L19-L28).
- [Lolgab's regression request](https://github.com/com-lihaoyi/fastparse/pull/256#issuecomment-913136906) and [composed CSS regression](https://github.com/com-lihaoyi/fastparse/blob/1b38279037a66df6ef8da4f83027721ff77908b4/cssparse/test/src/cssparse/CssTests.scala#L195-L216).
- [PR 272 root cause](https://github.com/com-lihaoyi/fastparse/commit/22051f098d4cf3f2cb7510ba214cbf2e9b478108), [`Whitespace` trait](https://github.com/com-lihaoyi/fastparse/blob/22051f098d4cf3f2cb7510ba214cbf2e9b478108/fastparse/src/fastparse/Whitespace.scala#L9-L11), [`fail` regression](https://github.com/com-lihaoyi/fastparse/blob/22051f098d4cf3f2cb7510ba214cbf2e9b478108/fastparse/test/src/fastparse/ParsingTests.scala#L106-L114) and [major-version timing](https://github.com/com-lihaoyi/fastparse/pull/272#issuecomment-1451784405).
- [Port acceptance boundary](https://github.com/com-lihaoyi/fastparse/pull/262#issuecomment-1258747216) and [grammar-scope limit](https://github.com/com-lihaoyi/fastparse/pull/262#issuecomment-1261557029).
- [Scala 3 inline specialization](https://github.com/com-lihaoyi/fastparse/blob/d1003d4ed1bee2e2cbdc5b68f3229910165c6b0f/fastparse/src-3/fastparse/internal/MacroRepImpls.scala#L38-L49) and [actual historical CI](https://github.com/com-lihaoyi/fastparse/blob/d1003d4ed1bee2e2cbdc5b68f3229910165c6b0f/.github/workflows/actions.yml#L14-L68).
