---
name: scala-oss-library-review
description: Use when reviewing, refactoring or hardening an open-source Scala library PR and you need the matching history-derived skill. Routes to evidence-backed skills mined from 2018-2024 ZIO, Typelevel, http4s, Play and Li Haoyi source and maintainer reviews.
license: MIT
---

# Scala OSS library review router

Entry point for the history-derived Scala skills in this catalog. Their 28 findings
were authored from pinned 2018-01-01..2024-12-31 source and maintainer PR review
history, independently audited and evaluated, then merged into six thematic skills.
Each merged skill states the shared invariants and keeps every finding as a case
file in `references/` with its evidence in `references/evidence/<original-id>.json`.
This router adds no historical claims of its own.

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
   and load every skill whose trigger matches. One PR often needs two. Inside a
   skill, its routing table names the case file for the library under change.
2. Walk the recurring themes below as a checklist for anything the focused
   skills do not cover.
3. Report findings using the loaded skill's output contract. Record false
   positives explicitly; every routed skill lists the ones its history showed.

## Review and Refactoring Checks

Recurring themes across the routed skills. They are cross-repository patterns,
not universal rules; confirm the library actually makes each promise.

- Cancellation is not failure. Keep interruption, error and success observable as
  different outcomes through races, memoization, cancel tokens and pooled
  handoffs (`scala-effect-cancellation-finalization`, `scala-http-server-semantics`).
- Resource lifetimes follow use, not syntax. Check acquire < use < release per
  element, one acquired state per acquisition, and cleanup reachable on partial
  startup (`scala-stream-resource-scoping`, `scala-effect-cancellation-finalization`).
- Error provenance survives cleanup. A secondary finalizer or diagnostic error
  must not replace or silently drop the primary result
  (`scala-effect-cancellation-finalization`, `scala-http-server-semantics`).
- Diagnostics must not change semantics. Labels, verbose modes and debug readers
  keep acceptance, consumed input and subject progress unchanged
  (`scala-runtime-diagnostics-hot-paths`).
- Optimizations need evidence for the path they change. Benchmarks must exercise
  the new path, and fast paths must keep branch isolation and allocation promises
  (`scala-runtime-diagnostics-hot-paths`, `scala-library-compatibility-laws`).
- Compatibility means old binaries still behave correctly, not just link. Check
  erased signatures, inherited trait fields, law-backed instance strength and
  documented emission counts (`scala-library-compatibility-laws`,
  `scala-stream-resource-scoping`).
- Wire and policy behavior is a matrix, not a happy path. Enumerate missing,
  wildcard, encoded and bodyless cases (`scala-http-server-semantics`).
- Macro and compiler-plugin refactors preserve what was captured and when it ran
  (`scala-compiler-macro-refactoring`).
- A reviewer's proposal is not project policy until the final patch adopted it.
  Every merged skill separates observed code, reviewer prescription and inference.

## Validation

- Confirm each loaded skill's trigger actually matches the diff, and that its
  version fence matches the code's library and Scala versions.
- Prefer the repository's real build and test commands; the routed skills say how
  to discover them rather than inventing targets.

## Examples

### Good

A PR replaces `race` with a hand-rolled fiber join in a Cats Effect 3 library.
Load `scala-effect-cancellation-finalization`, read its Cats Effect outcome case
file, apply the canceled-winner and waiter-cleanup checks, and use the
error-provenance case for the new finalizer.

### Broken and Correction

Broken: applying an FS2 per-element scope rule to a single fixed outer resource
and demanding per-element lifetimes. Correction: `scala-stream-resource-scoping`
lists this as a false positive; one lifetime extension is correct there.

### Negative

A Spring Boot service written in Scala with no published library API: do not
route here; use the general Scala skills.

## Output Contract

List the skills and case files loaded and why, then findings grouped by skill, each with
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
- Each merged skill's `references/evidence/*.json` (pinned SHAs and comment permalinks).
