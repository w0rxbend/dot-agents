# benchstat Reference

`benchstat` gives statistical summaries and A/B comparisons of Go benchmark results. Single run shows no variance. `benchstat` tells real difference from noise.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Basic Workflow](#basic-workflow)
  - [Step 0: Write benchmarks](#step-0-write-benchmarks)
  - [Step 1: Measure baseline](#step-1-measure-baseline)
  - [Step 2: Make your change](#step-2-make-your-change)
  - [Step 3: Measure again](#step-3-measure-again)
  - [Step 4: Compare](#step-4-compare)
- [Reading the Output](#reading-the-output)
  - [Unit normalization](#unit-normalization)
  - [When the `~` symbol appears](#when-the--symbol-appears)
- [Flags Reference](#flags-reference)
  - [Projection flags](#projection-flags)
  - [Filter flag](#filter-flag)
  - [Input labeling](#input-labeling)
- [Filter Expression Syntax](#filter-expression-syntax)
  - [Matching operators](#matching-operators)
  - [Logical operators](#logical-operators)
  - [Filter key types](#filter-key-types)
  - [Filter examples](#filter-examples)
- [Projection Examples](#projection-examples)
  - [Default: before/after file comparison](#default-beforeafter-file-comparison)
  - [Compare sub-benchmark parameters within a single file](#compare-sub-benchmark-parameters-within-a-single-file)
  - [Simplify rows to base name only](#simplify-rows-to-base-name-only)
  - [Control column order](#control-column-order)
  - [Group by GOMAXPROCS](#group-by-gomaxprocs)
  - [Separate tables per package](#separate-tables-per-package)
  - [Ignore a dimension](#ignore-a-dimension)
  - [Cross-dimensional comparison](#cross-dimensional-comparison)
- [Unit Metadata](#unit-metadata)
  - [`assume=exact`](#assumeexact)
  - [`assume=nothing` (default)](#assumenothing-default)
- [Interleaving Runs](#interleaving-runs)
- [How Many Runs?](#how-many-runs)
- [Single-File Summary](#single-file-summary)
- [Common Pitfalls](#common-pitfalls)
- [benchstat in CI](#benchstat-in-ci)

## Installation

```bash
go install golang.org/x/perf/cmd/benchstat@v0.0.0-20261009192801-be2c69fb417e  # pinned; bump to a reviewed version
```

## Usage

```bash
benchstat [flags] inputs...
```

Each input: file of `go test -bench` output. Optional labels: `label=path` syntax.

## Basic Workflow

### Step 0: Write benchmarks

Use standard Go benchmark function signature in `*_test.go`:

### Step 1: Measure baseline

Run with `-count=10` or more. One data point per run; meaningful confidence interval needs at least 10:

```bash
go test -run='^$' -bench=BenchmarkParse -benchmem -count=10 ./pkg/parser | tee old.txt
```

`-run='^$'` skips unit tests, so only benchmarks run.

### Step 2: Make your change

Edit code to optimize.

### Step 3: Measure again

Same command, flags, machine, load conditions:

```bash
go test -run='^$' -bench=BenchmarkParse -benchmem -count=10 ./pkg/parser | tee new.txt
```

### Step 4: Compare

```bash
benchstat old.txt new.txt
```

Output:

```
goos: linux
goarch: amd64
pkg: myapp/pkg/parser
cpu: AMD Ryzen 9 5950X 16-Core Processor
          │   old.txt   │              new.txt               │
          │   sec/op    │   sec/op     vs base               │
Parse-32    4.592µ ± 2%   3.041µ ± 1%  -33.78% (p=0.000 n=10)

          │  old.txt   │             new.txt              │
          │    B/op    │    B/op     vs base              │
Parse-32    1.024Ki ± 0%   0.512Ki ± 0%  -50.00% (p=0.000 n=10)

          │  old.txt  │            new.txt             │
          │ allocs/op │ allocs/op   vs base            │
Parse-32    12.00 ± 0%   6.000 ± 0%  -50.00% (p=0.000 n=10)
```

## Reading the Output

| Element | Meaning | What to look for |
| --- | --- | --- |
| **median** (e.g., `4.592µ`) | Central value across runs; unlike mean, outliers don't skew it | Reference number for benchmark |
| **± N%** (e.g., `± 2%`) | Half-width of 95% confidence interval, as % of median | Low (≤2%) = stable. High (>5%) = noisy; find noise sources before trusting results |
| **vs base** (e.g., `-33.78%`) | % change from first input (base) to later inputs | Negative = faster/smaller. Positive = slower/larger |
| **p=N** (e.g., `p=0.000`) | p-value from Mann-Whitney U-test (non-parametric) | <0.05 = statistically significant. ≥0.05 = difference could be noise |
| **n=N** (e.g., `n=10`) | Samples used in comparison | Usually matches `-count`; if not, check input files have same benchmark rows and units |
| **`~`** | No statistically significant difference | Do NOT claim improvement; change may be zero |
| **geomean** row | Geometric mean of changes across table | Overall proportional change; useful for many benchmarks at once |

### Unit normalization

benchstat normalizes display units:

- `ns/op` shown as `sec/op` (µ, m prefixes), avoiding nonsensical `µns/op`
- `MB/s` shown as `B/s` (K, M, G prefixes)

### When the `~` symbol appears

```
Parse-32    4.592µ ± 8%   4.481µ ± 7%  ~ (p=0.089 n=10)
```

benchstat cannot separate difference from noise. Wide CIs (±8%, ±7%) overlap. Options:

- Raise `-count` to 20+ (narrower CI may reveal real difference)
- Cut noise sources (close applications, plug in power, use dedicated machine)
- Accept no measurable effect on this benchmark

## Flags Reference

### Projection flags

| Flag | Default | Purpose |
| --- | --- | --- |
| `-table KEYS` | `.config` | Split results into tables by these keys |
| `-row KEYS` | `.fullname` | Split table rows by these keys |
| `-col KEYS` | `.file` | Columns compare different values of these keys |
| `-ignore KEYS` | (none) | Omit keys from grouping; suppresses "benchmarks vary" warnings |

**Available keys:**

| Key | Meaning | Example value |
| --- | --- | --- |
| `.name` | Base benchmark name (without sub-benchmark config) | `Parse` from `BenchmarkParse/size=4k-16` |
| `.fullname` | Full name including sub-benchmark configuration | `Parse/size=4k-16` |
| `.file` | Input file name or custom label | `old.txt` or `baseline` |
| `.config` | All file-level configuration keys combined | `goos/goarch/pkg/cpu` |
| `.unit` | Metric unit name | `sec/op`, `B/op`, `allocs/op` |
| `/{name-key}` | Per-benchmark sub-name key | `/size` extracts `4k` from `Parse/size=4k` |
| `/gomaxprocs` | GOMAXPROCS value; recognizes both `/gomaxprocs=N` and `-N` suffix convention | `16` from `Parse-16` |
| `goos` | Operating system (from benchmark output header) | `linux`, `darwin` |
| `goarch` | Architecture (from benchmark output header) | `amd64`, `arm64` |
| `pkg` | Package path (from benchmark output header) | `myapp/pkg/parser` |
| `cpu` | CPU model (from benchmark output header) | `AMD Ryzen 9 5950X` |

**Sort order modifiers** (append to any key):

| Modifier | Meaning | Example |
| --- | --- | --- |
| `@alpha` | Alphabetic sort | `/format@alpha` |
| `@num` | Numeric sort (understands prefixes: 2k, 1Mi) | `/size@num` |
| `@(val1 val2 ...)` | Fixed order + filter (only listed values, in this order) | `/format@(gob json)` |

### Filter flag

| Flag | Purpose |
| --- | --- |
| `-filter EXPR` | Filter benchmarks before grouping and comparison |

Details: [Filter Expression Syntax](#filter-expression-syntax).

### Input labeling

Syntax, not flag. Labels give clearer column headers:

```bash
# Default: file names become column headers
benchstat old.txt new.txt

# Custom labels
benchstat baseline=old.txt optimized=new.txt

# Multiple versions
benchstat v1=v1.txt v2=v2.txt v3=v3.txt
```

First input is always **base**; later inputs compare against it.

## Filter Expression Syntax

### Matching operators

| Pattern | Meaning | Example |
| --- | --- | --- |
| `key:value` | Exact match | `goos:linux` |
| `key:"value"` | Exact match with quoted value (allows spaces, special chars) | `pkg:"github.com/user/repo"` |
| `key:/regexp/` | Regular expression match (Go regexp syntax) | `.name:/Parse\|Encode/` |
| `key:(val1 OR val2)` | Match any listed value | `goos:(linux OR darwin)` |
| `*` | Match everything (all benchmarks) | `*` |

### Logical operators

| Operator | Meaning | Example |
| --- | --- | --- |
| `x y` | AND — both must match (implicit) | `goos:linux goarch:amd64` |
| `x AND y` | AND — explicit form | `goos:linux AND goarch:amd64` |
| `x OR y` | OR — either must match | `goos:linux OR goos:darwin` |
| `-x` | NOT — must not match | `-goos:windows` |
| `(...)` | Grouping / subexpression | `(goos:linux OR goos:darwin) -pkg:/internal/` |

### Filter key types

| Key | What it matches | Example |
| --- | --- | --- |
| `.name` | Base benchmark name | `.name:Parse` |
| `.fullname` | Full name with sub-benchmark config | `.fullname:/Parse\/size=4k/` |
| `/{name-key}` | Sub-benchmark parameter | `/size:4k` |
| `/gomaxprocs` | GOMAXPROCS value | `/gomaxprocs:16` |
| `.file` | Input file label | `.file:old.txt` |
| `.unit` | Metric unit | `.unit:sec/op` |
| `goos` | OS from header | `goos:linux` |
| `goarch` | Architecture from header | `goarch:amd64` |
| `pkg` | Package from header | `pkg:/parser/` |

### Filter examples

```bash
# Only Parse benchmarks
benchstat -filter '.name:Parse' old.txt new.txt

# Only benchmarks with size=4096 sub-parameter
benchstat -filter '/size:4096' old.txt new.txt

# Exclude Parallel benchmarks
benchstat -filter '-.name:/Parallel/' old.txt new.txt

# Linux amd64 only
benchstat -filter 'goos:linux goarch:amd64' old.txt new.txt

# Multiple benchmark names
benchstat -filter '.name:(Parse OR Encode OR Decode)' old.txt new.txt

# Complex: Linux or Darwin, not internal packages, only sec/op metric
benchstat -filter '(goos:linux OR goos:darwin) -pkg:/internal/ .unit:sec/op' old.txt new.txt

# Regex: all benchmarks starting with Bench
benchstat -filter '.name:/^Bench/' old.txt new.txt
```

## Projection Examples

### Default: before/after file comparison

```bash
benchstat old.txt new.txt
# Equivalent to:
benchstat -table .config -row .fullname -col .file old.txt new.txt
```

One row per benchmark, one column per file.

### Compare sub-benchmark parameters within a single file

One file with multiple sub-benchmarks (e.g., `BenchmarkEncode/format=json` and `BenchmarkEncode/format=gob`):

```bash
benchstat -col /format bench.txt
```

One column per `/format` value, compared to each other.

### Simplify rows to base name only

```bash
benchstat -col /format -row .name bench.txt
```

Drops sub-benchmark configuration from row names. More compact table.

### Control column order

```bash
# Force gob first, then json (instead of alphabetical)
benchstat -col '/format@(gob json)' bench.txt
```

### Group by GOMAXPROCS

```bash
benchstat -col /gomaxprocs bench.txt
```

Compares GOMAXPROCS values within one file.

### Separate tables per package

```bash
benchstat -table pkg old.txt new.txt
```

One table per package. For multi-package comparisons.

### Ignore a dimension

```bash
# Suppress "benchmarks vary in /gomaxprocs" warning
benchstat -row .name -ignore /gomaxprocs bench.txt
```

### Cross-dimensional comparison

```bash
# Rows = benchmark name, columns = OS, separate tables per architecture
benchstat -row .name -col goos -table goarch results.txt
```

## Unit Metadata

### `assume=exact`

Metrics that should not vary between runs (e.g., binary size, generated code size):

```
BenchmarkSize 1 42 custom-bytes/op
Unit custom-bytes/op assume=exact
```

With `assume=exact`:

- Non-parametric statistics off
- benchstat warns if values vary
- Comparisons shown even with single before/after measurement (no `-count` needed)

### `assume=nothing` (default)

Standard: non-parametric statistics (median + Mann-Whitney U-test). Needs multiple samples.

## Interleaving Runs

Sequential runs (all old, then all new) risk **systematic bias**: thermal throttling builds, background processes come and go, CPU frequency scaling adapts. Interleave to reduce it:

```bash
# Pre-compile both versions to avoid measuring compilation time
go test -c -o old.test ./pkg/parser
# ... make your change ...
go test -c -o new.test ./pkg/parser

# Interleave runs — alternating reduces systematic bias
for i in $(seq 1 10); do
    ./old.test -test.bench=BenchmarkParse -test.benchmem >> old.txt
    ./new.test -test.bench=BenchmarkParse -test.benchmem >> new.txt
done

benchstat old.txt new.txt
```

Pre-compiling with `go test -c` is critical. Otherwise each `go test -bench` invocation includes varying compilation time, contaminating results.

## How Many Runs?

| Scenario | Minimum `-count` | Why |
| --- | --- | --- |
| Quick local check | 6 | Rough confidence interval; fast feedback |
| Pre-merge comparison | 10 | Standard for catching moderate (>5%) changes |
| Detecting small changes (<5%) | 20-30 | More samples narrow CI; needed when signal is small versus noise |
| Noisy CI environment | 20+ | Shared CI runners have higher variance; more runs compensate |

**Never "retry until significant"**. Rerunning until `~` vanishes is selection bias (p-hacking). If 10 runs show `~`, change probably not meaningful. Raise run count **once**, accept result.

At α=0.05, ~5% of benchmarks report significance by chance (false positives). Normal; don't chase them.

## Single-File Summary

Variance of one run, no comparison:

```bash
benchstat bench.txt
```

Median and confidence interval per benchmark. Use to:

- Check measurement stability before code changes
- Find noisy benchmarks needing more runs or better isolation
- Quick summary of current performance

## Common Pitfalls

| Pitfall | Why it's wrong | Fix |
| --- | --- | --- |
| Running on laptop on battery | CPU throttles to save power; variance explodes | Plug in, disable power saving, or use desktop/server |
| Running with browser/IDE open | Background processes steal CPU, add noise | Close unneeded applications, or accept wider CIs |
| Comparing different `-count` values | Unequal sample sizes bias comparison | Use same `-count` for all inputs |

## benchstat in CI

CI pipelines with benchdiff, cob, and gobenchdata: see [CI Regression Detection](./ci-regression.md).
