---
name: docs-data-type-list-members
description: Use when extracting and categorizing public members from a Scala data type for documentation completeness checks.
---

# List Data Type Members

Parses Scala source file, prints public members of named type, grouped into sections for auditing.

Paths: `<this-skill-dir>` is this skill's directory (where this file lives).

```bash
scala-cli <this-skill-dir>/extract-members.scala \
  -- <source-file> [<type-name>]
```

Run with `--help` for full usage.

**Default text output sections** (each preceded by header line ending in `===`):
- **Companion Object Members** — factory methods, utilities, static operations
- **Public API** — instance methods on type itself
- **Inherited Methods** — methods from parent classes/traits (when cross-file analysis available)

Excludes private/protected members and internal helpers.

## JSON Output

For machine-readable output (piping into other scripts, filtering with `jq`), pass `--json`:

```bash
scala-cli <this-skill-dir>/extract-members.scala \
  -- --json <source-file> [<type-name>] | jq '.publicApi'
```

JSON schema:

```json
{
  "sourceFile": "<path>",
  "typeName":   "<name> or null",
  "companion":  ["..."],
  "publicApi":  ["..."],
  "inherited":  []
}
```

**Exit codes:**

| Code | Meaning                                               |
|------|-------------------------------------------------------|
| `0`  | Success — at least one public member extracted.       |
| `1`  | No public members found in file or named type.        |
| `2`  | Invocation error (missing arguments, file not found). |

Pipe output into `/docs-report-method-coverage` to check whether all members appear in reference doc.
