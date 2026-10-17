---
name: scala-zio-canceler-evaluation-owner
description: Use when refactoring ZIO cancel-token bridges. Trace strict effect construction and executor shifts without losing cancellation, finalization, or logging behavior.
license: MIT
---

# ZIO cancel-token evaluation ownership

Review the moment a cancellation action executes, not merely the executor named by its wrapper. This procedure comes from the failed intermediate fixes and final revision of ZIO PR 6401, with PR 8819 providing an important exception to blanket laziness advice.

## When to Use

Use for an unsafe-to-effect cancellation bridge, a refactor of a strict versus by-name constructor around blocking cancellation, or a small-compute-pool shutdown hang. Follow the complete path from the public effect to the foreign cancel token and its completion callback. A cleanup fix that changes an unrelated logger assertion also triggers this investigation.

## When Not to Use

Do not use this as a general ZIO service, Scope, or resource-management tutorial. Ordinary scoped finalizers without a foreign cancel-token bridge belong to existing ZIO guidance. Cats Effect outcome selection, Kafka callback-thread restrictions, and FS2 acquisition scopes are separate mechanisms. Do not migrate an existing ZIO/sbt implementation to Ox, Mill, or another effect model.

## Prerequisites

Record the checkout SHA, effect-library version/branch, Scala compiler, JDK, platform, and test project. Read the constructor definitions rather than assuming that similar names have the same strictness.

The main evidence is `60d47847d8a13694a78e45aedf289ed27eb6ef42` on `series/2.x`, March 2022: a ZIO 2 RC-era development state, not a released version inferred from the date. It uses `Runtime.run`, `IO.asyncInterrupt`, `ZTraceElement`, and `succeedBlocking`. Its sbt pin is 1.6.2; the CI Scala matrix is 2.11.12 / 2.12.15 / 2.13.8 / 3.1.1, with JVM testing on JDK 17 and separate JDK 8/11 coverage. Late-2022 sources use a different explicit `Unsafe` runtime interface. Rediscover replacements in a current checkout; do not paste the old bridge into it.

## Workflow

1. **Draw the evaluation path.** Record registration, cancel-token creation, invocation, waiting, and completion. Annotate which steps run during effect construction, which during execution, and which fiber/executor owns each step. In the historical source, `unsafeRunAsyncCancelable` returns a token whose invocation waits in `OneShot.get`; token creation and invocation are not interchangeable.
2. **Expand wrappers until strictness is visible.** Trace helper arguments, local `val`s, `succeed`/strict constructors, and `blocking`. A by-name outer parameter is not enough: passing it into a strict inner constructor can evaluate it before the executor shift.
3. **Check the underlying cancellation connection.** Does interrupting the returned effect actually invoke the token and wait for underlying finalization, or only end the outer observer? PR 6401 changed the bridge to an interruptible async registration. Do not repair this solely at the application entrypoint if the reusable runtime bridge is responsible.
4. **Preserve independent observations.** Keep the existing failing-application logger test and the startup-controlled finalizer test. The historical attempt to remove nested runtime execution changed logging; review redirected the correction into `Runtime.run` rather than accepting the weaker assertion.
5. **Make the smallest ownership correction.** Suspend the blocking cancel invocation until the blocking executor owns it. Do not shift the entire original workload merely because doing so hides the hang. Recheck neighboring bridge wrappers that use the same constructor.
6. **Challenge the laziness rule.** For an immutable snapshot produced inside an already owner-confined callback, delaying the state read can move it onto a foreign fiber. Establish ownership first; choose strictness second. PR 8819's callback proposal raised this concern but was later superseded for diagnostic-progress reasons.

## Review and Refactoring Checks

Preserve these invariants: the cancellation token is not invoked during construction; external interruption reaches the underlying computation; interruption completion observes finalization; failure still reaches the configured logger; blocking waits do not occupy the compute executor needed by cleanup.

Flag a definite eager blocking invocation before the shift as high severity when it can starve cancellation. Treat an untraced helper as an investigation gap, not proof of deadlock. False positives include a token that only schedules nonblocking cancellation, an already-computed immutable value, and an eager state snapshot inside its legitimate owner. A larger compute pool can conceal the problem and is not an equivalence proof. Do not reject `ensuring` itself: the historical flag-setting test uses it legitimately after the guarded effect begins.

## Validation

Read `build.sbt`, `project/BuildHelper.scala`, `project/build.properties`, CI, and the selected spec before execution. The pinned build places tests in `coreTestsJVM`, separately from production core, and documents the ZIO Test `testOnly` selector. In an independently authorized checkout with trusted sbt launcher and dependencies, run `sbt 'coreTestsJVM/testOnly *ZIOAppSpec'`, then `sbt 'coreTestsJVM/test'`. Confirm the selected suite and both logger/finalizer cases actually ran; a successful command with zero tests is insufficient.

Add a regression that first receives an explicit startup signal, then interrupts and awaits completion, then checks finalization. Keep logging as a separate failure-path assertion. Repeat with a deliberately small **effective compute executor**, an independent blocking executor, and an external test deadline/cleanup mechanism. PR 6401 reports `-XX:ActiveProcessorCount=2` as a reproducer, not a universal executor configuration. Inspect test forking and custom executors before choosing how to apply it.

These are future execution instructions, not results from this research. March-2022 Native `test` delegates to compilation; it cannot validate cancellation. See [evidence](references/evidence.json).

## Examples

### Good

At the pinned March-2022 source, the cancel token is returned from async registration inside `ZIO.succeedBlocking(canceler(fiberId))`, and `succeedBlocking` implements `blocking(ZIO.succeed(a))`. The action remains suspended until the shift. `ZIOAppSpec` waits on `running`, interrupts, and reads the finalizer flag; its existing hooked-logger counter remains intact. This is an observed implementation and test, not an executed result here.

### Broken and Correction

A helper accepts `a: => A` but constructs `blocking(ZIO.succeedNow(a))`. When `a` invokes a cancel token that synchronously waits for cleanup, it runs before the blocking shift. Correction in the historical API: use the suspended constructor inside `blocking`, retain interruptible registration, and rerun the finalizer and logger regressions on the constrained executor. For a different ZIO version, discover the corresponding APIs first rather than mechanically renaming them.

### Negative

An owner callback reads mutable child state immediately, constructs an immutable result, and returns that result to a foreign caller. Replacing it with a lazy state read is not automatically safer: it can execute on the caller. Do not request laziness on this skill's authority. Separately review whether the callback protocol itself prevents diagnostics from observing a blocked subject; this skill does not endorse PR 8819's rejected message-only design.

## Output Contract

Return the version/platform and an evaluation-path table, followed by findings containing `file:line`, severity, evidence IDs or pinned citations, the violated invariant, a minimal correction, and a test with a specific observable oracle. Separate source observation, reviewer reasoning, your inference, tests actually executed, and tests blocked by prerequisites. Report unchanged logging behavior explicitly; do not count structural skill lint as race validation.

## Limitations

One substantive bridge repair supplies the central mechanism; PR 8819 is a contrasting ownership review, not an independent reproduction of the same bug. No Scala build, signal delivery, or constrained-executor experiment was run while authoring. Formal historical maintainer rank is unknown; logins identify observed participants only. The selected historical methods are not promised to exist in current ZIO.

## Sources

- [Evidence and claim mappings](references/evidence.json), primarily `c-canceler-evaluation`.
- [adamgfraser: fix the runtime bridge without losing logging](https://github.com/zio/zio/pull/6401#discussion_r821070309).
- [adamgfraser: strict evaluation occurred before the shift](https://github.com/zio/zio/pull/6401#issuecomment-1062710624).
- [Final constructor implementation](https://github.com/zio/zio/blob/60d47847d8a13694a78e45aedf289ed27eb6ef42/core/shared/src/main/scala/zio/ZIO.scala#L5217-L5218).
- [kyri-petrou: lazy snapshot may execute on the caller](https://github.com/zio/zio/pull/8819#discussion_r1591660374).
