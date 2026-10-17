---
name: scala-oss-library-review
description: Use when reviewing, refactoring or hardening an open-source Scala library PR and you need the matching history-derived skill. Routes to evidence-backed skills mined from 2018-2024 ZIO, Typelevel, http4s, Play and Li Haoyi source and maintainer reviews.
license: MIT
---

# Scala OSS library review router

Entry point for the history-derived Scala skills in this catalog. Each routed skill
was authored from pinned 2018-01-01..2024-12-31 source and maintainer PR review
history, then independently audited and evaluated before promotion. This router
adds no historical claims of its own; evidence lives in each skill's
`references/evidence.json`.

## When to Use

- Reviewing or authoring a PR against an open-source Scala library, especially
  effect systems (ZIO, Cats Effect), streaming (FS2), HTTP stacks (http4s,
  ZIO HTTP, Play, Cask), typeclass libraries (Cats), parsers, macros or compiler
  plugins (Fastparse, sourcecode, Acyclic, Ammonite).
- Picking which focused skill applies to a diff, or checking a PR against the
  recurring review themes below.

## When Not to Use

- Application code with no library compatibility or concurrency contract.
  Use `scala-type-system`, `direct-style-scala` or `scala-functional-patterns` instead.
- General Scala API/binary contract work not tied to one of these mechanisms.
  Use `scala-library-contracts`.
- Build-tool questions. Use the `mill-*` skills.

## Prerequisites

- The diff or files under review, and the library's major version (ZIO 1/2,
  Cats Effect 2/3, Scala 2/3, JVM/JS/Native). Several skills fence their rules
  to specific eras; do not apply them across a version boundary unchecked.

## Workflow

1. Find the subsystem the change touches in [the routing index](references/skill-index.md)
   and load every skill whose trigger matches. One PR often needs two.
2. Walk the recurring themes below as a checklist for anything the focused
   skills do not cover.
3. Report findings using the loaded skill's output contract. Record false
   positives explicitly; every routed skill lists the ones its history showed.

## Review and Refactoring Checks

Recurring themes across the routed skills. They are cross-repository patterns,
not universal rules; confirm the library actually makes each promise.

- Cancellation is not failure. Keep interruption, error and success observable as
  different outcomes through races, memoization, cancel tokens and pooled
  handoffs (`scala-cats-effect-outcome-sensitive-concurrency`,
  `scala-zio-canceler-evaluation-owner`, `scala-zio-http-channel-handoff-completion`).
- Resource lifetimes follow use, not syntax. Check acquire < use < release per
  element, one acquired state per acquisition, and cleanup reachable on partial
  startup (`scala-fs2-per-element-scope-propagation`,
  `scala-http4s-stateful-factory-acquisition`,
  `scala-play-partial-startup-shutdown-completion`).
- Error provenance survives cleanup. A secondary finalizer or diagnostic error
  must not replace or silently drop the primary result
  (`scala-cats-effect-cleanup-error-provenance`,
  `scala-zio-http-request-local-error-disclosure`).
- Diagnostics must not change semantics. Labels, verbose modes and debug readers
  keep acceptance, consumed input and subject progress unchanged
  (`scala-fastparse-diagnostic-mode-review`, `scala-zio-diagnostic-reader-progress`).
- Optimizations need evidence for the path they change. Benchmarks must exercise
  the new path, and fast paths must keep branch isolation and allocation promises
  (`scala-cats-effect-runtime-benchmark-review`, `scala-fastparse-hot-path-cost-review`,
  `scala-cats-traversal-branch-isolation`).
- Compatibility means old binaries still behave correctly, not just link. Check
  erased signatures, inherited trait fields, law-backed instance strength and
  documented emission counts (`scala-cats-erased-runtime-compatibility`,
  `scala-cats-law-backed-instance-surface`, `scala-fs2-sink-emission-cardinality`).
- Wire and policy behavior is a matrix, not a happy path. Enumerate missing,
  wildcard, encoded and bodyless cases (`scala-http4s-uri-segment-representation`,
  `scala-http4s-http1-bodyless-connection-framing`, `scala-play-cors-csrf-policy-matrix`,
  `scala-zio-http-middleware-execution-boundaries`, `scala-cask-route-trie-validation-order`).
- Macro and compiler-plugin refactors preserve what was captured and when it ran
  (`scala-sourcecode-args-capture-review`, `scala-acyclic-whole-run-compiler-adapters`,
  `scala-ammonite-symbol-derived-closure-capture`,
  `scala-fastparse-shared-run-combinator-extraction`).
- A reviewer's proposal is not project policy until the final patch adopted it.
  Every routed skill separates observed code, reviewer prescription and inference.

## Validation

- Confirm each loaded skill's trigger actually matches the diff, and that its
  version fence matches the code's library and Scala versions.
- Prefer the repository's real build and test commands; the routed skills say how
  to discover them rather than inventing targets.

## Examples

### Good

A PR replaces `race` with a hand-rolled fiber join in a Cats Effect 3 library.
Load `scala-cats-effect-outcome-sensitive-concurrency`, apply its canceled-winner
and waiter-cleanup checks, and use the error-provenance theme for the new
finalizer.

### Broken and Correction

Broken: applying an FS2 per-element scope rule to a single fixed outer resource
and demanding per-element lifetimes. Correction: the routed skill lists this as a
false positive; one lifetime extension is correct there.

### Negative

A Spring Boot service written in Scala with no published library API: do not
route here; use the general Scala skills.

## Output Contract

List the skills loaded and why, then findings grouped by skill, each with
location, violated invariant, evidence or reasoning, and any false-positive
consideration. State which version fence was assumed.

## Limitations

- Coverage is uneven: some repositories contributed several skills, others none
  (see `research/scala-history/KNOWLEDGE.md` in the dot-agents repository for
  per-repository outcomes). Absence of a skill is not evidence of no practice.
- Skills were evaluated by model-based review against held-out historical cases;
  no upstream Scala build was executed during research.

## Sources

- [Routing index](references/skill-index.md), regenerated from the promotion ledger.
- Each routed skill's `references/evidence.json` (pinned SHAs and comment permalinks).
