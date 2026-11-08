# Derivation, rendering, and effect contracts

## Identify the actual derivation boundary

`worxbend` monorepo holds both `pretty-printo` and `reveal`; similar API names do not mean interchangeable derivation rules. Trace public `derived`/inline entrypoint to expansion code and runtime helpers. Check where macro is **expanded**: compiler options on macro implementation module alone cannot exercise generated consumer trees.

In quoted code, keep each `Expr`, `Term`, `TypeRepr`, `Symbol` inside its valid `Quotes` context. When contract requires one evaluation, bind inline argument once; otherwise substitution can repeat effects at every generated occurrence. Keep annotation precedence deterministic, generic substitution correct, diagnostics on offending user type or field. One successful compile or `-Xcheck-macros` does not disprove scope extrusion; test actual nested/sealed/product expansion shapes.

Reviewed `reveal` implementation keeps separate budgets for nested domain types, emitted wrapper layers, redaction reachability. Cycles differ from generically growing types: `Node[A] -> Node[List[A]]` never repeats same applied type. When changing traversal, keep termination and refusal tests. Inline-count compiler flag does not bound ordinary recursion inside macro execution. See [expansion implementation and documented limits](https://github.com/worxbend/worxbend/blob/2b3a4c8566c82982b3af833ff91cced1c845a477/libs/commons/reveal/src/main/scala/com/worxbend/reveal/PrettyPrintableMacro.scala).

## Preserve the secret boundary

In these renderers exclusion wins over redaction; neither rule should read hidden value. Catch accidental evaluation with null values and with types whose renderers throw or observe. Repeated annotation resolution follows project's declared source-order rule. Nested annotated descendants must not fall through to unsafe generated case-class `toString` merely because immediate container is unannotated. At boundary touched by change, verify containers, tuples, sealed branches, opaque/generic types, explicit custom instances. See [annotation behavior tests](https://github.com/worxbend/worxbend/blob/2b3a4c8566c82982b3af833ff91cced1c845a477/libs/commons/reveal/src/test/scala/com/worxbend/reveal/AnnotationsSuite.scala) and [delegation/refusal tests](https://github.com/worxbend/worxbend/blob/2b3a4c8566c82982b3af833ff91cced1c845a477/libs/commons/reveal/src/test/scala/com/worxbend/reveal/DelegationSuite.scala).

Treat unresolved redaction reachability as uncertainty, not evidence printing is safe. Keep documented limitations honest: reviewed macro explicitly records concrete non-final-class/subclass hole. Security-focused task: reproduce that boundary, evaluate compatible remedy. Do not silently call entire renderer leak-proof.

Glyphora's `Masked` is **display representation** retaining plaintext, not secure storage. Mask count uses grapheme clusters; width uses terminal cells; diagnostic `toString` prints only mask. Do not replace with UTF-16 `length` or claim it protects serialization/reflection. See [masked-text contract](https://github.com/worxbend/glyphora/blob/a6be4185e94e7a5001f5a01afef8aece7db07d6b/core/src/main/scala/io/worxbend/tui/core/Masked.scala).

## Preserve effects and streams

Before restructuring client code, determine who owns cancellation, backend lifecycle, callbacks, retries, typed errors. Future API does not license changing public result to ZIO; ZIO library is not candidate for incidental Ox migration.

Gitea streaming downloads transfer open response to lazily consumed ZStream. Early termination closes response; rerunning stream sends another request. Reviewed streaming path deliberately has no replay retry and no request-observer events; it uses per-chunk stall budget instead of total download deadline. Preserve or explicitly revise these guarantees with tests. See [streaming ownership and retry contract](https://github.com/worxbend/gitea-scala-client/blob/2590501c22c8dd0bba216c24b2e03e6da873b313/backend-zio/src/io/worxbend/gitea4s/backend/zio/GiteaDownloads.scala).
