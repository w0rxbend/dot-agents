# Private Service Patterns

## Microservice Topology

Most common private service pattern is **public gateway + internal microservices**:

```
Internet → [Web Service: gateway] → Private Network → [pserv: user-service]
                                                    → [pserv: billing-service]
                                                    → [pserv: notification-service]
```

Gateway (web service) is only public-facing service. All internal services use `type: pserv` and communicate over private network.

### Wiring in Blueprints

Each internal service exposes its address via `fromService`:

```yaml
envVars:
  - key: USER_SERVICE_URL
    fromService:
      name: user-service
      type: pserv
      property: hostport
```

Gateway concatenates protocol + hostport in its code:

```javascript
const userServiceUrl = `http://${process.env.USER_SERVICE_URL}`;
```

## gRPC Setup

1. Configure gRPC server to listen on `0.0.0.0:<PORT>` (use `PORT` env var or any non-restricted port)
2. Set `type: pserv` in Blueprint
3. Consumers connect via `<service-name>:<port>` with gRPC client

```yaml
services:
  - type: pserv
    name: grpc-service
    runtime: go
    plan: starter
    region: oregon
    buildCommand: go build -o server .
    startCommand: ./server
    envVars:
      - key: GRPC_PORT
        value: "50051"
```

**Note:** gRPC uses HTTP/2 over private network; plaintext is common there. Private network is not an auth boundary: any service in same workspace and region can reach pserv, so authenticate internal callers (shared secret from env var, JWT or mTLS) and add TLS for sensitive payloads when threat model calls for it.

## Sidecar Pattern

Run supporting infrastructure (metrics collectors, log aggregators, proxies) as private services:

```yaml
services:
  - type: pserv
    name: otel-collector
    runtime: docker
    plan: starter
    region: oregon
    dockerfilePath: ./collector/Dockerfile
    startCommand: otelcol --config /etc/otel-config.yaml
```

Application services send telemetry to `otel-collector:<port>` on private network.

## Health Checks for Private Services

If service exposes HTTP endpoint, configure health check path:

```yaml
services:
  - type: pserv
    name: internal-api
    healthCheckPath: /health
```

For non-HTTP services (gRPC, TCP), Render checks that process is running and port is bound. No custom health check for non-HTTP protocols.

## Port Binding

- Multiple ports: service can listen on several, but `fromService` only exposes primary port via `property: port`

### Restricted ports

System ports (typically 0-1023) may be restricted. Use ports >= 1024.

## Private Service vs Web Service

For public access **and** internal access, use **web service**. Web services get both public URL and internal hostname on private network.
