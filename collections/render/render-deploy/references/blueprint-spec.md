# Render Blueprint Specification

Reference for Blueprint files: YAML (typically `render.yaml`) in repository root.

## Root-Level Structure

```yaml
# Top-level fields
services: []         # Array of service definitions
databases: []        # Array of PostgreSQL databases
envVarGroups: []     # Reusable environment variable groups (optional)
projects: []         # Project organization (optional)
ungrouped: []        # Resources outside projects (optional)
previews:            # Preview environment configuration (optional)
  generation: auto_preview | manual | none
```

## Service Types

### Web Services (`type: web`)

HTTP services, APIs, web apps. Public via HTTPS.

**Required fields:**
- `name`: Unique service ID
- `type`: Must be `web`
- `runtime`: Language/environment (see Runtimes section)
- `buildCommand`: Builds app
- `startCommand`: Starts server

**Common optional fields:**
- `plan`: Instance type (default: `free`)
- `region`: Deploy region (default: `oregon`)
- `branch`: Git branch to deploy (default: `main`)
- `autoDeploy`: Auto-deploy on push (default: `true`)
- `envVars`: Environment variables array
- `healthCheckPath`: Health check endpoint (default: `/`)
- `numInstances`: Instance count (manual scaling)
- `scaling`: Autoscaling configuration

**Example:**
```yaml
services:
  - type: web
    name: api-server
    runtime: node
    plan: free
    buildCommand: npm ci
    startCommand: npm start
    branch: main
    autoDeploy: true
    envVars:
      - key: NODE_ENV
        value: production
      - key: PORT
        value: 10000
```

### Worker Services (`type: worker`)

Background job processors, queue consumers. Not publicly accessible.

**Required fields:**
- `name`: Unique service ID
- `type`: Must be `worker`
- `runtime`: Language/environment
- `buildCommand`: Build command
- `startCommand`: Starts worker process

**Key differences from web services:**
- No health checks
- No port binding required

**Example:**
```yaml
services:
  - type: worker
    name: job-processor
    runtime: python
    plan: starter  # free instances are web/static/Postgres/Key Value only
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A tasks worker --loglevel=info
    envVars:
      - key: REDIS_URL
        fromService:
          name: redis
          type: keyvalue
          property: connectionString
```

### Cron Jobs (`type: cron`)

Tasks run on cron schedule.

**Required fields:**
- `name`: Unique service ID
- `type`: Must be `cron`
- `runtime`: Language/environment
- `schedule`: Cron expression
- `buildCommand`: Build command
- `startCommand`: Runs on schedule

**Schedule format:** Standard cron syntax (minute hour day month weekday)

**Examples:**
- `0 0 * * *` - Daily at midnight UTC
- `*/15 * * * *` - Every 15 minutes
- `0 9 * * 1` - Every Monday at 9 AM UTC

**Example:**
```yaml
services:
  - type: cron
    name: daily-backup
    runtime: node
    schedule: "0 2 * * *"
    buildCommand: npm ci
    startCommand: node scripts/backup.js
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: postgres
          property: connectionString
```

### Static Sites (`type: static` or `type: web` with `runtime: static`)

Serve static HTML/CSS/JS files via CDN.

**Required fields:**
- `name`: Unique service ID
- `type`: `web`
- `runtime`: `static`
- `buildCommand`: Builds static assets
- `staticPublishPath`: Path to built files (e.g., `./build`, `./dist`)

**Optional configuration:**
- `routes`: SPA routing rules
- `headers`: Custom HTTP headers
- `buildFilter`: Path filters for build triggers

**Example:**
```yaml
services:
  - type: web
    name: react-app
    runtime: static
    buildCommand: npm ci && npm run build
    staticPublishPath: ./dist
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
    headers:
      - path: /*
        name: Cache-Control
        value: public, max-age=31536000, immutable
```

### Private Services (`type: pserv`)

Internal services, reachable only within your Render account.

**Required fields:**
- `name`: Unique service ID
- `type`: Must be `pserv`
- `runtime`: Language/environment
- `buildCommand`: Build command
- `startCommand`: Start command

**Use cases:** internal APIs, database proxies, microservices not exposed to internet.

**Example:**
```yaml
services:
  - type: pserv
    name: internal-api
    runtime: go
    plan: starter  # free instances are web/static/Postgres/Key Value only
    buildCommand: go build -o bin/app
    startCommand: ./bin/app
```

## Runtimes

### Native Runtimes

**Node.js (`runtime: node`):**
- Versions: 14, 16, 18, 20, 21
- Default version: 20
- Set version in `package.json` engines field

**Python (`runtime: python`):**
- Versions: 3.8, 3.9, 3.10, 3.11, 3.12
- Default version: 3.11
- Set version in `runtime.txt` or `Pipfile`

**Go (`runtime: go`):**
- Versions: 1.20, 1.21, 1.22, 1.23
- Uses go modules
- Version from `go.mod`

**Ruby (`runtime: ruby`):**
- Versions: 3.0, 3.1, 3.2, 3.3
- Uses Bundler
- Version from `.ruby-version` or `Gemfile`

**Rust (`runtime: rust`):**
- Latest stable version
- Uses Cargo

**Elixir (`runtime: elixir`):**
- Latest stable version
- Uses Mix

### Docker Runtime

**Docker (`runtime: docker`):**
Builds from Dockerfile in repository.

**Additional fields:**
- `dockerfilePath`: Path to Dockerfile (default: `./Dockerfile`)
- `dockerContext`: Build context directory (default: `.`)

**Example:**
```yaml
services:
  - type: web
    name: docker-app
    runtime: docker
    dockerfilePath: ./docker/Dockerfile
    dockerContext: .
    plan: free
```

**Image (`runtime: image`):**
Deploys pre-built Docker images from registry.

**Additional fields:**
- `image`: Image URL (e.g., `registry.com/image:tag`)
- `registryCredential`: Credentials for private registries

**Example:**
```yaml
services:
  - type: web
    name: prebuilt-app
    runtime: image
    image: myregistry.com/app:v1.2.3
    plan: free
```

## Service Plans

| Plan | RAM | CPU | Price |
|------|-----|-----|-------|
| `free` | 512 MB | 0.5 | Free (750 hrs/mo) |
| `starter` | 512 MB | 0.5 | $7/month |
| `standard` | 2 GB | 1 | $25/month |
| `pro` | 4 GB | 2 | $85/month |
| `pro_plus` | 8 GB | 4 | $175/month |

**Default to `plan: free` for web services, static sites, Postgres and Key Value unless user specifies otherwise.** Background workers, cron jobs and private services have no free instance type. Use `starter` (cheapest paid plan) for them and tell user they will be billed.

## Regions

- `oregon` (US West) - Default
- `ohio` (US East)
- `virginia` (US East)
- `frankfurt` (EU)
- `singapore` (Asia)

## Environment Variables

### 1. Hardcoded Values

Non-sensitive configuration:

```yaml
envVars:
  - key: NODE_ENV
    value: production
  - key: API_URL
    value: https://api.example.com
  - key: LOG_LEVEL
    value: info
```

### 2. Generated Secrets

Render generates base64-encoded 256-bit random value:

```yaml
envVars:
  - key: SESSION_SECRET
    generateValue: true
  - key: ENCRYPTION_KEY
    generateValue: true
```

### 3. User-Provided Secrets

Prompts user for values during Blueprint creation:

```yaml
envVars:
  - key: STRIPE_SECRET_KEY
    sync: false
  - key: JWT_SECRET
    sync: false
  - key: API_KEY
    sync: false
```

**`sync: false` means "user will fill this in the Dashboard".**

### 4. Database References

Link to database connection strings:

```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: postgres
      property: connectionString
  - key: REDIS_URL
    fromService:
      name: redis
      type: keyvalue
      property: connectionString
```

**Available properties:**
- `connectionString`: Full connection URL
- `host`: Database host
- `port`: Database port
- `user`: Database username
- `password`: Database password
- `database`: Database name
- `hostport`: Combined `host:port`

### 5. Service References

Link to other services:

```yaml
envVars:
  - key: API_URL
    fromService:
      name: api-server
      type: web
      property: host
```

### 6. Environment Variable Groups

Reusable groups shared across services:

```yaml
envVarGroups:
  - name: shared-config
    envVars:
      - key: LOG_LEVEL
        value: info
      - key: ENVIRONMENT
        value: production

services:
  - type: web
    name: web-app
    runtime: node
    envVars:
      - fromGroup: shared-config
      - key: PORT
        value: 10000
```

## Databases

### PostgreSQL

```yaml
databases:
  - name: postgres
    databaseName: myapp_prod
    user: myapp_user
    plan: free
    postgresMajorVersion: "15"
    ipAllowList: []
```

**Plans:**
- `free`: 1 GB storage, 97 MB RAM, 0.1 CPU
- `basic-256mb`, `basic-512mb`, `basic-1gb`, `basic-4gb`
- `pro-4gb`, `pro-8gb`, `pro-16gb`, etc.
- `accelerated-4gb`, `accelerated-8gb`, etc. (SSD-backed)

**Key fields:**
- `name`: Identifier for references
- `databaseName`: Actual PostgreSQL database name
- `user`: Database username
- `postgresMajorVersion`: PostgreSQL version (11-16)
- `ipAllowList`: Array of CIDR blocks (empty = internal only)
- `diskSizeGB`: Storage size (paid plans only)

**High Availability (paid plans):**
```yaml
databases:
  - name: postgres
    databaseName: myapp_prod
    plan: pro-4gb
    highAvailabilityEnabled: true
```

**Read Replicas (paid plans):**
```yaml
databases:
  - name: postgres
    databaseName: myapp_prod
    plan: pro-4gb
    readReplicas:
      - name: read-replica-1
        region: ohio
      - name: read-replica-2
        region: frankfurt
```

### Key Value (Redis-compatible)

Declare Key Value instances under `services:` with `type: keyvalue` (not under `databases:`).
Other services reference them with `fromService` + `type: keyvalue`:

```yaml
services:
  - type: keyvalue
    name: redis
    plan: free
    maxmemoryPolicy: allkeys-lru
    ipAllowList: []  # internal only
```

**Plans:** Key Value has own plan list (`free`, `starter`, `standard`, `pro`, ...). See render-keyvalue skill.

**maxmemoryPolicy options:**
- `allkeys-lru`: Evict least recently used keys
- `volatile-lru`: Evict LRU keys with TTL
- `allkeys-random`: Evict random keys
- `volatile-random`: Evict random keys with TTL
- `volatile-ttl`: Evict keys with soonest TTL
- `noeviction`: Return errors when memory full

## Scaling

### Manual Scaling

Fixed instance count:

```yaml
services:
  - type: web
    name: my-app
    runtime: node
    plan: standard
    numInstances: 3
```

### Autoscaling

Scales on CPU/memory:

```yaml
services:
  - type: web
    name: my-app
    runtime: node
    plan: standard
    scaling:
      minInstances: 1
      maxInstances: 5
      targetCPUPercent: 60
      targetMemoryPercent: 70
```

**Notes:**
- Autoscaling disabled in preview environments
- Preview environments run `minInstances` count
- Requires Professional or higher workspace

## Health Checks

```yaml
services:
  - type: web
    name: my-app
    runtime: node
    healthCheckPath: /health
```

**Recommended:** Add dedicated `/health` endpoint returning `200 OK`.

## Build Filters

Trigger builds based on changed files:

```yaml
services:
  - type: web
    name: frontend
    runtime: static
    buildFilter:
      paths:
        - frontend/**
      ignoredPaths:
        - frontend/README.md
        - frontend/**/*.test.js
```

**Behavior:**
- If `paths` specified: Build only when files in those paths change
- If `ignoredPaths` specified: Don't build when only ignored files change

## Projects and Environments

Organize services into projects with multiple environments:

```yaml
projects:
  - name: my-application
    environments:
      - name: production
        services:
          - type: web
            name: prod-api
            runtime: node
            plan: pro
            buildCommand: npm ci
            startCommand: npm start
        databases:
          - name: prod-postgres
            plan: pro-4gb
        networking:
          isolation: enabled
        permissions:
          protection: enabled

      - name: staging
        services:
          - type: web
            name: staging-api
            runtime: node
            plan: starter
            buildCommand: npm ci
            startCommand: npm start
        databases:
          - name: staging-postgres
            plan: free
```

**Environment features:**
- `networking.isolation`: Network isolation between environments
- `permissions.protection`: Require approval for environment changes

## Preview Environments

Automatic preview environments for pull requests:

```yaml
previews:
  generation: auto_preview  # auto_preview | manual | none
```

**Options:**
- `auto_preview`: Auto-create preview environment for each PR
- `manual`: User triggers preview creation manually
- `none`: Disable preview environments

## Complete Example

```yaml
services:
  # Web service
  - type: web
    name: web-app
    runtime: node
    plan: free
    region: oregon
    buildCommand: npm ci && npm run build
    startCommand: npm start
    branch: main
    autoDeploy: true
    healthCheckPath: /health
    envVars:
      - key: NODE_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: postgres
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: redis
          type: keyvalue
          property: connectionString
      - key: JWT_SECRET
        sync: false

  # Background worker
  - type: worker
    name: queue-worker
    runtime: node
    plan: starter  # free instances are web/static/Postgres/Key Value only
    buildCommand: npm ci
    startCommand: node worker.js
    envVars:
      - key: REDIS_URL
        fromService:
          name: redis
          type: keyvalue
          property: connectionString

  # Cron job
  - type: cron
    name: daily-cleanup
    runtime: node
    schedule: "0 3 * * *"
    buildCommand: npm ci
    startCommand: node scripts/cleanup.js
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: postgres
          property: connectionString

  # Static frontend
  - type: web
    name: frontend
    runtime: static
    buildCommand: npm ci && npm run build
    staticPublishPath: ./dist
    routes:
      - type: rewrite
        source: /*
        destination: /index.html

  # Key Value (Redis-compatible) instance
  - type: keyvalue
    name: redis
    plan: free
    maxmemoryPolicy: allkeys-lru
    ipAllowList: []

databases:
  - name: postgres
    databaseName: app_production
    user: app_user
    plan: free
    postgresMajorVersion: "15"
    ipAllowList: []
```

## Validation

Validate Blueprint before deploying (when CLI command is available):

```bash
render blueprint validate
```

**Common validation errors:**
- Missing required fields
- Invalid runtime values
- Incorrect environment variable references
- Invalid cron expressions
- Invalid YAML syntax

## Best Practices

1. **Mark all secrets with `sync: false`** - Never hardcode sensitive values
2. **Use `fromDatabase` for Postgres URLs and `fromService` (with `type: keyvalue`) for Key Value URLs** - Automatic internal connection strings
3. **Use non-interactive build commands** - Prevents build hangs
4. **Bind to `0.0.0.0:$PORT`** - Required for web services
5. **Use build filters** - Optimize build triggers in monorepos

## Additional Resources

- Official Blueprint Specification: https://render.com/docs/blueprint-spec
- Render CLI Documentation: https://render.com/docs/cli
- Environment Variables Guide: https://render.com/docs/environment-variables
