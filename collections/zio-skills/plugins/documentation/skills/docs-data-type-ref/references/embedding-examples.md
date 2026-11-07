# Embedding Example Files with `SourceFile`

Guidance for embedding full Scala source files in reference page via `SourceFile.print`. Load when writing **Running the Examples** section of `docs-data-type-ref` page, or reformatting existing page's embeds.

`docs-data-type-ref` default: **always use `SourceFile.print`** for examples. Hand-pasted source duplicates code and drifts; `SourceFile.print` reads file at mdoc compile time, keeping docs and examples in lock-step.

## Pattern

```scala mdoc:passthrough
import docs.SourceFile

SourceFile.print("<module_name>-examples/src/main/scala/<package>/<ExampleFile>.scala")
```

Emits fenced Scala code block with file path as title.

## Critical: Import Form

Always import as `import docs.SourceFile` and call `SourceFile.print(...)`. **Do NOT** use `import docs.SourceFile._` with bare `print(...)`. Wildcard import shadows `Predef.print` inside mdoc sessions. Resulting compile error confuses because obvious culprit (`print`) appears defined.

✅ Good:

```scala mdoc:passthrough
import docs.SourceFile

SourceFile.print("schema-examples/src/main/scala/example/Person.scala")
```

❌ Bad (shadows `Predef.print`):

```scala mdoc:passthrough
import docs.SourceFile._

print("schema-examples/src/main/scala/example/Person.scala")
```

## Optional Parameters

| Parameter           | Type            | Default | Purpose                                          |
|---------------------|-----------------|---------|--------------------------------------------------|
| `lines`             | `Seq[(Int, Int)]` | none  | Include only specific 1-indexed line ranges     |
| `showLineNumbers`   | `Boolean`       | `false` | Render with line numbers in gutter              |
| `showTitle`         | `Boolean`       | `true`  | Show file path as code-block title              |

### Examples

Embed only lines 10–25 of file:

```scala mdoc:passthrough
SourceFile.print(
  "schema-examples/src/main/scala/example/Person.scala",
  lines = Seq((10, 25))
)
```

Embed whole file with line numbers, no title:

```scala mdoc:passthrough
SourceFile.print(
  "schema-examples/src/main/scala/example/Person.scala",
  showLineNumbers = true,
  showTitle = false
)
```

## Common Failures

| Symptom                                                    | Likely cause                                                  | Fix                                                                                  |
|------------------------------------------------------------|---------------------------------------------------------------|--------------------------------------------------------------------------------------|
| `not found: object docs`                                   | Docs subproject does not include `SourceFile` helper.         | Verify `docs/src/main/scala/docs/SourceFile.scala` exists; if not, copy it from project's docs scaffold. |
| `value print is not a member of Predef`                    | Used `import docs.SourceFile._`                               | Switch to `import docs.SourceFile`, call `SourceFile.print(...)` qualified.          |
| Embedded file appears empty                                | Wrong path, or file moved                                     | Run doc build (`sbt "docs/mdoc"`); mdoc reports missing path.                        |
| `lines = Seq(...)` shows truncated output                  | Range is exclusive of upper bound or off-by-one               | Range is inclusive on both ends; double-check line numbers in source file.           |

## When to Skip `SourceFile`

- Example is **fewer than ~10 lines** AND only place that snippet appears. Plain ```` ```scala mdoc ```` block is fine.
- Example is **synthetic** (illustrative only, not runnable companion file). Belongs inline.

Every other case (any "Running the Examples" section, any reused snippet, any example over ~10 lines): use `SourceFile.print`.
