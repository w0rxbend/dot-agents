### **1. Service Pattern with ZLayer**
*   **Explanation**: **Decouples a service's contract (interface) from its implementation**, per "Onion Architecture" principles. **Trait** defines capabilities; **concrete class** implements them, receiving dependencies via constructor; **ZLayer** in companion object handles initialization and finalization.
*   **Code Example**:
    ```scala
    // 1. Interface
    trait Salutation { def get: UIO[String] } // another domain service
trait Greeter { def sayHello(name: String): UIO[String] }
    
    // 2. Implementation with constructor dependencies
    case class GreeterLive(salutation: Salutation) extends Greeter {
      def sayHello(name: String): UIO[String] = salutation.get.map(s => s"$s, $name!")
    }
    
    // 3. Layer for dependency injection
    object Greeter {
      val layer: URLayer[Salutation, Greeter] = ZLayer.derive[GreeterLive]
    }
    ```

### **2. Repository Pattern**
*   **Explanation**: Specialized Service Pattern that **encapsulates data access logic** (e.g., SQL queries or API calls).
*   **Code Example**:
    ```scala
    trait UserRepo { def findById(id: UUID): Task[Option[User]] }
    
    case class PostgresUserRepo(db: Database) extends UserRepo {
      def findById(id: UUID): Task[Option[User]] = 
        ZIO.attemptBlocking(db.query("SELECT * FROM users WHERE id = ?", id)) // bind params; never interpolate values into SQL
    }
    
    object UserRepo {
      val layer: ZLayer[Database, Nothing, UserRepo] = ZLayer.derive[PostgresUserRepo]
    }
    ```

### **3. HTTP Handler Pattern**
*   **Explanation**: ZIO HTTP models transactions as **pure functions from a Request to a ZIO effect producing a Response**. Routes use **declarative DSL** (RoutePattern) for type-safe path parameter and query string extraction.
*   **Code Example**:
    ```scala
    import zio.http._
    
    val userRoute: Route[UserRepo, Nothing] = 
      Method.GET / "users" / uuid("id") -> handler { (id: UUID, req: Request) =>
        UserRepo.findById(id).map {
          case Some(user) => Response.json(user.toJson)
          case None       => Response.notFound
        }.orDie
      }
    ```

### **4. Background Worker / Job Processing**
*   **Explanation**: **Queue** distributes work; **forkDaemon** runs long-lived "worker" fibers that outlive parent's scope.
*   **Code Example**:
    ```scala
    def startWorker(queue: Queue[Job]): ZIO[Any, Nothing, Fiber.Runtime[Nothing, Nothing]] =
      queue.take
        .flatMap(job => process(job).ignoreLogged) // process job
        .forever
        .forkDaemon // runs in global scope
    ```

### **5. Retry and Scheduling**
*   **Explanation**: **Schedule** describes **composable strategies** for retrying failed effects or repeating successful ones. These "blueprints" can combine **delays (exponential backoff), repetition limits, and conditions**.
*   **Code Example**:
    ```scala
    val retryPolicy = 
      Schedule.exponential(1.second) && Schedule.recurs(5) // backoff + max retries
      
    val robustAction = 
      ZIO.attempt(unstableCall()).retry(retryPolicy)
    ```

### **6. Parallel Processing**
*   **Explanation**: High-level operators like **foreachPar** and **zipPar** run effects concurrently without manual fiber management. They follow **structured concurrency**: if one sub-task fails, all siblings are interrupted automatically, preventing resource leaks.
*   **Code Example**:
    ```scala
    val urls = List("url1", "url2", "url3")
    
    // Process all URLs in parallel with a concurrency limit of 5
    val results = ZIO.foreachParN(5)(urls) { url =>
      HttpClient.get(url)
    }
    ```
