# Distinct diagnostic oracles

Build a minimal deterministic parser around a unique label. Keep its input, starting index and naming stable. Use the exact target-version parser syntax; do not infer current message field names from historical source.

| Input and mode | Expected invariant | Common false conclusion |
|---|---|---|
| String, ordinary parse of custom Fail | Failure at the expected index; no extra consumption | An absent label means the overload is broken |
| String, verbose parse of custom Fail | Same failure position, custom label through the supported message surface | Any failure string, including the default label, proves propagation |
| String, ordinary parse followed by trace | Replay preserves parser/start index, collects custom message at the failure | Trace is only formatting and cannot execute the parser again |
| String, plain Fail control | Default `fail` label when the selected mode collects it | Fixing custom Fail permits changing plain Fail's contract |
| One-shot iterator/reader | Original-run diagnostics where supported; historical replay check remains | Keeping every chunk forever is a harmless formatting repair |

For the known PR 244 defect, inspect both `SharedPackageDefs.scala:164` and `ExampleTests.scala:135` at its head. At the PR 297 merge SHA the corrected test is at line 136; line numbers differ across revisions. Use exact SHA/file references in a historical finding and current `file:line` in a live review.

Suggested mutation check, only in an authorized test checkout: temporarily change the corrected reporting closure back to the default literal. The custom-label oracle must fail while the default-Fail control remains valid. Restore the implementation. This is a proposed test of the oracle, not an operation executed during research.

The historical correction supplies a replay assertion but not proof that every row above was independently tested. PR 297 comments distinguish the focused change from external-repository integration failures; do not relabel author-reported CI retries as locally reproduced success.

Sources and claims: [evidence.json](evidence.json), especially `fp-fail-source-244`, `fp-fail-test-244`, `fp-fail-fix-297`, `fp-fail-test-297`, `fp-trace-2022`, `fp-input-2020`, and `fp-fix-validation-297`.
