---
name: nim-memory-management
user-invocable: false
description: Nim 2 memory management - ORC/ARC/refc selection with --mm, ref vs ptr, move semantics (sink, lent, ensureMove), lifetime hooks (=destroy, =copy, =sink, =wasMoved, =dup, =trace) and manual allocation. Use when choosing a memory model, writing resource-owning types, debugging leaks or copies, or porting pre-2.0 destructor code; use nim-c-interop for C ownership boundaries.
allowed-tools: []
---

# Nim Memory Management

## 1. Know the version and memory model

Run `nim -v` before writing hooks. Nim 2.0 changed the defaults:

| Topic | Nim 1.x | Nim 2.x |
|-------|---------|---------|
| Default memory model | `refc` (deferred RC + mark/sweep) | `orc` (ARC + cycle collector) |
| Selection flag | `--gc:<x>` | `--mm:<x>` (`--gc` still accepted but deprecated) |
| `=destroy` signature | `proc =destroy(x: var T)` | `proc =destroy(x: T)` (`var T` is deprecated) |
| Extra hooks | `=destroy`, `=copy`, `=sink`, `=trace` | adds `=wasMoved` and `=dup` |
| Threads | `--threads:off` default | `--threads:on` default |
| `ensureMove` | absent | available |

Pick a model:

| `--mm:` | Behavior | Use when |
|---------|----------|----------|
| `orc` (default) | Deterministic ref counting, plus a cycle collector for cyclic `ref` graphs | Almost everything, including async code (async creates cycles) |
| `arc` | Same as ORC without the cycle collector; cycles leak | Hard real-time or embedded code that you have proven acyclic |
| `refc` | Legacy thread-local heaps, deferred RC | Only to keep an old dependency working while you migrate it |
| `none` | No collection; `ref` never freed | Tiny embedded targets with no `ref` usage |

Detect at compile time with `when defined(gcDestructors)` (true for ARC and
ORC) or `when defined(gcOrc)` / `defined(gcArc)`.

Mark `ref` types that can never form cycles with `{.acyclic.}` so ORC skips
tracing them; that is a promise, not a hint - a cycle in an `acyclic` type leaks.

## 2. Value, `ref`, `ptr`

| Kind | Ownership | Freed by |
|------|-----------|----------|
| `object`, `array`, `tuple` | value, copied/moved on assignment | scope exit (`=destroy`) |
| `seq`, `string` | value semantics, heap buffer | scope exit; copies are deep, moves are O(1) |
| `ref T` | shared, reference counted | last reference dropped (or cycle collection under ORC) |
| `ptr T` | untraced raw pointer | you (`dealloc`, `freeShared`) |

- Default to values and `seq`/`string`; reach for `ref` only for shared
  identity or recursive structures.
- `ptr` is for C interop and custom allocators. Wrap it in an object with hooks
  (section 4) instead of passing raw pointers around.
- `addr x` on a local is valid only while `x` is alive; never store it.

## 3. Moves, `sink`, `lent`

The compiler turns the last use of a local into a move and the others into
copies. Make that work for you:

```nim
proc store(db: var seq[string]; s: sink string) =
  db.add s                      # moved in when the caller passes a last use

var db: seq[string]
var line = "x".repeat(1000)     # import std/strutils for repeat
store(db, line)                 # last use of `line` -> moved, no copy

var a = @[1, 2, 3]
let b = move(a)                 # explicit move; `a` is now empty
let c = ensureMove(b)           # Nim 2: compile error if this would copy
```

- `sink T` parameters take ownership; the compiler copies only if the caller
  still uses the argument afterwards.
- `lent T` is for **return types** (and iterator yields) to return a borrowed
  view without copying: `proc first(s: Stack): lent Item = s.items[0]`.
  Ordinary parameters are already passed without copying.
- `--expandArc:procName` prints the code after ARC/ORC inserted copies, moves and
  destroys. Use it when you suspect a hidden copy.
- The `Performance` hint (`--hint:Performance:on`) reports some implicit copies
  of `sink` arguments; check `nim --fullhelp` for your version.

## 4. Lifetime hooks (Nim 2)

Write hooks for a type that owns a non-memory resource or a raw buffer. Order of
definition matters: declare hooks right after the type, before any proc uses it.

### Move-only handle (file descriptor, socket, GPU object)

```nim
import std/[posix, oserrors]

type Fd = object
  h: cint

proc `=destroy`(x: Fd) =
  if x.h >= 0:
    discard posix.close(x.h)

proc `=wasMoved`(x: var Fd) = x.h = -1
proc `=copy`(dst: var Fd; src: Fd) {.error: "Fd is move-only".}
proc `=dup`(src: Fd): Fd {.error: "Fd is move-only".}

proc openFd(path: string): Fd =
  result = Fd(h: posix.open(path.cstring, O_RDONLY))
  if result.h < 0: raiseOSError(osLastError())
```

With `=copy` marked `{.error.}` every accidental copy is a compile error, and
moves work automatically through the default `=sink`.

### Owning container over a raw buffer

```nim
type Buf[T] = object
  len: int
  data: ptr UncheckedArray[T]

proc `=destroy`[T](x: Buf[T]) =
  if x.data != nil:
    for i in 0..<x.len: `=destroy`(x.data[i])
    dealloc(x.data)

proc `=wasMoved`[T](x: var Buf[T]) = x.data = nil

proc `=trace`[T](x: var Buf[T]; env: pointer) =
  # Lets ORC see refs stored inside the buffer.
  if x.data != nil:
    for i in 0..<x.len: `=trace`(x.data[i], env)

proc `=copy`[T](dst: var Buf[T]; src: Buf[T]) =
  if dst.data == src.data: return       # self-assignment
  `=destroy`(dst)
  `=wasMoved`(dst)
  dst.len = src.len
  if src.data != nil:
    dst.data = cast[ptr UncheckedArray[T]](alloc0(src.len * sizeof(T)))
    for i in 0..<src.len: dst.data[i] = src.data[i]

proc `=sink`[T](dst: var Buf[T]; src: Buf[T]) =
  `=destroy`(dst)
  `=wasMoved`(dst)
  dst.len = src.len
  dst.data = src.data
```

Rules:

- `=destroy(x: T)` must not mutate `x`; reset state belongs in `=wasMoved`.
- Destroy contained managed values yourself when you own them through a `ptr`.
- Provide `=trace` whenever a `ptr` buffer can hold `ref`s, or ORC cannot collect
  cycles through it.
- Porting 1.x code: change `=destroy(x: var T)` to `=destroy(x: T)`, move any
  `x.field = nil` resets into `=wasMoved`, and rebuild with `--mm:orc`.
- Use `defer:` (built in) or `try/finally` for one-off cleanup that does not
  warrant a type.

## 5. Manual allocation

```nim
let p = create(int)              # zeroed, typed: ptr int
p[] = 42
dealloc(p)

let arr = cast[ptr UncheckedArray[float]](alloc0(100 * sizeof(float)))
arr[99] = 1.0
dealloc(arr)
```

- `alloc`/`alloc0`/`create`/`realloc` + `dealloc` for thread-local use;
  `allocShared`/`createShared` + `deallocShared`/`freeShared` for memory handed
  to other threads.
- `sizeof` of a `ptr`/`ref` type is the pointer size, not the pointee - pass the
  pointee object type (`sizeof(MyObj)`), or use `create(MyObj)`.
- Allocators (arena, pool) should be objects with a `=destroy` that frees every
  block, and `=copy` set to `{.error.}`.

## 6. Threads

- Nim 2 compiles with `--threads:on`. Under ARC/ORC one shared heap is used, so a
  `ref` may move between threads, but its reference count is not atomic: only
  hand over a graph that no other thread still references.
- Use `std/isolation` (`isolate`, `Isolated[T]`) to prove unique ownership when
  sending, and channels from the `threading` package (`threading/channels`) or
  `std/typedthreads` for workers.
- `{.gcsafe.}` procs must not touch GC'd globals; `{.threadvar.}` gives
  per-thread globals.

## 7. Debugging memory problems

| Symptom | Tool |
|---------|------|
| Leak under ORC/ARC | `-d:useMalloc` then Valgrind or `--passC:-fsanitize=address --passL:-fsanitize=address` |
| Leak only with `--mm:arc` | a cycle: switch to ORC, break it, or use a non-owning `ptr`/ID back-reference |
| Unexpected copies / slow code | `--expandArc:procName`, add `ensureMove`, use `sink` params |
| Use after free | ASan with `-d:useMalloc`; check `ptr`/`addr` escaping its owner |
| Memory growth | `getOccupiedMem()` before/after; `GC_fullCollect()` forces an ORC cycle collection |

Runtime checks: bounds, overflow and nil checks stay on with `-d:release` and are
removed by `-d:danger`. Profile and test with the flags you ship.

## Done when

- `nim -v` is known and hooks use the Nim 2 signatures (`=destroy(x: T)`,
  `=wasMoved`) unless the project pins 1.x.
- The memory model is the default ORC, or the deviation is justified (proven
  acyclic for ARC, a named dependency for refc).
- Every type owning a `ptr` or OS handle has `=destroy` + `=wasMoved` and either
  a correct `=copy` or `=copy {.error.}`.
- Leak checks pass under `-d:useMalloc` with Valgrind or ASan.

## Resources

- [Nim memory management (mm)](<https://nim-lang.org/docs/mm.html>)
- [Nim destructors and move semantics](<https://nim-lang.org/docs/destructors.html>)
- [Nim 2.0 release notes](<https://nim-lang.org/blog/2023/08/01/nim-v20-released.html>)
- [Introduction to ARC/ORC](<https://nim-lang.org/blog/2020/10/15/introduction-to-arc-orc.html>)
