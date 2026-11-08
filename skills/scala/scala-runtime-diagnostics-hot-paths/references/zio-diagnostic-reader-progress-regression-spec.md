# ZIO blocked-reader regression specification (folded from scala-zio-diagnostic-reader-progress references/regression-spec.md)

Companion to [zio-diagnostic-reader-progress.md](zio-diagnostic-reader-progress.md).

Original test specification for review and future implementation; not historical source, compiled Scala, or report of successful execution. Pin source under review to `6edd4984c1102eefd1edf9e0582c70e69125d0f8` before comparing observed direct-read implementation with proposed message-only mutation. Read [evidence](evidence/scala-zio-diagnostic-reader-progress.json) first.

## Source map

- `core/shared/src/main/scala/zio/Fiber.scala`: `dumpAllWith` recursively invokes `fiber.children` (lines 851–855).
- `core/shared/src/main/scala/zio/internal/FiberRuntime.scala`: `childrenChunk` snapshots locally captured child-set reference (lines 90–105); `getChildren` creates concurrent weak set (lines 526–531); `transferChildren` can replace reference with null (lines 1433–1441).
- `core/jvm/src/main/scala/zio/internal/PlatformSpecific.scala`: concurrent weak-set construction wraps weak collection (lines 108–112).
- `core-tests/shared/src/test/scala/zio/FiberSpec.scala`: roots and interruption tests are neighboring regression conventions, not blocked-reader tests.

## Positive mutation: mailbox observation

Replace only direct child observation with request whose callback runs on subject fiber. Writes stay owner-confined; subject keeps its children. Mutation is textual review fixture; do not silently apply it to user's checkout.

1. Use dedicated subject executor and independent observer executor, both owned by test harness. Keep external watchdog able to unblock subject; do not schedule teardown on deliberately blocked executor.
2. Subject spawns live child and publishes its identity to harness. Establish child is registered before blocking phase. Hold strong reference to child so GC does not make this weak-reference timing test.
3. Block subject inside controlled synchronous gate in its run loop, not on `Promise.await` or `ZIO.never`. Publish gate entry. Deliberately models review concern; not recommended application code. No real remote I/O required.
4. After observing gate entry, request `subject.children` from independent observer. Keep subject's gate closed. Record completion event and returned child IDs.
5. Require observation to complete before external deadline and before gate-release event, with already-established live child visible in this stable schedule. Timeout is failed observation, not reason to wait for subject to recover and then pass test.
6. In all outcomes, release gate from independent harness before awaiting interruption/termination. Clean up subject, child, observer, executors. This order keeps harness from hanging while trying to interrupt unresponsive subject.

Predictions: direct implementation avoids subject-message dependency; mutation does not complete before gate release. Falsifiable predictions, not measured results. Timeout could also reflect unrelated executor starvation; record actual executor identities and gate-entry evidence before attributing it.

## Repair and whole-dump variant

Restore independently readable, safely synchronized child state, or supply alternative access-path and publication argument. Repeat same schedule. Then exercise whole-dump traversal separately: root tracking enabled, inert nonblocking dump consumer, finite controlled fiber tree. Do not read callback blocking on output as child-set regression. Do not assert global instantaneous tree snapshot while concurrent transfers are allowed.

## Independent reachability regression

At `e89e3e23d63260930a8685e2a93729e42a8932dc`, PR 2274 tests grandparent interruption reaching grandchild. Its latch precedes parent fork/completion, so repetition does not force alleged parent-terminated interleaving. Stronger new oracle: explicitly acknowledge C's startup and B's completion/transfer before inspecting from A and interrupting A. First compare permitted ownership policy at target ZIO major. Stronger schedule is our proposal, not claim about historical test.

## Negative control

Use immutable snapshot already published to observer: no callback to subject, no live mutable collection escaping. Should be read without waiting for subject. Do not require locking value whose construction and publication proof already satisfies contract.
