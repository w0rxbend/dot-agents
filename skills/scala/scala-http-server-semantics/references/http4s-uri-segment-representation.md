# Preserve http4s URI segment meaning

> Library: http4s (core `Uri.Path`). Formerly `scala-http4s-uri-segment-representation` skill, merged into `scala-http-server-semantics`. Evidence: [evidence/scala-http4s-uri-segment-representation.json](evidence/scala-http4s-uri-segment-representation.json).

## When to Use

Parser/renderer changes, adding raw path segments, replacing String path alias with wrapper, or changing routing operations that split and concatenate paths. Key question: is a value an encoded segment, decoded segment text or whole path? Scala type String alone does not answer it.

## When Not to Use

Not a general URL sanitizer, query/form encoder, filesystem-path rule, or mandate to redesign application domain types. Explicit application routing normalization is separate policy. Do not expand into changing Cats Effect, adopting Ox or replacing repository's sbt build.

## Prerequisites

Before choosing constructors, read target revision's `Uri.scala`, path syntax, routing callers, law instances, generators, build. Detect Scala and http4s versions from that checkout; record full source SHA for historical comparisons.

Inspected 2020 snapshot `7775249e97abcb951c596a1f9a6104bf53bcc498`: Scala 2.12.12/2.13.3, Cats Effect 2.3.1, FS2 2.5.0. `Uri.Path.Segment.apply` encodes raw text; `Segment.encoded` takes already encoded text. Observed historical APIs, not guaranteed names or behavior on another branch. Calendar year does not identify release line.

## Workflow

1. Build boundary table: producer, entry representation, constructor/decoder used, exit representation, consumer. Trace parsing, segment append, rendering, `pathInfo`/`scriptName`, changed split/concat call sites. Check whether split indices count characters or segments.
2. Preserve encoding state. Parsed `we-have-a%2Ftest` must not pass through a constructor that encodes `%` again. Raw segment text `we-have-a/test` must encode its slash as segment data, not add a path separator. Do not decode whole path before splitting.
3. Enumerate path shape separately from segment contents: empty path, root, relative/absolute, interior empty segments, trailing separators. Keep normalization opt-in at its documented boundary. Common server treating `/a//b` like `/a/b` does not establish library-level equivalence.
4. Alias-to-wrapper migration: search typed equality and universal `==`/`equals` call sites. Convert comparisons to Path-to-Path or explicit rendering-to-String as intended. Do not make `path.equals(string)` true while `string.equals(path)` is false to hide migration break.
5. Preserve laws actually supported: equality symmetry, equal-value hash agreement, ordering consistency, associative concatenation. Run registered Order/Semigroup checks; do not invent Monoid identity because a reviewer considered one.
6. Add literal expected-path regressions before simplifying storage, normalization or allocation. Separate new regression from pre-existing edge case and from intentionally changed routing policy.

## Review and Refactoring Checks

Invariant: changed operation keeps intended segment boundaries, encoding state, path flags. Review data meaning, not just signatures. Keep equality symmetry even if migration support needs lint rule or explicit caller edits.

False positives: encoded constructor suits previously parsed encoded data; not automatically injection defect. Explicit normalization can be right for an application. Hash collisions between unequal paths do not violate equal-values-have-equal-hashes law.

Do not copy whole 2020 implementation as verified model: its `normalize` rebuilds a Path with default flags; String split handling needs trailing-empty tests; Segment equality match lacks unrelated-type fallback. These observations limit the exemplar; they do not prove current-version defect.

## Validation

Discover ownership from `build.sbt`: at cited snapshot, core tests live in separate `tests` project so they can depend on published test helpers. In separately authorized isolated checkout, inspect build, run `sbt projects` and `sbt 'tests / Test / definedTests'`, then `sbt 'tests / testOnly org.http4s.PathSuite org.http4s.UriSpec'`. Confirm nonzero tests and exact suite names; do not substitute `core/test` or invent Mill targets.

Exercise raw slash, encoded `%2F`, literal percent text, empty/root paths, `/a//b`, `/a/`, `/a//`, relative counterparts. Check round-trips against independent literals and intended contract, not another call to changed normalizer. Migration tests include null/unrelated-type equality and String comparisons. Required current-target checks; historical examples do not prove every edge case passes. No upstream compilation or tests ran for this procedure.

## Examples

### Good

Historical regression parses `https://example.com/we-have-a%2Ftest` into encoded segment; appending raw `we-have-a/test` yields one segment with escaped slash. Follow that distinction: assert encoded segment text plus segment count, not merely that rendering returns a String.

### Broken and Correction

Refactor decodes `/a%2Fb` to `/a/b` before splitting, calls result equivalent. One segment became two. Correction: split at actual path separators keeping encoded segment values, or use representation explicitly carrying decoded segment boundaries, encoding only during rendering. Separately, fix String-compatibility `equals` branch with explicit caller migration, not asymmetric equality.

### Negative

Application deliberately maps repeated slashes to one before own route lookup, documents that policy, leaves general URI parsing alone. Do not reject that policy with this procedure. Verify it stays localized and does not silently modify signatures, cache keys or other URI consumers outside its contract.

## Output Contract

Per finding: `file:line`, severity, representation transition, violated invariant, historical evidence ID, proposed bounded correction, discriminating test. State target Scala/http4s versions, discovered project/suite selectors, executed commands and observed results, or explicitly unexecuted obligations. Report intentional normalization separately from defects.

## Limitations

Derived from PR #3221 and commit-pinned source/tests; not comprehensive URI conformance audit or proof of current implementation correctness. Reviewer preferences are attributed to their comments, not asserted as unanimous maintainer policy. Adjacent generic Scala type-design (`scala-type-system`) and library-compatibility (`scala-library-contracts`, `scala-library-compatibility-laws`) skills stay authoritative in own scopes.

## Sources

See [evidence and claims](evidence/scala-http4s-uri-segment-representation.json), especially `c-uri-representation-laws`.

- [Representation alternatives in #3221](https://github.com/http4s/http4s/pull/3221#pullrequestreview-403779674).
- [Repeated separators](https://github.com/http4s/http4s/pull/3221#discussion_r418401915) and [equality migration](https://github.com/http4s/http4s/pull/3221#issuecomment-630286898).
- [Historical constructors](https://github.com/http4s/http4s/blob/7775249e97abcb951c596a1f9a6104bf53bcc498/core/src/main/scala/org/http4s/Uri.scala#L426-L430) and [encoding regressions](https://github.com/http4s/http4s/blob/7775249e97abcb951c596a1f9a6104bf53bcc498/tests/src/test/scala/org/http4s/UriSpec.scala#L1113-L1122).
