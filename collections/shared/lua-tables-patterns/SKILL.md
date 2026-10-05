---
name: lua-tables-patterns
user-invocable: false
description: Use when lua tables as the universal data structure including arrays, dictionaries, objects, metatables, object-oriented patterns, data structures, and advanced table manipulation for building flexible, efficient Lua applications.
allowed-tools: []
---

# Use Lua tables

Treat tables as the Lua data/ownership model. Inspect the host runtime before choosing syntax: embedded LuaJIT/Neovim, Lua 5.1, and newer Lua versions differ in library and language support. Preserve metatable behavior, array sequence assumptions, and C-facing ownership. Profile before adding cache or allocation optimizations.

Read the relevant section of [references/language-patterns.md](references/language-patterns.md) for examples and detailed procedures:

- Introduction
- Table Fundamentals
- Array Patterns
- Dictionary and Set Patterns
- Metatables and Metamethods
- Object-Oriented Patterns
- Common Data Structures
- Best Practices
- Common Pitfalls
- When to Use This Skill
- Resources

Verify behavior in the actual embedded runtime and preserve its module conventions.
