---
name: render-docker
description: >-
  Builds and deploys Docker containers on Render—Dockerfiles, multi-stage
  builds, Blueprint Docker fields, private registries, layer caching, and
  platform constraints. Use when the user mentions Docker,
  Dockerfile, container images, multi-stage builds, container registry,
  GHCR, ECR, BuildKit, dockerContext, runtime docker or image, or
  optimizing Docker builds on Render.
license: MIT
compatibility: >-
  Any Render compute service (web, private, worker, cron) with runtime: docker
  or runtime: image.
metadata:
  author: Render
  version: "1.0.0"
  category: deployment
---

# Render Docker Deployments

Render builds Docker images with BuildKit. Compute services supporting custom runtimes take `runtime: docker` (build repo Dockerfile) or `runtime: image` (pull prebuilt image, no Dockerfile build on Render). Templates and deeper patterns: `references/`.

## When to Use

- Writing or debugging Render service Dockerfile
- Choosing `runtime: docker` or `runtime: image` in Blueprint
- Private base images or prebuilt images with registry credentials
- Multi-stage builds, build args, secrets, layer caching
- Container image performance and security hardening on Render

Full Blueprint authoring: **render-blueprints**. End-to-end deploy flows: **render-deploy**.

## Blueprint Configuration

| Field | Role |
|-------|------|
| `dockerfilePath` | Dockerfile path (default `./Dockerfile`) |
| `dockerContext` | Build context directory (sent to daemon) |
| `dockerCommand` | Overrides container `CMD` after build |
| `image.url` | Image reference for `runtime: image` (registry/repo:tag or digest) |
| `registryCredential` | Private pull auth; often `fromRegistryCreds` naming Dashboard-stored credential |

Example sketch (values illustrative):

```yaml
services:
  - type: web
    name: api
    runtime: docker
    region: oregon
    plan: starter
    dockerfilePath: ./Dockerfile
    dockerContext: .
    dockerCommand: node server.js
    envVars:
      - key: PORT
        value: 10000
```

For `runtime: image`, set `image.url`, plus `registryCredential` if needed (see Registry Configuration).

## Multi-Stage Builds

Recommended for production. Builder stage compiles and installs dependencies. Minimal runner stage copies only artifacts and runtime files. Language-specific templates: `references/dockerfile-patterns.md`.

## Build Args vs Secrets

**Critical:** **Never pass secrets via `ARG`.** Build args persist in image layers, recoverable from image history or intermediate layers.

- Prefer runtime env vars (Render env vars / secret files) for app secrets.
- Build-time secrets (e.g. private package feeds): BuildKit secret mounts (`RUN --mount=type=secret,...`), not `ARG`.

## Registry Configuration

Private base images (`runtime: docker`) or prebuilt images (`runtime: image`) need auth:

- Store credentials in Render Dashboard under **Registry Credentials**.
- Reference them in Blueprint via `registryCredential.fromRegistryCreds.name` (match Dashboard name).

Common registries work (Docker Hub, GHCR, ECR, Google Artifact Registry, others). Per-provider steps: `references/registry-setup.md`.

Prebuilt image services do **not** auto-deploy when registry tag moves. After publishing new image, trigger manual redeploy or deploy hook.

## Layer Caching

- Render caches Docker layers between builds. Put rarely changing instructions early (see `references/optimization-guide.md`).
- **Tags and caching:** mutable tags like `latest` can resolve to stale cached images. Prefer immutable digest (`repo/image@sha256:...`) or version pin (`v1.2.3`).

## Platform Specifics

- Render builds **linux/amd64**. Do not assume other architectures in production images.
- Port binding as for native services: bind HTTP to `0.0.0.0:$PORT` (Render sets `PORT`).
- Health checks same as non-Docker web services (`healthCheckPath`, etc.).
- Render secret files appear under `/etc/secrets/`. Do not rely on repo-root secret paths in container unless image explicitly copies or mounts them.

## `.dockerignore` and Start Commands

- Always keep `.dockerignore` excluding `node_modules`, `.git`, `.env`, build artifacts, logs, OS junk. Cuts context upload, keeps local files out of layers. Lists and rationale: `references/optimization-guide.md`.
- **Custom start command:** put multiple shell steps in one shell form, e.g. `/bin/sh -c 'set -e; ./migrate && exec node server.js'`. Prefer `exec` so app gets signals for graceful shutdown.

## References

| Document | Contents |
|----------|----------|
| `references/dockerfile-patterns.md` | Multi-stage templates (Node, Python, Go, Ruby, Rust, static sites) |
| `references/registry-setup.md` | Docker Hub, GHCR, ECR, Artifact Registry + Blueprint wiring |
| `references/optimization-guide.md` | Layer order, `.dockerignore`, BuildKit cache mounts, debugging |

## Related Skills

- **render-deploy** — Deploy flows, Blueprint vs Dashboard, operational steps
- **render-blueprints** — Full `render.yaml` schema, wiring, validation
- **render-web-services** — Web service behavior, health checks, HTTP edge cases
