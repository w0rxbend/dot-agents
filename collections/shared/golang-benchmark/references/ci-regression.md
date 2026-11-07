# CI Benchmark Regression Detection

> **Run these tools in CI only, not on local machines.** Local results are noisy (background processes, thermal throttling, inconsistent CPU frequency), so local regressions are unreliable and waste developer time.

Pin tool installs to reviewed versions (never `@latest`) and actions to a full commit SHA; give the token least privilege (`permissions:`).

## Table of Contents

- [benchdiff](#benchdiff)
- [cob](#cob)
- [gobenchdata](#gobenchdata)
  - [CLI commands](#cli-commands)
  - [GitHub Action setup](#github-action-setup)
  - [Regression gating on PRs](#regression-gating-on-prs)
  - [Dashboard configuration](#dashboard-configuration)
- [Tool Selection Guide](#tool-selection-guide)
- [Noisy Neighbor Mitigation](#noisy-neighbor-mitigation)
  - [Why CI benchmarks are noisy](#why-ci-benchmarks-are-noisy)
  - [Strategies](#strategies)
- [System Tuning for Self-Hosted Runners](#system-tuning-for-self-hosted-runners)
  - [Disable CPU frequency scaling](#disable-cpu-frequency-scaling)
  - [Disable Turbo Boost](#disable-turbo-boost)
  - [Pin benchmarks to specific CPU cores](#pin-benchmarks-to-specific-cpu-cores)
  - [Disable SMT (Hyper-Threading)](#disable-smt-hyper-threading)
  - [Combined CI setup script](#combined-ci-setup-script)

## benchdiff

Runs Go benchmarks on two git refs; `benchstat` shows deltas. Caches non-worktree refs, so re-runs only re-measure worktree. Prevents macOS sleep during benchmarks.

```bash
go install filippo.io/mostly-harmless/benchdiff@v0.0.0-20261103164203-dfa6dee15068
```

```bash
# Compare current worktree against HEAD (default)
benchdiff -- -benchmem

# Compare two specific refs
benchdiff -base-ref main -head-ref feature-branch

# Compare against a specific commit or tag
benchdiff -base-ref v1.2.0

# Pass extra flags to go test — everything after -- goes to go test
benchdiff -- -benchmem -count=10 -benchtime=3s

# Filter to specific benchmarks
benchdiff -- -benchmem -count=10 -bench=BenchmarkParse

# Target a specific package
benchdiff -- -benchmem -count=10 ./pkg/parser/...

# Clear cached results (useful after rebasing or when cache is stale)
benchdiff -clear-cache

# Combine: compare main with 10 iterations, filtered to critical benchmarks
benchdiff -base-ref main -- -benchmem -count=10 -bench='BenchmarkParse|BenchmarkEncode'
```

Best for: quick PR-to-base comparisons in git-based workflows.

## cob

Compares HEAD vs HEAD~1 benchmarks; fails CI job if performance degrades past configurable threshold (default 20%).

```bash
go install github.com/knqyf263/cob@v0.0.8
```

```bash
# Run with default 20% threshold — compares HEAD vs HEAD~1
cob

# Stricter threshold for critical paths (10% regression = failure)
cob -threshold 10

# Compare against a specific base commit
cob -base main

# Only report regressions (ignore improvements)
cob -only-degression

# Choose which metrics to compare (default: ns/op,B/op)
cob -compare "ns/op,B/op,allocs/op"

# Custom go test arguments
cob -bench-args "test -run '^$' -bench BenchmarkParse -benchmem ./pkg/parser/..."

# Increase benchmark duration for more stable results
cob -bench-args "test -run '^$' -bench . -benchmem -benchtime=3s ./..."

# Skip cob for a specific commit: include [skip cob] in commit message
```

**Caution:** `cob` runs `git reset` internally; uncommitted changes can be lost. Always commit first.

- For safety, run only in CI pipelines, not locally.
- `cob` needs all benchmarks to pass; skips CI gating if any fails.
- `cob` compares single runs without `benchstat`-style statistics, so noisier than `benchdiff`.

Best for: simple post-commit CI regression gating where fast feedback beats statistical rigor.

## gobenchdata

GitHub Action + CLI: collects benchmark results, publishes JSON to gh-pages, shows performance trends in interactive web dashboard.

```bash
go install go.bobheadxi.dev/gobenchdata@v1.3.1
```

### CLI commands

```bash
# Parse go test -bench output to JSON
go test -bench=. -benchmem -count=5 ./... | gobenchdata --json bench.json

# Parse from a file
gobenchdata --json bench.json < bench.txt

# Add a tag to the benchmark run (e.g., git commit)
gobenchdata --json bench.json --tag "$(git rev-parse --short HEAD)" < bench.txt

# Evaluate regression checks against a checks config
gobenchdata checks eval bench.txt --checks-config .gobenchdata-checks.yml

# Generate the web dashboard app (static Vue.js site)
gobenchdata web generate ./dashboard-app

# Serve the dashboard locally for preview
gobenchdata web serve ./dashboard-app

# Merge multiple benchmark JSON files
gobenchdata merge old-bench.json new-bench.json > combined.json

# Prune old entries (keep last 30 runs)
gobenchdata prune --count 30 bench.json
```

### GitHub Action setup

```yaml
# .github/workflows/benchmark.yml
name: Benchmark
on: [push]
jobs:
  benchmark:
    runs-on: ubuntu-latest
    permissions:
      contents: write # needed to push to gh-pages; keep other jobs read-only
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: stable
      - name: Run benchmarks
        run: go test -bench=. -benchmem -count=5 ./... | tee bench.txt
      - uses: bobheadxi/gobenchdata@20682793c754a5377454d3e2b617e45a55ba0b6d # v1.3.1
        with:
          PRUNE_COUNT: 30
          GO_TEST_PKGS: ./...
          BENCHMARKS_OUT: bench.txt
          PUBLISH: true
          PUBLISH_BRANCH: gh-pages
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Regression gating on PRs

```yaml
- name: Check for regressions
  run: gobenchdata checks eval bench.txt --checks-config .gobenchdata-checks.yml
```

```yaml
# .gobenchdata-checks.yml
checks:
  - name: "No major regressions"
    package: ./...
    benchmarks: [".*"]
    thresholds:
      - metric: NsPerOp
        max: 1.2 # fail if >20% slower
      - metric: AllocedBytesPerOp
        max: 1.3 # fail if >30% more allocations
  - name: "Critical path stability"
    package: ./pkg/parser
    benchmarks: ["BenchmarkParse.*"]
    thresholds:
      - metric: NsPerOp
        max: 1.1 # stricter: fail if >10% slower
```

### Dashboard configuration

```yaml
# gobenchdata-web.yml — configure the Vue.js dashboard
title: "My Project Benchmarks"
description: "Performance tracking dashboard"
chartGroups:
  - name: Parser
    charts:
      - name: Parse Performance
        package: myapp/pkg/parser
        benchmarks: ["BenchmarkParse.*"]
        metrics: [NsPerOp, AllocedBytesPerOp, AllocsPerOp]
  - name: Encoding
    charts:
      - name: Encode/Decode
        package: myapp/pkg/encoding
        benchmarks: ["Benchmark(Encode|Decode).*"]
        metrics: [NsPerOp, MBPerS]
```

Best for: long-term trend tracking and visualization; complements benchdiff/cob for immediate gating.

## Tool Selection Guide

| Tool | Statistical rigor | Dashboard | Best for |
| --- | --- | --- | --- |
| **benchdiff** | High (uses benchstat) | No | Local dev + CI PR comparisons |
| **cob** | Low (single comparison) | No | Quick CI gate, simple setup |
| **gobenchdata** | Medium (configurable checks) | Yes (Vue.js on gh-pages) | Long-term trend tracking |
| **benchstat** (raw) | High | No (CSV export) | Maximum control, custom workflows |

## Noisy Neighbor Mitigation

Cloud CI shares hardware with other jobs. Expect 5-10% variance even on quiet machines.

### Why CI benchmarks are noisy

- **Shared CPU/memory** — other CI jobs compete
- **Thermal throttling** — sustained load cuts clock speed
- **Different hardware across runs** — runner specs may differ
- **Kernel scheduling** — context switches add unpredictable latency
- **Disk I/O contention** — shared storage hits I/O-bound benchmarks

### Strategies

**Statistical rigor** — `-count=10` or more, compare with `benchstat`. Single run is meaningless. p-value test filters noise-induced false positives.

**Relative comparison in same job** — run base and head in same CI job on same machine, not against historical absolute values. Cancels machine-to-machine variation. Tools like `benchdiff` do this automatically, checking out both git refs.

**Dedicated benchmark runners** — for critical path benchmarks, self-hosted runners with no other workloads. No noisy neighbors; more infrastructure cost.

**Conservative thresholds** — higher regression thresholds on shared CI (20%+) than dedicated runners (10%). Tight thresholds on noisy runners give false positives that erode trust. GitHub-hosted runners show ~2-3% coefficient of variation at best; <1% false positive rate needs 7%+ performance gate.

**Never "retry until pass"** — retrying until pass is selection bias. If benchmark is flaky, fix noise source (more iterations, dedicated runner, wider threshold), don't retry.

## System Tuning for Self-Hosted Runners

> **WARNING: These commands modify kernel and CPU settings. Apply them ONLY on dedicated CI runners, NEVER on developer machines or shared servers.**

### Disable CPU frequency scaling

Variable CPU frequency makes times meaningless; same code runs at different speeds depending on load and thermals:

```bash
# Set all CPUs to "performance" governor (fixed maximum frequency)
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Disable Turbo Boost

Turbo Boost raises clock speed briefly, then throttles under sustained load. Start and end of run differ:

```bash
# Intel
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

# AMD
echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost
```

### Pin benchmarks to specific CPU cores

Stops OS migrating benchmark process across cores, which thrashes caches (L1/L2 caches are per-core):

```bash
# Pin to cores 2 and 3 (leave cores 0-1 for OS and other processes)
taskset -c 2,3 go test -bench=. -count=10 ./...
```

### Disable SMT (Hyper-Threading)

SMT shares execution units between logical cores of one physical core, causing unpredictable contention:

```bash
# Disable SMT system-wide
echo off | sudo tee /sys/devices/system/cpu/smt/control

# Or disable individual sibling cores (check /sys/devices/system/cpu/cpu*/topology/thread_siblings_list)
echo 0 | sudo tee /sys/devices/system/cpu/cpu1/online  # if cpu0 and cpu1 are siblings
```

### Combined CI setup script

```bash
#!/bin/bash
# benchmark-setup.sh — run on self-hosted CI runner before benchmarks
set -euo pipefail

echo "=== Configuring CPU for stable benchmarks ==="
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || true
echo off | sudo tee /sys/devices/system/cpu/smt/control 2>/dev/null || true

echo "=== Running benchmarks on isolated cores ==="
taskset -c 2,3 go test -bench=. -benchmem -count=10 ./... | tee bench.txt
```
