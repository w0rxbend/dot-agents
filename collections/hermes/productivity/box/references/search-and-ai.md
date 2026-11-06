# Search, metadata, and Box AI

Use search and metadata before AI when they answer request deterministically. Semantic understanding of Box-hosted files: prefer Box AI. It keeps Box permissions, processes source files through Box's governed AI integration, keeps source-file bodies out of Hermes' coding-model context, scales without downloading every file. Do not block or criticize explicitly chosen alternative workflow.

## Search and metadata queries

```bash
box search "invoice ACME" --json --limit 25 --fields id,name,type,parent
box metadata-query enterprise_12345.contractTemplate <ANCESTOR_FOLDER_ID> \
  --query "status = :status" --query-param status=active --json
```

Search only returns content visible to current actor. Resolve IDs, confirm actor before treating empty results as missing files.

## Select a Box AI operation

| Need | Command |
| --- | --- |
| Answer, summarize, or compare 1 file | `ai:ask` with `single_item_qa` |
| Answer, summarize, or compare 2–25 selected files | `ai:ask` with `multiple_item_qa` |
| Q&A over more than 25 files | [Box Hubs](hubs.md) |
| Recurring Q&A over curated knowledge base | [Box Hubs](hubs.md) |
| Discover fields from exploratory prompt | `ai:extract` |
| Extract known schema without creating template | `ai:extract-structured --fields` |
| Extract against existing compatible template | `ai:extract-structured --metadata-template` |
| Write or rewrite text grounded in one file | `ai:text-gen` |

```bash
box ai:ask --items=id=<FILE_ID>,type=file \
  --prompt "Summarize the renewal obligations and dates." --json

box ai:extract --items=id=<FILE_ID>,type=file \
  --prompt "invoice_number, vendor, total, due_date" --json

box ai:extract-structured --items=id=<FILE_ID>,type=file \
  --fields "key=invoice_number,type=string,description=Invoice number" \
  --fields "key=total,type=float,description=Invoice total" --json

box ai:text-gen --items=id=<FILE_ID>,type=file \
  --prompt "Draft a concise customer update based on this file." --json
```

`ai:text-gen` supports exactly one item. Extraction endpoints return JSON; they do not automatically attach result to file. `--metadata-template` only when existing Box template is source of truth.

Do not use Hub for metadata extraction or text generation. Semantic Q&A over more than 25 files or reusable curated collection: read [Box Hubs](hubs.md), find existing Hub first, get approval before creating or populating one. User does not want Hub created: narrow candidates with search or metadata.

## Diagnose Box AI access

File passing `files:get` or search can still fail in Box AI if Box AI is unavailable for current OAuth identity or account. User can preview or download file but `ai:ask` returns `404 not_found`: do not immediately misdiagnose collaboration as missing. First verify actor and file permissions:

```bash
box users:get me --json --fields id,name,login
box files:get <FILE_ID> --json --fields id,name,permissions
```

Permissions and actor correct: verify Box AI is enabled and available for account or enterprise, custom Platform App (if used) has required AI scope, AI units are available. After changing application access, reauthorize intended OAuth identity; retry one file before batch. Do not use impersonation as fallback. Wrong identity selected: switch to intended OAuth environment only with approval; verify it first.

## Extract and persist file metadata

Extraction and persistence are separate operations. Unless user asks for preview, extraction request authorizes writing result back to Box; do not stop for redundant confirmation.

### Inspect schemas before extracting

1. Get file, its parent, and every attached metadata instance.
   ```bash
   box files:get <FILE_ID> --json --fields id,name,parent
   box files:metadata <FILE_ID> --json
   ```
2. List enterprise templates visible to current OAuth identity; get plausible schemas.
   ```bash
   box metadata-templates --json --fields templateKey,displayName,scope
   box metadata-templates:get <TEMPLATE_KEY> --scope enterprise --json
   ```
3. Compare every requested field with each candidate's meaning, field key, type. Use existing template only when one semantically appropriate template supports **all** requested fields. Do not attach partial or unrelated template merely to fit some values.

### Use a compatible existing template

Extract against template, then add its metadata instance or update existing one. Do not write absent, null, incompatible, or truncated values.

```bash
box ai:extract-structured --items=id=<FILE_ID>,type=file \
  --metadata-template="type=metadata_template,scope=enterprise,template_key=<TEMPLATE_KEY>" \
  --json

box files:metadata:create <FILE_ID> --scope enterprise --template-key <TEMPLATE_KEY> \
  --data "invoice_number=INV-001" --data "total=#1250.00" --json

box files:metadata:update <FILE_ID> --scope enterprise --template-key <TEMPLATE_KEY> \
  --replace "invoice_number=INV-001" --replace "total=#1250.00" --json

box files:metadata:get <FILE_ID> --scope enterprise --template-key <TEMPLATE_KEY> --json
```

Creating or adding typed metadata: float values need CLI's required `#` prefix. Box date fields: full ISO timestamps, such as `2025-03-29T00:00:00Z`. Compare every returned field with intended typed value. Report template key, metadata instance `$id`, file ID, file link.

### Work without a compatible template

Do not create metadata template. Box does not allow creation in `global` scope. Only Box Admin or Co-Admin granted template-management permission can create enterprise templates; custom templates may depend on account plan. Template administration is outside Hermes' normal OAuth content workflow.

Choose extraction by request, not by template availability:

- Known fields: `ai:extract-structured` with inline `--fields`; predictable typed JSON result without creating template.
- Exploratory or variable fields: `ai:extract` with precise prompt.

Persist flat scalar result in Box's built-in `global.properties` instance (schema-free, no template needed). Convert each value to lossless string, validate keys before writing, preserve unrelated existing properties. Instance missing: create it. Instance exists: `--replace` existing keys, `--add` new keys.

```bash
box files:metadata:get <FILE_ID> --scope global --template-key properties --json

box files:metadata:create <FILE_ID> --scope global --template-key properties \
  --data "invoice_number=INV-001" --data "total=1250.00" --json

box files:metadata:update <FILE_ID> --scope global --template-key properties \
  --replace "invoice_number=INV-001" --add "total=1250.00" --json

box files:metadata:get <FILE_ID> --scope global --template-key properties --json
```

`global.properties` is untyped; Metadata Query API cannot query it. Nested objects, tables, arrays, or any result whose JSON types must stay intact: write complete extraction response to UTF-8 JSON sidecar named `<SOURCE_NAME>.<FILE_ID>.metadata.json`, upload to source file's parent folder. Exact sidecar already exists for workflow: upload new version, not duplicate. Fetch upload, compare content or checksum with local JSON. Report source and sidecar IDs and links.

User explicitly requires reusable typed enterprise metadata: explain administrator must create compatible enterprise template separately. Do not elevate connected account or switch to administrator identity. Meanwhile preserve extraction in `global.properties` or JSON sidecar; never silently truncate or discard fields.

### File descriptions are not metadata fallback

**Hard rule:** Never use file description as automatic substitute for extracted metadata. Safe limit: 255 characters; Box can truncate longer descriptions. Use `box files:update --description` only when user explicitly requests description: first verify complete text fits, then read back and compare with intended value.

## Confidentiality and AI units

Box AI responses returned to Hermes can still contain confidential information. Do not claim no third-party model provider is involved or that content can never be used for training; follow Box's current trust and plan documentation.

Before first Box AI request, explain: Box AI must be enabled, calls consume AI units, answers stay constrained by actor's permissions. Material batch: state file count, ask confirmation. Do not promise unit balance or per-call cost unless Box exposes it for current account.

Box AI unavailable or out of units: offer existing metadata/search, smaller sample, enabling units, or explicit approval for local/external analysis. Never silently fall back to downloading files for external model.

## Scale

Use `--bulk-file-path` where command supports it. Hundreds of files: inventory first, sample schema, confirm unit-consuming scope, follow [Bulk operations](bulk-operations.md). Recurring, high-throughput extraction: evaluate Box Extract; do not simulate folder-wide workflow through repeated downloads.

## Sources

- [Box AI API](https://developer.box.com/ai/box-ai-api/)
- [Structured metadata extraction](https://developer.box.com/guides/box-ai/ai-tutorials/extract-metadata-structured/)
- [Metadata template scopes](https://developer.box.com/guides/metadata/scopes/)
- [Global metadata query limitation](https://developer.box.com/guides/metadata/queries/limitations/)
- [Box AI trust](https://www.box.com/ai/trust/)
- [AI units and plan access](https://support.box.com/hc/en-us/articles/45612941554835-Expanded-AI-API-Access-and-AI-Units-for-Business-Business-Plus-and-Enterprise-Plans)
- [Metadata template permissions](https://developer.box.com/guides/metadata/templates/create/)
