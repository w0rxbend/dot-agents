# Performance Testing Types

## Table of Contents

1. [Load Testing](#load-testing)
2. [Stress Testing](#stress-testing)
3. [Soak Testing](#soak-testing)
4. [Spike Testing](#spike-testing)
5. [Decision Matrix](#decision-matrix)
6. [Test Scenario Design](#test-scenario-design)
7. [Interpreting Results](#interpreting-results)
8. [Tool Comparison](#tool-comparison)

---

## Load Testing

### Purpose
Validate behavior at expected traffic and verify SLO compliance.

### Characteristics

- **Load Level:** Normal to high (expected peak traffic)
- **Duration:** 10-30 minutes
- **Ramp Pattern:** Gradual increase to target load, sustain, then ramp down
- **Pass Criteria:** All SLOs met (latency, throughput, error rate)

### Key Metrics

- **Response Time Percentiles:** p50, p95, p99 latency
- **Throughput:** Sustained requests per second
- **Error Rate:** Percentage of failed requests (typically < 0.1%)
- **Resource Utilization:** CPU, memory, disk I/O during load

### When to Use

**Primary Scenarios:**
- Pre-launch capacity validation
- Post-refactor regression testing
- Validating infrastructure changes
- Setting performance baselines
- Verifying auto-scaling configuration

**Example Use Cases:**
- E-commerce site: Simulate Black Friday traffic (10,000 concurrent users)
- API service: Test 1,000 requests/second sustained load
- Dashboard: Validate 500 concurrent viewers
- SaaS platform: Test expected user concurrency

### Load Pattern Design

**Ramp-up stages:**
1. Warm-up: 0% → 50% of target load (5 minutes)
2. Ramp to peak: 50% → 100% of target load (5 minutes)
3. Sustained load: 100% of target load (20 minutes)
4. Ramp-down: 100% → 0% (5 minutes)

### Load Testing Best Practices

- Include think time between requests (1-5 seconds)
- Test under production-like conditions (time of day, data volume)
- Run several times to account for variance

---

## Stress Testing

### Purpose
Find capacity limits, breaking points and failure modes.

### Characteristics

- **Load Level:** Progressively increasing beyond normal capacity
- **Duration:** Until system breaks or saturates
- **Ramp Pattern:** Continuous gradual increase (no sustain periods)
- **Pass Criteria:** Graceful degradation, no cascading failures

### Key Metrics

- **Maximum Sustained Throughput:** Requests/sec before errors spike
- **Breaking Point:** Load level where error rate exceeds threshold (>5%)
- **Failure Mode:** How system fails (timeout, crash, queue backup)
- **Recovery Time:** How long recovery takes after load drops
- **Resource Exhaustion:** CPU at 100%, memory exhaustion, connection pool saturation

### When to Use

**Primary Scenarios:**
- Capacity planning (how much can we handle?)
- Understanding failure behavior
- Validating rate limiting and circuit breakers
- Infrastructure sizing decisions
- Testing recovery mechanisms

**Example Use Cases:**
- API service: Ramp from 100 to 10,000 req/s until errors spike
- Database: Increase connection pool until connection exhaustion
- Message queue: Push messages until consumer lag becomes unrecoverable
- Cache layer: Increase requests until cache eviction rate hurts performance

### Stress Pattern Design

**Ramping strategy:**
1. Start at baseline (10% capacity)
2. Increase by 10-20% every 2-3 minutes
3. Continue until error rate exceeds threshold (e.g., >5%)
4. Hold breaking-point load for 5 minutes (observe behavior)
5. Ramp down to 0%

### Stress Testing Best Practices

- Watch for graceful degradation (slow responses vs. crashes)
- Confirm circuit breakers and rate limiters engage
- Find bottleneck resource (CPU, memory, network, database connections)
- Document failure mode for incident response planning

---

## Soak Testing

### Purpose
Find memory leaks, resource exhaustion and performance degradation over time.

### Characteristics

- **Load Level:** Moderate (typical production load, 60-80% capacity)
- **Duration:** Extended (hours to days)
- **Ramp Pattern:** Quick ramp-up, then sustain for duration
- **Pass Criteria:** No memory growth, no latency degradation, no connection leaks

### Key Metrics

- **Memory Usage Over Time:** Should stay stable (no upward trend)
- **Connection Pool Usage:** Should not grow (detects leaks)
- **Response Time Trend:** Should stay consistent (no degradation)
- **Disk Space Usage:** Should not grow unbounded (log rotation, temp files)
- **Database Connection Count:** Should stay stable
- **GC Pause Time:** Should not increase over time

### When to Use

**Primary Scenarios:**
- Detecting memory leaks
- Validating connection pool cleanup
- Testing long-running batch jobs
- Ensuring database query plan stability
- Validating log rotation and cleanup
- Testing resource cleanup (file handles, connections)

**Example Use Cases:**
- API service: Run at 60% capacity for 24 hours, monitor memory
- Background job processor: Process 10,000 jobs over 12 hours
- WebSocket server: Hold 1,000 connections for 8 hours
- Cache layer: Run sustained load for 48 hours, check memory growth

### Soak Pattern Design

**Typical Soak Pattern:**
```
Users
  ^
  |  ┌─────────────────────────────────┐
  | /                                   \
  |/                                     \
  └──────────────────────────────────────> Time
      5m       24 hours               5m
   Ramp-up      Sustain            Ramp-down
```

### Soak Testing Best Practices

- Check for connection leaks (database, HTTP, WebSocket)
- Run during off-hours (minimize production impact)
- Use production-like data volumes

### Common Issues Detected

- **Memory Leaks:** Gradual memory growth over hours
- **Connection Leaks:** Database/HTTP connections not closed
- **File Handle Leaks:** File descriptors not released
- **Log File Growth:** Logs not rotated, filling disk
- **Cache Growth:** Cache eviction not working
- **Goroutine Leaks (Go):** Goroutines not terminated
- **Event Listener Leaks (JS):** Event listeners not removed

---

## Spike Testing

### Purpose
Validate response to sudden traffic spikes and auto-scaling effectiveness.

### Characteristics

- **Load Level:** Sudden jump from low to very high
- **Duration:** Short bursts (seconds to minutes)
- **Ramp Pattern:** Instant spike, brief sustain, drop
- **Pass Criteria:** Handles spike without significant errors, scales appropriately

### Key Metrics

- **Time to Scale:** How fast auto-scaling provisions resources
- **Error Rate During Spike:** Percentage of failed requests during burst
- **Recovery Time:** Time to return to normal after spike
- **Queue Depth:** Message or request queue depth during spike
- **Cache Hit Rate:** Cache effectiveness during burst

### When to Use

**Primary Scenarios:**
- Validating auto-scaling configuration
- Testing event-driven systems (product launches, breaking news)
- Ensuring rate limiting doesn't block legitimate traffic
- Cloud resource burst capacity validation
- Testing queue and buffering mechanisms

**Example Use Cases:**
- News site: Simulate breaking news spike (0 to 5,000 users in 1 minute)
- Ticketing platform: Concert ticket release (10x normal load instantly)
- API rate limiter: Burst 100 req/s for 10 seconds, then 10 req/s baseline
- E-commerce flash sale: Sudden spike at sale start

### Spike Pattern Design

**Typical Spike Pattern:**
```
Users
  ^
  |     ┌──┐
  |     │  │         ┌──┐
  |     │  │         │  │
  | ────┘  └─────────┘  └────
  └──────────────────────────> Time
  Base  Spike  Base  Spike  Base
  5m     2m    5m    2m     5m
```

### Spike Testing Best Practices

- Start from realistic baseline load (not 0)
- Spike to 2-10x baseline load
- Sustain spike 1-5 minutes
- Return to baseline to observe recovery
- Test several spikes (not only one)
- Monitor auto-scaling metrics (instance count, scale events)

---

## Decision Matrix

### Choosing the Right Test Type

| Scenario | Load Test | Stress Test | Soak Test | Spike Test |
|----------|-----------|-------------|-----------|------------|
| Pre-launch capacity validation | ✅ Primary | ✅ Secondary | ⚠️ Optional | ⚠️ Optional |
| Post-refactor regression | ✅ Primary | ❌ | ❌ | ❌ |
| Finding maximum capacity | ❌ | ✅ Primary | ❌ | ❌ |
| Investigating memory leak | ❌ | ❌ | ✅ Primary | ❌ |
| Validating auto-scaling | ⚠️ Optional | ⚠️ Optional | ❌ | ✅ Primary |
| Black Friday preparation | ✅ Primary | ✅ Secondary | ⚠️ Optional | ✅ Secondary |
| Detecting resource leaks | ❌ | ❌ | ✅ Primary | ❌ |
| Infrastructure sizing | ✅ Primary | ✅ Primary | ❌ | ❌ |

### Test Type by Time Available

| Time Available | Recommended Tests |
|----------------|-------------------|
| < 30 minutes | Load test (quick baseline) |
| 1-2 hours | Load test + Stress test |
| 4-8 hours | Load + Stress + Spike tests |
| Overnight/weekend | Full suite (Load + Stress + Soak + Spike) |

---

## Test Scenario Design

### Realistic User Scenarios

**Avoid:** Single endpoint hammering
```javascript
// BAD: Unrealistic load
export default function() {
  http.get('https://api.example.com/products');
}
```

**Prefer:** Multi-step user flows
```javascript
// GOOD: Realistic user behavior
export default function() {
  // Browse products
  http.get('https://api.example.com/products');
  sleep(2);

  // View product detail
  const productId = Math.floor(Math.random() * 1000);
  http.get(`https://api.example.com/products/${productId}`);
  sleep(3);

  // Add to cart (30% of users)
  if (Math.random() < 0.3) {
    http.post('https://api.example.com/cart', JSON.stringify({
      product_id: productId,
      quantity: 1,
    }));
    sleep(1);
  }
}
```

### Think Time

Add realistic delays between requests.

**Typical think times:**
- Browsing content: 2-5 seconds
- Reading details: 5-10 seconds
- Filling forms: 10-30 seconds
- Decision-making: 5-15 seconds

### Data Variation

Use realistic data, not same data for every user.

**Techniques:**
- Random IDs from realistic range
- CSV files with test data
- Parameterized data from environment
- Randomized request payloads

---

## Interpreting Results

### Latency Percentiles

**Example interpretation:**
```
p50: 50ms   (typical user experiences 50ms)
p95: 200ms  (95% of users experience < 200ms)
p99: 500ms  (1% of users experience > 500ms, up to 500ms)
p99.9: 2s   (0.1% of users experience very slow responses)
```

### Throughput

**Requests per second (RPS):**
- Should stay stable under load
- Drops at breaking point (stress test)

**Example:**
```
Target: 1,000 RPS
Achieved: 980 RPS (within 2%, acceptable)
```

### Error Rate

**Acceptable error rates:**
- **Load test:** < 0.1% (very low)
- **Stress test:** < 5% at peak (some errors acceptable)
- **Soak test:** < 0.01% (almost zero)
- **Spike test:** < 1% during spike

**Error types to track:**
- HTTP 5xx (server errors)
- Timeouts (slow responses)
- Connection failures

### Resource Utilization

**Key resources to monitor:**
- CPU utilization (target 60-80% at peak load)
- Memory usage (should not grow unbounded)
- Network I/O (bandwidth saturation)
- Disk I/O (database, logging)
- Database connections (pool exhaustion)

---

## Tool Comparison

### k6 vs. Locust vs. JMeter

| Feature | k6 | Locust | JMeter |
|---------|----|----|--------|
| **Language** | JavaScript | Python | Java (GUI + XML) |
| **Learning Curve** | Low | Low | Medium-High |
| **CI/CD Integration** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Distributed Testing** | ✅ (k6 Cloud) | ✅ (built-in) | ✅ (manual setup) |
| **Real-time Monitoring** | CLI + Grafana | Web UI | GUI |
| **Protocols** | HTTP/1.1, HTTP/2, WebSocket, gRPC | HTTP (extensible) | HTTP, SOAP, FTP, JDBC |
| **Modern API Focus** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Scripting Flexibility** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**Recommendation:**
- **k6:** Modern APIs, microservices, CI/CD focus, JavaScript-familiar teams
- **Locust:** Python teams, complex user flows, web UI needed
- **JMeter:** Enterprise environments, legacy systems, SOAP/JDBC protocols

---

## Performance Testing Checklist

### Before Running Tests

- [ ] Define SLOs (latency, throughput, error rate)
- [ ] Design realistic user scenarios
- [ ] Pick test environment (staging, dedicated load test)
- [ ] Match test environment to production (data volume, configuration)
- [ ] Configure monitoring (metrics, logs, dashboards)
- [ ] Notify team (load tests can impact shared environments)

### During Tests

- [ ] Monitor application metrics (latency, errors, throughput)
- [ ] Monitor infrastructure metrics (CPU, memory, disk, network)
- [ ] Watch for error spikes
- [ ] Check logs for errors/warnings
- [ ] Confirm realistic load distribution (not all hitting one endpoint)

### After Tests

- [ ] Analyze results (percentiles, throughput, errors)
- [ ] Compare against SLOs (pass/fail)
- [ ] Find bottlenecks (CPU, memory, database, network)
- [ ] Document findings (capacity limits, failure modes)
- [ ] Plan optimizations (if needed)
- [ ] Re-run tests to validate improvements
