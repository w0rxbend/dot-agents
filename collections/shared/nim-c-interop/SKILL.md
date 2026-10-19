---
name: nim-c-interop
user-invocable: false
description: Nim/C interop - importc/exportc/header/dynlib pragmas, wrapping C libraries with Nim 2 destructor-based handles, callbacks, struct layout, cstring lifetimes and building Nim as a C library. Use when calling C from Nim or exposing Nim to C; use nim-memory-management for hook semantics and memory models.
allowed-tools: []
---

# Nim C Interop

## Introduction

Nim compiles to C, enabling seamless interoperability with C code and libraries.
This bi-directional integration allows Nim developers to leverage decades of C
libraries while exposing Nim code to C applications. Understanding C interop is
essential for systems programming and library wrapping.

The interop mechanism uses pragmas like importc, exportc, and header to declare
foreign functions and types. Nim's type system maps naturally to C, with explicit
control over memory layout and calling conventions. This enables zero-overhead
abstraction while maintaining C ABI compatibility.

This skill covers importing C functions and types, wrapping C libraries, header
file generation, memory layout control, callback handling, and patterns for safe
type-safe C interop in systems programming.

## Importing C Functions

Import C functions using pragmas to make them callable from Nim code.

```nim
# Basic C function import
proc printf(format: cstring): cint {.importc, varargs, header: "<stdio.h>".}

proc main() =
  printf("Hello from C!\n")
  printf("Number: %d\n", 42)

# C function with explicit name
proc c_sqrt(x: cdouble): cdouble {.importc: "sqrt", header: "<math.h>".}

proc useSqrt() =
  let result = c_sqrt(16.0)
  echo result  # 4.0

# Multiple headers
proc malloc(size: csize_t): pointer {.importc, header: "<stdlib.h>".}
proc free(p: pointer) {.importc, header: "<stdlib.h>".}

proc manualAlloc() =
  var p = malloc(100)
  # Use memory
  free(p)

# C types mapping
proc strlen(s: cstring): csize_t {.importc, header: "<string.h>".}
proc strcpy(dest, src: cstring): cstring {.importc, header: "<string.h>".}

# Variadic C functions
proc snprintf(buf: cstring, size: csize_t, format: cstring): cint
  {.importc, varargs, header: "<stdio.h>".}

proc formatString(): string =
  var buffer: array[256, char]
  discard snprintf(cstring(addr buffer), 256, "Value: %d", 42)
  result = $cstring(addr buffer)

# C object-like macros as imported variables (importing them as procs would
# generate `EXIT_SUCCESS()`, which is invalid C)
var EXIT_SUCCESS {.importc: "EXIT_SUCCESS", header: "<stdlib.h>".}: cint
var EXIT_FAILURE {.importc: "EXIT_FAILURE", header: "<stdlib.h>".}: cint

# Function pointers
type
  # qsort's prototype takes `const void*`; GCC 14+ rejects a plain `void*`
  # comparator as an incompatible pointer type, so import the const type
  ConstPtr {.importc: "const void*", nodecl.} = pointer
  CompareFunc = proc (a, b: ConstPtr): cint {.cdecl.}

proc qsort(base: pointer, nmemb, size: csize_t, compar: CompareFunc)
  {.importc, header: "<stdlib.h>".}

proc compareInts(a, b: ConstPtr): cint {.cdecl.} =
  let x = cast[ptr cint](a)[]
  let y = cast[ptr cint](b)[]
  return cint(x > y) - cint(x < y)  # x - y can overflow

proc sortArray() =
  var arr = [5.cint, 2, 8, 1, 9]  # element type must match the comparator (cint, not int)
  qsort(addr arr[0], arr.len.csize_t, sizeof(cint).csize_t, compareInts)

# C struct access
type
  TimeSpec {.importc: "struct timespec", header: "<time.h>".} = object
    tv_sec: int
    tv_nsec: int

proc clock_gettime(clk_id: cint, tp: ptr TimeSpec): cint
  {.importc, header: "<time.h>".}

# Calling conventions
proc win_api_func(): cint {.stdcall, importc, dynlib: "kernel32.dll".}

# C++ name mangling
proc cpp_function(x: cint): cint
  {.importcpp, header: "<myheader.hpp>".}

# C library linking
{.passL: "-lm".}  # Link math library
proc cos(x: cdouble): cdouble {.importc, header: "<math.h>".}
```

Import pragmas enable calling C code with full type safety from Nim.

## Wrapping C Libraries

Create type-safe Nim wrappers around C libraries for idiomatic usage.

```nim
# Simple wrapper
type
  FileHandle = distinct cint

proc c_open(path: cstring, flags: cint): cint
  {.importc: "open", header: "<fcntl.h>".}

proc c_close(fd: cint): cint
  {.importc: "close", header: "<unistd.h>".}

proc openFile(path: string): FileHandle =
  let fd = c_open(cstring(path), 0)
  if fd < 0:
    raise newException(IOError, "Failed to open file")
  FileHandle(fd)

proc close(fh: FileHandle) =
  discard c_close(cint(fh))

# Wrapping libcurl
type
  Curl = distinct pointer

const CURLE_OK = 0

proc curl_easy_init(): Curl {.importc, header: "<curl/curl.h>".}
proc curl_easy_cleanup(curl: Curl) {.importc, header: "<curl/curl.h>".}
proc curl_easy_setopt(curl: Curl, option: cint, parameter: pointer): cint
  {.importc, varargs, header: "<curl/curl.h>".}

type
  CurlHandle = object
    handle: Curl

proc newCurl(): CurlHandle =
  result.handle = curl_easy_init()
  if result.handle.pointer == nil:
    raise newException(Exception, "Failed to initialize curl")

proc close(curl: CurlHandle) =
  curl_easy_cleanup(curl.handle)

proc setUrl(curl: CurlHandle, url: string) =
  discard curl_easy_setopt(curl.handle, 10002, cstring(url))

# RAII wrapper with destructor (Nim 2 hook signatures; Nim 1.x used
# `=destroy(x: var T)` and reset fields inside it)
type
  CurlSession = object
    curl: Curl

proc `=destroy`(session: CurlSession) =
  if session.curl.pointer != nil:
    curl_easy_cleanup(session.curl)

proc `=wasMoved`(session: var CurlSession) = session.curl = Curl(nil)
# Without this, a copy would call curl_easy_cleanup twice.
proc `=copy`(dst: var CurlSession; src: CurlSession) {.error: "move-only".}

proc newSession(): CurlSession =
  result.curl = curl_easy_init()

# Wrapping complex C API
type
  # Import the opaque C structs so pointer types match the header exactly
  # (a `distinct pointer` becomes void* and GCC 14+ rejects void** for sqlite3**)
  Sqlite3 {.importc: "sqlite3", header: "<sqlite3.h>", incompleteStruct.} = object
  Sqlite3Stmt {.importc: "sqlite3_stmt", header: "<sqlite3.h>", incompleteStruct.} = object
  SqliteDb = ptr Sqlite3
  SqliteStmt = ptr Sqlite3Stmt

proc sqlite3_open(filename: cstring, db: ptr SqliteDb): cint
  {.importc, header: "<sqlite3.h>".}

proc sqlite3_close(db: SqliteDb): cint
  {.importc, header: "<sqlite3.h>".}

proc sqlite3_prepare_v2(
  db: SqliteDb, sql: cstring, nbyte: cint,
  stmt: ptr SqliteStmt, tail: ptr cstring
): cint {.importc, header: "<sqlite3.h>".}

type
  Database = object
    handle: SqliteDb

# Declare hooks right after the type, before any proc uses Database:
# Nim 2 rejects a hook bound after the type's first use.
proc `=destroy`(db: Database) =
  if db.handle != nil:
    discard sqlite3_close(db.handle)

proc `=wasMoved`(db: var Database) = db.handle = nil
proc `=copy`(dst: var Database; src: Database) {.error: "move-only".}

proc openDatabase(filename: string): Database =
  var db: SqliteDb
  let rc = sqlite3_open(cstring(filename), addr db)
  if rc != 0:
    raise newException(IOError, "Cannot open database")
  result.handle = db

# C callback wrapping
type
  EventCallback = proc (data: pointer) {.cdecl.}

proc c_register_callback(cb: EventCallback, data: pointer)
  {.importc: "register_callback", header: "events.h".}

proc nimCallback(data: pointer) {.cdecl.} =
  echo "Callback triggered"

proc registerEvent() =
  c_register_callback(nimCallback, nil)
```

Wrappers provide Nim-idiomatic interfaces while preserving C library functionality.

## Exporting to C

Export Nim functions to C using exportc pragma for library creation.

```nim
# Basic export
proc add(a, b: cint): cint {.exportc.} =
  a + b

# Export with specific name
proc multiply(a, b: cint): cint {.exportc: "nim_multiply".} =
  a * b

# Export with dynlib
proc divide(a, b: cint): cint {.exportc, dynlib.} =
  if b == 0: return 0
  a div b

# Export complex types
type
  Point {.exportc.} = object
    x: cint
    y: cint

proc createPoint(x, y: cint): Point {.exportc.} =
  Point(x: x, y: y)

proc pointDistance(p1, p2: Point): cdouble {.exportc.} =  # import std/math
  let dx = (p2.x - p1.x).float
  let dy = (p2.y - p1.y).float
  sqrt(dx * dx + dy * dy)

# Export string operations. Never return cstring(someNimString): the Nim
# string is freed when the proc returns and C gets a dangling pointer.
# Either write into a caller-owned buffer...
proc upperInto(input: cstring; buf: ptr char; bufLen: csize_t): cint {.exportc.} =
  let s = toUpperAscii($input)              # import std/strutils
  if s.len.csize_t + 1 > bufLen: return -1
  copyMem(buf, cast[pointer](s.cstring), s.len + 1)
  result = s.len.cint

# ...or hand out a copy C must release through a matching exported free.
proc upperDup(input: cstring): cstring {.exportc.} =
  let s = toUpperAscii($input)
  let p = allocShared0(s.len + 1)          # zeroed, so NUL-terminated
  copyMem(p, cast[pointer](s.cstring), s.len)
  result = cast[cstring](p)

proc upperFree(p: cstring) {.exportc.} = deallocShared(cast[pointer](p))

# C consumers need a header: write the .h yourself (declaring Point and the
# exported procs), or try `--header` and check that your Nim version still
# supports it. Do not also {.emit.} a typedef for an exportc type such as
# Point: the generated C would then define it twice.

# Export callbacks
type
  Callback = proc (value: cint) {.cdecl.}

proc registerCallback(cb: Callback) {.exportc.} =
  cb(42)

# Building shared library
# Compile with: nim c --app:lib --noMain mylib.nim

# Library initialization
proc NimMain() {.importc.}

proc libInit() {.exportc: "lib_init".} =
  NimMain()
  echo "Nim library initialized"

# Export with error handling
proc safeOperation(value: cint): cint {.exportc.} =
  try:
    if value < 0:
      raise newException(ValueError, "Negative value")
    result = value * 2
  except:
    result = -1
```

Exportc enables creating C-compatible libraries from Nim code.

## Memory Layout and Alignment

Control memory layout for C struct compatibility and performance.

```nim
# Packed structures
type
  PackedStruct {.packed.} = object
    a: uint8
    b: uint32
    c: uint8

echo sizeof(PackedStruct)  # 6 bytes (no padding)

# Aligned structures
type
  AlignedStruct = object
    data {.align(16).}: array[4, float32]  # align applies to fields and variables

echo alignof(AlignedStruct)  # 16

# C struct layout
type
  CStruct {.importc, header: "myheader.h".} = object
    field1: cint
    field2: cdouble
    field3: cstring

# Union types
type
  Union {.union.} = object
    intValue: cint
    floatValue: cfloat
    bytes: array[4, uint8]

proc accessUnion() =
  var u: Union
  u.intValue = 0x12345678
  echo u.bytes[0].toHex

# Bit fields (via packed)
type
  BitField {.packed.} = object
    flag1: uint8  # Use 1 byte per field
    flag2: uint8
    value: uint16

# Padding control
type
  ControlledPadding = object
    a: uint8
    pad1 {.align(4).}: array[3, uint8]
    b: uint32

# Calculating offsets
proc fieldOffset() =
  type T = object
    a: int32
    b: int64

  echo offsetOf(T, a)  # 0
  echo offsetOf(T, b)  # 8 (with padding)

# C array mapping
type
  CArray = object
    data: ptr UncheckedArray[cint]
    len: csize_t

proc accessCArray(arr: CArray) =
  for i in 0..<arr.len:
    echo arr.data[i]

# Flexible array member
type
  FlexArray = object
    length: cint
    data: UncheckedArray[cint]

proc createFlexArray(size: int): ptr FlexArray =
  let totalSize = sizeof(cint) + size * sizeof(cint)
  result = cast[ptr FlexArray](alloc(totalSize))
  result.length = cint(size)
```

Memory layout control ensures C compatibility and optimal performance.

## FFI Patterns and Safety

Common patterns for safe foreign function interface usage.

```nim
# Safe string conversion
proc safeToString(cs: cstring): string =
  if cs == nil:
    return ""
  result = $cs

# Handling C errors
type
  CError = object
    code: cint
    message: cstring

proc checkError(err: CError) =
  if err.code != 0:
    raise newException(Exception, $err.message)

# Resource management
type
  Resource = object
    handle: pointer

# Hooks first, then the procs that create or use Resource
proc `=destroy`(r: Resource) =
  if r.handle != nil:
    deallocShared(r.handle)

proc `=wasMoved`(r: var Resource) = r.handle = nil
proc `=copy`(dst: var Resource; src: Resource) {.error: "move-only".}

proc acquire(): Resource =
  result.handle = allocShared(1024)

# Callback with closure
type
  ClosureCallback = object
    fn: proc (data: pointer) {.cdecl.}
    data: pointer

var globalClosure: ref tuple[callback: proc()]

proc wrapCallback(callback: proc()) =
  globalClosure = new(tuple[callback: proc()])
  globalClosure.callback = callback

  proc cCallback(data: pointer) {.cdecl.} =
    globalClosure.callback()

  # Register cCallback with C library

# Opaque types
type
  OpaqueHandle {.importc, header: "lib.h".} = object

proc createHandle(): ptr OpaqueHandle
  {.importc, header: "lib.h".}

proc destroyHandle(h: ptr OpaqueHandle)
  {.importc, header: "lib.h".}

# Platform-specific code
when defined(windows):
  proc windowsFunc() {.importc, dynlib: "kernel32.dll".}
elif defined(posix):
  proc posixFunc() {.importc, header: "<unistd.h>".}
```

Safe FFI patterns prevent common C interop errors and resource leaks.

## Best Practices

1. **Use distinct types** for C handles to prevent mixing different handle types

2. **Implement destructors** for wrapped resources to ensure cleanup

3. **Check for nil** when receiving pointers from C code

4. **Use cstring carefully** as Nim strings and C strings have different lifetimes

5. **Wrap C APIs** with Nim-idiomatic interfaces rather than exposing C directly

6. **Test interop code** thoroughly as type mismatches cause runtime errors

7. **Make every handle wrapper move-only** (`=copy {.error.}`) so a copy can
   never double-free the C resource

8. **Ship a hand-written header** for exported procs and keep it in sync with
   the `exportc` names; call `NimMain()` once before other exports when built
   with `--noMain`

9. **Handle C errors** explicitly and convert to Nim exceptions

10. **Document memory ownership** for functions passing pointers between
    Nim and C

## Common Pitfalls

1. **Not preserving string lifetime** when passing Nim strings to C causes corruption

2. **Forgetting to link C libraries** with passL causes undefined symbol errors

3. **Mismatching calling conventions** (cdecl vs stdcall) causes stack corruption

4. **Not handling nil pointers** from C causes segmentation faults

5. **Incorrect memory layout** for C structs causes data corruption

6. **Handing a `ref` to C without keeping a Nim-side owner** lets ARC/ORC free
   it while C still holds the pointer; keep it alive (store it, or `GC_ref`
   and later `GC_unref`) for as long as C may call back with it

7. **Not checking C return values** misses error conditions

8. **Mixing Nim and C memory** management causes double-free or leaks

9. **Re-declaring C structs by hand** instead of importing them: prefer
   `{.importc: "struct x", header: "x.h".} = object` so the C compiler owns the
   layout; use `{.packed.}` only when the C side is packed

10. **Not testing on target platform** misses platform-specific issues

## When to Use This Skill

Apply C interop when wrapping existing C libraries for Nim projects.

Use importc to leverage battle-tested C code without reimplementation.

Export Nim functions to create libraries usable from C applications.

Integrate with system APIs only available through C interfaces.

Optimize hot paths by calling optimized C implementations.

Build upon C ecosystems while writing higher-level Nim code.

## Done when

- Every imported proc matches the C prototype (types, `cint`/`csize_t`,
  calling convention) and links (`{.passL: "-lfoo".}` or `dynlib`).
- Each owned C handle lives in a move-only wrapper with Nim 2 hooks
  (`=destroy(x: T)`, `=wasMoved`, `=copy {.error.}`).
- No `cstring` derived from a Nim string outlives that string, and every
  pointer handed to C has a documented owner and free function.
- Built and run on the target platform; examples here were not compiled while
  editing this skill.

## Resources

- [Nim C Interop](<https://nim-lang.org/docs/manual.html#foreign-function-interface>)
- [Nim FFI Guide](<https://nim-lang.org/docs/backends.html#c-ffi>)
- [wrapping C libraries](<https://nim-by-example.github.io/ffi/>)
- [Nim C Integration](<https://nim-lang.org/docs/lib.html#c-interface>)
- [Nim Compiler Backend](<https://nim-lang.org/docs/nimc.html#c-code-generation>)
