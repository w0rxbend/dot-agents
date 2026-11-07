---
name: docs-report-method-coverage
description: Use when checking if documentation covers all public members of a Scala data type.
---

# Report Method Coverage

Cross-checks public members of Scala data type against reference doc page. Reports members not documented.

Paths: `<this-skill-dir>` is this skill's own directory (where this file lives). `<docs-data-type-list-members-skill-dir>` is directory of `docs-data-type-list-members` skill from same zio-skills set, installed next to this one (e.g. as `zio-skills--docs-data-type-list-members`).

```bash
bash <this-skill-dir>/check-method-coverage.sh \
  <TypeName> <doc-file.md> [members-file]
```

Supply members via `[members-file]` or pipe on stdin (typically from `docs-data-type-list-members` script):

```bash
scala-cli <docs-data-type-list-members-skill-dir>/extract-members.scala -- Reader.scala Reader \
  | bash <this-skill-dir>/check-method-coverage.sh \
      Reader docs/reference/reader.md
```

Run script with `--help` for full usage.

**Exit codes:**

| Code | Meaning                                                         |
|------|-----------------------------------------------------------------|
| `0`  | Full coverage: every public member documented.                  |
| `1`  | One or more members missing from documentation.                 |
| `2`  | Invocation error (missing arguments, file not found, no input). |

## JSON Output

For machine-readable output (CI gates, downstream filtering with `jq`), pass `--json`:

```bash
bash <this-skill-dir>/check-method-coverage.sh \
  --json Reader docs/reference/reader.md members.txt | jq '.fullCoverage'
```

JSON schema:

```json
{
  "typeName":    "Reader",
  "docFile":     "docs/reference/reader.md",
  "categories": {
    "companion": { "total": 5, "documented": 4, "missing": ["foo"] },
    "publicApi": { "total": 12, "documented": 12, "missing": [] }
  },
  "fullCoverage": false
}
```

Categories with no input members omitted from `categories` object. Exit codes unchanged in JSON mode.
