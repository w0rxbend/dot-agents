# Box CLI guide

Run Box commands via Hermes' `terminal` tool. Prefer documented commands; use help only if needed option is missing here or installed CLI rejects syntax.

## Use one command runner

Resolve one runner before any Box operation:

1. If `box` already resolves in runtime shell (`command -v box` on macOS/Linux, `Get-Command box` in PowerShell), use it as-is, wherever Hermes or Box CLI was installed.
2. Else install and verify isolated CLI in writable, persistent Hermes runtime directory, preferably `tools/box-cli` under Hermes home. `HERMES_HOME` is optional; unset means platform default (`~/.hermes` on macOS/Linux, `%LOCALAPPDATA%\hermes` on Windows).
3. Not writable: ask for writable persistent runtime directory. Never assume Hermes's source checkout, global npm prefix, or user home is writable. Nonstandard existing CLI not on `PATH`: ask for its executable path; do not scan machine.

Use `npm exec --prefix` only after Hermes installed and verified that exact local copy. Run each install block as one terminal call; record printed absolute prefix, reuse that literal path. Never rely on shell variable surviving separate Hermes terminal call. Never give user unverified `npm exec --prefix` command.

Box CLI 4 needs Node.js 18 or newer. First run `node --version` and `npm --version` in runtime and shell Hermes will use. Node missing or major version below 18: ask approval to install or activate supported Node by environment's normal mechanism, rerun both checks. npm unavailable or filesystem not writable: ask for runtime-appropriate install or writable Hermes home. Never assume system package manager, desktop, or elevated privileges.

On macOS/Linux:

```bash
node --version
npm --version
BOX_CLI_HOME="${HERMES_HOME:-$HOME/.hermes}/tools/box-cli"
mkdir -p "$BOX_CLI_HOME"
npm install --prefix "$BOX_CLI_HOME" @box/cli@4.10.1
npm exec --prefix "$BOX_CLI_HOME" -- box --version
cd "$BOX_CLI_HOME" && pwd -P
```

On Windows PowerShell:

```powershell
node --version
npm --version
$boxCliHome = Join-Path $(if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA "hermes" }) "tools\box-cli"
New-Item -ItemType Directory -Force -Path $boxCliHome | Out-Null
npm install --prefix $boxCliHome @box/cli@4.10.1
npm exec --prefix $boxCliHome -- box --version
Resolve-Path $boxCliHome
```

Version is pinned; bump only to reviewed release, keep generated `package-lock.json`. Keep resolved runner for whole task. Hermes installed local copy: replace leading `box` in every example with `npm exec --prefix` runner below. Else use already-resolved `box`.

Other references use `bash` fences and POSIX `\` continuations. PowerShell: same Box arguments, on one line or with backtick continuation. PowerShell variables only in PowerShell examples.

On macOS/Linux:

```bash
npm exec --prefix "<VERIFIED_ABSOLUTE_PREFIX>" -- box
```

On Windows PowerShell:

```powershell
npm exec --prefix "<VERIFIED_ABSOLUTE_PREFIX>" -- box
```

Example on macOS/Linux:

```bash
npm exec --prefix "<VERIFIED_ABSOLUTE_PREFIX>" -- box users:get me --json --fields id,name,login
```

No global npm install, no `sudo`, no change to npm's global prefix or `PATH`.

## Check identity and control output

On macOS/Linux:

```bash
command -v box
box --version
box users:get me --json --fields id,name,login
box folders:items 0 --json --max-items 20 --fields id,name,type
```

On Windows PowerShell:

```powershell
Get-Command box -ErrorAction SilentlyContinue
box --version
box users:get me --json --fields id,name,login
box folders:items 0 --json --max-items 20 --fields id,name,type
```

`--json`: machine-readable output. `--fields`: only needed fields. Folder `0` is actor's root, not full access inventory: do not reject shared file or folder from its listing; never use it to discover Box Hubs.

## Environments and actors

```bash
box configure:environments:list
box configure:environments:set-current <ENVIRONMENT_NAME>
box users:get me --json --fields id,name,login
```

CLI has one current environment. Confirm before switching, then verify actor. Do ordinary Hermes work as that environment's OAuth identity; do not impersonate another user.

Isolated npm install isolates executable, not authenticated environments. Box CLI stores environments and tokens per runtime OS user: platform credential store if available, else `~/.box`. Hermes profiles and concurrent sessions under one OS user can therefore share current Box environment. Warn about this at setup; verify actor before every task. Explain that switching environment can affect other Hermes sessions and ordinary Box CLI use under that OS account.

Linux secure storage depends on Secret Service/libsecret. CLI reports plaintext fallback: warn credentials may be stored in `~/.box/box_environments.json` and token-cache files. Do not read or print those files. Before production use, recommend supported Secret Service/libsecret package or isolated runtime user. Do not assume package manager; do not require extra confirmation merely to deliver warning.

## Pagination and search

```bash
box folders:items <FOLDER_ID> --json --max-items 100 --fields id,name,type
box search "quarterly review" --json --limit 20 --fields id,name,type,parent
box metadata-query enterprise_12345.contractTemplate <ANCESTOR_FOLDER_ID> \
  --query "status = :status" --query-param status=active --json
```

Paginate inventories fully before bulk work. Metadata queries require template scope/key and ancestor folder ID.

## REST escape hatch

No dedicated command: `box request` keeps configured auth; do ordinary requested operation. Do not stop to ask merely because it uses REST. Endpoint-specific bodies and headers: [REST API fallback](rest-api.md).

```bash
box request /files/<FILE_ID> --json
box request /files/<FILE_ID> -X PUT --body '{"name":"renamed.pdf"}' --json
box request /folders -X POST --body '{"name":"New folder","parent":{"id":"0"}}' --json
```

SDK or raw HTTP only when CLI is unavailable or application code needs direct REST.

## Batch inputs and mutations

Many commands accept `--bulk-file-path` (CSV or JSON). Use only after inventorying target set and confirming material writes. Ordered moves, version updates, other recoverable mutations: keep operation log, process serially. Bounded concurrency in application SDK code only when its retry and rate-limit behavior is explicit.

## Confirmation rules

- Confirm before deletes, access or identity changes, broad moves, or ambiguous target.
- Confirm scope before AI-unit-consuming bulk request.
- Do not pass `--yes` unless user already approved exact operation.
