---
name: lua-tables-patterns
user-invocable: false
description: Lua tables as arrays, maps, sets and objects; metatables and OOP; version differences across 5.1, LuaJIT and 5.4. Use when writing or reviewing table-heavy Lua (including Neovim/LuaJIT plugins); use lua-coroutines for coroutines and lua-c-integration for the C API.
allowed-tools: []
---

# Use Lua tables

Tables are Lua's only composite type: arrays, maps, sets, objects, modules and
namespaces are all tables. Get three things right before writing code: which
runtime runs it, whether a table is a *sequence*, and which metatables are in play.

## 1. Identify the runtime first

| Host | Language | Check with |
|------|----------|------------|
| Neovim, OpenResty, LÖVE, many games | LuaJIT (5.1 semantics + a few 5.2 extensions) | `print(jit and jit.version)` |
| Old embeds, Redis scripting | Lua 5.1 | `print(_VERSION)` -> `Lua 5.1` |
| Current PUC Lua, most new embeds | Lua 5.4 | `print(_VERSION)` -> `Lua 5.4` |

Write to the oldest runtime you must support. Shim the differences once at the
top of the module instead of branching everywhere.

## 2. Version differences that affect table code

| Topic | Lua 5.1 / LuaJIT | Lua 5.4 |
|-------|------------------|---------|
| Unpack | global `unpack(t, i, j)`; some LuaJIT 2.1 builds also expose `table.unpack` - do not rely on it | `table.unpack(t, i, j)`; global `unpack` removed |
| Pack with count | not in 5.1 (availability varies in LuaJIT); use `{n = select("#", ...), ...}` | `table.pack(...)` sets field `n` |
| Move ranges | manual loop (LuaJIT 2.1 has `table.move`) | `table.move(a1, f, e, t, a2)` |
| `__len` on tables | ignored (only userdata) | honored by `#` |
| `__pairs` / `__ipairs` | ignored (LuaJIT: only with 5.2 compat) | `__pairs` honored; `__ipairs` removed in 5.4, `ipairs` respects `__index` |
| `__gc` on tables | not called (userdata only) | called |
| `__close`, `<close>`, `<const>` | absent | 5.4 only |
| Integer vs float keys | all numbers are doubles | integer subtype; float keys with an exact integer value are normalized, so `t[1]` and `t[1.0]` are the same key |
| Integer division `//`, bitwise ops | absent (LuaJIT: `bit` library) | built in |
| Preallocation | LuaJIT: `require("table.new")(narr, nhash)` | none in Lua (C: `lua_createtable`) |
| Clearing | LuaJIT: `require("table.clear")(t)` | assign a new table or loop with `next` |

Portable shim:

```lua
local unpack = table.unpack or unpack
local pack = table.pack or function(...) return { n = select("#", ...), ... } end
```

## 3. Sequences and the `#` operator

`#t` is only well-defined when `t` is a **sequence**: keys `1..n` all non-nil and
no other positive integer keys. With holes, any *border* may be returned, and the
answer differs between 5.1, LuaJIT and 5.4 and even between table construction
orders.

- Never store `nil` in an array slot you will later measure; use a sentinel
  (`false`, a unique `NIL = {}`) or keep an explicit count field `n`.
- For varargs that may contain `nil`, use `select("#", ...)` or `pack(...).n`,
  never `#{...}`.
- `ipairs` stops at the first `nil`; `pairs` order is unspecified, so sort keys
  when output order matters (logs, tests, serialization).
- Do not add new keys during a `pairs` traversal; assigning existing keys
  (including to `nil`) is allowed.

## 4. Pick a shape

| Need | Shape | Note |
|------|-------|------|
| Ordered list | sequence `{a, b, c}` | append with `t[#t + 1] = v` |
| Lookup by key | map `{[k] = v}` | any non-nil, non-NaN key |
| Membership | set `{[v] = true}` | `pairs` to iterate; count separately |
| Object | table + metatable with `__index = Class` | methods via `obj:method()` |
| Cache keyed by objects | weak table `setmetatable({}, {__mode = "k"})` | entries vanish when keys are collected |
| Read-only view / defaults | proxy with `__index`/`__newindex` | `rawget`/`rawset` bypass |

## 5. Metatables and OOP checklist

- Set `Class.__index = Class` once; constructors call `setmetatable(obj, Class)`.
- Use `:` for methods and calls (`obj:m()` passes `obj` as `self`); a `.` call
  with a missing `self` is the most common OOP bug.
- Inheritance: `setmetatable(Child, {__index = Parent})`; call parent methods as
  `Parent.method(self, ...)`.
- Inside `__index`/`__newindex` handlers use `rawget`/`rawset` to avoid
  recursion.
- `__eq` is only consulted when both operands are tables (5.1 additionally
  requires the same metamethod on both).

## 6. Reference material

Read the matching section of
[references/language-patterns.md](references/language-patterns.md) when you need
worked code:

- **Table Fundamentals / Array Patterns** - map/filter/reduce, slicing, chunking,
  flattening helpers.
- **Dictionary and Set Patterns** - merge, invert, group-by, set algebra.
- **Metatables and Metamethods** - vectors with operators, read-only and default
  tables, proxies, `__call`.
- **Object-Oriented Patterns** - classes, inheritance, mixins, private state via
  closures.
- **Common Data Structures** - stack, queue, linked list, priority queue.
- **Best Practices / Common Pitfalls** - review checklist.

The reference is written mostly against Lua 5.4; apply the table in section 2
when targeting 5.1 or LuaJIT.

## Done when

- The target runtime is named and every library call exists there (no bare
  `unpack` on 5.4, no `table.pack`/`table.move` on plain 5.1).
- No `#` or `ipairs` over a table that can contain holes.
- Iteration order is never relied on for `pairs`.
- Code was run under the real host (for Neovim: `nvim --headless -c 'lua ...'`).
