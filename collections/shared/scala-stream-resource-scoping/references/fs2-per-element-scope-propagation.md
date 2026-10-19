# FS2 (typelevel/fs2): per-element scope propagation across handoffs — originally `scala-fs2-per-element-scope-propagation`

Evidence: [evidence/scala-fs2-per-element-scope-propagation.json](evidence/scala-fs2-per-element-scope-propagation.json),
claim `fs2-claim-scope-boundaries`.

Scope: a stream combinator detaches production from consumption through a channel, buffer, prefetch or parallel worker
(`parEvalMap`) and claims to preserve the lifetime of emitted resource-backed values; or a proposed scope wrapper changes
interruption inheritance to implement tracing. Test later per-element acquisitions and inherited interruption before
accepting a lease-based refactor.

Not for: a pure `map`, a generic Cats Effect `Resource` cleanup review, or a callback dispatcher change with no
stream-scope transfer (see [fs2-foreign-callback-lanes.md](fs2-foreign-callback-lanes.md) for protocol ordering and
server/consumer ownership). Do not install the rejected `extendScopeThrough` or `noInterruptScope` APIs as repairs.
Preserve the repository's effect-polymorphic model, not an unrelated direct-style or ZIO rewrite.

## Prerequisites and version fences

Identify the actual FS2, Scala and Cats Effect versions, target platform, changed combinator and acquisition/use/release
sites. Read the target branch's `Stream`, `Pull`, `internal/Scope` and tests before adapting a historical probe.

- #2843 used CE 3.3.6 in 2022.
- #3512's December 2024 proposal uses CE 3.5.7, Scala 2.12.20/2.13.15/3.3.4 and sbt 1.10.5.
- Both proposals closed unmerged. A method visible in their diff is not thereby available in a release.
- Treat `IOLocal` observations as IO-specific; do not add an IO requirement to a generic interpreter merely to use the
  example.

## Workflow

1. Draw the producer scope, handoff, worker and downstream consumer. For each acquired value, mark its final use and
   finalizer; include an acquisition that happens only after the first pull. Distinguish lifetime through the mapping
   function from lifetime through downstream use of its result.
2. Trace `Pull.extendScopeTo` to `Scope.lease` at the target SHA. Determine whether it enumerates current resources or
   registers future acquisitions. The #3512 source enumerates currently reachable resources; its comment also warns that
   leasing can miss resources already finalizing. Never treat a lease as an ongoing subscription.
3. Compare the proposed fix against multiple independent bracket-per-element scopes, not just several brackets nested
   under one outer element. Add a delayed consumer so the producer can advance. Track each resource separately; a single
   global finalized flag can hide which element failed.
4. Test normal exhaustion, downstream early termination, producer failure and cancellation while a handoff is pending.
   Require each acquired resource to be released once, no use after its release, and bounded shutdown. Do not repair early
   release by retaining all resources until an unbounded stream ends.
5. Separately test interruption before, within and after a wrapper under different inherited modes. In #2843, adding
   explicit interruption made one local-state assertion pass but did not restore the parent's mode. Compare the unchanged
   stream with the wrapped stream rather than assuming an enabled scope is a neutral reset.
6. If no supported repair preserves these properties, report the rejected design and missing proof. A useful review can
   reject a superficially passing fix without inventing a replacement algorithm.

## Review checks

Preserve `acquire(i) < use(i) < release(i)` for each resource actually used, including later acquisitions. Permit unused
acquired values to be finalized during cancellation; they need not be used first. Preserve error propagation,
exactly-once release and inherited interruption. Check that moving a finalizer does not create a cycle where foreground
shutdown waits on a producer waiting on the foreground.

Counterexamples from the claim: a single outer bracket can pass the proposed test while bracket-per-element resources
opened on later pulls close too early. Explicitly making a traced inner stream interruptible can break a parent that
intentionally disabled interruption.

## False positives

- A single fixed outer resource legitimately needs only one lifetime extension.
- A pure transformed value may no longer borrow its source resource. Require an actual borrowing/use path before
  alleging premature finalization.
- Do not mistake FS2 stream interruption context for universal Cats Effect masking semantics.
- A pure `Stream` of immutable integers changing its arithmetic mapping, without resource acquisition, asynchronous
  handoff or interruption changes, needs no leases or interruption matrix. Choosing not to alter an intentionally
  inherited interruption mode is not a missing cancellation feature.

## Validation

After authorization to execute upstream build code, inspect `build.sbt`, `project/build.properties`, plugins and platform
requirements; run `sbt projects` and `sbt 'show coreJVM / Test / definedTests'`. At the pinned #3512 proposal run
`sbt 'coreJVM/testOnly fs2.ParEvalMapSuite'`; at #2843 run `sbt 'coreJVM/testOnly fs2.StreamInterruptSuite'`. Confirm
nonzero discovery and assertions, not just exit status.

Reconstruct #3512's final comment case in a new test: six elements, each with its own Deferred-backed bracket; delay each
`parEvalMap(2)` use and assert it completes its Deferred before that element's finalizer. The final discussion case is
absent from the retrieved head suite. Prefer deterministic scheduling/barriers for a new regression; timeouts only bound
hangs. Add a cancellation probe with per-element release counts. These commands and probes are validation instructions,
not tests executed during research.

## Examples

- Good: a reviewer sees a channel-based transformation and separately traces the second and sixth per-element resources.
  The regression records use before release for every used element and releases unused acquisitions on cancellation. It
  also checks the stream after a tracing wrapper under an already noninterruptible parent. Passing the original
  single-resource case is supporting, not decisive, evidence.
- Broken and correction: a patch peeks once, leases the current scope and then feeds every later element into a channel.
  One outer-bracket test passes, so the patch claims general scope safety. Correction: add repeated independent brackets
  and delay worker consumption; inspect which later resources were absent from the lease. Reject or redesign the transfer
  until each required lifetime is covered. Do not present the #3512 implementation as the correction: its author
  withdrew it after precisely this counterexample.

## Case-specific output

Invariant per resource, concrete interleaving, regression test; observed historical behavior vs author-reported results vs
inference; whether a repair is proposed, compiled, executed or still blocked; finalizer/progress cases not exercised.

## Limitations

These are review procedures inferred from rejected designs, not a proof that current FS2 has the same bug. The historical
multi-scope result was reported in discussion, not reproduced here. No upstream Scala compilation or behavioral
evaluation was performed. An independent peer must challenge the proposed tests and inspect an unused historical case
before acceptance. Participants are attributed to their actual comments; formal lead-maintainer roles are not
established.

## Sources

- [#3512 final counterexample](https://github.com/typelevel/fs2/pull/3512#issuecomment-2564978516), contrasted with
  [the actual lease implementation](https://github.com/typelevel/fs2/blob/cc55983834c90e0fcb5cef6eb9d6f50fa382f64c/core/shared/src/main/scala/fs2/internal/Scope.scala#L451-L478).
- [#2843 inherited-mode correction](https://github.com/typelevel/fs2/pull/2843#discussion_r824022114).
- Further pinned comments (#3512 inadequacy and review, #2843 failure report) and build/test SHAs are in the evidence file.
