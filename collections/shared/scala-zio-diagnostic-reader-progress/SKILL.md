---
name: scala-zio-diagnostic-reader-progress
description: Use when changing ZIO fiber diagnostic reads. Review child-set synchronization, blocked-subject progress, and descendant reachability during runtime refactoring.
license: MIT
---

# ZIO diagnostic readers are real observers

Removing a lock can preserve writer confinement while breaking diagnostics. Review who reads runtime state, whether those reads need the subject to run, and whether living descendants remain discoverable after parent completion.

## When to Use

Use when replacing the runtime's child collection, routing `children` or fiber-dump reads through messages, changing weak-reference handling, or changing child transfer during parent completion. It also applies when a stream optimization unexpectedly changes shared `FiberRuntime` state. The concrete target is a runtime observation contract, not general collection style.

## When Not to Use

Do not impose concurrent collections on genuinely owner-only state with no foreign observer. Do not use this for application service wiring, general logging, or a compiler/platform migration. A pure stream hot-path change with unchanged runtime observation belongs to an operator-semantics review. A cancel token evaluated before an executor shift belongs to `scala-zio-canceler-evaluation-owner`.

## Prerequisites

Identify the exact ZIO version/branch, Scala version, platform, JDK, and runtime implementation. Map production and test projects before editing. Preserve existing effect and build choices.

PR 8819's final state is `6edd4984c1102eefd1edf9e0582c70e69125d0f8`, May 2024, ZIO 2 `series/2.x`: Scala 2.12.19 / 2.13.13 / 3.3.3, Scala.js plugin 1.16.0, Native plugin 0.4.17. Its JVM child set delegates to a synchronized weak set. PR 2274 is a different ZIO 1-development-era state, `e89e3e23d63260930a8685e2a93729e42a8932dc`, December 2019; its parent/child implementation must not be transplanted into ZIO 2. Neither development SHA identifies an exact released artifact by itself.

## Workflow

1. **Inventory observers, not only writers.** Trace public `Fiber.children`, synthetic-fiber delegation, `Fiber.dumpAllWith`, runtime child snapshot construction, and platform collection creation. List owner reads, foreign reads, adds, transfers, cleanup, and weak-reference expunging. Follow usages of private helpers before narrowing visibility or claiming confinement.
2. **Draw the progress dependency.** For each foreign read, ask whether it runs directly or sends a request requiring the subject run loop to process it. A Promise-suspended fiber is not necessarily a blocked run loop. Model a subject stuck inside synchronous I/O while a separately runnable observer requests its children.
3. **Audit collection operations for hidden mutation.** Read the chosen implementation, including `isEmpty`, traversal, and weak-key cleanup. PR 8819's author found the supposed read-only weak-set operation could mutate; a granular locking proposal was withdrawn. Do not generalize this into a ban on all weak collections.
4. **Preserve independent observation.** Require the replacement not to introduce a wait for subject run-loop progress. A concurrent snapshot or another proven design may suffice; historical synchronization is not a universal implementation mandate. Do not claim a strict latency bound solely from use of a lock.
5. **Preserve reachability through completion.** Draw A → B → C, let B finish while C remains alive, and inspect both parent pointers and parent child-sets/root tracking. PR 2274's discussion corrected a mistaken assumption that updating the child's parent pointer alone preserved traversal and interruption. Test both observation and ownership, without imposing its old lifetime policy on a new major version.
6. **Separate refactoring from optimization.** Keep the diagnostic data-structure change independently reviewable from stream throughput work. Reopen the final source: PR 8819 restored synchronized child storage, while retaining other optimizations. PR 318 supports staging platform seams before bulk moves; it does not independently validate the child set.

## Review and Refactoring Checks

Preserve the invariants that a diagnostic child read does not newly depend on the blocked subject making progress, live descendants remain reachable according to this version's ownership policy, and safe observation does not require retaining every completed ancestor forever.

Check publication of the child-set reference separately from synchronization inside the set. Verify traversal behavior, not just `add`. Distinguish a permitted stale/best-effort snapshot from missing synchronization or permanently lost descendants. The final 2024 source explicitly allows a stale snapshot during transfer; do not silently demand a linearizable, globally instantaneous fiber tree.

False positives: an owner-only buffer with a valid publication edge; a debug API explicitly documented to require subject cooperation; or harmless snapshot staleness permitted by the selected implementation. Conversely, labeling a method “debugging only” does not remove its operational progress requirement. An unsynchronized collection is not automatically wrong, and `synchronized` does not by itself prove freedom from deadlock.

## Validation

Read the selected `build.sbt`, `project/BuildHelper.scala`, launcher pin, CI, and test sources. The May-2024 build defines the separate `coreTests` JVM/JS/Native cross-project; its aliases include `coreTestsJVM/test`. With explicit execution authorization and trusted dependencies, discover projects using `sbt projects`, confirm `coreTestsJVM`, then run `sbt 'coreTestsJVM/testOnly *FiberSpec'` and `sbt 'coreTestsJVM/test'`. Verify actual test discovery and outcomes. Do not execute fetched upstream builds during a read-only research run.

The inspected `FiberSpec` tests roots and interruption but does **not** establish blocked-subject diagnostic progress. Add the [pinned regression specification](references/regression-spec.md): a controlled blocked subject, an independently scheduled observer, a finite observation deadline, and teardown that unblocks the subject even when observation fails. First test `children`; then separately test whole-dump traversal, whose callbacks and other reads can introduce unrelated waits. Exercise concurrent child transfer and the A/B/C reachability case as separate tests. Port JVM blocking fixtures only to supported platforms; inspect JS/Native task bodies rather than reporting a compile-only `test` as execution.

## Examples

### Good

At the final PR 8819 SHA, `FiberRuntime.children` directly computes `childrenChunk` in the observing effect; collection creation resolves to `Collections.synchronizedSet(newWeakSet[A]())` on JVM. `Fiber.dumpAllWith` recursively visits `fiber.children`. This removes the proposed subject-mailbox dependency. It is source evidence for the access path, not a measured bounded-latency guarantee.

### Broken and Correction

An optimization makes the child set owner-confined and implements every diagnostic read as a `Stateful` message to the subject. All tests with runnable subjects pass. A subject blocked inside synchronous I/O cannot process the request, so a full tree dump can stop there. Correction: retain safe foreign observation or implement an independently justified concurrent snapshot; do not merely make the callback payload eager. The eager snapshot fixes evaluation ownership but cannot make a blocked subject process its mailbox. Add a regression that observes before releasing the subject's blocking gate.

### Negative

A local accumulator has no external reads until its owner publishes an immutable result. There is no child enumeration, diagnostic traversal, or live-descendant transfer. Do not add locks because PR 8819 used a synchronized set. Similarly, a snapshot that misses a concurrently transferred child once is not automatically a violation where documented observations are best-effort; test stable reachability after an explicit transfer boundary instead.

## Output Contract

Return an observer/writer table, a progress-dependency diagram, and a version-specific ownership map. Each finding must include `file:line`, severity, evidence, the invariant affected, the smallest repair, and a test with a controlled schedule and observable result. Distinguish a confirmed mailbox dependency from an unproved collection race. Report observed historical tests, proposed stronger oracles, executed tests, and outstanding prerequisites separately.

## Limitations

The Loom discussion in 2024 was an anticipated runtime constraint, not proof that a Loom deployment failed or was tested. No upstream Scala test was run here. The 2019 grandchild regression does not deterministically await parent termination; its `nonFlaky` repetition is weaker than an explicit handoff barrier. Our blocked-reader regression is an original, unexecuted specification pinned to actual source, not a newly discovered historical test. The two eras support different parts of the review procedure, not one timeless runtime implementation. Formal maintainer ranks remain unknown.

## Sources

- [Evidence and exact claim mappings](references/evidence.json): `c-diagnostic-progress`, `c-diagnostic-reachability`.
- [jdegoes: blocked children observation](https://github.com/zio/zio/pull/8819#discussion_r1594393395).
- [eyalfa: weak-set read can mutate](https://github.com/zio/zio/pull/8819#discussion_r1597677573).
- [Final JVM weak-set implementation](https://github.com/zio/zio/blob/6edd4984c1102eefd1edf9e0582c70e69125d0f8/core/jvm/src/main/scala/zio/internal/PlatformSpecific.scala#L108-L112).
- [2019 discussion corrects reachability assumptions](https://github.com/zio/zio/pull/2274#issuecomment-555686706).
- [2019 grandchild interruption regression](https://github.com/zio/zio/blob/e89e3e23d63260930a8685e2a93729e42a8932dc/core-tests/shared/src/test/scala/zio/FiberSpec.scala#L102-L114).
