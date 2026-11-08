### **1. Overusing `Task` instead of Domain Errors**
*   **Description**: Defaulting to `Task[A]` (type alias for `ZIO[Any, Throwable, A]`) for every business-logic failure.
*   **Why it is wrong**: `Throwable` is unsealed: compiler cannot verify all error cases are handled. Conflates **expected domain errors** (like `UserNotFound`) with **defects** (unrecoverable bugs like `StackOverflowError`). Forces defensive programming.
*   **Correct alternative**: Model expected errors as **Sealed Traits or Algebraic Data Types (ADTs)** for compiler-checked exhaustive pattern matching.
*   **Example**:
    *   *Anti-pattern*: `def getUser(id: Int): Task[User] = ZIO.fail(new Exception("User not found"))`
    *   *Idiomatic*: `def getUser(id: Int): IO[UserError, User] = ZIO.fail(UserNotFound(id))`

### **2. Mixing `Future` with ZIO Incorrectly**
*   **Description**: `Future` created outside ZIO effect, then wrapped with `ZIO.fromFuture`.
*   **Why it is wrong**: `Future` is a **running computation**. Created outside ZIO, it starts immediately, breaking referential transparency. ZIO cannot **retry, delay, or properly interrupt** work already "in flight".
*   **Correct alternative**: Pass function that creates `Future` into `ZIO.fromFuture`. Creation deferred until effect runs.
*   **Example**:
    *   *Anti-pattern*: `val f = callLegacyApi(); ZIO.fromFuture(_ => f)`
    *   *Idiomatic*: `ZIO.fromFuture(ec => callLegacyApi()(ec))`

### **3. Misusing Environment (Declaring Dependencies in `R`)**
*   **Description**: Service's dependencies declared in environment channel (`R`) of its own trait methods.
*   **Why it is wrong**: "Leaky" interface: implementation details (what service needs) exposed to every caller. Environment type "bloats" as dependencies ripple through call stack.
*   **Correct alternative**: **Service Pattern**: trait with `R` of `Any`; dependencies go into **constructor** of concrete implementation class.
*   **Example**:
    *   *Anti-pattern*: `trait UserService { def get(id: Int): ZIO[Database, E, User] }`
    *   *Idiomatic*: `case class LiveUserService(db: Database) extends UserService { def get(id: Int): IO[E, User] = ... }`

### **4. Unsafe Resource Handling with `ensuring`**
*   **Description**: `.ensuring` releases resource right after acquisition effect.
*   **Why it is wrong**: Interruption can occur in "gap" after acquisition, before `use` effect begins. There `ensuring` will not trigger: parent effect never technically "started" its main logic. Result: **resource leak**.
*   **Correct alternative**: `ZIO.acquireReleaseWith` or `ZIO.acquireRelease` within `Scope`. Release logic guaranteed to run if acquisition completes.
*   **Example**:
    *   *Anti-pattern*: `acquire.flatMap(r => use(r).ensuring(release(r)))`
    *   *Idiomatic*: `ZIO.acquireReleaseWith(acquire)(release)(use)`

### **5. Blocking Operations without Proper Wrappers**
*   **Description**: Synchronous blocking I/O (like `scala.io.Source` or legacy JDBC) wrapped in standard constructors like `ZIO.attempt` or `ZIO.succeed`.
*   **Why it is wrong**: ZIO’s default executor has small, fixed thread count optimized for CPU-bound work. Blocking I/O there can cause **thread starvation**: whole application hangs or performs poorly.
*   **Correct alternative**: `ZIO.attemptBlocking` or `ZIO.attemptBlockingIO`. Shifts work to dedicated, dynamically-sized blocking thread pool.
*   **Example**:
    *   *Anti-pattern*: `ZIO.attempt(Source.fromURL(url).mkString)`
    *   *Idiomatic*: `ZIO.attemptBlockingIO(Source.fromURL(url).mkString)`

### **6. Accessor Methods in Service Companion Objects**
*   **Description**: Companion-object methods that delegate to `ZIO.serviceWithZIO`, mirroring each service trait method.
*   **Why it is wrong**: Pattern **deprecated by the ZIO library**. Redundant boilerplate duplicates whole service interface in companion object. Obscures actual dependency at call site.
*   **Correct alternative**: Call `ZIO.serviceWithZIO[Service](_.method(args))` directly at each call site.
*   **Example**:
    *   *Anti-pattern*:
        ```scala
        object Greeter {
          val layer: URLayer[Salutation, Greeter] = ZLayer.derive[GreeterLive]
          def sayHello(name: String): URIO[Greeter, String] = ZIO.serviceWithZIO(_.sayHello(name))
        }
        // call site:
        Greeter.sayHello("World")
        ```
    *   *Idiomatic*:
        ```scala
        object Greeter {
          val layer: URLayer[Salutation, Greeter] = ZLayer.derive[GreeterLive]
        }
        // call site:
        ZIO.serviceWithZIO[Greeter](_.sayHello("World"))
        ```
