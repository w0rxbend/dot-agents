### **1. Fork and Join: Manual Concurrency**
*   **`fork`**: `.fork` starts effect immediately on new fiber, returns `Fiber` object.
*   **`join`**: `.join` semantically blocks current fiber until forked fiber completes; returns its result. Underlying OS thread is not blocked.

**Example:**
```scala
for {
  fiber <- doLongWork.fork           // Starts work in background
  _     <- doOtherWork               // Current fiber continues
  result <- fiber.join               // Waits for background work
} yield result
```

### **2. Interruption: Safe Cancellation**
Stops fiber whose result is no longer needed (e.g., timeout, user closing connection).
*   **Finalizers**: Unlike Java threads, interrupting ZIO fiber is **safe**: all finalizers (cleanup logic) run.
*   **Timing**: Runtime checks for interruption between instructions. Cannot interrupt single "monolithic" side-effecting block unless wrapped in constructors like `attemptBlockingCancelable`.

### **3. Parallel Operators (Structured Concurrency)**
High-level operators handle fiber management, error propagation, and interruption automatically. They follow **structured concurrency**: fibers scoped to parents, interrupted if parent fails or terminates.

*   **`zipPar`**: Runs two effects in parallel, returns tuple of results. If one fails, other is interrupted immediately.
*   **`foreachPar`**: Runs effect for each collection element in parallel.
*   **`race`**: Runs two effects concurrently, returns first success, interrupts "loser".

**Example:**
```scala
// Fetch multiple URLs in parallel with a concurrency limit of 10
ZIO.foreachParN(10)(urls)(url => httpClient.get(url))
```

### **4. Race Conditions & Shared State**
Concurrency gets "hard" when fibers share state. ZIO uses functional primitives, not traditional locks:
*   **`Ref`**: Purely functional `AtomicReference`. Atomic updates for single variables.
*   **`STM` (Software Transactional Memory)**: Composes multiple atomic operations into one transaction. Prevents complex races like "bank transfer problem" (one account debited, other not yet credited).

### **Practical Rules & Best Practices**
*   **Prefer High-Level Operators**: `foreachPar`, `zipPar`, `timeout` instead of manual `fork` and `join` whenever possible.
*   **Join or Interrupt**: After manual `fork`, eventually `join` or `interrupt` fiber. Avoids "dangling" work.
*   **Use `ZIO.scoped`**: Scopes define exactly how long fiber or resource lives.
*   **Protect Critical Work**: `.uninterruptible` or `uninterruptibleMask` for logic that must finish once started (e.g., complex state updates).

### **Common Mistakes**
*   **Blocking the Executor**: Synchronous blocking I/O (like legacy JDBC) in standard `ZIO.attempt`. Can cause **thread starvation**. Always use `ZIO.attemptBlocking`.
*   **The Interruption Gap**: `.ensuring` for resource cleanup. Interruption can hit after acquisition, before `.ensuring` begins: **leak**. Always use `ZIO.acquireRelease`.
*   **Non-Atomic Composition**: Expecting two separate `Ref` updates to stay consistent without `STM`. Each update is atomic; sequence is not.
*   **Monolithic Effects**: Giant `while` loop in `ZIO.succeed`. Runtime can't check for interruption inside it, so fiber becomes unresponsive to cancellation.
