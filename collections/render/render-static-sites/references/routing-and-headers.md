# Static Site Routing and Headers

## Redirect and Rewrite Rules

Configure in Dashboard (Settings > Redirects/Rewrites) or via Blueprint `routes` field.

### Rule types

| Type | Behavior | Status code |
|------|----------|-------------|
| `redirect` | Client-side redirect (browser URL changes) | 301 (permanent) or 302 (temporary) |
| `rewrite` | Server-side rewrite (browser URL unchanged) | Transparent |

### SPA catch-all (most common)

Every SPA needs this rule for client-side routing:

```yaml
routes:
  - type: rewrite
    source: /*
    destination: /index.html
```

Without it, direct navigation to `/dashboard` or `/about` returns 404 from CDN.

### Ordering

Render evaluates rules **top to bottom**. Place specific rules above catch-all rules:

```yaml
routes:
  # Specific redirects first
  - type: redirect
    source: /old-blog/*
    destination: /blog/*
  - type: redirect
    source: /docs
    destination: https://docs.example.com
  # SPA catch-all last
  - type: rewrite
    source: /*
    destination: /index.html
```

### Path patterns

| Pattern | Matches |
|---------|---------|
| `/exact` | Only `/exact` |
| `/path/*` | `/path/` and everything under it |
| `/*` | Everything (catch-all) |

## Custom Response Headers

Configure in Dashboard (Settings > Headers) or via Blueprint `headers` field.

### Security headers

```yaml
headers:
  - path: /*
    name: X-Frame-Options
    value: DENY
  - path: /*
    name: X-Content-Type-Options
    value: nosniff
  - path: /*
    name: Referrer-Policy
    value: strict-origin-when-cross-origin
  - path: /*
    name: Permissions-Policy
    value: camera=(), microphone=(), geolocation=()
```

### Cache headers for static assets

```yaml
headers:
  - path: /assets/*
    name: Cache-Control
    value: public, max-age=31536000, immutable
  - path: /index.html
    name: Cache-Control
    value: no-cache
```

Vite, Webpack and other bundlers add content hashes to asset filenames, so `immutable` is safe. Always revalidate entry point (`index.html`).

### CORS headers

```yaml
headers:
  - path: /api/*
    name: Access-Control-Allow-Origin
    value: https://app.example.com
  - path: /api/*
    name: Access-Control-Allow-Methods
    value: GET, POST, OPTIONS
```

## Automatic behaviors

- **HTTP → HTTPS** redirect automatic (no configuration needed)
- **Brotli compression** applied automatically
- **Cache invalidation** immediate on every deploy
