# Derivation, rendering, and effect contracts

## Identify the actual derivation boundary

The `worxbend` monorepo contains both `pretty-printo` and `reveal`; similarly named APIs do not imply interchangeable derivation rules. Trace the public `derived`/inline entrypoint to expansion code and runtime helpers. Check where the macro is **expanded**: compiler options on a macro implementation module alone cannot exercise generated consumer trees.

For quoted code, keep each `Expr`, `Term`, `TypeRepr`, and `Symbol` within its valid `Quotes` context. Bind an inline argument once when the contract requires one evaluation; substitution can otherwise repeat effects at every generated occurrence. Keep annotation precedence deterministic, generic substitution correct, and diagnostics attached to the offending user type or field. Scope extrusion is not disproved by one successful compile or by `-Xcheck-macros`; include the actual nested/sealed/product expansion shapes in tests.

The reviewed `reveal` implementation has separate budgets for nested domain types, emitted wrapper layers, and redaction reachability. Cycles and generically growing types are different: `Node[A] -> Node[List[A]]` never repeats the same applied type. Keep termination and refusal tests when changing traversal; an inline-count compiler flag does not bound ordinary recursion inside macro execution. See [expansion implementation and documented limits](https://github.com/worxbend/worxbend/blob/2b3a4c8566c82982b3af833ff91cced1c845a477/libs/commons/reveal/src/main/scala/com/worxbend/reveal/PrettyPrintableMacro.scala).

## Preserve the secret boundary

For these renderers, exclusion wins over redaction, and neither rule should read the hidden value. Exercise null values and types with throwing or observing renderers to catch accidental evaluation. Repeated annotation resolution follows the project's declared source-order rule. Nested annotated descendants must not fall through to unsafe generated case-class `toString` merely because the immediate container is unannotated. Verify containers, tuples, sealed branches, opaque/generic types, and explicit custom instances at the boundary touched by the change. See [annotation behavior tests](https://github.com/worxbend/worxbend/blob/2b3a4c8566c82982b3af833ff91cced1c845a477/libs/commons/reveal/src/test/scala/com/worxbend/reveal/AnnotationsSuite.scala) and [delegation/refusal tests](https://github.com/worxbend/worxbend/blob/2b3a4c8566c82982b3af833ff91cced1c845a477/libs/commons/reveal/src/test/scala/com/worxbend/reveal/DelegationSuite.scala).

Treat unresolved redaction reachability as uncertainty, not evidence that printing is safe. Preserve documented limitations honestly: the reviewed macro explicitly records a concrete non-final-class/subclass hole. A security-focused task should reproduce that boundary and evaluate a compatible remedy; do not silently describe the entire renderer as leak-proof.

Glyphora's `Masked` is a **display representation** retaining plaintext, not secure storage. Its mask count uses grapheme clusters and width uses terminal cells; diagnostic `toString` prints only the mask. Do not replace this with UTF-16 `length` or claim it protects serialization/reflection. See [masked-text contract](https://github.com/worxbend/glyphora/blob/a6be4185e94e7a5001f5a01afef8aece7db07d6b/core/src/main/scala/io/worxbend/tui/core/Masked.scala).

## Preserve effects and streams

Determine who owns cancellation, backend lifecycle, callbacks, retries, and typed errors before restructuring client code. A Future API is not permission to change the public result to ZIO; a ZIO library is not a candidate for an incidental Ox migration.

Gitea's streaming downloads transfer an open response to a lazily consumed ZStream. Early termination closes it; running the stream again sends another request. The reviewed streaming path deliberately has no replay retry and no request-observer events, with a per-chunk stall budget instead of a total download deadline. Preserve or explicitly revise these guarantees with tests. See [streaming ownership and retry contract](https://github.com/worxbend/gitea-scala-client/blob/2590501c22c8dd0bba216c24b2e03e6da873b313/backend-zio/src/io/worxbend/gitea4s/backend/zio/GiteaDownloads.scala).
