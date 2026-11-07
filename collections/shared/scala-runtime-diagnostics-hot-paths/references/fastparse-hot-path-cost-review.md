# Fastparse: hot-path allocation, closure and callsite bytecode cost (originally scala-fastparse-hot-path-cost-review)

Library: com-lihaoyi/fastparse. Evidence: [evidence/scala-fastparse-hot-path-cost-review.json](evidence/scala-fastparse-hot-path-cost-review.json) (claims `fp-claim-diagnostic-cost-gating` (diagnostics off), `fp-claim-verbose-trace-cost` (diagnostics on), `fp-claim-callsite-bytecode`, `fp-claim-perf-measurement`).

Fastparse runs every parser through one mutable `ParsingRun`. Scala 2 macros and Scala 3 inline methods paste combinator bodies into user parsers, so small helper cost is paid at every call site, often on every parse step. Reviews those costs, not parse-result correctness.

Two cost regimes; never mix them:

- **Diagnostics off.** Ordinary `parse(...)` with `verboseFailures = false`: throughput hot path. No message objects may be allocated here.
- **Diagnostics on.** Verbose parse, or `trace()`, which reruns parser with `verboseFailures = true`. 2023 source documents it as slowest mode (about 2x). Real cost users pay and project benchmarks, but separate budget.

## Scope

Use when diff touches: `ParsingRun` success/failure/report helpers; `Msgs`/`Lazy` construction; bodies of `.rep`, `~`, literal or whitespace macros; Scala 3 inline port of Scala 2 macro; PR claiming speedup.

Typical triggers: new `String`, by-name, `List(...)` or closure argument on per-step call; runtime "is this a no-op?" check or default argument emitted into expanded code; allocation rewrites inside verbose-only aggregation (diagnostics-on cost); benchmark numbers offered as justification; compiler-matrix edits bundled into performance PR.

Not for:

- changes to parse values, consumed index, cut or backtracking: review first with shared-run combinator case in `scala-compiler-macro-refactoring`;
- changes to which label or terminal is reported: use [fastparse-diagnostic-mode-review.md](fastparse-diagnostic-mode-review.md); this case covers only what that work costs;
- ordinary user grammars, and `Parsed` post-processing that runs once per finished parse;
- generic JVM tuning (use `performance-engineering` or `mill-performance`);
- pushing effect systems, immutable state or blanket `List` bans onto unrelated code.

## Prerequisites and version fence

Detect from target `build.sc`/`build.mill`, not from memory: Fastparse major version; Scala cells; whether changed file is under `src-2` (quasiquote macros) or `src-3` (inline/quoted).

| Era | Diagnostic flag and messages | Toolchain |
| --- | --- | --- |
| 2018 (Fastparse 2 development) | `tracingEnabled`; `shortFailureMsg` closures | — |
| 2023 (PR 273 merge `0a3de65`) | `verboseFailures`; `Msgs`/`Lazy` | Scala 3.2.2, 2.13.10, 2.12.17, 2.11.12 |
| 2024 snapshot | `verboseFailures`; `Msgs`/`Lazy` | Scala 3.3.3, 2.13.14, 2.12.19; Mill 0.12.0; `perftests.bench2` / `perftests.benchScala33` |

Map field names on target revision. Inspected core is synchronous; does not use CE, ZIO or Ox.

## Workflow

1. **Classify the regime and the path.** Per changed line: runs with diagnostics off, or only under `if (ctx.verboseFailures)` / during `trace()`? Runs per step (`freshSuccess`/`freshFailure` call sites, rep loops, expanded bodies), or once after parse (formatting `Parsed.Failure` strings)? Apply steps 2 and 3 to matching regime. Post-parse formatting is cold in both regimes.
2. **Diagnostics off: no message work before the flag.** Look for strings, by-name parameters, `() => ...`, `new Lazy`, `Msgs(...)` or `List(...)` evaluated before flag check. In 2018, lihaoyi moved `tracingEnabled` check to call sites "to avoid unnecessary allocation of the by-name argument lambda". In 2024, `freshFailure()` still takes no arguments, resets diagnostic state only under `verboseFailures`. Whitespace comment-failure path calls `freshFailure` with nothing, reports terminal only under flag. Any new eager argument reverses that design.
3. **Diagnostics on: treat it as its own budget.** Allocation in verbose-only aggregation (`aggregateMsg`/`aggregateTerminal`/`setMsg`, `Msgs(new Lazy(...) :: Nil)`) is diagnostics-on cost. PR 273's `List(...)` to `:: Nil` rewrites all sit at such sites. Author said it "Seems like" Scala 2 optimizes this but Scala 3 does not, based on profiler run in early 2023. Judge such change by benchmark failure arm (step 5), not success arm. Do not dismiss it as cold; do not cite it as diagnostics-off evidence. Do not accept or demand mechanical `::` rewrites without profile on actually affected compiler.
4. **Callsite size: Scala 2 and Scala 3 differ.**
   - Prefer expansion-time branches over runtime no-op checks. `NoWhitespace` type test dates to 2018 Scala 2 `~` (`e7d9576`); Scala 3 `.rep` adopted it in PR 273; Scala 2 `.rep` in PR 310 (2024), replacing runtime `ne noWhitespaceImplicit` check plus annotation. No-argument `.rep` was constant-folded in 2018 "to remove all the branches from the hot paths".
   - **Scala 2 macros and non-inline runtime helpers called from expanded code:** prefer telescoping overloads to default arguments. 2020 `ParsingRun` comment cites "bytecode size blowup".
   - **Scala 3 `inline` parameters with defaults** (PR 273's `inline def rep(inline min: Int = 0, inline sep: => P[_] = null, ...)`) are read by `MacroRepImpls` as expansion-time constants through `getInlineExpansionValue`. Intended design, not a finding.
   - Weigh all this against Scala 2 documentation, which deliberately keeps general repetition cases as normal methods to avoid code bloat.
5. **Measurement, proportional to risk.**
   - If change may add per-step work or alters aggregation, run revision's `perftests` pair: Scala 2.13 module plus Scala 3 module reusing its sources. Compare before and after on same toolchain.
   - Report arms separately. Benchmark 0: `parse(data).get` with verbose off. Benchmark 1: failing parse followed by `.extra.traced`, a verbose replay (`perftests/bench2/src/perftests/Utils.scala` lines 88-95).
   - Keep failure-message tests in same change.
   - Benchmark pair is **optional** when expansion-time elimination strictly removes generated code and adds nothing. PR 310's eligible discussion requested or reported no benchmark before merge. For such change, require expansion-equivalence argument and passing tests instead.
6. **Separate compiler-matrix changes.** In PR 273, lefou asked "Do you drop Scala 3.1 support on purpose?"; lihaoyi answered with macro-compilation reason. Ask for that kind of stated reason; judge matrix change on own merits.

Provenance: steps 2 to 5 are inferences from source, author's commit/PR rationale and build structure. Only step 6 rests on direct reviewer question and answer. No reviewer set performance threshold; PR 271 merged with recorded Scala 3 slowdown of about 10%.

## Checks

Invariants to preserve:

- With diagnostics off, per-step code allocates no message objects.
- With diagnostics on, labels and aggregates are unchanged.
- Observable behaviour is unchanged: `.rep`/`.repX` call syntax (re-probe it, as PR 271 did), parse results and indices.
- Generated code does not grow without measured benefit.

Refactor is acceptable only when it reads as "same semantics, fewer allocations or less bytecode" *in a named regime*, with both halves checked.

False positives:

- message building inside existing `if (ctx.verboseFailures)` block, when review question is diagnostics-off cost;
- string formatting of finished `Parsed.Failure`;
- `List(...)` in Scala 2-only code or in cold code;
- Scala 3 `inline` parameters with defaults that macro reads as constants;
- default argument on non-inlined public method kept for API compatibility. Rmgk's port preferred API compatibility over specialized `rep(min)` overload;
- regression claim based on one noisy benchmark iteration. PR 273's own numbers vary.

Not a false positive: allocation added to `trace()` replay or verbose aggregation. Diagnostics-on cost; benchmark failure arm measures it.

## Validation

1. Read target `build.sc`/`build.mill` and CI. Do not use documentation-site `build.sbt` as library gate. Do not run fetched launcher during read-only review.
2. In trusted, separately authorized checkout of 2024 revision, run correctness gate first: `./mill -i --disable-ticker __.jvm.__.compile + __.jvm.__.test`.
3. If workflow step 5 requires it, run benchmark modules before and after change: `./mill -i perftests.bench2.test` (Scala 2.13) and `./mill -i perftests.benchScala33.test` (Scala 3.3.3). At PR 273 revision, Scala 3 module is `perftests.benchScala3`. Rediscover module names for other revisions.
4. Confirm `FailureTests` cases (for example `whitespaceFail`) and affected consumer suites actually ran, not just compiled.
5. Report JVM, Scala cell, benchmark arm used, per-iteration numbers as raw observations. JVM numbers say nothing about JS or Native performance.

Authoring run executed none of these commands.

## Examples

**Good.** At PR 273 merge `0a3de65`, Scala 3 `MacroRepImpls` checks at expansion time whether implicit whitespace is `NoWhitespace`; if so, emits no whitespace branch. Same PR adds `inline` default parameters to `rep`, which macro reads as constants. Outcome: accept specialization; file no default-argument finding.

Same PR's `:: Nil` changes sit in verbose-only aggregation: classify as diagnostics-on improvement. Author's numbers support that. Harness counts completed runs per 10-second window, so higher is better. On Scala 3, Benchmark 1 (traced failure arm) rises from about 1.9k to about 2.8k runs after warm-up; Benchmark 0 (verbose off) moves only from about 7.6k to about 8.1k. PR body also includes one Scala 2.13 reference run. Record all these numbers as author-reported, not reproduced.

**Broken and correction (eager message).** Change adds `ctx.freshFailure(msg = s"expected $name")`, building string on every failure regardless of `verboseFailures`. Undoes gating from commit `e32dd15`; puts diagnostics work on diagnostics-off path. Correction: keep `freshFailure()` argument-free; report label only under flag, as `if (ctx.verboseFailures) ctx.reportTerminalMsg(ctx.index, () => msg)` does at PR 297. Then rerun label tests with diagnostics on; compare Benchmark 0 with failing input and diagnostics off.

**Broken and correction (runtime branch).** Scala 2 macro emits runtime `ws ne NoWhitespace.noWhitespaceImplicit` test into every `.rep` call site. Correction: decide by `ws.tpe =:= typeOf[NoWhitespace.noWhitespaceImplicit.type]` at expansion time, as PR 310 does. Strictly shrinks generated code, so green tests plus equivalence argument suffice; benchmark optional.

**Negative.** PR rewrites `List(a, b)` to `a :: b :: Nil` in string formatting of finished `Parsed.Failure`, or in Scala 2-only `src-2` code, with no profile. That code runs once per finished parse; historical evidence for rewrite concerns Scala 3 verbose aggregation. Do not request or approve it as performance fix. New default argument on non-inlined public `parse` overload does not trigger this case; neither does Scala 3 `inline` default.

## Case output fields

Per finding: `file:line`; severity; regime (diagnostics off or on) and path (per-step or cold); mechanism (closure, by-name, eager string, list, default argument on Scala 2 or runtime helper, runtime branch); evidence ID and original GitHub URL; expected direction of cost change; bounded correction; regression test (label test with diagnostics on) and benchmark arm to compare, or why no benchmark is needed. Keep source reasoning, author-reported numbers and numbers you measured separate. Never present model-based review as measured speedup. For no-change verdict, name gate, regime or cold path making cost acceptable.

## Limitations

- Evidence is mostly author rationale (commit and PR messages) plus source observation. Not a record of maintainer preferences on performance review.
- Claim that benchmarks are optional for strictly shrinking code rests on PR 310 having no benchmark request: absence of evidence, not stated policy.
- No benchmark, JIT, bytecode-size or allocation measurement was reproduced.
- `List` versus `::` claim is tied to 2023 Scala 3 compiler; may not hold on later versions.
- PR 276 read only at patch and source level.
- Independent peer evaluation and authorized execution still open.

## Sources

- [2018 gating commit](https://github.com/com-lihaoyi/fastparse/commit/e32dd15da436bbcb3702256643663270a18b93e8), [2018 NoWhitespace fast path](https://github.com/com-lihaoyi/fastparse/blob/e7d957694a17f899e5a883205ceeaa044da58001/fasterparser/src/fasterparser/Parsing.scala#L82-L90) and [2018 rep constant folding](https://github.com/com-lihaoyi/fastparse/commit/9f6bd5e21bc8246b70aeccc74f1da3ad288c29ec).
- [Telescoping-overload rationale, 2020](https://github.com/com-lihaoyi/fastparse/blob/dd74612224846d3743e19419b3f1191554b973f5/fastparse/src/fastparse/ParsingRun.scala#L251-L256).
- PR 273: [merge](https://github.com/com-lihaoyi/fastparse/commit/0a3de65844a3879c9a093652f8b2dcce550afd24), [Scala 3 inline defaults](https://github.com/com-lihaoyi/fastparse/blob/0a3de65844a3879c9a093652f8b2dcce550afd24/fastparse/src-3/fastparse/package.scala#L176-L180), [benchmark arms](https://github.com/com-lihaoyi/fastparse/blob/0a3de65844a3879c9a093652f8b2dcce550afd24/perftests/bench2/src/perftests/Utils.scala#L88-L95), [trace cost doc](https://github.com/com-lihaoyi/fastparse/blob/0a3de65844a3879c9a093652f8b2dcce550afd24/fastparse/src/fastparse/Parsed.scala#L120-L141), and lefou's [question](https://github.com/com-lihaoyi/fastparse/pull/273#discussion_r1124148640) with its [reply](https://github.com/com-lihaoyi/fastparse/pull/273#discussion_r1124162833).
- PR 310: [Scala 2 expansion-time NoWhitespace](https://github.com/com-lihaoyi/fastparse/blob/7f6dddcefdef433b5961b8d1ec4a3746c1e03fdd/fastparse/src-2/fastparse/internal/MacroRepImpls.scala#L59-L69) and [discussion](https://github.com/com-lihaoyi/fastparse/pull/310).
- [PR 271 recorded slowdown](https://github.com/com-lihaoyi/fastparse/commit/ac05071ac8dd9f101660f4dbe9057ef74af0f1c9), [rmgk's compatibility tradeoff](https://github.com/com-lihaoyi/fastparse/pull/271#issuecomment-1449822638) and [2024 benchmark modules](https://github.com/com-lihaoyi/fastparse/blob/d1003d4ed1bee2e2cbdc5b68f3229910165c6b0f/build.mill#L225-L245).
- [Evidence and claim subset](evidence/scala-fastparse-hot-path-cost-review.json).
