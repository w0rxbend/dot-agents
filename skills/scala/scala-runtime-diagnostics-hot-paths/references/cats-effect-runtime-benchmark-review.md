# Cats Effect: runtime benchmark relevance for scheduler and packed-stack optimizations (originally scala-cats-effect-runtime-benchmark-review)

Library: typelevel/cats-effect (CE3). Evidence: [evidence/scala-cats-effect-runtime-benchmark-review.json](evidence/scala-cats-effect-runtime-benchmark-review.json) (claims `ce-claim-scheduler-evidence`, `ce-claim-optimization-bottleneck`; evidence IDs such as `ce-scheduler-measure-path`, `ce-scheduler-retraction`, `ce-scheduler-external`, `ce-scheduler-close`, `ce-copy-close`, `ce-code-scheduler-branch`, `ce-code-scheduler-benchmark`, `ce-code-bytestack`, `ce-scheduler-progress-test`, `ce-scheduler-late-work-test`, `ce-scheduler-build-jmh`, `ce-scheduler-build-tests`, `ce-scheduler-build-versions`, `ce-copy-build-platform`, `ce-code-ci-native`).

## Scope

Use for changes to worker placement, initial scheduling versus rescheduling, async callback dispatch, or packed runtime data structures. Before reading speedup numbers, check whether performance evidence measures the proposed change. Review procedure, not replacement scheduler.

Not for: application latency tuning that traces no relevant CE runtime path. Do not prescribe external-queue scheduling or `Arrays.copyOf` globally. Unlike generic profiling guidance, requires CE callback-origin, schedule/reschedule and packed-stack representation checks.

## Prerequisites and version fence

Pin baseline and candidate SHAs; read actual build, runtime source and benchmark classes. Record Scala, Cats Effect, JDK, platform, workload.

- PR2514's rejected source `118f9af3e97b4387bcd9cc3b4dc8e4373e7d2292`: CE3 base 3.3, Scala 2.12.15/2.13.7/3.0.2, Cats 2.6.1, JVM/JS targets.
- PR3963's rejected source `e0d9ff3166e8207a14b43e41103b569fe76d928a`: base 3.5, Scala 2.12.17/2.13.10/3.2.2, Cats 2.9.0, JVM/JS/Native.

Base versions are build settings, not release assertions. Keep work-stealing JVM claims apart from JVM/Native-shared array changes (ByteStack lives under `core/jvm-native`). Do not execute downloaded benchmarks or build definitions without separately authorized environment.

## Workflow

1. **Locate the changed path.** Draw scheduling entries from fiber `start`, cooperative `cede`, async completion, foreign `Runnable` submission. Compare `scheduleFiber` and `rescheduleFiber`; do not infer behavior from similar names or comments alone.
2. **Map each benchmark to that graph.** Separate initialization from repeated measured work. Inspected WorkStealing benchmark starts fibers, then runs repeated cedes. Not literally devoid of scheduling, but unchanged cede-loop results cannot show benefit of changed initial-placement policy. Confirm hot-path coverage by instrumentation/profiling in authorized run.
3. **Record callback origin.** Internal Queue backed by Deferred can complete from compute worker, not necessarily same dispatch path as foreign NIO completion. Build matched internal and external workloads; verify external completion comes from independently owned pool. Reviewer suggested Dispatcher with external fulfillment, not renaming Queue traffic as external IO.
4. **Separate metrics and confounders.** Distinguish total throughput, per-request latency and work distribution across competing tasks. One chosen subset finishing faster can be priority bias, not global fairness. Keep work units and pool sizes comparable. CPU-consuming blackholes belong on compute for this workload, not `blocking` merely because they take time.
5. **Check the actual representation.** Before intrinsic arguments, inspect element type, allocation size, growth frequency, copied metadata. ByteStack: packed `Array[Int]` with count slot. ArrayStack: references. Large-byte-array SIMD results cannot establish either path's improvement. Check end-to-end bottleneck relevance before accepting extra complexity.
6. **Separate correctness from speed.** Preserve exactly-once task progress, wakeups, cancellation, ownership; for growth, live elements, count and capacity behavior. Run relevant runtime regressions even if benchmark improves. Bound JVM performance conclusions when source is shared with Native or JS.
7. **State disposition honestly.** Missing representative evidence leaves optimization unsubstantiated, not universally harmful. Both historical proposals closed unmerged; their benchmark tables are author-reported, not reproduced by this case.

## Checks

Read discussion retractions: changing initial placement did not strip affinity from every running fiber, because rescheduling was unchanged. Functional stress test can reveal hang without measuring fairness. High-throughput benchmark can hide starvation of unmeasured work class.

False positives: cede benchmark kept as regression guard, useful even when it cannot prove new path's benefit. `Arrays.copyOf` may fit measured bottleneck elsewhere. Do not reject all intrinsic substitutions over one closed CE proposal.

## Validation

In authorized historical checkout, inspect sbt/plugin pins; confirm IDs with `sbt projects`. At PR2514 SHA, `benchmarks` depends on `core.jvm` and enables JmhPlugin. Review supplied this invocation shape; use only after confirming benchmark exists:

- `sbt 'benchmarks/Jmh/run -wi 10 -i 10 -f 2 -t 1 WorkStealingBenchmark.scheduling'`

Ten warmups/iterations and two forks: historical example, not universal confidence guarantee.

Run existing JVM correctness probes separately:

- `sbt 'testsJVM/testOnly cats.effect.unsafe.DrainBatchSpec'`
- `sbt 'testsJVM/testOnly cats.effect.unsafe.HelperThreadParkSpec'`

DrainBatchSpec: concurrent starts, bounded queues, completion counter. HelperThreadParkSpec: small runtime, delayed arrivals, owned shutdown. Neither is fairness benchmark. Both are real-thread stress tests, not small deterministic unit tests; read timeout/runtime behavior before running. No dedicated ByteStack/ArrayStack test file found at PR3963 tree. Write focused growth/count regression; do not invent selector.

Before/after measurements must keep exact SHAs, JDK/CPU, pool topology, warmup/forks, units, uncertainty. State untested JS/Native behavior. This research executed no upstream Scala tests or benchmarks; asserts no speedup.

## Examples

**Good.** scheduleFiber proposal keeps cede-heavy benchmark as regression guard, adds separately fulfilled external-callback workload, reports request latency beside total work. Both workloads traced to same candidate source; runtime-progress tests kept separate. Proposal stays unverified until those measurements run.

**Broken and correction.** Compute-worker Queue workload improves selected request throughput; change advertised as fairer for external NIO. Correction: verify callback-origin branch, arrange actual foreign-pool completion, move CPU-only work off blocking pool, compare same work populations. Repaired benchmark design is not itself a performance result. Likewise, before evaluating ByteStack changes, replace irrelevant byte-array benchmark with actual packed integer growth case.

**Negative.** Reviewer claims benchmark never calls `start`, or schedule-only edit necessarily removes reschedule affinity. Reject both absolutes: source contains initial starts; historical discussion explicitly retracts affinity claim.

## Case output fields

Path/topology/metric matrix. Findings with `file:line`, severity, evidence, missing or discriminating test. Label each result: source observation, historical participant report, proposed experiment, or locally reproduced measurement. Separate semantic blockers from unsupported performance claims; list platform gaps.

## Limitations

Historical workload critiques do not prove current scheduler behavior. Structural validation proves no benchmark efficacy, Native speedup, or universal fairness theorem. Avoid global runtime redesign until target-version traces and measurements justify it.

## Sources

- [PR2514 path critique](https://github.com/typelevel/cats-effect/pull/2514#issuecomment-962851599), [retraction](https://github.com/typelevel/cats-effect/pull/2514#issuecomment-962952490), [external-callback analysis](https://github.com/typelevel/cats-effect/pull/2514#issuecomment-980841821) and [close](https://github.com/typelevel/cats-effect/pull/2514#issuecomment-1066309829).
- [PR3963 bottleneck disposition](https://github.com/typelevel/cats-effect/pull/3963#issuecomment-1913191239).
- [Pinned implementation, benchmark, correctness tests and claims](evidence/scala-cats-effect-runtime-benchmark-review.json).
