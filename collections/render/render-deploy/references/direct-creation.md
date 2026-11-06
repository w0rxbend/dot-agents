# Direct Creation (MCP) Details

## Direct Creation Workflow

### Step 1: Analyze Codebase

Use [codebase-analysis.md](codebase-analysis.md) to find runtime, build/start commands, env vars, datastores.

### Step 2: Create Resources via MCP

**Create a Web Service:**
```
create_web_service(
  name: "my-api",
  runtime: "node",  # or python, go, rust, ruby, elixir, docker
  repo: "https://github.com/username/repo",
  branch: "main",  # optional, defaults to repo default branch
  buildCommand: "npm ci",
  startCommand: "npm start",
  plan: "free",  # free, starter, standard, pro, pro_max, pro_plus, pro_ultra
  region: "oregon",  # oregon, frankfurt, singapore, ohio, virginia
  envVars: [
    {"key": "NODE_ENV", "value": "production"}
  ]
)
```

**Create a Static Site:**
```
create_static_site(
  name: "my-frontend",
  repo: "https://github.com/username/repo",
  branch: "main",
  buildCommand: "npm run build",
  publishPath: "dist",  # or build, public, out
  envVars: [
    {"key": "VITE_API_URL", "value": "https://api.example.com"}
  ]
)
```

**Create a Cron Job:**
```
create_cron_job(
  name: "daily-cleanup",
  runtime: "node",
  repo: "https://github.com/username/repo",
  schedule: "0 0 * * *",  # Daily at midnight (cron syntax)
  buildCommand: "npm ci",
  startCommand: "node scripts/cleanup.js",
  plan: "starter"  # no free cron plan; confirm paid plan with user first
)
```

**Create a PostgreSQL Database:**
```
create_postgres(
  name: "myapp-db",
  plan: "free",  # free, basic_256mb, basic_1gb, basic_4gb, pro_4gb, etc.
  region: "oregon"
)
```

**Create a Key-Value Store (Redis):**
```
create_key_value(
  name: "myapp-cache",
  plan: "free",  # free, starter, standard, pro, pro_plus
  region: "oregon",
  maxmemoryPolicy: "allkeys_lru"  # eviction policy
)
```

### Step 3: Configure Environment Variables

After creating services, add environment variables:

```
update_environment_variables(
  serviceId: "<service-id-from-creation>",
  envVars: [
    {"key": "DATABASE_URL", "value": "<connection-string>"},
    {"key": "LOG_LEVEL", "value": "info"}
  ]
)
```

**Note:** For database connection strings, get internal URL from database details in Dashboard or via `get_postgres(postgresId: "<id>")`; don't echo it back.

**Secrets** (`JWT_SECRET`, `API_KEY`, etc.): user sets them in Dashboard. Never ask user to paste secret values into chat.

### Step 4: Verify Deployment

Services with `autoDeploy: "yes"` (default) deploy automatically on creation.

**Check deployment status:**
```
list_deploys(serviceId: "<service-id>", limit: 1)
```

**Monitor logs for errors:**
```
list_logs(resource: ["<service-id>"], level: ["error"], limit: 50)
```

**Check health metrics:**
```
get_metrics(
  resourceId: "<service-id>",
  metricTypes: ["http_request_count", "cpu_usage", "memory_usage"]
)
```
