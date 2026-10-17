# Preserve http4s URI segment meaning

> Library: http4s (core `Uri.Path`). Originally the `scala-http4s-uri-segment-representation` skill; merged into `scala-http-server-semantics`. Evidence: [evidence/scala-http4s-uri-segment-representation.json](evidence/scala-http4s-uri-segment-representation.json).

## When to Use

Use for parser/renderer changes, adding raw path segments, replacing a String path alias with a wrapper, or changing routing operations that split and concatenate paths. The key question is whether a value is an encoded segment, decoded segment text, or an entire path—not merely whether its Scala type is String.

## When Not to Use

Do not apply this as a general URL sanitizer, query/form encoder, filesystem-path rule, or mandate to redesign application domain types. Explicit application routing normalization is a separate policy. Do not expand the task into changing Cats Effect, adopting Ox, or replacing the repository's sbt build.

## Prerequisites

Read the target revision's `Uri.scala`, path syntax, routing callers, law instances, generators, and build before choosing constructors. Detect Scala and http4s versions from that checkout; record the full source SHA for historical comparisons.

The inspected 2020 snapshot `7775249e97abcb951c596a1f9a6104bf53bcc498` uses Scala 2.12.12/2.13.3, Cats Effect 2.3.1 and FS2 2.5.0. It has `Uri.Path.Segment.apply` for encoding raw text and `Segment.encoded` for already encoded text. These are observed historical APIs, not guaranteed names or behavior on another branch. Calendar year does not identify the release line.

## Workflow

1. Make a boundary table: producer, representation on entry, constructor/decoder used, representation on exit, and consumer. Trace parsing, segment append, rendering, `pathInfo`/`scriptName`, and changed split/concat call sites. Determine whether split indices count characters or segments.
2. Preserve encoding state. Parsed `we-have-a%2Ftest` must not pass through a constructor that encodes `%` again. Raw segment text `we-have-a/test` must encode its slash as segment data rather than introduce a path separator. Do not decode the whole path before splitting it.
3. Enumerate path shape separately from segment contents: empty path, root, relative/absolute, interior empty segments, and trailing separators. Keep normalization opt-in at its documented boundary. A common server treating `/a//b` like `/a/b` does not establish library-level equivalence.
4. For alias-to-wrapper migration, search both typed equality and universal `==`/`equals` call sites. Convert comparisons to Path-to-Path or explicit rendering-to-String as intended. Do not make `path.equals(string)` true while `string.equals(path)` is false to hide a migration break.
5. Preserve the actually supported laws. Check equality symmetry, equal-value hash agreement, ordering consistency and associative concatenation. Run registered Order/Semigroup checks; do not invent a Monoid identity because a reviewer considered one.
6. Add literal expected-path regressions before simplifying storage, normalization, or allocation. Separate a newly introduced regression from a pre-existing edge case and from an intentionally changed routing policy.

## Review and Refactoring Checks

The invariant is preservation of intended segment boundaries, encoding state and path flags through the changed operation. Review data meaning, not just signatures. Preserve equality symmetry even when migration support needs a lint rule or explicit caller edits.

False positives: an encoded constructor is appropriate for previously parsed encoded data; it is not automatically an injection defect. Explicit normalization can be correct for an application. Hash collisions between unequal paths are not a violation of the equal-values-have-equal-hashes law.

Do not copy the entire 2020 implementation as a verified model: its `normalize` reconstructs a Path with default flags; its String split handling needs trailing-empty tests; and its Segment equality match lacks an unrelated-type fallback. Those source observations limit the exemplar, rather than proving a current-version defect.

## Validation

Discover ownership from `build.sbt`: at the cited snapshot core tests are in the separate `tests` project so they can depend on published test helpers. In a separately authorized isolated checkout, inspect the build, then use `sbt projects` and `sbt 'tests / Test / definedTests'` before running `sbt 'tests / testOnly org.http4s.PathSuite org.http4s.UriSpec'`. Confirm nonzero tests and the exact suite names; do not substitute `core/test` or invent Mill targets.

Exercise raw slash, encoded `%2F`, literal percent text, empty/root paths, `/a//b`, `/a/`, `/a//`, and relative counterparts. Check round-trip expectations against independent literals and the intended contract, not against another call to the changed normalizer. Include null/unrelated-type equality and String comparisons in migration tests. These are required current-target checks; the historical examples do not prove every edge case passes. No upstream compilation or tests were executed to author this procedure.

## Examples

### Good

The historical regression parses `https://example.com/we-have-a%2Ftest` into an encoded segment, while appending raw `we-have-a/test` produces one segment with an escaped slash. Follow that distinction and assert the encoded segment text plus segment count, rather than merely checking that rendering returns a String.

### Broken and Correction

A refactor decodes `/a%2Fb` into `/a/b` before splitting, then calls the result equivalent. It changed one segment into two. Correction: split at actual path separators while retaining encoded segment values, or use a representation that explicitly carries decoded segment boundaries and encodes only during rendering. Separately, repair a String-compatibility `equals` branch with explicit caller migration, not asymmetric equality.

### Negative

An application deliberately maps repeated slashes to one slash before its own route lookup, documents that policy, and does not alter general URI parsing. Do not reject that application policy using this procedure. Verify it remains localized and does not silently modify signatures, cache keys or other URI consumers outside its contract.

## Output Contract

Return each finding as `file:line`, severity, representation transition, violated invariant, historical evidence ID, proposed bounded correction, and discriminating test. State target Scala/http4s versions, discovered project/suite selectors, executed commands and observed results—or explicitly unexecuted obligations. Report intentional normalization separately from defects.

## Limitations

This procedure derives from PR #3221 and commit-pinned source/tests; it is not a comprehensive URI conformance audit or proof of current implementation correctness. Reviewer preferences are attributed to their comments, not asserted as unanimous maintainer policy. Adjacent generic Scala type-design (`scala-type-system`) and library-compatibility (`scala-library-contracts`, `scala-library-compatibility-laws`) skills remain authoritative for their own scopes.

## Sources

See [evidence and claims](evidence/scala-http4s-uri-segment-representation.json), especially `c-uri-representation-laws`.

- [Representation alternatives in #3221](https://github.com/http4s/http4s/pull/3221#pullrequestreview-403779674).
- [Repeated separators](https://github.com/http4s/http4s/pull/3221#discussion_r418401915) and [equality migration](https://github.com/http4s/http4s/pull/3221#issuecomment-630286898).
- [Historical constructors](https://github.com/http4s/http4s/blob/7775249e97abcb951c596a1f9a6104bf53bcc498/core/src/main/scala/org/http4s/Uri.scala#L426-L430) and [encoding regressions](https://github.com/http4s/http4s/blob/7775249e97abcb951c596a1f9a6104bf53bcc498/tests/src/test/scala/org/http4s/UriSpec.scala#L1113-L1122).
