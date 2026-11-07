* **ZIO[R, E, A] (Functional Effect)**
    * **Definition**: Immutable value describing concurrent workflow: needs environment `R`, eventually yields `A` or fails with `E`.
    * **Role**: Separates describing computation from running it. Enables referential transparency and composability.
    * **Example**: `val effect: ZIO[Any, Nothing, Unit] = ZIO.succeed(println("Action"))`.

* **Type Parameters (R, E, A)**
    * **Definition**: `R`: contravariant input (environment). `E`: covariant failure output. `A`: covariant success output.
    * **Role**: Statically typed, compile-time model for dependency injection and error tracking.
    * **Example**: `ZIO[UserRepo, IOException, String]` (in ZIO 2, built-ins like `Console` and `Clock` are not part of `R`).

* **Fibers**
    * **Definition**: Lightweight virtual threads managed by ZIO runtime.
    * **Role**: Basic concurrency unit: millions of independent tasks without OS thread overhead.
    * **Example**: `for { f <- effect.fork; a <- f.join } yield a`.

* **Interruption**
    * **Definition**: Stops fiber's execution and runs its finalizers.
    * **Role**: Cancels unneeded computations safely, preventing resource leaks.
    * **Example**: `fiber.interrupt`.

* **Environment (ZEnvironment)**
    * **Definition**: Type-indexed map of service implementations an effect requires.
    * **Role**: Modularity: effects "borrow" services provided at application edge.
    * **Example**: `ZIO.service[Clock]`.

* **ZLayer**
    * **Definition**: "Recipe" building services from their dependencies, with effectful initialization and finalization.
    * **Role**: Automates complex dependency graph wiring into single composable value.
    * **Example**: `val layer = ZLayer.fromFunction(MyServiceLive.apply _)`.

* **Scope**
    * **Definition**: Data type for resource lifetime; stores finalizers.
    * **Role**: Unifies resource management: extend or close resource lifetimes declaratively.
    * **Example**: `ZIO.scoped { ZIO.acquireRelease(open)(close).flatMap(use) }`.

* **Resource Safety**
    * **Definition**: Guarantee that resources are released regardless of success, failure, or interruption.
    * **Example**: `ZIO.acquireReleaseWith(acquire)(release)(use)`.
