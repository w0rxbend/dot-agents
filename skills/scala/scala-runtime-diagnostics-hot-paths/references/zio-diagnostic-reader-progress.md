# ZIO: diagnostic readers must not depend on subject progress (originally scala-zio-diagnostic-reader-progress)

Library: zio/zio. Evidence: [evidence/scala-zio-diagnostic-reader-progress.json](evidence/scala-zio-diagnostic-reader-progress.json) (claims `c-diagnostic-progress`, `c-diagnostic-reachability`). Pinned regression specification: [zio-diagnostic-reader-progress-regression-spec.md](zio-diagnostic-reader-progress-regression-spec.md).

## Scope

Use when replacing runtime's child collection, routing `children` or fiber-dump reads through messages, changing weak-reference handling, or changing child transfer during parent completion. Also applies when stream optimization unexpectedly changes shared `FiberRuntime` state. Target: runtime observation contract, not general collection style.

Not for: genuinely owner-only state with no foreign observer (do not impose concurrent collections there); application service wiring, general logging, compiler/platform migration. Pure stream hot-path change with unchanged runtime observation belongs to operator-semantics review. Cancel token evaluated before executor shift belongs to `scala-effect-cancellation-finalization` (canceler evaluation owner).

## Prerequisites and version fence

Identify exact ZIO version/branch, Scala version, platform, JDK, runtime implementation. Map production and test projects before editing. Preserve existing effect and build choices.

- PR 8819's final state is `6edd4984c1102eefd1edf9e0582c70e69125d0f8`, May 2024, ZIO 2 `series/2.x`: Scala 2.12.19 / 2.13.13 / 3.3.3, Scala.js plugin 1.16.0, Native plugin 0.4.17. Its JVM child set delegates to synchronized weak set.
- PR 2274 is different ZIO 1-development-era state, `e89e3e23d63260930a8685e2a93729e42a8932dc`, December 2019; its parent/child implementation must not be transplanted into ZIO 2.

Neither development SHA alone identifies exact released artifact.

## Workflow

1. **Inventory observers, not only writers.** Trace public `Fiber.children`, synthetic-fiber delegation, `Fiber.dumpAllWith`, runtime child snapshot construction, platform collection creation. List owner reads, foreign reads, adds, transfers, cleanup, weak-reference expunging. Follow private-helper usages before narrowing visibility or claiming confinement.
2. **Draw the progress dependency.** Per foreign read: runs directly, or sends request that subject run loop must process? Promise-suspended fiber is not necessarily blocked run loop. Model subject stuck inside synchronous I/O while separately runnable observer requests its children.
3. **Audit collection operations for hidden mutation.** Read chosen implementation, including `isEmpty`, traversal, weak-key cleanup. PR 8819's author found supposedly read-only weak-set operation could mutate; granular locking proposal was withdrawn. Do not generalize this into ban on all weak collections.
4. **Preserve independent observation.** Replacement must not introduce wait for subject run-loop progress. Concurrent snapshot or other proven design may suffice; historical synchronization is not universal implementation mandate. Do not claim strict latency bound solely from lock use.
5. **Preserve reachability through completion.** Draw A → B → C; let B finish while C stays alive; inspect both parent pointers and parent child-sets/root tracking. PR 2274's discussion corrected mistaken assumption that updating child's parent pointer alone preserved traversal and interruption. Test observation and ownership, without imposing its old lifetime policy on new major version.
6. **Separate refactoring from optimization.** Keep diagnostic data-structure change reviewable apart from stream throughput work. Reopen final source: PR 8819 restored synchronized child storage while keeping other optimizations. PR 318 supports staging platform seams before bulk moves; it does not independently validate child set.

## Checks

Preserve invariants: diagnostic child read does not newly depend on blocked subject making progress; live descendants stay reachable under this version's ownership policy; safe observation does not require retaining every completed ancestor forever.

Check child-set reference publication separately from synchronization inside set. Verify traversal behavior, not just `add`. Distinguish permitted stale/best-effort snapshot from missing synchronization or permanently lost descendants. Final 2024 source explicitly allows stale snapshot during transfer; do not silently demand linearizable, globally instantaneous fiber tree.

False positives: owner-only buffer with valid publication edge; debug API explicitly documented to require subject cooperation; harmless snapshot staleness permitted by selected implementation. Conversely, labeling a method "debugging only" does not remove its operational progress requirement. Unsynchronized collection is not automatically wrong; `synchronized` alone does not prove freedom from deadlock.

## Validation

Read selected `build.sbt`, `project/BuildHelper.scala`, launcher pin, CI, test sources. May-2024 build defines separate `coreTests` JVM/JS/Native cross-project; its aliases include `coreTestsJVM/test`. With explicit execution authorization and trusted dependencies: discover projects using `sbt projects`, confirm `coreTestsJVM`, then run `sbt 'coreTestsJVM/testOnly *FiberSpec'` and `sbt 'coreTestsJVM/test'`. Verify actual test discovery and outcomes. Do not execute fetched upstream builds during read-only research run.

Inspected `FiberSpec` tests roots and interruption but does **not** establish blocked-subject diagnostic progress. Add [pinned regression specification](zio-diagnostic-reader-progress-regression-spec.md): controlled blocked subject, independently scheduled observer, finite observation deadline, teardown that unblocks subject even when observation fails. Test `children` first; then whole-dump traversal separately, since its callbacks and other reads can introduce unrelated waits. Exercise concurrent child transfer and A/B/C reachability case as separate tests. Port JVM blocking fixtures only to supported platforms. Inspect JS/Native task bodies; do not report compile-only `test` as execution.

## Examples

**Good.** At final PR 8819 SHA, `FiberRuntime.children` directly computes `childrenChunk` in observing effect; collection creation resolves to `Collections.synchronizedSet(newWeakSet[A]())` on JVM. `Fiber.dumpAllWith` recursively visits `fiber.children`. This removes proposed subject-mailbox dependency. Source evidence for access path, not measured bounded-latency guarantee.

**Broken and correction.** Optimization makes child set owner-confined and implements every diagnostic read as `Stateful` message to subject. All tests with runnable subjects pass. Subject blocked inside synchronous I/O cannot process request, so full tree dump can stop there. Correction: keep safe foreign observation or implement independently justified concurrent snapshot; do not merely make callback payload eager. Eager snapshot fixes evaluation ownership but cannot make blocked subject process its mailbox. Add regression that observes before releasing subject's blocking gate.

**Negative.** Local accumulator has no external reads until owner publishes immutable result: no child enumeration, diagnostic traversal, or live-descendant transfer. Do not add locks because PR 8819 used synchronized set. Likewise, snapshot that misses concurrently transferred child once is not automatically violation where documented observations are best-effort; test stable reachability after explicit transfer boundary instead.

## Case output fields

Observer/writer table, progress-dependency diagram, version-specific ownership map. Each finding must include `file:line`, severity, evidence, affected invariant, smallest repair, test with controlled schedule and observable result. Distinguish confirmed mailbox dependency from unproved collection race. Report observed historical tests, proposed stronger oracles, executed tests, outstanding prerequisites separately.

## Limitations

2024 Loom discussion was anticipated runtime constraint, not proof Loom deployment failed or was tested. No upstream Scala test run here. 2019 grandchild regression does not deterministically await parent termination; its `nonFlaky` repetition is weaker than explicit handoff barrier. Blocked-reader regression is original, unexecuted specification pinned to actual source, not newly discovered historical test. Two eras support different parts of review procedure, not one timeless runtime implementation. Formal maintainer ranks remain unknown.

## Sources

- [jdegoes: blocked children observation](https://github.com/zio/zio/pull/8819#discussion_r1594393395).
- [eyalfa: weak-set read can mutate](https://github.com/zio/zio/pull/8819#discussion_r1597677573).
- [Final JVM weak-set implementation](https://github.com/zio/zio/blob/6edd4984c1102eefd1edf9e0582c70e69125d0f8/core/jvm/src/main/scala/zio/internal/PlatformSpecific.scala#L108-L112).
- [2019 discussion corrects reachability assumptions](https://github.com/zio/zio/pull/2274#issuecomment-555686706).
- [2019 grandchild interruption regression](https://github.com/zio/zio/blob/e89e3e23d63260930a8685e2a93729e42a8932dc/core-tests/shared/src/test/scala/zio/FiberSpec.scala#L102-L114).
- [Evidence and exact claim mappings](evidence/scala-zio-diagnostic-reader-progress.json).
