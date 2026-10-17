---
name: scala-fastparse-hot-path-cost-review
description: Use when reviewing allocation, closure or bytecode-size changes in Fastparse ParsingRun helpers, inline/macro combinators, or diagnostic-message construction. Separates diagnostics-off per-step cost from verbose/trace-replay cost and fences callsite rules by Scala 2 macro versus Scala 3 inline.
license: MIT
---

# Review Fastparse hot-path and diagnostic cost changes

Fastparse runs every parser through one mutable `ParsingRun`. Scala 2 macros and Scala 3 inline methods paste combinator bodies into user parsers, so a small cost in one helper is paid at every call site, and often on every parse step. This skill reviews those costs. It does not review whether the parse result is correct.

Fastparse has two cost regimes, and you must never mix them:

- **Diagnostics off.** This is an ordinary `parse(...)` with `verboseFailures = false`. It is the throughput hot path. No message objects may be allocated here.
- **Diagnostics on.** This is a verbose parse, or `trace()`, which re-runs the parser with `verboseFailures = true`. The 2023 source documents this as the slowest mode (about 2x). It is a real cost that users pay and the project benchmarks, but it is a separate budget.

## When to Use

Use this skill when a diff touches any of the following:

- `ParsingRun` success/failure/report helpers;
- `Msgs`/`Lazy` construction;
- the bodies of the `.rep`, `~`, literal or whitespace macros;
- a Scala 3 inline port of a Scala 2 macro;
- a PR that claims a speedup.

Typical triggers:

- a new `String`, by-name, `List(...)` or closure argument on a call that runs per step;
- a runtime "is this a no-op?" check, or a default argument, emitted into expanded code;
- allocation rewrites inside verbose-only aggregation (diagnostics-on cost);
- benchmark numbers offered as justification;
- compiler-matrix edits bundled into a performance PR.

The claims are `fp-claim-diagnostic-cost-gating` (diagnostics off), `fp-claim-verbose-trace-cost` (diagnostics on), `fp-claim-callsite-bytecode` and `fp-claim-perf-measurement`. They live in the [evidence reference](references/evidence.json).

## When Not to Use

- If the change alters parse values, consumed index, cut or backtracking, use `scala-fastparse-shared-run-combinator-extraction` first.
- If the change alters which label or terminal is reported, use `scala-fastparse-diagnostic-mode-review`. This skill covers only what that work costs.
- Ordinary user grammars, and `Parsed` post-processing that runs once per finished parse, are out of scope.
- Generic JVM tuning is out of scope; use `performance-engineering` or `mill-performance`.
- Do not use this skill to push effect systems, immutable state or blanket `List` bans onto unrelated code.

## Prerequisites

Detect the following from the target `build.sc`/`build.mill`, not from memory:

- the Fastparse major version;
- the Scala cells;
- whether the changed file is under `src-2` (quasiquote macros) or `src-3` (inline/quoted).

Evidence eras:

| Era | Diagnostic flag and messages | Toolchain |
| --- | --- | --- |
| 2018 (Fastparse 2 development) | `tracingEnabled`; `shortFailureMsg` closures | — |
| 2023 (PR 273 merge `0a3de65`) | `verboseFailures`; `Msgs`/`Lazy` | Scala 3.2.2, 2.13.10, 2.12.17, 2.11.12 |
| 2024 snapshot | `verboseFailures`; `Msgs`/`Lazy` | Scala 3.3.3, 2.13.14, 2.12.19; Mill 0.12.0; `perftests.bench2` / `perftests.benchScala33` |

Map field names on the target revision. The inspected core is synchronous and does not use CE, ZIO or Ox.

## Workflow

1. **Classify the regime and the path.** For each changed line, decide two things:
   - Does it run with diagnostics off, or only under `if (ctx.verboseFailures)` / during `trace()`?
   - Does it run per step (`freshSuccess`/`freshFailure` call sites, rep loops, expanded bodies), or once after the parse (formatting `Parsed.Failure` strings)?

   Steps 2 and 3 apply to the matching regime. Formatting after the parse is cold in both regimes.
2. **Diagnostics off: no message work before the flag.** Look for strings, by-name parameters, `() => ...`, `new Lazy`, `Msgs(...)` or `List(...)` that are evaluated before the flag is checked. In 2018, lihaoyi moved the `tracingEnabled` check to the call sites "to avoid unnecessary allocation of the by-name argument lambda". In 2024, `freshFailure()` still takes no arguments and resets diagnostic state only under `verboseFailures`. The whitespace comment-failure path calls `freshFailure` with nothing and reports a terminal only under the flag. Any new eager argument reverses that design.
3. **Diagnostics on: treat it as its own budget.** Allocation inside verbose-only aggregation (`aggregateMsg`/`aggregateTerminal`/`setMsg`, `Msgs(new Lazy(...) :: Nil)`) is diagnostics-on cost. The `List(...)` to `:: Nil` rewrites in PR 273 are all at such sites. The author said this "Seems like" it is optimized on Scala 2 but not on Scala 3, based on a profiler run in early 2023. Judge such a change by the failure arm of the benchmark (see step 5), not the success arm. Do not dismiss it as cold, and do not cite it as diagnostics-off evidence. Do not accept or demand mechanical `::` rewrites without a profile on the compiler that is actually affected.
4. **Callsite size: Scala 2 and Scala 3 differ.**
   - Prefer branches decided at expansion time over runtime no-op checks. The `NoWhitespace` type test goes back to 2018 Scala 2 `~` (`e7d9576`), Scala 3 `.rep` adopted it in PR 273, and Scala 2 `.rep` adopted it in PR 310 (2024), which replaced a runtime `ne noWhitespaceImplicit` check plus an annotation. The no-argument `.rep` was constant-folded in 2018 "to remove all the branches from the hot paths".
   - **Scala 2 macros and non-inline runtime helpers called from expanded code:** prefer telescoping overloads to default arguments. The 2020 `ParsingRun` comment cites "bytecode size blowup".
   - **Scala 3 `inline` parameters with defaults** (PR 273's `inline def rep(inline min: Int = 0, inline sep: => P[_] = null, ...)`) are read by `MacroRepImpls` as expansion-time constants through `getInlineExpansionValue`. They are the intended design, not a finding.
   - Weigh all of this against the Scala 2 documentation, which deliberately keeps general repetition cases as normal methods to avoid code bloat.
5. **Measurement, proportional to risk.**
   - When a change may add per-step work or alters aggregation, run the revision's `perftests` pair: the Scala 2.13 module, and the Scala 3 module that reuses its sources. Compare before and after on the same toolchain.
   - Report the two arms separately. Benchmark 0 is `parse(data).get` with verbose off. Benchmark 1 is a failing parse followed by `.extra.traced`, which is a verbose replay (`perftests/bench2/src/perftests/Utils.scala` lines 88-95).
   - Keep failure-message tests in the same change.
   - A benchmark pair is **optional** when expansion-time elimination strictly removes generated code and adds nothing. No benchmark was requested or reported anywhere in PR 310's eligible discussion before it merged. For such a change, require an expansion-equivalence argument and passing tests instead.
6. **Separate compiler-matrix changes.** In PR 273, lefou asked "Do you drop Scala 3.1 support on purpose?", and lihaoyi answered with a reason about macro compilation. Ask for that kind of stated reason, and judge the matrix change on its own merits.

Steps 2 to 5 are inferences from source, the author's commit/PR rationale and the build structure. Only step 6 rests on a direct reviewer question and answer. No reviewer set a performance threshold, and PR 271 merged with a recorded Scala 3 slowdown of about 10%.

## Review and Refactoring Checks

Invariants to preserve:

- With diagnostics off, per-step code allocates no message objects.
- With diagnostics on, labels and aggregates are unchanged.
- Observable behaviour is unchanged: `.rep`/`.repX` call syntax (re-probe it, as PR 271 did), parse results and indices.
- Generated code does not grow without a measured benefit.

A refactor is acceptable only when it reads as "same semantics, fewer allocations or less bytecode" *in a named regime*, and both halves of that statement are checked.

False positives:

- message building inside an existing `if (ctx.verboseFailures)` block, when the review question is diagnostics-off cost;
- string formatting of a finished `Parsed.Failure`;
- `List(...)` in Scala 2-only code or in cold code;
- Scala 3 `inline` parameters with defaults that the macro reads as constants;
- a default argument on a non-inlined public method kept for API compatibility. Rmgk's port preferred API compatibility over a specialized `rep(min)` overload.
- a regression claim based on one noisy benchmark iteration. PR 273's own numbers vary.

Not a false positive: allocation added to `trace()` replay or to verbose aggregation. That is diagnostics-on cost, and the benchmark's failure arm measures it.

## Validation

1. Read the target `build.sc`/`build.mill` and CI. Do not use the documentation-site `build.sbt` as the library gate, and do not run a fetched launcher during a read-only review.
2. In a trusted, separately authorized checkout of the 2024 revision, run the correctness gate first: `./mill -i --disable-ticker __.jvm.__.compile + __.jvm.__.test`.
3. If step 5 of the workflow requires it, run the benchmark modules before and after the change: `./mill -i perftests.bench2.test` (Scala 2.13) and `./mill -i perftests.benchScala33.test` (Scala 3.3.3). At the PR 273 revision, the Scala 3 module is `perftests.benchScala3`. Rediscover module names for other revisions.
4. Confirm that the `FailureTests` cases (for example `whitespaceFail`) and the affected consumer suites actually ran, not just compiled.
5. Report the JVM, the Scala cell, which benchmark arm was used and the per-iteration numbers as raw observations. JVM numbers say nothing about JS or Native performance.

This authoring run executed none of these commands.

## Examples

### Good

At PR 273 merge `0a3de65`, Scala 3 `MacroRepImpls` checks at expansion time whether the implicit whitespace is `NoWhitespace` and, if so, emits no whitespace branch. The same PR adds `inline` default parameters to `rep`, which the macro reads as constants. Review outcome: accept the specialization, and file no default-argument finding.

The `:: Nil` changes in the same PR sit in verbose-only aggregation, so classify them as a diagnostics-on improvement. The author's numbers support that classification. The harness counts completed runs per 10-second window, so higher is better. On Scala 3, Benchmark 1 (the traced failure arm) rises from about 1.9k to about 2.8k runs after warm-up, while Benchmark 0 (verbose off) moves only from about 7.6k to about 8.1k. The PR body also includes one Scala 2.13 reference run. Record all of these numbers as author-reported, not reproduced.

### Broken and Correction

A change adds `ctx.freshFailure(msg = s"expected $name")`, which builds the string on every failure regardless of `verboseFailures`. That undoes the gating from commit `e32dd15` and puts diagnostics work on the diagnostics-off path.

Correction: keep `freshFailure()` free of arguments and report the label only under the flag, as `if (ctx.verboseFailures) ctx.reportTerminalMsg(ctx.index, () => msg)` does at PR 297. Then rerun the label tests with diagnostics on, and compare Benchmark 0 with failing input and diagnostics off.

A second broken case: a Scala 2 macro emits a runtime `ws ne NoWhitespace.noWhitespaceImplicit` test into every `.rep` call site. Correction: decide by `ws.tpe =:= typeOf[NoWhitespace.noWhitespaceImplicit.type]` at expansion time, as PR 310 does. This change strictly shrinks the generated code, so green tests and an equivalence argument are enough; a benchmark is optional.

### Negative

A PR rewrites `List(a, b)` to `a :: b :: Nil` in the string formatting of a finished `Parsed.Failure`, or in Scala 2-only `src-2` code, with no profile. That code runs once per finished parse, and the historical evidence for the rewrite concerns Scala 3 verbose aggregation. Do not request or approve it as a performance fix.

A new default argument on a non-inlined public `parse` overload does not trigger this skill. Neither does a Scala 3 `inline` default.

## Output Contract

For each finding, report:

- `file:line`;
- severity;
- the regime (diagnostics off or on) and the path (per-step or cold);
- the mechanism (closure, by-name, eager string, list, default argument on Scala 2 or a runtime helper, runtime branch);
- the evidence ID and the original GitHub URL;
- the expected direction of the cost change;
- a bounded correction;
- the regression test (a label test with diagnostics on) and the benchmark arm to compare, or why no benchmark is needed.

Keep source reasoning, author-reported numbers and numbers you measured separate. Never present a model-based review as a measured speedup. For a no-change verdict, name the gate, regime or cold path that makes the cost acceptable.

## Limitations

- The evidence is mostly author rationale (commit and PR messages) plus source observation. The only reviewer evidence is a short exchange about the compiler matrix. This is not a record of maintainer preferences on performance review.
- The claim that benchmarks are optional for strictly shrinking code rests on PR 310 having no benchmark request. That is an absence of evidence, not a stated policy.
- No benchmark, JIT, bytecode-size or allocation measurement was reproduced.
- The `List` versus `::` claim is tied to a 2023 Scala 3 compiler and may not hold on later versions.
- PR 276 was read only at the patch and source level.
- Independent peer evaluation and authorized execution are still open.

## Sources

- [Evidence and claim subset](references/evidence.json).
- [2018 gating commit](https://github.com/com-lihaoyi/fastparse/commit/e32dd15da436bbcb3702256643663270a18b93e8), [2018 NoWhitespace fast path](https://github.com/com-lihaoyi/fastparse/blob/e7d957694a17f899e5a883205ceeaa044da58001/fasterparser/src/fasterparser/Parsing.scala#L82-L90) and [2018 rep constant folding](https://github.com/com-lihaoyi/fastparse/commit/9f6bd5e21bc8246b70aeccc74f1da3ad288c29ec).
- [Telescoping-overload rationale, 2020](https://github.com/com-lihaoyi/fastparse/blob/dd74612224846d3743e19419b3f1191554b973f5/fastparse/src/fastparse/ParsingRun.scala#L251-L256).
- PR 273: [merge](https://github.com/com-lihaoyi/fastparse/commit/0a3de65844a3879c9a093652f8b2dcce550afd24), [Scala 3 inline defaults](https://github.com/com-lihaoyi/fastparse/blob/0a3de65844a3879c9a093652f8b2dcce550afd24/fastparse/src-3/fastparse/package.scala#L176-L180), [benchmark arms](https://github.com/com-lihaoyi/fastparse/blob/0a3de65844a3879c9a093652f8b2dcce550afd24/perftests/bench2/src/perftests/Utils.scala#L88-L95), [trace cost doc](https://github.com/com-lihaoyi/fastparse/blob/0a3de65844a3879c9a093652f8b2dcce550afd24/fastparse/src/fastparse/Parsed.scala#L120-L141), and lefou's [question](https://github.com/com-lihaoyi/fastparse/pull/273#discussion_r1124148640) with its [reply](https://github.com/com-lihaoyi/fastparse/pull/273#discussion_r1124162833).
- PR 310: [Scala 2 expansion-time NoWhitespace](https://github.com/com-lihaoyi/fastparse/blob/7f6dddcefdef433b5961b8d1ec4a3746c1e03fdd/fastparse/src-2/fastparse/internal/MacroRepImpls.scala#L59-L69) and [discussion](https://github.com/com-lihaoyi/fastparse/pull/310).
- [PR 271 recorded slowdown](https://github.com/com-lihaoyi/fastparse/commit/ac05071ac8dd9f101660f4dbe9057ef74af0f1c9), [rmgk's compatibility tradeoff](https://github.com/com-lihaoyi/fastparse/pull/271#issuecomment-1449822638) and the [2024 benchmark modules](https://github.com/com-lihaoyi/fastparse/blob/d1003d4ed1bee2e2cbdc5b68f3229910165c6b0f/build.mill#L225-L245).
