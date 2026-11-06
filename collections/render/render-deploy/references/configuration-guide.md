# Render Configuration Guide

## Environment Variables

### Required vs Optional Variables

**Always declare ALL environment variables in render.yaml**, even if user provides values later.

**Three categories:**

1. **Configuration values** (hardcoded):
```yaml
envVars:
  - key: NODE_ENV
    value: production
  - key: LOG_LEVEL
    value: info
  - key: API_URL
    value: https://api.example.com
```

2. **Secrets** (user provides):
```yaml
envVars:
  - key: JWT_SECRET
    sync: false
  - key: STRIPE_SECRET_KEY
    sync: false
  - key: API_KEY
    sync: false
```

3. **Auto-generated** (Render provides):
```yaml
envVars:
  - key: SESSION_SECRET
    generateValue: true
  - key: ENCRYPTION_KEY
    generateValue: true
```

### Database Connection Patterns

**Multiple databases:**
```yaml
envVars:
  - key: PRIMARY_DB_URL
    fromDatabase:
      name: postgres-primary
      property: connectionString
  - key: ANALYTICS_DB_URL
    fromDatabase:
      name: postgres-analytics
      property: connectionString
  - key: CACHE_URL
    fromService:
      name: redis
      type: keyvalue
      property: connectionString
```

### Cross-Service References

Reference other services in your account:

```yaml
services:
  - type: web
    name: frontend
    runtime: node
    envVars:
      - key: API_URL
        fromService:
          name: backend-api
          type: web
          property: host  # or hostport, port

  - type: web
    name: backend-api
    runtime: node
```

**Available properties:**
- `host`: Service hostname
- `port`: Service port
- `hostport`: Combined `host:port`

### Environment Variable Groups

Share common configuration across services:

```yaml
envVarGroups:
  - name: common-config
    envVars:
      - key: NODE_ENV
        value: production
      - key: LOG_LEVEL
        value: info
      - key: TZ
        value: UTC

services:
  - type: web
    name: web-app
    runtime: node
    envVars:
      - fromGroup: common-config
      - key: PORT
        value: 10000

  - type: worker
    name: worker
    runtime: node
    envVars:
      - fromGroup: common-config
```

---

## Port Binding

### The Port Binding Requirement

**CRITICAL:** Web services must bind to `0.0.0.0:$PORT`

- Render sets `PORT` environment variable (default: 10000)
- Services must bind to `0.0.0.0` (not `localhost` or `127.0.0.1`)
- Health checks fail if port binding is incorrect
- Deploy fails or service gets no traffic

### Code Examples by Language

**Node.js / Express:**
```javascript
const express = require('express');
const app = express();

const PORT = process.env.PORT || 3000;

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
```

**Python / Flask:**
```python
import os
from flask import Flask

app = Flask(__name__)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

**Python / Django:**

In `settings.py`:
```python
import os
# e.g. my-app.onrender.com (see assets/python-django.yaml); never ['*']
ALLOWED_HOSTS = os.environ['DJANGO_ALLOWED_HOSTS'].split(',')
```

Start command in render.yaml:
```yaml
startCommand: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

**Python / FastAPI:**
```python
import os
import uvicorn
from fastapi import FastAPI

app = FastAPI()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

Start command:
```yaml
startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Go:**
```go
package main

import (
    "fmt"
    "net/http"
    "os"
)

func main() {
    port := os.Getenv("PORT")
    if port == "" {
        port = "3000"
    }

    http.HandleFunc("/", handler)
    fmt.Printf("Server starting on port %s\n", port)
    http.ListenAndServe(":"+port, nil)
}
```

**Ruby / Rails:**

In `config/puma.rb`:
```ruby
port ENV.fetch("PORT") { 3000 }
bind "tcp://0.0.0.0:#{ENV.fetch('PORT', 3000)}"
```

**Rust / Actix:**
```rust
use actix_web::{App, HttpServer};
use std::env;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let port = env::var("PORT").unwrap_or_else(|_| "8080".to_string());
    let addr = format!("0.0.0.0:{}", port);

    HttpServer::new(|| App::new())
        .bind(&addr)?
        .run()
        .await
}
```

---

## Build Commands

### Non-Interactive Flags

**Always use non-interactive flags** so builds never hang waiting for input.

**npm (Node.js):**
```yaml
buildCommand: npm ci
# NOT: npm install
```

**pip (Python):**
```yaml
buildCommand: pip install -r requirements.txt
# Already non-interactive
```

**apt (System packages):**
```yaml
buildCommand: apt-get update && apt-get install -y libpq-dev
# Use -y flag to auto-confirm
```

**bundler (Ruby):**
```yaml
buildCommand: bundle install --jobs=4 --retry=3
```

### Build with Additional Steps

**Node.js with build step:**
```yaml
buildCommand: npm ci && npm run build
```

**Python Django with static files:**
```yaml
buildCommand: pip install -r requirements.txt && python manage.py collectstatic --no-input
```

**Ruby Rails with assets:**
```yaml
buildCommand: bundle install && bundle exec rails assets:precompile
```

### Build Timeouts

**Free tier:** 15 minutes
**Paid tiers:** Configurable

**If builds timeout:**
1. Optimize dependencies (remove unused packages)
2. Use build caching
3. Pre-build in CI/CD
4. Upgrade to paid tier for longer timeouts

---

## Database Connections

### Internal vs External URLs

**Use internal URLs for better performance:**

`fromDatabase` fills environment variable with database's internal connection string.

```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: postgres
      property: connectionString
```

### Connection Pooling

**Node.js / PostgreSQL:**
```javascript
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL, // internal URL (private network)
  // External URL: ssl: true (add `ca` if cert not publicly trusted); never rejectUnauthorized: false
  max: 20, // Maximum pool size
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

**Python / PostgreSQL:**
```python
import psycopg2.pool

pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    dsn=os.environ['DATABASE_URL']
)
```

**Django Settings:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'URL': os.environ['DATABASE_URL'],
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}
```

### Database Migrations

**Run migrations during build:**

**Django:**
```yaml
buildCommand: pip install -r requirements.txt && python manage.py migrate
```

**Rails:**
```yaml
buildCommand: bundle install && bundle exec rails db:migrate
```

**Node.js / Prisma:**
```yaml
buildCommand: npm ci && CHECKPOINT_DISABLE=1 npx prisma migrate deploy  # opt out of Prisma CLI telemetry
```

---

## Free Tier Limitations

### What's Included

**Free tier provides:**
- 1 web service
- 1 PostgreSQL database (1 GB storage, 97 MB RAM)
- 750 hours/month compute
- 512 MB RAM per service
- 0.5 CPU per service
- 100 GB bandwidth/month

### Resource Limits

**Spin Down (Free services):**
- Services spin down after 15 minutes of inactivity
- First request after spin down takes ~30 seconds (cold start)

### When to Upgrade

**Upgrade to paid plan when:**
- Need more than 1 web service
- Need always-on services (no spin down)
- Traffic exceeds free tier limits
- Need more memory/CPU
- Need faster build times
- Need preview environments

---

## Health Checks

### Adding Health Check Endpoints

**Node.js / Express:**
```javascript
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'ok',
    timestamp: new Date().toISOString()
  });
});
```

**Python / Flask:**
```python
@app.route('/health')
def health():
    return {'status': 'ok'}, 200
```

**Python / FastAPI:**
```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Go:**
```go
http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte(`{"status":"ok"}`))
})
```

### Configure in render.yaml

```yaml
services:
  - type: web
    name: my-app
    runtime: node
    healthCheckPath: /health
```

Gives faster deploy detection and automatic restart on health check failures.

---

## Common Deployment Issues

### Issue 1: Missing Environment Variables

**Symptom:** Service crashes with "undefined variable" errors

**Solution:** Add all required env vars to render.yaml (secrets with `sync: false`).

### Issue 2: Port Binding Errors

**Symptom:** `EADDRINUSE` or health check timeout errors

**Solution:** Bind app to `0.0.0.0:$PORT`.

### Issue 3: Build Hangs

**Symptom:** Build times out after 15 minutes

**Solution:** Use non-interactive build commands (`npm ci`, not `npm install`).

### Issue 4: Database Connection Fails

**Symptom:** `ECONNREFUSED` on port 5432

**Solutions:**
1. Use `fromDatabase` for automatic internal URLs
2. Enable SSL for external connections
3. Check `ipAllowList` settings

### Issue 5: Static Site 404s

**Symptom:** Client-side routes return 404

**Solution:** Add SPA rewrite rules:
```yaml
routes:
  - type: rewrite
    source: /*
    destination: /index.html
```

### Issue 6: Out of Memory (OOM)

**Symptom:** Service crashes with `JavaScript heap out of memory`

**Solutions:**
1. Optimize app memory usage
2. Reduce dependency size
3. Upgrade to higher plan with more RAM

---

## Best Practices Checklist

**Environment Variables:**
- [ ] All env vars declared in render.yaml
- [ ] Secrets marked with `sync: false`
- [ ] Database URLs use `fromDatabase` references

**Port Binding:**
- [ ] App binds to `process.env.PORT`
- [ ] Bind to `0.0.0.0` (not `localhost`)

**Build Commands:**
- [ ] Use non-interactive flags (`npm ci`, `-y`, etc.)
- [ ] Build completes under 15 minutes (free tier)

**Start Commands:**
- [ ] Command starts HTTP server correctly

**Health Checks:**
- [ ] `/health` endpoint implemented
- [ ] Returns 200 status code

**Database:**
- [ ] Connection pooling configured
- [ ] Uses connection string from `fromDatabase`
- [ ] SSL enabled if needed

**Plans:**
- [ ] `plan: free` by default where available (not for workers, cron jobs or private services)
- [ ] Upgrade path documented for users

**Git Repository:**
- [ ] render.yaml committed to repository
- [ ] Pushed to git remote (GitHub/GitLab/Bitbucket)
- [ ] Branch specified in render.yaml (if not main)

---

## Additional Resources

- Blueprint Specification: [blueprint-spec.md](blueprint-spec.md)
- Service Types: [service-types.md](service-types.md)
- Runtimes: [runtimes.md](runtimes.md)
- Official Render Docs: https://render.com/docs
