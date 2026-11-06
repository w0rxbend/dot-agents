# Render Service Types

## Web Services (`type: web`)

### Purpose

HTTP servers handling requests from internet. Publicly reachable via HTTPS URLs.

### Use Cases

- **REST APIs**: JSON APIs for mobile or frontend apps
- **GraphQL servers**: GraphQL endpoints for client queries
- **Web applications**: Server-rendered sites (Django, Rails, Express)
- **Full-stack frameworks**: Next.js, Nuxt.js, Remix, SvelteKit
- **WebSocket servers**: Real-time communication servers
- **SSR applications**: Server-side rendered React, Vue or Angular apps

### Key Characteristics

- **Public URL**: Auto-assigned `https://[service-name].onrender.com`
- **Port binding required**: Must bind to `0.0.0.0:$PORT`
- **Health checks**: Render pings service to verify it runs
- **HTTPS**: Automatic SSL/TLS certificates
- **Load balancing**: Traffic spread across multiple instances
- **Custom domains**: Own domain names supported

### Required Configuration

```yaml
type: web
name: my-api
runtime: node
buildCommand: npm ci
startCommand: npm start
```

### Best Practices

1. **Bind to environment PORT**:
```javascript
const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0');
```

2. **Add health check endpoint**:
```javascript
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});
```

3. **Use appropriate timeouts**: Web requests should finish within 30 seconds

4. **Implement graceful shutdown**: Handle SIGTERM signals

---

## Worker Services (`type: worker`)

### Purpose

Run background tasks without handling HTTP requests. Not publicly reachable.

### Use Cases

- **Queue processors**: Redis queue, BullMQ, Celery, Sidekiq
- **Background jobs**: Email sending, image processing, data exports
- **Event consumers**: Message queue consumers (Kafka, RabbitMQ, etc.)
- **Data pipeline workers**: ETL processes, data transformation
- **Scheduled background tasks**: Continuous processes (not cron)
- **WebSocket backend**: Dedicated WebSocket handler services

### Key Characteristics

- **No public URL**: Not reachable from internet
- **No port binding**: No need to listen on port
- **No health checks**: Render monitors process health differently
- **Long-running**: Can run indefinitely
- **Private communication**: Reach via internal networking
- **Restart on crash**: Auto-restarted if process dies

### Required Configuration

```yaml
type: worker
name: queue-processor
runtime: python
buildCommand: pip install -r requirements.txt
startCommand: celery -A tasks worker --loglevel=info
```

### Best Practices

1. **Connect to message queue**:
```python
import redis
r = redis.from_url(os.environ['REDIS_URL'])
```

2. **Graceful shutdown**: Finish current jobs before exit

### Common Patterns

**Node.js with BullMQ:**
```yaml
type: worker
name: job-processor
runtime: node
buildCommand: npm ci
startCommand: node worker.js
envVars:
  - key: REDIS_URL
    fromService:
      name: redis
      type: keyvalue
      property: connectionString
```

---

## Cron Jobs (`type: cron`)

### Purpose

Run tasks on repeating schedule. Execute, complete, shut down.

### Use Cases

- **Database backups**: Regular automated backups
- **Report generation**: Daily/weekly reports
- **Data cleanup**: Delete old records periodically
- **Cache warming**: Pre-populate caches
- **Email digests**: Send scheduled email summaries
- **Data synchronization**: Sync between systems
- **Batch processing**: Process accumulated data

### Key Characteristics

- **Scheduled execution**: Runs on cron schedule
- **Automatic shutdown**: Shuts down after completing
- **No persistent port**: No listening port kept
- **No health checks**: Task completes or fails
- **UTC timezone**: All schedules in UTC
- **Maximum runtime**: Jobs time out after configured limit

### Required Configuration

```yaml
type: cron
name: daily-backup
runtime: node
schedule: "0 2 * * *"  # Daily at 2 AM UTC
buildCommand: npm ci
startCommand: node scripts/backup.js
```

### Schedule Format

Standard cron syntax: `minute hour day month weekday`

**Common schedules:**

| Schedule | Description |
|----------|-------------|
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour |
| `0 0 * * *` | Daily at midnight UTC |
| `0 9 * * 1-5` | Weekdays at 9 AM UTC |
| `0 0 1 * *` | First day of each month |
| `0 9 * * 1` | Every Monday at 9 AM UTC |

### Best Practices

1. **Handle failures gracefully**: Make jobs idempotent

2. **Set appropriate timeouts**: Match expected job duration

### Example Use Cases

**Daily Database Backup:**
```yaml
type: cron
name: db-backup
runtime: python
schedule: "0 1 * * *"  # 1 AM UTC daily
buildCommand: pip install -r requirements.txt
startCommand: python scripts/backup.py
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: postgres
      property: connectionString
  - key: S3_BUCKET
    value: my-backups
```

---

## Static Sites (`type: web` + `runtime: static`)

### Purpose

Serve static HTML, CSS and JavaScript files via CDN. No backend runtime.

### Use Cases

- **Single Page Applications (SPAs)**: React, Vue, Angular apps
- **Static site generators**: Gatsby, Next.js (static export), Hugo
- **Documentation sites**: MkDocs, Docusaurus, VitePress
- **Landing pages**: Marketing sites
- **Portfolio sites**: Personal websites
- **JAMstack sites**: Static sites with API integration

### Key Characteristics

- **CDN delivery**: Global edge caching
- **No backend runtime**: Serves only built files

### Required Configuration

```yaml
type: web
name: frontend
runtime: static
buildCommand: npm ci && npm run build
staticPublishPath: ./dist  # or ./build, ./out, ./public
```

### Routing for SPAs

SPAs need rewrite rules for client-side routing:

```yaml
type: web
name: react-app
runtime: static
buildCommand: npm ci && npm run build
staticPublishPath: ./build
routes:
  - type: rewrite
    source: /*
    destination: /index.html
```

### Custom Headers

Add cache control and security headers:

```yaml
type: web
name: static-site
runtime: static
buildCommand: npm ci && npm run build
staticPublishPath: ./dist
headers:
  # Cache static assets
  - path: /static/*
    name: Cache-Control
    value: public, max-age=31536000, immutable

  # Security headers
  - path: /*
    name: X-Frame-Options
    value: DENY
  - path: /*
    name: X-Content-Type-Options
    value: nosniff
```

### Build Filters

Monorepos: build only when frontend files change:

```yaml
type: web
name: frontend
runtime: static
buildCommand: npm ci && npm run build
staticPublishPath: ./dist
buildFilter:
  paths:
    - frontend/**
  ignoredPaths:
    - frontend/**/*.test.js
    - frontend/README.md
```

### Best Practices

1. **Use proper cache headers**: Long cache for hashed assets

2. **Handle 404s**: Create custom 404.html page

---

## Private Services (`type: pserv`)

### Purpose

Receive traffic only from other Render services on same private network. Not exposed to public internet.

### Use Cases

- **Internal APIs**: Accessed only by other services
- **Database proxies**: Connection pools, read replicas
- **Microservices**: Service mesh architectures
- **Admin tools**: Internal dashboards
- **Cache layers**: Internal caching services
- **Message brokers**: Internal message queues

### Key Characteristics

- **No public URL**: Reachable only via internal DNS
- **Internal networking**: Fast, low-latency connections
- **Port binding required**: Must bind to `0.0.0.0:$PORT`

### Required Configuration

```yaml
type: pserv
name: internal-api
runtime: node
buildCommand: npm ci
startCommand: npm start
```

### Internal Addresses

Render gives each web service and private service unique hostname on private network. Hostname is stable. It maps to instance IPs, which can change between deploys. Free web services can't receive private traffic.

Services can talk over private network only when in same workspace and region. Find internal address in service's **Connect** menu under **Internal**. Private services also show it as **Service Address**.

Internal address form: `internal-hostname:port`. Add protocol when client requires one, for example `http://internal-hostname:port`.

In Blueprint, use `fromService` to inject address into another service:

```yaml
services:
  - type: web
    name: frontend
    runtime: node
    envVars:
      - key: API_URL
        fromService:
          name: internal-api
          type: pserv
          property: hostport
```

For web and private services, `host` gives internal hostname. `hostport` gives hostname and listening port as `host:port`.

---

## Comparison Table

| Feature | Web | Worker | Cron | Static | Private |
|---------|-----|--------|------|--------|---------|
| Public URL | ✅ Yes | ❌ No | ❌ No | ✅ Yes | ❌ No |
| Port Binding | ✅ Required | ❌ Not needed | ❌ Not needed | ❌ N/A | ✅ Required |
| Health Checks | ✅ Yes | ❌ No | ❌ No | ❌ N/A | ✅ Yes |
| Runtime | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes |
| Persistent | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| Scaling | ✅ Yes | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| Use Case | HTTP servers | Background jobs | Scheduled tasks | Static files | Internal services |

## Choosing the Right Service Type

**Use Web Service when:**
- App handles HTTP requests
- Users reach it via URL
- Load balancing and scaling needed

**Use Worker Service when:**
- Processing background jobs
- Consuming from message queues
- Running long-lived processes without HTTP

**Use Cron Job when:**
- Running scheduled tasks
- Processing need not be always-on
- Tasks run periodically (hourly, daily, weekly)

**Use Static Site when:**
- Serving pre-built HTML/CSS/JS
- No backend processing needed
- Want CDN caching and fast delivery

**Use Private Service when:**
- Only other services access it
- Want internal-only communication
- Building microservice architectures
