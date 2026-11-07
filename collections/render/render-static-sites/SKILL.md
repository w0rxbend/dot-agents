---
name: render-static-sites
description: >-
  Deploys and configures static sites on Render's global CDN—build commands,
  publish paths, SPA routing, redirects, custom headers, and PR previews. Use
  when the user needs to deploy a static site, set up a React/Vue/Hugo/Gatsby
  frontend, configure SPA fallback routing, add redirect rules, customize
  response headers, or choose between a static site and a web service for
  their frontend.
  Trigger terms: static site, CDN, SPA, single-page app, React deploy,
  Vue deploy, Hugo, Gatsby, Docusaurus, Jekyll, staticPublishPath.
license: MIT
compatibility: Render static sites (free tier available)
metadata:
  author: Render
  version: "1.0.0"
  category: compute
---

# Render Static Sites

## When to Use

- Deploying **static site or SPA** (no server-side rendering)
- Choosing between **Static Site** and **Web Service** for frontend
- Configuring **SPA fallback routing**, **redirects/rewrites**, or **custom headers**
- Setting up **PR preview environments** for static site
- Troubleshooting **build failures** or **stale content** on CDN-hosted site

For SSR frameworks (Next.js, Nuxt, SvelteKit) needing running server, use **render-web-services** instead.

## Static Site vs Web Service

| Need | Use | Why |
|------|-----|-----|
| Pure HTML/CSS/JS, SPA, docs, blog | **Static Site** | Free, global CDN, instant cache invalidation |
| SSR (Next.js `next start`, Nuxt server) | **Web Service** | Needs running Node/Python/etc. process |
| Static export from SSR framework | **Static Site** | If framework supports full static export (Next.js `output: 'export'` in `next.config.js`, `nuxt generate`) |
| API backend | **Web Service** | Static sites cannot run server code |

**Key constraint:** Static sites are **not on the private network**. Cannot communicate with other Render services over internal hostnames.

## Build and Publish

| Setting | Purpose |
|---------|---------|
| `buildCommand` | Installs dependencies, builds assets (e.g. `npm ci && npm run build`) |
| `staticPublishPath` | Built output directory to serve (e.g. `build`, `dist`, `public`) |

Render auto-detects and installs dependencies. Set `SKIP_INSTALL_DEPS=true` to handle installation yourself in build command.

See `references/framework-configs.md` for build commands and publish paths for 10+ frameworks.

## SPA Routing and Redirects

Single-page apps need catch-all rule so CDN serves `index.html` for all routes instead of returning 404.

Configure **Redirect/Rewrite Rules** in Dashboard (Settings > Redirects/Rewrites) or via Blueprint `routes` field (see Blueprint Configuration).

For multi-path redirects (e.g. old blog URLs), add specific rules **above** catch-all so they take priority.

See `references/routing-and-headers.md` for redirect types, header rules, caching patterns.

## Custom Response Headers

Add security and performance headers from Dashboard (Settings > Headers) or Blueprint `headers` field:

```yaml
headers:
  - path: /*
    name: X-Frame-Options
    value: DENY
  - path: /assets/*
    name: Cache-Control
    value: public, max-age=31536000, immutable
```

## PR Previews

Static sites support automatic PR previews. Each pull request gets unique URL with built site.

- Enable in Dashboard: Settings > PR Previews
- Blueprint: set `previews.generation` to `automatic` or `manual`
- Preview URLs follow pattern `<service>-<pr-id>.onrender.com`

## Blueprint Configuration

```yaml
services:
  - type: web
    runtime: static
    name: my-frontend
    buildCommand: npm ci && npm run build
    staticPublishPath: dist
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
    headers:
      - path: /*
        name: X-Frame-Options
        value: DENY
    previews:
      generation: automatic
```

**Note:** Static sites use `type: web` with `runtime: static` in Blueprints. No separate `type: static`.

## CDN and Performance

- **Global CDN**, edge caching worldwide
- **Automatic TLS**
- **Brotli compression**
- **HTTP/2** by default
- **Immediate cache invalidation** on every deploy (zero-downtime, atomic deploys)
- **DDoS protection** included free

## Billing

Static sites have **free tier**. Usage counts against workspace-level monthly included amounts for:

- **Outbound bandwidth** (data served to users)
- **Pipeline minutes** (build time)

## Related Skills

- **render-blueprints** — Full `render.yaml` schema for static site fields
- **render-domains** — Custom domain and TLS setup
- **render-deploy** — Deploy flows, CLI, MCP operations
