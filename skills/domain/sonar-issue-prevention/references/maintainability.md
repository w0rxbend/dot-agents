# Maintainability without contract drift

## Complexity: S3776, S1067, S1066

Extract coherent operations, not arbitrary blocks chosen only to beat a metric. Parser can dispatch to object/array readers; CLI can orchestrate input validation, execution, reporting. Keep error context and branch order visible.

Name long predicates by invariant checked. Preserve short-circuit evaluation, side effects, error precedence. Merge nested guards only if evaluating inner condition at combined point behaves identically.

Scala concurrent loops: identify scope/resource ownership before extracting functions. Preserve cancellation checks, deadlines, channel termination, pending state, loss accounting. Return immutable collection outcomes or ADTs where helpful. Do not move method-local loop state into shared fields. Keep existing effect model and compiler options. Historical benchmark kept for A/B measurement is not a normal refactoring target.

## Repeated literals: S1192

Use named constant when occurrences mean same thing: fixture IDs, artifact paths, expected stable diagnostics, endpoint defaults. Scope it to smallest owning suite/module. No global constants for unrelated equal strings. Do not force every two-character delimiter behind a name.

Tests keep independent expectations. Test-local expected diagnostic is fine. Importing production constant to assert against itself can mask contract change. Keep descriptive scenario names. Do not extract synthetic credentials only to evade credential rule.

## Test precision: S5778, S2068

Prepare arguments outside exception assertion; block holds only intended throwing operation. Assert relevant error context when it matters. Keep redaction, invalid-URI, Unicode-authentication, missing-password cases. Use clearly synthetic, test-only values that do not authenticate to real services. Document this if a security rule misclassifies them.

## Small Python improvements: S7494, S7500, S9409

Prefer dictionary comprehension when transforming keys or values; keep duplicate-key and ordering semantics. If iterable already holds desired key/value pairs, `dict(pairs)` beats identity comprehension. Avoid cycling between S7494 and S7500: merge adjacent construction and transformation into one meaningful comprehension where appropriate. Use `extend` for coherent consecutive group of list elements. Avoid these rewrites when they obscure evaluation order or comprehension side effects.

## Verification

Pick tests for changed behavior: parser malformed/duplicate/deep inputs, timeout/closure/overflow boundaries, output byte equality, exception provenance, dictionary overwrite behavior. Keep exact project coverage gates intact; never add exclusions to hide branches introduced by refactoring.
