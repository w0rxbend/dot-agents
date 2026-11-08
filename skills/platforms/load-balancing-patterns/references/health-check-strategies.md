# Health Check Strategies

## Table of Contents

1. [Health Check Types](#health-check-types)
2. [Health Endpoint Design](#health-endpoint-design)
3. [Health Check Parameters](#health-check-parameters)
4. [Health Check Hysteresis](#health-check-hysteresis)
5. [Advanced Health Check Patterns](#advanced-health-check-patterns)
6. [Monitoring Health Checks](#monitoring-health-checks)
7. [Troubleshooting Health Check Issues](#troubleshooting-health-check-issues)

## Health Check Types

### TCP Connect Check

**How it works:** Load balancer attempts TCP connection to backend port

**Validates:**
- Port open and accepting connections
- Network connectivity
- Process listening on port

**Does NOT validate:**
- Application works correctly
- Dependencies available
- Application can handle requests

**Use for:**
- Non-HTTP services
- Basic availability monitoring
- Fast failure detection
- Protocols without health endpoints

**Example (NGINX):**
```nginx
upstream backend {
    server backend1:8080 max_fails=3 fail_timeout=30s;
    server backend2:8080 max_fails=3 fail_timeout=30s;
}
```

### HTTP/HTTPS Health Check

**How it works:** Load balancer sends HTTP GET, validates response

**Validates:**
- HTTP service responds
- Expected status code returned (200, 204)
- Optional: response body contains expected content
- Optional: response headers match criteria

**Example (HAProxy):**
```haproxy
backend web_servers
    option httpchk GET /health HTTP/1.1\r\nHost:\ example.com
    http-check expect status 200
    http-check expect rstring "healthy"

    server web1 192.168.1.101:8080 check inter 5s fall 3 rise 2
    server web2 192.168.1.102:8080 check inter 5s fall 3 rise 2
```

**Example (AWS ALB):**
```hcl
resource "aws_lb_target_group" "app" {
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200,204"
    protocol            = "HTTP"
  }
}
```

### gRPC Health Check

**How it works:** Uses standard gRPC Health Checking Protocol

**Validates:**
- gRPC service responds
- Service reports healthy status
- Connection works

**Example (Envoy):**
```yaml
clusters:
- name: grpc_backend
  health_checks:
  - timeout: 1s
    interval: 5s
    unhealthy_threshold: 3
    healthy_threshold: 2
    grpc_health_check:
      service_name: "myservice"
      authority: "grpc.example.com"
```

**Implementation (Go):**
```go
import (
    "google.golang.org/grpc/health"
    healthpb "google.golang.org/grpc/health/grpc_health_v1"
)

// Register health service
healthServer := health.NewServer()
healthpb.RegisterHealthServer(grpcServer, healthServer)

// Set service status
healthServer.SetServingStatus("myservice", healthpb.HealthCheckResponse_SERVING)
```

## Health Endpoint Design

### Liveness Check

**Purpose:** Is application process alive?

**Endpoint:** `/health/live` or `/live`

**Response:** 200 if process running

**Implementation (Python/Flask):**
```python
@app.route('/health/live')
def liveness():
    """Liveness check - is process alive?"""
    return {'status': 'alive'}, 200
```

**Use for:**
- Kubernetes liveness probe
- Process monitoring
- Container health

**Failure action:** Restart container/process

### Readiness Check

**Purpose:** Can application handle traffic?

**Endpoint:** `/health/ready` or `/ready`

**Validates:**
- Database connectivity
- Cache availability (Redis, Memcached)
- External API dependencies
- Required services reachable

**Implementation (Python/Flask):**
```python
@app.route('/health/ready')
def readiness():
    """Readiness check - can handle traffic?"""
    checks = {}

    # Check database
    try:
        db.session.execute('SELECT 1')
        checks['database'] = True
    except Exception as e:
        checks['database'] = False
        logger.error(f"Database check failed: {e}")

    # Check Redis
    try:
        redis_client.ping()
        checks['redis'] = True
    except Exception as e:
        checks['redis'] = False
        logger.error(f"Redis check failed: {e}")

    # Check external API
    try:
        response = requests.get('https://api.example.com/health', timeout=2)
        checks['external_api'] = response.status_code == 200
    except Exception as e:
        checks['external_api'] = False
        logger.error(f"External API check failed: {e}")

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return {
        'status': 'ready' if all_healthy else 'not_ready',
        'checks': checks
    }, status_code
```

**Use for:**
- Load balancer health checks
- Kubernetes readiness probe
- Traffic routing decisions

**Failure action:** Remove from load balancer pool (don't restart)

### Startup Check

**Purpose:** Has application finished initializing?

**Endpoint:** `/health/startup` or `/startup`

**Use for:**
- Apps with long startup times
- Data loading or cache warming
- Running migrations

**Kubernetes example:**
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10

startupProbe:
  httpGet:
    path: /health/startup
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

## Health Check Parameters

### Interval

**Guidelines:**
- Critical services: 5-10 seconds
- Standard services: 10-30 seconds
- Slow-changing backends: 30-60 seconds
- Development/testing: 5 seconds

### Timeout

**Guidelines:**
- Always less than interval
- Typical: 2-5 seconds
- Fast services: 1-2 seconds
- Slow services: 5-10 seconds

**Example:**
```yaml
# Interval: 10s, Timeout: 3s
# Check every 10 seconds, fail if no response in 3 seconds
health_check:
  interval: 10s
  timeout: 3s
```

### Failure Threshold (Unhealthy Threshold)

**Definition:** Consecutive failures before server marked unhealthy

**Guidelines:**
- Stable networks: 2-3 failures
- Flaky networks: 3-5 failures
- Critical services: 2 failures (fail fast)
- Non-critical services: 3-5 failures (tolerate transients)

**Example (AWS ALB):**
```hcl
health_check {
  unhealthy_threshold = 3  # Mark unhealthy after 3 consecutive failures
  interval            = 30 # Check every 30 seconds
  # Total time to mark unhealthy: 3 * 30 = 90 seconds
}
```

### Success Threshold (Healthy Threshold)

**Definition:** Consecutive successes before server marked healthy

**Guidelines:**
- Usually lower than failure threshold (2 vs 3)
- Prevents rapid re-addition of flapping servers
- Higher for previously problematic servers

**Example (Kubernetes):**
```yaml
readinessProbe:
  successThreshold: 2    # Need 2 successes to mark ready
  failureThreshold: 3    # Need 3 failures to mark not ready
  periodSeconds: 10
  # Time to mark ready: 2 * 10 = 20 seconds
  # Time to mark not ready: 3 * 10 = 30 seconds
```

## Health Check Hysteresis

**Problem:** Servers flip rapidly between healthy/unhealthy (flapping)

**Solution:** Different thresholds for marking up vs down

**Example (NGINX Plus):**
```nginx
upstream backend {
    server backend1:8080;
    server backend2:8080;
}

server {
    location / {
        proxy_pass http://backend;
        health_check interval=5s fails=3 passes=2;
        # Requires 3 failures to mark down
        # Requires 2 successes to mark up
    }
}
```

**Hysteresis in practice:**
```
State: Healthy
Check 1: Fail (count: 1)
Check 2: Fail (count: 2)
Check 3: Fail (count: 3) → Mark UNHEALTHY

State: Unhealthy
Check 4: Success (count: 1)
Check 5: Success (count: 2) → Mark HEALTHY
Check 6: Success (count: 3)
```

## Advanced Health Check Patterns

### Weighted Health Checks

Check several conditions, weighted by importance:

```python
@app.route('/health/ready')
def readiness():
    checks = {
        'database': {'weight': 10, 'healthy': check_database()},
        'cache': {'weight': 5, 'healthy': check_cache()},
        'external_api': {'weight': 3, 'healthy': check_api()}
    }

    total_weight = sum(c['weight'] for c in checks.values())
    healthy_weight = sum(c['weight'] for c in checks.values() if c['healthy'])

    # Pass if >80% of weighted checks pass
    threshold = 0.8
    is_healthy = (healthy_weight / total_weight) >= threshold

    return {
        'status': 'ready' if is_healthy else 'degraded',
        'score': healthy_weight / total_weight,
        'checks': {k: v['healthy'] for k, v in checks.items()}
    }, 200 if is_healthy else 503
```

### Graceful Degradation

Report degraded state without failing:

```python
@app.route('/health/ready')
def readiness():
    db_healthy = check_database()
    cache_healthy = check_cache()

    if db_healthy and cache_healthy:
        return {'status': 'ready', 'mode': 'full'}, 200
    elif db_healthy:
        # Can serve from database, cache unavailable
        return {'status': 'ready', 'mode': 'degraded'}, 200
    else:
        # Cannot serve traffic
        return {'status': 'not_ready'}, 503
```

### Custom Response Matching

**NGINX Plus - Match response body:**
```nginx
match app_healthy {
    status 200-299;
    header Content-Type = "application/json";
    body ~ "\"status\":\"healthy\"";
}

health_check match=app_healthy;
```

**HAProxy - Expect JSON response:**
```haproxy
backend api_servers
    option httpchk GET /health
    http-check expect rstring \"status\":\"ok\"
    http-check expect rstring \"database\":true
```

### Health Check Authentication

**Problem:** Health endpoint exposed to load balancer but not public internet

**Solution 1: Source IP restriction**
```nginx
location /health {
    allow 10.0.0.0/8;      # Allow LB subnet
    allow 172.16.0.0/12;   # Allow internal network
    deny all;

    return 200 "healthy";
}
```

**Solution 2: Shared secret header**
```python
HEALTH_CHECK_SECRET = os.environ['HEALTH_CHECK_SECRET']

@app.route('/health/ready')
def readiness():
    secret = request.headers.get('X-Health-Check-Secret')
    if secret != HEALTH_CHECK_SECRET:
        abort(403)

    # Perform health checks
    return {'status': 'ready'}, 200
```

**HAProxy configuration:**
```haproxy
backend web_servers
    option httpchk
    http-check send meth GET uri /health ver HTTP/1.1 hdr Host example.com hdr X-Health-Check-Secret "${HEALTH_CHECK_SECRET}"   # from env, not in config
```

## Monitoring Health Checks

### Metrics to Track

**Health check success rate:**
- Target: >99.9% for stable systems
- Alert if <95% over 5 minutes

**Time to detect failure:**
- Track: time from actual failure to removal from pool
- Formula: `failure_threshold * interval`

**Flapping rate:**
- Count: state transitions per hour
- Alert if >10 transitions per server per hour
- Signals unstable backend or misconfigured thresholds

**Health check latency:**
- Track: health endpoint response time
- Alert if p95 > timeout threshold
- Signals backend degradation

### Logging Health Check Events

```python
import logging

logger = logging.getLogger(__name__)

@app.route('/health/ready')
def readiness():
    checks = perform_health_checks()

    if not all(checks.values()):
        # Log failed checks
        failed = [k for k, v in checks.items() if not v]
        logger.warning(f"Health check degraded: {failed}")

    return {'checks': checks}, 200 if all(checks.values()) else 503
```

## Troubleshooting Health Check Issues

### Problem: False Failures

**Symptoms:** Healthy servers marked unhealthy

**Causes:**
- Timeout too short
- Health endpoint too slow
- Network latency spikes

**Solutions:**
- Raise timeout
- Speed up health endpoint (cache results)
- Raise failure threshold
- Add separate fast liveness check

### Problem: Slow Failure Detection

**Symptoms:** Failed servers stay in pool too long

**Causes:**
- Long check interval
- High failure threshold

**Solutions:**
- Shorten interval (check more often)
- Lower failure threshold
- Add active health checks (NGINX Plus)

### Problem: Health Check Overload

**Symptoms:** Health checks use significant resources

**Causes:**
- Too many load balancers checking
- Deep health checks on every request
- Short interval with expensive checks

**Solutions:**
- Shallow checks for liveness
- Deep checks only for readiness
- Cache health check results (5-10s)
- Lengthen check interval

**Health check result caching:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=1)
def cached_health_check():
    return {
        'timestamp': datetime.now(),
        'healthy': perform_expensive_checks()
    }

@app.route('/health/ready')
def readiness():
    result = cached_health_check()

    # Invalidate cache after 5 seconds
    if datetime.now() - result['timestamp'] > timedelta(seconds=5):
        cached_health_check.cache_clear()
        result = cached_health_check()

    return {'status': 'ready' if result['healthy'] else 'not_ready'}, \
           200 if result['healthy'] else 503
```
