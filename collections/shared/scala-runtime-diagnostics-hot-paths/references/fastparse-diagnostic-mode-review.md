# Fastparse: failure labels, diagnostic modes and trace replay (originally scala-fastparse-diagnostic-mode-review)

Library: com-lihaoyi/fastparse. Evidence: [evidence/scala-fastparse-diagnostic-mode-review.json](evidence/scala-fastparse-diagnostic-mode-review.json) (claims `fp-claim-diagnostic-modes`, `fp-claim-wrapper-terminal-isolation`).

A diagnostic overload can preserve the failure position yet discard its new message. A passing test can encode that same mistake. Review the label producer and its oracle together, while keeping ordinary parsing, verbose parsing and replay separate.

## Scope

Use for a Fastparse custom `Fail` overload, changes to terminal-message reporting, a wrapper parser that hides or negates its child (`opaque`, `unary_!` or a new combinator of that kind), or a refactor of failure tracing. The trigger is a change in diagnostic data flow or mode selection, not every unsuccessful parse.

Not for: generic logging/error handling or unrelated HTTP errors. If the change moves child execution, repetition state or cuts, review it first with the shared-run combinator case in `scala-compiler-macro-refactoring`. If the label contract is unchanged and only the cost of building messages with diagnostics off is in question, use [fastparse-hot-path-cost-review.md](fastparse-hot-path-cost-review.md). A caller asking for tracing after a one-shot input is consumed does not by itself establish a diagnostic regression. This case does not authorize unbounded buffering or replacing Fastparse with an effect system.

## Prerequisites and version fence

Identify Fastparse and Scala versions, the actual `Fail` overload, `Parsed.Failure`/`Extra.trace` and the concrete `ParserInput`. Read the regression test and its callers before trusting its expected string.

The faulty PR 244 head is `749d0c10d9ae3a1e1d8487cc7d45df8024f21547` (2023-03-07). PR 297 corrects both implementation and test in merged commit `49ba3cf46705a5068541537991ce1c2167760a2b` (2023-11-26). Its build declares Scala 3.3.1/3.2.2/2.13.10/2.12.17/2.11.12 and excludes Scala 3 from its Native 0.4.9 matrix. Do not transfer that platform limitation or a release claim to later versions. The 2024 build has a different matrix. The inspected core remains synchronous and uses no CE/ZIO/Ox runtime.

Field names change across revisions: `terminalParserMsgs` (PR 276, `f40fe81`) became `terminalMsgs` (PR 278, `186337a`). Map them on the target revision.

## Workflow

1. **Define the contract independently of the test.** For `Fail(msg)`, write separate expectations: failure rather than success, zero additional input consumption, supplied label when diagnostics are enabled, and the unchanged ordinary-mode policy. Plain `Fail` must retain its default label. An assertion copied from old behavior is not the specification for a new parameter.
2. **Trace the message end to end.** Follow the argument into `freshFailure`, the guarded `reportTerminalMsg`, and formatting/aggregation. In PR 244, the parameter existed but the reporting closure still returned the literal `"fail"`. Check whether the test requests a distinct custom message but also expects `"fail"`.
3. **Keep verbosity owned by the existing context.** PR 244's reviewer challenged an extra default-on verbosity argument. Preserve the target implementation's `ctx.verboseFailures` guard unless changing that policy is explicitly in scope. The review text says `ctx.verboseFailure` (singular); that is the historical quote, not the implementation identifier.
4. **Separate the three observation paths.** Ordinary parsing may omit the label. Verbose parsing reports during that run. `extra.trace()` checks replayability and runs the original parser again with verbose failures and a trace index. It is not a pure getter over the original exception text. Repeated callbacks or nondeterministic parser actions can make replay an unsuitable oracle; use a deterministic reproduction.
5. **Check the input capability before replay.** Indexed string input is replayable in the inspected source; buffered iterator/reader input rejects tracing. For one-shot input, test diagnostics during an appropriate original run rather than silently retaining every chunk or bypassing `checkTraceable()`.
6. **Isolate terminals in hiding/negating wrappers.** The terminal aggregate is normally append-only, so a child's expectations accumulate even when the wrapper is meant to hide them. At PR 276, `unary_!` snapshots `terminalParserMsgs` before its child and restores it under `verboseFailures`; the source comment explains that the negated child's terminals "end up in error messages" otherwise. PR 278 fixed `opaque`, which reported its own label but leaked inner terminals; the fix snapshots `ctx.terminalMsgs` before `parse0()` and restores it under the guard before `reportTerminalMsg(oldIndex, () => msg)`. For a new or refactored wrapper, ask: should the user see the child's terminals? If not, require the snapshot/restore, keep index/success/cut computation outside the guard, and add a deterministic `trace()` test asserting `longAggregateMsg`, `longMsg` and `longTerminalsMsg` separately, as PR 278's `opaqueTerminals` does.
7. **Repair producer and oracle together.** Use the supplied message under the existing guard, preserve the default overload and failure position, and assert a custom label distinct from the default. Then test ordinary, verbose and replay paths separately. Keep a default-label control so the repair cannot accidentally relabel all failures.

Provenance: the historical mode-preservation request is explicit reviewer guidance; the complete test matrix, replay-safety checks and terminal isolation are source-derived inferences (PR 278 had no review or issue comments). PR 297 verifies the source correction, not universal historical CI success or a particular published release.

## Checks

Preserve the invariant that reporting a custom label does not change acceptance, consumed index, cuts, or ordinary-mode policy. Keep the same original parser and starting index when replaying. Do not eagerly render or globally enable traces merely to make one message assertion pass.

Review literal/default label, custom label, position and parse-stack expectations independently. Replacing every failure-string snapshot with new output can hide an unrelated parser-name or aggregation regression.

For a hiding/negating wrapper, also preserve: the wrapper's own label is reported at its start index; child terminals are discarded only under `verboseFailures`; enclosing terminals collected before the wrapper survive the restore.

False positives:

- an empty nonverbose label is expected in the inspected `Parsed.Failure`;
- the buffered-input replay exception is deliberate;
- formatting changes do not automatically imply a grammar bug;
- a transparent wrapper (a named rule, a logging wrapper) should keep child terminals, so do not demand a reset there;
- narrowed downstream `terminals` snapshots are the intended effect when an opaque wrapper is fixed; PR 278 narrowed four ScalaParse expectations — justify each rather than rejecting them.

Conversely, matching index zero alone does not establish custom-label correctness. A merged PR and an added test did not prevent the historical ignored-message defect.

## Distinct diagnostic oracles (folded from the original diagnostic-matrix.md)

Build a minimal deterministic parser around a unique label. Keep its input, starting index and naming stable. Use the exact target-version parser syntax; do not infer current message field names from historical source.

| Input and mode | Expected invariant | Common false conclusion |
|---|---|---|
| String, ordinary parse of custom Fail | Failure at the expected index; no extra consumption | An absent label means the overload is broken |
| String, verbose parse of custom Fail | Same failure position, custom label through the supported message surface | Any failure string, including the default label, proves propagation |
| String, ordinary parse followed by trace | Replay preserves parser/start index, collects custom message at the failure | Trace is only formatting and cannot execute the parser again |
| String, plain Fail control | Default `fail` label when the selected mode collects it | Fixing custom Fail permits changing plain Fail's contract |
| One-shot iterator/reader | Original-run diagnostics where supported; historical replay check remains | Keeping every chunk forever is a harmless formatting repair |

For the known PR 244 defect, inspect both `SharedPackageDefs.scala:164` and `ExampleTests.scala:135` at its head. At the PR 297 merge SHA the corrected test is at line 136; line numbers differ across revisions. Use exact SHA/file references in a historical finding and current `file:line` in a live review.

Suggested mutation check, only in an authorized test checkout: temporarily change the corrected reporting closure back to the default literal. The custom-label oracle must fail while the default-Fail control remains valid. Restore the implementation. This is a proposed test of the oracle, not an operation executed during research.

The historical correction supplies a replay assertion but not proof that every row above was independently tested. PR 297 comments distinguish the focused change from external-repository integration failures; do not relabel author-reported CI retries as locally reproduced success. Relevant evidence IDs: `fp-fail-source-244`, `fp-fail-test-244`, `fp-fail-fix-297`, `fp-fail-test-297`, `fp-trace-2022`, `fp-input-2020`, `fp-fix-validation-297`.

## Validation

Discover the target revision's library build, launcher and test modules. The sampled `build.sbt` is for the documentation site, not the core suite. In a trusted, separately authorized checkout matching the PR 297 build, `./mill -i 'fastparse.jvm[3.3.1].test'` targets a declared core test module; use its Scala 2 cells as appropriate. Confirm `ExampleTests` and the relevant diagnostic cases execute, rather than accepting compilation-only output.

For the later 2024 revision, the observed CI gate is `./mill -i --disable-ticker __.jvm.__.publishArtifacts + __.jvm.__.compile + __.jvm.__.test`; discover narrower selectors from that build before applying them elsewhere. Require the minimal label regression to fail before the correction and pass afterwards when execution is authorized. Exercise the broader failure suite for shared message machinery. Do not claim that a JVM run covers JS or Native.

No upstream build was executed while authoring this case. PR 297's discussion reports intermittent integration-source failures, including failures after merge. If an external grammar checkout blocks a future run, report that separately from the focused label test; do not fabricate a green full suite or repeatedly rerun until only the last success is visible.

## Examples

**Good.** At the PR 297 merge commit, `Fail(msg)` calls `reportTerminalMsg(ctx.index, () => msg)` only under `ctx.verboseFailures`, and plain `Fail` delegates with `"fail"`. The named parser `failWithLabel` fails at index zero on `asdad`; its replay test expects `Expected failWithLabel:1:1 / custom fail msg:1:1, found "asdad"`. This is an observed source/test pair, not an execution result from this research.

**Broken and correction (Fail).** At PR 244 head, `Fail("custom fail msg")` still reports `() => "fail"`, and `ExampleTests` expects the default label. Correction: replace the literal reporting value with `msg` and change that oracle to the requested custom label, while keeping the verbosity guard and zero-consumption failure. PR 297 contains exactly that bounded semantic repair. Add separate default, ordinary and explicit-verbose controls for new work; those additional controls are proposed validation, not all asserted to exist in the historical fix.

**Broken and correction (opaque).** At PR 276 merge `f40fe81`, `opaque` runs `parse0()` and then only calls `reportTerminalMsg(oldIndex, () => msg)` under the guard. It takes no snapshot, so the terminals its hidden child appended stay in the aggregate. PR 278's commit message names this ("manually backtrack any terminals"), and its ScalaParse snapshots narrowed from long alternations of identifier sub-parsers to `(id | "case" | "object")`. Correction: capture the terminal aggregate before `parse0()` and restore it under `verboseFailures` before reporting the wrapper label. The merged `opaqueTerminals` test for `"A".opaque("a") ~/ "B".opaque("b") ~/ End` on `AAB` expects all three trace views to read `Expected Test:1:1 / b:1:2, found "AB"`.

**Negative.** A failure from `IteratorParserInput` rejects `trace()` after consumption. Do not report a missing custom-label fix solely because replay is unavailable, nor remove the capability check. Use fresh input and an appropriate initial diagnostic mode for a supported probe. An ordinary nonverbose string parse with no label likewise does not justify enabling verbose failures globally.

## Case output fields

Each finding: `file:line`, severity, mode/input capability, supplied versus observed label, failure index, evidence ID and source URL, bounded correction, and a discriminating test. Separate the implementation defect from a defective oracle. For no-change verdicts, explain the policy that makes the apparent missing label or replay rejection intentional.

## Limitations

A focused diagnostic contract review, not proof of security hardening, exhaustive aggregation correctness or performance neutrality. The correction's exact merged SHA is established; its first released version is not. Existing ABI guidance still applies if an overload's public signature changes (see `scala-library-compatibility-laws`). Historical maintainer rank is not inferred from current GitHub association. Independent peer exercise and authorized Scala execution remain separate gates.

## Sources

- [Lihaoyi's mode-preservation review](https://github.com/com-lihaoyi/fastparse/pull/244#issuecomment-933432686) and [makkarpov's post-merge counterexample](https://github.com/com-lihaoyi/fastparse/pull/244#issuecomment-1556229773).
- [Faulty producer](https://github.com/com-lihaoyi/fastparse/blob/749d0c10d9ae3a1e1d8487cc7d45df8024f21547/fastparse/src/fastparse/SharedPackageDefs.scala#L162-L166).
- [Corrected producer](https://github.com/com-lihaoyi/fastparse/blob/49ba3cf46705a5068541537991ce1c2167760a2b/fastparse/src/fastparse/SharedPackageDefs.scala#L157-L166) and [corrected test](https://github.com/com-lihaoyi/fastparse/blob/49ba3cf46705a5068541537991ce1c2167760a2b/fastparse/test/src/fastparse/ExampleTests.scala#L130-L136).
- [`unary_!` terminal reset, PR 276](https://github.com/com-lihaoyi/fastparse/blob/f40fe81b485b561587ca06ff64fd4b5fac6f88d6/fastparse/src-2/fastparse/package.scala#L279-L302), [`opaque` fix](https://github.com/com-lihaoyi/fastparse/blob/186337a0b73423b1dc77562979135f8cfbf47e5f/fastparse/src/fastparse/SharedPackageDefs.scala#L230-L245) and [`opaqueTerminals` test, PR 278](https://github.com/com-lihaoyi/fastparse/blob/186337a0b73423b1dc77562979135f8cfbf47e5f/fastparse/test/src/fastparse/ParsingTests.scala#L246-L253).
- [Replay implementation](https://github.com/com-lihaoyi/fastparse/blob/af4b47f25bdf7e85bf6196676db84805fb6e5358/fastparse/src/fastparse/Parsed.scala#L131-L142) and [buffered input restriction](https://github.com/com-lihaoyi/fastparse/blob/dd74612224846d3743e19419b3f1191554b973f5/fastparse/src/fastparse/ParserInput.scala#L185-L189).
- [Evidence and claim subset](evidence/scala-fastparse-diagnostic-mode-review.json), including exact timestamps and original short excerpts.
