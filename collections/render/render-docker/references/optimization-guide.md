# Docker build optimization on Render

Render uses BuildKit and caches Docker layers between builds.

## Layer ordering (maximize cache hits)

1. Copy dependency manifests first (`package.json`, `package-lock.json`, `requirements.txt`, `go.mod`, `Gemfile`, etc.).
2. Install dependencies in dedicated `RUN` (or cache mounts, see below).
3. Copy application source last.

App code changes should **not** rebuild dependency layers. Dependency-only changes may rebuild source layers, usually cheaper than full reinstall each time.

## `.dockerignore`

Exclude anything build or runtime image does not need. Typical entries:

```
node_modules
.git
.env
.env.*
__pycache__
*.pyc
.next
dist
build
*.log
.DS_Store
coverage
.vscode
.idea
```

Overly aggressive `.dockerignore` rules often cause “file not found” errors in `COPY`. If build fails after tightening ignore rules, verify every `COPY` path is still in context.

## Multi-stage benefits

- **Smaller final image** — no compilers, headers, or devDependencies in production.
- **Faster deploys** — less to pull and extract per instance.
- **Security** — fewer packages and tools in attack surface.

## BuildKit on Render

Available:

- **Cache mounts:** `RUN --mount=type=cache,target=/root/.npm ...` or pip/npm/yarn caches speed installs.
- **Secret mounts:** `RUN --mount=type=secret,id=npmrc ...` for build-time private registry auth **without** baking secrets into layers.

Enable features with syntax directive when needed:

```dockerfile
# syntax=docker/dockerfile:1
```

## Image size tips

- Prefer `-alpine`, `-slim`, or distroless bases when your stack allows.
- After `apt-get install`, remove lists: `rm -rf /var/lib/apt/lists/*`.
- Combine related `RUN` instructions to cut layer count unless caching suffers.
- Strip debug symbols in compiled languages (`-ldflags="-s -w"` for Go, release builds for Rust).

## Build caching on Render

- Layers reused when instructions and inputs match previous builds.
- **Ordering matters:** put slowest, most stable steps **early**.
- Intentional cache bust: pass build arg that changes when full rebuild wanted (non-secret values only).

## Debugging failed builds

1. Read Render build logs end-to-end. BuildKit often names failing step.
2. **Missing files:** verify paths relative to `dockerContext`; confirm `.dockerignore` does not exclude them.
3. **Wrong platform:** artifacts must target linux/amd64 (local Docker emulation can hide issues).
4. **Missing system libraries:** add packages in right stage: builder for compile-time, runner for run-time.
5. **Out-of-memory:** large parallel compilations may need less parallelism, or larger local/staging iteration loop before pushing.

## Mutable tags vs digests

Even with good Dockerfile caching, deployed images on tags like `latest` can appear “stuck” if registry or platform layer caches by tag. Prefer version tags or SHA256 digests for anything that must be reproducible.
