---
name: diagnosing-bugs
description: Diagnosis loop for hard bugs and performance regressions - build a tight pass/fail feedback loop first, then reproduce, test falsifiable hypotheses and instrument. Use when the user says "diagnose", or a bug or slowdown resists a quick fix (intermittent, cause not obvious, or a first fix attempt failed); not for an obvious error with a clear one-line fix.
---

# Diagnosing Bugs

Skip phases only when explicitly justified.

When exploring codebase, read `GLOSSARY.md` (if it exists) to model relevant modules. Check ADRs in area you touch.

## Redact

You will show commands, outputs and captured artifacts. **Redact every secret first**: write `<REDACTED>` in its place. Build loops against env vars so credentials stay in environment, out of what you show. Captured artifacts carry auth headers: quote only lines that carry signal.

If redacted output is not enough to diagnose bug, say so and ask user.

## Phase 1: Build a feedback loop

**This is the skill.** Everything else is mechanical. With **tight** pass/fail signal (one that goes red on _this_ bug), you will find cause.

Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.**

### Ways to construct one, in roughly this order

1. **Failing test** at whatever seam reaches bug: unit, integration, e2e.
2. **Curl / HTTP script** against running dev server.
3. **CLI invocation** with fixture input; diff stdout against known-good snapshot.
4. **Headless browser script** (Playwright / Puppeteer) driving UI, asserting on DOM/console/network.
5. **Replay a captured trace.** Save real network request / payload / event log to disk. Replay it through code path in isolation.
6. **Throwaway harness.** Minimal subset of system (one service, mocked deps) exercising bug code path via single function call.
7. **Property / fuzz loop.** Bug is "sometimes wrong output"? Run 1000 random inputs, look for failure mode.
8. **Bisection harness.** Bug appeared between two known states (commit, dataset, version)? Automate "boot at state X, check, repeat" so you can `git bisect run` it.
9. **Differential loop.** Run same input through old-version vs new-version (or two configs); diff outputs.
10. **HITL bash script.** Last resort. Human must click? Drive _them_ with `scripts/hitl-loop.template.sh` so loop stays structured. Captured output feeds back to you.

### Tighten the loop

Treat loop as product. Once you have _a_ loop, **tighten** it:

- Faster: cache setup, skip unrelated init, narrow test scope.
- Sharper signal: assert on specific symptom, not "didn't crash".
- More deterministic: pin time, seed RNG, isolate filesystem, freeze network.

30-second flaky loop barely beats no loop. 2-second deterministic loop is tight: debugging superpower.

### Non-deterministic bugs

Goal is not clean repro but **higher reproduction rate**. Loop trigger 100×, parallelise, add stress, narrow timing windows, inject sleeps. 50%-flake bug is debuggable; 1% is not. Keep raising rate until debuggable.

### When you genuinely cannot build a loop

Stop, say so explicitly, list what you tried. Ask user for: (a) access to environment that reproduces it, (b) redacted captured artifact (HAR file, log dump, core dump, screen recording with timestamps), or (c) permission to add temporary production instrumentation. Do **not** proceed to hypothesise without loop.

### Completion criterion: a tight loop that goes red

Phase 1 done when loop is **tight** and **red-capable**: you can name **one command** (script path, test invocation, curl), **already run at least once** (show invocation and output, redacted), that is:

- [ ] **Red-capable**: drives actual bug code path and asserts **user's exact symptom**, so it can go red on this bug and green once fixed. Not "runs without erroring": must be able to _catch this specific bug_.
- [ ] **Deterministic**: same verdict every run (flaky bugs: pinned, high reproduction rate, per above).
- [ ] **Fast**: seconds, not minutes.
- [ ] **Agent-runnable**: runs unattended; human in loop only via `scripts/hitl-loop.template.sh`.

Catch yourself reading code to build theory before this command exists? **Stop: jumping straight to hypothesis is exact failure this skill prevents.** No red-capable command, no Phase 2.

## Phase 2: Reproduce + minimise

Run loop. Watch it go red as bug appears.

Confirm:

- [ ] Loop produces failure mode **user** described, not different failure that happens to be nearby.
- [ ] Failure reproduces across multiple runs (non-deterministic bugs: at rate high enough to debug against).
- [ ] Exact symptom captured (error message, wrong output, slow timing) so later phases can verify fix addresses it.

### Minimise

Once red, shrink repro to **smallest scenario that still goes red**. Cut inputs, callers, config, data, steps **one at a time**; re-run loop after each cut. Keep only what's load-bearing for failure.

Done when **every remaining element is load-bearing**: removing any one turns loop green.

Do not proceed until reproduced **and** minimised.

## Phase 3: Hypothesise

Generate **3–5 ranked hypotheses** before testing any.

Each hypothesis must be **falsifiable**: state its prediction.

> Format: "If <X> is the cause, then <changing Y> will make the bug disappear / <changing Z> will make it worse."

Cannot state prediction? Hypothesis is a vibe: discard or sharpen it.

**Show ranked list to user before testing.** User often has domain knowledge that re-ranks instantly ("we just deployed a change to #3"), or knows hypotheses already ruled out. Do not block on it: if user is AFK, proceed with your ranking.

## Phase 4: Instrument

Each probe must map to specific Phase 3 prediction. **Change one variable at a time.**

Tool preference:

1. **Debugger / REPL inspection** if env supports it. One breakpoint beats ten logs.
2. **Targeted logs** at boundaries that distinguish hypotheses.
3. Never "log everything and grep".

**Tag every debug log** with unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup at end becomes single grep.

**Perf branch.** For performance regressions, logs are usually wrong. Instead: establish baseline measurement (timing harness, `performance.now()`, profiler, query plan), then bisect. Measure first, fix second.

## Phase 5: Fix + regression test

Write regression test **before fix**, but only if **correct seam** exists for it.

Correct seam: test exercises **real bug pattern** as it occurs at call site. If only available seam is too shallow (single-caller test when bug needs multiple callers, unit test that can't replicate triggering chain), regression test there gives false confidence.

**If no correct seam exists, that itself is the finding.** Note it: codebase architecture prevents locking bug down. Flag it for next phase.

If correct seam exists:

1. Turn minimised repro into failing test at that seam.
2. Watch it fail. Forced red by mutating code or fixture? `diff` against pristine copy to prove mutation landed before trusting it.
3. Apply fix.
4. Watch it pass.
5. Re-run Phase 1 feedback loop against original (un-minimised) scenario.

## Phase 6: Cleanup

Required before declaring done:

- [ ] Original repro no longer reproduces (re-run Phase 1 loop)
- [ ] Regression test passes (or missing seam documented)
- [ ] All `[DEBUG-...]` instrumentation removed (`grep` the prefix)
- [ ] Throwaway prototypes deleted (or moved to clearly-marked debug location)
- [ ] Correct hypothesis stated in commit / PR message, so next debugger learns
