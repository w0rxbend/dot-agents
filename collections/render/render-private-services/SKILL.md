---
name: render-private-services
description: >-
  Configures Render private services—internal-only apps that accept traffic
  exclusively from other Render services over the private network. Use when
  the user needs an internal API, microservice, gRPC server, sidecar, or any
  service that should not be publicly accessible. Also use when choosing
  between a private service and a background worker.
  Trigger terms: private service, pserv, internal service, internal API,
  microservice, gRPC, not public, private network service.
license: MIT
compatibility: Render private services (paid plans)
metadata:
  author: Render
  version: "1.0.0"
  category: compute
---

# Render Private Services

Private services match web services except they have **no public URL**.

## When to Use

- **Internal API** or **microservice** behind public gateway
- **gRPC**, **TCP** or other non-HTTP server that only your services call
- Infrastructure components (**Elasticsearch**, **ClickHouse**, **RabbitMQ**)
- Choosing between **private service** and **background worker**

Public-facing HTTP services: use **render-web-services**. Services that receive no traffic: use **render-background-workers**.

## Private Service vs Background Worker

| Criterion | Private Service | Background Worker |
|-----------|----------------|-------------------|
| Binds to port | **Yes** (required) | No |
| Receives private network traffic | **Yes** | No |
| Sends outbound traffic | Yes | Yes |
| Internal hostname | **Yes** | No |
| Use case | Internal APIs, gRPC, TCP servers | Queue consumers, async processors |

**Rule of thumb:** if process **listens on a port** and other services call it, it's a private service. If it **pulls work from a queue** and never receives requests, it's a background worker.

## How Private Services Work

- No `onrender.com` subdomain; not reachable from internet
- Reachable at `<service-name>:<port>` on private network, only by other Render services in same region and workspace
- Supports **any protocol**: HTTP, gRPC, TCP, WebSocket, custom binary protocols
- Same build/deploy lifecycle as web services (build command, start command, pre-deploy, health checks via private network)
- Supports persistent disks, scaling, Docker runtime, same as web services

## Connecting to a Private Service

Other services reference private service via its **internal hostname and port**:

```
http://<service-name>:<port>
```

In Blueprints, wire address with `fromService`:

```yaml
- key: INTERNAL_API_URL
  fromService:
    name: my-api
    type: pserv
    property: hostport
```

Available `fromService` properties for `pserv`:

| Property | Value |
|----------|-------|
| `host` | Internal hostname (e.g. `my-api`) |
| `port` | Port service listens on |
| `hostport` | `host:port` combined (e.g. `my-api:10000`) |

To reference specific env var from private service, use `envVarKey` instead of `property`.

## Port Binding

Private services **must bind to at least one port**.

- Bind to `0.0.0.0` (not `127.0.0.1` or `localhost`)
- `PORT` env var defaults to `10000`, but any non-restricted port works
- For non-HTTP protocols (gRPC, TCP), configure server on desired port and tell consumers `hostport`

## Blueprint Configuration

### Microservices pattern (gateway + internal services)

```yaml
services:
  - type: web
    name: gateway
    runtime: node
    plan: starter
    region: oregon
    buildCommand: npm ci && npm run build
    startCommand: npm start
    envVars:
      - key: USER_SERVICE_URL
        fromService:
          name: user-service
          type: pserv
          property: hostport
      - key: BILLING_SERVICE_URL
        fromService:
          name: billing-service
          type: pserv
          property: hostport

  - type: pserv
    name: user-service
    runtime: node
    plan: starter
    region: oregon
    buildCommand: npm ci
    startCommand: node server.js
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: db
          property: connectionString

  - type: pserv
    name: billing-service
    runtime: python
    plan: starter
    region: oregon
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn billing:app
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: db
          property: connectionString
```

## References

| Document | Contents |
|----------|----------|
| `references/patterns.md` | Microservice topology, gRPC setup, sidecar patterns, health checks for private services |

## Related Skills

- **render-web-services** — Public HTTP services
- **render-networking** — Private network, DNS, service discovery
- **render-background-workers** — Services that receive no traffic
- **render-blueprints** — Full `render.yaml` schema, `fromService` wiring
- **render-scaling** — Instance types and autoscaling for private services
