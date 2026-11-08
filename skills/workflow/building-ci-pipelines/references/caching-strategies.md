# Caching Strategies for CI Pipelines

## Table of Contents

1. [Cache Fundamentals](#cache-fundamentals)
2. [GitHub Actions Caching](#github-actions-caching)
3. [GitLab CI Caching](#gitlab-ci-caching)
4. [Docker Layer Caching](#docker-layer-caching)
5. [Remote Caching (Turborepo/Nx)](#remote-caching-turboreponx)
6. [Multi-Layer Strategies](#multi-layer-strategies)
7. [Cache Invalidation](#cache-invalidation)

## Cache Fundamentals

### What to Cache

**Dependencies:**
- `node_modules` (Node.js)
- `~/.cargo` (Rust)
- `~/.cache/pip` (Python)
- `~/go/pkg/mod` (Go)

**Build Outputs:**
- `dist/`, `build/` (compiled code)
- `.next/`, `.nuxt/` (framework builds)
- `target/` (Rust)

**Intermediate Artifacts:**
- `tsconfig.tsbuildinfo` (TypeScript)
- `.vite/` (Vite)
- Coverage data

### Cache Key Design

**Good cache keys:**
```yaml
# Dependencies - invalidate on lock file change
key: deps-${{ hashFiles('**/package-lock.json') }}

# Build outputs - invalidate on source change
key: build-${{ hashFiles('src/**/*.ts') }}

# OS-specific
key: ${{ runner.os }}-deps-${{ hashFiles('**/package-lock.json') }}
```

**Bad cache keys:**
```yaml
# Too generic - never invalidates
key: node-modules

# Too specific - low cache hit rate
key: build-${{ github.sha }}
```

### Cache Restore Keys

Give fallback keys:
```yaml
key: ${{ runner.os }}-deps-${{ hashFiles('**/package-lock.json') }}
restore-keys: |
  ${{ runner.os }}-deps-
  ${{ runner.os }}-
```

## GitHub Actions Caching

### Automatic Language Caching

```yaml
# Node.js
- uses: actions/setup-node@v4
  with:
    node-version: 24
    cache: 'npm'  # Automatically caches ~/.npm

# Python
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'

# Go
- uses: actions/setup-go@v5
  with:
    go-version: '1.23'
    cache: true

# Rust (use external action)
- uses: Swatinem/rust-cache@v2
```

### Manual Cache Control

```yaml
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      ~/.cache
      node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

### Cache Limits

- **Size limit:** 10GB per repository
- **Retention:** 7 days for inactive caches
- **Entries:** Unlimited (until 10GB total)

### Cache Hit Reporting

```yaml
- name: Cache dependencies
  id: cache
  uses: actions/cache@v4
  with:
    path: node_modules
    key: deps-${{ hashFiles('package-lock.json') }}

- name: Install dependencies
  if: steps.cache.outputs.cache-hit != 'true'
  run: npm ci

- name: Report cache hit
  run: echo "Cache hit: ${{ steps.cache.outputs.cache-hit }}"
```

## GitLab CI Caching

### Basic Cache

```yaml
cache:
  key: "${CI_COMMIT_REF_SLUG}"
  paths:
    - node_modules/
    - .npm/

build:
  script:
    - npm ci
    - npm run build
```

### Per-Job Cache

```yaml
test:
  cache:
    key: test-cache
    paths:
      - node_modules/
  script:
    - npm test

build:
  cache:
    key: build-cache
    paths:
      - node_modules/
      - dist/
  script:
    - npm run build
```

### Cache Policies

```yaml
# Only download cache (don't update)
cache:
  key: deps
  paths:
    - node_modules/
  policy: pull

# Only upload cache (don't download)
cache:
  key: deps
  paths:
    - node_modules/
  policy: push
```

### Fallback Keys

```yaml
cache:
  key:
    files:
      - package-lock.json
  fallback_keys:
    - default-npm-cache
  paths:
    - node_modules/
```

## Docker Layer Caching

### BuildKit Cache

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build with cache
  uses: docker/build-push-action@v5
  with:
    context: .
    cache-from: type=registry,ref=ghcr.io/${{ github.repository }}:buildcache
    cache-to: type=registry,ref=ghcr.io/${{ github.repository }}:buildcache,mode=max
```

### Multi-Stage Dockerfile Optimization

```dockerfile
# Base stage - changes infrequently
FROM node:24-alpine AS base
WORKDIR /app

# Dependencies stage - changes when package.json changes
FROM base AS deps
COPY package.json package-lock.json ./
RUN npm ci

# Build stage - changes when source changes
FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production stage - minimal final image
FROM base AS runner
COPY --from=builder /app/dist ./dist
COPY --from=deps /app/node_modules ./node_modules
CMD ["node", "dist/index.js"]
```

### GitHub Actions Docker Cache

```yaml
- name: Docker meta
  id: meta
  uses: docker/metadata-action@v5
  with:
    images: ghcr.io/${{ github.repository }}

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    cache-from: |
      type=registry,ref=ghcr.io/${{ github.repository }}:buildcache
      type=registry,ref=ghcr.io/${{ github.repository }}:latest
    cache-to: type=registry,ref=ghcr.io/${{ github.repository }}:buildcache,mode=max
```

## Remote Caching (Turborepo/Nx)

### Turborepo Remote Cache

**Setup:**
```bash
npx turbo telemetry disable  # turbo telemetry is on by default
npx turbo login
npx turbo link
```

**CI Usage:**
```yaml
- name: Build with remote cache
  run: npx turbo run build
  env:
    TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
    TURBO_TEAM: ${{ vars.TURBO_TEAM }}
    TURBO_TELEMETRY_DISABLED: 1  # turbo telemetry is on by default
```

### Nx Cloud

**Setup:**
```bash
npx nx connect-to-nx-cloud
```

**CI Usage:**
```yaml
- name: Build with Nx Cloud
  run: npx nx affected -t build
  env:
    NX_CLOUD_ACCESS_TOKEN: ${{ secrets.NX_CLOUD_ACCESS_TOKEN }}
```

## Multi-Layer Strategies

### Layer 1: Package Manager Cache

```yaml
- uses: actions/setup-node@v4
  with:
    cache: 'npm'  # Caches ~/.npm
```

### Layer 2: Node Modules Cache

```yaml
- uses: actions/cache@v4
  with:
    path: node_modules
    key: deps-${{ hashFiles('package-lock.json') }}
```

### Layer 3: Build Tool Cache (Nx)

```yaml
- uses: actions/cache@v4
  with:
    path: .nx/cache
    key: nx-${{ hashFiles('nx.json') }}
```

### Layer 4: Build Outputs Cache

```yaml
- uses: actions/cache@v4
  with:
    path: |
      apps/**/dist
      packages/**/dist
    key: build-${{ hashFiles('src/**/*.ts') }}
```

### Layer 5: Remote Cache (Turborepo/Nx)

```yaml
env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
```

## Cache Invalidation

### When to Invalidate

**Dependency changes** (lock file hash) and **source code changes** (source hash): see `deps-` and `build-` keys in [Cache Key Design](#cache-key-design).

**Configuration changes:**
```yaml
key: config-${{ hashFiles('tsconfig.json', 'vite.config.ts') }}
```

### Manual Invalidation

**GitHub Actions:**
Delete cache via API (confirm cache ID with user first):
```bash
GH_TELEMETRY=false gh api repos/{owner}/{repo}/actions/caches/{cache_id} --method DELETE
```

**GitLab CI:**
Build > Pipelines > **Clear runner caches**, or bump cache key prefix (see [Stale Cache](#stale-cache)). Not `jobs/{job_id}/erase`: that permanently deletes job log and artifacts.

### Time-Based Invalidation

```yaml
key: cache-${{ runner.os }}-${{ github.run_number }}
restore-keys: |
  cache-${{ runner.os }}-
```

Run number is cache key; falls back to previous runs.

## Best Practices

**DO:**
- Cache dependencies separately from builds
- Use remote caching for monorepos
- Monitor cache hit rates

**DON'T:**
- Cache sensitive data
- Cache generated files in git

## Troubleshooting

### Low Cache Hit Rate

Check cache key specificity:
```yaml
# Too specific (low hits)
key: build-${{ github.sha }}

# Better
key: build-${{ hashFiles('src/**') }}
```

### Cache Size Issues

Check cache size:
```bash
GH_TELEMETRY=false gh api repos/{owner}/{repo}/actions/cache/usage
```

Shrink cache:
```yaml
# Only cache necessary files
path: |
  node_modules
  !node_modules/.cache
```

### Stale Cache

Force cache refresh:
```yaml
key: v2-deps-${{ hashFiles('package-lock.json') }}
```

Bump version prefix to invalidate old caches.
