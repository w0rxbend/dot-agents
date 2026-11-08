# Troubleshooting: Common mdoc Mistakes

## "My code won't compile in mdoc"

**Symptom:** mdoc reports compilation error when run locally.

**Common causes:**

### Missing Import
```scala mdoc:silent
// ❌ Missing: where is Product?
val p = Product("Widget", 99)
```

**Fix:** Add import:
```scala mdoc:silent
case class Product(name: String, price: Double)
val p = Product("Widget", 99)
```

### Type Mismatch
```scala mdoc:silent
case class User(name: String, age: Int)
```

```scala mdoc:compile-only
// ❌ age should be Int, not String
val user = User("Alice", "thirty")
```

**Fix:** Match types:
```scala mdoc:compile-only
val user = User("Alice", 30)
```

### Undefined Method
```scala mdoc:silent
case class Point(x: Int, y: Int)
```

```scala mdoc:compile-only
// ❌ Point has no moveTo method
val moved = Point(1, 2).moveTo(3, 4)
```

**Fix:** Define method or use available operations:
```scala mdoc:compile-only
val p = Point(1, 2)
val moved = Point(3, 4)  // Create new point
```

### Implicit Not Found
```scala mdoc:compile-only
// ❌ Schema not derived
case class Product(name: String, price: Double)
val schema = Schema[Product]
```

**Fix:** Add implicit derivation:
```scala mdoc:compile-only
import zio.blocks.schema.Schema

case class Product(name: String, price: Double)
implicit val schema: Schema[Product] = Schema.derived
```

---

## "I can't redefine a name — it says the type already exists"

**Symptom:** Compilation error like "type Person is defined twice" when redefining name in later block.

### Reason
Once `mdoc:silent` block runs, name stays in scope for all later blocks. Cannot redefine it in another `silent` block:

```scala mdoc:silent
case class Person(name: String, age: Int)
```

```scala mdoc:silent
// ❌ ERROR: Person already defined!
case class Person(name: String, email: String)
```

### Fix 1: Use `mdoc:silent:nest`
```scala mdoc:silent
case class Person(name: String, age: Int)
val alice = Person("Alice", 30)
```

```scala mdoc:silent:nest
// ✓ OK: wrapped in object, can shadow Person
case class Person(name: String, email: String)
val bob = Person("Bob", "bob@example.com")
```

`:nest` modifier wraps code in anonymous object, creating new namespace.

### Fix 2: Use `mdoc:silent:reset`
Use for **completely fresh scope** (often better for new guide sections):

```scala mdoc:silent
case class Person(name: String, age: Int)
```

```scala mdoc:silent:reset
// ✓ OK: reset clears all prior scope
case class Person(name: String, email: String)
```

### Fix 3: Use different names
If you need only a variation, name them differently:

```scala mdoc:silent
case class PersonV1(name: String, age: Int)
case class PersonV2(name: String, email: String)
```

---

## "The output doesn't show — the result is hidden"

**Symptom:** You use `mdoc` but nothing appears in rendered output.

### Reason 1: You used `mdoc:compile-only` instead of `mdoc`
```scala mdoc:silent
def greet(name: String) = s"Hello, $name"
```

```scala mdoc:compile-only
// ❌ This shows source but NOT the output
greet("World")
```

**Fix:** Use `mdoc` to render output:
```scala mdoc
greet("World")
```

### Reason 2: The variable isn't in scope
```scala mdoc:compile-only
val x = 42
```

```scala mdoc
// ❌ ERROR: x is not in scope (compile-only isolated)
x + 1
```

**Fix:** Use `mdoc:silent` for setup, then `mdoc` for output:
```scala mdoc:silent
val x = 42
```

```scala mdoc
x + 1
```

### Reason 3: You're in an `mdoc:silent` block
```scala mdoc:silent
// ❌ This is hidden — silenced output
val result = 2 + 2
result
```

**Fix:** Put expression in separate `mdoc` block:
```scala mdoc:silent
val result = 2 + 2
```

```scala mdoc
result
```

---

## "My `mdoc:silent:reset` didn't clear the prior scope"

**Symptom:** Name you thought was cleared is still accessible after reset.

### Reason
Scope is per-document-section. If blocks sit in **different Markdown sections** separated by headers or prose, they may not share scope. Reset applies within current context.

**Example (wrong assumption):**
```scala mdoc:silent
val x = 1
```

Lots of prose here...

```scala mdoc:silent:reset
val y = x + 1  // ❌ x might not be in scope if reset "cleared" it
```

**Fix:** Verify scope behavior locally with `sbt docs`. To be explicit, redefine everything needed:

```scala mdoc:silent:reset
val x = 1
val y = x + 1
```

---

## "Why is the order of my mdoc blocks weird?"

**Symptom:** Blocks compile individually but fail when run together.

### Reason
Scope is **cumulative and sequential**. If Block B depends on something defined in Block A, Block A **must come first**:

```scala mdoc:silent
val name = "Alice"
```

```scala mdoc:silent
val greeting = s"Hello, $name"  // ✓ OK: name defined earlier
```

Reversed order fails:

```scala mdoc:silent
// ❌ ERROR: name not yet defined
val greeting = s"Hello, $name"
```

```scala mdoc:silent
val name = "Alice"
```

**Fix:** Arrange blocks in dependency order:
1. Imports
2. Type definitions (case classes, traits)
3. Helper functions
4. Examples using the above

---

## "I used imports in multiple blocks — will they conflict?"

**Symptom:** `import zio.blocks.schema._` sits in multiple blocks; duplication worry.

### Answer
**No conflict.** Imports are idempotent. Importing same module multiple times is safe:

```scala mdoc:silent
import zio.blocks.schema._
import zio.blocks.schema.json._
```

```scala mdoc:silent
import zio.blocks.schema._  // ✓ OK: re-importing is safe
val x = Schema[Int]
```

**Style tip:** Put all imports in first `mdoc:silent` block to keep them visible. If later section needs different imports, use `mdoc:silent:reset` first.

---

## "I want to show imports but not actually use them in later blocks"

**Symptom:** Readers should see import statement, but it should not be in scope.

### Solution: Use `mdoc:compile-only`
```scala mdoc:compile-only
import zio.blocks.schema._
import zio.blocks.schema.json._
```

Shows imports without adding them to shared scope.

If you **do** want them in scope, use `mdoc:silent`:

```scala mdoc:silent
import zio.blocks.schema._
```

---

## "The real output differs from what I wrote in comments"

**Symptom:** You hand-wrote `// Right(42)` but mdoc shows `// val res0: Either[...] = Right(42)`.

### Why This Happens
You used `mdoc:compile-only` but hand-added result comment. mdoc doesn't evaluate `compile-only` blocks, so comment is plain text.

### Fix
Use `mdoc` and let mdoc render actual output:

```scala mdoc:silent
def safeDivide(a: Int, b: Int): Either[String, Int] =
  if (b == 0) Left("division by zero") else Right(a / b)
```

```scala mdoc
safeDivide(10, 2)
safeDivide(10, 0)
```

---

## "I have a large example — should it be one block or multiple?"

**Symptom:** Example is long; structure unclear.

### Guideline
Split into **multiple blocks** if:
- Explanation belongs **between setup and usage**
- Different **sections** of example should be independently visible
- Output of one part is **educational by itself**

Keep as **one block** if:
- **Self-contained, standalone example** (use `compile-only`)
- All parts **equally important**, best understood together

### Example: Multi-block (Progressive Narrative)
```scala mdoc:silent
case class Request(id: String, status: String)
val req = Request("123", "pending")
```

Here's the initial request. Now let's update it:

```scala mdoc:silent:nest
val updated = req.copy(status = "completed")
```

```scala mdoc
updated
```

### Example: Single-block (Self-Contained)
```scala mdoc:compile-only
case class Request(id: String, status: String)
val req = Request("123", "pending")
val updated = req.copy(status = "completed")
println(updated)
```
