# Probe matrix for a Fastparse combinator extraction

These are proposed current-change checks inferred from the cited historical mechanisms, not claims that all historical tests existed or passed. Instantiate each row with the target compiler's actual syntax and supported overloads. Preserve the old result unless the requested change explicitly corrects it.

| Changed boundary | Discriminating input/check | Invariant |
|---|---|---|
| Ordinary higher-order wrapper | Run a child bracketed by `Index`; inspect both child values in a sequence | Child execution occurs between its own indices, not before the wrapper |
| Shared-run sequence | Use differently typed or distinguishable left/right results, and a failing left child | Left value is saved before right mutation; right does not run after left failure |
| Repetition bounds | Zero, one, lower-bound shortfall, upper-bound completion, and `exactly`; compare literal and runtime bounds where legal | Same count, result and final index across specialized/general paths |
| Separator | Absent separator, successful separator, missing next element and failed separator; distinguish cut versus uncut separator | Failed speculative progress rolls back only when allowed; no silent trailing-separator acceptance |
| Whitespace | NoWhitespace versus an actual whitespace parser; whitespace before a failing or zero-width right child | Whitespace progress does not substitute for right-child progress |
| Comment cut | Comment after last CSS declaration before `}`, plus existing declaration fixtures | Enclosing repetition can stop and enclosing whitespace can consume the comment |
| Buffered input | Same finite input as a string and several iterator chunks; include capture/lookahead and a committed prefix | Same value/index; no access before dropped-buffer boundary |
| Failure messages | Distinct child labels under verbose mode and supported string replay | Saved diagnostic fields still describe the correct child/branch |

Do not repeatedly parse an empty-success child without a bound merely to test progress: first inspect the target repetition contract and protect any liveness probe with the test runner's timeout. Do not impose a new progress/error policy as a refactoring.

For the CSS historical fixture, `CssParser.scala:188-206` ties declaration repetition to enclosing whitespace, and `CssTests.scala:195-216` checks both declarations and index 80. For the wrapper, `ExampleTests.scala:515-522` checks nested values/offsets but not full consumption. These are different oracles; neither alone proves all repetition branches.

Measure code size and runtime separately if specialization changes. The 2022 Scala 2 source explicitly limits macro expansion to avoid code bloat. The 2024 Scala 3 general macro inspects static values and retains conditional code generation. A stale copied header or an author-reported percentage is not a benchmark result for your change.

Use the evidence records `fp-state-2020`, `fp-sequence-2020`, `fp-css-source-256`, `fp-css-test-256`, `fp-repetition-2022`, `fp-repetition-2024`, and `fp-repetition-api-2024` in [evidence.json](evidence.json) to reopen the actual source before choosing a repair.
