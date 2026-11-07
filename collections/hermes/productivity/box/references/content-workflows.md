# Content workflows

After resolving item, use IDs, not paths. Target invisible to current OAuth identity: verify exact item ID, ask owner to invite that identity to intended file, folder, or Hub.

## Browse and create folders

```bash
box folders:get <FOLDER_ID> --json --fields id,name,parent,item_collection
box folders:items <FOLDER_ID> --json --max-items 100 --fields id,name,type
box folders:create <PARENT_ID> "Customer-123" --json --fields id,name,parent
```

Duplicate name in one parent returns `409`. Reuse existing folder ID; do not retry blindly.

## Verify a shared file or folder

File or folder invite to current OAuth identity: take ID from its Box URL if available, fetch that exact item. Absence from folder `0` does not prove access failed; it is only that identity's root listing. Only name known: resolve ID via Box search, then fetch item:

```bash
box search "Quarterly plan" --json --limit 20 --fields id,name,type,parent
box files:get <FILE_ID> --json --fields id,name,parent
box folders:get <FOLDER_ID> --json --fields id,name,parent
```

Hub invite: see [Box Hubs](hubs.md). Hubs are not files or folders; discovery is separate.

## Upload, download, and version files

```bash
box files:upload ./artifact.pdf --parent-id <FOLDER_ID> --json --fields id,name,size
box files:get <FILE_ID> --json --fields id,name,size,sha1,parent
box files:download <FILE_ID> --destination . --save-as local-copy.pdf
box files:versions:upload <FILE_ID> ./updated.pdf --json --fields id,name,sha1
box files:versions:list <FILE_ID> --json
box files:versions:download <FILE_ID> <VERSION_ID> --destination . --save-as older.pdf
```

Download source bytes only when task needs local editing or user explicitly approves external analysis. Prefer new version over replacing unrelated file by name.

## Create native Box Notes

Box Note request: create native note from Markdown via `box request`, not uploaded text file named `.boxnote`. Exact request and verification command: [REST API fallback](rest-api.md). Create immediately when destination is explicit or unambiguously actor's root; otherwise ask which folder.

## Rename, tag, and move

```bash
box files:update <FILE_ID> --name "Renamed.pdf" --json --fields id,name
box files:update <FILE_ID> --description "Updated by Hermes" --tags "reviewed,2026" --json
box files:move <FILE_ID> <NEW_PARENT_ID> --json --fields id,name,parent
box folders:move <FOLDER_ID> <NEW_PARENT_ID> --json --fields id,name,parent
```

Read back item or its parent after every write. Moving folder moves its contents; confirm broad moves first.

## File descriptions

Safe file-description limit: 255 characters; Box can truncate longer values. Never use description as fallback for extracted metadata. Set one only when user explicitly asks: verify complete text fits before writing, then fetch file and compare returned description with intended value. Persist extracted results as metadata or JSON sidecar instead; see [Search and AI](search-and-ai.md).

## Collaborate and share

```bash
box collaborations:create <FOLDER_ID> folder --role editor --login collaborator@example.com --json
box shared-links:create <FILE_ID> file --access company --json
box shared-links:create <FOLDER_ID> folder --access open --json
```

Use narrowest collaboration role. Creating or widening shared link changes access: require explicit confirmation.

## Navigate without changing permissions

Report these links for items caller already knows; they do not create shared link:

- File: `https://app.box.com/file/<FILE_ID>`
- Folder: `https://app.box.com/folder/<FOLDER_ID>`

Include item ID with link. Human cannot open item visible only to connected Box account: say so; do not create link with broader access.

## Read and write metadata

```bash
box files:metadata:get <FILE_ID> --scope global --template-key properties --json
box files:metadata:create <FILE_ID> --scope global --template-key properties \
  --data invoice_id=INV-001 --json
```

`global.properties` is Box's built-in schema-free metadata instance; no template creation required. Not reusable typed enterprise schema; Metadata Query API cannot use it. Read all existing metadata instances before writing to preserve unrelated properties. Metadata extracted from document content: [Search and AI](search-and-ai.md). Do not use partial, unrelated, or incomplete enterprise template.
