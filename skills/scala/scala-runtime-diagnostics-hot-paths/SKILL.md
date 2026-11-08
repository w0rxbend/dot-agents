---
name: scala-runtime-diagnostics-hot-paths
description: Use when a Scala library change touches a diagnostic mode, failure-trace replay, a runtime diagnostic reader (fiber children/dumps), a per-step hot path (allocation, closures, macro/inline callsite bytecode) or a performance claim backed by a benchmark — covering Fastparse verbose failures/trace and ParsingRun cost, Cats Effect scheduler and packed-stack benchmarks, and ZIO fiber child observation. Unlike the effect-cancellation, stream-scoping, HTTP, compatibility-law and compiler-macro skills, its question is whether observation and optimization leave semantics unchanged and whether the evidence measures the path actually changed.
license: MIT
---

# Scala runtime diagnostics and hot paths

Case files under `references/` hold pinned, library-specific detail.

## When to Use

- Fastparse change to `Fail` labels, `reportTerminalMsg`, terminal aggregation, `opaque`/`unary_!`-style wrappers, `Parsed.Failure`/`trace()`, `ParsingRun` helpers, `Msgs`/`Lazy`, `.rep`/`~`/whitespace macro bodies, or Scala 3 inline port of a Scala 2 macro.
- Cats Effect runtime change to worker placement (`scheduleFiber`/`rescheduleFiber`), async callback dispatch, or packed runtime structures (`ByteStack`, `ArrayStack`), especially if justified by JMH numbers.
- ZIO runtime change to fiber child collection, `Fiber.children`/`Fiber.dumpAllWith` read paths, weak-reference handling, or child transfer on parent completion. Includes stream optimizations touching shared `FiberRuntime` state.
- Analogous code in other Scala libraries: debug/verbose flag gating message construction, replay or re-execution for diagnostics, monitoring read of state owned by another thread/fiber/actor, or PR whose evidence is a microbenchmark.

## When Not to Use

- Change alters parse values, consumed index, cuts or backtracking: start with shared-run combinator case in `scala-compiler-macro-refactoring`. Return here only for its cost or diagnostics.
- Cancellation, finalizers, canceler evaluation ownership, or `Outcome` handling: `scala-effect-cancellation-finalization`.
- Stream element scopes, sink cardinality, foreign callback lanes: `scala-stream-resource-scoping`.
- Binary/source compatibility of new overload or signature: `scala-library-compatibility-laws` (diagnostic overloads still need it).
- Ordinary application latency tuning, generic JVM tuning, or user grammars: `performance-engineering`, `performance-optimization`, `mill-performance`.
- Owner-only state with no foreign observer; cold code running once per finished operation (formatting a `Parsed.Failure`).
- Do not use this skill to push effect systems, immutable state, blanket `List` bans, global locks, or global `Arrays.copyOf` rules onto unrelated code.

## Prerequisites

- Pin exact library version/branch and SHA, Scala cells, platforms (JVM/JS/Native), JDK, and for macro code `src-2` (Scala 2 quasiquote macros) vs `src-3` (Scala 3 inline/quoted). Read these from target build (`build.sc`/`build.mill`/`build.sbt`, `project/*.scala`, CI), never from memory.
- Read changed source **and** its offered test or benchmark, plus callers of both.
- Load matching case file(s) from routing table before writing findings.
- Treat downloaded builds and benchmark harnesses as untrusted. Do not execute them in read-only review; run only in a separately authorized, trusted checkout.

## Shared Model: Invariants

"Transferable": applies to analogous code in other Scala libraries; concrete mechanism stays library-specific.

**I1. Observation does not change the observed result.** Enabling diagnostics, adding a label, or reading runtime state must not change acceptance, consumed index, cuts, scheduling or ownership. *Fastparse diagnostic mode:* custom `Fail(msg)` label must not change failure position or ordinary-mode policy. Hiding/negating wrappers restore terminal aggregate only under `verboseFailures`; index/success/cut computation stays outside the guard. *ZIO:* diagnostic read must not mutate (PR 8819 found a supposedly read-only weak-set operation could mutate). Transferable.

**I2. An observer must not depend on the subject's progress.** Reads routed through subject's mailbox stall exactly when diagnostics matter most: subject blocked in synchronous I/O. *ZIO PR 8819:* final source reads `childrenChunk` directly from a synchronized weak set on JVM; message-only design would stop a tree dump at a blocked subject. *Fastparse* analog: `trace()` re-runs the parser, so needs input still replayable. Buffered iterator/reader input rejects it by design. Transferable: name what each observation path requires (subject run loop, replayable input, deterministic actions).

**I3. Diagnostic modes are separate paths with separate contracts and separate cost budgets.** *Fastparse:* ordinary parse, verbose parse and `trace()` replay each have own expectations (ordinary mode may omit the label). Diagnostics-off is throughput hot path, allocating no message objects before flag check (2018 gating commit `e32dd15`; 2024 `freshFailure()` takes no arguments). Diagnostics-on/trace (documented about 2x slower in 2023) is a real, separately benchmarked budget. Do not dismiss diagnostics-on allocation as cold. Do not cite it as diagnostics-off evidence. Transferable.

**I4. Evidence must exercise the changed path, regime and representation.** *Cats Effect PR2514:* cede-loop benchmark cannot establish an initial-placement change; compute-worker Queue completion is not foreign NIO completion. *Cats Effect PR3963:* large-byte-array SIMD results say nothing about packed `Array[Int]` ByteStack growth. *Fastparse:* report Benchmark 0 (`parse(data).get`, verbose off) and Benchmark 1 (failing parse + `.extra.traced`) separately; judge verbose-aggregation changes by failure arm. Transferable.

**I5. Oracles must discriminate.** Test passing with defect present is not evidence. *Fastparse PR 244:* test asked for custom label and also expected `"fail"`; PR 297 fixed producer and oracle together. *ZIO:* `FiberSpec` tests roots and interruption, not blocked-subject progress. 2019 grandchild regression's `nonFlaky` repetition does not force parent-terminated interleaving. *Cats Effect:* `DrainBatchSpec`/`HelperThreadParkSpec` are progress stress tests, not fairness benchmarks. Transferable: keep a control (default label, runnable subject, unchanged path) next to each discriminating case.

**I6. Correctness gates are separate from speed claims.** "Same semantics, fewer allocations or less bytecode, in a named regime": check both halves (*Fastparse*). Preserve exactly-once progress, wakeups, cancellation, ownership and growth invariants even when a benchmark improves (*Cats Effect*). Keep diagnostic data-structure change independently reviewable from stream throughput work (*ZIO PR 8819*, which restored synchronized child storage while retaining other optimizations). Transferable.

**I7. Generated code size is a hot-path cost of its own.** Macro/inline bodies paste into every call site. Prefer branches decided at expansion time over runtime no-op checks (`NoWhitespace` type test: Scala 2 `~` 2018 `e7d9576`, Scala 3 `.rep` PR 273, Scala 2 `.rep` PR 310). For Scala 2 macros and non-inline helpers called from expanded code, prefer telescoping overloads to default arguments ("bytecode size blowup", 2020 `ParsingRun` comment). Scala 3 `inline` defaults read as expansion-time constants are intended design. Library-specific to macro/inline-heavy libraries; Scala 2 vs Scala 3 split is a version fence.

**I8. Dispositions follow the evidence's provenance.** Distinguish source observation, reviewer proposal, merged decision, author-reported numbers, inference, proposed experiment, and locally reproduced measurement. Missing representative evidence means "unsubstantiated", not "harmful" (both CE proposals closed unmerged; neither bans array copying or initial-placement changes). Strictly shrinking expansion-time change may need only an equivalence argument and green tests (PR 310 merged with no benchmark request: absence of evidence, not stated policy). Transferable.

## Routing Table

| Change touches | Load |
|---|---|
| Fastparse `Fail`/`Fail(msg)`, `reportTerminalMsg`, `freshFailure` label flow, `Parsed.Failure` messages, `Extra.trace`/`trace()`, `checkTraceable`, `ParserInput` replay capability, `opaque`, `unary_!`, any hiding/negating wrapper, `terminalMsgs`/`terminalParserMsgs`, `longAggregateMsg`/`longMsg`/`longTerminalsMsg` | [references/fastparse-diagnostic-mode-review.md](references/fastparse-diagnostic-mode-review.md) |
| Fastparse `ParsingRun` success/failure/report helpers, `Msgs`/`Lazy` construction, `aggregateMsg`/`aggregateTerminal`/`setMsg`, `.rep`/`~`/literal/whitespace macro bodies (`MacroRepImpls`, `src-2` vs `src-3`), default arguments vs overloads in expanded code, `perftests` numbers, compiler-matrix edits in a perf PR | [references/fastparse-hot-path-cost-review.md](references/fastparse-hot-path-cost-review.md) |
| Both label behavior and its cost (e.g. new eager message argument) | Both Fastparse files: diagnostic-mode for contract, hot-path for cost |
| Cats Effect `WorkStealingThreadPool` placement, `scheduleFiber`/`rescheduleFiber`, `start`/`cede`/async completion entry, external `Runnable` submission, `WorkStealingBenchmark`, `ByteStack`/`ArrayStack` growth, `Arrays.copyOf`/intrinsic arguments, JMH runs | [references/cats-effect-runtime-benchmark-review.md](references/cats-effect-runtime-benchmark-review.md) |
| ZIO `FiberRuntime` child set, `Fiber.children`, `Fiber.dumpAllWith`, `childrenChunk`, `getChildren`, `transferChildren`, `PlatformSpecific` weak-set construction, routing reads through `Stateful` messages, parent/child reachability on completion | [references/zio-diagnostic-reader-progress.md](references/zio-diagnostic-reader-progress.md) and its [regression specification](references/zio-diagnostic-reader-progress-regression-spec.md) |
| Analogous code elsewhere (debug flag gating, replay-for-diagnostics, cross-thread monitoring reads, microbenchmark-justified PRs) | This file's workflow; load nearest case as worked example |

## Workflow

**[T]** steps transfer to analogous code. **[L]** marks library/version-specific detail held in case files.

1. **[T] Classify the change.** Diagnostic contract change (what is reported or observable), diagnostic access-path change (how observation reaches state), hot-path cost change, or performance claim? Many diffs are several; review each separately (I6).
2. **[T] Map the paths and regimes.** Draw every path through changed code. Parsers: ordinary / verbose / replay, and per-step vs once-after-parse. Runtimes: `start` / `cede` / async completion / foreign submission, and owner read vs foreign read vs transfer vs cleanup. **[L]** Use case file's concrete path list (e.g. Fastparse Benchmark 0/1, CE `scheduleFiber` vs `rescheduleFiber`, ZIO `dumpAllWith` → `children` → `childrenChunk`).
3. **[T] State the contract independently of existing tests.** Write per-path expectations: result and position unchanged; label/terminals as intended; observation completes without subject running; live descendants reachable under this version's ownership policy; no message allocation with diagnostics off. Assertion copied from old behavior does not specify a new parameter.
4. **[T] Trace data flow end to end.** Follow new parameter from producer to reporting closure and formatter (Fastparse PR 244 dropped it at the closure). Follow a read to what it really executes, including hidden mutation in "read-only" collection operations (ZIO weak set).
5. **[T] Find progress dependencies.** Per observation, ask what must run or stay available for it to complete: subject's run loop, replayable input, deterministic parser actions, right pool. Promise-suspended fiber is not necessarily a blocked run loop; model synchronous blocking explicitly.
6. **[T] Check gating before work.** On fast path, nothing diagnostic is evaluated before flag check: no strings, by-names, `() => ...`, `new Lazy`, `Msgs(...)`, `List(...)` arguments. **[L]** For macro/inline code, decide branches at expansion time and respect Scala 2 overloads vs Scala 3 inline-defaults split.
7. **[T] Audit the evidence against the path.** For each offered test and benchmark: which path and regime does its measured loop execute (not its setup)? Which callback origin? Which data representation (element type, size, growth frequency)? Which metric (throughput, per-request latency, distribution across competing work)? Would it fail if defect were present? Confirm hot-path coverage with profiling/instrumentation in an authorized run.
8. **[T] Design the discriminating oracle.** Pair each defect-detecting test with a control: default label next to custom label; runnable subject next to blocked subject; unchanged benchmark kept as regression guard next to new-path workload. Use deterministic schedules (explicit gates and barriers, finite deadlines, teardown that cannot hang), not repetition.
9. **[T] Repair minimally.** Repair producer and oracle together. Keep existing verbosity owner (`ctx.verboseFailures`). Restore independent observation instead of making a mailbox payload eager. Prefer expansion-time elimination. Keep refactor and optimization in separately reviewable units.
10. **[T] Dispose by provenance (I8).** Report what is source-observed, author-reported, proposed, and what you executed. Do not convert closed proposals into bans, or noisy single runs into regressions.

## Review and Refactoring Checks

Transferable:

- [ ] Enabling diagnostics changes no result, position, cut, scheduling decision or ownership.
- [ ] Ordinary-mode/default behavior (default label, default overload, owner-only writes) unchanged.
- [ ] Each foreign observation completes without observed subject making progress, or its cooperation requirement is explicitly documented.
- [ ] Replay/re-execution for diagnostics keeps same original input and start position, checks its capability, and serves as oracle only for deterministic code.
- [ ] No diagnostic work evaluated before the gate on a per-step path.
- [ ] "Read-only" operations on chosen collection really do not mutate.
- [ ] Publication of a shared reference checked separately from synchronization inside the structure.
- [ ] Each test/benchmark exercises changed path, regime, callback origin and representation; setup not mistaken for measured loop.
- [ ] Metrics separated (throughput vs latency vs fairness/distribution); work units and pool sizes comparable; CPU work not moved to a blocking pool merely because it is slow.
- [ ] Each discriminating test has a control and deterministic schedule.
- [ ] Correctness regressions run regardless of benchmark outcome.
- [ ] JVM conclusions not extended to JS/Native, especially for source shared across platforms.
- [ ] Compiler-matrix changes in a performance PR carry their own stated reason.

Library/version-specific (details in case files):

- [ ] Fastparse: hiding/negating wrappers snapshot and restore terminal aggregate under `verboseFailures`; wrapper label reported at its start index; enclosing terminals survive; trace views asserted separately.
- [ ] Fastparse: Scala 2 macro/non-inline helpers avoid default arguments in expanded code; Scala 3 `inline` defaults accepted; `List` vs `::` rewrites only with a profile on affected compiler.
- [ ] Cats Effect: `scheduleFiber` vs `rescheduleFiber` compared directly; external-callback workload fulfilled from independently owned pool; ByteStack evaluated as packed `Array[Int]` with a count slot.
- [ ] ZIO: A → B → C reachability after B completes, checking both parent pointers and child-sets/root tracking; stale snapshot during transfer permitted in 2024 source; ZIO 1 parent/child design not transplanted into ZIO 2.

## Consolidated False Positives

- Fastparse: empty nonverbose label in `Parsed.Failure`; buffered-input `trace()` rejection; formatting-only changes; transparent wrappers (named rule, logging wrapper) keeping child terminals; narrowed downstream `terminals` snapshots after an opaque fix (PR 278 narrowed four ScalaParse expectations; justify each).
- Fastparse cost: message building inside an existing `if (ctx.verboseFailures)` block when question is diagnostics-off cost; formatting a finished `Parsed.Failure`; `List(...)` in Scala 2-only or cold code; Scala 3 `inline` defaults read as constants; default argument on a non-inlined public method kept for API compatibility; regression claim from one noisy iteration. **Not** a false positive: allocation added to `trace()` replay or verbose aggregation.
- Cats Effect: keeping a cede benchmark as regression guard; `Arrays.copyOf` for a measured bottleneck elsewhere; claims that benchmark never calls `start`, or that a schedule-only edit removes reschedule affinity (both refuted in source/discussion).
- ZIO: owner-only buffer with valid publication edge; debug API explicitly documented to require subject cooperation; harmless staleness permitted by selected implementation; unsynchronized collection is not automatically wrong. Conversely, "debugging only" does not remove a progress requirement, and `synchronized` alone does not prove freedom from deadlock.
- General: matching a failure index alone does not prove label correctness. A merged PR with an added test did not prevent the Fastparse ignored-message defect.

## Version Fences

| Library | Fence |
|---|---|
| Fastparse diagnostics | PR 244 head `749d0c1` (2023-03-07, defect); PR 297 merge `49ba3cf` (2023-11-26, fix; Scala 3.3.1/3.2.2/2.13.10/2.12.17/2.11.12; Scala 3 excluded from Native 0.4.9 matrix — do not transfer). First released version with the fix not established. `terminalParserMsgs` (PR 276 `f40fe81`) → `terminalMsgs` (PR 278 `186337a`). |
| Fastparse cost | 2018 `tracingEnabled`/`shortFailureMsg`; 2023 PR 273 `0a3de65` `verboseFailures`/`Msgs`/`Lazy` (Scala 3.2.2, 2.13.10, 2.12.17, 2.11.12; Scala 3 bench module `perftests.benchScala3`); 2024 snapshot Scala 3.3.3, 2.13.14, 2.12.19, Mill 0.12.0, `perftests.bench2`/`perftests.benchScala33`. `List` vs `::` evidence is a 2023 Scala 3 compiler observation. |
| Cats Effect | PR2514 `118f9af` (CE3 base 3.3, Scala 2.12.15/2.13.7/3.0.2, Cats 2.6.1, JVM/JS); PR3963 `e0d9ff3` (base 3.5, Scala 2.12.17/2.13.10/3.2.2, Cats 2.9.0, JVM/JS/Native). Both closed unmerged. Base versions are build settings, not release assertions. |
| ZIO | ZIO 2 PR 8819 final `6edd498` (May 2024, Scala 2.12.19/2.13.13/3.3.3, Scala.js plugin 1.16.0, Native plugin 0.4.17); ZIO 1-era PR 2274 `e89e3e2` (Dec 2019). Development SHAs, not release artifacts. Loom was an anticipated constraint, not a tested deployment. |

All inspected Fastparse cores are synchronous and use no CE/ZIO/Ox runtime.

## Validation

1. **Discover real targets.** Read target build and CI, then list modules (`./mill resolve __` style discovery for Mill builds, `sbt projects` for sbt builds) before using any selector. Fastparse's sampled `build.sbt` is the documentation site, not the library gate. Case files give historical selectors (e.g. `./mill -i 'fastparse.jvm[3.3.1].test'`, `./mill -i perftests.bench2.test`, `sbt 'testsJVM/testOnly cats.effect.unsafe.DrainBatchSpec'`, `sbt 'coreTestsJVM/testOnly *FiberSpec'`); rediscover them for other revisions.
2. **Correctness before speed.** Run correctness gate first. Confirm relevant cases really executed (not compile-only), including on JS/Native where claimed.
3. **Fail-before / pass-after.** In an authorized checkout, minimal regression must fail on the defect and pass on the repair. Mutation check (e.g. reverting Fastparse's reporting closure to the default literal) validates the oracle itself.
4. **Measure only when the risk warrants it.** For added per-step work or changed aggregation, compare before/after on same toolchain; report each arm separately. Record exact SHAs, JDK/CPU, Scala cell, pool topology, warmup/forks, units, per-iteration raw numbers and uncertainty.
5. **Report external flakiness separately.** Do not rerun until only a green run is visible. Do not relabel author-reported CI retries as local success.

Proposed regressions (e.g. the ZIO blocked-reader specification) are unexecuted specifications.

## Examples

### Good

- Fastparse PR 297: `Fail(msg)` reports `() => msg` only under `ctx.verboseFailures`, plain `Fail` keeps `"fail"`, and replay test expects `Expected failWithLabel:1:1 / custom fail msg:1:1, found "asdad"`. Contract, gate and oracle agree (I1, I3, I5).
- Fastparse PR 273: Scala 3 `.rep` eliminates whitespace branch at expansion time for `NoWhitespace`. `:: Nil` rewrites sit in verbose aggregation and are judged by traced failure arm (author-reported Scala 3 Benchmark 1 ~1.9k → ~2.8k runs per 10 s window, Benchmark 0 ~7.6k → ~8.1k; not reproduced) (I3, I4, I7).
- ZIO PR 8819 final: `children` computes `childrenChunk` directly from a JVM synchronized weak set; no subject-mailbox dependency (I2). Source evidence of the access path, not a latency bound.

### Broken and Correction

- Eager `ctx.freshFailure(msg = s"expected $name")` builds a string on every failure. Correction: argument-free `freshFailure()` and label reporting under the flag; rerun label tests with diagnostics on; compare Benchmark 0 with failing input and diagnostics off (I3).
- ZIO child set made owner-confined, with every read sent as a `Stateful` message, passes all tests with runnable subjects. Yet a dump stalls at a subject blocked in synchronous I/O. Correction: safe foreign observation or justified concurrent snapshot (eager payload does not help), plus gated regression that observes before releasing the subject (I2, I5).
- Compute-worker Queue workload advertised as proof of fairer external NIO scheduling. Correction: verify callback-origin branch, complete from a foreign pool, keep CPU work on compute, compare same work populations. Repaired design is not itself a result (I4, I8).

### Negative

- `List(a, b)` → `a :: b :: Nil` rewrite in `Parsed.Failure` formatting or Scala 2-only code without a profile: not a performance fix; do not request or approve it as one.
- `IteratorParserInput` rejecting `trace()` after consumption: intended capability check, not a missing label fix.
- Owner-local accumulator published as an immutable result: no foreign observer, so no lock needed.
- Reviewer claim that a schedule-only CE edit necessarily removes reschedule affinity: refuted by the retraction in PR2514.

## Output Contract

Return:

1. **Classification and path map:** change kind(s) from workflow step 1; path/regime (or path/topology/metric) matrix; for runtime readers, observer/writer table and progress-dependency diagram.
2. **Findings**, each with `file:line`, severity, invariant (I1–I8) and case, regime/path or mode/input capability, mechanism, evidence ID and original source URL, bounded correction, and discriminating test with its control (or benchmark arm to compare, or why none is needed).
3. **Provenance labels** on every claim: source observation, reviewer proposal, merged decision, author/participant report, inference, proposed experiment, or locally executed result. Separate implementation defects from defective oracles, and semantic blockers from unsupported performance claims.
4. **Execution record:** commands and results only if really executed. Otherwise "source-reviewed / model-based" with missing execution listed, plus platform gaps.
5. For no-change verdicts: the gate, regime, cold path, documented policy or capability check making the apparent issue intentional.

## Limitations

- Four cases from three libraries. Shared invariants are synthesized from them and are review heuristics, not proofs of performance neutrality, fairness, bounded latency or exhaustive aggregation correctness.
- Evidence is mostly source observation and author rationale. Reviewer evidence is sparse (Fastparse: PR 244 mode-preservation request and a PR 273 compiler-matrix exchange; Cats Effect: PR2514/PR3963 discussions; ZIO: PR 8819 and PR 2274 discussions). Historical maintainer rank not inferred.
- No benchmark, JIT, bytecode-size, allocation or upstream test result was reproduced. Author-reported numbers are reported as such.
- Historical fixes and closed proposals do not establish current behavior or released versions. Re-pin on target revision.
- Independent peer evaluation and authorized Scala execution remain open gates.

## Sources

- [Fastparse diagnostic modes and trace replay](references/fastparse-diagnostic-mode-review.md) — evidence [scala-fastparse-diagnostic-mode-review.json](references/evidence/scala-fastparse-diagnostic-mode-review.json).
- [Fastparse hot-path and callsite cost](references/fastparse-hot-path-cost-review.md) — evidence [scala-fastparse-hot-path-cost-review.json](references/evidence/scala-fastparse-hot-path-cost-review.json).
- [Cats Effect runtime benchmark relevance](references/cats-effect-runtime-benchmark-review.md) — evidence [scala-cats-effect-runtime-benchmark-review.json](references/evidence/scala-cats-effect-runtime-benchmark-review.json).
- [ZIO diagnostic reader progress](references/zio-diagnostic-reader-progress.md) and [regression specification](references/zio-diagnostic-reader-progress-regression-spec.md) — evidence [scala-zio-diagnostic-reader-progress.json](references/evidence/scala-zio-diagnostic-reader-progress.json).
- Neighbouring skills: `scala-oss-library-review` (router), `scala-library-contracts`, `scala-type-system`, `scala-functional-patterns`, `direct-style-scala`, `scala-effect-cancellation-finalization`, `scala-stream-resource-scoping`, `scala-http-server-semantics`, `scala-library-compatibility-laws`, `scala-compiler-macro-refactoring`.
