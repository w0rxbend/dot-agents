# Channels and Select Patterns

## Table of Contents

- [Goroutine Lifecycle](#goroutine-lifecycle)
  - [Panic Recovery at Goroutine Boundaries](#panic-recovery-at-goroutine-boundaries)
- [Channel Direction](#channel-direction)
- [Channel Closing](#channel-closing)
- [Buffer Size](#buffer-size)
- [Select for Non-Blocking Communication](#select-for-non-blocking-communication)
- [Avoid Repeated `time.After` in Hot Loops](#avoid-repeated-timeafter-in-hot-loops)

## Goroutine Lifecycle

NEVER start goroutine without knowing how it stops.

```go
// ✗ Bad — fire-and-forget, no way to stop or wait
func startWorker() {
    go func() {
        for {
            doWork() // runs forever, leaks on shutdown
        }
    }()
}

// ✓ Good — goroutine respects context cancellation, caller can wait
func startWorker(ctx context.Context) *sync.WaitGroup {
    var wg sync.WaitGroup
    wg.Add(1)
    go func() {
        defer wg.Done()
        for {
            select {
            case <-ctx.Done():
                return
            default:
                doWork(ctx)
            }
        }
    }()
    return &wg
}
```

### Panic Recovery at Goroutine Boundaries

Panic in goroutine crashes whole process. Always recover at goroutine boundaries in production code:

```go
go func() {
    defer func() {
        if r := recover(); r != nil {
            // ...
        }
    }()
    doWork(ctx)
}()
```

## Channel Direction

Specify direction in function signatures so compiler catches misuse:

```go
// ✗ Bad — caller could accidentally close or send on a receive-only channel
func consume(ch chan int) { ... }

// ✓ Good — compiler enforces correct usage
func produce(ch chan<- int) { ... } // send-only
func consume(ch <-chan int) { ... } // receive-only
```

## Channel Closing

Sender (producer) MUST close channels, NEVER receiver. Receiver close panics if sender writes after close.

```go
// ✓ Good — producer closes when done
func generate(ctx context.Context) <-chan int {
    ch := make(chan int)
    go func() {
        defer close(ch) // sender closes
        for i := 0; ; i++ {
            select {
            case ch <- i:
            case <-ctx.Done():
                return
            }
        }
    }()
    return ch
}
```

## Buffer Size

| Size | When to use |
| --- | --- |
| 0 (unbuffered) | Default. Syncs sender and receiver. Use for handoff guarantees |
| 1 | Signal channels (`done := make(chan struct{}, 1)`), or sender must not block on single pending item |
| N > 1 | Only with measured justification. Document why N and what happens when buffer fills |

```go
// ✓ Good — unbuffered for synchronous handoff
ch := make(chan Result)

// ✓ Good — buffered 1 for signal
done := make(chan struct{}, 1)

// ✗ Suspicious — arbitrary large buffer hides backpressure problems
// Give explanation in comments.
ch := make(chan Task, 1000) // why 1000? what if it fills?
```

## Select for Non-Blocking Communication

Multiplex channel operations with `select`. Always include `ctx.Done()` to prevent goroutine leaks:

```go
func process(ctx context.Context, in <-chan Task, out chan<- Result) {
    for {
        select {
        case <-ctx.Done():
            return
        case task, ok := <-in:
            if !ok {
                return // channel closed
            }
            result := handle(ctx, task)
            select {
            case out <- result:
            case <-ctx.Done():
                return
            }
        }
    }
}
```

## Avoid Repeated `time.After` in Hot Loops

```go
// ✗ Bad — creates a new timer on every iteration
for {
    select {
    case msg := <-ch:
        handle(msg)
    case <-time.After(5 * time.Second): // repeated allocation/churn
        handleTimeout()
    }
}

// ✓ Good (Go 1.23+) — reuse the timer
timer := time.NewTimer(5 * time.Second)
defer timer.Stop()
for {
    select {
    case msg := <-ch:
        timer.Stop()
        timer.Reset(5 * time.Second)
        handle(msg)
    case <-timer.C:
        handleTimeout()
        timer.Reset(5 * time.Second)
    }
}
```

Go <1.23: if `timer.Stop()` returns false, drain possible stale value before `Reset`. Go 1.23+: receive from `timer.C` after `Stop` returns is guaranteed to block, not get stale value.
