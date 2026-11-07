# Edge Functions

## Table of Contents

- [Cloudflare Workers](#cloudflare-workers)
- [Deno Deploy](#deno-deploy)
- [Vercel Edge Functions](#vercel-edge-functions)
- [Hono Framework](#hono-framework)
- [Comparison](#comparison)

## Cloudflare Workers

### Performance Characteristics

- **Cold Start**: <5ms (V8 isolates, not containers)
- **Locations**: 200+ global edge locations
- **Memory**: 128MB per request
- **CPU Time**: 50ms (free), 15s (paid)
- **Execution Model**: V8 isolates (shared runtime, isolated contexts)

### When to Use

- Global content delivery
- API gateway/middleware
- HTML rewriting (HTMLRewriter API)
- Edge authentication
- Low-latency API responses (<50ms)

### Setup

```bash
# Install Wrangler
npm install -g wrangler

# Opt out of Wrangler usage telemetry (on by default)
export WRANGLER_SEND_METRICS=false

# Login
wrangler login

# Initialize project
wrangler init my-worker

# Develop locally
wrangler dev

# Deploy
wrangler deploy
```

### Basic Worker

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    return new Response('Hello from Cloudflare Workers!');
  },
};
```

### Environment Variables & Secrets

**wrangler.toml**:
```toml
name = "my-worker"
main = "src/index.ts"
compatibility_date = "2024-01-01"
send_metrics = false  # no Wrangler telemetry for this project

[vars]
ENVIRONMENT = "production"

# Secrets (set via wrangler secret)
# TURSO_AUTH_TOKEN
# DATABASE_URL
```

**Set Secrets**:
```bash
# Set secret
wrangler secret put TURSO_AUTH_TOKEN

# List secrets
wrangler secret list
```

**Access in Worker**:
```typescript
export default {
  async fetch(request: Request, env: Env) {
    const token = env.TURSO_AUTH_TOKEN; // Secret
    const environment = env.ENVIRONMENT; // Variable

    return new Response(`Environment: ${environment}`);
  },
};
```

### D1 Database (SQLite)

Cloudflare's edge SQLite database.

```typescript
import { Hono } from 'hono'

type Bindings = {
  DB: D1Database
}

const app = new Hono<{ Bindings: Bindings }>()

app.get('/users', async (c) => {
  const { results } = await c.env.DB
    .prepare('SELECT * FROM users LIMIT 10')
    .all()

  return c.json(results)
})

app.post('/users', async (c) => {
  const { name, email } = await c.req.json()

  await c.env.DB
    .prepare('INSERT INTO users (name, email) VALUES (?, ?)')
    .bind(name, email)
    .run()

  return c.json({ success: true })
})

export default app
```

**wrangler.toml**:
```toml
[[d1_databases]]
binding = "DB"
database_name = "my-database"
database_id = "<database-id>"
```

### KV Store (Key-Value)

```typescript
import { Hono } from 'hono'

type Bindings = {
  CACHE: KVNamespace
}

const app = new Hono<{ Bindings: Bindings }>()

app.get('/cache/:key', async (c) => {
  const key = c.req.param('key')
  const value = await c.env.CACHE.get(key)

  if (!value) {
    return c.json({ error: 'Not found' }, 404)
  }

  return c.text(value)
})

app.put('/cache/:key', async (c) => {
  const key = c.req.param('key')
  const value = await c.req.text()

  // Store with 1 hour TTL
  await c.env.CACHE.put(key, value, {
    expirationTtl: 3600,
  })

  return c.json({ success: true })
})

export default app
```

### HTMLRewriter (Edge HTML Processing)

```typescript
class LinkTransformer {
  element(element: Element) {
    // Add UTM parameters to all links
    const href = element.getAttribute('href')
    if (href) {
      const url = new URL(href)
      url.searchParams.set('utm_source', 'edge')
      element.setAttribute('href', url.toString())
    }
  }
}

export default {
  async fetch(request: Request) {
    const response = await fetch(request)

    return new HTMLRewriter()
      .on('a', new LinkTransformer())
      .transform(response)
  },
}
```

## Deno Deploy

TypeScript-native edge runtime, deployed globally.

### Performance Characteristics

- **Cold Start**: <50ms
- **Locations**: Global edge (34 regions)
- **Memory**: 512MB per isolate
- **CPU Time**: 50ms per request
- **Execution Model**: V8 isolates

### When to Use

- TypeScript APIs (no build step)
- Real-time apps (WebSockets)
- Edge rendering
- Deno-compatible code

### Setup

```bash
# Install Deno (package manager)
brew install deno            # macOS/Linux; or: winget install DenoLand.Deno
# Or download the installer, inspect it, then run it
curl -fsSL https://deno.land/install.sh -o deno-install.sh && less deno-install.sh && sh deno-install.sh

# Deploy via GitHub integration (recommended)
# Or use deployctl

# Install deployctl
deno install -gArf jsr:@deno/deployctl@1.13.1   # pinned; Deno 2 needs -g for global installs

# Deploy
deployctl deploy --project=my-app main.ts
```

### Basic Server

```typescript
// Built-in server: no remote import needed
Deno.serve((req: Request) => {
  const url = new URL(req.url);

  if (url.pathname === "/api/hello") {
    return new Response(JSON.stringify({ message: "Hello from Deno!" }), {
      headers: { "content-type": "application/json" },
    });
  }

  return new Response("Not Found", { status: 404 });
});
```

### With Hono (Universal Framework)

```typescript
// Pin every remote import (verify current release); commit deno.lock so integrity is checked
import { Hono } from "jsr:@hono/hono@4.13.16";
import { createClient } from "npm:@libsql/client@0.18.0/web";

const app = new Hono();

const db = createClient({
  url: Deno.env.get("TURSO_URL")!,
  authToken: Deno.env.get("TURSO_TOKEN")!,
});

app.get("/", (c) => c.json({ message: "Hello from Deno!" }));

app.get("/api/users/:id", async (c) => {
  const id = c.req.param("id");

  // Query Turso edge database (parameterized; never interpolate input into SQL)
  const result = await db.execute({
    sql: "SELECT * FROM users WHERE id = ?",
    args: [id],
  });

  return c.json(result.rows);
});

Deno.serve(app.fetch);
```

### Environment Variables

```typescript
// Access environment variables
const apiKey = Deno.env.get("API_KEY");
const dbUrl = Deno.env.get("DATABASE_URL");

// Set via Deno Deploy dashboard or deployctl env file (gitignored; keeps secrets out of argv/history)
deployctl deploy --project=my-app --env-file=.env main.ts
```

### KV Store

```typescript
const kv = await Deno.openKv();

// Set value
await kv.set(["users", userId], userData);

// Get value
const entry = await kv.get(["users", userId]);
console.log(entry.value);

// Delete value
await kv.delete(["users", userId]);

// List keys
for await (const entry of kv.list({ prefix: ["users"] })) {
  console.log(entry.key, entry.value);
}
```

## Vercel Edge Functions

Edge functions integrated with Next.js and Vercel platform.

### Performance Characteristics

- **Cold Start**: <50ms
- **Locations**: 300+ global edge locations
- **Memory**: 128MB per function
- **CPU Time**: 30s per request
- **Execution Model**: V8 isolates

### When to Use

- Next.js apps (tight integration)
- Edge middleware
- A/B testing
- Personalization

### Setup (Next.js)

```typescript
// app/api/hello/route.ts
import { NextRequest, NextResponse } from 'next/server'

export const runtime = 'edge' // Enable edge runtime

export async function GET(request: NextRequest) {
  const geo = request.geo // Geolocation data

  return NextResponse.json({
    message: 'Hello from edge!',
    location: geo?.city,
    country: geo?.country,
  })
}
```

### Edge Middleware

```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  // A/B testing at edge
  const bucket = Math.random() < 0.5 ? 'A' : 'B'

  const response = NextResponse.next()
  response.cookies.set('bucket', bucket)

  // Rewrite based on bucket
  if (bucket === 'B') {
    return NextResponse.rewrite(new URL('/variant-b', request.url))
  }

  return response
}

export const config = {
  matcher: '/pricing',
}
```

### Edge Config

Fast global key-value store for Vercel Edge Functions.

```typescript
import { get } from '@vercel/edge-config'

export const runtime = 'edge'

export async function GET() {
  // Read from Edge Config (<10ms globally)
  const featureFlags = await get('featureFlags')

  return new Response(JSON.stringify(featureFlags))
}
```

## Hono Framework

### Why Hono

- **Universal**: Cloudflare Workers, Deno, Bun, Node.js, Vercel Edge
- **Fast**: 3-4x faster than Express
- **Small**: 14KB bundle size
- **TypeScript-first**: Full type safety

### Installation

```bash
npm install hono
```

### Basic API

```typescript
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import { etag } from 'hono/etag'

const app = new Hono()

// Middleware (cors() alone allows any origin: only for public, credential-free APIs)
app.use('*', cors({ origin: ['<your-app-origin>'] }))  // explicit allowlist
app.use('*', logger())
app.use('*', etag())

// Routes
app.get('/', (c) => c.json({ message: 'Hello Hono!' }))

app.get('/users/:id', async (c) => {
  const id = c.req.param('id')
  // Fetch user...
  return c.json({ id, name: 'John' })
})

app.post('/users', async (c) => {
  const body = await c.req.json()
  // Create user...
  return c.json({ success: true }, 201)
})

// Export for different runtimes
export default app
```

### Runtime-Specific Adapters

**Cloudflare Workers**:
```typescript
import { Hono } from 'hono'
const app = new Hono()
// ... routes ...
export default app
```

**Deno**:
```typescript
import { Hono } from "jsr:@hono/hono@4.13.16"  // pinned
const app = new Hono()
// ... routes ...
Deno.serve(app.fetch)
```

**Node.js**:
```typescript
import { Hono } from 'hono'
import { serve } from '@hono/node-server'

const app = new Hono()
// ... routes ...

serve(app)
```

**Bun**:
```typescript
import { Hono } from 'hono'
const app = new Hono()
// ... routes ...
export default app
```

### TypeScript Types

```typescript
import { Hono } from 'hono'

type Bindings = {
  DB: D1Database
  CACHE: KVNamespace
  TURSO_TOKEN: string
}

type Variables = {
  userId: string
}

const app = new Hono<{ Bindings: Bindings; Variables: Variables }>()

app.use('*', async (c, next) => {
  // Middleware with type safety
  c.set('userId', '123')
  await next()
})

app.get('/users', async (c) => {
  const userId = c.get('userId') // TypeScript knows this is string
  const token = c.env.TURSO_TOKEN // TypeScript knows this exists

  return c.json({ userId })
})
```

## Comparison

### Performance Matrix

| Platform | Cold Start | Global Locations | Memory | CPU Time | Free Tier |
|----------|-----------|------------------|--------|----------|-----------|
| **Cloudflare Workers** | <5ms | 200+ | 128MB | 50ms (10s paid) | 100k requests/day |
| **Deno Deploy** | <50ms | 34 | 512MB | 50ms | 100k requests/month |
| **Vercel Edge** | <50ms | 300+ | 128MB | 30s | Included with Vercel |

### Feature Comparison

| Feature | Cloudflare Workers | Deno Deploy | Vercel Edge |
|---------|-------------------|-------------|-------------|
| **TypeScript** | ✅ (build required) | ✅ Native | ✅ (build required) |
| **WebSockets** | ✅ Durable Objects | ✅ Native | ❌ |
| **Edge Database** | ✅ D1 (SQLite) | ✅ KV Store | ✅ Edge Config |
| **KV Store** | ✅ Workers KV | ✅ Deno KV | ✅ Edge Config |
| **Cron Jobs** | ✅ | ✅ | ❌ |
| **Streaming** | ✅ | ✅ | ✅ |
| **File Upload** | ✅ R2 | ❌ | ❌ |

### Use Case Recommendations

**Cloudflare Workers**:
- ✅ Lowest cold starts (<5ms)
- ✅ Most global locations (200+)
- ✅ Edge database (D1)
- ✅ File storage (R2)
- ❌ WebSockets require Durable Objects

**Deno Deploy**:
- ✅ TypeScript-native (no build)
- ✅ WebSockets support
- ✅ Deno ecosystem
- ✅ Simple deployment
- ❌ Fewer locations (34)

**Vercel Edge**:
- ✅ Next.js integration
- ✅ Most global locations (300+)
- ✅ Edge Config (fast KV)
- ✅ Edge middleware
- ❌ Vendor lock-in

## Best Practices

### Edge-Friendly Patterns

**1. Minimize Cold Start Time**:
```typescript
// ❌ Bad: Heavy imports
import { analyzeImage } from './ml-library'; // 5MB bundle

// ✅ Good: Lazy load or use edge-optimized libraries
const analyzeImage = await import('./edge-ml'); // 50KB
```

**2. Cache Aggressively**:
```typescript
import { Hono } from 'hono'
import { cache } from 'hono/cache'

const app = new Hono()

app.get(
  '/api/data',
  cache({
    cacheName: 'api-cache',
    cacheControl: 'public, max-age=3600',
  }),
  async (c) => {
    const data = await fetch('https://api.example.com/data')
    return c.json(await data.json())
  }
)
```

**3. Use Edge Databases**:
```typescript
// ✅ Good: Edge database (Turso, D1)
const user = await c.env.DB
  .prepare('SELECT * FROM users WHERE id = ?')
  .bind(userId)
  .first()

// ❌ Bad: Remote database (high latency)
const user = await fetch(`https://us-east-api.com/users/${userId}`)
```

### Error Handling

```typescript
import { Hono } from 'hono'

const app = new Hono()

app.onError((err, c) => {
  console.error(`${err}`)

  if (err instanceof HTTPException) {
    return c.json({ error: err.message }, err.status)
  }

  return c.json({ error: 'Internal Server Error' }, 500)
})

app.get('/users/:id', async (c) => {
  const id = c.req.param('id')

  try {
    const user = await fetchUser(id)
    if (!user) {
      throw new HTTPException(404, { message: 'User not found' })
    }
    return c.json(user)
  } catch (error) {
    throw new HTTPException(500, { message: 'Database error' })
  }
})
```

### Security

```typescript
import { Hono } from 'hono'
import { secureHeaders } from 'hono/secure-headers'
import { csrf } from 'hono/csrf'

const app = new Hono()

// Security headers
app.use('*', secureHeaders())

// CSRF protection
app.use('*', csrf())

// Rate limiting (Cloudflare Workers)
app.use('*', async (c, next) => {
  const ip = c.req.header('CF-Connecting-IP')
  const key = `rate-limit:${ip}`

  const count = await c.env.CACHE.get(key)
  if (count && parseInt(count) > 100) {
    return c.json({ error: 'Rate limit exceeded' }, 429)
  }

  await c.env.CACHE.put(key, String(parseInt(count || '0') + 1), {
    expirationTtl: 60, // 1 minute window
  })

  await next()
})
```
