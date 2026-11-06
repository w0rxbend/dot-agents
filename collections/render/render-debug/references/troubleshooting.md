# Render Troubleshooting Guide

## General Debugging Process

### Debug Priority Checklist

Check in this order:

- [ ] Environment variables (most common)
- [ ] Port binding (second most common)
- [ ] Dependencies installed correctly
- [ ] Database connections configured
- [ ] Build command succeeds
- [ ] Start command correct
- [ ] Health check endpoint exists
- [ ] Resource limits (memory, CPU)

## Issue Category 1: Environment Variables

### Problem: Missing Environment Variable

**Symptoms:**
- `ReferenceError: DATABASE_URL is not defined`
- `KeyError: 'API_KEY'`
- Service crashes right after start

**Diagnosis Steps:**

1. Find variable name in logs:
```bash
render logs -r <service-id> --level error -o json | grep "not defined"
```

2. List current environment variables (Dashboard or render.yaml)

3. Identify missing variable

**Fix Procedure:**

**Step 1:** Add to render.yaml

For database connections:
```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: postgres
      property: connectionString
```

For secrets (user provides):
```yaml
envVars:
  - key: JWT_SECRET
    sync: false
  - key: API_KEY
    sync: false
```

For generated values:
```yaml
envVars:
  - key: SESSION_SECRET
    generateValue: true
```

For hardcoded config:
```yaml
envVars:
  - key: NODE_ENV
    value: production
```

**Step 2:** Commit and push after user confirms (push auto-deploys)
```bash
git add render.yaml
git commit -m "Add missing environment variable: DATABASE_URL"
git push origin main
```

**Step 3:** If using `sync: false`, tell user (never ask them to paste secret into chat):
1. Open Dashboard: `https://dashboard.render.com/web/[service]/env`
2. Fill in secret value
3. Click "Save Changes"

**Step 4:** Redeploy (after user confirms)
```bash
render deploys create <service-id> --wait
```

**Verification:**
```bash
render logs -r <service-id> --tail -o text
# Should see successful startup
```

---

## Issue Category 2: Port Binding

### Problem: Port Binding Error

**Symptoms:**
- `EADDRINUSE: address already in use`
- `Health check timeout`
- Service starts but gets no traffic

**Diagnosis Steps:**

1. Check for hardcoded port:
```bash
# Look for hardcoded ports in code
grep -r "listen(3000" .
grep -r "port.*=" . | grep -v "process.env"
```

2. Check for localhost binding:
```bash
grep -r "localhost" .
grep -r "127.0.0.1" .
```

**Fix Procedure by Language:**

**Node.js / Express:**

Before (WRONG):
```javascript
app.listen(3000);
// or
app.listen(3000, 'localhost');
```

After (CORRECT):
```javascript
const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
```

**Python / Flask:**

Before (WRONG):
```python
app.run(port=5000)
```

After (CORRECT):
```python
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

**Python / Django:**

Ensure gunicorn uses $PORT:
```yaml
# In render.yaml
startCommand: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

**Go:**

Before (WRONG):
```go
http.ListenAndServe(":3000", handler)
```

After (CORRECT):
```go
port := os.Getenv("PORT")
if port == "" {
    port = "3000"
}
http.ListenAndServe(":"+port, handler)
```

**Verification:**
```bash
# Should see message like "Server running on port 10000"
render logs -r <service-id> --tail -o text
```

---

## Issue Category 3: Database Connection

### Problem: Cannot Connect to Database

**Symptoms:**
- `ECONNREFUSED 127.0.0.1:5432`
- `could not connect to server`
- `Connection refused`

**Diagnosis Steps:**

1. Check DATABASE_URL is set:
```bash
# Look in render.yaml
grep "DATABASE_URL" render.yaml
```

2. Verify database provisioned:
```bash
render services -o json
# Look for database service
```

3. Check connection code

**Fix Procedure:**

**Step 1:** Ensure DATABASE_URL in render.yaml
```yaml
envVars:
  - key: DATABASE_URL
    fromDatabase:
      name: postgres
      property: connectionString

databases:
  - name: postgres
    databaseName: myapp_prod
    plan: free
```

**Step 2:** Configure SSL if needed. Prefer internal Database URL (private network, same region). External URL: keep cert verification on (add `ca: <provider CA>` if not publicly trusted; libpq `sslmode=verify-full`). Never `rejectUnauthorized: false`.

**Node.js / pg:**
```javascript
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  // External URL only; internal URL needs no SSL
  ssl: process.env.NODE_ENV === 'production' ? {
    rejectUnauthorized: true
  } : false
});
```

**Python / psycopg2:**
```python
import psycopg2

conn = psycopg2.connect(
    os.environ['DATABASE_URL'],  # external URL only
    sslmode='verify-full',
    sslrootcert='system'  # libpq 16+; or provider CA file path
)
```

**Step 3:** Add connection pooling

**Node.js:**
```javascript
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,  # Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

**Python:**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    os.environ['DATABASE_URL'],
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

**Step 4:** Test connection
```javascript
// Add health check with DB ping
app.get('/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.status(200).json({ status: 'ok', database: 'connected' });
  } catch (err) {
    res.status(500).json({ status: 'error', database: 'disconnected' });
  }
});
```

---

## Issue Category 4: Build Failures

### Problem: Build Command Fails

**Symptoms:**
- `npm ERR!`
- `error: failed to compile`
- Build timeout

**Diagnosis Steps:**

1. Check build logs:
```bash
render logs -r <service-id> --type deploy --level error -o json
```

2. Identify error type:
- Missing dependency?
- Compilation error?
- Build timeout?

**Fix Procedures:**

**Missing Dependency:**

Check package.json/requirements.txt:
```json
{
  "dependencies": {
    "express": "^4.18.0"  // Add missing package
  }
}
```

**Build Command Wrong:**

Fix in render.yaml:
```yaml
# Node.js
buildCommand: npm ci && npm run build

# Python
buildCommand: pip install -r requirements.txt

# Go
buildCommand: go build -o bin/app .
```

**Build Timeout (Free tier: 15 minutes):**

Optimize:
```yaml
# Use ci instead of install (faster)
buildCommand: npm ci --prefer-offline && npm run build

# Remove unused dependencies
# Upgrade to paid tier for longer timeout
```

---

## Issue Category 5: Health Check Failures

### Problem: Health Check Timeout

**Symptoms:**
- `Health check timeout after 300 seconds`
- `failed to become healthy`

**Diagnosis Steps:**

1. Check app binds correct port
2. Check health check endpoint exists
3. Check startup time

**Fix Procedure:**

**Step 1:** Add health endpoint

**Node.js:**
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
    json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
})
```

**Step 2:** Configure in render.yaml
```yaml
healthCheckPath: /health
```

**Step 3:** Optimize startup time

Run slow operations after server starts:
```javascript
// Start server first
const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);

  // Then do slow operations
  initializeCache();
  warmupConnections();
});
```

---

## Issue Category 6: Memory Issues

### Problem: Out of Memory

**Symptoms:**
- `JavaScript heap out of memory`
- `Killed` (exit code 137)
- Service crashes randomly

**Diagnosis Steps:**

1. Check logs for OOM errors
2. Monitor memory usage
3. Identify memory leaks

**Fix Procedures:**

**Immediate Fix (Node.js):**

Raise heap size (if on paid plan):
```yaml
envVars:
  - key: NODE_OPTIONS
    value: --max-old-space-size=2048  # 2GB
```

**Long-term Fixes:**

1. **Profile memory usage:**
```javascript
// Add memory monitoring
setInterval(() => {
  const used = process.memoryUsage();
  console.log(`Memory: ${Math.round(used.heapUsed / 1024 / 1024)}MB`);
}, 60000);
```

2. **Optimize data processing:**
```javascript
// Process in chunks instead of all at once
for (let i = 0; i < data.length; i += 1000) {
  const chunk = data.slice(i, i + 1000);
  await processChunk(chunk);
}
```

3. **Fix memory leaks:**
- Clear intervals/timeouts
- Remove event listeners
- Close database connections
- Clear caches periodically

4. **Upgrade plan:**
- Free: 512 MB
- Starter: 512 MB
- Standard: 2 GB
- Pro: 4 GB+

---

## Issue Category 7: Runtime Crashes

### Problem: Service Crashes After Start

**Symptoms:**
- Service starts then exits
- `Process exited with code 1`
- Uncaught exceptions

**Diagnosis Steps:**

1. Get runtime logs:
```bash
render logs -r <service-id> --level error -o json
```

2. Find uncaught errors:
- Unhandled Promise rejections
- Uncaught exceptions
- Fatal errors

**Fix Procedure:**

**Add error handlers:**

**Node.js:**
```javascript
// Catch all uncaught errors
process.on('uncaughtException', (err) => {
  console.error('Uncaught Exception:', err);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Express error handler (add last)
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Internal server error' });
});
```

**Python:**
```python
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

try:
    # Your code
    app.run()
except Exception as e:
    logger.error(f"Fatal error: {e}", exc_info=True)
    raise
```

---

## Decision Tree: Where to Start

```
Deployment Failed?
├─ Build phase failed?
│  ├─ Check build logs for errors
│  ├─ Verify buildCommand is correct
│  ├─ Check dependencies installed
│  └─ Fix compilation errors
│
├─ Deploy phase failed?
│  ├─ Check start command
│  ├─ Verify port binding
│  ├─ Check environment variables
│  └─ Check health check endpoint
│
└─ Runtime failures?
   ├─ Check for uncaught exceptions
   ├─ Verify database connections
   ├─ Check memory usage
   └─ Review application logs
```

## Debugging Checklist

Before asking for help, verify:

- [ ] All environment variables declared in render.yaml
- [ ] Secrets have `sync: false` and are filled in Dashboard
- [ ] App binds to `process.env.PORT` (or equivalent)
- [ ] App binds to `0.0.0.0` (not localhost)
- [ ] Build command non-interactive
- [ ] Dependencies in package.json/requirements.txt
- [ ] DATABASE_URL set if using database
- [ ] /health endpoint exists (if using health checks)
- [ ] Local build works (`npm ci && npm run build`)
- [ ] Start command correct

## Advanced Troubleshooting

### Enable Debug Logging

Temporary only, with user confirmation: verbose/dev-mode logs can leak secrets and stack traces. Revert after debugging.

**Node.js:**
```yaml
envVars:
  - key: DEBUG
    value: "*"  # Enable all debug logs
  - key: NODE_ENV
    value: development  # More verbose logs
```

### Test Locally First

```bash
# Simulate Render environment
export PORT=10000
export DATABASE_URL="postgresql://..."
npm ci && npm run build && npm start
```

### Check Render Status

Issue may be platform-wide:
- https://status.render.com

## Getting Help

If still stuck after these steps:

1. **Gather information:**
   - Service ID
   - Error messages from logs
   - render.yaml content
   - Steps to reproduce

2. **Check documentation:**
   - https://render.com/docs

3. **Community support:**
   - Render Community Forum
   - Discord server
