---
name: scala-acyclic-whole-run-compiler-adapters
description: Use when refactoring Acyclic compiler adapters. Review Scala 2/3 whole-run analysis, duplicate or hidden diagnostics, unit-map boundaries, and warning-test oracles without changing marker semantics.
license: MIT
---

# Acyclic whole-run compiler adapters

Preserve what a compiler user observes, not just which cycles the graph algorithm finds. Acyclic's Scala 3 port initially passed graph-oriented work yet reported the same cycle repeatedly and hid supplemental dependency locations. Use that failure mechanism to bound the refactor.

## When to Use

Use for changes to Acyclic's compiler callbacks, shared graph extraction, reporter adapters, or their in-process compiler tests. Also use when a port reports duplicate cycles, loses source locations, or claims whole-project coverage from an incremental compilation. The core procedure is diagnostic-preserving refactoring, not a general Scala organization checklist.

## When Not to Use

Do not load solely for ordinary application cycles, arbitrary macro hygiene, dependency bumps, or generic Mill source sharing. Do not replace general library-compatibility guidance with this skill. An analyzer intentionally processing one unit per callback does not need Acyclic's whole-run guard. Do not introduce ZIO, Cats Effect or Ox into these synchronous compiler integrations.

## Prerequisites

Read the target revision's build, compiler dependencies, plugin descriptors, phase registrations and tests. Record exact Scala, Mill, uTest and JDK versions; calendar year alone is insufficient. Historical reference points are Scala 2-only/Mill 0.10.10/uTest 0.8.1 in 2022 and Scala 2.11–2.13 plus Scala 3.3–3.5/Mill 0.11.12/uTest 0.8.2 in September 2024. These are historical families, not a recommendation to support every patch release today.

Trace `RuntimePlugin`/`TestPlugin` → compiler-specific `PluginPhase` → `BasePluginPhase.runAllUnits` → `GraphAnalysis`, and `BaseCycleTests` → the selected `TestUtils`. Obtain permission and an isolated checkout before executing upstream builds. Read [historical-boundaries.md](references/historical-boundaries.md) for exact snapshots, source locations and build caveats.

## Workflow

1. **Write the behavioral baseline.** Identify file/pkg/skipped markers, force and warning options, graph input units, and whether the task is a refactor or an intentional semantic extension. Preserve package-internal cycles allowed by `acyclic.pkg`. Under force, skipped changes cycle-start eligibility; it is not permission to delete every edge involving that file.
2. **Separate compiler adaptation from graph policy.** Keep tree/symbol/unit traversal and reporting in adapters. Share graph construction, package aggregation, cycle selection and report orchestration only where semantics match. Retain dependency trees with edges: they supply leading positions, symbol names and supplemental lines. PR 136's factoring request was about this boundary, not maximum abstraction.
3. **Establish invocation and state ownership.** Trace whether a callback receives one unit while its implementation enumerates all units. For whole-run work, require one analysis per compilation run, not one per file. Inspect plugin and phase construction/reset paths before selecting a guard. The historical `alreadyRun` field lives on `TestPlugin`; it demonstrates a repair for one compilation, not correctness across reused instances. Do not reset it on every per-unit callback.
4. **Preserve the graph domain.** Keep validity, different-source-file and `unitMap.contains(symbolPath(sym))` checks before map lookup. Missing units must not become crashes or invented whole-project edges. A clean run and an incremental subset are different coverage claims.
5. **Review reporter semantics, not method names.** The Scala 3 implementation of shared `reportInform` uses `report.echo`, because `report.inform` hid the supplemental messages without `-verbose`. Preserve default visibility, error versus warning severity, positioned leading dependencies and human line numbering. Do not demand byte-identical caret formatting from different compilers.
6. **Repair the oracle before trusting parity.** Trace the entire test expression. `make(...).exists(...)` computes a Boolean; assert it. Match the actual severity representation and tuple shape. `makeFail` already asserts internally, but its conversion to sets and expected-subset check erase duplicate/extra reports. Capture raw events separately before normalization. Confirm which plugin the harness loads; a previously released bootstrap plugin must not pre-reject intentionally cyclic resources.
7. **Apply the smallest change and validate the matrix below.** Keep publication/toolchain changes separate unless necessary for the adapter under test. Do not report success from compilation alone when the contract concerns warnings or diagnostic multiplicity.

## Review and Refactoring Checks

Preserve these invariants:

- One execution of whole-run analysis per run; a second supported run is not silently suppressed.
- The selected simple two-file cycle emits one top-level cycle diagnostic, independent of an unrelated third unit. Do not generalize this to one diagnostic for every possible project graph.
- Leading dependency positions and supplemental lines survive graph extraction and appear without verbose logging.
- Warn mode still checks the graph and emits the expected warning rather than merely compiling successfully.
- Edges refer only to admitted units; package-marker and skipped behavior remain unchanged.

Avoid false positives: an internally asserting helper needs no redundant outer assertion; permitted package-internal cycles are not defects; distinct cycles may legitimately produce multiple diagnostics; different source caret styles are not semantic drift. An absent self-plugin dependency in the September 2024 build does not require restoring the 2022 bootstrap exclusions.

## Validation

Discover commands from the revision, not from a modern Mill template. The pinned 2024 CI uses `./mill -i -j 0 __.publishArtifacts + __.test`; inspect `build.sc`, `.mill-version`, the launcher and `.github/workflows/actions.yml` before using it in an authorized isolated environment. Do not run the separate publishing job. The historical workflow declares Java 8; verify each selected compiler's real JDK prerequisites instead of assuming that declaration proves compatibility. For a narrower run, first resolve the actual cross-module/test selectors using the selected Mill version's help; do not invent an sbt target.

Request these concrete tests and record actual execution separately from proposed expectations:

- Acyclic graph, marked two-file cycle, marked package/external cycle, allowed package-internal cycle, force/skip, and warn cases across both adapters.
- A two-file cycle with multiple references on different lines, compiled without `-verbose`: capture raw diagnostics and callback counts, then compare graph membership separately. Add an unrelated third file; multiplicity must not scale with input-unit count.
- A warning mutation: suppress or change the expected warning and require the assertion to fail. Respect 2022 `(position, message, severity)` versus 2024 `(message, severity)` tuples.
- Two successive compilation runs sharing the same compiler/plugin instance **if that lifecycle is supported**. Existing `make` constructs a fresh context/compiler/plugin; calling it twice is not this test. If reuse is unsupported, document that boundary rather than inventing a reset hook.
- A full-source clean compile versus a partial incremental input: report the latter as partial coverage, never a global acyclicity proof.

No upstream build or Scala test was executed while authoring this skill.

## Examples

### Good

Extract graph assembly into `BasePluginPhase[CompilationUnit, Tree, Symbol]` while keeping compiler traversal and reporter calls in `src-2`/`src-3`. Preserve `unitMap` guards and dependency trees. The historical Scala 3 reporter uses `echo` and `sourcePos.line + 1`. Accept the extraction only after graph, marker and raw diagnostic checks—not because the two adapters have similar method names. See `acy-claim-compiler-boundary` and `acy-claim-diagnostic-cardinality`.

### Broken and Correction

A per-unit Scala 3 callback invokes whole-run analysis unconditionally, and `reportInform` delegates to verbose-only `inform`. Set-canonicalized cycle tests still see the expected cycle. Correction: bind execution to the actual run lifetime and use default-visible reporting; test one diagnostic for the simple cycle before and after adding an unrelated unit. The historical flag is an example repair, not a universally safe lifecycle template.

Separately, the 2022 warning test returned `make(...).exists { case (_, "Unwanted cyclic dependency", "warning") => true; case _ => false }` without asserting it. Correct by asserting the predicate and matching the harness's `"WARNING"` representation. Do not copy the 2024 two-element pattern into the older three-element tuple. Removing the warning must make the repaired test fail; this is a proposed mutation check, not an executed result.

### Negative

`makeFail` intercepts compilation failure and asserts cycle inclusion internally. Do not flag its call site merely because it lacks `assert`. Likewise, `success/pkg/innercycle` is deliberately successful: tightening it would change the public marker contract. If reviewing only an ordinary release-number edit, decline this compiler-lifecycle workflow unless the diff actually changes adapter behavior.

## Output Contract

Return each finding with `file:line`, severity, violated invariant, exact version/revision, evidence ID or pinned source URL, minimal correction, and a discriminating test. Label historical observation, reviewer guidance and new inference separately. Include tested versus untested compiler cells, raw diagnostic counts where executed, clean versus incremental scope, plugin-instance reuse assumptions, and blockers. A proposed test or structurally valid skill is not an execution result.

## Limitations

Evidence is a bounded historical sample through 2024, concentrated on PR 136 with earlier test/build context. The reused-instance risk is source-derived and unexecuted; no confirmed repeated-run bug or current-version fix is claimed. The historical makeFail helper proves expected-cycle inclusion, not exact report count. JVM compiler execution does not establish Scala.js/Native consumer coverage. Preserve existing effect and direct-style choices.

## Sources

Claims and short attributed excerpts: [evidence.json](references/evidence.json). Version/build and provenance detail: [historical-boundaries.md](references/historical-boundaries.md).

- [PR 136: shared graph versus compiler-specific operations](https://github.com/com-lihaoyi/acyclic/pull/136#discussion_r1760522833).
- [PR 136: observed duplicate reports and missing supplemental lines](https://github.com/com-lihaoyi/acyclic/pull/136#issuecomment-2367017360).
- [PR 136: conditional assertion guidance and author repair](https://github.com/com-lihaoyi/acyclic/pull/136#discussion_r1760455092).
- [2024 TestUtils: set-based cycle inclusion](https://github.com/com-lihaoyi/acyclic/blob/fbb60d12e73723b34ee15db3ae3231dd89b8bdc8/acyclic/test/src-3/acyclic/TestUtils.scala#L99-L119).
