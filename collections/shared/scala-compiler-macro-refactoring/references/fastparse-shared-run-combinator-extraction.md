# Fastparse (com-lihaoyi/fastparse): shared-run combinator extraction

Originally `scala-fastparse-shared-run-combinator-extraction`. Evidence: [evidence/scala-fastparse-shared-run-combinator-extraction.json](evidence/scala-fastparse-shared-run-combinator-extraction.json) (claims `fp-claim-evaluation-order`, `fp-claim-cut-regression`, `fp-claim-staging-boundaries`, `fp-claim-function-typed-implicit`, `fp-claim-compiler-migration-scope`; source observations separated from inference).

Treat parser expression as operation on current run, not immutable parser AST. Keep Fastparse's synchronous, allocation-conscious implementation. Do not introduce effect runtime or mechanically replace its mutable fields with immutable application-state patterns.

## Scope

Use for: extracted parser wrapper changing evaluation order; sequence/repetition consolidation; cut moved into reusable whitespace or comment parsing; change to implicit/given hook every combinator calls on shared run (for example `Whitespace`); Scala 2 -> Scala 3 port of these combinators, asking whether shared-run behaviour survived compiler change. Review both generated operation and enclosing grammar. For a port, `fp-claim-compiler-migration-scope` bounds work: compile engine and keep all consumer suites passing, without teaching ScalaParse new Scala 3 syntax.

Not for: ordinary immutable `Parsed` values, general Scala collection refactor, generic ABI cleanup, compiler syntax-only rename. Do not apply Fastparse 2/3 shared-run model to Fastparse 1 without inspecting that implementation. Custom failure label with unchanged parsing control flow, or allocation/closure/callsite-bytecode cost question with unchanged semantics, belongs to `scala-runtime-diagnostics-hot-paths`.

## Prerequisites

Identify Fastparse revision, Scala compiler version, source roots, target platforms from actual build. Before editing, read public `P` alias, changed combinator, `ParsingRun`, input implementation, consumer tests.

Historical boundaries: 2020 build uses Scala 2.12.10/2.13.1 for JVM (`fp-build-2020`); 2022 repetition implementation lives under `src-2` (`fp-repetition-2022`). 2024 build uses Scala 3.3.3/2.13.14/2.12.19, Scala.js 1.16.0, Native 0.5.1 (`fp-build-2024`). Scala 3 has inline/by-name entrypoints and quoted macros; do not infer their staging from a Scala 2 signature. Evidence-era pins, not advice to downgrade current project.

## Workflow

1. **Classify boundary.** Distinguish ordinary method parameter, by-name parser, inline receiver, quoted expression, completed `Parsed` result. Trace call sites through relevant compiler-specific package API. A `val` holding a `ParsingRun` is not a snapshot of that run's mutable fields.
2. **Write execution ledger.** Per child, list when it executes and which fields it reads/writes: `index`, `isSuccess`, `successValue`, `cut`, diagnostic aggregates, `noDropBuffer`. Historical sequence macro saves left value, index and messages before whitespace/right-child execution. Preserve those dependencies, not merely local-variable names. Map historical field names to target revision; they changed across eras.
3. **Extract with same staging.** Defer child expressions to original position. Save earlier results into locals before another child overwrites shared run; do not read earlier child through aliased run afterwards. Preserve failure short-circuiting. Ordinary wrappers: by-name is the demonstrated mechanism. Macros: inspect expansion/staging instead of adding `=>` blindly.
4. **Trace commitment through caller.** For whitespace/comment cut, inspect surrounding `.rep`, optional parser, alternative, closing delimiter. Ask which branch must still backtrack when whitespace succeeds but following item fails. Keep input needed by capture/lookahead/backtracking available; preserve scoped `noDropBuffer` restoration and existing buffer-drop guards.
5. **Keep specialization observable.** Enumerate `.rep`/`.repX` overloads, literal versus runtime bounds, separator presence, whitespace implementation. Scala 2 historically split common macros from general runtime methods; later Scala 3 shares one macro inspecting inline values. Source consolidation is allowed but must not accidentally replace specialized generated paths with repeated runtime branching.
6. **Check implicit hooks for accidental conversions.** Hook whose implicit value is function-typed, such as pre-3.0 whitespace `P[_] => P[Unit]`, can also be applied by Scala 2 as implicit conversion. In PR 272 this silently rewrote `def fail2[T: P]: P[Unit] = Fail.!` into whitespace call. Whitespace ignores failures, so `Fail` result was overwritten on shared run. When value type and expected type differ only by what such function maps between, ask whether a view was inserted. If execution is authorized, compile with target's implicit-conversion diagnostics. Repair: dedicated trait or SAM type, not function type, plus minimal regression ascribing conversion-triggering type and asserting `Parsed.Failure`. PR 272's trait change was binary incompatible and timed for 3.0.0, so route that ABI decision to `scala-library-compatibility-laws` / `scala-library-contracts`.
7. **Make reproduction discriminating.** Keep prior success tests; add separate issue-named minimal case. Assert semantic value and consumed index, not only `isSuccess`. For whole-input grammar also assert `End` or full consumption. Keep throughput and generated-code-size measurements separate from correctness.

Field/staging procedure is inference from source and documented examples. Lolgab's separate minimal-regression request in PR 256 is explicit review guidance. Open proposal to detect eager parser parameters (#204) does not prove a compiler check exists; LPTK describes that code as written in 2018 and never reviewed (`fp-parameter-check-context-204`). #323's Scala-version-dependent delegation discussion is context, not adopted API: its author reports it "works" in the Scala 3 macro but fails in Scala 2 (`fp-delegation-response-323`). That motivates separate compiler probes, not a reproduced result. PR 310's added `actions: List[CodeAction]` parameter in compiler-internal test adapter (`fp-nsc-adapter-310`) shows compiler-internal test hooks need version-specific roots, unlike shared grammar semantics.

## Invariants

Each child executes at intended position and count. Saved child values survive sibling execution. Success/failure and final index agree. No implicitly inserted call overwrites a child's failure. Cuts commit only intended branches. Diagnostics keep intended child provenance. Capture/backtracking never access discarded input.

Short successful string does not exercise separator failure, cut propagation or chunk boundaries. Re-probe compiler-specific call syntax before imposing `.rep()` rewrites; PR 271 records reverting unnecessary parentheses (`fp-overloads-271`, `fp-hygiene-271`).

## False positives

Macro surface parameter can be staged without resembling ordinary by-name method. Storing immutable results is safe. Explicit, non-implicit function parameter cannot be inserted as view, so it is not a PR 272-style finding. Removing all cuts or retaining all input indefinitely is not bounded repair. Scala 3 quote hygiene does not authorize removing Scala 2 name qualification. Shared source is not inherently slower. Method that merely takes an already-produced `Parsed.Success` and formats its value neither executes a parser nor shares a mutable run; do not make it by-name or rewrite it into a macro. Deliberate commit after unique grammar prefix is not defective solely because backtracking is disabled.

## Probe matrix

Proposed current-change checks inferred from cited historical mechanisms, not claims that all historical tests existed or passed. Instantiate each row with target compiler's actual syntax and supported overloads. Keep old result unless requested change explicitly corrects it.

| Changed boundary | Discriminating input/check | Invariant |
|---|---|---|
| Ordinary higher-order wrapper | Run child bracketed by `Index`; inspect both child values in a sequence | Child executes between its own indices, not before wrapper |
| Shared-run sequence | Differently typed or distinguishable left/right results, and failing left child | Left value saved before right mutation; right does not run after left failure |
| Repetition bounds | Zero, one, lower-bound shortfall, upper-bound completion, `exactly`; compare literal and runtime bounds where legal | Same count, result and final index across specialized/general paths |
| Separator | Absent separator, successful separator, missing next element, failed separator; distinguish cut versus uncut separator | Failed speculative progress rolls back only when allowed; no silent trailing-separator acceptance |
| Whitespace | NoWhitespace versus actual whitespace parser; whitespace before failing or zero-width right child | Whitespace progress does not substitute for right-child progress |
| Comment cut | Comment after last CSS declaration before `}`, plus existing declaration fixtures | Enclosing repetition can stop and enclosing whitespace can consume comment |
| Buffered input | Same finite input as string and as several iterator chunks; include capture/lookahead and committed prefix | Same value/index; no access before dropped-buffer boundary |
| Failure messages | Distinct child labels under verbose mode and supported string replay | Saved diagnostic fields still describe correct child/branch |

Do not repeatedly parse an empty-success child without a bound merely to test progress. First inspect target repetition contract; guard any liveness probe with test runner's timeout. Do not impose new progress/error policy as a refactoring.

For CSS historical fixture, `CssParser.scala:188-206` ties declaration repetition to enclosing whitespace; `CssTests.scala:195-216` checks both declarations and index 80. For wrapper, `ExampleTests.scala:515-522` checks nested values/offsets but not full consumption. Different oracles; neither alone proves all repetition branches.

If specialization changes, measure code size and runtime separately. 2022 Scala 2 source explicitly limits macro expansion to avoid code bloat. 2024 Scala 3 general macro inspects static values and keeps conditional code generation. Stale copied header or author-reported percentage is not a benchmark result for your change.

Reopen `fp-state-2020`, `fp-sequence-2020`, `fp-css-source-256`, `fp-css-test-256`, `fp-repetition-2022`, `fp-repetition-2024`, and `fp-repetition-api-2024` before choosing repair.

## Validation

First read target checkout's `build.sc` or `build.mill`, pinned launcher/version, CI. Sampled `build.sbt` renders documentation; do not use `sbt test` as library gate. Do not execute fetched launcher or build in read-only research session.

In separately authorized, trusted checkout with matching toolchain, 2024 CI provides concrete JVM gate `./mill -i --disable-ticker __.jvm.__.publishArtifacts + __.jvm.__.compile + __.jvm.__.test`. Its build declares core and CssParse JVM test modules, permitting focused selectors such as `./mill -i --disable-ticker 'fastparse.jvm[3.3.3].test'` and `./mill -i --disable-ticker 'cssparse.jvm[3.3.3].test'` for that revision. Rediscover selectors for other versions; confirm named regression ran. When editing shared/macro code, also use corresponding declared Scala 2 cells.

After core checks, run affected ScalaParse/PythonParse/CssParse consumers. If JS or Native code paths change, inspect and run their separate CI jobs with suitable platform tools; JVM success is not platform coverage. For performance work, locate revision's `perftests` modules and compare before/after with same inputs/toolchain, without inventing pass threshold. None of these upstream commands ran during research.

## Examples

**Good.** PR 212's Scala 2 wrapper uses `def Indexed[_: P, T](p: => P[T]): P[(Int, T, Int)] = P(Index ~ p ~ Index)`. Its `1+2` example checks nested result `(0, "1", 1, (2, "2", 3))`: leading indices belong to input before each child runs. Keep that value/offset oracle when extracting wrapper. Add final-index assertion for new whole-input acceptance test; historical test discarded that outer index.

**Broken and correction.** Changing that ordinary wrapper to accept `p: P[T]`, or caching its argument before entering wrapper, runs parser too early. Correction: restore deferred evaluation and keep leading `Index` before child execution; recheck nested values as well as offsets. Do not promise a specific exception on every compiler.

Second composition trap, PR 256: cuts inside `comment` commit failed declaration repetition when trailing comment precedes `}`. Bounded correction removes those cuts from this reusable comment path, not from whole library. New issue-255 fixture keeps both declarations and asserts index 80 for its exact multiline input; reformatted input needs its own index oracle.

## Output additions

Per finding: changed evaluation/control-flow edge, minimal input, expected value/index/commit behavior. If no defect found, name which aliasing/cut/specialization paths were checked and which remain untested.

## Limitations

Evidence is sampled historical implementation and review, not current API guarantee or parser-performance benchmark. Do not infer a maintainer's permanent style preference from a merge.

## Sources

- [Deferred wrapper and value/offset test, PR 212 head](https://github.com/com-lihaoyi/fastparse/blob/75853db8a510bc56019d7bcb74dd87e28a58457d/fastparse/test/src/fastparse/ExampleTests.scala#L515-L522).
- [Shared-run field ownership](https://github.com/com-lihaoyi/fastparse/blob/dd74612224846d3743e19419b3f1191554b973f5/fastparse/src/fastparse/ParsingRun.scala#L19-L28).
- [Lolgab's regression request](https://github.com/com-lihaoyi/fastparse/pull/256#issuecomment-913136906) and [composed CSS regression](https://github.com/com-lihaoyi/fastparse/blob/1b38279037a66df6ef8da4f83027721ff77908b4/cssparse/test/src/cssparse/CssTests.scala#L195-L216).
- [PR 272 root cause](https://github.com/com-lihaoyi/fastparse/commit/22051f098d4cf3f2cb7510ba214cbf2e9b478108), [`Whitespace` trait](https://github.com/com-lihaoyi/fastparse/blob/22051f098d4cf3f2cb7510ba214cbf2e9b478108/fastparse/src/fastparse/Whitespace.scala#L9-L11), [`fail` regression](https://github.com/com-lihaoyi/fastparse/blob/22051f098d4cf3f2cb7510ba214cbf2e9b478108/fastparse/test/src/fastparse/ParsingTests.scala#L106-L114) and [major-version timing](https://github.com/com-lihaoyi/fastparse/pull/272#issuecomment-1451784405).
- [Port acceptance boundary](https://github.com/com-lihaoyi/fastparse/pull/262#issuecomment-1258747216) and [grammar-scope limit](https://github.com/com-lihaoyi/fastparse/pull/262#issuecomment-1261557029).
- [Scala 3 inline specialization](https://github.com/com-lihaoyi/fastparse/blob/d1003d4ed1bee2e2cbdc5b68f3229910165c6b0f/fastparse/src-3/fastparse/internal/MacroRepImpls.scala#L38-L49) and [actual historical CI](https://github.com/com-lihaoyi/fastparse/blob/d1003d4ed1bee2e2cbdc5b68f3229910165c6b0f/.github/workflows/actions.yml#L14-L68).
