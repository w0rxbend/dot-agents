# OAuth setup

OAuth for every Hermes-to-Box connection. It follows signed-in Box user's permissions and app scopes; it does not grant enterprise-wide access.

## Choose the OAuth account

Authorize Box account Hermes acts as. Narrower boundary: authorize account invited only to files, folders, or Hubs Hermes should access. Do not make it administrator merely to unlock exceptional operation.

Shared or background deployment: every user gets access of its one authorized Box account. Do not connect broader personal or administrator account. Before browser flow, confirm authorization browser is signed in as intended Box account.

Pick descriptive environment name, such as `hermes-box-oauth`. Do not overwrite or reauthorize existing environment until its identity is confirmed.

## Same-host interactive path

First resolve runner via [CLI guide](cli-guide.md). Ask whether Hermes runs on same computer as authorizing browser. Use this path only when user confirms (normally local setup); do not infer it from operating system alone.

Start one official local login without `--code`. Examples use `box`; swap in verified local runner only when Hermes installed and verified private CLI copy:

```bash
box login --default-box-app --name <ENVIRONMENT_NAME>
box users:get me --json --fields id,name,login
```

Flow creates and selects named environment. Run it in Hermes's terminal; do not ask user to copy runner command. Announce pending authorization, wait for CLI to finish, then check actor. Let CLI open authorization page and receive local callback. Do not use browser tools, inspect tabs, request resulting URL, navigate to Box, or ask user to paste code.

Callback server cannot bind port 3000, browser shows unusable authorization result, or callback never reaches waiting CLI: stop that login before retrying. Retry official app on supported ports `3001`, `4000`, `5000`, `8080`, one at a time; verify actor after each success:

```bash
box login --default-box-app --port 3001 --name <ENVIRONMENT_NAME>
```

Do not switch same-host setup to `--code` merely because port 3000 failed. Use `--code` only after supported local ports fail or user confirms authorization browser is on another host.

## Separate-host or headless path

Use only after user explicitly confirms Hermes is on remote host (such as VPS, container, or cloud VM), or headless with authorization browser on another computer. With resolved runner:

```bash
box login --default-box-app --code --name <ENVIRONMENT_NAME>
```

Open displayed URL with browser tool only if that tool controls human's authorization browser. Else show URL, pause while user signs in and approves, continue CLI's code-and-state prompts, verify actor. Do not use this path when same-host callback is available.

## Existing environments

CLI stores multiple named environments, one current default:

```bash
box configure:environments:list
box configure:environments:set-current <ENVIRONMENT_NAME>
box users:get me --json --fields id,name,login
```

Switch current environment only after approval, especially on shared or background installation; then verify actor. Identity is API-only or lacks normal Box login: do not use it for Hermes; connect normal Box account via OAuth.

## Custom OAuth Platform App

Use only when operation needs scope official CLI app lacks, such as **Manage webhooks**. In [Box Developer Console](https://app.box.com/developers/console), create or select Platform App with **User Authentication (OAuth 2.0)**; enable only required scopes. Never broaden scopes merely to avoid authorization error.

Same topology decision as official app. Same-host browser: add `http://localhost:3000/callback` as OAuth redirect URI in app's **Configuration** tab, save, then run:

```bash
box login --platform-app --port 3000 --name <ENVIRONMENT_NAME>
```

Port 3000 cannot bind: pick another free local port, add exact `http://localhost:<PORT>/callback` URI to Platform App, save, stop failed login, retry with matching `--port`. Unlike official app, custom Platform App may use any port whose exact callback URI is registered.

Remote or headless runtime with authorization browser on another computer: register same loopback callback URI, add `--code`:

```bash
box login --platform-app --code --port 3000 --name <ENVIRONMENT_NAME>
```

Before remote flow, explain browser may end on unreachable localhost page; this is expected. Resulting URL holds `code` and `state`, which waiting CLI requests. Ask user for only those two values, submit to existing process, verify actor. Do not inspect unrelated browser tabs or switch to local callback workflow on remote host.

Let CLI prompt for Client ID and Client Secret. Never ask user to paste Client Secret into chat or write it to Hermes configuration. Never give user unverified local-runner command to copy. Authenticate intended user in browser, verify actor. Keep administrator-only operations outside normal Hermes OAuth identity.

## Official links

- [Box CLI quick start](https://developer.box.com/guides/cli/quick-start/)
- [Box CLI headless login](https://developer.box.com/guides/cli/headless-login/)
- [OAuth 2.0 guide](https://developer.box.com/guides/authentication/oauth2/)
- [Box OAuth scopes](https://developer.box.com/guides/api-calls/permissions-and-errors/scopes/)
