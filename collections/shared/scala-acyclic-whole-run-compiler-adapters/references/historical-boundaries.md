# Historical boundaries and validation design

This reference distinguishes observed history from checks proposed for a target checkout. It is not a current API reference. Resolve the claim/evidence IDs below in [evidence.json](evidence.json).

## Version and organization map

| Snapshot | Compiler/build boundary | What changes for review |
| --- | --- | --- |
| `e090ee2b8de5d7c468cd4787b1820fec567c5ad4`, 2022-12-08T20:48:06Z | Scala 2.11.12, 2.12.8–2.12.17, 2.13.0–2.13.10; Mill 0.10.10; uTest 0.8.1 | Compiler-coupled `acyclic/src/acyclic/plugin/PluginPhase.scala`; `TestUtils.make` returns position/message/severity triples. Build self-applies published Acyclic 0.3.6, but disables that plugin for test compilation. |
| `fbb60d12e73723b34ee15db3ae3231dd89b8bdc8`, 2024-09-23T04:17:11Z | Scala 2.11.12, 2.12.9–2.12.20, 2.13.1–2.13.15, 3.3.0–3.3.3, 3.4.0–3.4.3, 3.5.0–3.5.1; Mill 0.11.12; uTest 0.8.2 | Shared `BasePluginPhase`/`GraphAnalysis`, compiler-specific `src-2`/`src-3`, shared `BaseCycleTests`, and adapter-specific test harnesses returning message/severity pairs. `ScalaTests` plus `super.sources()` preserves version-specific test roots. Production self-plugin dependency is absent. |

The plugin executes in a JVM compiler. Neither snapshot establishes JS/Native runtime behavior. There is no effect-library version: these sources use synchronous compiler APIs and local mutable graph state. Do not retrofit application-style concurrency or effect abstractions as part of an adapter extraction.

The 2019 baseline in the broader dossier predates full-version publication; do not backport later build assumptions merely because the source language family is unchanged. Current validation must rediscover the selected build and compiler APIs.

## Review sequence, not an approval narrative

1. In PR 136, the author questioned whether a warning predicate needed an assertion. Li Haoyi's answer was conditional on the helper's implementation (`acy-review-port-test`). The author traced the sequence-returning helper and the Boolean-returning `exists`, then added an assertion and corrected severity spelling (`acy-response-port-test`). The 2022 and 2024 test snapshots show the before/after shape.
2. Li Haoyi asked to share operations on graph values while retaining bespoke compiler operations (`acy-review-port-boundary`). The author's response and final `BasePluginPhase` substantiate that revision. A shared implementation is not proof that traversal order or reporting lifecycle is equivalent.
3. A later two-file consumer check reported duplicate top-level diagnostics and missing supplemental lines (`acy-review-port-diagnostics`). The author's own response identifies verbose-only reporting and per-unit callback behavior (`acy-response-port-diagnostics`). These are author-reported experiments, not experiments executed by the researcher.

The review repair commits recorded in the corpus are `545b931d8b5f290c70df2912356eef6445b15bf2` (assertion), `c032bc725a8acd0668a1a32b38021382b39b734e` (duplicate-run guard), and `23c947d38d89091fc4173034a0fa00bfe7c36e78` (echo). Final source evidence is pinned to the independently dated September 23 snapshot. A merge or approval adds no independent behavioral proof.

## Source map and discriminating observations

At the 2024 snapshot:

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

## Build execution boundary

The historical CI command is `./mill -i -j 0 __.publishArtifacts + __.test` (`acy-ci-command-2024`). It selects artifact generation and tests; it is not the separate release job. Before execution, inspect the selected launcher and build/plugin dependencies, use an isolated writable checkout, obtain execution/network permission, and match compiler/JDK prerequisites. Do not invoke publishing, signing or credentials. Resolve narrower selectors against the actual pinned Mill version rather than substituting current module syntax.

The historical CI declares Temurin Java 8. No successful run of that matrix was verified here. Compiler tests, diagnostic mutation checks and reused-instance checks remain unexecuted. The readme's incremental-compilation limitation means a passing partial compile is never sufficient evidence for global acyclicity (`acy-claim-current-unit-domain`).
