### **Typed Errors vs. Defects**
*   **Typed Errors (Checked Failures):** Anticipated failures modeled in `E` type parameter of `ZIO[R, E, A]`. In type signature, so compiler can verify handling.
    *   *Example:* `UserNotFound` when querying database.
*   **Defects (Unchecked Failures):** Unanticipated bugs or unrecoverable situations like `StackOverflowError` or `ArithmeticException`. Not in `E` channel; captured in `Cause` data structure.
    *   *Example:* Undocumented `IOException` in basic console application.

### **Core Error Operators**
*   **`mapError`:** Transforms error type without handling failure. Use to unify error hierarchies (e.g., `DbError` and `ApiError` into common `AppError`).
*   **`catchAll`:** Recovers from all typed errors with fallback effect.
    *   *Usage:* `ZIO.readFile("config.json").catchAll(_ => ZIO.succeed(DefaultConfig))`.
*   **`foldZIO`:** Most general handler: separate effects for success and failure. Transforms both paths into new common success type.

### **Narrowing and Converting Errors**
*   **`orDie`:** Converts `Throwable` error into defect. Use when error is truly unrecoverable at that level of your app. Simplifies type signature to `ZIO[R, Nothing, A]`.
*   **`refineToOrDie`:** Keeps one specific error type in typed channel; kills fiber on all others.
    *   *Practical Case:* Recover from `IOException`; crash if `SecurityException` occurs.

### **Either vs. ZIO Error Channel**
*   **When to use the ZIO Channel:** Standard sequential workflows. Short-circuits automatically in `for-comprehensions`: if first effect fails, later ones never run.
*   **When to use `Either`:** Errors are unrelated and you want to avoid widening error channel to `Any`. "Unwrap" `Either` into ZIO channel with `.some` or `.absolve` for standard composition.

### **Rules of Thumb**
*   **Model Domain Errors with ADTs:** `sealed traits` or `case classes` for expected failures. Enables **exhaustive type checking**.
*   **Log Defects at the Edge:** Never "swallow" defects early. Log them at application entry point, where context is richest, then let fiber die or rethrow.
*   **Narrow Errors Upward:** Low-level utilities return broad errors (like `IOException`). Higher business layers refine them into specific domain failures or defects.

### **Anti-patterns**
*   **Overusing `Task`:** Avoid defaulting to `Task[A]` (error type fixed to `Throwable`) for business logic. Forces "defensive programming": you never know exactly what can fail.
*   **Swallowing Defects:** Catching all defects to prevent crash hides bugs' root cause. Use `.tapDefect` for logging instead.
*   **Ignoring Interruption:** `.ensuring` for resource release instead of `acquireReleaseWith`. Interruption can hit "gap" after acquisition, before `.ensuring` starts: **resource leaks**.
