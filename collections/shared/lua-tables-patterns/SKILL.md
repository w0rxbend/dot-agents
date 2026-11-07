---
name: lua-tables-patterns
user-invocable: false
description: Lua tables as arrays, maps, sets and objects; metatables and OOP; version differences across 5.1, LuaJIT and 5.4. Use when writing or reviewing table-heavy Lua (including Neovim/LuaJIT plugins); use lua-coroutines for coroutines and lua-c-integration for the C API.
allowed-tools: []
---

# Use Lua tables

Settle three things before coding: runtime, whether table is *sequence*, which
metatables apply.

## 1. Identify the runtime first

| Host | Language | Check with |
|------|----------|------------|
| Neovim, OpenResty, LÖVE, many games | LuaJIT (5.1 semantics + few 5.2 extensions) | `print(jit and jit.version)` |
| Old embeds, Redis scripting | Lua 5.1 | `print(_VERSION)` -> `Lua 5.1` |
| Current PUC Lua, most new embeds | Lua 5.4 | `print(_VERSION)` -> `Lua 5.4` |

Target oldest runtime you must support. Shim differences once at module top;
no scattered branches.

## 2. Version differences that affect table code

| Topic | Lua 5.1 / LuaJIT | Lua 5.4 |
|-------|------------------|---------|
| Unpack | global `unpack(t, i, j)`; some LuaJIT 2.1 builds expose `table.unpack` - do not rely on it | `table.unpack(t, i, j)`; global `unpack` removed |
| Pack with count | not in 5.1 (varies in LuaJIT); use `{n = select("#", ...), ...}` | `table.pack(...)` sets field `n` |
| Move ranges | manual loop (LuaJIT 2.1 has `table.move`) | `table.move(a1, f, e, t, a2)` |
| `__len` on tables | ignored (only userdata) | honored by `#` |
| `__pairs` / `__ipairs` | ignored (LuaJIT: only with 5.2 compat) | `__pairs` honored; `__ipairs` removed in 5.4, `ipairs` respects `__index` |
| `__gc` on tables | not called (userdata only) | called |
| `__close`, `<close>`, `<const>` | absent | 5.4 only |
| Integer vs float keys | all numbers are doubles | integer subtype; float keys with exact integer value normalized, so `t[1]` and `t[1.0]` are same key |
| Integer division `//`, bitwise ops | absent (LuaJIT: `bit` library) | built in |
| Preallocation | LuaJIT: `require("table.new")(narr, nhash)` | none in Lua (C: `lua_createtable`) |
| Clearing | LuaJIT: `require("table.clear")(t)` | assign new table or loop with `next` |

Portable shim:

```lua
local unpack = table.unpack or unpack
local pack = table.pack or function(...) return { n = select("#", ...), ... } end
```

## 3. Sequences and the `#` operator

`#t` is well-defined only for a **sequence**: keys `1..n` all non-nil, no other
positive integer keys. With holes, `#` may return any *border*. Result varies
across 5.1, LuaJIT and 5.4, even across construction orders.

- Never store `nil` in array slot you later measure. Use sentinel (`false`,
  unique `NIL = {}`) or explicit count field `n`.
- Varargs that may hold `nil`: `select("#", ...)` or `pack(...).n`, never
  `#{...}`.
- `ipairs` stops at first `nil`. `pairs` order unspecified; sort keys when
  output order matters (logs, tests, serialization).
- No new keys during `pairs` traversal. Assigning existing keys (including to
  `nil`) is allowed.

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
- Use `:` for methods and calls (`obj:m()` passes `obj` as `self`). `.` call
  missing `self` is most common OOP bug.
- Inheritance: `setmetatable(Child, {__index = Parent})`; call parent methods as
  `Parent.method(self, ...)`.
- In `__index`/`__newindex` handlers, use `rawget`/`rawset` to avoid recursion.
- `__eq` runs only when both operands are tables (5.1 also requires same
  metamethod on both).

## 6. Reference material

For worked code, read matching section of
[references/language-patterns.md](references/language-patterns.md):

- **Table Fundamentals / Array Patterns** - map/filter/reduce, slicing, chunking,
  flattening.
- **Dictionary and Set Patterns** - merge, invert, group-by, set algebra.
- **Metatables and Metamethods** - vectors with operators, read-only and default
  tables, proxies, `__call`.
- **Object-Oriented Patterns** - classes, inheritance, mixins, private state via
  closures.
- **Common Data Structures** - stack, queue, linked list, priority queue.
- **Best Practices / Common Pitfalls** - review checklist.

Reference targets mostly Lua 5.4. For 5.1 or LuaJIT, apply section 2 table.

## Done when

- Target runtime named; every library call exists there (no bare `unpack` on
  5.4, no `table.pack`/`table.move` on plain 5.1).
- No `#` or `ipairs` over table that can contain holes.
- Code never relies on `pairs` iteration order.
- Code ran under real host (Neovim: `nvim --headless -c 'lua ...'`).
