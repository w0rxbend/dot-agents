# Benchmarks in a Test Suite

Benchmarking methodology (`benchstat`, profiling from benchmarks, noise control, CI regression detection) lives in `samber/cc-skills-golang@golang-benchmark` skill. This page covers only benchmarks written next to same package's tests.

## Shape

```go
func BenchmarkStringConcatenation(b *testing.B) {
    b.Run("plus-operator", func(b *testing.B) {
        for b.Loop() {
            result := "a" + "b" + "c"
            _ = result
        }
    })

    b.Run("strings.Builder", func(b *testing.B) {
        for b.Loop() {
            var builder strings.Builder
            builder.WriteString("a")
            builder.WriteString("b")
            builder.WriteString("c")
            _ = builder.String()
        }
    })
}
```

Sub-benchmarks give each variant own output name, which `benchstat` compares. One benchmark mixing both variants yields one number and hides difference.

## Varying input size

```go
func BenchmarkFibonacci(b *testing.B) {
    sizes := []int{10, 20, 30}
    for _, size := range sizes {
        b.Run(fmt.Sprintf("n=%d", size), func(b *testing.B) {
            b.ReportAllocs()
            for b.Loop() {
                Fibonacci(size)
            }
        })
    }
}
```

Size-parameterized sub-benchmarks expose complexity growth: jump outpacing size increase signals superlinear algorithm, invisible to any single-size benchmark.

## `b.Loop()` vs `b.N`

For Go 1.24+, write new benchmarks with `b.Loop()`. It keeps setup out of timed region and stops compiler optimizing loop body away, two failure modes that make `b.N` benchmarks report impossibly fast results. Use legacy `b.N` loop only when module targets Go <1.24 or when intentionally preserving existing benchmark code.
