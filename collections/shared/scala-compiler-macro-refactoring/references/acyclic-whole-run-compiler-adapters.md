# Acyclic (com-lihaoyi/acyclic): whole-run compiler adapters

Originally `scala-acyclic-whole-run-compiler-adapters`. Evidence: [evidence/scala-acyclic-whole-run-compiler-adapters.json](evidence/scala-acyclic-whole-run-compiler-adapters.json). Claim IDs below (`acy-claim-*`) and record IDs (`acy-*`) resolve there.

Preserve what compiler users see, not only cycles graph algorithm finds. Acyclic's Scala 3 port first passed graph work, yet reported same cycle repeatedly and hid supplemental dependency locations. That failure mechanism bounds refactor.

## Scope

Use for changes to Acyclic's compiler callbacks, shared graph extraction, reporter adapters or in-process compiler tests. Also when a port duplicates cycle reports, loses source locations, or claims whole-project coverage from incremental compilation. Diagnostic-preserving refactoring, not general Scala organization checklist.

Not for: ordinary application cycles, arbitrary macro hygiene, dependency bumps, generic Mill source sharing. Analyzer intentionally processing one unit per callback does not need Acyclic's whole-run guard. Do not introduce ZIO, Cats Effect or Ox into these synchronous compiler integrations.

## Prerequisites

Read target revision's build, compiler dependencies, plugin descriptors, phase registrations, tests. Record exact Scala, Mill, uTest, JDK versions; calendar year alone is insufficient.

Trace `RuntimePlugin`/`TestPlugin` -> compiler-specific `PluginPhase` -> `BasePluginPhase.runAllUnits` -> `GraphAnalysis`, and `BaseCycleTests` -> selected `TestUtils`. Get permission and isolated checkout before running upstream builds.

### Version and organization map

| Snapshot | Compiler/build boundary | What changes for review |
| --- | --- | --- |
| `e090ee2b8de5d7c468cd4787b1820fec567c5ad4`, 2022-12-08T20:48:06Z | Scala 2.11.12, 2.12.8-2.12.17, 2.13.0-2.13.10; Mill 0.10.10; uTest 0.8.1 | Compiler-coupled `acyclic/src/acyclic/plugin/PluginPhase.scala`; `TestUtils.make` returns position/message/severity triples. Build self-applies published Acyclic 0.3.6, disabled for test compilation. |
| `fbb60d12e73723b34ee15db3ae3231dd89b8bdc8`, 2024-09-23T04:17:11Z | Scala 2.11.12, 2.12.9-2.12.20, 2.13.1-2.13.15, 3.3.0-3.3.3, 3.4.0-3.4.3, 3.5.0-3.5.1; Mill 0.11.12; uTest 0.8.2 | Shared `BasePluginPhase`/`GraphAnalysis`; compiler-specific `src-2`/`src-3`; shared `BaseCycleTests`; adapter-specific harnesses return message/severity pairs. `ScalaTests` plus `super.sources()` keeps version-specific test roots. No production self-plugin dependency. |

Historical families, not advice to support every patch release today. Plugin runs in JVM compiler; neither snapshot establishes JS/Native runtime behavior. No effect-library version: synchronous compiler APIs and local mutable graph state. Do not retrofit application-style concurrency or effect abstractions during adapter extraction. Broader dossier's 2019 baseline predates full-version publication; do not backport later build assumptions only because source language family is unchanged. Current validation must rediscover selected build and compiler APIs.

## Workflow

1. **Write behavioral baseline.** Identify file/pkg/skipped markers, force and warning options, graph input units, and whether task is refactor or intentional semantic extension. Preserve package-internal cycles allowed by `acyclic.pkg`. Under force, skipped changes cycle-start eligibility; it does not permit deleting every edge touching that file.
2. **Separate compiler adaptation from graph policy.** Adapters keep tree/symbol/unit traversal and reporting. Share graph construction, package aggregation, cycle selection, report orchestration only where semantics match. Keep dependency trees on edges: they supply leading positions, symbol names, supplemental lines. PR 136's factoring request targeted this boundary, not maximum abstraction.
3. **Establish invocation and state ownership.** Check whether callback receives one unit while implementation enumerates all units. Whole-run work needs one analysis per compilation run, not per file. Inspect plugin and phase construction/reset paths before picking guard. Historical `alreadyRun` field on `TestPlugin` repairs one compilation; it does not prove correctness across reused instances. Do not reset it on every per-unit callback.
4. **Preserve graph domain.** Keep validity, different-source-file and `unitMap.contains(symbolPath(sym))` checks before map lookup. Missing units must not become crashes or invented whole-project edges. Clean run and incremental subset are different coverage claims.
5. **Review reporter semantics, not method names.** Scala 3 implementation of shared `reportInform` uses `report.echo`, because `report.inform` hid supplemental messages without `-verbose`. Preserve default visibility, error versus warning severity, positioned leading dependencies, human line numbering. Do not demand byte-identical caret formatting across compilers.
6. **Repair oracle before trusting parity.** Trace whole test expression. `make(...).exists(...)` computes a Boolean; assert it. Match actual severity representation and tuple shape. `makeFail` asserts internally, but its set conversion and expected-subset check erase duplicate/extra reports. Capture raw events before normalization. Confirm which plugin harness loads; previously released bootstrap plugin must not pre-reject intentionally cyclic resources.
7. **Apply smallest change and validate matrix below.** Keep publication/toolchain changes separate unless adapter under test needs them. Compilation alone does not prove success when contract covers warnings or diagnostic multiplicity.

## Invariants

- Whole-run analysis executes once per run; second supported run is not silently suppressed.
- Selected simple two-file cycle emits one top-level cycle diagnostic, with or without unrelated third unit. Do not generalize to one diagnostic for every possible project graph.
- Leading dependency positions and supplemental lines survive graph extraction and show without verbose logging.
- Warn mode still checks graph and emits expected warning, not merely compiles.
- Edges refer only to admitted units; package-marker and skipped behavior unchanged.

## False positives

Internally asserting helper needs no outer assertion. Permitted package-internal cycles are not defects. Distinct cycles may legitimately yield multiple diagnostics.

## Review sequence (observed history, not an approval narrative)

1. In PR 136, author asked whether a warning predicate needed assertion. Li Haoyi's answer depended on helper implementation (`acy-review-port-test`). Author traced sequence-returning helper and Boolean-returning `exists`, added assertion, fixed severity spelling (`acy-response-port-test`). 2022 and 2024 test snapshots show before/after shape.
2. Li Haoyi asked to share operations on graph values while keeping bespoke compiler operations (`acy-review-port-boundary`). Author's response and final `BasePluginPhase` substantiate that revision. Shared implementation does not prove equivalent traversal order or reporting lifecycle.
3. Later two-file consumer check found duplicate top-level diagnostics and missing supplemental lines (`acy-review-port-diagnostics`). Author's own response identifies verbose-only reporting and per-unit callback behavior (`acy-response-port-diagnostics`). Author-reported experiments, not researcher-executed.

Review repair commits in corpus: `545b931d8b5f290c70df2912356eef6445b15bf2` (assertion), `c032bc725a8acd0668a1a32b38021382b39b734e` (duplicate-run guard), `23c947d38d89091fc4173034a0fa00bfe7c36e78` (echo). Final source evidence pinned to independently dated September 23 snapshot. Merge or approval adds no independent behavioral proof.

## Source map and discriminating observations (2024 snapshot)

- `acyclic/src/acyclic/plugin/BasePluginPhase.scala:51-68`: create `unitMap`, extract symbol/tree dependencies, reject invalid/self/out-of-run references before lookup. Current-compilation analysis, not persistent whole-project graph.
- `BasePluginPhase.scala:104-151`: choose cycles, call cycle reporter, select fatal/warning severity, echo leading locations, print supplemental dependency lines. Dependency values must keep trees, not only connectivity booleans.
- `acyclic/src-3/acyclic/plugin/Plugin.scala:14-36`: `alreadyRun` is plugin-instance state; `init` does not visibly reset it. Source does not show whether production compiler reuse keeps that instance alive.
- `acyclic/src-3/acyclic/plugin/PluginPhase.scala:26-32`: human line numbers add one; unpositioned supplemental output uses echo. Common method name `reportInform` does not mandate calling compiler method named inform.
- `acyclic/test/src-3/acyclic/TestUtils.scala:59-82`: each call builds new context, compiler and test plugin. Calling helper twice cannot prove a guard resets for reused plugin.
- `TestUtils.scala:99-119`: actual and expected cycles become sets; inclusion permits extra cycles and hides duplicates. Rotational normalization stays useful for graph comparison but must not be the only diagnostic oracle.

### Raw-event regression design (inference)

Capture analysis entry count, raw top-level cycle reports and source-location messages separately. Count diagnostics by cycle message and severity, not every info line; one cycle intentionally has several location messages. Keep raw events before canonicalization.

For review's simple two-file cycle, use force or explicit markers so detection is enabled. Put multiple references on separate lines to exercise supplemental-message path. Repeat after adding unrelated acyclic unit. Top-level cardinality stays one; extra locations must show without verbose mode. Proposed test must fail if once-per-run gate is removed or echo becomes verbose-only inform. It need not require identical caret formatting or equal report counts for unrelated multi-cycle graphs.

For repeated-run coverage, first establish compiler's supported ownership contract. If reuse is supported, keep same compiler/plugin across two runs and change cycle between them. Require fresh analysis in second run while still deduplicating callbacks within each run. Never claim this passed from two independent `make` calls. Do not prescribe unverified compiler reset API.

## Test and bootstrap isolation

`acy-claim-bootstrap-isolation` is supporting validation context, not standalone publication skill. In revisions self-applying a released plugin, inspect production plugin dependency and test module inheritance. PR 54's isolation commit and 2022 build disable published plugin on test module; harness explicitly loads implementation under test. Otherwise deliberately cyclic resources can fail before intended assertion runs.

PR 123's reviewer removed stale Scala 2.13.13 exclusion once matching artifact existed, leaving newly unreleased target excluded. That does not justify requiring bootstrap exclusions in September 2024, where production self-application is removed. Do not restore historical machinery only for stylistic consistency.

## Validation

Discover commands from revision, not modern Mill template. Pinned 2024 CI uses `./mill -i -j 0 __.publishArtifacts + __.test` (`acy-ci-command-2024`): artifact generation plus tests, not separate release job. Before using it in authorized isolated environment, inspect `build.sc`, `.mill-version`, launcher and `.github/workflows/actions.yml`. Get execution/network permission; match compiler/JDK prerequisites. Do not invoke publishing, signing or credentials. Historical workflow declares Temurin Java 8; verify each selected compiler's real JDK prerequisites instead of treating that declaration as compatibility proof. For narrower run, resolve actual cross-module/test selectors from selected Mill version's help; do not invent sbt target.

Request these concrete tests; record actual execution separately from proposed expectations:

- Acyclic graph, marked two-file cycle, marked package/external cycle, allowed package-internal cycle, force/skip, and warn cases across both adapters.
- Two-file cycle with multiple references on different lines, compiled without `-verbose`: capture raw diagnostics and callback counts, then compare graph membership separately. Add unrelated third file; multiplicity must not scale with input-unit count.
- Warning mutation: suppress or change expected warning; assertion must fail. Respect 2022 `(position, message, severity)` versus 2024 `(message, severity)` tuples.
- Two successive compilation runs sharing one compiler/plugin instance **if that lifecycle is supported**. If reuse is unsupported, document that boundary; do not invent reset hook.
- Full-source clean compile versus partial incremental input: report latter as partial coverage, never global acyclicity proof (`acy-claim-current-unit-domain`; readme incremental-compilation limitation).

Compiler tests, diagnostic mutation checks and reused-instance checks remain unexecuted; no upstream build or Scala test ran while authoring.

## Examples

**Good.** Extract graph assembly into `BasePluginPhase[CompilationUnit, Tree, Symbol]`; keep compiler traversal and reporter calls in `src-2`/`src-3`. Preserve `unitMap` guards and dependency trees. Historical Scala 3 reporter uses `echo` and `sourcePos.line + 1`. Accept extraction only after graph, marker and raw diagnostic checks, not because adapters have similar method names (`acy-claim-compiler-boundary`, `acy-claim-diagnostic-cardinality`).

**Broken and correction.** Per-unit Scala 3 callback runs whole-run analysis unconditionally; `reportInform` delegates to verbose-only `inform`. Set-canonicalized cycle tests still see expected cycle. Correction: bind execution to actual run lifetime and use default-visible reporting. Test one diagnostic for simple cycle before and after adding unrelated unit.

Separately, 2022 warning test returned `make(...).exists { case (_, "Unwanted cyclic dependency", "warning") => true; case _ => false }` without asserting it. Fix: assert predicate and match harness's `"WARNING"` representation (`acy-claim-warning-test-oracle`). Do not copy 2024 two-element pattern into older three-element tuple.

**Negative.** `makeFail` intercepts compilation failure and asserts cycle inclusion internally; do not flag its call site only for lacking `assert`. `success/pkg/innercycle` is deliberately successful: tightening it would change public marker contract. Ordinary release-number edit does not trigger this compiler-lifecycle workflow unless diff changes adapter behavior.

## Limitations

Evidence: bounded historical sample through 2024, centered on PR 136 plus earlier test/build context. Reused-instance risk is source-derived and unexecuted; no confirmed repeated-run bug or current-version fix claimed.

## Sources

- [PR 136: shared graph versus compiler-specific operations](https://github.com/com-lihaoyi/acyclic/pull/136#discussion_r1760522833).
- [PR 136: observed duplicate reports and missing supplemental lines](https://github.com/com-lihaoyi/acyclic/pull/136#issuecomment-2367017360).
- [PR 136: conditional assertion guidance and author repair](https://github.com/com-lihaoyi/acyclic/pull/136#discussion_r1760455092).
- [2024 TestUtils: set-based cycle inclusion](https://github.com/com-lihaoyi/acyclic/blob/fbb60d12e73723b34ee15db3ae3231dd89b8bdc8/acyclic/test/src-3/acyclic/TestUtils.scala#L99-L119).
