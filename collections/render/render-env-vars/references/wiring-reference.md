# Blueprint environment variable wiring

Pair with **render-blueprints** skill for service structure, previews and validation.

## Field summary

| Field | Meaning |
|-------|---------|
| `key` | Environment variable name |
| `value` | Hardcoded string (avoid secrets) |
| `generateValue: true` | Platform generates **base64 256-bit** random string |
| `sync: false` | Dashboard prompt on **initial Blueprint create only**; ignored on updates; not for previews or env groups |
| `fromDatabase` | Pull fields from Postgres (or other supported) database resource |
| `fromService` | Pull connection details from another Render service |
| `fromGroup` | Import all variables from environment group by name |

## `value` — hardcoded string

```yaml
envVars:
  - key: LOG_LEVEL
    value: info
  - key: APP_ENV
    value: production
```

Use only for non-sensitive config. Never commit API keys or passwords this way.

## `generateValue` — random secret

```yaml
envVars:
  - key: SESSION_SECRET
    generateValue: true
```

Render creates **base64-encoded 256-bit** value at provision time. Rotation usually needs manual Dashboard edit or API update, depending on workflow.

## `sync: false` — Dashboard-supplied on first create

```yaml
envVars:
  - key: STRIPE_SECRET_KEY
    sync: false
```

- Prompt appears in Dashboard when Blueprint **first** creates service.
- **Updates** to `render.yaml` do **not** re-trigger prompt for existing services.
- **Excluded** from preview environment behavior for protected values (treat as operator-managed).

## `fromDatabase` — database properties

Reference database defined in same Blueprint (name must match resource’s `name`).

Available **properties** (use subset app needs):

- `connectionString`
- `host`
- `port`
- `user`
- `password`
- `database`

```yaml
databases:
  - name: mydb
    databaseName: myapp
    user: myuser

services:
  - type: web
    name: api
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: mydb
          property: connectionString
      - key: PGHOST
        fromDatabase:
          name: mydb
          property: host
      - key: PGPORT
        fromDatabase:
          name: mydb
          property: port
      - key: PGUSER
        fromDatabase:
          name: mydb
          property: user
      - key: PGPASSWORD
        fromDatabase:
          name: mydb
          property: password
      - key: PGDATABASE
        fromDatabase:
          name: mydb
          property: database
```

## `fromService` — Key Value (Redis-style)

Use `type: keyvalue` with one of: `connectionString`, `host`, `port`, `hostport`.

```yaml
services:
  - type: keyvalue
    name: cache
    ipAllowList: []

  - type: web
    name: api
    envVars:
      - key: REDIS_URL
        fromService:
          name: cache
          type: keyvalue
          property: connectionString
      - key: REDIS_HOST
        fromService:
          name: cache
          type: keyvalue
          property: host
      - key: REDIS_PORT
        fromService:
          name: cache
          type: keyvalue
          property: port
      - key: REDIS_HOSTPORT
        fromService:
          name: cache
          type: keyvalue
          property: hostport
```

## `fromService` — private service or web service

For **private services** (`pserv`) or **web** services, typical properties:

- `host` — internal hostname
- `hostport` — `host:port` combined

Or reference **specific env var** exposed by other service with `envVarKey` (when supported for that link type; confirm in Dashboard-generated Blueprints for your service types).

```yaml
services:
  - type: pserv
    name: internal-api
    env: docker
    # ...

  - type: web
    name: gateway
    envVars:
      - key: INTERNAL_API_HOST
        fromService:
          name: internal-api
          type: pserv
          property: host
      - key: INTERNAL_API_HOSTPORT
        fromService:
          name: internal-api
          type: pserv
          property: hostport
```

```yaml
  - key: UPSTREAM_TOKEN
    fromService:
      name: internal-api
      type: web
      envVarKey: SERVICE_TOKEN
```

(Adjust `type` to match target service: `web`, `pserv`, etc.)

## `fromGroup` — environment group

Links **all** variables from named group. Group must exist (or be created in same Blueprint workflow, depending on org’s pattern).

```yaml
services:
  - type: web
    name: app
    envVars:
      - fromGroup: shared-config
      - key: SERVICE_SPECIFIC
        value: only-on-app
```

Group keys appear as if defined on service.

## Precedence

1. **Service-level** `envVars` entries **override** any same-name variable from linked **environment groups**.
2. **Multiple groups** on one service: overlapping keys resolve to **most recently created** group. This is **not guaranteed stable** across account operations. Prefer **non-overlapping** keys per group or **single** group per concern.

## Edge cases

- **`fromService` / `fromDatabase` outside the Blueprint file** — Can reference resources **not** declared in `render.yaml` **only if** they **already exist** in same Render **workspace** (same team/account context) and names match. Otherwise provision fails at apply time.
- **`sync: false` in groups** — Not allowed; use Dashboard or service-level entries.
- **Preview environments** — Sensitive patterns (`sync: false`, some generated rotations) may behave differently. Verify preview env docs in **render-blueprints**.
- **Secret files** — Declared separately from `envVars`. Paths always `/etc/secrets/<filename>` at runtime.

## Minimal multi-pattern example

```yaml
services:
  - type: web
    name: full-example
    runtime: node
    buildCommand: npm install && npm run build
    startCommand: npm start
    envVars:
      - fromGroup: baseline
      - key: PUBLIC_API_URL
        value: https://api.example.com
      - key: WEBHOOK_SIGNING_SECRET
        generateValue: true
      - key: THIRD_PARTY_API_KEY
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: prod-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: sessions-kv
          type: keyvalue
          property: connectionString
```
