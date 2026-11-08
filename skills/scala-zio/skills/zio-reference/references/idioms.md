### **Error Handling**

*   **Rule**: Model expected domain errors as sealed traits or Algebraic Data Types (ADTs).
    *   **Why**: Compiler checks exhaustiveness. Failure modes become statically-checked documentation.
    *   **Example**: `ZIO.fail(InsufficientFunds(required, actual))`
    *   **Anti-example**: `ZIO.fail(new Exception("Insufficient funds"))`

*   **Rule**: Use `orDie` to shift unrecoverable `Throwable` errors to defect channel.
    *   **Why**: Simpler type signatures: error channel holds business logic failures; catastrophic bugs propagate as fiber failures.
    *   **Example**: `ZIO.attempt(file.readLine).orDie`
    *   **Anti-example**: `val task: ZIO[Any, Throwable, Unit] = ZIO.attempt(println("Critical internal bug"))`

*   **Rule**: Never "swallow" defects. Log with `tapDefect`, then propagate failure.
    *   **Why**: Hidden errors make debugging impossible. Logging at failure site adds context before error reaches system edge.
    *   **Example**: `effect.tapDefect(c => ZIO.logErrorCause("Unexpected failure", c))`
    *   **Anti-example**: `effect.catchAllDefect(_ => ZIO.unit)`

### **Composition**

*   **Rule**: Use for-comprehensions for sequential effect composition.
    *   **Example**: `for { user <- getUser; _ <- notify(user) } yield ()`
    *   **Anti-example**: `getUser.flatMap(user => notify(user).map(_ => ()))`

*   **Rule**: Use `zipLeft` (`<*`) or `zipRight` (`*>`) when one effect's result is not needed.
    *   **Why**: Clearly signal discarded result; less boilerplate in `map` or for-comprehensions.
    *   **Example**: `Console.printLine("Starting") *> runTask`
    *   **Anti-example**: `for { _ <- Console.printLine("Starting"); res <- runTask } yield res`

### **Environment and Dependency Injection**

*   **Rule**: Declare service dependencies in implementation class constructor, not in ZIO environment channel.
    *   **Example**: `case class LiveUserRepo(db: Database) extends UserRepo`
    *   **Anti-example**: `class LiveUserRepo { def get: ZIO[Database, E, User] = ZIO.service[Database].flatMap(...) }`

*   **Rule**: Use `Service Pattern`: trait, implementation case class, `ZLayer` companion.
    *   **Why**: Standard structure; uses ZIO's automatic layer wiring and dependency inference.
    *   **Example**: `trait Repo; case class LiveRepo() extends Repo; object Repo { val layer = ZLayer.derive[LiveRepo] }`
    *   **Anti-example**: Passing service instances manually through deep call stacks.

### **Resource Handling**

*   **Rule**: Use `ZIO.acquireRelease` for any operation needing allocation then deallocation.
    *   **Why**: Release runs regardless of success, failure, or interruption. `ensuring` cannot guarantee this if effect never starts.
    *   **Example**: `ZIO.acquireRelease(openFile)(f => ZIO.succeed(f.close()))`
    *   **Anti-example**: `ZIO.attempt(openFile).flatMap(f => use(f).ensuring(ZIO.attempt(f.close())))`

*   **Rule**: Use `ZIO.scoped` for narrowest possible resource lifetime.
    *   **Example**: `ZIO.scoped { fileResource.flatMap(readData) }`
    *   **Anti-example**: Opening resource at app start and never closing it until JVM exits.

### **Concurrency**

*   **Rule**: Use high-level parallel operators (`zipPar`, `foreachPar`) instead of manual `fork`/`join`.
    *   **Why**: Automatically handle fiber supervision, error aggregation, and safe sibling interruption if one fails.
    *   **Example**: `ZIO.foreachPar(urls)(fetch)`
    *   **Anti-example**: `ZIO.foreach(urls)(url => fetch(url).fork).flatMap(ZIO.collectAll)`

*   **Rule**: Use `ZIO.uninterruptibleMask` instead of `ZIO.uninterruptible` when defining custom operators.
    *   **Why**: Operator protects critical setup/cleanup; caller's task stays interruptible via `restore` function.
    *   **Example**: `ZIO.uninterruptibleMask(restore => setup *> restore(task) *> cleanup)`
    *   **Anti-example**: `setup.uninterruptible *> task.interruptible *> cleanup.uninterruptible`

*   **Rule**: Always `join` or `interrupt` any fiber you manually `fork`.
    *   **Why**: Unhandled fiber "leaks": background tasks may keep running unexpectedly after parent completes.
    *   **Example**: `effect.fork.flatMap(f => f.join.onInterrupt(f.interrupt))`
    *   **Anti-example**: `effect.fork *> ZIO.unit` (without supervision or joining)
