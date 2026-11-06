---
name: docs-mdoc-conventions
description: Shared reference for mdoc code block modifiers and Docusaurus admonitions used across ZIO library documentation skills. Include when writing any documentation that contains Scala code blocks.
allowed-tools: Read, Glob, Grep
color: silver
---

## Agent Workflow

**Phase 1 — Planning only, no edits yet**
Scan document for every Scala code block missing mdoc modifier
(skip pseudocode / type-signature-only blocks). Per block:

1. Create parent task: "Fix mdoc modifier – <section>:<line>"
2. Under it, create two child tasks:
  - "1. Choose and apply modifier"
  - "2. Run `sbt \"docs/mdoc --in <file>.md --out website/<file>.md\"` and confirm zero errors"

Do not touch any source file until full task tree exists and you have
listed it for confirmation.

**Phase 2 — Execution, one leaf task at a time**
Work tree top-to-bottom. Per parent task:
- Mark parent `in_progress`
- Mark child 1 `in_progress` → apply modifier → mark child 1 `completed`
- Mark child 2 `in_progress` → run `sbt "docs/mdoc --in <file> --out website/<file>"` → confirm exit 0 → mark child 2 `completed`
- Mark parent `completed`
  Only then move to next parent task.

**Phase 3 — Mechanical validation**
Once all tasks are `completed`, run (`<this-skill-dir>` is this skill's own directory):

```
bash <this-skill-dir>/check-mdoc-conventions.sh <file.md>
```

Verify exit code 0. If not, re-open relevant tasks and fix.

## Modifiers & Rules

Pick by scope sharing and whether output renders:

- **`mdoc:compile-only`** — Renders source only. Own definitions do not carry to later blocks. Definitions and imports from earlier `mdoc:silent`/`mdoc:invisible` blocks in same file are visible inside it (observed in scalacv, whose guides share one import block). In Mill project, local check is repository's mdoc task (`./mill docs.mdocCheck` in scalacv), not `sbt "docs/mdoc"`.
  **Default** for self-contained examples: shows structure, not evaluated output.

- **`mdoc:silent`** — Renders nothing (hidden), scope shared with later blocks.
  Define types, values or imports that later blocks reference. Scope persists until
  `silent:reset`. **Cannot** redefine same name in later block — use
  `mdoc:silent:nest` for that.

- **`mdoc:silent:nest`** — Renders nothing, scope shared, code wrapped in anonymous `object`.
  Like `silent`, but can **shadow/redefine names** from earlier blocks (e.g., redefining
  `Person` with different fields in later section). Use when `silent` fails on name collision.

- **`mdoc:silent:reset`** — Renders nothing, wipes all accumulated scope, starts fresh.
  Use when switching to wholly different context (new domain, new imports) mid-document
  and `silent:nest` won't suffice.

- **`mdoc`** (no qualifier) — Renders source + evaluated output, scope shared with later blocks.
  REPL-style result, like hand-written `// Right(42L)` but evaluated. Builds on prior
  `silent`/`silent:nest` definitions, or runs standalone for self-contained examples that need output.

- **`mdoc:invisible`** — Invisible code block, scope shared with later blocks.
  Signals "hidden imports only" — rare. Prefer imports in `mdoc:silent` setup block
  (visible in scope) or inside `compile-only` block (self-contained examples).
  Use `invisible` only when shared imports must **not** appear anywhere in rendered output.

- **`mdoc:embed:<path>`** — Custom modifier: replaces block (leave body empty) with file
  at `<path>` (repo-root relative) as titled code fence. Append `:showLineNumbers` for line
  numbers (docs-* skills' spelling; if build rejects it, check which name
  your `zio-sbt-source` version accepts, use that consistently). Use for tutorial's "Putting It Together" final block, pointing at companion example
  file, single source of truth for that complete example. Never paste same code inline
  when companion file carries it. Needs docs subproject to depend on
  `"dev.zio" %% "zio-sbt-source"` — add if missing.

- **No mdoc** (plain `` ```scala ``) — Renders source only, not compiled.
  For pseudocode, ASCII diagrams, illustrative type signatures, non-Scala syntax (e.g., sbt configuration).

- **Public API only.** mdoc block compiles in default package, like user code —
  reference only PUBLIC symbols. `private`/`private[pkg]`/`protected` type or member won't compile in
  snippet, so never demonstrate closed extension point: ✅ implement public
  `LogRecordProcessor` ❌ implement `LogFormatter` whose required parameter type is
  `private[telemetry]`. Check visibility in real source before drafting. If only path
  needs package-private symbol, pick public alternative or drop example.

- -**Never hardcode expression output in comments**: Let mdoc render output; no comments like `// None` or `// "hello"`. Use bare `mdoc` to show all vals; use `mdoc:silent` only when output is verbose boilerplate.

**Bad vs. Good:**
- ❌ `val x = 42 // 42`  
  ✅ `val x = 42` (mdoc renders the output)

## Choosing the Right Modifier

Decision tree:

```
Is this real executable Scala code?
│
├─ NO → Use plain ```scala (pseudocode, ASCII art, type signatures)
│
└─ YES → Do later blocks need these definitions?
   │
   ├─ NO → Do you want to show the output/result?
   │  │
   │  ├─ NO → Use mdoc:compile-only (source only, isolated)
   │  │
   │  └─ YES → Use mdoc (source + output; scope still shared — add :reset to the next block that must not see it)
   │
   └─ YES → Is this a later block showing a result?
      │
      ├─ YES → Use mdoc (source + output)
      │
      └─ NO → Are you redefining a name from an earlier block?
         │
         ├─ YES → Use mdoc:silent:nest (shadow existing names)
         │
         └─ NO → Use mdoc:silent (regular setup)
```

## Common Patterns

### Pattern 1: Silent Setup + Output Rendering (Query DSL SQL Guide)

```scala mdoc:silent
import zio.blocks.schema._

case class Product(
  name: String,
  price: Double,
  category: String,
  inStock: Boolean,
  rating: Int
)

object Product extends CompanionOptics[Product] {
  implicit val schema: Schema[Product] = Schema.derived
  val price: Lens[Product, Double] = optic(_.price)
}

def columnName(optic: zio.blocks.schema.Optic[?, ?]): String = {
  val nodes = optic.toDynamic.nodes
  nodes.collect { case f: DynamicOptic.Node.Field => f.name }.mkString("_")
}
```

With `columnName` in scope, call it and see result:

```scala mdoc
columnName(Product.price)
columnName(Product.name)
```

### Pattern 2: Redefining with Nesting

To redefine a name (e.g., `Person`), use `nest` modifier:

```
Block A: mdoc
  ├─ case class Person(...)    ← in scope
  └─ val alice = ...           ← in scope

Block B: mdoc
  ├─ Can reference alice  ✓
  └─ Can reference Person ✓

Block C: mdoc:nest
  ├─ All prior scope accessible ✓
  └─ Can redefine Person ✓

Block D: mdoc
  ├─ Can reference new Person  ✓
  └─ Cannot reference old Person ✗
```

### Pattern 3: Self-Contained

```scala mdoc:compile-only
case class User(name: String, age: Int)
val user = User("Alice", 30)
```

Each `compile-only` block stands alone. Next example in document has no access to `user`.

### Pattern 4: Setup + Show Output

Use only when first block holds larger setup (e.g., multiple case classes, imports) that later blocks reference, and later block is evaluated to show output:

```scala mdoc:silent
def add(a: Int, b: Int): Int = a + b
```

Now call it and show the result:

```scala mdoc
add(2, 3)
```

If setup is only a line or two, combining it with output block is often cleaner:

```scala mdoc
def add(a: Int, b: Int): Int = a + b

add(2, 3)
```

### Pattern 5: Multi-Step Guide
1. **Setup block** → `mdoc:silent` (case classes, imports)
2. **Example 1** → `mdoc` (show output)
3. **Building on Example 1** → `mdoc` (reuse prior definitions)
4. **New Topic** → `mdoc:silent:reset` + `mdoc:silent` (fresh context)
5. **Final Copy-Paste** → `mdoc:compile-only` (standalone)

### Pattern 6: Multi-Example Documentation Suite

When document holds many independent, self-contained examples (e.g., 4–6 usage examples per library type), **every** example's first code block must use `mdoc:silent:reset` to prevent variable name collisions across examples.

Without reset, `val file`, `val config` or `val user` from Example 1 collide with same-named vars in Example 2, giving "Conflicting definitions" errors even for conceptually separate examples.

```scala mdoc:silent:reset
import zio.blocks.codegen.ir._
import zio.blocks.codegen.emit._

val user = CaseClass("User", List(Field("id", TypeRef.Long)))
val file = ScalaFile(
  packageDecl = PackageDecl("com.example"),
  types = List(user)
)
```

```scala mdoc
ScalaEmitter.emit(file, EmitterConfig())
```

Next example resets again:

```scala mdoc:silent:reset
val order = CaseClass("Order", List(Field("id", TypeRef.Long)))
val file = ScalaFile(
  packageDecl = PackageDecl("com.example"),
  types = List(order)
)
```

```scala mdoc
ScalaEmitter.emit(file, EmitterConfig())
```

## When to Use `:reset`

- Switching to **wholly different domain** (Product → JSON → User)
- Starting **new tutorial section** with independent examples
- **Isolating independent examples in multi-example document** — each `###` section is fresh, self-contained example reusing common names like `file`, `config` or `user`
- Avoid if: only defining new helper function (no reset needed)

## Tips

- **Group related setup blocks** — all prerequisites in one `silent` block if possible
- **Use `:reset` at right scope** — once per independent example in multi-example documents; prefer `:nest` for minor redefinitions *within* single example

## Mechanical Validation

Before submitting, run mdoc-conventions checker on file. Flags any plain ```` ```scala ```` block that should carry mdoc modifier:

```
bash <this-skill-dir>/check-mdoc-conventions.sh <file.md>
```

`--help` gives full usage. **Exit codes:**

| Code | Meaning                                                         |
|------|-----------------------------------------------------------------|
| `0`  | No violations — every executable Scala block has mdoc modifier. |
| `1`  | One or more code blocks missing mdoc modifiers.                 |
| `2`  | Invocation error (missing/extra arguments, file not found).     |

## Docs Classpath

mdoc compiles against docs project's `.dependsOn(...)`. If documented module is missing there,
add it to `build.sbt` (match sibling style, e.g. `<module>.jvm`) and reload. Never downgrade real code
to plain ```` ```scala ```` over missing dependency. Never leave runnable example uncompiled to
dodge build gap.

**Fix build gaps in build, never in page.** `key not found: VERSION` means docs
project defines no `mdocVariables`. Add `mdocVariables += "VERSION" -> version.value` there and
re-run: ✅ `mdocVariables += "VERSION" -> version.value"` in `build.sbt` ❌ writing `% "0.1.0"` into
page (reads as fixed, breaks writing-style rule 25's `@VERSION@` placeholder).

## Verifying the Full Compile

Checker above catches only missing modifiers, not real compile errors.
Always follow with real mdoc compile scoped to touched file, never whole docs set
(unscoped `sbt docs/mdoc` recompiles every doc — minutes of sbt for one-file change):

```bash
sbt "docs/mdoc --in <file> --out website/<file>"
```

`mdoc` is sbt task, not shell binary: quote whole `docs/mdoc …` as one argument (never bare
`mdoc`, never unquoted). One `--in`/`--out` pair per file; `--out` is same path prefixed with
`website/`, e.g. `docs/reference/x.md` → `website/docs/reference/x.md`. If failure output shows only
stack trace with "stack trace is suppressed; run 'last <scope>'", run that `sbt "last <scope>"`
command for real error.

## Troubleshooting

If mdoc produces more than 3 compilation errors, blocks likely aren't isolated. Check for missing `:reset` or `:nest` modifiers, or name collisions between blocks. If issue persists, strip all mdoc modifiers from reported lines and confirm errors vanish. Then re-apply correct modifiers one by one via decision tree, running `sbt "docs/mdoc --in <path> --out website/<path>"` after each change before continuing.

Common mdoc mistakes and fixes: **`references/troubleshooting.md`**.

---

## Tabbed Scala 2 / Scala 3 Examples

When section shows syntax that differs between Scala 2 and Scala 3, use Docusaurus tabs,
not sequential prose blocks.

### Required MDX imports

Add these two lines at top of any `.md` file using tabs (right after frontmatter's closing
`---`, before prose):

```mdx
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
```

### Tab structure

````mdx
<Tabs groupId="scala-version" defaultValue="scala2">
  <TabItem value="scala2" label="Scala 2">

```scala mdoc:compile-only
// Scala 2 syntax here
```

  </TabItem>
  <TabItem value="scala3" label="Scala 3">

```scala mdoc:compile-only
// Scala 3 syntax here
```

  </TabItem>
</Tabs>
````

### Rules

- Always use `groupId="scala-version"` — syncs all tab groups on page when
  reader picks version.
- Always use `defaultValue="scala2"` — Scala 2 shown first by default.
- Blank lines inside `<TabItem>` are required for mdoc to process fenced code blocks.
- `mdoc:compile-only` is modifier for code inside tabs (same as elsewhere).
- mdoc passes JSX components through unchanged — only fenced `scala mdoc:*` blocks are
  rewritten.
- Do **not** use tabs for examples identical in both versions — only
  when syntax genuinely differs.

---

## Docusaurus Admonitions

Callouts use Docusaurus admonition syntax (titles optional):

```
:::note[Title of the note]
Additional context or clarification.
:::

:::tip[Title of the tip]
Helpful shortcut or best practice.
:::

:::warning[Title of the warning]
Common mistake or gotcha to avoid.
:::

:::info[Title of the info]
Background information that is useful but not essential.
:::

:::danger[Title of the danger]
Serious risk of data loss, incorrect behavior, or security issue.
:::
```

Use admonitions **sparingly** — at most 3–4 per typical document. Reserve them for genuinely
important information, not decoration of every section.
