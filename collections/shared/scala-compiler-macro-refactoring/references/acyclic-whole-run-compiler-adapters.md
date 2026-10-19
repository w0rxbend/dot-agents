# Acyclic (com-lihaoyi/acyclic): whole-run compiler adapters

Originally `scala-acyclic-whole-run-compiler-adapters`. Evidence: [evidence/scala-acyclic-whole-run-compiler-adapters.json](evidence/scala-acyclic-whole-run-compiler-adapters.json). Claim IDs below (`acy-claim-*`) and record IDs (`acy-*`) resolve there.

Preserve what a compiler user observes, not just which cycles the graph algorithm finds. Acyclic's Scala 3 port initially passed graph-oriented work yet reported the same cycle repeatedly and hid supplemental dependency locations. Use that failure mechanism to bound the refactor.

## Scope

Use for changes to Acyclic's compiler callbacks, shared graph extraction, reporter adapters, or their in-process compiler tests; also when a port reports duplicate cycles, loses source locations, or claims whole-project coverage from an incremental compilation. The core procedure is diagnostic-preserving refactoring, not a general Scala organization checklist.

Not for: ordinary application cycles, arbitrary macro hygiene, dependency bumps, or generic Mill source sharing. An analyzer intentionally processing one unit per callback does not need Acyclic's whole-run guard. Do not introduce ZIO, Cats Effect or Ox into these synchronous compiler integrations.

## Prerequisites

Read the target revision's build, compiler dependencies, plugin descriptors, phase registrations and tests. Record exact Scala, Mill, uTest and JDK versions; calendar year alone is insufficient.

Trace `RuntimePlugin`/`TestPlugin` -> compiler-specific `PluginPhase` -> `BasePluginPhase.runAllUnits` -> `GraphAnalysis`, and `BaseCycleTests` -> the selected `TestUtils`. Obtain permission and an isolated checkout before executing upstream builds.

### Version and organization map

| Snapshot | Compiler/build boundary | What changes for review |
| --- | --- | --- |
| `e090ee2b8de5d7c468cd4787b1820fec567c5ad4`, 2022-12-08T20:48:06Z | Scala 2.11.12, 2.12.8-2.12.17, 2.13.0-2.13.10; Mill 0.10.10; uTest 0.8.1 | Compiler-coupled `acyclic/src/acyclic/plugin/PluginPhase.scala`; `TestUtils.make` returns position/message/severity triples. Build self-applies published Acyclic 0.3.6, but disables that plugin for test compilation. |
| `fbb60d12e73723b34ee15db3ae3231dd89b8bdc8`, 2024-09-23T04:17:11Z | Scala 2.11.12, 2.12.9-2.12.20, 2.13.1-2.13.15, 3.3.0-3.3.3, 3.4.0-3.4.3, 3.5.0-3.5.1; Mill 0.11.12; uTest 0.8.2 | Shared `BasePluginPhase`/`GraphAnalysis`, compiler-specific `src-2`/`src-3`, shared `BaseCycleTests`, and adapter-specific test harnesses returning message/severity pairs. `ScalaTests` plus `super.sources()` preserves version-specific test roots. Production self-plugin dependency is absent. |

These are historical families, not a recommendation to support every patch release today. The plugin executes in a JVM compiler; neither snapshot establishes JS/Native runtime behavior. There is no effect-library version: these sources use synchronous compiler APIs and local mutable graph state. Do not retrofit application-style concurrency or effect abstractions as part of an adapter extraction. The 2019 baseline in the broader dossier predates full-version publication; do not backport later build assumptions merely because the source language family is unchanged. Current validation must rediscover the selected build and compiler APIs.

## Workflow

1. **Write the behavioral baseline.** Identify file/pkg/skipped markers, force and warning options, graph input units, and whether the task is a refactor or an intentional semantic extension. Preserve package-internal cycles allowed by `acyclic.pkg`. Under force, skipped changes cycle-start eligibility; it is not permission to delete every edge involving that file.
2. **Separate compiler adaptation from graph policy.** Keep tree/symbol/unit traversal and reporting in adapters. Share graph construction, package aggregation, cycle selection and report orchestration only where semantics match. Retain dependency trees with edges: they supply leading positions, symbol names and supplemental lines. PR 136's factoring request was about this boundary, not maximum abstraction.
3. **Establish invocation and state ownership.** Trace whether a callback receives one unit while its implementation enumerates all units. For whole-run work, require one analysis per compilation run, not one per file. Inspect plugin and phase construction/reset paths before selecting a guard. The historical `alreadyRun` field lives on `TestPlugin`; it demonstrates a repair for one compilation, not correctness across reused instances. Do not reset it on every per-unit callback.
4. **Preserve the graph domain.** Keep validity, different-source-file and `unitMap.contains(symbolPath(sym))` checks before map lookup. Missing units must not become crashes or invented whole-project edges. A clean run and an incremental subset are different coverage claims.
5. **Review reporter semantics, not method names.** The Scala 3 implementation of shared `reportInform` uses `report.echo`, because `report.inform` hid the supplemental messages without `-verbose`. Preserve default visibility, error versus warning severity, positioned leading dependencies and human line numbering. Do not demand byte-identical caret formatting from different compilers.
6. **Repair the oracle before trusting parity.** Trace the entire test expression. `make(...).exists(...)` computes a Boolean; assert it. Match the actual severity representation and tuple shape. `makeFail` already asserts internally, but its conversion to sets and expected-subset check erase duplicate/extra reports. Capture raw events separately before normalization. Confirm which plugin the harness loads; a previously released bootstrap plugin must not pre-reject intentionally cyclic resources.
7. **Apply the smallest change and validate the matrix below.** Keep publication/toolchain changes separate unless necessary for the adapter under test. Do not report success from compilation alone when the contract concerns warnings or diagnostic multiplicity.

## Invariants

- One execution of whole-run analysis per run; a second supported run is not silently suppressed.
- The selected simple two-file cycle emits one top-level cycle diagnostic, independent of an unrelated third unit. Do not generalize this to one diagnostic for every possible project graph.
- Leading dependency positions and supplemental lines survive graph extraction and appear without verbose logging.
- Warn mode still checks the graph and emits the expected warning rather than merely compiling successfully.
- Edges refer only to admitted units; package-marker and skipped behavior remain unchanged.

## False positives

An internally asserting helper needs no redundant outer assertion; permitted package-internal cycles are not defects; distinct cycles may legitimately produce multiple diagnostics; different source caret styles are not semantic drift. An absent self-plugin dependency in the September 2024 build does not require restoring the 2022 bootstrap exclusions.

## Review sequence (observed history, not an approval narrative)

1. In PR 136, the author questioned whether a warning predicate needed an assertion. Li Haoyi's answer was conditional on the helper's implementation (`acy-review-port-test`). The author traced the sequence-returning helper and the Boolean-returning `exists`, then added an assertion and corrected severity spelling (`acy-response-port-test`). The 2022 and 2024 test snapshots show the before/after shape.
2. Li Haoyi asked to share operations on graph values while retaining bespoke compiler operations (`acy-review-port-boundary`). The author's response and final `BasePluginPhase` substantiate that revision. A shared implementation is not proof that traversal order or reporting lifecycle is equivalent.
3. A later two-file consumer check reported duplicate top-level diagnostics and missing supplemental lines (`acy-review-port-diagnostics`). The author's own response identifies verbose-only reporting and per-unit callback behavior (`acy-response-port-diagnostics`). These are author-reported experiments, not experiments executed by the researcher.

Review repair commits recorded in the corpus: `545b931d8b5f290c70df2912356eef6445b15bf2` (assertion), `c032bc725a8acd0668a1a32b38021382b39b734e` (duplicate-run guard), `23c947d38d89091fc4173034a0fa00bfe7c36e78` (echo). Final source evidence is pinned to the independently dated September 23 snapshot. A merge or approval adds no independent behavioral proof.

## Source map and discriminating observations (2024 snapshot)

- `acyclic/src/acyclic/plugin/BasePluginPhase.scala:51-68`: create `unitMap`, extract symbol/tree dependencies, reject invalid/self/out-of-run references before lookup. This is current-compilation analysis, not a persistent whole-project graph.
- `BasePluginPhase.scala:104-151`: choose cycles, call the cycle reporter, select fatal/warning severity, echo leading locations and print supplemental dependency lines. Dependency values must retain trees, not just connectivity booleans.
- `acyclic/src-3/acyclic/plugin/Plugin.scala:14-36`: `alreadyRun` is plugin-instance state and `init` does not visibly reset it. The source does not establish whether production compiler reuse keeps that instance alive.
- `acyclic/src-3/acyclic/plugin/PluginPhase.scala:26-32`: human line numbers add one; unpositioned supplemental output uses echo. The common method name `reportInform` is not a mandate to invoke the compiler method named inform.
- `acyclic/test/src-3/acyclic/TestUtils.scala:59-82`: each call builds a new context and compiler and loads a new test plugin. Calling this helper twice cannot prove a guard resets for a reused plugin.
- `TestUtils.scala:99-119`: actual and expected cycles become sets; inclusion permits extra cycles and conceals duplicates. Rotational normalization can remain useful for graph comparison, but it must not be the only diagnostic oracle.

### Raw-event regression design (inference)

Capture analysis entry count, raw top-level cycle reports, and source-location messages separately. Filter diagnostic counts by the cycle message and severity, not by every info line; one cycle intentionally has several location messages. Retain raw events before canonicalization.

For the review's simple two-file cycle, use force or explicit markers so detection is actually enabled. Add multiple references on separate lines to exercise the supplemental-message path. Repeat after adding an unrelated acyclic unit. Expected top-level cardinality stays one; verbose mode must not be necessary to see the extra locations. The proposed test must fail if the once-per-run gate is removed or echo is replaced by verbose-only inform. It need not require identical compiler caret formatting or demand the same number of reports for unrelated multi-cycle graphs.

For repeated-run coverage, establish the compiler's supported ownership contract first. If reuse is supported, retain the same compiler/plugin across two runs, change the cycle between runs, and require fresh analysis in the second run while still deduplicating callbacks inside each run. Never claim this passed from two independent `make` calls. Do not prescribe an unverified compiler reset API.

## Test and bootstrap isolation

`acy-claim-bootstrap-isolation` is supporting validation context, not a standalone publication skill. In revisions that self-apply a released plugin, inspect both the production plugin dependency and test module inheritance. PR 54's isolation commit and the 2022 build disable the published plugin on the test module; the harness explicitly loads the implementation under test. Otherwise deliberately cyclic resources can fail before the intended assertion runs.

PR 123's reviewer removed a stale exclusion for Scala 2.13.13 after its matching artifact existed, leaving the newly unreleased target excluded. This does not justify requiring bootstrap exclusions in September 2024, where production self-application has been removed. Do not restore historical machinery solely for stylistic consistency.

## Validation

Discover commands from the revision, not from a modern Mill template. The pinned 2024 CI uses `./mill -i -j 0 __.publishArtifacts + __.test` (`acy-ci-command-2024`); it selects artifact generation and tests and is not the separate release job. Inspect `build.sc`, `.mill-version`, the launcher and `.github/workflows/actions.yml` before using it in an authorized isolated environment; obtain execution/network permission and match compiler/JDK prerequisites. Do not invoke publishing, signing or credentials. The historical workflow declares Temurin Java 8; verify each selected compiler's real JDK prerequisites instead of assuming that declaration proves compatibility. For a narrower run, resolve the actual cross-module/test selectors using the selected Mill version's help; do not invent an sbt target.

Request these concrete tests and record actual execution separately from proposed expectations:

- Acyclic graph, marked two-file cycle, marked package/external cycle, allowed package-internal cycle, force/skip, and warn cases across both adapters.
- A two-file cycle with multiple references on different lines, compiled without `-verbose`: capture raw diagnostics and callback counts, then compare graph membership separately. Add an unrelated third file; multiplicity must not scale with input-unit count.
- A warning mutation: suppress or change the expected warning and require the assertion to fail. Respect 2022 `(position, message, severity)` versus 2024 `(message, severity)` tuples.
- Two successive compilation runs sharing the same compiler/plugin instance **if that lifecycle is supported**. Existing `make` constructs a fresh context/compiler/plugin; calling it twice is not this test. If reuse is unsupported, document that boundary rather than inventing a reset hook.
- A full-source clean compile versus a partial incremental input: report the latter as partial coverage, never a global acyclicity proof (`acy-claim-current-unit-domain`; readme incremental-compilation limitation).

No successful run of the historical matrix was verified. Compiler tests, diagnostic mutation checks and reused-instance checks remain unexecuted; no upstream build or Scala test was executed while authoring.

## Examples

**Good.** Extract graph assembly into `BasePluginPhase[CompilationUnit, Tree, Symbol]` while keeping compiler traversal and reporter calls in `src-2`/`src-3`. Preserve `unitMap` guards and dependency trees. The historical Scala 3 reporter uses `echo` and `sourcePos.line + 1`. Accept the extraction only after graph, marker and raw diagnostic checks, not because the two adapters have similar method names (`acy-claim-compiler-boundary`, `acy-claim-diagnostic-cardinality`).

**Broken and correction.** A per-unit Scala 3 callback invokes whole-run analysis unconditionally, and `reportInform` delegates to verbose-only `inform`. Set-canonicalized cycle tests still see the expected cycle. Correction: bind execution to the actual run lifetime and use default-visible reporting; test one diagnostic for the simple cycle before and after adding an unrelated unit. The historical flag is an example repair, not a universally safe lifecycle template.

Separately, the 2022 warning test returned `make(...).exists { case (_, "Unwanted cyclic dependency", "warning") => true; case _ => false }` without asserting it. Correct by asserting the predicate and matching the harness's `"WARNING"` representation (`acy-claim-warning-test-oracle`). Do not copy the 2024 two-element pattern into the older three-element tuple. Removing the warning must make the repaired test fail; this is a proposed mutation check, not an executed result.

**Negative.** `makeFail` intercepts compilation failure and asserts cycle inclusion internally. Do not flag its call site merely because it lacks `assert`. `success/pkg/innercycle` is deliberately successful: tightening it would change the public marker contract. An ordinary release-number edit does not trigger this compiler-lifecycle workflow unless the diff actually changes adapter behavior.

## Limitations

Evidence is a bounded historical sample through 2024, concentrated on PR 136 with earlier test/build context. The reused-instance risk is source-derived and unexecuted; no confirmed repeated-run bug or current-version fix is claimed. The historical `makeFail` helper proves expected-cycle inclusion, not exact report count. JVM compiler execution does not establish Scala.js/Native consumer coverage.

## Sources

- [PR 136: shared graph versus compiler-specific operations](https://github.com/com-lihaoyi/acyclic/pull/136#discussion_r1760522833).
- [PR 136: observed duplicate reports and missing supplemental lines](https://github.com/com-lihaoyi/acyclic/pull/136#issuecomment-2367017360).
- [PR 136: conditional assertion guidance and author repair](https://github.com/com-lihaoyi/acyclic/pull/136#discussion_r1760455092).
- [2024 TestUtils: set-based cycle inclusion](https://github.com/com-lihaoyi/acyclic/blob/fbb60d12e73723b34ee15db3ae3231dd89b8bdc8/acyclic/test/src-3/acyclic/TestUtils.scala#L99-L119).
