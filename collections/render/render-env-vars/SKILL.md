---
name: render-env-vars
description: >-
  Configures environment variables, secrets, and env groups on Render. Use when
  the user needs to set env vars, wire secrets between services, create env
  groups, use generateValue, set sync: false, or troubleshoot missing or
  incorrect environment variable values in Blueprints or the Dashboard.
license: MIT
compatibility: Render Dashboard, CLI, or MCP tools
metadata:
  author: Render
  version: "1.0.0"
  category: configuration
---

# Environment Variables on Render

Config reaches services as **environment variables**, always **strings** at platform layer. Apps must parse numbers, booleans and structured data explicitly.

## When to Use This Skill

Use when users want to:

- Add, change or remove env vars or secrets
- Understand Dashboard vs Blueprint vs API/MCP flows
- Use **environment groups** for shared config
- Wire `fromDatabase`, `fromService`, `fromGroup`, `sync: false`, or `generateValue` in Blueprints
- Debug missing vars, secret files, precedence or platform-injected names

## Setting Variables

### Dashboard

- Add vars **individually** (name + value) or **in bulk** by pasting/uploading `.env`-style file.
- **Save options** typically include:
  - **Save and rebuild & deploy** — picks up build-time changes
  - **Deploy only** — runtime change without full rebuild (when applicable)
  - **Save only** — persist without triggering deploy

Dashboard edits suit fast iteration, or values repo should not carry.

### Blueprint (`render.yaml`)

Declare `envVars` per service: literals, generated secrets, sync-disabled prompts, or references to databases, other services, env groups.

### MCP / API

Automation sets vars on existing services (e.g. `update_environment_variables`). For CI, rotation, or syncing Dashboard state with external secret stores without committing secrets to Git. Never ask user to paste secret values into chat: secrets go via Dashboard, `sync: false` or `generateValue`; MCP only for non-secret values or values read from a secret store. Saving can trigger deploy: confirm with user before changing production vars.

## Secret Management

- **`sync: false`** — Dashboard prompts for value **only on initial Blueprint setup** (resource first created). **Blueprint updates** **ignore** it; file alone does not re-prompt. **Excluded from preview environments**; **invalid inside environment groups**.
- **`generateValue: true`** — Random **base64-encoded 256-bit** value generated at provision time. For passwords, signing keys, tokens that do not need human-chosen values.
- **Never commit real secrets** in `render.yaml` as plain `value:` entries. Prefer Dashboard, secret manager integration, `generateValue`, or `sync: false` with Dashboard entry.

### Secret files

- Store sensitive file content as **secret files**, not inline env strings. Appear as **plaintext files** under **`/etc/secrets/<filename>`**.
- **Combined limit**: **1 MB** total secret file payload per service or per linked env group (as applicable).
- **Docker**: secret files available under **`/etc/secrets/`** on running instance.

## Environment Groups

**Environment groups**: named variable sets linked to **multiple services**.

- **Precedence**: **service-level** vars **override** same-name vars from linked groups.
- **Multiple groups** on one service: **most recently created** group wins overlapping keys. Ordering **not documented as stable**; avoid relying on it. Use distinct names or consolidate groups.
- Groups can be **scoped to a project environment**, so staging and production differ without duplicating every service definition.

## Blueprint Wiring (Summary)

Full syntax, examples, edge cases: `references/wiring-reference.md`. Authoritative Blueprint docs: **render-blueprints** skill.

| Mechanism | Role |
|-----------|------|
| `value` | Hardcoded string (non-secret config only) |
| `generateValue: true` | Platform-generated secret |
| `sync: false` | Dashboard prompt on **initial** create only |
| `fromDatabase` | Inject DB fields (`connectionString`, `host`, `port`, `user`, `password`, `database`) |
| `fromService` | Key Value: `type: keyvalue` + properties; private/web: `host`, `hostport`, or `envVarKey` |
| `fromGroup` | Link all vars from named group |

## Platform-Injected Variables

Render sets **read-only** vars apps read at runtime (some also at build). Full list, build vs runtime availability, language version env vars, **WEB_CONCURRENCY** defaults: `references/platform-variables.md`.

## Runtime-Specific Defaults

Render and buildpacks may set per-language defaults (verify in service’s **Environment** tab); table in `references/platform-variables.md`.

Always bind HTTP servers to **`0.0.0.0`** and **`PORT`** (**default `10000`**; or stack’s documented port env) unless using static site or custom Docker entrypoint.

## Common Issues

1. **Everything is a string** — `DEBUG=false` is truthy in many parsers. Use explicit comparison or typed config loaders.
2. **`WEB_CONCURRENCY`** — Default changed for services **created after December 8, 2025**. Debugging worker counts: compare with older services, see `references/platform-variables.md`.
3. **Undocumented `RENDER_*` variables** — Names and semantics may change. Do not depend on undocumented injection for critical logic.
4. **Blueprint vs Dashboard drift** — Editing only `render.yaml` does not retroactively apply `sync: false` prompts on update. Env key merge strategy is easy to misunderstand; test in scratch service.
5. **Secret file paths** — Code must read **`/etc/secrets/<filename>`**. Wrong paths or missing mounts usually show as file-not-found at runtime.

## References

- `references/wiring-reference.md` — Complete Blueprint `envVar` wiring, YAML examples, precedence, edge cases
- `references/platform-variables.md` — Injected variables (build vs runtime), language versions, concurrency, reading vars from code

## Related Skills

- **render-blueprints** — Full Blueprint authoring, validation, multi-service layouts
- **render-deploy** — First deploy, repo requirements, MCP vs YAML
- **render-web-services** — Ports, health checks, scaling behavior tied to env-driven servers
