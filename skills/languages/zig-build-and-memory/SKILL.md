---
name: zig-build-and-memory
description: Maintain version-sensitive Zig build graphs, allocator ownership, buffered I/O, tests and fuzz targets, especially zig-playground's Zig 0.15.2 minimum API contract. Use when editing build.zig, allocator or I/O code, or tests in a Zig project.
license: MIT
---

# Zig build and memory contracts

Read build.zig.zon and build.zig before choosing snippets or commands. Confirm actual compiler version and supported floor. Minimum 0.15.2 is not an exact compiler pin, nor proof every future standard library is compatible. Preserve module names, package fingerprint and dependency hashes unless deliberately changing package identity or dependencies.

Read [build-memory-io.md](references/build-memory-io.md) for repository's module/test graph, unmanaged containers, allocation failure, writer flush and fuzz semantics. Match official docs and std source to compiler in use.

For a change, state who owns allocated bytes and when slices become invalid. Run relevant module and executable tests through existing build graph, then format/build checks fitting the change. Keep deterministic regression results, fuzz duration/corpus findings and cross-target compile results distinct.
