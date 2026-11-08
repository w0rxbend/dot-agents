# Benchmarking Best Practices

## Table of Contents

1. [Benchmarking Fundamentals](#benchmarking-fundamentals)
2. [Micro-Benchmarking](#micro-benchmarking)
3. [HTTP Benchmarking](#http-benchmarking)
4. [Database Benchmarking](#database-benchmarking)
5. [Comparing Implementations](#comparing-implementations)
6. [Avoiding Common Pitfalls](#avoiding-common-pitfalls)

---

## Benchmarking Fundamentals

### What is Benchmarking?

**Benchmarking vs. Profiling vs. Load Testing:**

| Type | Purpose | Scope | Output |
|------|---------|-------|--------|
| **Benchmarking** | Measure one operation | Function or micro-operation | Operations/sec, latency |
| **Profiling** | Find bottlenecks | Application-wide | Flamegraph, hot functions |
| **Load Testing** | Validate capacity | System-wide | Throughput, p95 latency |

**Use cases:**
- Compare two implementations (which is faster?)
- Set baselines (how fast is this operation?)
- Detect regressions (did performance degrade?)
- Validate optimizations (did change help?)

### Benchmarking Best Practices

Run many iterations, warm up first, use realistic inputs: see [Avoiding Common Pitfalls](#avoiding-common-pitfalls).

**Isolate Variables**
```python
# Bad: Multiple changes at once
def optimized_function():
    # Changed algorithm AND added caching
    pass

# Good: One change at a time
def optimized_algorithm():
    # Only changed algorithm
    pass

def with_caching():
    # Only added caching
    pass
```

---

## Micro-Benchmarking

### Python (timeit)

**Built-in benchmark module:**
```python
import timeit

# Benchmark single statement
duration = timeit.timeit('sum(range(100))', number=10000)
print(f'{duration:.4f} seconds for 10,000 runs')

# Benchmark function
def my_function():
    return sum(range(100))

duration = timeit.timeit(my_function, number=10000)
print(f'{duration:.4f} seconds for 10,000 runs')

# With setup code
duration = timeit.timeit(
    stmt='sorted(data)',
    setup='data = list(range(1000, 0, -1))',
    number=1000
)
```

### Python (pytest-benchmark)

**Benchmarks with statistics:**
```bash
pip install pytest-benchmark
```

```python
# test_performance.py
def my_function(n):
    return sum(range(n))

def test_benchmark_sum(benchmark):
    result = benchmark(my_function, 1000)
    assert result == 499500

# Run: pytest test_performance.py --benchmark-only
```

**Output:**
```
Name              Min       Max      Mean    StdDev
test_benchmark    10.5μs    15.2μs   11.3μs  0.8μs
```

### Go (testing.B)

**Built-in benchmarking:**
```go
package mypackage

import "testing"

func BenchmarkSum(b *testing.B) {
    data := make([]int, 1000)
    for i := range data {
        data[i] = i
    }

    b.ResetTimer()  // Reset timer after setup

    for i := 0; i < b.N; i++ {
        Sum(data)
    }
}

func BenchmarkSumParallel(b *testing.B) {
    data := make([]int, 1000)

    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            Sum(data)
        }
    })
}
```

**Run:**
```bash
# Run all benchmarks
go test -bench=.

# Run specific benchmark
go test -bench=BenchmarkSum

# With memory allocation stats
go test -bench=. -benchmem

# Output:
# BenchmarkSum-8    1000000    1050 ns/op    0 B/op    0 allocs/op
```

### TypeScript (Benchmark.js)

```bash
npm install benchmark
```

```typescript
import Benchmark from 'benchmark';

const suite = new Benchmark.Suite();

suite
  .add('Array#forEach', function() {
    const arr = [1, 2, 3, 4, 5];
    arr.forEach(x => x * 2);
  })
  .add('Array#map', function() {
    const arr = [1, 2, 3, 4, 5];
    arr.map(x => x * 2);
  })
  .on('cycle', function(event: any) {
    console.log(String(event.target));
  })
  .on('complete', function(this: any) {
    console.log('Fastest is ' + this.filter('fastest').map('name'));
  })
  .run({ async: true });

// Output:
// Array#forEach x 10,234,567 ops/sec ±0.98%
// Array#map x 8,123,456 ops/sec ±1.23%
// Fastest is Array#forEach
```

---

## HTTP Benchmarking

### autocannon (Node.js/TypeScript)

```bash
npm install -g autocannon
```

**Usage:**
```bash
# Basic benchmark (10 connections, 30 seconds)
autocannon -c 10 -d 30 http://localhost:3000/api/users

# Output:
# Stat      Avg     Stdev   Max
# Latency   12ms    5ms     50ms
# Req/Sec   800     100     1000
```

**Programmatic:**
```typescript
import autocannon from 'autocannon';

const result = await autocannon({
  url: 'http://localhost:3000/api/users',
  connections: 10,
  duration: 30,
});

console.log(result.latency);  // { mean, stddev, p50, p95, p99 }
console.log(result.requests);  // { average, mean, stddev }
```

### ab (Apache Bench)

**Simple CLI benchmarking:**
```bash
# 1000 requests, 10 concurrent
ab -n 1000 -c 10 http://localhost:3000/api/users

# Output:
# Requests per second:    850.23 [#/sec]
# Time per request:       11.762 [ms] (mean)
```

### vegeta (Go)

**Load testing and benchmarking:**
```bash
# Install
go install github.com/tsenart/vegeta/v12@v12.13.0
```

**Usage:**
```bash
# Attack at 100 req/s for 30s
echo "GET http://localhost:3000/api/users" | vegeta attack -rate=100 -duration=30s | vegeta report

# Output:
# Requests      [total, rate, throughput]  3000, 100.03, 99.98
# Latency       [mean, 50, 95, 99, max]    10ms, 8ms, 15ms, 25ms, 50ms
```

---

## Database Benchmarking

### PostgreSQL (pgbench)

**Built-in benchmarking tool:**
```bash
# Initialize test database
pgbench -i -s 10 mydb

# Run benchmark (10 clients, 1000 transactions each)
pgbench -c 10 -t 1000 mydb

# Output:
# tps = 850.234567 (including connections establishing)
# latency average = 11.762 ms
```

**Custom SQL:**
```bash
# Create test script (test.sql)
cat > test.sql <<EOF
SELECT * FROM users WHERE id = :id;
EOF

# Run custom benchmark
pgbench -c 10 -t 1000 -f test.sql mydb
```

### MySQL (sysbench)

```bash
# Install
sudo apt-get install sysbench

# Credentials out of argv/shell history: chmod 600 file with lines mysql-user=... and mysql-password=...
chmod 600 sysbench.cfg

# Prepare test
sysbench oltp_read_write --config-file=sysbench.cfg --mysql-db=mydb prepare

# Run benchmark
sysbench oltp_read_write --config-file=sysbench.cfg --mysql-db=mydb --threads=10 --time=60 run

# Cleanup
sysbench oltp_read_write --config-file=sysbench.cfg --mysql-db=mydb cleanup
```

---

## Comparing Implementations

### A/B Performance Testing

**Python:**
```python
import timeit

def implementation_a(data):
    return sum(data)

def implementation_b(data):
    total = 0
    for item in data:
        total += item
    return total

data = list(range(10000))

# Benchmark both
time_a = timeit.timeit(lambda: implementation_a(data), number=1000)
time_b = timeit.timeit(lambda: implementation_b(data), number=1000)

print(f'A: {time_a:.4f}s')
print(f'B: {time_b:.4f}s')
print(f'Faster: {"A" if time_a < time_b else "B"} by {abs(time_a - time_b) / min(time_a, time_b) * 100:.1f}%')
```

**Go:**
```go
package mypackage

import "testing"

func BenchmarkImplementationA(b *testing.B) {
    data := make([]int, 10000)
    b.ResetTimer()

    for i := 0; i < b.N; i++ {
        ImplementationA(data)
    }
}

func BenchmarkImplementationB(b *testing.B) {
    data := make([]int, 10000)
    b.ResetTimer()

    for i := 0; i < b.N; i++ {
        ImplementationB(data)
    }
}
```

**Run:**
```bash
go test -bench=. -benchmem

# Output comparison:
# BenchmarkImplementationA-8    100000    10500 ns/op    0 B/op    0 allocs/op
# BenchmarkImplementationB-8     50000    20500 ns/op    0 B/op    0 allocs/op
# → A is 2x faster
```

### Regression Detection

**GitHub Actions (Go benchmarks):**
```yaml
name: Benchmark

on: [push, pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v4

      - name: Run benchmarks
        run: go test -bench=. -benchmem | tee benchmark.txt

      - name: Store benchmark result
        uses: benchmark-action/github-action-benchmark@v1  # pin to a full commit SHA
        with:
          tool: 'go'
          output-file-path: benchmark.txt
          fail-on-alert: true  # Fail if performance regresses
          alert-threshold: '110%'  # Alert if 10% slower
```

---

## Avoiding Common Pitfalls

### Pitfall 1: Not Warming Up

**Problem:** First run slower (JIT compilation, caching).

```python
# Bad: Cold start measured
result = timeit.timeit(my_function, number=1)

# Good: Warm-up runs
for _ in range(100):
    my_function()  # Warm-up

result = timeit.timeit(my_function, number=1000)
```

### Pitfall 2: Dead Code Elimination

**Problem:** Compiler optimizes away unused results.

```go
// Bad: Result not used (may be optimized away)
func BenchmarkSum(b *testing.B) {
    data := make([]int, 1000)

    for i := 0; i < b.N; i++ {
        Sum(data)  // Result discarded
    }
}

// Good: Store result (prevents optimization)
func BenchmarkSum(b *testing.B) {
    data := make([]int, 1000)
    var result int

    for i := 0; i < b.N; i++ {
        result = Sum(data)  // Result used
    }

    _ = result  // Prevent unused variable warning
}
```

### Pitfall 3: Unrealistic Inputs

**Problem:** Trivial data.

```python
# Bad: Tiny input (not representative)
timeit.timeit(lambda: sorted([3, 1, 2]), number=1000)

# Good: Realistic input
timeit.timeit(lambda: sorted(list(range(10000, 0, -1))), number=1000)
```

### Pitfall 4: Measuring Setup Time

**Problem:** Setup counted in benchmark.

```python
# Bad: Includes list creation time
timeit.timeit('sorted(list(range(1000, 0, -1)))', number=1000)

# Good: Setup separate
timeit.timeit(
    stmt='sorted(data)',
    setup='data = list(range(1000, 0, -1))',
    number=1000
)
```

### Pitfall 5: Ignoring Variance

**Problem:** Single run, no statistics.

```python
# Bad: Single measurement
duration = timeit.timeit(my_function, number=1)

# Good: Multiple runs with statistics
import statistics

durations = [timeit.timeit(my_function, number=1) for _ in range(100)]
mean = statistics.mean(durations)
stddev = statistics.stdev(durations)

print(f'Mean: {mean:.4f}s, StdDev: {stddev:.4f}s')
```

---

## Benchmarking Checklist

### Before Benchmarking
- [ ] Define what to measure (specific operation)
- [ ] Use realistic inputs (production-like data)
- [ ] Isolate variables (one change at a time)
- [ ] Close other applications (reduce noise)

### During Benchmarking
- [ ] Run warm-up iterations (JIT, caching)
- [ ] Run multiple iterations (statistical significance)
- [ ] Use result (prevent dead code elimination)
- [ ] Measure only relevant code (exclude setup)

### After Benchmarking
- [ ] Compute statistics (mean, stddev, percentiles)
- [ ] Compare to baseline (regression detection)
- [ ] Document results
- [ ] Validate in production (synthetic ≠ real-world)
