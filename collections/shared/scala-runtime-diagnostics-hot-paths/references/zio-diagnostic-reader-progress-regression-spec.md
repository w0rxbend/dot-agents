# ZIO blocked-reader regression specification (folded from scala-zio-diagnostic-reader-progress references/regression-spec.md)

Companion to [zio-diagnostic-reader-progress.md](zio-diagnostic-reader-progress.md).

This is an original test specification for review and future implementation, not historical source, compiled Scala, or a report of successful execution. Pin the source under review to `6edd4984c1102eefd1edf9e0582c70e69125d0f8` before comparing the observed direct-read implementation with a proposed message-only mutation. Read [evidence](evidence/scala-zio-diagnostic-reader-progress.json) first.

## Source map

- `core/shared/src/main/scala/zio/Fiber.scala`: `dumpAllWith` recursively invokes `fiber.children` (lines 851–855).
- `core/shared/src/main/scala/zio/internal/FiberRuntime.scala`: `childrenChunk` snapshots a locally captured child-set reference (lines 90–105); `getChildren` creates the concurrent weak set (lines 526–531); `transferChildren` can replace the reference with null (lines 1433–1441).
- `core/jvm/src/main/scala/zio/internal/PlatformSpecific.scala`: concurrent weak-set construction wraps the weak collection (lines 108–112).
- `core-tests/shared/src/test/scala/zio/FiberSpec.scala`: roots and interruption tests are neighboring regression conventions, not blocked-reader tests.

## Positive mutation: mailbox observation

Replace only the direct child observation with a request whose callback runs on the subject fiber. Keep writes owner-confined and retain the subject's children. The mutation is a textual review fixture; do not silently apply it to a user's checkout.

1. Use a dedicated subject executor and an independent observer executor, both owned by the test harness. Keep an external watchdog capable of unblocking the subject; do not schedule teardown on the deliberately blocked executor.
2. Have the subject spawn a live child and publish its identity to the harness. Establish that the child is registered before the blocking phase. Hold a strong reference to the child so GC does not make this a weak-reference timing test.
3. Block the subject inside a controlled synchronous gate in its run loop, not on `Promise.await` or `ZIO.never`. Publish entry into that gate. This intentionally models the review concern; it is not recommended application code. No real remote I/O is required.
4. After observing gate entry, request `subject.children` from the independent observer. Keep the subject's gate closed. Record the completion event and returned child IDs.
5. Require observation to complete before the external deadline and before the gate-release event, with the already-established live child visible in this stable schedule. A timeout is a failed observation, not a reason to wait for the subject to recover and then pass the test.
6. In all outcomes, release the gate from the independent harness before awaiting interruption/termination. Clean up subject, child, observer and executors. This order prevents the test harness from hanging while trying to interrupt an unresponsive subject.

The direct implementation is predicted to avoid the subject-message dependency. The mutation is predicted not to complete before gate release. These are falsifiable predictions, not measured results. A timeout could also reflect unrelated executor starvation; record actual executor identities and gate-entry evidence before attributing it.

## Repair and whole-dump variant

Restore independently readable, safely synchronized child state, or supply an alternative access-path and publication argument. Repeat the same schedule. Then exercise whole-dump traversal separately, with root tracking enabled, an inert nonblocking dump consumer, and a finite controlled fiber tree. Do not interpret a callback that blocks on output as a child-set regression. Do not assert a global instantaneous tree snapshot while concurrent transfers are allowed.

## Independent reachability regression

At `e89e3e23d63260930a8685e2a93729e42a8932dc`, PR 2274 tests grandparent interruption reaching a grandchild. Its latch precedes parent fork/completion, so repetition does not force the alleged parent-terminated interleaving. A stronger new oracle would explicitly acknowledge C's startup and B's completion/transfer before inspecting from A and interrupting A. Compare the permitted ownership policy at the target ZIO major first. This stronger schedule is our proposal, not a claim about the historical test.

## Negative control

Use an immutable snapshot already published to the observer, with no callback to the subject and no live mutable collection escaping. It should be read without waiting for the subject. Do not require locking a value whose construction and publication proof already satisfies the contract.
