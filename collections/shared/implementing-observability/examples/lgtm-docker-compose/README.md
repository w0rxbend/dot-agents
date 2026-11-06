# LGTM Stack Docker Compose

Local development observability stack (see "Production Deployment" below before shared use): Loki (Logs), Grafana (Visualization), Tempo (Traces), Mimir (Metrics).

## What is LGTM?

Open-source observability platform with unified UI for logs, metrics, and traces.

**Components:**
- **Loki** - Log aggregation (like Prometheus for logs)
- **Grafana** - Dashboards and visualization
- **Tempo** - Distributed tracing
- **Mimir** - Prometheus-compatible metrics (long-term storage)
- **Grafana Alloy** - OpenTelemetry collector

## Files

```
lgtm-docker-compose/
├── docker-compose.yml       # All services
├── grafana/
│   ├── datasources.yml      # Pre-configured datasources
│   └── dashboards/
├── loki/
│   └── loki-config.yaml
├── tempo/
│   └── tempo-config.yaml
├── mimir/
│   └── mimir-config.yaml
└── alloy/
    └── config.alloy         # OpenTelemetry collector config
```

## Quick Start

```bash
# Set GRAFANA_ADMIN_PASSWORD in a gitignored .env first
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f grafana

# Stop
docker-compose down
```

## Access Points

All ports bind 127.0.0.1 only.

- **Grafana UI:** http://localhost:3000 (admin / `GRAFANA_ADMIN_PASSWORD`)
- **Loki API:** http://localhost:3100
- **Tempo API:** http://localhost:3200
- **Mimir API:** http://localhost:9009
- **OTLP gRPC:** localhost:4317
- **OTLP HTTP:** localhost:4318

## docker-compose.yml

Use the bundled `docker-compose.yml`: pinned images (never `:latest`), ports on 127.0.0.1, anonymous auth off, admin password from `.env`, usage reporting to Grafana Labs off. Keep these in any copy.

## Pre-configured Datasources

```yaml
# grafana/datasources.yml
apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    isDefault: false
    editable: true

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    isDefault: false
    editable: true

  - name: Mimir
    type: prometheus
    access: proxy
    url: http://mimir:9009/prometheus
    isDefault: true
    editable: true
```

## Application Integration

### Python (FastAPI)

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure exporter
tracer_provider = TracerProvider()
otlp_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Set global tracer
from opentelemetry import trace
trace.set_tracer_provider(tracer_provider)

# Auto-instrument FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)
```

### TypeScript

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: 'http://localhost:4317',
  }),
  serviceName: 'my-app',
});

sdk.start();
```

## Querying in Grafana

### LogQL (Loki)

```logql
# All logs from service
{service_name="my-app"}

# Error logs only
{service_name="my-app"} |= "error"

# By trace ID
{service_name="my-app"} | json | trace_id="abc123"
```

### TraceQL (Tempo)

```traceql
# Find slow requests
{ duration > 1s }

# By service and endpoint
{ service.name = "api" && http.route = "/users" }
```

### PromQL (Mimir)

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])
```

## Production Deployment

For Kubernetes deployment, see the observability skill's Kubernetes manifests.

## Resources

- Grafana LGTM: https://grafana.com/oss/
- OpenTelemetry: https://opentelemetry.io/docs/
