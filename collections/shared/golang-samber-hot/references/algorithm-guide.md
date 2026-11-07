# Algorithm Selection Guide

## Table of Contents

- [Decision Tree](#decision-tree)
- [Algorithm Deep Dives](#algorithm-deep-dives)
  - [LRU (Least Recently Used)](#lru-least-recently-used)
  - [LFU (Least Frequently Used)](#lfu-least-frequently-used)
  - [TinyLFU](#tinylfu)
  - [W-TinyLFU (Weighted TinyLFU)](#w-tinylfu-weighted-tinylfu)
  - [S3FIFO (Segmented Small-Size FIFO)](#s3fifo-segmented-small-size-fifo)
  - [ARC (Adaptive Replacement Cache)](#arc-adaptive-replacement-cache)
  - [TwoQueue](#twoqueue)
  - [SIEVE](#sieve)
  - [FIFO (First In, First Out)](#fifo-first-in-first-out)
- [Comparison Matrix](#comparison-matrix)
- [Measuring Hit Rate](#measuring-hit-rate)
- [Switching Algorithms](#switching-algorithms)

## Decision Tree

```
Start here
  |
  v
Do you know your access pattern?
  |-- No --> Use W-TinyLFU (adapts automatically)
  |-- Yes
       |
       v
     Is recency the primary signal? (sessions, recent queries, time-windowed data)
       |-- Yes --> LRU
       |-- No
            |
            v
          Is frequency the primary signal? (popular products, DNS, static config)
            |-- Yes --> Does the popularity ranking shift over time?
            |           |-- Yes --> TinyLFU (frequency with decay)
            |           |-- No --> LFU
            |-- No
                 |
                 v
               Is throughput critical and cache is large? (>100k items, high write rate)
                 |-- Yes --> S3FIFO
                 |-- No
                      |
                      v
                    Do you want self-tuning with no config? (unknown or shifting patterns)
                      |-- Yes --> ARC (higher memory) or W-TinyLFU (lower memory)
                      |-- No
                           |
                           v
                         Is scan resistance needed with simplicity?
                           |-- Yes --> SIEVE
                           |-- No --> W-TinyLFU (safe default)
```

## Algorithm Deep Dives

### LRU (Least Recently Used)

**Constant:** `hot.LRU`

Evicts item idle longest. Simple doubly-linked list + hash map implementation.

- **Strengths:** Simple mental model, predictable behavior, low per-operation overhead
- **Weaknesses:** Scan pollution — one sequential scan evicts all hot items. No frequency awareness.
- **Ideal workload:** Time-windowed data (user sessions, recent search results, short-lived tokens)
- **Degrades when:** Batch job or sequential scan touches many cold keys, evicting frequently-used items

### LFU (Least Frequently Used)

**Constant:** `hot.LFU`

Evicts item with fewest accesses. Tracks per-key access counts.

- **Strengths:** Keeps popular items regardless of access timing
- **Weaknesses:** Stale popular items never evict — item accessed 10,000 times yesterday blocks new hot items today. No frequency decay.
- **Ideal workload:** Stable popularity rankings (DNS records, country code lookups, static configuration)
- **Degrades when:** Popularity shifts over time or new items must ramp up quickly

### TinyLFU

**Constant:** `hot.TinyLFU`

Estimates frequency via compact Count-Min Sketch instead of per-key counters. Includes frequency decay: old access counts fade over time.

- **Strengths:** Low memory for frequency tracking, decay handles popularity shifts, good admission filtering
- **Weaknesses:** Admission filter adds write overhead. Sketch approximation can cause rare false positives.
- **Ideal workload:** Read-heavy with moderate frequency bias (API response caching, content delivery metadata)
- **Degrades when:** Write-heavy workloads where admission overhead exceeds benefit

### W-TinyLFU (Weighted TinyLFU)

**Constant:** `hot.WTinyLFU`

Small "window" LRU in front of TinyLFU's admission filter. New items enter window; filter decides promotion to main cache. Balances recency and frequency automatically.

- **Strengths:** Best general-purpose hit rate across diverse workloads. Self-adapting to recency and frequency patterns.
- **Weaknesses:** Slightly more complex internals (eviction order harder to reason about while debugging)
- **Ideal workload:** Mixed or unknown access patterns, general-purpose caching
- **Degrades when:** Rarely — safest default. May underperform specialized algorithms on extreme workloads.

### S3FIFO (Segmented Small-Size FIFO)

**Constant:** `hot.S3FIFO`

Three FIFO segments: small, main, ghost queues. Items promoted small to main only if accessed again. Ghost queue tracks recently evicted keys for scan resistance.

- **Strengths:** Excellent throughput (FIFO operations cheaper than linked-list manipulations). Good scan resistance. Simple eviction path.
- **Weaknesses:** Segmented structure needs enough capacity. Less effective on small caches.
- **Ideal workload:** High-throughput systems with large caches (>100k items), CDN-like access patterns
- **Degrades when:** Cache very small (<1000 items) — segments don't have room to differentiate access patterns

### ARC (Adaptive Replacement Cache)

**Constant:** `hot.ARC`

Four internal lists: recency (recent, recent-ghost) and frequency (frequent, frequent-ghost). Dynamically adjusts recency/frequency split based on which ghost list sees more hits.

- **Strengths:** Self-tuning — learns from misses whether to favor recency or frequency. No manual parameter tuning.
- **Weaknesses:** ~2x memory overhead for ghost lists. More complex implementation.
- **Ideal workload:** Workloads shifting between recency and frequency patterns (mixed database query caching)
- **Degrades when:** Memory constrained — ghost lists consume significant space

### TwoQueue

**Constant:** `hot.TwoQueue`

Splits items into "hot" (frequently accessed) and "cold" (recently added) queues, evicted independently. Items graduate cold to hot on second access.

- **Strengths:** Separates one-hit wonders from useful items well. Scan resistant.
- **Weaknesses:** Optimal tuning requires understanding hot/cold split ratio
- **Ideal workload:** Clear hot/cold distinction (e.g., 20% of keys serve 80% of requests)
- **Degrades when:** Access patterns uniform with no clear hot/cold split

### SIEVE

**Constant:** `hot.SIEVE`

Modern algorithm: one bit per entry (visited/not-visited) plus circular "hand" pointer. Simple scan-resistant LRU alternative.

- **Strengths:** Very low per-item overhead (1 bit). Scan-resistant. Simple implementation.
- **Weaknesses:** Less sophisticated than W-TinyLFU or ARC for complex patterns
- **Ideal workload:** Scan resistance with minimal complexity and overhead
- **Degrades when:** Access patterns highly skewed — specialized algorithms capture skew better

### FIFO (First In, First Out)

**Constant:** `hot.FIFO`

Evicts oldest inserted item, ignoring access pattern. No recency or frequency tracking.

- **Strengths:** Simplest possible eviction. Predictable. Zero per-access overhead.
- **Weaknesses:** No intelligence — ignores how often or recently items are accessed
- **Ideal workload:** TTL-driven caches with similar item lifetimes where eviction order doesn't matter (log buffers, time-series windows)
- **Degrades when:** Hit rate matters — any other algorithm outperforms FIFO on non-uniform access patterns

## Comparison Matrix

| Algorithm | Scan Resistance | Frequency Awareness | Memory Overhead | Throughput | Tuning Complexity |
| --- | --- | --- | --- | --- | --- |
| LRU | None | None | Low | High | None |
| LFU | None | High (no decay) | Medium | Medium | None |
| TinyLFU | Medium | High (with decay) | Low | Medium | None |
| W-TinyLFU | High | High (with decay) | Low | Medium | None |
| S3FIFO | High | Low | Medium | Very High | None |
| ARC | High | Medium | High (2x) | Medium | None (self-tuning) |
| TwoQueue | Medium | Medium | Medium | Medium | Low |
| SIEVE | Medium | None | Very Low | High | None |
| FIFO | None | None | Very Low | Very High | None |

## Measuring Hit Rate

Validate algorithm choice: enable Prometheus metrics, check hit ratio.

```go
cache := hot.NewHotCache[string, *User](hot.WTinyLFU, 10_000).
    WithTTL(5 * time.Minute).
    WithPrometheusMetrics("user_cache").
    WithJanitor().
    Build()
defer cache.StopJanitor()

prometheus.MustRegister(cache)
```

Key PromQL queries:

```promql
# Hit ratio (target: >80%)
rate(hot_cache_hit_count{cache="user_cache"}[5m]) /
rate(hot_cache_get_count{cache="user_cache"}[5m])

# Eviction rate (high = cache too small)
rate(hot_cache_eviction_count{cache="user_cache"}[5m])
```

If hit rate below SLO: increase capacity first, then try different algorithm.

## Switching Algorithms

Switching algorithm is one-line change. Rest of builder chain stays identical:

```go
// Before
cache := hot.NewHotCache[string, *User](hot.LRU, 10_000).
    WithTTL(5 * time.Minute).
    WithJanitor().
    Build()

// After — only the first argument changes
cache := hot.NewHotCache[string, *User](hot.WTinyLFU, 10_000).
    WithTTL(5 * time.Minute).
    WithJanitor().
    Build()
```
