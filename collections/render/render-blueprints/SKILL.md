---
name: render-blueprints
description: >-
  Authors and validates render.yaml Blueprints for Render infrastructure. Use
  when the user needs to write or edit a render.yaml, wire services together
  with fromDatabase/fromService/fromGroup, set up projects and environments
  for multi-service apps, configure preview environments, validate against
  the schema, or fix immutable field errors. Trigger terms: render.yaml,
  Blueprint, IaC, fromDatabase, fromService, envVarGroups, previews, projects,
  environments.
license: MIT
compatibility: >-
  Git repository on GitHub, GitLab, or Bitbucket for Blueprint sync. Render CLI
  v2.7.0+ recommended for `render blueprints validate`. IDEs can validate
  against the public JSON Schema URL below.
metadata:
  author: Render
  version: "1.0.0"
  category: configuration
---

# Render Blueprints (render.yaml)

Blueprints define Render infrastructure as YAML, usually `render.yaml` at repo root.

## When to Use

Use when user:

- Creates or edits `render.yaml` / Blueprint
- Wires databases, private services, or Key Value into app env vars
- Groups services with **projects** and **environments**
- Configures **preview environments** for pull requests
- Validates YAML against Render’s schema or CLI
- Asks what can or cannot change after creation

End-to-end deploy flows and MCP/CLI operations: **render-deploy**. Env var strategy outside Blueprint syntax: **render-env-vars**. Docker-specific Blueprint fields: **render-docker**.

## Blueprint Structure

### Top-level keys

| Key | Purpose |
|-----|---------|
| `services` | Web, worker, cron, private service, Key Value, static (via `web` + `runtime: static`) |
| `databases` | Managed PostgreSQL instances |
| `envVarGroups` | Reusable env var sets for services |
| `projects` | Optional grouping with `environments` and service lists |
| `previews` | PR preview environment defaults |

Resources are **ungrouped** or in **environment-scoped** lists, depending on whether you use projects model. Avoid duplicating one logical resource in multiple places (see `references/common-mistakes.md`).

### Schema and IDE validation

- **JSON Schema URL:** `https://render.com/schema/render.yaml.json`
- Map `render.yaml` to that schema in editor for completions and diagnostics.

### Minimal example: web + PostgreSQL

```yaml
databases:
  - name: mydb
    plan: basic-256mb
    region: oregon

services:
  - type: web
    name: api
    runtime: node
    region: oregon
    plan: starter
    buildCommand: npm ci && npm run build
    startCommand: npm start
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: mydb
          property: connectionString
```

## Service Types

| `type` | Role |
|--------|------|
| `web` | Public HTTP service (`runtime: static` for static sites) |
| `pserv` | Private service (internal HTTP/TCP; not public) |
| `worker` | Long-running background process |
| `cron` | Scheduled job (`schedule` required) |
| `keyvalue` | Managed Key Value (Redis-compatible); Blueprints accept alias **`redis`** |

## Runtimes

Common `runtime` values: **`node`**, **`python`**, **`go`**, **`ruby`**, **`rust`**, **`elixir`**, **`docker`**, **`image`**, **`static`**.

- **`docker`**: Build from `Dockerfile` (see `dockerfilePath`, `dockerContext`, `dockerCommand`).
- **`image`**: Run prebuilt container image (registry + optional `registryCredential`).
- **`static`**: Static site; needs `staticPublishPath` and build output paths (see references).

## Cross-Service Wiring

`envVars` entries (and groups) can pull values from other resources instead of hardcoded secrets.

### `fromDatabase`

Reference database in `databases:` by `name`. Properties:

- `connectionString`, `host`, `port`, `user`, `password`, `database`

### `fromService`

Reference service by `name`. Typical properties:

- `host`, `port`, `hostport`, `connectionString`, `envVarKey`

Valid properties depend on target service type (e.g. Key Value vs `pserv`).

### `fromGroup`

Attach shared vars from `envVarGroups` by group `name`.

### Other env var keys

- **`value`**: Literal string.
- **`generateValue`**: Render generates random secret (password/API key).
- **`sync`**: Set `sync: false` for secrets that should not sync from repo on each update (see wiring reference edge cases).

Full patterns and combinations: `references/wiring-patterns.md`.

## Projects and Environments

Single-service apps: flat top-level `services`/`databases` is fine. Use projects for multiple services, staging/production separation, or environment-scoped env groups.

```yaml
projects:
  - name: my-app
    environments:
      - name: production
        services:
          - type: web
            name: api
            runtime: node
            plan: standard
            buildCommand: npm ci && npm run build
            startCommand: npm start
            envVars:
              - key: DATABASE_URL
                fromDatabase:
                  name: db
                  property: connectionString
              - key: REDIS_URL
                fromService:
                  type: keyvalue
                  name: cache
                  property: connectionString
              - key: API_SECRET
                sync: false

          - type: worker
            name: jobs
            runtime: node
            plan: starter
            buildCommand: npm ci
            startCommand: node worker.js
            envVars:
              - key: DATABASE_URL
                fromDatabase:
                  name: db
                  property: connectionString
              - key: REDIS_URL
                fromService:
                  type: keyvalue
                  name: cache
                  property: connectionString

          - type: keyvalue
            name: cache
            plan: starter
            maxmemoryPolicy: noeviction
            ipAllowList: []  # internal only; add specific CIDRs only if external access is needed

        databases:
          - name: db
            plan: starter
```

Key rules:

- Each environment owns its `services` and `databases` lists.
- Do not define same resource at both root level and inside an environment.
- `envVarGroups` can be scoped to one project environment or shared across workspace.
- Environment isolation (Professional+) can block cross-environment private network traffic.

## Preview Environments

Top-level `previews` controls PR previews:

- **`previews.generation`**: `off` (default), `manual`, or `automatic`
- **`previews.expireAfterDays`**: Auto-delete preview stacks after N days

Services can override preview behavior (e.g. service-level `previews.generation`). Limitations (autoscaling, `sync: false` vars, `previewPlan` / flexible instance constraints): see `references/preview-environments.md`.

## Validation

```bash
RENDER_CLI_DISABLE_ANALYTICS=1 render blueprints validate
```

Render CLI sends usage analytics by default; prefix every `render` command with `RENDER_CLI_DISABLE_ANALYTICS=1`. Needs **Render CLI v2.7.0+**. Run from repo root, or pass path options your CLI version supports. Fix schema and semantic errors before merging Blueprint changes.

## Immutable Fields

**CRITICAL:** Some fields cannot change after creation. Edits may be rejected or need replacement resources.

### Services

- **`type`**: Cannot change (e.g. web → worker).
- **`runtime`**: Cannot change (e.g. node → docker).

### Databases

Cannot change after creation:

- `name` (logical Blueprint/database identifier here)
- `databaseName`
- `user`
- `region`
- `postgresMajorVersion`

Plan other fields (disk, HA, replicas) carefully up front. Check Render docs for which fields scale vs need recreation.

## Key Fields (Quick Map)

| Area | Fields |
|------|--------|
| Plans | `plan`, `previewPlan` (previews), database `plan` |
| Build/run | `buildCommand`, `startCommand`, `preDeployCommand`, `rootDir` |
| Deploy | `autoDeployTrigger`: `commit`, `checksPass`, or `off` |
| Lifecycle | `maxShutdownDelaySeconds`: 1–300, default **30** |
| HTTP | `healthCheckPath`, `domains` |
| Storage | `disk` (`name`, `mountPath`, `sizeGB`) |
| Scale | `scaling` / `numInstances` (see references) |
| Monorepo | `buildFilter` (`paths`, `ignoredPaths`) |
| Docker | `dockerfilePath`, `dockerContext`, `dockerCommand`, `registryCredential` |

Deprecated names to avoid: `env` (use `runtime`), `redis` (use `keyvalue`), `autoDeploy` (use `autoDeployTrigger`), `pullRequestPreviewsEnabled` (use `previews.generation`). Details: `references/common-mistakes.md`.

## References

| Document | Contents |
|----------|----------|
| `references/field-reference.md` | YAML fields by service type, database, groups, projects, previews, scaling, disk, static, Key Value |
| `references/wiring-patterns.md` | `fromDatabase` / `fromService` / `fromGroup` examples, `sync: false`, `generateValue`, combinations |
| `references/common-mistakes.md` | Branch + previews, `buildFilter`, replicas, duplicates, preview plans, wiring mistakes |
| `references/preview-environments.md` | `previews.generation`, expiry, overrides, `previewPlan`, disks, PR workflow |

## Related Skills

- **render-deploy** — Deploy flows, Blueprint vs direct create, MCP/deeplinks
- **render-env-vars** — Env var strategy, secrets, Dashboard vs Blueprint
- **render-docker** — Dockerfile-backed services, image runtime nuances
