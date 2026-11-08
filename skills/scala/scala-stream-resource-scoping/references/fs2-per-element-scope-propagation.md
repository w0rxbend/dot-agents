# FS2 (typelevel/fs2): per-element scope propagation across handoffs — originally `scala-fs2-per-element-scope-propagation`

Evidence: [evidence/scala-fs2-per-element-scope-propagation.json](evidence/scala-fs2-per-element-scope-propagation.json),
claim `fs2-claim-scope-boundaries`.

Scope: stream combinator detaches production from consumption via channel, buffer, prefetch or parallel worker
(`parEvalMap`) yet claims to preserve lifetime of emitted resource-backed values; or proposed scope wrapper changes
interruption inheritance for tracing. Test later per-element acquisitions and inherited interruption before accepting
lease-based refactor.

Not for: pure `map`, generic Cats Effect `Resource` cleanup review, or callback dispatcher change with no stream-scope
transfer (protocol ordering and server/consumer ownership: [fs2-foreign-callback-lanes.md](fs2-foreign-callback-lanes.md)).
Do not install rejected `extendScopeThrough` or `noInterruptScope` APIs as repairs. Preserve repository's
effect-polymorphic model; no unrelated direct-style or ZIO rewrite.

## Prerequisites and version fences

Identify actual FS2, Scala, Cats Effect versions, target platform, changed combinator, acquisition/use/release sites.
Read target branch's `Stream`, `Pull`, `internal/Scope` and tests before adapting historical probe.

- #2843 used CE 3.3.6 in 2022.
- #3512's December 2024 proposal uses CE 3.5.7, Scala 2.12.20/2.13.15/3.3.4 and sbt 1.10.5.
- Both proposals closed unmerged. Method visible in their diff is not thereby available in a release.
- `IOLocal` observations are IO-specific; do not add IO requirement to generic interpreter merely to use the example.

## Workflow

1. Draw producer scope, handoff, worker, downstream consumer. Per acquired value, mark final use and finalizer;
   include acquisitions happening only after first pull. Distinguish lifetime through mapping function from lifetime
   through downstream use of its result.
2. Trace `Pull.extendScopeTo` to `Scope.lease` at target SHA. Does it enumerate current resources or register future
   acquisitions? #3512 source enumerates currently reachable resources; its comment warns leasing can miss resources
   already finalizing. Never treat lease as ongoing subscription.
3. Test proposed fix against multiple independent bracket-per-element scopes, not just several brackets nested under
   one outer element. Add delayed consumer so producer can advance. Track each resource separately; single global
   finalized flag can hide which element failed.
4. Test normal exhaustion, downstream early termination, producer failure, cancellation with pending handoff. Require
   each acquired resource released once, no use after its release, bounded shutdown. Do not fix early release by
   retaining all resources until unbounded stream ends.
5. Separately test interruption before, within, after wrapper under different inherited modes. In #2843, explicit
   interruption made one local-state assertion pass but did not restore parent's mode. Compare unchanged stream with
   wrapped stream; do not assume enabled scope is a neutral reset.
6. If no supported repair preserves these properties, report rejected design and missing proof. Useful review can
   reject superficially passing fix without inventing replacement algorithm.

## Review checks

Preserve `acquire(i) < use(i) < release(i)` for each resource actually used, including later acquisitions. Unused
acquired values may be finalized during cancellation; they need not be used first. Preserve error propagation,
exactly-once release, inherited interruption. Check moved finalizer creates no cycle where foreground shutdown waits on
producer waiting on foreground.

Counterexamples from claim: single outer bracket can pass proposed test while bracket-per-element resources opened on
later pulls close too early. Explicitly making traced inner stream interruptible can break parent that intentionally
disabled interruption.

## False positives

- Single fixed outer resource legitimately needs only one lifetime extension.
- Pure transformed value may no longer borrow its source resource. Require actual borrowing/use path before alleging
  premature finalization.
- Do not mistake FS2 stream interruption context for universal Cats Effect masking semantics.
- Pure `Stream` of immutable integers changing its arithmetic mapping, without resource acquisition, asynchronous
  handoff or interruption changes, needs no leases or interruption matrix. Choosing not to alter intentionally
  inherited interruption mode is not a missing cancellation feature.

## Validation

After authorization to execute upstream build code, inspect `build.sbt`, `project/build.properties`, plugins and platform
requirements; run `sbt projects` and `sbt 'show coreJVM / Test / definedTests'`. At pinned #3512 proposal run
`sbt 'coreJVM/testOnly fs2.ParEvalMapSuite'`; at #2843 run `sbt 'coreJVM/testOnly fs2.StreamInterruptSuite'`. Confirm
nonzero discovery and assertions, not just exit status.

Reconstruct #3512's final comment case as new test: six elements, each with own Deferred-backed bracket; delay each
`parEvalMap(2)` use, assert it completes its Deferred before that element's finalizer. Retrieved head suite lacks final
discussion case. Prefer deterministic scheduling/barriers for new regression; timeouts only bound hangs. Add
cancellation probe with per-element release counts. These commands and probes are validation instructions, not tests
executed during research.

## Examples

- Good: reviewer sees channel-based transformation, separately traces second and sixth per-element resources.
  Regression records use before release for every used element, releases unused acquisitions on cancellation, and
  checks stream after tracing wrapper under already noninterruptible parent. Passing original single-resource case is
  supporting, not decisive, evidence.
- Broken and correction: patch peeks once, leases current scope, then feeds every later element into channel. One
  outer-bracket test passes, so patch claims general scope safety. Correction: add repeated independent brackets, delay
  worker consumption; inspect which later resources lease missed. Reject or redesign transfer until each required
  lifetime is covered. Do not present #3512 implementation as the correction: its author withdrew it after precisely
  this counterexample.

## Case-specific output

Invariant per resource, concrete interleaving, regression test; observed historical behavior vs author-reported results vs
inference; whether repair is proposed, compiled, executed or still blocked; finalizer/progress cases not exercised.

## Limitations

Review procedures inferred from rejected designs, not proof current FS2 has same bug. Historical multi-scope result was
reported in discussion, not reproduced here. No upstream Scala compilation or behavioral evaluation performed.
Independent peer must challenge proposed tests and inspect an unused
historical case before acceptance. Formal lead-maintainer roles not established.

## Sources

- [#3512 final counterexample](https://github.com/typelevel/fs2/pull/3512#issuecomment-2564978516), contrasted with
  [the actual lease implementation](https://github.com/typelevel/fs2/blob/cc55983834c90e0fcb5cef6eb9d6f50fa382f64c/core/shared/src/main/scala/fs2/internal/Scope.scala#L451-L478).
- [#2843 inherited-mode correction](https://github.com/typelevel/fs2/pull/2843#discussion_r824022114).
- Further pinned comments (#3512 inadequacy and review, #2843 failure report) and build/test SHAs in evidence file.
