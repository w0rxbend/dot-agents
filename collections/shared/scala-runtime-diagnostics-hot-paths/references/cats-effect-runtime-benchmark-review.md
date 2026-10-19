# Cats Effect: runtime benchmark relevance for scheduler and packed-stack optimizations (originally scala-cats-effect-runtime-benchmark-review)

Library: typelevel/cats-effect (CE3). Evidence: [evidence/scala-cats-effect-runtime-benchmark-review.json](evidence/scala-cats-effect-runtime-benchmark-review.json) (claims `ce-claim-scheduler-evidence`, `ce-claim-optimization-bottleneck`; evidence IDs such as `ce-scheduler-measure-path`, `ce-scheduler-retraction`, `ce-scheduler-external`, `ce-scheduler-close`, `ce-copy-close`, `ce-code-scheduler-branch`, `ce-code-scheduler-benchmark`, `ce-code-bytestack`, `ce-scheduler-progress-test`, `ce-scheduler-late-work-test`, `ce-scheduler-build-jmh`, `ce-scheduler-build-tests`, `ce-scheduler-build-versions`, `ce-copy-build-platform`, `ce-code-ci-native`).

## Scope

Use on changes to worker placement, initial scheduling versus rescheduling, async callback dispatch, or packed runtime data structures. Decide whether the performance evidence measures the proposed change before interpreting speedup numbers. This is a review procedure, not a replacement scheduler implementation.

Not for: ordinary application latency tuning without tracing a relevant CE runtime path. Do not prescribe external-queue scheduling or `Arrays.copyOf` globally. This differs from generic profiling guidance by requiring CE callback-origin, schedule/reschedule and packed-stack representation checks.

## Prerequisites and version fence

Pin baseline and candidate SHAs and read their actual build, runtime source and benchmark classes. Record Scala, Cats Effect, JDK, platform and workload.

- PR2514's rejected source `118f9af3e97b4387bcd9cc3b4dc8e4373e7d2292`: CE3 base 3.3, Scala 2.12.15/2.13.7/3.0.2, Cats 2.6.1, JVM/JS targets.
- PR3963's rejected source `e0d9ff3166e8207a14b43e41103b569fe76d928a`: base 3.5, Scala 2.12.17/2.13.10/3.2.2, Cats 2.9.0, JVM/JS/Native.

Base versions are build settings, not release assertions. Keep work-stealing JVM claims separate from JVM/Native-shared array changes (ByteStack lives under `core/jvm-native`). Do not execute downloaded benchmarks or build definitions without a separately authorized environment.

## Workflow

1. **Locate the changed path.** Draw entries from fiber `start`, cooperative `cede`, async completion and foreign `Runnable` submission into scheduling. Compare `scheduleFiber` and `rescheduleFiber`; do not infer behavior from similar names or comments alone.
2. **Map each benchmark to that graph.** Separate initialization from the repeated measured work. The inspected WorkStealing benchmark starts fibers, then runs repeated cedes. It is not literally devoid of scheduling, but unchanged cede-loop results cannot establish the benefit of a changed initial-placement policy. Confirm actual hot-path coverage with instrumentation/profiling in the authorized run.
3. **Record callback origin.** An internal Queue backed by Deferred can complete from a compute worker. That is not necessarily the same dispatch path as a foreign NIO completion. Build matched internal and external workloads; for the latter, verify completion from an independently owned pool. The reviewer suggested Dispatcher with external fulfillment, not renaming Queue traffic as external IO.
4. **Separate metrics and confounders.** Distinguish total throughput, per-request latency and how work is distributed across competing tasks. Faster completion of one chosen subset can be priority bias rather than global fairness. Keep work units and pool sizes comparable. CPU-consuming blackholes belong to compute for this workload, not `blocking` merely because they take time.
5. **Check the actual representation.** Before using intrinsic arguments, inspect element type, allocation size, growth frequency and copied metadata. ByteStack is packed `Array[Int]` with a count slot; ArrayStack uses references. Large-byte-array SIMD results cannot establish either path's improvement. Check end-to-end bottleneck relevance before accepting extra complexity.
6. **Separate correctness from speed.** Preserve exactly-once task progress, wakeups, cancellation and ownership; for growth, preserve live elements, count and capacity behavior. Run relevant runtime regressions even if a benchmark improves. Keep JVM performance conclusions bounded when source is shared with Native or JS.
7. **State disposition honestly.** Missing representative evidence means the optimization remains unsubstantiated, not that it is universally harmful. Both historical proposals were closed unmerged. Their benchmark tables are author-reported results, not measurements reproduced by this case.

## Checks

Preserve the invariants of scheduling progress and data representation independently of the metric. Read retractions in the discussion: changing initial placement did not mean every running fiber lost affinity, because rescheduling was unchanged. A functional stress test can reveal a hang without measuring fairness; a high-throughput benchmark can conceal starvation of an unmeasured class of work.

False positives: retaining a cede benchmark as a regression guard is useful even when it cannot prove the new path's benefit. `Arrays.copyOf` may be appropriate for a measured bottleneck elsewhere. Do not reject all intrinsic substitutions based on one closed CE proposal.

## Validation

In an authorized historical checkout, inspect sbt/plugin pins and use `sbt projects` to confirm IDs. At the PR2514 SHA, `benchmarks` depends on `core.jvm` and enables JmhPlugin. The review supplied this invocation shape, to use only after checking the benchmark exists:

- `sbt 'benchmarks/Jmh/run -wi 10 -i 10 -f 2 -t 1 WorkStealingBenchmark.scheduling'`

Its ten warmups/iterations and two forks are the historical example, not a universal confidence guarantee.

Run the existing JVM correctness probes separately:

- `sbt 'testsJVM/testOnly cats.effect.unsafe.DrainBatchSpec'`
- `sbt 'testsJVM/testOnly cats.effect.unsafe.HelperThreadParkSpec'`

DrainBatchSpec drives concurrent starts, bounded queues and a completion counter; HelperThreadParkSpec uses a small runtime, delayed arrivals and owned shutdown. Neither is a fairness benchmark. Read timeout/runtime behavior before running these real-thread stress tests; they are not small deterministic unit tests. No dedicated ByteStack/ArrayStack test file was located at the PR3963 tree, so author a focused growth/count regression rather than inventing a selector.

Before/after measurements must retain exact SHAs, JDK/CPU, pool topology, warmup/forks, units and uncertainty. State any untested JS/Native behavior. This research executed no upstream Scala tests or benchmarks and asserts no speedup.

## Examples

**Good.** A scheduleFiber proposal retains the cede-heavy benchmark as a regression guard, adds a separately fulfilled external-callback workload, and reports request latency alongside total work. It traces both workloads to the same candidate source and keeps runtime-progress tests separate. The proposal stays unverified until those measurements actually run.

**Broken and correction.** A compute-worker Queue workload improves selected request throughput, so a change is advertised as fairer for external NIO. Correction: verify the callback-origin branch, arrange actual foreign-pool completion, remove CPU-only work from the blocking pool, and compare the same work populations. The repaired benchmark design is not itself a performance result. Similarly, replace an irrelevant byte-array benchmark with the actual packed integer growth case before evaluating ByteStack changes.

**Negative.** A reviewer claims the benchmark never calls `start`, or that a schedule-only edit necessarily removes reschedule affinity. Reject those absolutes: source contains initial starts and the historical discussion explicitly retracts the affinity claim. Do not ban array copying merely because PR3963 lacked a worthwhile bottleneck benefit.

## Case output fields

A path/topology/metric matrix and findings with `file:line`, severity, evidence, and the missing or discriminating test. Label each result as source observation, historical participant report, proposed experiment, or locally reproduced measurement. Separate semantic blockers from unsupported performance claims and list platform gaps.

## Limitations

Historical workload critiques do not prove current scheduler behavior. No benchmark efficacy, Native speedup, or universal fairness theorem follows from structural validation. Avoid global runtime redesign until target-version traces and measurements justify it.

## Sources

- [PR2514 path critique](https://github.com/typelevel/cats-effect/pull/2514#issuecomment-962851599), [retraction](https://github.com/typelevel/cats-effect/pull/2514#issuecomment-962952490), [external-callback analysis](https://github.com/typelevel/cats-effect/pull/2514#issuecomment-980841821) and [close](https://github.com/typelevel/cats-effect/pull/2514#issuecomment-1066309829).
- [PR3963 bottleneck disposition](https://github.com/typelevel/cats-effect/pull/3963#issuecomment-1913191239).
- [Pinned implementation, benchmark, correctness tests and claims](evidence/scala-cats-effect-runtime-benchmark-review.json).
