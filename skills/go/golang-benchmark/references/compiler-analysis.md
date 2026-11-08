# Compiler Analysis Reference

Go compiler diagnostic flags show **why** a function allocates or **why** compiler won't inline it.

Use when pprof shows a hot function and you need compiler's view of it. No runtime overhead: analysis is compile-time.

## Table of Contents

- [Escape Analysis](#escape-analysis)
  - [Commands](#commands)
  - [Reading the output](#reading-the-output)
  - [Common escape causes](#common-escape-causes)
- [Inlining Decisions](#inlining-decisions)
  - [Commands](#commands-1)
  - [Reading the output](#reading-the-output-1)
  - [Common inlining blockers](#common-inlining-blockers)
- [SSA Dump](#ssa-dump)
  - [Commands](#commands-2)
  - [Reading ssa.html](#reading-ssahtml)
- [Assembly Output](#assembly-output)
  - [Commands](#commands-3)
  - [Reading assembly output](#reading-assembly-output)
  - [Comparing assembly before/after optimization](#comparing-assembly-beforeafter-optimization)

## Escape Analysis

Escape analysis decides stack (cheap, freed on return) or heap (expensive, needs GC) for each variable. "Moved to heap" means variable might outlive function.

### Commands

```bash
# Show escape decisions — one line per escaped variable
go build -gcflags="-m" ./... 2>&1 | grep "escapes to heap"
go build -gcflags="-m" ./... 2>&1 | grep "moved to heap"

# Verbose mode — shows the reason for each escape decision
go build -gcflags="-m -m" ./...

# Filter to a specific package
go build -gcflags="-m" ./pkg/parser 2>&1 | grep "escapes"

# Filter to a specific file
go build -gcflags="-m" ./pkg/parser/parse.go 2>&1

# Apply to all dependencies too (usually too noisy, but useful for debugging)
go build -gcflags="all=-m" ./...

# Combine with grep for a specific function
go build -gcflags="-m" ./pkg/parser 2>&1 | grep "Parse"

# Combine with grep to see what stays on the stack (does NOT escape)
go build -gcflags="-m" ./pkg/parser 2>&1 | grep "does not escape"
```

### Reading the output

```
./pkg/parser/parse.go:15:6: can inline Parse
./pkg/parser/parse.go:42:13: &result escapes to heap
./pkg/parser/parse.go:42:13:   flow: ~r0 = &result:
./pkg/parser/parse.go:42:13:     from &result (address-of) at ./pkg/parser/parse.go:42:13
./pkg/parser/parse.go:42:13:     from return &result (return) at ./pkg/parser/parse.go:42:6
```

`-m -m` (verbose) shows **escape chain**, the reason for escape. Here `&result` takes `result`'s address and that pointer is returned, so `result` outlives function and escapes to heap.

### Common escape causes

| Cause | Example | Why it escapes |
| --- | --- | --- |
| **Returning pointer to local** | `return &result` | Local outlives call; caller holds reference |
| **Interface boxing** | `var x any = myStruct` | Concrete type stored in `interface{}` allocates heap copy |
| **Closure capturing local** | `go func() { use(localVar) }()` | Goroutine may run after enclosing function returns |
| **Slice append beyond capacity** | `s = append(s, item)` when len == cap | Allocates new backing array on heap |
| **Passing pointer to unanalyzable function** | `json.Marshal(&data)` | Compiler can't prove pointer isn't retained across package boundary |
| **Storing in struct field that escapes** | `obj.Field = &local` | If `obj` is heap-allocated, its pointees must be too |
| **fmt.Sprintf and friends** | `fmt.Sprintf("%d", n)` | Arguments boxed into `any` (interface boxing) + result string heap-allocated |
| **Sending pointer on channel** | `ch <- &data` | Receiver may be different goroutine with different lifetime |

**Not all escapes are problems.** Investigate only in functions pprof flags as allocation-heavy. Function called once at startup can escape freely.

## Inlining Decisions

Inlining replaces call with function body at call site. Removes call overhead, enables more optimizations (better escape analysis, dead code elimination, constant folding). Non-inlined hot-path functions may benefit from simplification.

### Commands

```bash
# Show which functions CAN be inlined
go build -gcflags="-m" ./... 2>&1 | grep "can inline"

# Show which functions CANNOT be inlined (with the reason)
go build -gcflags="-m" ./... 2>&1 | grep "cannot inline"

# Show inlining decisions for a specific package
go build -gcflags="-m" ./pkg/handler 2>&1 | grep "inline"

# Show where inlining was actually applied (function was inlined into caller)
go build -gcflags="-m" ./... 2>&1 | grep "inlining call to"

# Verbose mode — shows the cost budget and why inlining was blocked
go build -gcflags="-m -m" ./... 2>&1 | grep "inline"

# Filter to a specific function
go build -gcflags="-m" ./pkg/handler 2>&1 | grep "HandleRequest"

# Show both inlining and escape analysis together (they interact)
go build -gcflags="-m" ./pkg/handler 2>&1 | grep -E "(inline|escape|moved to heap)"
```

### Reading the output

```
./pkg/handler/handler.go:20:6: can inline validateInput
./pkg/handler/handler.go:35:6: cannot inline HandleRequest: function too complex: cost 120 exceeds budget 80
./pkg/handler/handler.go:42:19: inlining call to validateInput
```

Inline cost budget is approximately 80–82 AST nodes (as of Go 1.22+; increased in later releases). Costlier functions (more AST nodes, complex control flow) are not inlined. Check actual threshold with `-gcflags="-m -m"`.

### Common inlining blockers

| Blocker | Why it prevents inlining | Mitigation |
| --- | --- | --- |
| **Function too complex** | Body cost exceeds budget (80) | Split into smaller functions; extract cold path |
| **`defer` statement** | Adds cleanup code that complicates inlining | Remove `defer` from tiny hot functions; call cleanup directly |
| **`recover()` call** | Forces stack frame preservation | Move `recover()` to wrapper function |
| **`go` statement** | Goroutine launch has implicit complexity | Extract goroutine body into separate function |
| **Type switch / interface method call** | Dynamic dispatch can't be resolved at compile time | Use concrete types in hot paths |
| **`select` statement** | Complex runtime interaction | Simplify channel patterns in hot functions |

**Value receivers vs pointer receivers:** Receiver choice can affect copying, aliasing, escape analysis, inlining. Pointer receiver methods can inline too. Value receivers do not guarantee inlining. Check real decisions with `-gcflags="-m -m"`.

## SSA Dump

SSA (Static Single Assignment) dump shows compiler's intermediate representation after each optimization pass (dead code elimination, bounds check removal, constant folding, register allocation).

### Commands

```bash
# Generate SSA dump for a specific function — creates ssa.html in current directory
GOSSAFUNC=Parse go build ./pkg/parser
# Open ssa.html in browser — shows each optimization pass side by side

# Generate for a method on a type
GOSSAFUNC='(*Parser).Parse' go build ./pkg/parser

# Generate for a function in a specific package (when names collide)
GOSSAFUNC=myapp/pkg/parser.Parse go build ./...

# Combine with a specific output directory
GOSSAFUNC=Parse GOSSADIR=/tmp/ssa go build ./pkg/parser
# Creates /tmp/ssa/ssa.html
```

### Reading ssa.html

HTML shows function code at each compiler pass:

1. **Source** — original Go code
2. **AST** — abstract syntax tree
3. **Start** — initial SSA form
4. **Opt** — after optimization passes (dead code, constant prop, bounds check elimination)
5. **Lower** — architecture-specific lowering
6. **Regalloc** — after register allocation
7. **Genssa** — final generated code

Click a value in any pass to highlight it across passes and trace its transformation. Red values were eliminated (dead code); green values are new (introduced by a pass).

**What to look for:**

- **Bounds checks remaining** — uneliminated `IsInBounds` or `IsSliceInBounds` operations. Explicit bounds checks or `_ = s[n-1]` hints can help
- **Dead code not eliminated** — values computed, never used (should be eliminated; if not, check side effects)
- **Constant folding** — constant computations should resolve at compile time
- **Register spills** — values moved to stack for lack of registers; indicates heavy register pressure

## Assembly Output

Actual machine code from compiler. Use to verify SIMD instructions, bounds checks, register allocation, micro-optimization decisions.

### Commands

```bash
# Full assembly output for a package (very verbose)
go build -gcflags="-S" ./pkg/parser 2>&1 | head -200

# Assembly for a specific function (grep for the function name)
go build -gcflags="-S" ./pkg/parser 2>&1 | grep -A 50 '"".Parse'

# Assembly for all packages (including dependencies — very verbose)
go build -gcflags="all=-S" ./... 2>&1 | grep -A 50 'myapp/pkg/parser.Parse'

# Disassemble a compiled binary (alternative to -gcflags="-S")
go build -o myapp ./cmd/server
go tool objdump -s Parse myapp

# Disassemble with source interleaving
go tool objdump -S -s Parse myapp

# Disassemble a specific symbol
go tool objdump -s 'myapp/pkg/parser.Parse' myapp

# Disassemble a specific text range (by address)
go tool objdump -start 0x4a3b00 -end 0x4a3c00 myapp

# List all symbols in a binary
go tool nm myapp | grep Parse

# Cross-compile and inspect assembly for a different architecture
GOARCH=arm64 go build -gcflags="-S" ./pkg/parser 2>&1 | head -200
```

### Reading assembly output

```asm
"".Parse STEXT size=240 args=0x18 locals=0x48
    0x0000 MOVQ (TLS), CX           ; goroutine stack check
    0x0009 LEAQ -64(SP), AX
    0x000e CMPQ AX, 16(CX)          ; stack overflow check
    0x0012 JLS  228                  ; jump to stack growth
    0x0018 SUBQ $72, SP             ; allocate stack frame
    0x001c MOVQ BP, 64(SP)          ; save base pointer
    0x0021 LEAQ 64(SP), BP          ; set new base pointer
    ; ... function body ...
    0x00e0 CALL runtime.makeslice(SB) ; heap allocation!
```

**What to look for:**

- `CALL runtime.makeslice` or `CALL runtime.newobject` — heap allocations in hot path
- `CALL runtime.growslice` — slice capacity exceeded, triggering copy
- `PCDATA` / `FUNCDATA` — GC metadata (ignore for performance analysis)
- Bounds check sequences: `CMPQ` + `JCC` before array/slice access — sometimes removable
- SIMD instructions: `VMOVDQU`, `VPSHUFB`, `VPADDB`, etc. — verify auto-vectorization or manual SIMD
- `CALL runtime.morestack_noctxt` — stack growth (normal; frequent calls indicate deep recursion)

### Comparing assembly before/after optimization

```bash
# Before your change
go build -gcflags="-S" ./pkg/parser 2>&1 > asm-before.txt

# After your change
go build -gcflags="-S" ./pkg/parser 2>&1 > asm-after.txt

# Diff the assembly
diff asm-before.txt asm-after.txt
```
