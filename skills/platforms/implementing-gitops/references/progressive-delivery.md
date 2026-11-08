# Progressive Delivery Patterns

## Table of Contents

1. [Deployment Strategies](#deployment-strategies)
2. [Argo Rollouts](#argo-rollouts)
3. [Flagger Integration](#flagger-integration)
4. [Metrics and Analysis](#metrics-and-analysis)

## Deployment Strategies

### Strategy Comparison

| Strategy | Downtime | Rollback Speed | Resource Usage | Complexity |
|----------|----------|----------------|----------------|------------|
| **AllAtOnce** | Yes | Manual | Low | Low |
| **Rolling** | No | Gradual | Medium | Low |
| **Canary** | No | Fast | Medium | Medium |
| **Blue-Green** | No | Instant | High (2x) | Medium |
| **A/B Testing** | No | Fast | Medium | High |

### When to Use

- **Canary:** Production deployments; gradual rollout on real traffic, metric-based validation
- **Blue-Green:** When instant rollback is critical
- **Rolling:** Kubernetes default; non-critical services with simple requirements
- **A/B Testing:** Feature validation on specific user segments

## Argo Rollouts

### Installation

```bash
# Download assets of a pinned release (not releases/latest), review, then apply
ROLLOUTS_VERSION=v1.10.2
BIN=kubectl-argo-rollouts-$(uname -s | tr '[:upper:]' '[:lower:]')-amd64
# GH_TELEMETRY=false: gh sends usage telemetry by default
GH_TELEMETRY=false gh release download "$ROLLOUTS_VERSION" -R argoproj/argo-rollouts \
  -p install.yaml -p argo-rollouts-checksums.txt -p "$BIN"
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f install.yaml

# Install kubectl plugin (or: brew install argoproj/tap/kubectl-argo-rollouts);
# verify the binary against the release checksums before installing
sha256sum --ignore-missing -c argo-rollouts-checksums.txt &&
  chmod +x "./$BIN" && sudo mv "./$BIN" /usr/local/bin/kubectl-argo-rollouts
```

### Basic Canary Rollout

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp
  namespace: myapp
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 1m}
      - setWeight: 40
      - pause: {duration: 1m}
      - setWeight: 60
      - pause: {duration: 1m}
      - setWeight: 80
      - pause: {duration: 1m}
  revisionHistoryLimit: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:v2
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

### Canary with Analysis

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 30s}
      - analysis:
          templates:
          - templateName: success-rate
          args:
          - name: service-name
            value: myapp-canary
      - setWeight: 50
      - pause: {duration: 30s}
      - analysis:
          templates:
          - templateName: success-rate
          - templateName: latency
          args:
          - name: service-name
            value: myapp-canary
      - setWeight: 80
      - pause: {duration: 30s}
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:v2
        ports:
        - containerPort: 8080
```

### AnalysisTemplate: Success Rate

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
  - name: service-name
  metrics:
  - name: success-rate
    interval: 5m
    count: 3
    successCondition: result[0] >= 0.95
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          sum(rate(
            http_requests_total{service="{{args.service-name}}",status=~"2.."}[5m]
          )) /
          sum(rate(
            http_requests_total{service="{{args.service-name}}"}[5m]
          ))
```

### AnalysisTemplate: Latency

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: latency
spec:
  args:
  - name: service-name
  metrics:
  - name: latency-p95
    interval: 5m
    count: 3
    successCondition: result[0] <= 500
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          histogram_quantile(0.95,
            sum(rate(
              http_request_duration_seconds_bucket{service="{{args.service-name}}"}[5m]
            )) by (le)
          ) * 1000
```

### Blue-Green Deployment

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp
spec:
  replicas: 5
  strategy:
    blueGreen:
      activeService: myapp-active
      previewService: myapp-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 300
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:v2
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-active
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-preview
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
```

### Canary with Ingress Traffic Splitting

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp
spec:
  replicas: 5
  strategy:
    canary:
      canaryService: myapp-canary
      stableService: myapp-stable
      trafficRouting:
        nginx:
          stableIngress: myapp-ingress
      steps:
      - setWeight: 10
      - pause: {duration: 1m}
      - setWeight: 20
      - pause: {duration: 1m}
      - setWeight: 50
      - pause: {duration: 2m}
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:v2
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-stable
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: myapp-canary
spec:
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
```

### Rollout CLI Commands

```bash
# List rollouts
kubectl argo rollouts list rollouts

# Get rollout status
kubectl argo rollouts get rollout myapp

# Watch rollout progress
kubectl argo rollouts get rollout myapp --watch

# Promote rollout (manual step)
kubectl argo rollouts promote myapp

# Abort rollout
kubectl argo rollouts abort myapp

# Retry failed rollout
kubectl argo rollouts retry rollout myapp

# View rollout history
kubectl argo rollouts history rollout myapp

# Rollback to previous version
kubectl argo rollouts undo myapp

# Restart rollout
kubectl argo rollouts restart myapp
```

## Flagger Integration

### Installation

```bash
# Add Flagger Helm repository
helm repo add flagger https://flagger.app

# Install Flagger with Prometheus (pinned chart version)
helm upgrade -i flagger flagger/flagger --version 1.45.0 \
  --namespace flux-system \
  --set prometheus.install=true \
  --set meshProvider=kubernetes
```

Dashboards: skip the `flagger/grafana` chart (old Grafana, usage reporting to Grafana Labs on, anonymous Admin when no password set). Import `charts/grafana/dashboards/*.json` from fluxcd/flagger at the pinned release into your own Grafana, run with `GF_ANALYTICS_REPORTING_ENABLED=false` and `GF_ANALYTICS_CHECK_FOR_UPDATES=false`.

### Canary with Flagger

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
  namespace: myapp
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  service:
    port: 80
    targetPort: 8080
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 1m
    webhooks:
    - name: load-test
      url: http://flagger-loadtester.test/
      timeout: 5s
      metadata:
        type: cmd
        cmd: "hey -z 1m -q 10 -c 2 http://myapp-canary.myapp/"
```

### Flagger with Service Mesh (Istio)

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
  namespace: myapp
spec:
  provider: istio
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  service:
    port: 80
    targetPort: 8080
    gateways:
    - myapp-gateway
    hosts:
    - myapp.example.com
  analysis:
    interval: 30s
    threshold: 10
    maxWeight: 50
    stepWeight: 5
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500
      interval: 1m
```

### Flagger Blue-Green

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
  namespace: myapp
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  service:
    port: 80
  analysis:
    interval: 1m
    threshold: 3
    iterations: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    webhooks:
    - name: smoke-test
      url: http://flagger-loadtester/
      timeout: 30s
      metadata:
        type: cmd
        cmd: "curl -f http://myapp-canary.myapp/ || exit 1"
  strategy:
    type: bluegreen
```

### A/B Testing with Flagger

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
  namespace: myapp
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  service:
    port: 80
  analysis:
    interval: 1m
    threshold: 10
    iterations: 10
    match:
    - headers:
        x-canary:
          exact: "insider"
    - headers:
        cookie:
          regex: "^(.*?;)?(canary=always)(;.*)?$"
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
```

## Metrics and Analysis

### Prometheus Metrics for Analysis

```yaml
# Success rate metric
sum(rate(http_requests_total{status=~"2.."}[5m])) /
sum(rate(http_requests_total[5m]))

# Latency P95
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
) * 1000

# Error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m]))

# Request rate
sum(rate(http_requests_total[5m]))
```

### Custom Metrics Provider

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: custom-metrics
spec:
  args:
  - name: service-name
  metrics:
  - name: custom-metric
    interval: 5m
    successCondition: result >= 0.95
    provider:
      web:
        url: "http://metrics-service/api/metrics?service={{args.service-name}}"
        jsonPath: "{$.success_rate}"
```

### Analysis with Multiple Providers

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: multi-metrics
spec:
  metrics:
  - name: prometheus-metric
    provider:
      prometheus:
        address: http://prometheus:9090
        query: "sum(rate(http_requests_total[5m]))"
  - name: datadog-metric
    provider:
      datadog:
        apiKey:
          secretKeyRef:
            name: datadog-secret
            key: api-key
        query: "avg:system.cpu.user{service:myapp}"
  - name: newrelic-metric
    provider:
      newRelic:
        profile: myapp-profile
        query: "SELECT average(duration) FROM Transaction WHERE appName = 'myapp'"
```

## Best Practices

### Metrics Selection

- Monitor success rate (errors per request)
- Track latency percentiles (P50, P95, P99)
- Measure resource usage (CPU, memory)
- Watch custom business metrics

### Rollout Configuration

- Start with small traffic weights (5-10%)
- Use multiple analysis steps
- Set failure thresholds
- Set reasonable timeouts
- Enable automatic rollback

### Testing

- Test rollout strategies in staging first
- Validate analysis templates against historical data
- Simulate failures to verify rollback
