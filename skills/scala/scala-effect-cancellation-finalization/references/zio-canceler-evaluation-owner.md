# ZIO: cancel-token evaluation ownership (originally scala-zio-canceler-evaluation-owner)

Evidence: [evidence/scala-zio-canceler-evaluation-owner.json](evidence/scala-zio-canceler-evaluation-owner.json)
(claim `c-canceler-evaluation`).

Review the moment cancellation action executes, not only the executor its wrapper names. PR 8819 gives important
exception to blanket laziness advice.

## Scope

Unsafe-to-effect cancellation bridges, strict versus by-name constructor refactors around blocking cancellation,
small-compute-pool shutdown hangs. Follow complete path from public effect to foreign cancel token and its completion
callback. Cleanup fix that changes unrelated logger assertion also triggers this investigation.

Not ZIO service, Scope or resource-management tutorial; ordinary scoped finalizers without foreign cancel-token bridge
belong to existing ZIO guidance. Do not migrate ZIO/sbt implementation to Ox, Mill or another effect model.

## Version and source boundaries

Record checkout SHA, effect-library version/branch, Scala compiler, JDK, platform, test project. Read constructor
definitions; do not assume similar names share strictness.

Main evidence: `60d47847d8a13694a78e45aedf289ed27eb6ef42` on `series/2.x`, March 2022. ZIO 2 RC-era development state,
not released version inferred from date. Uses `Runtime.run`, `IO.asyncInterrupt`, `ZTraceElement`, `succeedBlocking`.
sbt 1.6.2; CI Scala matrix 2.11.12 / 2.12.15 / 2.13.8 / 3.1.1; JVM testing on JDK 17 with separate JDK 8/11 coverage.
Late-2022 sources use different explicit `Unsafe` runtime interface. Rediscover replacements in current checkout; do
not paste old bridge into it. March-2022 Native `test` delegates to compilation and cannot validate cancellation.

## Observed source (pinned)

- [`Runtime.run`](https://github.com/zio/zio/blob/60d47847d8a13694a78e45aedf289ed27eb6ef42/core/shared/src/main/scala/zio/Runtime.scala#L80-L81):
  `val canceler = unsafeRunAsyncCancelable(zio)(exit => callback(ZIO.done(exit)))` then
  `Left(ZIO.succeedBlocking(canceler(fiberId)))`. Cancel token exposed through `asyncInterrupt`.
- [Unsafe canceler waits](https://github.com/zio/zio/blob/60d47847d8a13694a78e45aedf289ed27eb6ef42/core/shared/src/main/scala/zio/Runtime.scala#L310-L311):
  `canceler(fiberId)(result.set)` then `result.get()` (a `OneShot`). Token invocation, unlike token creation, must not
  block compute executor needed for finalization.
- [`succeedBlocking`](https://github.com/zio/zio/blob/60d47847d8a13694a78e45aedf289ed27eb6ef42/core/shared/src/main/scala/zio/ZIO.scala#L5217-L5218):
  `def succeedBlocking[A](a: => A)(implicit trace: ZTraceElement): UIO[A] = blocking(ZIO.succeed(a))`. Method name
  containing Blocking is not, alone, evidence that argument evaluation happens there.
- [`ZIOAppSpec`](https://github.com/zio/zio/blob/60d47847d8a13694a78e45aedf289ed27eb6ef42/core-tests/shared/src/test/scala/zio/ZIOAppSpec.scala#L66-L69):
  `running.await`, `fiber.interrupt`, `ref.get` then `assertTrue(finalized)`. Prior logger assertion stays in same
  file.
- [Build](https://github.com/zio/zio/blob/60d47847d8a13694a78e45aedf289ed27eb6ef42/build.sbt#L193-L193):
  `lazy val coreTests = crossProject(JSPlatform, JVMPlatform)`. Tests are separate cross-project; do not guess
  `coreTestsJVM` from production core module.

## Review history (attributed)

- adamgfraser, [root fix](https://github.com/zio/zio/pull/6401#discussion_r821070309): "a logger was installed, a
  failure occurred, and the logger was not called. I think the underlying problem here is that `run` is not
  propagating…" — rejects accepting changed logging test as incidental; redirects fix from ZIOApp into
  `Runtime.run`.
- adamgfraser, [evaluation boundary](https://github.com/zio/zio/pull/6401#issuecomment-1062710624): "The canceler just
  needs to be run on the blocking thread pool but that was not happening because the canceler was being eagerly
  evaluating by `succeedNow` before…" — final source switches by-name computation to `succeed` inside `blocking`
  without shifting original effect wholesale.
- davidlar, [reproduction](https://github.com/zio/zio/pull/6401#issuecomment-1062260550): "By adding
  `-XX:ActiveProcessorCount=2`, I can reproduce this locally." Historical testimony, not run performed here.
- kyri-petrou, [PR 8819](https://github.com/zio/zio/pull/8819#discussion_r1591660374): "Won't `fib.childrenChunk` be
  executed on the fiber that called `asyncZIO`? Should it be changed to `Exit.succeed(fib.childrenChunk)`…" — eager
  evaluation may be correct inside already-owned state callback. That intermediate design was later superseded for
  diagnostic-progress reasons.

Formal historical maintainer rank unknown; logins identify observed participants only.

## Workflow

1. **Draw the evaluation path.** Registration, cancel-token creation, invocation, waiting, completion. Annotate which
   steps run during effect construction, which during execution, which fiber/executor owns each step. In historical
   source, `unsafeRunAsyncCancelable` returns token whose invocation waits in `OneShot.get`.
2. **Expand wrappers until strictness is visible.** Trace helper arguments, local `val`s, `succeed`/strict
   constructors, `blocking`. By-name outer parameter is not enough: passing it into strict inner constructor can
   evaluate it before executor shift.
3. **Check the underlying cancellation connection.** Does interrupting returned effect actually invoke token and wait
   for underlying finalization, or only end outer observer? PR 6401 changed bridge to interruptible async
   registration. Do not repair this solely at application entrypoint if reusable runtime bridge is responsible.
4. **Preserve independent observations.** Keep failing-application logger test and startup-controlled finalizer test.
   Historical attempt to remove nested runtime execution changed logging; review redirected correction into
   `Runtime.run` instead of accepting weaker assertion.
5. **Make the smallest ownership correction.** Suspend blocking cancel invocation until blocking executor owns it. Do
   not shift entire original workload merely because that hides hang. Recheck neighboring bridge wrappers using same
   constructor.
6. **Challenge the laziness rule.** For immutable snapshot produced inside already owner-confined callback, delaying
   state read can move it onto foreign fiber. Establish ownership first; choose strictness second.

## Checks

Preserve: cancellation token not invoked during construction; external interruption reaches underlying computation;
interruption completion observes finalization; failure still reaches configured logger; blocking waits do not occupy
compute executor needed by cleanup.

Severity: definite eager blocking invocation before shift is high severity when it can starve cancellation. Untraced
helper is investigation gap, not proof of deadlock.

False positives: token that only schedules nonblocking cancellation; already-computed immutable value; eager state
snapshot inside its legitimate owner. Larger compute pool can conceal problem; not equivalence proof. Do not reject
`ensuring` itself: historical flag-setting test uses it legitimately after guarded effect begins.

## Validation

Before execution, read `build.sbt`, `project/BuildHelper.scala`, `project/build.properties`, CI, selected spec. In
independently authorized checkout with trusted sbt launcher and dependencies:

- `sbt 'coreTestsJVM/testOnly *ZIOAppSpec'`
- `sbt 'coreTestsJVM/test'`

Confirm selected suite and both logger/finalizer cases actually ran; successful command with zero tests is
insufficient.

Regression design: receive explicit startup signal, interrupt and await completion, then check finalization. Keep
logging as separate failure-path assertion. Repeat with deliberately small **effective compute executor**, independent
blocking executor, external test deadline/cleanup mechanism. `-XX:ActiveProcessorCount=2` is reported reproducer, not
universal executor configuration; inspect test forking and custom executors before applying it. These are future
execution instructions; no Scala build, signal delivery or constrained-executor experiment ran.

## Examples

- **Good.** Pinned source: cancel token returned from async registration inside
  `ZIO.succeedBlocking(canceler(fiberId))`, and `succeedBlocking` implements `blocking(ZIO.succeed(a))`. Action stays
  suspended until shift. `ZIOAppSpec` waits on `running`, interrupts, reads finalizer flag; hooked logger counter stays
  intact. Observed implementation and test, not executed result.
- **Broken and correction.** Helper accepts `a: => A` but constructs `blocking(ZIO.succeedNow(a))`. When `a` invokes
  cancel token that synchronously waits for cleanup, it runs before blocking shift. Correction in historical API: use
  suspended constructor inside `blocking`, keep interruptible registration, rerun finalizer and logger regressions on
  constrained executor. For different ZIO version, discover corresponding APIs first.
- **Negative.** Owner callback reads mutable child state immediately, builds immutable result, returns it to foreign
  caller. Replacing it with lazy read is not automatically safer: it can execute on caller. Do not request laziness on
  this case's authority; do not endorse PR 8819's rejected message-only design.

## Output

Version/platform and evaluation-path table; findings with `file:line`, severity, evidence IDs or pinned citations,
violated invariant, minimal correction, test with specific observable oracle. Separate source observation, reviewer
reasoning, inference, tests executed, tests blocked by prerequisites. Report unchanged logging behavior explicitly;
structural skill lint is not race validation.

## Limitations

One substantive bridge repair supplies central mechanism; PR 8819 is contrasting ownership review, not independent
reproduction.
