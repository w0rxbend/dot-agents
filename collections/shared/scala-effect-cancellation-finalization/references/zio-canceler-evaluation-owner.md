# ZIO: cancel-token evaluation ownership (originally scala-zio-canceler-evaluation-owner)

Evidence: [evidence/scala-zio-canceler-evaluation-owner.json](evidence/scala-zio-canceler-evaluation-owner.json)
(claim `c-canceler-evaluation`).

Review the moment a cancellation action executes, not merely the executor named by its wrapper. Derived from the failed
intermediate fixes and final revision of ZIO PR 6401; PR 8819 provides an important exception to blanket laziness
advice.

## Scope

Unsafe-to-effect cancellation bridges, refactors of strict versus by-name constructors around blocking cancellation,
small-compute-pool shutdown hangs. Follow the complete path from the public effect to the foreign cancel token and its
completion callback. A cleanup fix that changes an unrelated logger assertion also triggers this investigation.

Not a ZIO service, Scope or resource-management tutorial; ordinary scoped finalizers without a foreign cancel-token
bridge belong to existing ZIO guidance. Do not migrate a ZIO/sbt implementation to Ox, Mill or another effect model.

## Version and source boundaries

Record checkout SHA, effect-library version/branch, Scala compiler, JDK, platform and test project. Read constructor
definitions rather than assuming similar names have the same strictness.

Main evidence: `60d47847d8a13694a78e45aedf289ed27eb6ef42` on `series/2.x`, March 2022 — a ZIO 2 RC-era development
state, not a released version inferred from the date. It uses `Runtime.run`, `IO.asyncInterrupt`, `ZTraceElement` and
`succeedBlocking`. sbt 1.6.2; CI Scala matrix 2.11.12 / 2.12.15 / 2.13.8 / 3.1.1; JVM testing on JDK 17 with separate
JDK 8/11 coverage. Late-2022 sources use a different explicit `Unsafe` runtime interface. Rediscover replacements in a
current checkout; do not paste the old bridge into it. March-2022 Native `test` delegates to compilation and cannot
validate cancellation.

## Observed source (pinned)

- [`Runtime.run`](https://github.com/zio/zio/blob/60d47847d8a13694a78e45aedf289ed27eb6ef42/core/shared/src/main/scala/zio/Runtime.scala#L80-L81):
  `val canceler = unsafeRunAsyncCancelable(zio)(exit => callback(ZIO.done(exit)))` then
  `Left(ZIO.succeedBlocking(canceler(fiberId)))` — the cancel token is exposed through `asyncInterrupt`.
- [Unsafe canceler waits](https://github.com/zio/zio/blob/60d47847d8a13694a78e45aedf289ed27eb6ef42/core/shared/src/main/scala/zio/Runtime.scala#L310-L311):
  `canceler(fiberId)(result.set)` then `result.get()` (a `OneShot`). Token invocation, unlike token creation, must not
  block the compute executor needed for finalization.
- [`succeedBlocking`](https://github.com/zio/zio/blob/60d47847d8a13694a78e45aedf289ed27eb6ef42/core/shared/src/main/scala/zio/ZIO.scala#L5217-L5218):
  `def succeedBlocking[A](a: => A)(implicit trace: ZTraceElement): UIO[A] = blocking(ZIO.succeed(a))`. A method name
  containing Blocking alone is not evidence that argument evaluation happens there.
- [`ZIOAppSpec`](https://github.com/zio/zio/blob/60d47847d8a13694a78e45aedf289ed27eb6ef42/core-tests/shared/src/test/scala/zio/ZIOAppSpec.scala#L66-L69):
  `running.await`, `fiber.interrupt`, `ref.get` then `assertTrue(finalized)`. The prior logger assertion remains in the
  same file.
- [Build](https://github.com/zio/zio/blob/60d47847d8a13694a78e45aedf289ed27eb6ef42/build.sbt#L193-L193):
  `lazy val coreTests = crossProject(JSPlatform, JVMPlatform)` — tests are a separate cross-project; `coreTestsJVM` is
  not guessed from the production core module.

## Review history (attributed)

- adamgfraser, [root fix](https://github.com/zio/zio/pull/6401#discussion_r821070309): "a logger was installed, a
  failure occurred, and the logger was not called. I think the underlying problem here is that `run` is not
  propagating…" — rejects accepting the changed logging test as incidental; redirects the fix from ZIOApp into
  `Runtime.run`.
- adamgfraser, [evaluation boundary](https://github.com/zio/zio/pull/6401#issuecomment-1062710624): "The canceler just
  needs to be run on the blocking thread pool but that was not happening because the canceler was being eagerly
  evaluating by `succeedNow` before…" — final source switches the by-name computation to `succeed` inside `blocking`
  without shifting the original effect wholesale.
- davidlar, [reproduction](https://github.com/zio/zio/pull/6401#issuecomment-1062260550): "By adding
  `-XX:ActiveProcessorCount=2`, I can reproduce this locally." Historical testimony, not a run performed here.
- kyri-petrou, [PR 8819](https://github.com/zio/zio/pull/8819#discussion_r1591660374): "Won't `fib.childrenChunk` be
  executed on the fiber that called `asyncZIO`? Should it be changed to `Exit.succeed(fib.childrenChunk)`…" — eager
  evaluation may be correct inside an already-owned state callback. That intermediate design was later superseded for
  diagnostic-progress reasons.

Formal historical maintainer rank is unknown; logins identify observed participants only.

## Workflow

1. **Draw the evaluation path.** Registration, cancel-token creation, invocation, waiting, completion. Annotate which
   steps run during effect construction, which during execution, and which fiber/executor owns each step. In the
   historical source `unsafeRunAsyncCancelable` returns a token whose invocation waits in `OneShot.get`.
2. **Expand wrappers until strictness is visible.** Trace helper arguments, local `val`s, `succeed`/strict constructors
   and `blocking`. A by-name outer parameter is not enough: passing it into a strict inner constructor can evaluate it
   before the executor shift.
3. **Check the underlying cancellation connection.** Does interrupting the returned effect actually invoke the token and
   wait for underlying finalization, or only end the outer observer? PR 6401 changed the bridge to an interruptible
   async registration. Do not repair this solely at the application entrypoint if the reusable runtime bridge is
   responsible.
4. **Preserve independent observations.** Keep the failing-application logger test and the startup-controlled
   finalizer test. The historical attempt to remove nested runtime execution changed logging; review redirected the
   correction into `Runtime.run` rather than accepting the weaker assertion.
5. **Make the smallest ownership correction.** Suspend the blocking cancel invocation until the blocking executor owns
   it. Do not shift the entire original workload merely because doing so hides the hang. Recheck neighboring bridge
   wrappers that use the same constructor.
6. **Challenge the laziness rule.** For an immutable snapshot produced inside an already owner-confined callback,
   delaying the state read can move it onto a foreign fiber. Establish ownership first; choose strictness second.

## Checks

Preserve: the cancellation token is not invoked during construction; external interruption reaches the underlying
computation; interruption completion observes finalization; failure still reaches the configured logger; blocking waits
do not occupy the compute executor needed by cleanup.

Severity: a definite eager blocking invocation before the shift is high severity when it can starve cancellation. An
untraced helper is an investigation gap, not proof of deadlock.

False positives: a token that only schedules nonblocking cancellation; an already-computed immutable value; an eager
state snapshot inside its legitimate owner. A larger compute pool can conceal the problem and is not an equivalence
proof. Do not reject `ensuring` itself: the historical flag-setting test uses it legitimately after the guarded effect
begins.

## Validation

Read `build.sbt`, `project/BuildHelper.scala`, `project/build.properties`, CI and the selected spec before execution.
In an independently authorized checkout with trusted sbt launcher and dependencies:

- `sbt 'coreTestsJVM/testOnly *ZIOAppSpec'`
- `sbt 'coreTestsJVM/test'`

Confirm the selected suite and both logger/finalizer cases actually ran; a successful command with zero tests is
insufficient.

Regression design: receive an explicit startup signal, interrupt and await completion, then check finalization. Keep
logging as a separate failure-path assertion. Repeat with a deliberately small **effective compute executor**, an
independent blocking executor, and an external test deadline/cleanup mechanism. `-XX:ActiveProcessorCount=2` is a
reported reproducer, not a universal executor configuration; inspect test forking and custom executors before applying
it. These are future execution instructions; no Scala build, signal delivery or constrained-executor experiment ran.

## Examples

- **Good.** At the pinned source, the cancel token is returned from async registration inside
  `ZIO.succeedBlocking(canceler(fiberId))`, and `succeedBlocking` implements `blocking(ZIO.succeed(a))`. The action
  stays suspended until the shift. `ZIOAppSpec` waits on `running`, interrupts, and reads the finalizer flag; the hooked
  logger counter remains intact. Observed implementation and test, not an executed result.
- **Broken and correction.** A helper accepts `a: => A` but constructs `blocking(ZIO.succeedNow(a))`. When `a` invokes a
  cancel token that synchronously waits for cleanup, it runs before the blocking shift. Correction in the historical
  API: use the suspended constructor inside `blocking`, retain interruptible registration, rerun finalizer and logger
  regressions on the constrained executor. For a different ZIO version, discover the corresponding APIs first.
- **Negative.** An owner callback reads mutable child state immediately, constructs an immutable result, and returns it
  to a foreign caller. Replacing it with a lazy read is not automatically safer: it can execute on the caller. Do not
  request laziness on this case's authority, and do not endorse PR 8819's rejected message-only design.

## Output

Version/platform and an evaluation-path table; findings with `file:line`, severity, evidence IDs or pinned citations,
violated invariant, minimal correction, and a test with a specific observable oracle. Separate source observation,
reviewer reasoning, inference, tests executed and tests blocked by prerequisites. Report unchanged logging behavior
explicitly; structural skill lint is not race validation.

## Limitations

One substantive bridge repair supplies the central mechanism; PR 8819 is a contrasting ownership review, not an
independent reproduction. The historical methods are not promised to exist in current ZIO.
