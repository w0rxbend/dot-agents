---
name: docs-report-method-coverage
description: Use when checking if documentation covers all public members of a Scala data type.
---

# Report Method Coverage

Cross-checks the public members of a Scala data type against a reference doc page and reports any members that are not documented.

Paths: `<this-skill-dir>` is this skill's own directory (where this file lives); `<docs-data-type-list-members-skill-dir>` is the directory of the `docs-data-type-list-members` skill from the same zio-skills set (installed next to this one, e.g. as `zio-skills--docs-data-type-list-members`).

```bash
bash <this-skill-dir>/check-method-coverage.sh \
  <TypeName> <doc-file.md> [members-file]
```

Members may be supplied via `[members-file]` or piped on stdin (typically from the `docs-data-type-list-members` script):

```bash
scala-cli <docs-data-type-list-members-skill-dir>/extract-members.scala -- Reader.scala Reader \
  | bash <this-skill-dir>/check-method-coverage.sh \
      Reader docs/reference/reader.md
```

Run the script with `--help` for the full usage.

**Exit codes:**

| Code | Meaning                                                              |
|------|----------------------------------------------------------------------|
| `0`  | Full coverage — every public member is documented.                   |
| `1`  | One or more members are missing from the documentation.              |
| `2`  | Invocation error (missing arguments, file not found, no input).      |

## JSON Output

For machine-readable output (e.g., CI gates, downstream filtering with `jq`), pass `--json`:

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

Categories with no input members are omitted from the `categories` object. Exit codes are unchanged in JSON mode.
