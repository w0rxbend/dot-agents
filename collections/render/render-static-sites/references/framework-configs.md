# Static Site Framework Configurations

## Framework Reference

### React (Create React App)

```yaml
buildCommand: npm ci && npm run build
staticPublishPath: build
```

### React / Vue / Svelte (Vite)

```yaml
buildCommand: npm ci && npm run build
staticPublishPath: dist
```

### Next.js (static export)

Requires `output: 'export'` in `next.config.js`:

```yaml
buildCommand: npm ci && NEXT_TELEMETRY_DISABLED=1 next build
staticPublishPath: out
```

For SSR (`next start`), use **Web Service** instead.

### Nuxt (static generate)

```yaml
buildCommand: npm ci && nuxt generate
staticPublishPath: .output/public
```

For SSR (`nuxt build` + server), use **Web Service**.

### SvelteKit (static adapter)

Requires `@sveltejs/adapter-static` in `svelte.config.js`:

```yaml
buildCommand: npm ci && npm run build
staticPublishPath: build
```

### Astro

Default static output:

```yaml
buildCommand: npm ci && ASTRO_TELEMETRY_DISABLED=1 astro build
staticPublishPath: dist
```

For SSR mode, use **Web Service**.

### Hugo

```yaml
buildCommand: hugo --minify
staticPublishPath: public
```

### Gatsby

```yaml
buildCommand: npm ci && GATSBY_TELEMETRY_DISABLED=1 gatsby build
staticPublishPath: public
```

### Docusaurus

```yaml
buildCommand: npm ci && npm run build
staticPublishPath: build
```

### Jekyll

```yaml
buildCommand: bundle exec jekyll build
staticPublishPath: _site
```

### Eleventy (11ty)

```yaml
buildCommand: npm ci && npx @11ty/eleventy
staticPublishPath: _site
```

### Angular

```yaml
buildCommand: npm ci && ng build --configuration production
staticPublishPath: dist/<project-name>/browser
```

Angular 17+ uses `browser` subfolder. Older versions use `dist/<project-name>`.

## Environment Variables

Common build-time env vars:

| Variable | Purpose |
|----------|---------|
| `NODE_VERSION` | Pin Node.js version (e.g. `20`) |
| `HUGO_VERSION` | Pin Hugo version |
| `PYTHON_VERSION` | Pin Python version (Jekyll, Pelican) |
| `SKIP_INSTALL_DEPS` | Set `true` to skip auto dependency install |
| `NEXT_TELEMETRY_DISABLED`, `ASTRO_TELEMETRY_DISABLED`, `GATSBY_TELEMETRY_DISABLED` | Set `1` (build-command prefix above or service env var): these CLIs send usage telemetry by default |
| `NODE_ENV` | Defaults to `production` on Render |
