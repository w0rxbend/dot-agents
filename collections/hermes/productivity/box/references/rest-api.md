# REST API fallback

`box request` covers operations without dedicated CLI subcommand, reusing configured Box identity. Continue ordinary requested work without asking user to choose REST fallback. Confirm only for deletes, access or identity changes, broad or costly batches, or ambiguous target or scope. Direct REST only when CLI is unavailable or application code needs raw endpoint an SDK cannot cover.

REST does not bypass Box metadata safety rules: inspect metadata instances and existing schemas first, never create or change metadata template, retrieve and compare instance after every write. Never use file description as implicit metadata fallback.

## CLI request escape hatch

```bash
box request /files/<FILE_ID> --json
box request /files/<FILE_ID> -X PUT --body '{"name":"renamed.pdf"}' --json
box request /folders -X POST --body '{"name":"New folder","parent":{"id":"0"}}' --json
```

## Create a native Box Note

Box Note request: create native note with Box Notes API; do not upload plain text with `.boxnote` suffix. Use intended parent folder (`0` only when user's target is unambiguously their root), then fetch returned file to verify:

```bash
box request /notes/convert -X POST \
  --header "box-version: 2026.0" \
  --body '{"content":"# Hello world\n\nhello world","content_format":"markdown","parent":{"id":"0"},"name":"hello-world"}' \
  --json
box files:get <RETURNED_FILE_ID> --json --fields id,name,type,parent
```

`content` is Markdown, limited to 1 MB. Report returned file ID and normal Box file link.

## OAuth identity boundary

`box request` uses selected OAuth CLI environment; it does not bypass that user's Box permissions. CLI unavailable: OAuth-authorized SDK client per [SDK development](sdk-development.md). Never echo, log, or commit OAuth tokens or client secrets.

## Sources

- [Box API reference](https://developer.box.com/reference/)
- [Box Notes API: create a note from Markdown](https://developer.box.com/guides/box-notes/convert-markdown/)
- [OAuth 2.0](https://developer.box.com/guides/authentication/oauth2/)
