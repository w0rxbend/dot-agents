### **ZIO Abstraction Decision Guide**

#### **1. ZLayer (Dependency Injection & Lifecycle)**
*   **When to use it**: Dependencies between services; services needing effectful initialization or finalization. Ideal for "wiring" application at edge.
*   **When NOT to use it**: Avoid for simple, short-lived values or data without lifecycle.
*   **Example use case**: `GitHubService` that depends on `Config` and `HTTPClient`.

#### **2. Ref (Shared Mutable State)**
*   **When to use it**: Mutable state shared across fibers, updated atomically via compare-and-swap.
*   **When NOT to use it**: Not for updates coordinated across multiple references at once (use `TRef/STM` instead). Use `FiberRef` if state must be local to a fiber.
*   **Example use case**: Concurrent request counter or simple in-memory cache.

#### **3. Queue (Work Distribution)**
*   **When to use it**: Distributing unique tasks among worker fibers (FIFO), or buffering between push-based and pull-based systems.
*   **When NOT to use it**: Avoid for broadcasting same message to all consumers (use `Hub`).
*   **Example use case**: Background worker pool: multiple fibers take tasks from shared bounded queue.

#### **4. Hub (Broadcasting)**
*   **When to use it**: Every subscriber needs copy of every published message (one-to-many communication).
*   **When NOT to use it**: Not for work distribution where only one worker should process each item.
*   **Example use case**: Real-time chat room or stock tick distribution system.

#### **5. Schedule (Retries & Repetition)**
*   **When to use it**: Strategies to retry failed effects or repeat successful ones, by conditions or time intervals.
*   **When NOT to use it**: Avoid for simple, non-timed recursive loops with purely internal logic.
*   **Example use case**: Retrying database connection with exponential backoff, or running cleanup task every Monday at 9 AM.

#### **6. Fiber (Low-Level Concurrency)**
*   **When to use it**: Building new concurrency primitives, or low-level manual control over virtual thread lifecycle.
*   **When NOT to use it**: Default to high-level operators like `zipPar`, `foreachPar`, or `race` whenever possible.
*   **Example use case**: Background health-check process forked via `forkDaemon`, outliving its parent.

#### **7. Scope (Resource Management)**
*   **When to use it**: Lifetime of composable resources needing finalization, especially resources used across multiple effects.
*   **When NOT to use it**: Simple resources within single lexical block: `ZIO.acquireReleaseWith` is often simpler.
*   **Example use case**: Multiple files or network connections that must all close when analysis task finishes.

#### **8. Promise (Synchronization)**
*   **When to use it**: One fiber must wait for result or signal that another fiber provides exactly once.
*   **When NOT to use it**: Not for distributing multiple work items (use `Queue`) or repeatedly changing state (use `Ref`).
*   **Example use case**: Asynchronous cache lookup: multiple fibers wait for first fiber to finish computation.

#### **9. Semaphore (Work Limiting)**
*   **When to use it**: Limit how many fibers can access specific code region or resource at once.
*   **When NOT to use it**: Avoid for coordinating complex transactional state (use `STM`).
*   **Example use case**: Capping application at 10 concurrent outgoing HTTP requests to external API.

#### **10. ZStream (High-Level Streaming)**
*   **When to use it**: Zero or more (potentially infinite) values produced incrementally over time.
*   **When NOT to use it**: Not if computation always produces exactly one value (use `ZIO`).
*   **Example use case**: Processing continuous stream of tweets, or reading massive file line-by-line.
