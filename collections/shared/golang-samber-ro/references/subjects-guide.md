# Subjects Guide

Subjects are both Observable and Observer: they receive values (via `Send`, `Error`, `Complete`) and accept subscribers. Natively **hot**: subscribers share one execution. Late subscribers only see future emissions (unless replay configured).

## Table of Contents

- [When to Use Subjects vs Cold Observables](#when-to-use-subjects-vs-cold-observables)
- [Subject Types](#subject-types)
  - [PublishSubject](#publishsubject)
  - [BehaviorSubject](#behaviorsubject)
  - [ReplaySubject](#replaysubject)
  - [AsyncSubject](#asyncsubject)
  - [UnicastSubject](#unicastsubject)
- [Cold to Hot Conversion](#cold-to-hot-conversion)
  - [Share](#share)
  - [ShareReplay](#sharereplay)
  - [Connectable Observable](#connectable-observable)
- [Subject Decision Table](#subject-decision-table)
- [Common Subject Mistakes](#common-subject-mistakes)

## When to Use Subjects vs Cold Observables

| Use case | Approach |
| --- | --- |
| Data pipeline from known source (slice, channel, HTTP) | Cold observable (default) |
| Event bus with decoupled producers and consumers | Subject |
| Multiple consumers need same WebSocket/ticker stream | Cold observable + `Share()` or `ShareReplay()` |
| Imperatively push values from non-reactive code | Subject |
| Bridge between callback API and reactive pipeline | Subject (receive callbacks, emit to pipeline) |

## Subject Types

### PublishSubject

Standard multicast. Subscribers only see values emitted **after** they subscribe.

```go
subject := ro.NewPublishSubject[string]()

// Subscriber 1
subject.Subscribe(ro.OnNext(func(s string) {
    fmt.Println("sub1:", s)
}))

subject.Send("hello")  // sub1 sees this

// Subscriber 2 (late)
subject.Subscribe(ro.OnNext(func(s string) {
    fmt.Println("sub2:", s)
}))

subject.Send("world")  // both see this
subject.Complete()
```

**Use when:** broadcasting events where late subscribers don't need history — UI events, log streams, notifications.

### BehaviorSubject

Replays **last emitted value** (or initial value) to every new subscriber immediately on subscription.

```go
subject := ro.NewBehaviorSubject[int](0) // initial value = 0

// Subscriber 1 immediately receives 0
subject.Subscribe(ro.OnNext(func(v int) {
    fmt.Println("sub1:", v) // 0, then 42
}))

subject.Send(42)

// Subscriber 2 immediately receives 42 (latest value)
subject.Subscribe(ro.OnNext(func(v int) {
    fmt.Println("sub2:", v) // 42
}))
```

**Use when:** subscribers need current state — config values, connection status, latest price.

### ReplaySubject

Buffers last **N values**, replays them to every new subscriber.

```go
subject := ro.NewReplaySubject[string](3) // buffer size = 3

subject.Send("a")
subject.Send("b")
subject.Send("c")
subject.Send("d") // "a" evicted from buffer

// Late subscriber receives "b", "c", "d" (last 3)
subject.Subscribe(ro.OnNext(func(s string) {
    fmt.Println(s)
}))
```

**Use when:** late subscribers need recent history — chat messages, recent logs, last N stock ticks.

### AsyncSubject

Emits **only the last value**, and only when subject completes. If subject errors, no value emitted.

```go
subject := ro.NewAsyncSubject[int]()

subject.Subscribe(ro.NewObserver(
    func(v int) { fmt.Println(v) },    // receives 3 only
    func(err error) { },
    func() { fmt.Println("done") },
))

subject.Send(1)
subject.Send(2)
subject.Send(3)
subject.Complete() // triggers emission of 3, then "done"
```

**Use when:** only final result matters — computation result, last response in batch.

### UnicastSubject

Allows exactly **one subscriber**. Buffers values internally until that subscriber connects.

```go
subject := ro.NewUnicastSubject[int](100) // buffer size

subject.Send(1) // buffered
subject.Send(2) // buffered

// Single subscriber receives buffered + future values
subject.Subscribe(ro.OnNext(func(v int) {
    fmt.Println(v) // 1, 2, then future values
}))
// Second subscribe would panic or error
```

**Use when:** single consumer with buffering — job queues, request pipelines where exactly one handler processes events.

## Cold to Hot Conversion

Cold observable (e.g. HTTP request) that multiple subscribers must share:

### Share

```go
// Each subscriber to `cold` would trigger a separate HTTP request
cold := httpPlugin.Get[Data](url)

// Share: single execution, multiple subscribers
hot := ro.Pipe1(cold, ro.Share[Data]())

hot.Subscribe(uiObserver)       // shares one HTTP call
hot.Subscribe(metricsObserver)  // same data, no extra request
```

`Share` uses reference counting: source subscribes when first subscriber arrives, unsubscribes when last one leaves.

### ShareReplay

```go
// Late subscribers get the last N values + future values
hot := ro.Pipe1(cold, ro.ShareReplay[Data](1))
```

### Connectable Observable

Precise control over when shared subscription starts:

```go
connectable := ro.Connectable[Data](cold)

// Set up subscribers first
connectable.Subscribe(observer1)
connectable.Subscribe(observer2)

// Start the shared execution explicitly
sub, err := connectable.Connect(ctx)
```

## Subject Decision Table

| Subject | Replay | Subscribers | Use case |
| --- | --- | --- | --- |
| `PublishSubject` | None | Many | Event bus, notifications |
| `BehaviorSubject` | Last 1 (+ initial) | Many | Current state, config |
| `ReplaySubject` | Last N | Many | Recent history, chat |
| `AsyncSubject` | Last 1 (on complete) | Many | Final computation result |
| `UnicastSubject` | Buffered (pre-subscribe) | Exactly 1 | Single-consumer queue |

## Common Subject Mistakes

| Mistake | Why | Fix |
| --- | --- | --- |
| Calling `Send()` after `Complete()` | Values silently dropped — subject is terminal | Track lifecycle, don't reuse completed subjects |
| Using PublishSubject when late subscribers need history | Late subscribers miss all prior events | Use BehaviorSubject (last 1) or ReplaySubject (last N) |
| Using ReplaySubject with unbounded buffer | Memory grows without limit | Set explicit `bufferSize` |
| Multiple subscribers on UnicastSubject | Panics or undefined behavior | Use PublishSubject for multicast, UnicastSubject for single consumer |
| Not calling `Complete()` on subjects | Subscribers wait forever, goroutine leak | Always `Complete()` or `Error()` when source is done |
