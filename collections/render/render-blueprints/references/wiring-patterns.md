# Cross-Service Wiring Patterns

## fromDatabase

Reference Managed Postgres database property:

```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: my-postgres
      property: connectionString
```

Available properties:

| Property | Value |
|----------|-------|
| `connectionString` | Full `postgres://` URL (most common) |
| `host` | Database hostname |
| `port` | Database port |
| `user` | Database user |
| `password` | Database password |
| `database` | Database name |

`name` must match database in same Blueprint's `databases` section, or existing workspace database.

---

## fromService (Key Value)

Reference Key Value (Redis-compatible) instance:

```yaml
envVars:
  - key: REDIS_URL
    fromService:
      name: my-redis
      type: keyvalue
      property: connectionString
```

Available properties:

| Property | Value |
|----------|-------|
| `connectionString` | Full `redis://` URL |
| `host` | Internal hostname |
| `port` | Port number |
| `hostport` | `host:port` combined |

---

## fromService (Private Service or Web Service)

Reference another service's internal address or env var:

```yaml
envVars:
  # Get internal hostname
  - key: AUTH_SERVICE_HOST
    fromService:
      name: auth-service
      type: pserv
      property: host

  # Get host:port
  - key: AUTH_SERVICE_URL
    fromService:
      name: auth-service
      type: pserv
      property: hostport

  # Copy an env var from another service
  - key: SHARED_SECRET
    fromService:
      name: auth-service
      type: pserv
      envVarKey: API_SECRET
```

Available properties for `pserv` and `web`:

| Property | Value |
|----------|-------|
| `host` | Internal hostname |
| `hostport` | `host:port` combined |

`envVarKey` copies specific env var value from other service.

---

## fromGroup

Link entire environment group:

```yaml
envVars:
  - fromGroup: shared-secrets
```

Adds all variables from named group to service. Group must exist in workspace or be defined in `envVarGroups`.

---

## generateValue

Generate random base64-encoded 256-bit secret:

```yaml
envVars:
  - key: APP_SECRET
    generateValue: true
```

---

## sync: false

Prompt user for value in Dashboard:

```yaml
envVars:
  - key: STRIPE_API_KEY
    sync: false
```

Use for secrets that should never appear in Blueprint file.

---

## Combined Example

Web service wired to Postgres, Key Value, and private service:

```yaml
services:
  - type: web
    name: api
    runtime: node
    plan: starter
    buildCommand: npm ci
    startCommand: npm start
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: cache
          type: keyvalue
          property: connectionString
      - key: AUTH_HOST
        fromService:
          name: auth
          type: pserv
          property: hostport
      - key: JWT_SECRET
        generateValue: true
      - key: STRIPE_KEY
        sync: false
      - fromGroup: shared-config

  - type: pserv
    name: auth
    runtime: node
    plan: starter
    buildCommand: npm ci
    startCommand: npm start

  - type: keyvalue
    name: cache
    plan: starter
    maxmemoryPolicy: allkeys-lru
    ipAllowList: []  # internal only; add specific CIDRs only if external access is needed

databases:
  - name: db
    plan: starter

envVarGroups:
  - name: shared-config
    envVars:
      - key: LOG_LEVEL
        value: info
```

---

## Edge Cases

- **sync: false only prompts on initial Blueprint setup.** Later syncs preserve existing `sync: false` values. Adding new `sync: false` var to existing Blueprint does not prompt.
- **sync: false is excluded from preview environments.** Users must set these values manually for each preview.
- **sync: false is invalid in envVarGroups.** Silently ignored if used in group definition.
- **fromService/fromDatabase can reference services outside the Blueprint**, but referenced service must already exist in workspace.
- **generateValue** generates once on initial create. Does not regenerate on later Blueprint syncs.
