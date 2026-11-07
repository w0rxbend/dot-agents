# Bulk operations

For more than a handful of files. Pick OAuth actor before inventory; workflow only processes content that identity can access.

## Workflow

```
Inventory → classify if needed → plan → confirm → execute → verify → report
```

## Inventory and plan

```bash
box folders:items <FOLDER_ID> --json --max-items 1000 --fields id,name,type,parent
```

Paginate until every item is counted. Record IDs, names, types, target folder IDs, completed-ID log. Before broad moves, access changes, or AI use, get approval on scope and ambiguous cases.

## Classify content

Prefer deterministic filename, extension, existing-metadata rules. Semantic classification: Box AI, not file-body downloads:

```bash
box ai:ask --items=id=<FILE_ID>,type=file \
  --prompt "Classify as invoice, receipt, contract, report, or other." --json
```

Known fields: `ai:extract-structured`. Variable fields: `ai:extract`. Sample small representative set before large batch. Disclose Box AI unit use; confirm before material AI batch.

## Execute and recover

```bash
box folders:create <PARENT_ID> "Category" --json --fields id,name
box files:move <FILE_ID> <TARGET_FOLDER_ID> --json --fields id,name,parent
```

Run ordered CLI mutations serially; log each success or failure. `409`: find and reuse existing target. `429`: honor `Retry-After`, retry same request. Resume from `inventory minus completed IDs`; do not restart blindly.

Use documented `--bulk-file-path` workflow where command supports it. Bounded SDK concurrency only when application owns retries, idempotency, rate-limit handling.

## Verify and report

List source and each destination folder; compare IDs and counts with plan. Report links to source, destinations, exceptions. Do not dump hundreds of item links unless user asks for manifest.
