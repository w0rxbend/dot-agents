# Troubleshooting

Before changing approach, capture actor, object ID and type, exact command, status code, safe error body.

## First checks

```bash
box users:get me --json --fields id,name,login
box configure:environments:list
box files:get <FILE_ID> --json --fields id,name,parent
box folders:get <FOLDER_ID> --json --fields id,name,parent
box hubs --scope all --max-items 1000 --json
box hubs:get <HUB_ID> --json
```

Confirm actor, resource type, ID, resource-specific collaboration, app scopes, selected environment. Do not use folder `0` as access test: it cannot discover Hub and may not list every shared file or folder.

## Common failures

| Signal | Likely cause | Next action |
| --- | --- | --- |
| local OAuth reports `EADDRINUSE`, opens unusable result, or never returns to CLI | occupied or mismatched loopback callback port | stop waiting login process; official app: retry `3001`, `4000`, `5000`, then `8080`; custom app: register exact new callback URI before retrying |
| remote OAuth browser ends on unreachable localhost page | expected `--code` redirect or wrong topology | Hermes remote: return URL's `code` and `state` to waiting CLI; Hermes and browser on same host: stop, restart without `--code` |
| 401 or 403 | expired auth, missing scope, insufficient role | verify identity, reauthorize app, check folder role |
| shared file/folder absent from root or 404 | wrong actor, access-only/shared item, or missing file/folder collaboration | verify `users:get me`, then fetch known file/folder ID directly; only change collaboration after confirming target and actor |
| Hub absent from root or 404 | root listing cannot discover Hubs, wrong actor, or missing Hub collaboration | run `box hubs --scope all` and `box hubs:get <HUB_ID>`; verify Hub collaboration separately from underlying-file access |
| 409 | duplicate name, existing collaboration, metadata conflict | list parent/template; reuse or rename deliberately |
| 429 | rate limit | honor `Retry-After`, retry same request, reduce batch rate |
| Box AI access error | feature disabled, plan/unit restriction, unsupported content | explain limitation; offer metadata/search, sample, units, or approved fallback |

Two Hermes profiles or sessions seem to change each other's Box actor: private npm install does not isolate Box CLI environments for same OS user. List environments, verify actor, ask before switching. Linux plaintext credential fallback: warn about `~/.box` without reading or printing its credential files; recommend Secret Service/libsecret or isolated runtime user.

Do not diagnose missing content until identity and access are verified. Do not silently change actors, broaden sharing, or download confidential source files as workaround.
