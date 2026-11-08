# Fastparse: failure labels, diagnostic modes and trace replay (originally scala-fastparse-diagnostic-mode-review)

Library: com-lihaoyi/fastparse. Evidence: [evidence/scala-fastparse-diagnostic-mode-review.json](evidence/scala-fastparse-diagnostic-mode-review.json) (claims `fp-claim-diagnostic-modes`, `fp-claim-wrapper-terminal-isolation`).

## Scope

Use for Fastparse custom `Fail` overload, terminal-message reporting changes, wrapper parser hiding or negating its child (`opaque`, `unary_!` or similar new combinator), or failure-tracing refactor. Trigger: change in diagnostic data flow or mode selection, not every unsuccessful parse.

Not for: generic logging/error handling or unrelated HTTP errors. If change moves child execution, repetition state or cuts, review first with shared-run combinator case in `scala-compiler-macro-refactoring`. If label contract is unchanged and only diagnostics-off message-building cost is in question, use [fastparse-hot-path-cost-review.md](fastparse-hot-path-cost-review.md). Caller wanting tracing after one-shot input is consumed does not alone establish diagnostic regression. Does not authorize unbounded buffering or replacing Fastparse with effect system.

## Prerequisites and version fence

Identify Fastparse and Scala versions, actual `Fail` overload, `Parsed.Failure`/`Extra.trace`, concrete `ParserInput`. Read regression test and its callers before trusting its expected string.

Faulty PR 244 head: `749d0c10d9ae3a1e1d8487cc7d45df8024f21547` (2023-03-07). PR 297 corrects implementation and test in merged commit `49ba3cf46705a5068541537991ce1c2167760a2b` (2023-11-26). Its build declares Scala 3.3.1/3.2.2/2.13.10/2.12.17/2.11.12 and excludes Scala 3 from its Native 0.4.9 matrix. Do not carry that platform limitation or release claim to later versions; 2024 build has different matrix. Inspected core is synchronous, uses no CE/ZIO/Ox runtime.

Field names change across revisions: `terminalParserMsgs` (PR 276, `f40fe81`) became `terminalMsgs` (PR 278, `186337a`). Map them on target revision.

## Workflow

1. **Define the contract independently of the test.** For `Fail(msg)`, write separate expectations: failure, not success; zero extra input consumption; supplied label when diagnostics enabled; unchanged ordinary-mode policy. Plain `Fail` must keep default label. Assertion copied from old behavior does not specify new parameter.
2. **Trace the message end to end.** Follow argument through `freshFailure`, guarded `reportTerminalMsg`, formatting/aggregation. PR 244 had the parameter, but reporting closure still returned literal `"fail"`. Check for test requesting distinct custom message yet expecting `"fail"`.
3. **Keep verbosity owned by the existing context.** PR 244's reviewer challenged extra default-on verbosity argument. Keep target's `ctx.verboseFailures` guard unless changing that policy is explicitly in scope. Review text says `ctx.verboseFailure` (singular): historical quote, not implementation identifier.
4. **Separate the three observation paths.** Ordinary parsing may omit label. Verbose parsing reports during that run. `extra.trace()` checks replayability, then reruns original parser with verbose failures and trace index; not a pure getter over original exception text. Repeated callbacks or nondeterministic parser actions can make replay unsuitable oracle; use deterministic reproduction.
5. **Check the input capability before replay.** In inspected source, indexed string input replays; buffered iterator/reader input rejects tracing. For one-shot input, test diagnostics during suitable original run. Do not silently retain every chunk or bypass `checkTraceable()`.
6. **Isolate terminals in hiding/negating wrappers.** Terminal aggregate is normally append-only: child expectations accumulate even when wrapper should hide them. At PR 276, `unary_!` snapshots `terminalParserMsgs` before child, restores it under `verboseFailures`; source comment says negated child's terminals otherwise "end up in error messages". PR 278 fixed `opaque`, which reported own label but leaked inner terminals: fix snapshots `ctx.terminalMsgs` before `parse0()`, restores under guard before `reportTerminalMsg(oldIndex, () => msg)`. For new or refactored wrapper, ask: should user see child's terminals? If not: require snapshot/restore, keep index/success/cut computation outside guard, add deterministic `trace()` test asserting `longAggregateMsg`, `longMsg` and `longTerminalsMsg` separately (as PR 278's `opaqueTerminals` does).
7. **Repair producer and oracle together.** Use supplied message under existing guard; keep default overload and failure position; assert custom label distinct from default. Then test ordinary, verbose, replay paths separately. Keep default-label control so repair cannot accidentally relabel all failures.

Provenance: mode-preservation request is explicit historical reviewer guidance. Full test matrix, replay-safety checks, terminal isolation: source-derived inferences (PR 278 had no review or issue comments). PR 297 verifies source correction, not universal historical CI success or specific published release.

## Checks

Invariant: reporting custom label leaves acceptance, consumed index, cuts and ordinary-mode policy unchanged. Replay with same original parser and starting index. Do not eagerly render or globally enable traces merely to pass one message assertion.

Review literal/default label, custom label, position, parse-stack expectations independently. Replacing every failure-string snapshot with new output can hide unrelated parser-name or aggregation regression.

For hiding/negating wrapper, also preserve: own label reported at its start index; child terminals discarded only under `verboseFailures`; enclosing terminals collected before wrapper survive restore.

False positives:

- empty nonverbose label is expected in inspected `Parsed.Failure`;
- buffered-input replay exception is deliberate;
- formatting changes do not automatically imply grammar bug;
- transparent wrapper (named rule, logging wrapper) should keep child terminals; do not demand reset there;
- narrowed downstream `terminals` snapshots are intended effect of opaque-wrapper fix. PR 278 narrowed four ScalaParse expectations; justify each, do not reject them.

Conversely, matching index zero alone does not establish custom-label correctness. Merged PR plus added test did not prevent historical ignored-message defect.

## Distinct diagnostic oracles (folded from the original diagnostic-matrix.md)

Build minimal deterministic parser around unique label; keep input, starting index and naming stable. Use exact target-version parser syntax; do not infer current message field names from historical source.

| Input and mode | Expected invariant | Common false conclusion |
|---|---|---|
| String, ordinary parse of custom Fail | Failure at expected index; no extra consumption | Absent label means overload is broken |
| String, verbose parse of custom Fail | Same failure position, custom label through supported message surface | Any failure string, including default label, proves propagation |
| String, ordinary parse followed by trace | Replay preserves parser/start index, collects custom message at failure | Trace is only formatting, cannot execute parser again |
| String, plain Fail control | Default `fail` label when selected mode collects it | Fixing custom Fail permits changing plain Fail's contract |
| One-shot iterator/reader | Original-run diagnostics where supported; historical replay check remains | Keeping every chunk forever is harmless formatting repair |

For known PR 244 defect, inspect `SharedPackageDefs.scala:164` and `ExampleTests.scala:135` at its head. At PR 297 merge SHA, corrected test is at line 136; line numbers differ across revisions. Historical finding: exact SHA/file references. Live review: current `file:line`.

Suggested mutation check, only in authorized test checkout: temporarily revert corrected reporting closure to default literal. Custom-label oracle must fail while default-Fail control stays valid. Restore implementation. Proposed oracle test, not operation executed during research.

Historical correction supplies replay assertion, not proof each row above was independently tested. PR 297 comments separate focused change from external-repository integration failures; do not relabel author-reported CI retries as locally reproduced success. Relevant evidence IDs: `fp-fail-source-244`, `fp-fail-test-244`, `fp-fail-fix-297`, `fp-fail-test-297`, `fp-trace-2022`, `fp-input-2020`, `fp-fix-validation-297`.

## Validation

Discover target revision's library build, launcher, test modules. Sampled `build.sbt` is for documentation site, not core suite. In trusted, separately authorized checkout matching PR 297 build, `./mill -i 'fastparse.jvm[3.3.1].test'` targets declared core test module; use its Scala 2 cells as appropriate. Confirm `ExampleTests` and relevant diagnostic cases execute; do not accept compilation-only output.

For later 2024 revision, observed CI gate is `./mill -i --disable-ticker __.jvm.__.publishArtifacts + __.jvm.__.compile + __.jvm.__.test`. Discover narrower selectors from that build before applying them elsewhere. When execution is authorized, minimal label regression must fail before correction and pass after. Exercise broader failure suite for shared message machinery. Do not claim JVM run covers JS or Native.

No upstream build executed while authoring this case. PR 297 discussion reports intermittent integration-source failures, including after merge. If external grammar checkout blocks future run, report it apart from focused label test. Do not fabricate green full suite or rerun repeatedly until only last success is visible.

## Examples

**Good.** At PR 297 merge commit, `Fail(msg)` calls `reportTerminalMsg(ctx.index, () => msg)` only under `ctx.verboseFailures`; plain `Fail` delegates with `"fail"`. Named parser `failWithLabel` fails at index zero on `asdad`; its replay test expects `Expected failWithLabel:1:1 / custom fail msg:1:1, found "asdad"`. Observed source/test pair, not execution result from this research.

**Broken and correction (Fail).** At PR 244 head, `Fail("custom fail msg")` still reports `() => "fail"`; `ExampleTests` expects default label. Correction: replace literal reporting value with `msg`, change that oracle to requested custom label, keep verbosity guard and zero-consumption failure. PR 297 contains exactly that bounded semantic repair. For new work, add separate default, ordinary and explicit-verbose controls. Those extras are proposed validation, not all asserted to exist in historical fix.

**Broken and correction (opaque).** At PR 276 merge `f40fe81`, `opaque` runs `parse0()`, then only calls `reportTerminalMsg(oldIndex, () => msg)` under guard. No snapshot, so terminals appended by hidden child stay in aggregate. PR 278's commit message names this ("manually backtrack any terminals"); its ScalaParse snapshots narrowed from long alternations of identifier sub-parsers to `(id | "case" | "object")`. Correction: capture terminal aggregate before `parse0()`, restore it under `verboseFailures` before reporting wrapper label. Merged `opaqueTerminals` test for `"A".opaque("a") ~/ "B".opaque("b") ~/ End` on `AAB` expects all three trace views to read `Expected Test:1:1 / b:1:2, found "AB"`.

**Negative.** Failure from `IteratorParserInput` rejects `trace()` after consumption. Do not report missing custom-label fix solely because replay is unavailable; do not remove capability check. For supported probe, use fresh input and suitable initial diagnostic mode.

## Case output fields

Each finding: `file:line`, severity, mode/input capability, supplied versus observed label, failure index, evidence ID and source URL, bounded correction, discriminating test. Separate implementation defect from defective oracle. For no-change verdict, explain policy making apparent missing label or replay rejection intentional.

## Limitations

Focused diagnostic contract review; not proof of security hardening, exhaustive aggregation correctness or performance neutrality. Correction's exact merged SHA is established; its first released version is not. Existing ABI guidance still applies if overload's public signature changes (see `scala-library-compatibility-laws`). Historical maintainer rank not inferred from current GitHub association. Independent peer exercise and authorized Scala execution remain separate gates.

## Sources

- [Lihaoyi's mode-preservation review](https://github.com/com-lihaoyi/fastparse/pull/244#issuecomment-933432686) and [makkarpov's post-merge counterexample](https://github.com/com-lihaoyi/fastparse/pull/244#issuecomment-1556229773).
- [Faulty producer](https://github.com/com-lihaoyi/fastparse/blob/749d0c10d9ae3a1e1d8487cc7d45df8024f21547/fastparse/src/fastparse/SharedPackageDefs.scala#L162-L166).
- [Corrected producer](https://github.com/com-lihaoyi/fastparse/blob/49ba3cf46705a5068541537991ce1c2167760a2b/fastparse/src/fastparse/SharedPackageDefs.scala#L157-L166) and [corrected test](https://github.com/com-lihaoyi/fastparse/blob/49ba3cf46705a5068541537991ce1c2167760a2b/fastparse/test/src/fastparse/ExampleTests.scala#L130-L136).
- [`unary_!` terminal reset, PR 276](https://github.com/com-lihaoyi/fastparse/blob/f40fe81b485b561587ca06ff64fd4b5fac6f88d6/fastparse/src-2/fastparse/package.scala#L279-L302), [`opaque` fix](https://github.com/com-lihaoyi/fastparse/blob/186337a0b73423b1dc77562979135f8cfbf47e5f/fastparse/src/fastparse/SharedPackageDefs.scala#L230-L245) and [`opaqueTerminals` test, PR 278](https://github.com/com-lihaoyi/fastparse/blob/186337a0b73423b1dc77562979135f8cfbf47e5f/fastparse/test/src/fastparse/ParsingTests.scala#L246-L253).
- [Replay implementation](https://github.com/com-lihaoyi/fastparse/blob/af4b47f25bdf7e85bf6196676db84805fb6e5358/fastparse/src/fastparse/Parsed.scala#L131-L142) and [buffered input restriction](https://github.com/com-lihaoyi/fastparse/blob/dd74612224846d3743e19419b3f1191554b973f5/fastparse/src/fastparse/ParserInput.scala#L185-L189).
- [Evidence and claim subset](evidence/scala-fastparse-diagnostic-mode-review.json), with exact timestamps and original short excerpts.
