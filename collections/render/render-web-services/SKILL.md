---
name: render-web-services
description: >-
  Configures Render web services—port binding, TLS, health checks, custom
  domains, auto-deploy, PR previews, persistent disks, and deploy lifecycle.
  Use when the user needs to set up a web service, fix health check failures,
  add a custom domain, configure zero-downtime deploys, or troubleshoot port
  binding issues.
license: MIT
compatibility: Render web services (native runtimes or Docker)
metadata:
  author: Render
  version: "1.0.0"
  category: compute
---

# Render Web Services

## When to Use

- Configure or debug **port binding**, **PORT**, **multi-port** web services
- **TLS/HTTPS** at edge vs inside container
- **Health checks** blocking or rolling back deploys
- **Custom domains**, DNS, certificate provisioning
- **Auto-deploy**, **CI-gated deploys**, **PR preview** generation
- **Persistent disks** and their effect on scaling and zero-downtime
- **Deploy lifecycle**: build, pre-deploy, swap, drain, **rollback**, shutdown delay

## Port Binding

- Listen on **`0.0.0.0`** (all interfaces). Binding only to **`localhost`** or **`127.0.0.1`** blocks Render’s proxy.
- HTTP listen port: **`PORT`** environment variable, set by Render. **Default is often `10000`**; change in service **Settings** (Dashboard).
- **Reserved ports** (do **not** bind app to these for normal traffic): **`18012`**, **`18013`**, **`19099`**.

### Multi-port Web Services

- Only **one** port gets **public** HTTP traffic: **`PORT`**.
- **Additional** open ports: Render’s **private network** only, not public internet via same public URL pattern.

## TLS and HTTPS

- **TLS terminates at Render’s edge.** Clients get HTTPS; process typically gets **plain HTTP** on `PORT`.
- Platform handles client **HTTPS redirect** at edge.
- **Do not terminate TLS inside app** for primary public listener unless rare, explicit need. Standard Web Services assume HTTP behind proxy.

## Health Checks

- Set path via **`healthCheckPath`** (Blueprint) or **Health Check Path** field (Dashboard).
- Render sends **HTTP GET** to that path. Responses must be **`2xx` or `3xx`**.
- **Failed health checks** prevent new deploy from **going live** (no production traffic).
- Probes run at **repeat interval** with per-request **timeout**, both **configurable** in service settings (Dashboard).
- Frequency, timeouts, tuning, pitfalls: `references/health-check-patterns.md`.

## Custom Domains

- Point DNS **CNAME** at **`[service-name].onrender.com`** (service hostname from Dashboard).
- Render **automatically provisions and renews** TLS certificates for verified domains.
- **Apex** (root) domains: where plain CNAME at `@` is unsupported, use provider-specific **CNAME-like** or flattened records.
- **Wildcard** domains (e.g. `*.example.com`) supported when configured and verified.
- Multiple custom domains per service supported; Blueprints list them under **`domains`** field.

Dashboard steps, verification, troubleshooting: `references/custom-domains.md`.

## Auto-Deploy and PR Previews

- **`autoDeployTrigger`** (Blueprint) / auto-deploy settings control when production deploys run:
  - **`commit`** — deploy on every push to tracked branch
  - **`checksPass`** — deploy only when required **Git checks** pass
  - **`off`** — **manual** deploys only (Dashboard, CLI, hooks)
- **PR previews**: Blueprint **`previews.generation`** (plus related preview settings). Generation depends on repo integration and plan.

## Persistent Disks

- Attach via **`disk`** field in Blueprint (or equivalent Dashboard storage settings).
- Attached persistent disk means **single-instance** only: no **horizontal scaling**.
- **Zero-downtime deploys are disabled** with persistent disk attached; rollout follows different pattern.
- **Disk size increases** allowed; **decreases** not.
- Disk **not mounted during build phase**, only at **runtime**.

## Deploy Lifecycle

Typical flow:

1. **Build** — clone repo, run **`buildCommand`**, produce runnable artifact/image.
2. **Pre-deploy command** (optional) — runs in **new** image **before** traffic switches; use for **migrations**. If it **fails**, deploy is **canceled**.
3. **Deploy** — new instances start; health checks must pass before traffic moves.
4. **Zero-downtime swap** (when applicable) — traffic shifts to new instances; **old instances drain** in-flight work.

- **`maxShutdownDelaySeconds`** (range **1–300**, **default 30**) caps how long old instances keep handling requests during drain before shutdown.
- **Rollbacks** — revert to **previous successful deploy** from Dashboard.

Full sequence, hooks, filters, triggers, CLI: `references/deploy-lifecycle.md`.

## Free Tier Notes

Free Web Services have **separate limits**: e.g. **no custom domains** on free instance type; services **spin down after inactivity** (cold start on next request). Treat free-tier behavior as distinct from paid Web Service defaults when advising on domains, uptime, scaling.

## Related Skills

- **render-deploy** — Blueprints, first-time deploy, `render.yaml` structure
- **render-docker** — Docker-based Web Services, image/runtime details
- **render-networking** — Private network, internal URLs, multi-port private listeners
- **render-scaling** — Instance counts, plans, scaling constraints (including disk interactions)
