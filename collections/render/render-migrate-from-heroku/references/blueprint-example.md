# Blueprint Example: Heroku Migration with Project/Environment Pattern

Complete `render.yaml` migrating a typical Heroku app: web dyno, worker dyno, Heroku Scheduler (clock), Postgres, Redis.

References: [Blueprint docs](https://render.com/docs/blueprint-spec#projects-and-environments) | [Blueprint YAML JSON schema](https://render.com/schema/render.yaml.json)

## Full Example

Assumes Node.js app `acme-app` migrating from Heroku US region.

```yaml
previews:
  generation: off
projects:
  - name: acme-app
    environments:
      - name: production
        services:
          # Web service (from Heroku web dyno)
          - type: web
            name: acme-app-web
            runtime: node
            plan: starter
            region: oregon
            buildCommand: npm ci && npm run build
            startCommand: npm start
            healthCheckPath: /health
            envVars:
              - key: NODE_ENV
                value: production
              - key: DATABASE_URL
                fromDatabase:
                  name: acme-app-db
                  property: connectionString
              - key: REDIS_URL
                fromService:
                  type: keyvalue
                  name: acme-app-cache
                  property: connectionString
              - key: APP_NAME
                value: acme-app
              - key: LOG_LEVEL
                value: info
              - key: STRIPE_API_KEY
                sync: false
              - key: JWT_SECRET
                sync: false

          # Background worker (from Heroku worker dyno)
          - type: worker
            name: acme-app-worker
            runtime: node
            plan: starter
            region: oregon
            buildCommand: npm ci
            startCommand: node worker.js
            envVars:
              - key: DATABASE_URL
                fromDatabase:
                  name: acme-app-db
                  property: connectionString
              - key: REDIS_URL
                fromService:
                  type: keyvalue
                  name: acme-app-cache
                  property: connectionString
              - key: APP_NAME
                value: acme-app
              - key: LOG_LEVEL
                value: info
              - key: STRIPE_API_KEY
                sync: false

          # Cron job (from Heroku Scheduler or clock dyno)
          - type: cron
            name: acme-app-cron
            runtime: node
            plan: starter
            region: oregon
            schedule: "0 * * * *"
            buildCommand: npm ci
            startCommand: node scripts/scheduled-task.js
            envVars:
              - key: DATABASE_URL
                fromDatabase:
                  name: acme-app-db
                  property: connectionString
              - key: APP_NAME
                value: acme-app
              - key: STRIPE_API_KEY
                sync: false

          # Key Value (from Heroku Data for Redis)
          - type: keyvalue
            name: acme-app-cache
            plan: starter
            ipAllowList: []  # internal only; app connects via fromService

        databases:
          # Postgres (from Heroku Postgres)
          - name: acme-app-db
            plan: basic-1gb
            diskSizeGB: 10  # carried over from Heroku plan allocation

```

## Key Patterns

### Environment variables

Define env vars directly on each service. Do not use `envVarGroups`: they can misapply during Blueprint sync.

### Secrets

Mark secrets `sync: false` so Dashboard prompts user. Render prompts only during initial Blueprint apply. Later, set secrets manually in Dashboard or via MCP `update_environment_variables`.

## Blueprint Rules

Follow when generating migration `render.yaml`:

- **Always use `projects:`/`environments:` pattern** — YAML must start with `projects:` key. Never use flat top-level `services:` or `databases:` keys.
- **Set every `plan:` field** from [service mapping](service-mapping.md): look up Heroku dyno size or add-on plan, use mapped Render plan. Never hardcode `starter` without checking mapping first.
- **Set `diskSizeGB` on databases** — carry over Heroku disk allocation from [service mapping](service-mapping.md). Round up to 1 or nearest multiple of 5. Render storage can expand later.
- Always include `previews: { generation: off }` at root to disable preview environments by default.
- Use `fromDatabase` for `DATABASE_URL`; never hardcode connection strings.
- Use `fromService` with `type: keyvalue` and `property: connectionString` for `REDIS_URL`.
- Key Value `ipAllowList: []` (internal only); add specific CIDRs only if user confirms external access is needed.
- Map region from Heroku via [service mapping](service-mapping.md).
- Only include service/database blocks the Heroku app uses.

## Plan Selection

Example uses `starter` and `basic-1gb` as representative values. Real migration: replace them with plans mapped from actual Heroku configuration.

**Fallback defaults** (when Heroku plan is unknown):

| Service type | Fallback plan |
|---|---|
| Web / worker / cron / static / pserv | `starter` |
| Key Value | `starter` |
| Postgres | `basic-1gb` |

## Adapting This Example

- **Python app:** Change `runtime: node` to `runtime: python`, update build/start commands (e.g., `pip install -r requirements.txt`, `gunicorn app:app`)
- **Ruby app:** Change to `runtime: ruby`, update commands (e.g., `bundle install`, `bundle exec puma`)
- **No worker:** Remove `type: worker` service block
- **No cron:** Remove `type: cron` service block
- **No Redis:** Remove `type: keyvalue` service block and any `REDIS_URL` env var references
- **No Postgres:** Remove `databases` section and any `DATABASE_URL` env var references
- **Static site:** Replace `type: web` with `runtime: static` and add `staticPublishPath`
- **EU region:** Change `region: oregon` to `region: frankfurt` (maps from Heroku `eu` region)
