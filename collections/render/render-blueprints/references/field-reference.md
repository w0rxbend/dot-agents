# Render Blueprint YAML Field Reference

Pair with `wiring-patterns.md`, `common-mistakes.md`, `preview-environments.md`.

## Conventions

- **`name`**: Stable resource identifier within Blueprint; used by `fromService`, `fromDatabase`, and Dashboard.
- **Required vs optional** varies by `type` and `runtime`; validate with JSON Schema (`https://render.com/schema/render.yaml.json`) and `render blueprints validate`.

---

## Common service fields (most types)

Applies broadly to `web`, `pserv`, `worker`, `cron`, and often `keyvalue` where relevant.

| Field | Notes |
|-------|--------|
| `name` | Unique among services in scope. |
| `type` | `web`, `pserv`, `worker`, `cron`, `keyvalue` (alias `redis`). **Immutable after create.** |
| `runtime` | `node`, `python`, `go`, `ruby`, `rust`, `elixir`, `docker`, `image`, `static`. **Immutable after create.** |
| `region` | Deploy region. |
| `plan` | Instance/plan slug. |
| `previewPlan` | Plan for preview instances; constraints vs primary `plan` (see preview doc). |
| `branch` | Git branch to deploy. |
| `rootDir` | Subdirectory for repo context. |
| `buildCommand` | Build step(s). |
| `startCommand` | Process to run (not used same way for `cron`; see below). |
| `preDeployCommand` | Command before deploy rollout. |
| `autoDeployTrigger` | `commit`, `checksPass`, or `off`. |
| `maxShutdownDelaySeconds` | 1–300; default **30**. |
| `healthCheckPath` | HTTP health check path (`web` / others where applicable). |
| `domains` | Custom domains list. |
| `envVars` | Env var objects (see [Env vars patterns](#env-vars-patterns)). |
| `buildFilter` | Limit builds to path changes (see [buildFilter](#buildfilter)). |
| `disk` | Persistent disk attachment (see [disk](#disk)). |
| `scaling` | Autoscaling settings (see [scaling](#scaling)). |
| `numInstances` | Manual instance count; interacts with `scaling`. |
| `registryCredential` | Private registry pulls (`image` runtime / images). |
| `dockerfilePath` | Dockerfile path (`docker` runtime). |
| `dockerContext` | Docker build context path. |
| `dockerCommand` | Override container command. |
| `previews` | Service-level preview overrides (e.g. `generation`). |

**Cron-specific**

| Field | Notes |
|-------|--------|
| `schedule` | Cron expression. |
| `buildCommand` / `startCommand` | Build + command run on schedule. |

**Private service (`pserv`)**

| Field | Notes |
|-------|--------|
| (common fields) | Consumers wire internal hostname/port via `fromService`. |

---

## Database fields (`databases`)

| Field | Notes |
|-------|--------|
| `name` | Blueprint identifier; **immutable** after creation. |
| `plan` | Database plan. |
| `previewPlan` | Plan for preview DB instances. |
| `previewDiskSizeGB` | Disk size for preview databases. |
| `postgresMajorVersion` | Major version; **immutable**. |
| `databaseName` | **Immutable.** |
| `user` | **Immutable.** |
| `region` | **Immutable.** |
| `diskSizeGB` | Storage size. |
| `storageAutoscalingEnabled` | Autoscale storage where supported. |
| `readReplicas` | Replica list; **empty list removes all replicas** (destructive). |
| `highAvailability` | HA enabled/disabled per plan support. |
| `ipAllowList` | CIDR restrictions. Omitted = all IPs allowed (credentials still required); `[]` = no external connections. Prefer `[]` or explicit CIDRs. |

---

## envVarGroups

| Field | Notes |
|-------|--------|
| `name` | Group identifier for `fromGroup`. |
| `envVars` | Same patterns as service `envVars` (`value`, `generateValue`, `fromDatabase`, `fromService`, etc.). |

**Constraint:** `sync: false` is **not valid** in env var groups (see wiring / mistakes docs).

---

## projects / environments

Projects group one or more **environments** (e.g. production, staging) under one Render project.

### Project fields

| Field | Notes |
|-------|--------|
| `name` | Project name (shown in Dashboard). |
| `environments` | List of environment blocks. |
| `envVarGroups` | Env var groups scoped to project (shared across its environments). |

### Environment fields

Each environment is self-contained resource set:

| Field | Notes |
|-------|--------|
| `name` | Environment key (e.g. `production`, `staging`). |
| `services` | Services in this environment (same schema as top-level `services`). |
| `databases` | Databases in this environment (same schema as top-level `databases`). |
| `envVarGroups` | Env var groups scoped to this environment. |

### Structural rules

- **No duplication:** Define each resource in **one** place: root level **or** inside single environment. Never both.
- **Cross-environment wiring:** `fromDatabase` and `fromService` resolve within same environment. Blueprint YAML does not support referencing resources across environments.
- **Environment isolation:** Professional and higher plans can isolate environments so services in different environments cannot reach each other over private network.
- **When to use projects:** Multiple services that belong together, staging/production parity, environment-scoped env groups. Single-service apps can use flat top-level lists instead.

---

## previews (top-level)

| Field | Notes |
|-------|--------|
| `generation` | `off` (default), `manual`, or `automatic`. |
| `expireAfterDays` | Delete preview environments after N days. |

---

## Env vars patterns

Each entry typically has `key` plus **one** of:

| Pattern | Purpose |
|---------|---------|
| `value` | Inline literal. |
| `generateValue` | Render generates random secret. |
| `sync` | `false` = do not sync from Blueprint after initial setup (secrets); see limitations in preview/group docs. |
| `fromDatabase` | Pull DB host, port, user, password, database, or `connectionString`. |
| `fromService` | Pull host/port/connection info from another service. |
| `fromGroup` | Import vars from `envVarGroup` by name. |

---

## scaling

| Field | Notes |
|-------|--------|
| `numInstances` | Fixed instance count when not autoscaling (or as baseline, depending on config). |
| `scaling.minInstances` | Floor for autoscaled services. |
| `scaling.maxInstances` | Ceiling for autoscaled services. |
| `scaling.targetCPUPercent` | CPU target for autoscaling. |
| `scaling.targetMemoryPercent` | Memory target for autoscaling. |

**Previews:** Autoscaling disabled; previews use **minInstances** behavior (see `preview-environments.md`).

---

## disk

Attached disk object on service:

| Field | Notes |
|-------|--------|
| `name` | Disk identifier. |
| `mountPath` | Mount path in instance filesystem. |
| `sizeGB` | Size in GB. |

---

## buildFilter

Limit which Git changes trigger builds:

| Field | Notes |
|-------|--------|
| `paths` | Include paths (glob / path rules per schema). |
| `ignoredPaths` | Excluded paths. |

**Sync behavior:** Omitting `paths` or `ignoredPaths` on sync can **replace** existing filters with empty lists. Always send full desired filter set.

---

## static site fields (`type: web`, `runtime: static`)

| Field | Notes |
|-------|--------|
| `buildCommand` | Build static assets. |
| `staticPublishPath` | Output directory for publishing. |
| `headers` | Custom response headers (rules/objects per schema). |
| `routes` | SPA / routing rules (e.g. fallback to `index.html`). |
| `buildFilter` | Path-based build triggers. |

---

## Key Value fields (`type: keyvalue`)

| Field | Notes |
|-------|--------|
| `name`, `region`, `plan` | Standard resource fields. |
| `maxmemoryPolicy` | Eviction policy string. |
| `ipAllowList` | **Required** for proper network restriction in typical setups. Do not omit unless you explicitly accept open access per product rules. |

---

## Schema

`https://render.com/schema/render.yaml.json` is source of truth for required fields and enum values; Render may add fields over time.
